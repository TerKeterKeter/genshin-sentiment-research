"""Monthly observational analysis. Never treat comments as revenue observations."""

import math
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from .core import utc
from .sentiment import LABELS

REVENUE_FIELDS = [
    "month",
    "revenue_usd",
    "platform_scope",
    "region_scope",
    "cn_android_included",
    "cn_android_multiplier",
    "source_url",
    "retrieved_at",
    "revision_notes",
    "available_at_utc",
]


def next_month(month):
    year, number = map(int, month.split("-"))
    return f"{year + (number == 12):04d}-{number % 12 + 1:02d}"


def validate_revenue(rows):
    from urllib.parse import urlsplit

    seen, scopes, sources = set(), set(), set()
    for row in rows:
        required = REVENUE_FIELDS[:-1]
        if any(k not in row for k in required):
            raise ValueError("Kolom revenue CSV tidak lengkap.")
        month = row["month"]
        if date.fromisoformat(month + "-01").strftime("%Y-%m") != month:
            raise ValueError("Format bulan harus YYYY-MM.")
        if month in seen:
            raise ValueError("Bulan revenue duplikat. Pilih satu revisi per bulan.")
        seen.add(month)
        if not all(
            row[k].strip()
            for k in ["platform_scope", "region_scope", "source_url", "retrieved_at"]
        ):
            raise ValueError("Cakupan dan provenance revenue wajib diisi.")
        if row["cn_android_included"] not in ["true", "false", "unknown"]:
            raise ValueError("CN Android: gunakan true, false, atau unknown.")
        if row["revenue_usd"]:
            value = float(row["revenue_usd"])
            if not math.isfinite(value) or value < 0:
                raise ValueError("Revenue harus angka USD nonnegatif atau kosong.")
        if row["cn_android_multiplier"]:
            multiplier = float(row["cn_android_multiplier"])
            if (
                not math.isfinite(multiplier)
                or multiplier <= 0
                or row["cn_android_included"] != "true"
            ):
                raise ValueError(
                    "Multiplier harus positif dan hanya untuk CN Android yang disertakan."
                )
        url = urlsplit(row["source_url"])
        if url.scheme != "https" or not url.hostname or url.username or url.password:
            raise ValueError("Gunakan URL sumber HTTPS publik tanpa kredensial.")
        if "T" in row["retrieved_at"]:
            utc(row["retrieved_at"])
        else:
            date.fromisoformat(row["retrieved_at"])
        if row.get("available_at_utc"):
            released = utc(row["available_at_utc"])
            if released < utc(next_month(month) + "-01T00:00:00Z"):
                raise ValueError(
                    "Revenue bulanan penuh tidak boleh tersedia sebelum bulannya selesai."
                )
        scopes.add(
            tuple(
                row[k]
                for k in [
                    "platform_scope",
                    "region_scope",
                    "cn_android_included",
                    "cn_android_multiplier",
                ]
            )
        )
        sources.add(row["source_url"])
    if len(scopes) > 1 or len(sources) > 1:
        raise ValueError(
            "Gunakan satu seri sumber dan cakupan konsisten; jangan campur wilayah/platform/multiplier."
        )
    return rows


def aggregate(events, comments, hours=72):
    groups = defaultdict(lambda: dict(events=set(), comments=[]))
    event_month = {}
    for event in events:
        month = (
            utc(event["video_published_at_utc"]) + timedelta(hours=hours)
        ).strftime("%Y-%m")
        event_month[event["event_id"]] = month
        groups[month]["events"].add(event["event_id"])
    seen = set()
    for row in comments:
        if row["comment_id"] in seen:
            raise ValueError("ID komentar duplikat pada input analisis.")
        seen.add(row["comment_id"])
        if row["event_id"] not in event_month:
            raise ValueError("Komentar tidak cocok dengan snapshot event.")
        if row["eligibility_status"] == "eligible" and row.get("sentiment") in LABELS:
            groups[event_month[row["event_id"]]]["comments"].append(row)
    output = []
    for month, group in sorted(groups.items()):
        n = len(group["comments"])
        row = dict(month=month, event_count=len(group["events"]), comment_count=n)
        for label in LABELS:
            row[label + "_proportion"] = (
                sum(c["sentiment"] == label for c in group["comments"]) / n
                if n
                else None
            )
        row["net_sentiment"] = (
            row["positive_proportion"] - row["negative_proportion"] if n else None
        )
        output.append(row)
    return output


