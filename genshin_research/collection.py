"""Top-level comments only. Timestamp filtering is local, not an API parameter."""

from datetime import timedelta

from .core import utc
from .workbench import now_utc

COMMENT_FIELDS = [
    "comment_id",
    "video_id",
    "event_id",
    "text_display",
    "published_at_utc",
    "updated_at_utc",
    "collected_at_utc",
    "like_count_at_collection",
    "language",
    "eligibility_status",
    "exclusion_reason",
]


def eligibility(published, updated, start, hours=72):
    cutoff = utc(start) + timedelta(hours=hours)
    if not utc(start) <= utc(published) < cutoff:
        return "excluded", "outside_window"
    if utc(updated) >= cutoff:
        return "excluded", "edited_at_or_after_cutoff"
    return "eligible", ""


def collect_event(
    api, event, hours=72, max_pages=10000, checkpoint=None, progress=lambda text: None
):
    """Traverse all accessible pages, persist partial progress and deduplicate IDs."""
    rows, seen, tokens = [], set(), set()
    status = dict(
        event_id=event["event_id"],
        video_id=event["video_id"],
        pagination_complete=False,
        pages=0,
        duplicate_ids=0,
        error=None,
    )
    token = None
    try:
        if now_utc() < utc(event["video_published_at_utc"]) + timedelta(hours=hours):
            raise ValueError(
                "Jendela 72 jam belum selesai; tunggu sebelum pengambilan utama."
            )
        for _ in range(max_pages):
            params = dict(
                part="snippet",
                videoId=event["video_id"],
                maxResults=100,
                order="time",
                textFormat="plainText",
            )
            if token:
                params["pageToken"] = token
            page = api("commentThreads", params)
            status["pages"] += 1
            collected = now_utc().isoformat()
            for item in page.get("items", []):
                comment = item["snippet"]["topLevelComment"]
                if comment["id"] in seen:
                    status["duplicate_ids"] += 1
                    continue
                snippet = comment["snippet"]
                state, reason = eligibility(
                    snippet["publishedAt"],
                    snippet["updatedAt"],
                    event["video_published_at_utc"],
                    hours,
                )
                rows.append(
                    dict(
                        comment_id=comment["id"],
                        video_id=event["video_id"],
                        event_id=event["event_id"],
                        text_display=snippet["textDisplay"],
                        published_at_utc=snippet["publishedAt"],
                        updated_at_utc=snippet["updatedAt"],
                        collected_at_utc=collected,
                        like_count_at_collection=snippet.get("likeCount", 0),
                        language="und",
                        eligibility_status=state,
                        exclusion_reason=reason,
                    )
                )
                seen.add(comment["id"])
            progress(
                f"{event['event_id']}: {status['pages']} halaman, {len(rows)} komentar unik"
            )
            token = page.get("nextPageToken")
            if not token:
                status["pagination_complete"] = True
            if checkpoint:
                checkpoint(rows, status)
            if not token:
                break
            if token in tokens:
                raise ValueError("Token pagination berulang.")
            tokens.add(token)
        if token:
            status["error"] = "page_limit_reached"
    except (RuntimeError, ValueError, KeyError) as error:
        status["error"] = str(error)
    if checkpoint:
        checkpoint(rows, status)
    return rows, status
