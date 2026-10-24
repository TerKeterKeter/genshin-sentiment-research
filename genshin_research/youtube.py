"""Read-only video/channel metadata adapter with bounded retries."""

import time


class YouTube:
    def __init__(self, key, attempts=3):
        if not key:
            raise ValueError("YOUTUBE_API_KEY required")
        self.key, self.attempts = key, attempts

    def __call__(self, resource, params):
        import requests

        for attempt in range(self.attempts):
            try:
                response = requests.get(
                    "https://www.googleapis.com/youtube/v3/" + resource,
                    params={**params, "key": self.key},
                    timeout=30,
                )
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt + 1 < self.attempts:
                        time.sleep(2**attempt)
                        continue
                # Do not log request URLs: they contain the key.
                if response.status_code != 200:
                    raise RuntimeError(f"YouTube HTTP {response.status_code}")
                return response.json()
            except requests.RequestException:
                if attempt + 1 == self.attempts:
                    raise RuntimeError("YouTube transport failure") from None
                time.sleep(2**attempt)
        raise RuntimeError("Retry limit reached")

    def official_channel_id(self):
        result = self("channels", {"part": "id", "forHandle": "@GenshinImpact"})
        if len(result.get("items", [])) != 1:
            raise ValueError("Official channel handle could not be resolved")
        return result["items"][0]["id"]

    def metadata(self, video_id):
        result = self("videos", {"part": "snippet,contentDetails", "id": video_id})
        if len(result.get("items", [])) != 1:
            raise ValueError("Video unavailable or invalid ID")
        item = result["items"][0]
        snippet = item["snippet"]
        return {
            "video_id": item["id"],
            "title": snippet["title"],
            "channel_id": snippet["channelId"],
            "channel_title": snippet["channelTitle"],
            "video_published_at_utc": snippet["publishedAt"],
            "duration": item["contentDetails"]["duration"],
        }
