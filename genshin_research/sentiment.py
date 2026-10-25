"""Reproducible local pretrained inference; predictions are not ground truth."""

import hashlib
import os
import random
import re
import unicodedata
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

from .core import utc

MODEL_ID = "cardiffnlp/twitter-roberta-base-sentiment-latest"
MODEL_REVISION = "3216a57f2a0d9c45a2e6c20157c20c49fb4bf9c7"
MODEL_LICENSE = "cc-by-4.0"
MODEL_SHA256 = "4d24a3e32a88ed1c4e5b789fc6644e2e767500554e954b27dccf52a8e762cbae"
LABELS = ["positive", "negative", "neutral"]


def normalize(text):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def preprocess(rows):
    from langdetect import DetectorFactory, LangDetectException, detect

    DetectorFactory.seed = 42
    counts = Counter(normalize(r["text_display"]).casefold() for r in rows)
    output = []
    for original in rows:
        row = dict(original)
        text = normalize(row["text_display"])
        try:
            language = detect(text)
        except LangDetectException:
            language = "und"
        row.update(
            normalized_text=text,
            language=language,
            duplicate_text_flag=counts[text.casefold()] > 1,
            spam_review_flag=bool(re.search(r"https?://|(.)\1{7,}", text)),
        )
        if row["eligibility_status"] == "eligible" and language != "en":
            row.update(
                eligibility_status="excluded",
                exclusion_reason="non_english_or_undetermined",
            )
        output.append(row)
    return output


