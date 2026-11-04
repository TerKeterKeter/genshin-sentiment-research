import csv
import json
from datetime import datetime, timezone
from pathlib import Path


def utc(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Timestamp must include timezone")
    return result.astimezone(timezone.utc)


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows, fields=None):
    rows = list(rows)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fields = fields or list(dict.fromkeys(key for row in rows for key in row))
    with open(path, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


OPERATION_LABELS = {
    "metadata_allowed": "Baca metadata YouTube",
    "collection_allowed": "Kumpulkan komentar utama",
    "derived_analysis_allowed": "Analisis sentimen dan evaluasi data nyata",
    "external_join_allowed": "Gabungkan agregat dengan revenue eksternal",
}


class DataUseSettingsError(PermissionError):
    """Missing project settings, shown as a checklist in the browser."""

    def __init__(self, requirements):
        self.requirements = requirements
        super().__init__(
            "Pengaturan penggunaan data belum lengkap. " + " ".join(requirements)
        )


def authorization_requirements(config, permissions, operation):
    """Explain each unmet setting without changing or granting any scope."""
    missing = []
    if config["dry_run"]:
        missing.append(
            "Mode Offline / dry-run masih aktif. Nonaktifkan hanya jika dasar "
            "penggunaan untuk langkah ini sudah diperiksa."
        )
    if not permissions.get(operation):
        label = OPERATION_LABELS.get(operation, operation)
        missing.append(
            f'Operasi "{label}" belum diaktifkan. Centang hanya jika langkah '
            "tersebut tercakup dalam dasar penggunaan proyek."
        )
    reviewed_at = str(permissions.get("policy_reviewed_at") or "").strip()
    reference = str(permissions.get("evidence_reference") or "").strip()
    if not reviewed_at:
        missing.append(
            'Isi "Tanggal tinjauan kebijakan" dengan tanggal ketika peneliti '
            "memeriksa ketentuan penggunaan yang berlaku."
        )
    if not reference:
        missing.append(
            'Isi "Referensi dasar penggunaan proyek" dengan sumber/rujukan '
            "yang benar-benar diperiksa, operasi yang dicakup, dan batasannya."
        )
    if (
        permissions.get("policy_review_status") != "documented"
        and reviewed_at
        and reference
    ):
        missing.append(
            "Tinjauan penggunaan belum tercatat lengkap. Periksa tanggal dan "
            "referensi pada Pengaturan & API, lalu klik Simpan pengaturan."
        )
    retention = permissions.get("retention_days")
    if type(retention) is not int or not 1 <= retention <= 30:
        missing.append(
            'Isi "Masa simpan data / retensi (hari)" dengan bilangan bulat 1–30. '
            "Ini batas penyimpanan paket data, bukan jumlah hari komentar yang diambil."
        )
    return missing


def authorize(config, permissions, operation):
    missing = authorization_requirements(config, permissions, operation)
    if missing:
        raise DataUseSettingsError(missing)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value, *, ensure_ascii=True):
    Path(path).write_text(
        json.dumps(value, indent=2, ensure_ascii=ensure_ascii) + "\n", encoding="utf-8"
    )
