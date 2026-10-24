import re
import random
import unicodedata
from collections import Counter, defaultdict
from datetime import timedelta
from .core import utc


def normalize(text):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', text)).strip()


def preprocess(rows, language='en'):
    from langdetect import detect, DetectorFactory, LangDetectException
    DetectorFactory.seed = 42
    counts = Counter(normalize(r['text_display']).casefold() for r in rows)
    result = []
    for original in rows:
        row = dict(original)
        row['normalized_text'] = normalize(row['text_display'])
        try:
            row['language'] = detect(row['normalized_text'])
        except LangDetectException:
            row['language'] = 'und'
        row['duplicate_text_flag'] = counts[row['normalized_text'].casefold()] > 1
        row['spam_review_flag'] = bool(re.search(r'https?://|(.)\1{7,}', row['normalized_text']))
        if row['eligibility_status'] == 'eligible' and row['language'] != language:
            row.update(eligibility_status='excluded', exclusion_reason='non_english_or_undetermined')
        result.append(row)
    return result


def infer(rows, config):
    from transformers import pipeline
    if not config['model_revision'] or config['model_license'].startswith('REQUIRES'):
        raise ValueError('Verify model card license, labels and immutable revision before inference')
    classifier = pipeline('sentiment-analysis', model=config['model_id'],
                          revision=config['model_revision'], device=-1)
    output = []
    for original in rows:
        row = dict(original)
        if row['eligibility_status'] == 'eligible':
            # RoBERTa maximum input length: long comments are explicitly flagged.
            length = len(classifier.tokenizer(row['normalized_text'], add_special_tokens=True)['input_ids'])
            row['truncated_for_model'] = length > 512
            pred = classifier(row['normalized_text'], truncation=True, max_length=512)[0]
            row.update(sentiment=config['label_mapping'][pred['label'].lower()],
                       score=pred['score'], model_id=config['model_id'], model_revision=config['model_revision'])
        output.append(row)
    return output


def annotation_sample(rows, events, n=200, seed=42):
    starts = {e['event_id']: utc(e['video_published_at_utc']) for e in events}
    groups = defaultdict(list)
    for row in rows:
        if row['eligibility_status'] == 'eligible':
            interval = int((utc(row['published_at_utc']) - starts[row['event_id']]).total_seconds() // 86400)
            groups[(row['event_id'], interval)].append(row)
    rng = random.Random(seed)
    for key in sorted(groups):
        group = groups[key]
        group.sort(key=lambda r: r['comment_id'])
        rng.shuffle(group)
    selected = []
    keys = sorted(groups)
    while len(selected) < n and any(groups.values()):
        for key in keys:
            if groups[key] and len(selected) < n:
                row = groups[key].pop()
                selected.append({'comment_id': row['comment_id'], 'event_id': row['event_id'],
                                 'text_display': row.get('text_display', ''),
                                 'interval_24h': key[1], 'annotator_1': '',
                                 'annotator_2': '', 'ambiguous': '', 'off_topic': '', 'adjudicated_label': ''})
    return selected


def evaluate(rows):
    from sklearn.metrics import f1_score, confusion_matrix, cohen_kappa_score
    labels = ['positive', 'negative', 'neutral']
    labeled = [r for r in rows if r.get('adjudicated_label') in labels and r.get('sentiment') in labels]
    if not labeled:
        raise ValueError('No manual gold labels paired with model predictions')
    gold = [r['adjudicated_label'] for r in labeled]
    pred = [r['sentiment'] for r in labeled]
    both = [r for r in rows if r.get('annotator_1') in labels and r.get('annotator_2') in labels]
    return {'n': len(labeled), 'labels': labels,
            'macro_f1': float(f1_score(gold, pred, labels=labels, average='macro', zero_division=0)),
            'confusion_matrix': confusion_matrix(gold, pred, labels=labels).tolist(),
            'unscored_rows': len(rows) - len(labeled),
            'agreement_n': len(both),
            'cohen_kappa': float(cohen_kappa_score([r['annotator_1'] for r in both],
                                                 [r['annotator_2'] for r in both])) if both and len({r['annotator_1'] for r in both} | {r['annotator_2'] for r in both}) > 1 else None}