@lru_cache(maxsize=1)
def classifier():
    os.environ.setdefault("HF_HOME", str(Path("data/model_cache").resolve()))
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    import torch
    from huggingface_hub import hf_hub_download

    torch.set_num_threads(min(4, os.cpu_count() or 1))
    from transformers import pipeline

    try:
        weights = hf_hub_download(
            MODEL_ID, "pytorch_model.bin", revision=MODEL_REVISION
        )
        checksum = hashlib.sha256()
        with open(weights, "rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                checksum.update(chunk)
        if checksum.hexdigest() != MODEL_SHA256:
            raise RuntimeError(
                "Checksum model tidak cocok; hentikan penggunaan cache model dan unduh ulang dari sumber resmi."
            )
        return pipeline(
            "sentiment-analysis",
            model=MODEL_ID,
            revision=MODEL_REVISION,
            tokenizer=MODEL_ID,
            device=-1,
            model_kwargs={"use_safetensors": False},
        )
    except (OSError, ValueError):
        raise RuntimeError(
            "Model belum dapat dimuat. Periksa instalasi requirements, ruang disk dan akses huggingface.co serta CDN bobotnya (termasuk us.aws.cdn.hf.co). Unduhan pertama sekitar 500 MB; TLS/checksum tidak dinonaktifkan."
        ) from None


def infer(rows, progress=lambda text: None, model=None):
    eligible = [r for r in rows if r["eligibility_status"] == "eligible"]
    if not eligible:
        return [dict(r) for r in rows]
    model = model or classifier()
    predicted = {}
    for start in range(0, len(eligible), 16):
        batch = eligible[start : start + 16]
        texts = [r["normalized_text"] for r in batch]
        predictions = model(texts, truncation=True, max_length=512, batch_size=16)
        for row, prediction in zip(batch, predictions, strict=True):
            label = prediction["label"].lower()
            if label not in LABELS:
                raise ValueError("Pemetaan label model tidak cocok dengan model card.")
            length = len(
                model.tokenizer(row["normalized_text"], add_special_tokens=True)[
                    "input_ids"
                ]
            )
            predicted[row["comment_id"]] = dict(
                sentiment=label,
                sentiment_score=prediction["score"],
                truncated_for_model=length > 512,
                model_id=MODEL_ID,
                model_revision=MODEL_REVISION,
                model_license=MODEL_LICENSE,
            )
        progress(
            f"NLP: {min(start + 16, len(eligible))}/{len(eligible)} komentar eligible"
        )
    return [{**r, **predicted.get(r["comment_id"], {})} for r in rows]


def exclusion_report(rows):
    sentiment_counts = dict(
        Counter(
            r["sentiment"]
            for r in rows
            if r.get("sentiment") in LABELS and r["eligibility_status"] == "eligible"
        )
    )
    return dict(
        total=len(rows),
        sentiment_counts={label: sentiment_counts.get(label, 0) for label in LABELS},
        eligible=sum(r["eligibility_status"] == "eligible" for r in rows),
        exclusion_reasons=dict(
            Counter(
                r["exclusion_reason"]
                for r in rows
                if r["eligibility_status"] != "eligible"
            )
        ),
        languages=dict(Counter(r["language"] for r in rows)),
        excluded_languages=dict(
            Counter(
                r["language"]
                for r in rows
                if r["exclusion_reason"] == "non_english_or_undetermined"
            )
        ),
        duplicate_text_flags=sum(
            str(r.get("duplicate_text_flag", "")).lower() == "true" for r in rows
        ),
        spam_review_flags=sum(
            str(r.get("spam_review_flag", "")).lower() == "true" for r in rows
        ),
        truncated_inputs=sum(
            str(r.get("truncated_for_model", "")).lower() == "true" for r in rows
        ),
    )


def annotation_sample(rows, events, n=200, seed=42):
    starts = {r["event_id"]: utc(r["video_published_at_utc"]) for r in events}
    groups = defaultdict(list)
    for row in rows:
        if row["eligibility_status"] == "eligible":
            interval = int(
                (utc(row["published_at_utc"]) - starts[row["event_id"]]).total_seconds()
                // 86400
            )
            groups[(row["event_id"], interval)].append(row)
    rng = random.Random(seed)
    for key in sorted(groups):
        groups[key].sort(key=lambda r: r["comment_id"])
        rng.shuffle(groups[key])
    result = []
    while len(result) < n and any(groups.values()):
        for key in sorted(groups):
            if groups[key] and len(result) < n:
                row = groups[key].pop()
                result.append(
                    dict(
                        comment_id=row["comment_id"],
                        event_id=row["event_id"],
                        interval_24h=key[1],
                        text_display=row["text_display"],
                        annotator_1="",
                        annotator_2="",
                        ambiguous="",
                        off_topic="",
                        adjudicated_label="",
                        annotation_notes="",
                    )
                )
    return result


def evaluate(annotations, predictions):
    from sklearn.metrics import cohen_kappa_score, confusion_matrix, f1_score

    lookup = {r["comment_id"]: r for r in predictions}
    ids = [r["comment_id"] for r in annotations]
    if len(ids) != len(set(ids)) or any(cid not in lookup for cid in ids):
        raise ValueError("ID anotasi duplikat atau tidak cocok dengan dataset.")
    gold, pred, both = [], [], []
    for row in annotations:
        for field in ["annotator_1", "annotator_2", "adjudicated_label"]:
            if row.get(field) and row[field] not in LABELS:
                raise ValueError(
                    f"Label {field} tidak valid; gunakan positive, negative atau neutral."
                )
        if (
            row.get("adjudicated_label") in LABELS
            and lookup[row["comment_id"]].get("sentiment") in LABELS
        ):
            gold.append(row["adjudicated_label"])
            pred.append(lookup[row["comment_id"]]["sentiment"])
        if row.get("annotator_1") in LABELS and row.get("annotator_2") in LABELS:
            both.append((row["annotator_1"], row["annotator_2"]))
    if not gold:
        raise ValueError("Belum ada gold manual yang dapat dievaluasi.")
    kappa = None
    if both and len({v for pair in both for v in pair}) > 1:
        kappa = float(cohen_kappa_score([r[0] for r in both], [r[1] for r in both]))
    return dict(
        n=len(gold),
        unscored_rows=len(annotations) - len(gold),
        labels=LABELS,
        macro_f1=float(
            f1_score(gold, pred, labels=LABELS, average="macro", zero_division=0)
        ),
        confusion_matrix=confusion_matrix(gold, pred, labels=LABELS).tolist(),
        agreement_n=len(both),
        cohen_kappa=kappa,
    )
