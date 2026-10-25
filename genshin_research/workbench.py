"""Local CSV/JSON persistence for one research project. No credentials are saved."""

import csv
import hashlib
import io
import json
import re
import shutil
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .core import read_csv, read_json, utc
from .registry import EVENT_FIELDS, video_id_from_input

SETTINGS = dict(
    dry_run=True,
    metadata_allowed=False,
    collection_allowed=False,
    derived_analysis_allowed=False,
    external_join_allowed=False,
    policy_review_status="reviewed",
    policy_reviewed_at="",
    evidence_reference="",
    retention_days=30,
    candidate_start="2026-01-01",
    candidate_end_exclusive="2026-10-01",
    window_hours=72,
    language="en",
    random_seed=42,
)
API_FIELDS = [
    "channel_id",
    "video_published_at_utc",
    "api_title",
    "api_verified_at_utc",
    "api_expires_at_utc",
    "official_channel_match",
]


def now_utc():
    return datetime.now(timezone.utc)


def json_safe(value):
    """Reject NaN/Infinity in saved scientific results."""
    return json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)


def csv_text(rows, fields=None):
    rows = list(rows)
    fields = fields or list(dict.fromkeys(k for row in rows for k in row))
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def parse_csv(content):
    stream = io.StringIO(
        content.decode("utf-8-sig") if isinstance(content, bytes) else content
    )
    reader = csv.DictReader(stream)
    if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("Header CSV kosong atau duplikat.")
    rows = list(reader)
    if any(None in row or any(v is None for v in row.values()) for row in rows):
        raise ValueError(
            "CSV rusak: jumlah kolom tidak sesuai header. Gunakan pemisah koma."
        )
    return rows