def pair_months(monthly, revenue, as_of=None):
    as_of = as_of or datetime.now(timezone.utc)
    validate_revenue(revenue)
    lookup = {r["month"]: r for r in revenue}
    pairs, coverage = [], []
    for row in monthly:
        target = next_month(row["month"])
        revenue_row = lookup.get(target)
        complete = utc(next_month(target) + "-01T00:00:00Z") <= as_of
        reason = "paired"
        if row["net_sentiment"] is None:
            reason = "no_eligible_comments"
        elif not complete:
            reason = "revenue_month_not_complete"
        elif not revenue_row or revenue_row["revenue_usd"] == "":
            reason = "revenue_missing"
        elif (
            revenue_row.get("available_at_utc")
            and utc(revenue_row["available_at_utc"]) > as_of
        ):
            reason = "source_not_available_as_of"
        coverage.append(dict(month=row["month"], revenue_month=target, status=reason))
        if reason == "paired":
            pairs.append(
                {
                    **row,
                    "revenue_month": target,
                    "revenue_usd": float(revenue_row["revenue_usd"]),
                    "available_at_utc": revenue_row.get("available_at_utc", ""),
                }
            )
    return pairs, coverage


def spearman(pairs):
    from scipy.stats import spearmanr

    x, y = [r["net_sentiment"] for r in pairs], [r["revenue_usd"] for r in pairs]
    report = dict(
        actual_pair_count=len(pairs),
        spearman_rho=None,
        p_value=None,
        limitation="Eksploratif, bukan kausal. Tren, update, rerun, serial dependence dan beda cakupan dapat memengaruhi hasil.",
    )
    if len(pairs) < 3 or len(set(x)) < 2 or len(set(y)) < 2:
        report["status"] = "insufficient_or_constant_data"
    else:
        rho, p = spearmanr(x, y)
        report.update(status="exploratory", spearman_rho=float(rho), p_value=float(p))
    return report


