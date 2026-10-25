"""Local browser workbench: CRUD, collection, local NLP, evaluation and monthly analysis."""

import io
import os
import secrets
import shutil
from datetime import timedelta

from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from .analysis import (
    REVENUE_FIELDS,
    aggregate,
    forecast,
    pair_months,
    scatter,
    spearman,
    validate_revenue,
)
from .audit import STATUSES, audit
from .collection import COMMENT_FIELDS, collect_event
from .core import authorize, read_csv, read_json, utc
from .jobs import Jobs
from .registry import video_id_from_input
from .sentiment import (
    MODEL_ID,
    MODEL_LICENSE,
    MODEL_REVISION,
    annotation_sample,
    evaluate,
    exclusion_report,
    infer,
    preprocess,
)
from .workbench import API_FIELDS, Store, csv_text, now_utc, parse_csv
from .youtube import YouTube


def create_app(data_dir="data/workbench"):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=secrets.token_hex(32),
        MAX_CONTENT_LENGTH=10 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Strict",
        TRUSTED_HOSTS=["localhost", "127.0.0.1"],
        YOUTUBE_API_KEY=os.environ.get("YOUTUBE_API_KEY", ""),
    )
    store = Store(data_dir)
    jobs = Jobs()
    app.extensions.update(store=store, jobs=jobs)

    @app.before_request
    def protect():
        if "csrf" not in session:
            session["csrf"] = secrets.token_urlsafe(32)
        if request.method == "POST":
            if not secrets.compare_digest(
                session["csrf"], request.form.get("csrf", "")
            ):
                abort(
                    400,
                    description="Form kedaluwarsa. Muat ulang halaman lalu coba lagi.",
                )
            if jobs.busy():
                flash("Ada proses berjalan. Tunggu sebelum mengubah data.", "error")
                return redirect(url_for("home"))
        if not jobs.busy():
            store.purge_expired()

    @app.after_request
    def no_browser_cache(response):
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.context_processor
    def context():
        return dict(
            csrf_token=session["csrf"],
            settings=store.settings(),
            data_location=str(store.root),
            key_present=bool(app.config["YOUTUBE_API_KEY"]),
            labels=["positive", "negative", "neutral"],
        )

    @app.errorhandler(ValueError)
    @app.errorhandler(PermissionError)
    @app.errorhandler(RuntimeError)
    @app.errorhandler(FileNotFoundError)
    def expected_error(error):
        message = str(error)
        key = app.config["YOUTUBE_API_KEY"]
        if key:
            message = message.replace(key, "[REDACTED]")
        return render_template("error.html", message=message), 400

    def allowed(operation):
        settings = store.settings()
        authorize(settings, settings, operation)
        return settings

    def api():
        return YouTube(app.config["YOUTUBE_API_KEY"])

    def start(title, function):
        return redirect(url_for("job_page", job_id=jobs.start(title, function)))

    def rows_for_run(run_id, filename):
        return read_csv(store.run_path(run_id) / filename)

    def save_run_json(run_id, filename, value):
        store.save_json(f"runs/{run_id}/{filename}", value)

    def invalidate_analysis(run_id):
        for filename in [
            "evaluation.json",
            "monthly.csv",
            "pairs.csv",
            "coverage.csv",
            "analysis.json",
            "forecast.json",
            "scatter.png",
        ]:
            (store.run_path(run_id) / filename).unlink(missing_ok=True)

    @app.get("/")
    def home():
        events = store.events()
        report = audit(events, store.settings(), read_csv(store.root / "coverage.csv"))
        return render_template(
            "home.html", events=events, runs=store.runs(), report=report
        )

    @app.get("/events")
    def events_page():
        return render_template("events.html", events=store.events())

    @app.post("/events")
    def add_event():
        event_id = store.add_event(
            request.form["link"], request.form.get("character_name", "")
        )
        flash(
            "Kandidat ditambahkan sebagai pending. Lengkapi verifikasi manusia.",
            "success",
        )
        return redirect(url_for("edit_event", event_id=event_id))

    @app.route("/events/<event_id>", methods=["GET", "POST"])
    def edit_event(event_id):
        event = store.event(event_id)
        if not event:
            abort(404)
        if request.method == "POST":
            fields = [
                "character_name",
                "announcement_source_url",
                "initial_announcement_at_utc",
                "content_type",
                "inclusion_status",
                "exclusion_reason",
                "verification_notes",
            ]
            changes = {k: request.form.get(k, "").strip() for k in fields}
            new_link = request.form.get("video_url", event["video_url"]).strip()
            new_id = video_id_from_input(new_link) if new_link else ""
            if new_id != event["video_id"]:
                if new_id and any(
                    r["video_id"] == new_id and r["event_id"] != event_id
                    for r in store.events()
                ):
                    raise ValueError("Video sudah dipakai kandidat lain.")
                changes.update({k: "" for k in API_FIELDS})
                changes.update(
                    video_id=new_id,
                    video_url=f"https://youtube.com/shorts/{new_id}" if new_id else "",
                    inclusion_status="pending",
                    content_type="",
                )
            merged = {**event, **changes}
            if changes["inclusion_status"] not in STATUSES:
                raise ValueError("Status tidak valid.")
            if changes["initial_announcement_at_utc"]:
                changes["initial_announcement_at_utc"] = utc(
                    changes["initial_announcement_at_utc"]
                ).isoformat()
            if changes["inclusion_status"] == "included":
                if event.get("official_channel_match") != "true" or not event.get(
                    "api_verified_at_utc"
                ):
                    raise ValueError(
                        "Ambil metadata API dan pastikan kanal resmi sebelum memilih included."
                    )
                check = audit([merged], store.settings(), [])
                if check["issues"]:
                    raise ValueError("; ".join(check["issues"]))
            if (
                changes["inclusion_status"] in {"excluded", "no_matching_short"}
                and not changes["exclusion_reason"]
            ):
                raise ValueError("Alasan pengecualian wajib diisi.")
            store.update_event(event_id, changes)
            flash(
                "Verifikasi manual disimpan. Dataset lama tetap memakai snapshot saat dikumpulkan.",
                "success",
            )
            return redirect(url_for("edit_event", event_id=event_id))
        return render_template("event.html", event=event)

    @app.post("/events/<event_id>/metadata")
    def event_metadata(event_id):
        settings = allowed("metadata_allowed")
        event = store.event(event_id)
        if not event:
            abort(404)
        client = api()

        def work(progress):
            progress("Mengambil videos.list dan channels.list...")
            metadata = client.metadata(event["video_id"])
            official = client.official_channel_id()
            verified = now_utc()
            changes = dict(
                channel_id=metadata["channel_id"],
                video_published_at_utc=metadata["video_published_at_utc"],
                api_title=metadata["title"],
                api_verified_at_utc=verified.isoformat(),
                api_expires_at_utc=(
                    verified + timedelta(days=settings["retention_days"])
                ).isoformat(),
                official_channel_match=str(metadata["channel_id"] == official).lower(),
            )
            if (
                (
                    event.get("channel_id")
                    and event["channel_id"] != changes["channel_id"]
                )
                or (
                    event.get("video_published_at_utc")
                    and utc(event["video_published_at_utc"])
                    != utc(changes["video_published_at_utc"])
                )
                or changes["official_channel_match"] == "false"
            ):
                changes["inclusion_status"] = "pending"
            store.update_event(event_id, changes)
            return "Metadata tersimpan. Penentuan drip marketing tetap manual."

        return start("Verifikasi metadata", work)

    @app.post("/events/<event_id>/delete")
    def delete_event(event_id):
        if request.form.get("confirm") != "yes":
            raise ValueError("Konfirmasi penghapusan diperlukan.")
        store.delete_event(event_id)
        flash(
            "Event dan seluruh dataset/turunan yang bergantung padanya dihapus.",
            "success",
        )
        return redirect(url_for("events_page"))

    @app.route("/coverage", methods=["GET", "POST"])
    def coverage_page():
        rows = read_csv(store.root / "coverage.csv")
        if request.method == "POST":
            for row in rows:
                month = row["month"]
                row.update(
                    discovery_status=request.form.get(month + "_status", "not_started"),
                    checked_at_utc=request.form.get(month + "_checked", "").strip(),
                    evidence_notes=request.form.get(month + "_notes", "").strip(),
                )
            report = audit([], store.settings(), rows)
            if report["issues"]:
                raise ValueError("; ".join(report["issues"]))
            store.save_csv("coverage.csv", rows)
            flash("Catatan pencarian per bulan disimpan.", "success")
            return redirect(url_for("coverage_page"))
        return render_template("coverage.html", coverage=rows)

    @app.route("/settings", methods=["GET", "POST"])
    def settings_page():
        if request.method == "POST":
            settings = store.settings()
            for name in [
                "dry_run",
                "metadata_allowed",
                "collection_allowed",
                "derived_analysis_allowed",
                "external_join_allowed",
            ]:
                settings[name] = request.form.get(name) == "on"
            settings["retention_days"] = int(request.form.get("retention_days", 30))
            if not 1 <= settings["retention_days"] <= 30:
                raise ValueError("Retensi harus 1–30 hari.")
            for name in ["policy_reviewed_at", "evidence_reference"]:
                settings[name] = request.form.get(name, "").strip()
            if settings["policy_reviewed_at"]:
                from datetime import date

                date.fromisoformat(settings["policy_reviewed_at"])
            settings["policy_review_status"] = (
                "documented"
                if settings["policy_reviewed_at"] and settings["evidence_reference"]
                else "reviewed"
            )
            if request.form.get("clear_key") == "on":
                app.config["YOUTUBE_API_KEY"] = ""
            elif request.form.get("api_key", "").strip():
                app.config["YOUTUBE_API_KEY"] = request.form["api_key"].strip()
            store.save_json("settings.json", settings)
            # Shorter retention applies immediately; never lengthen existing data lifetimes.
            limit = now_utc() + timedelta(days=settings["retention_days"])
            for run in store.runs():
                if utc(run["expires_at"]) > limit:
                    run["expires_at"] = limit.isoformat()
                    save_run_json(run["run_id"], "manifest.json", run)
            events = store.events()
            for event in events:
                if (
                    event.get("api_expires_at_utc")
                    and utc(event["api_expires_at_utc"]) > limit
                ):
                    event["api_expires_at_utc"] = limit.isoformat()
            store.save_events(events)
            flash(
                "Pengaturan disimpan. API key hanya di memori proses dan tidak ditulis ke disk.",
                "success",
            )
            return redirect(url_for("settings_page"))
        return render_template(
            "settings.html",
            model=dict(id=MODEL_ID, revision=MODEL_REVISION, license=MODEL_LICENSE),
        )

    @app.get("/datasets")
    def datasets_page():
        return render_template(
            "datasets.html",
            events=[r for r in store.events() if r["inclusion_status"] == "included"],
            runs=store.runs(),
        )

    @app.post("/datasets/collect")
    def collect_dataset():
        settings = allowed("collection_allowed")
        events = sorted(
            [r for r in store.events() if r["inclusion_status"] == "included"],
            key=lambda r: r["video_published_at_utc"],
        )
        if not events:
            raise ValueError("Belum ada event included.")
        report = audit(events, settings, [])
        if report["issues"]:
            raise ValueError("; ".join(report["issues"]))
        if request.form.get("mode") == "pilot":
            if len(events) < 6:
                raise ValueError(
                    "Pilot temporal membutuhkan setidaknya enam event. Pilih semua untuk uji kecil."
                )
            n = min(8, len(events))
            events = [events[round(i * (len(events) - 1) / (n - 1))] for i in range(n)]
        client = api()

        def work(progress):
            official = client.official_channel_id()
            for event in events:
                metadata = client.metadata(event["video_id"])
                if metadata["channel_id"] != official or utc(
                    metadata["video_published_at_utc"]
                ) != utc(event["video_published_at_utc"]):
                    raise ValueError(
                        "Metadata event berubah atau kanal bukan resmi. Verifikasi ulang registry."
                    )
                if (
                    utc(event["video_published_at_utc"])
                    + timedelta(hours=settings["window_hours"])
                    > now_utc()
                ):
                    raise ValueError(
                        "Jendela 72 jam belum selesai untuk salah satu event."
                    )
            run_id = store.new_run(events)
            all_rows, statuses = [], []
            for event in events:

                def checkpoint(rows, status):
                    store.save_csv(
                        f"runs/{run_id}/comments.csv", all_rows + rows, COMMENT_FIELDS
                    )
                    save_run_json(
                        run_id, "collection_status.json", statuses + [dict(status)]
                    )

                rows, status = collect_event(
                    client,
                    event,
                    settings["window_hours"],
                    checkpoint=checkpoint,
                    progress=progress,
                )
                all_rows.extend(rows)
                statuses.append(status)
            if len({r["comment_id"] for r in all_rows}) != len(all_rows):
                raise ValueError("ID komentar lintas event duplikat.")
            manifest = store.manifest(run_id)
            manifest["collection_complete"] = all(
                s["pagination_complete"] for s in statuses
            )
            manifest["registry_fingerprint"] = store.fingerprint(events)
            save_run_json(run_id, "manifest.json", manifest)
            return f"Dataset {run_id}: {len(all_rows)} komentar unik; pagination lengkap={manifest['collection_complete']}."

        return start("Pengumpulan komentar", work)

    @app.get("/datasets/<run_id>")
    def dataset_page(run_id):
        manifest = store.manifest(run_id)
        path = store.run_path(run_id)
        reports = {
            name: read_json(path / (name + ".json"))
            if (path / (name + ".json")).exists()
            else None
            for name in ["exclusions", "evaluation", "analysis", "forecast"]
        }
        statuses = (
            read_json(path / "collection_status.json")
            if (path / "collection_status.json").exists()
            else []
        )
        snapshot = read_csv(path / "events.csv")
        current = [store.event(row["event_id"]) for row in snapshot]
        changed = current != snapshot
        return render_template(
            "dataset.html",
            run=manifest,
            reports=reports,
            statuses=statuses,
            changed=changed,
            files=[p.name for p in path.iterdir() if p.is_file()],
        )

    @app.post("/datasets/<run_id>/delete")
    def delete_dataset(run_id):
        if request.form.get("confirm") != "yes":
            raise ValueError("Konfirmasi penghapusan diperlukan.")
        shutil.rmtree(store.run_path(run_id))
        flash("Dataset dan seluruh turunannya dihapus.", "success")
        return redirect(url_for("datasets_page"))

    @app.post("/datasets/<run_id>/nlp")
    def run_nlp(run_id):
        allowed("derived_analysis_allowed")
        store.require_run(run_id)

        def work(progress):
            manifest = store.manifest(run_id)
            manifest["nlp_complete"] = False
            save_run_json(run_id, "manifest.json", manifest)
            progress(
                "Mendeteksi bahasa; model pertama kali dapat memerlukan unduhan besar..."
            )
            rows = infer(
                preprocess(rows_for_run(run_id, "comments.csv")), progress=progress
            )
            fields = list(
                dict.fromkeys(
                    COMMENT_FIELDS
                    + [
                        "normalized_text",
                        "duplicate_text_flag",
                        "spam_review_flag",
                        "sentiment",
                        "sentiment_score",
                        "truncated_for_model",
                        "model_id",
                        "model_revision",
                        "model_license",
                    ]
                    + [k for row in rows for k in row]
                )
            )
            store.save_csv(
                f"runs/{run_id}/predictions.csv",
                [{k: r.get(k, "") for k in fields} for r in rows],
                fields,
            )
            invalidate_analysis(run_id)
            save_run_json(run_id, "exclusions.json", exclusion_report(rows))
            manifest.update(
                nlp_complete=True,
                predicted_at_utc=now_utc().isoformat(),
                model_id=MODEL_ID,
                model_revision=MODEL_REVISION,
                model_license=MODEL_LICENSE,
            )
            save_run_json(run_id, "manifest.json", manifest)
            return "NLP selesai. Prediksi belum menjadi ground truth; lanjut anotasi dan evaluasi."

        return start("Inferensi sentimen lokal", work)

    def require_predictions(run_id):
        manifest = store.require_run(run_id, predictions=True)
        if not manifest.get("nlp_complete"):
            raise ValueError(
                "NLP belum selesai/percobaan terakhir gagal. Jalankan ulang."
            )
        return manifest

    @app.route("/datasets/<run_id>/annotations", methods=["GET", "POST"])
    def annotations_page(run_id):
        allowed("derived_analysis_allowed")
        require_predictions(run_id)
        path = store.run_path(run_id) / "annotations.csv"
        if request.method == "POST":
            if not path.exists():
                sample = annotation_sample(
                    rows_for_run(run_id, "predictions.csv"),
                    rows_for_run(run_id, "events.csv"),
                )
                if not sample:
                    raise ValueError("Tidak ada komentar eligible untuk dianotasi.")
                store.save_csv(f"runs/{run_id}/annotations.csv", sample)
            elif request.files.get("file") and request.files["file"].filename:
                uploaded = parse_csv(request.files["file"].read())
                if not uploaded or not all("comment_id" in r for r in uploaded):
                    raise ValueError("CSV anotasi kosong/tanpa ID.")
                existing = {
                    r["comment_id"]: r for r in rows_for_run(run_id, "annotations.csv")
                }
                if len({r["comment_id"] for r in uploaded}) != len(uploaded) or any(
                    r["comment_id"] not in existing for r in uploaded
                ):
                    raise ValueError(
                        "Impor anotasi hanya boleh memuat ID unik dari sampel yang sama."
                    )
                for row in uploaded:
                    existing[row["comment_id"]].update(
                        {
                            k: row.get(k, "")
                            for k in [
                                "annotator_1",
                                "annotator_2",
                                "ambiguous",
                                "off_topic",
                                "adjudicated_label",
                                "annotation_notes",
                            ]
                        }
                    )
                store.save_csv(f"runs/{run_id}/annotations.csv", existing.values())
                invalidate_analysis(run_id)
            else:
                rows = rows_for_run(run_id, "annotations.csv")
                for row in rows:
                    if row["comment_id"] in request.form.getlist("comment_id"):
                        for field in [
                            "annotator_1",
                            "annotator_2",
                            "ambiguous",
                            "off_topic",
                            "adjudicated_label",
                            "annotation_notes",
                        ]:
                            value = request.form.get(
                                row["comment_id"] + "_" + field, ""
                            ).strip()
                            if (
                                field
                                in ["annotator_1", "annotator_2", "adjudicated_label"]
                                and value
                                and value not in ["positive", "negative", "neutral"]
                            ):
                                raise ValueError("Label tidak valid.")
                            row[field] = value
                store.save_csv(f"runs/{run_id}/annotations.csv", rows)
                invalidate_analysis(run_id)
            return redirect(
                url_for(
                    "annotations_page", run_id=run_id, page=request.args.get("page", 1)
                )
            )
        rows = rows_for_run(run_id, "annotations.csv") if path.exists() else []
        page = max(1, int(request.args.get("page", 1)))
        return render_template(
            "annotations.html",
            run_id=run_id,
            rows=rows[(page - 1) * 20 : page * 20],
            page=page,
            total=len(rows),
        )

    @app.post("/datasets/<run_id>/evaluate")
    def run_evaluation(run_id):
        allowed("derived_analysis_allowed")
        require_predictions(run_id)
        report = evaluate(
            rows_for_run(run_id, "annotations.csv"),
            rows_for_run(run_id, "predictions.csv"),
        )
        save_run_json(run_id, "evaluation.json", report)
        flash("Evaluasi label manual selesai.", "success")
        return redirect(url_for("dataset_page", run_id=run_id))

    @app.route("/revenue", methods=["GET", "POST"])
    def revenue_page():
        path = store.root / "revenue.csv"
        rows = read_csv(path) if path.exists() else []
        if request.method == "POST":
            if request.files.get("file") and request.files["file"].filename:
                if request.form.get("replace_confirm") != "yes":
                    raise ValueError("Konfirmasi penggantian seri revenue diperlukan.")
                rows = parse_csv(request.files["file"].read())
            else:
                row = {k: request.form.get(k, "").strip() for k in REVENUE_FIELDS}
                rows = [r for r in rows if r["month"] != row["month"]] + [row]
            validate_revenue(rows)
            store.save_csv(
                "revenue.csv", sorted(rows, key=lambda r: r["month"]), REVENUE_FIELDS
            )
            # Prior results must not survive a changed external series.
            for run in store.runs():
                for filename in [
                    "analysis.json",
                    "forecast.json",
                    "monthly.csv",
                    "pairs.csv",
                    "coverage.csv",
                    "scatter.png",
                ]:
                    (store.run_path(run["run_id"]) / filename).unlink(missing_ok=True)
            flash(
                "Revenue disimpan; analisis lama dibatalkan agar tidak memakai seri usang.",
                "success",
            )
            return redirect(url_for("revenue_page"))
        selected = next(
            (r for r in rows if r["month"] == request.args.get("month")), {}
        )
        return render_template(
            "revenue.html", rows=rows, fields=REVENUE_FIELDS, selected=selected
        )

    @app.get("/revenue/template")
    def revenue_template():
        return send_file(
            io.BytesIO(csv_text([], REVENUE_FIELDS).encode()),
            mimetype="text/csv",
            as_attachment=True,
            download_name="revenue-template.csv",
        )

    @app.post("/datasets/<run_id>/analyze")
    def run_analysis(run_id):
        allowed("derived_analysis_allowed")
        allowed("external_join_allowed")
        manifest = require_predictions(run_id)
        evaluation_path = store.run_path(run_id) / "evaluation.json"
        if not evaluation_path.exists():
            raise ValueError(
                "Lakukan evaluasi label manual sebelum analisis hubungan revenue."
            )
        revenue = (
            read_csv(store.root / "revenue.csv")
            if (store.root / "revenue.csv").exists()
            else []
        )

        def work(progress):
            progress("Mengagregasi berdasarkan akhir jendela 72 jam...")
            for filename in ["analysis.json", "forecast.json", "scatter.png"]:
                (store.run_path(run_id) / filename).unlink(missing_ok=True)
            monthly = aggregate(
                rows_for_run(run_id, "events.csv"),
                rows_for_run(run_id, "predictions.csv"),
                manifest["window_hours"],
            )
            pairs, coverage = pair_months(monthly, revenue)
            store.save_csv(f"runs/{run_id}/monthly.csv", monthly)
            store.save_csv(
                f"runs/{run_id}/pairs.csv",
                pairs,
                [
                    "month",
                    "event_count",
                    "comment_count",
                    "positive_proportion",
                    "negative_proportion",
                    "neutral_proportion",
                    "net_sentiment",
                    "revenue_month",
                    "revenue_usd",
                    "available_at_utc",
                ],
            )
            store.save_csv(f"runs/{run_id}/coverage.csv", coverage)
            store.save_csv(f"runs/{run_id}/revenue.csv", revenue, REVENUE_FIELDS)
            report = spearman(pairs)
            report["manual_evaluation"] = read_json(evaluation_path)
            report["analyzed_at_utc"] = now_utc().isoformat()
            report["source_scope"] = (
                {
                    k: revenue[0].get(k, "")
                    for k in [
                        "platform_scope",
                        "region_scope",
                        "cn_android_included",
                        "cn_android_multiplier",
                        "source_url",
                    ]
                }
                if revenue
                else None
            )
            report["forecasting"] = (
                "Eksperimen terpisah; tidak otomatis dibuat dari korelasi."
            )
            scatter(pairs, store.run_path(run_id) / "scatter.png")
            save_run_json(run_id, "analysis.json", report)
            (store.run_path(run_id) / "forecast.json").unlink(missing_ok=True)
            return f"Analisis selesai: {len(pairs)} pasangan bulanan aktual."

        return start("Analisis bulanan", work)

    @app.post("/datasets/<run_id>/forecast")
    def run_forecast(run_id):
        allowed("derived_analysis_allowed")
        allowed("external_join_allowed")
        require_predictions(run_id)
        path = store.run_path(run_id)
        if not (path / "analysis.json").exists():
            raise ValueError("Jalankan analisis bulanan dahulu.")
        report = audit(
            store.events(), store.settings(), read_csv(store.root / "coverage.csv")
        )
        complete = (
            not report["issues"]
            and not report["pending_events"]
            and all(v == "completed" for v in report["discovery_by_month"].values())
        )

        def work(progress):
            progress("Memeriksa data dan menjalankan hindcast berurutan waktu...")
            # Read CSV numerics explicitly; blanks mean missing, never zero sentiment.
            monthly = rows_for_run(run_id, "monthly.csv")
            for row in monthly:
                row["net_sentiment"] = (
                    float(row["net_sentiment"]) if row["net_sentiment"] != "" else None
                )
            pairs = rows_for_run(run_id, "pairs.csv")
            for row in pairs:
                row["net_sentiment"] = float(row["net_sentiment"])
                row["revenue_usd"] = float(row["revenue_usd"])
            result = forecast(monthly, pairs, discovery_complete=complete)
            save_run_json(run_id, "forecast.json", result)
            return "Pemeriksaan forecasting selesai. Baca status, alasan pembatasan dan peringatan pada dataset."

        return start("Forecasting eksperimental", work)

    @app.get("/datasets/<run_id>/files/<filename>")
    def run_file(run_id, filename):
        allowed_files = {
            "manifest.json",
            "events.csv",
            "comments.csv",
            "collection_status.json",
            "predictions.csv",
            "exclusions.json",
            "annotations.csv",
            "evaluation.json",
            "monthly.csv",
            "pairs.csv",
            "coverage.csv",
            "analysis.json",
            "forecast.json",
            "scatter.png",
            "revenue.csv",
        }
        if filename not in allowed_files:
            abort(404)
        path = store.run_path(run_id) / filename
        if not path.exists():
            abort(404)
        return send_file(
            path, as_attachment=filename != "scatter.png", download_name=filename
        )

    @app.get("/events/export")
    def export_events():
        return send_file(
            store.root / "events.csv", as_attachment=True, download_name="events.csv"
        )

    @app.get("/jobs/<job_id>")
    def job_page(job_id):
        job = jobs.get(job_id)
        if not job:
            abort(404)
        return render_template("job.html", job=job, job_id=job_id)

    @app.get("/jobs/<job_id>/status")
    def job_status(job_id):
        job = jobs.get(job_id)
        if not job:
            abort(404)
        return jsonify(job)

    return app