class Store:
    def __init__(self, root="data/workbench"):
        self.root = Path(root).resolve()
        if Path("data").resolve() not in self.root.parents:
            raise ValueError("Folder aplikasi harus berada di dalam data/.")
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        if not (self.root / "settings.json").exists():
            self.save_json("settings.json", SETTINGS)
        if not (self.root / "events.csv").exists():
            source = (
                Path("data/events.csv")
                if Path("data/events.csv").exists()
                else Path("templates/events.csv")
            )
            rows = read_csv(source) if source.exists() else []
            # Existing files are copied, never modified. Unverified API data is not treated as verified.
            self.save_events(rows)
        if not (self.root / "coverage.csv").exists():
            source = (
                Path("data/discovery_coverage.csv")
                if Path("data/discovery_coverage.csv").exists()
                else Path("templates/discovery_coverage.csv")
            )
            rows = read_csv(source) if source.exists() else []
            self.save_csv(
                "coverage.csv",
                rows,
                ["month", "discovery_status", "checked_at_utc", "evidence_notes"],
            )
        (self.root / "runs").mkdir(exist_ok=True)

    def path(self, relative):
        path = (self.root / relative).resolve()
        if self.root not in path.parents:
            raise ValueError("Lokasi berkas tidak diizinkan.")
        return path

    def atomic(self, relative, text):
        path = self.path(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
        try:
            temporary.write_text(text, encoding="utf-8")
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)

    def save_json(self, relative, value):
        with self.lock:
            self.atomic(relative, json_safe(value) + "\n")

    def save_csv(self, relative, rows, fields=None):
        with self.lock:
            self.atomic(relative, csv_text(rows, fields))

    def settings(self):
        return {**SETTINGS, **read_json(self.root / "settings.json")}

    def events(self):
        return read_csv(self.root / "events.csv")

    def save_events(self, rows):
        fields = list(
            dict.fromkeys(EVENT_FIELDS + API_FIELDS + [k for row in rows for k in row])
        )
        normalized = [{k: row.get(k, "") for k in fields} for row in rows]
        self.save_csv("events.csv", normalized, fields)

    def add_event(self, link, character=""):
        video_id = video_id_from_input(link) if link.strip() else ""
        if not video_id and not character.strip():
            raise ValueError(
                "Isi link Short atau nama karakter untuk event tanpa Short."
            )
        with self.lock:
            rows = self.events()
            if video_id and any(row["video_id"] == video_id for row in rows):
                raise ValueError("Video sudah terdaftar. Edit kandidat yang ada.")
            row = dict.fromkeys(EVENT_FIELDS + API_FIELDS, "")
            row.update(
                event_id="event_" + uuid.uuid4().hex[:12],
                video_id=video_id,
                video_url=f"https://youtube.com/shorts/{video_id}" if video_id else "",
                character_name=character.strip(),
                inclusion_status="pending",
            )
            rows.append(row)
            self.save_events(rows)
            return row["event_id"]

    def event(self, event_id):
        return next((r for r in self.events() if r["event_id"] == event_id), None)

    def update_event(self, event_id, changes):
        with self.lock:
            rows = self.events()
            row = next((r for r in rows if r["event_id"] == event_id), None)
            if row is None:
                raise ValueError("Event tidak ditemukan.")
            row.update(changes)
            self.save_events(rows)

    def delete_event(self, event_id):
        with self.lock:
            self.save_events([r for r in self.events() if r["event_id"] != event_id])
            # Delete dependent comments, labels, annotations and aggregates together.
            for run in self.runs():
                if event_id in run["event_ids"]:
                    shutil.rmtree(self.run_path(run["run_id"]))

    def run_path(self, run_id):
        if not re.fullmatch(r"[a-f0-9]{16}", run_id):
            raise ValueError("ID dataset tidak valid.")
        return self.path("runs/" + run_id)

    def new_run(self, events, synthetic=False):
        run_id = uuid.uuid4().hex[:16]
        path = self.run_path(run_id)
        path.mkdir()
        settings = self.settings()
        manifest = dict(
            run_id=run_id,
            created_at=now_utc().isoformat(),
            expires_at=(
                now_utc() + timedelta(days=settings["retention_days"])
            ).isoformat(),
            event_ids=[r["event_id"] for r in events],
            collection_complete=False,
            synthetic=synthetic,
            window_hours=settings["window_hours"],
            permission_reference=settings["evidence_reference"],
        )
        self.save_json(f"runs/{run_id}/manifest.json", manifest)
        self.save_csv(f"runs/{run_id}/events.csv", events)
        return run_id

    def manifest(self, run_id):
        return read_json(self.run_path(run_id) / "manifest.json")

    def runs(self):
        result = []
        for path in sorted((self.root / "runs").glob("*/manifest.json"), reverse=True):
            if re.fullmatch(r"[a-f0-9]{16}", path.parent.name):
                result.append(read_json(path))
        return sorted(result, key=lambda r: r["created_at"], reverse=True)

    def require_run(self, run_id, predictions=False):
        manifest = self.manifest(run_id)
        if utc(manifest["expires_at"]) <= now_utc():
            raise ValueError(
                "Dataset kedaluwarsa; hapus atau kumpulkan ulang sesuai izin."
            )
        if not manifest["collection_complete"]:
            raise ValueError(
                "Pagination belum lengkap. Dataset ini tidak boleh masuk analisis utama."
            )
        if predictions and not (self.run_path(run_id) / "predictions.csv").exists():
            raise ValueError("Jalankan NLP pada dataset ini terlebih dahulu.")
        return manifest

    def purge_expired(self):
        with self.lock:
            changed = False
            rows = self.events()
            for row in rows:
                # Unverified imported metadata also receives a conservative local expiry.
                if any(
                    row.get(k) for k in ["channel_id", "video_published_at_utc"]
                ) and not row.get("api_expires_at_utc"):
                    row["api_expires_at_utc"] = (
                        now_utc() + timedelta(days=30)
                    ).isoformat()
                    changed = True
                if (
                    row.get("api_expires_at_utc")
                    and utc(row["api_expires_at_utc"]) <= now_utc()
                ):
                    for key in API_FIELDS:
                        row[key] = ""
                    if row["inclusion_status"] == "included":
                        row["inclusion_status"] = "pending"
                    changed = True
            if changed:
                self.save_events(rows)
            for run in self.runs():
                if utc(run["expires_at"]) <= now_utc():
                    shutil.rmtree(self.run_path(run["run_id"]))

    def fingerprint(self, events):
        return hashlib.sha256(json.dumps(events, sort_keys=True).encode()).hexdigest()