def scatter(pairs, path):
    import os
    from pathlib import Path

    os.environ.setdefault("MPLCONFIGDIR", str(Path("data/plot_cache").resolve()))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 5))
    for row in pairs:
        ax.scatter(row["net_sentiment"], row["revenue_usd"])
        ax.annotate(
            row["month"], (row["net_sentiment"], row["revenue_usd"]), fontsize=8
        )
    ax.set(
        xlabel="Net sentiment: month t (72h window end)",
        ylabel="Third-party mobile revenue estimate USD: t+1",
        title="Exploratory monthly association — not causal",
    )
    if not pairs:
        ax.text(
            0.5, 0.5, "No matched monthly pairs", ha="center", transform=ax.transAxes
        )
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def forecast(monthly, pairs, as_of=None, discovery_complete=False):
    """Experimental Ridge, chronological hindcast and naive baseline; never random CV."""
    from sklearn.linear_model import Ridge
    from sklearn.metrics import mean_absolute_error
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    as_of = as_of or datetime.now(timezone.utc)
    ordered = sorted(pairs, key=lambda r: r["month"])
    result = dict(
        status="blocked",
        training_pairs=len(ordered),
        minimum_pairs=8,
        warning="Eksperimen berisiko tinggi dengan sampel kecil; bukan saran finansial atau bukti kausal. "
        "Backtest merupakan hindcast retrospektif, bukan rekonstruksi komentar/akurasi real-time. "
        "Ambang delapan pasangan adalah pemeriksaan teknis, bukan jaminan power statistik.",
        reasons=[],
        folds=[],
    )
    if any(
        utc(next_month(r["revenue_month"]) + "-01T00:00:00Z") > as_of
        or (r.get("available_at_utc") and utc(r["available_at_utc"]) > as_of)
        for r in ordered
    ):
        result["reasons"].append(
            "Target training belum selesai/tersedia pada tanggal analisis."
        )
    if any(r["revenue_month"] != next_month(r["month"]) for r in ordered):
        result["reasons"].append("Pemetaan target harus tepat bulan t+1.")
    if len(ordered) < 8:
        result["reasons"].append("Butuh minimal 8 pasangan bulanan lengkap.")
    if not discovery_complete:
        result["reasons"].append(
            "Selesaikan penelusuran seluruh periode dan kandidat pending dahulu."
        )
    if any(not r.get("available_at_utc") for r in ordered):
        result["reasons"].append(
            "Forecast memerlukan available_at_utc revenue yang terdokumentasi; tanggal retrieval tidak menggantikannya."
        )
    if any(next_month(a["month"]) != b["month"] for a, b in zip(ordered, ordered[1:])):
        result["reasons"].append(
            "Pasangan bulanan harus berurutan tanpa gap untuk eksperimen ini."
        )
    if len({r["net_sentiment"] for r in ordered}) < 2:
        result["reasons"].append("Fitur sentimen konstan/tidak tersedia.")
    if result["reasons"]:
        return result
    # At each origin, only use revenue targets released before the held-out target month.
    for test in ordered:
        origin = utc(test["revenue_month"] + "-01T00:00:00Z")
        train = [
            r
            for r in ordered
            if r["month"] < test["month"] and utc(r["available_at_utc"]) <= origin
        ]
        if len(train) < 4:
            continue
        model = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
        model.fit(
            [[r["net_sentiment"]] for r in train], [r["revenue_usd"] for r in train]
        )
        prediction = max(0.0, float(model.predict([[test["net_sentiment"]]])[0]))
        baseline = train[-1]["revenue_usd"]
        result["folds"].append(
            dict(
                month=test["month"],
                target_month=test["revenue_month"],
                actual=test["revenue_usd"],
                ridge=prediction,
                naive=baseline,
                n_train=len(train),
            )
        )
    if len(result["folds"]) < 3:
        result["reasons"].append(
            "Kurang dari 3 origin evaluasi dengan target training yang tersedia pada waktunya."
        )
        return result
    result["ridge_mae"] = float(
        mean_absolute_error(
            [r["actual"] for r in result["folds"]],
            [r["ridge"] for r in result["folds"]],
        )
    )
    result["naive_mae"] = float(
        mean_absolute_error(
            [r["actual"] for r in result["folds"]],
            [r["naive"] for r in result["folds"]],
        )
    )
    result["beats_naive_on_hindcast"] = result["ridge_mae"] < result["naive_mae"]
    if not result["beats_naive_on_hindcast"]:
        result["reasons"].append(
            "Ridge tidak mengalahkan baseline naif pada hindcast; jangan mengklaim peningkatan prediksi."
        )
    result["status"] = "hindcast_only"
    latest = max(
        (r for r in monthly if r["net_sentiment"] is not None),
        key=lambda r: r["month"],
        default=None,
    )
    if not latest:
        return result
    if utc(latest["month"] + "-01T00:00:00Z") > as_of:
        result["reasons"].append(
            "Fitur bulan terbaru berasal dari masa depan; proyeksi tidak dibuat."
        )
        return result
    target = next_month(latest["month"])
    if (
        any(r["revenue_month"] == target for r in ordered)
        or utc(next_month(target) + "-01T00:00:00Z") <= as_of
    ):
        result["reasons"].append(
            "Target terbaru sudah diketahui/berlalu; tidak diberi label prediksi masa depan."
        )
        return result
    model = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
    model.fit(
        [[r["net_sentiment"]] for r in ordered], [r["revenue_usd"] for r in ordered]
    )
    result.update(
        status="experimental_projection",
        target_month=target,
        projection_kind="forecast"
        if utc(target + "-01T00:00:00Z") > as_of
        else "nowcast_bulan_berjalan",
        projected_revenue_usd=max(
            0.0, float(model.predict([[latest["net_sentiment"]]])[0])
        ),
        naive_revenue_usd=ordered[-1]["revenue_usd"],
    )
    return result
