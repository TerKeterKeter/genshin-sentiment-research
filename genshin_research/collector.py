"""YouTube API adapter. Never stores author identifiers or API response bodies."""
import logging
import time
from datetime import datetime, timezone
from .core import eligibility

LOG = logging.getLogger(__name__)


class YouTube:
    def __init__(self, key, attempts=3):
        if not key:
            raise ValueError('YOUTUBE_API_KEY required')
        self.key, self.attempts = key, attempts

    def __call__(self, resource, params):
        import requests
        for attempt in range(self.attempts):
            try:
                response = requests.get('https://www.googleapis.com/youtube/v3/' + resource,
                                        params={**params, 'key': self.key}, timeout=30)
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt + 1 < self.attempts:
                        time.sleep(2 ** attempt)
                        continue
                # Do not log request URLs: they contain the key.
                if response.status_code != 200:
                    raise RuntimeError(f'YouTube HTTP {response.status_code}')
                return response.json()
            except requests.RequestException:
                if attempt + 1 == self.attempts:
                    raise RuntimeError('YouTube transport failure') from None
                time.sleep(2 ** attempt)
        raise RuntimeError('Retry limit reached')

    def official_channel_id(self):
        result = self('channels', {'part': 'id', 'forHandle': '@GenshinImpact'})
        if len(result.get('items', [])) != 1:
            raise ValueError('Official channel handle could not be resolved')
        return result['items'][0]['id']

    def metadata(self, video_id):
        result = self('videos', {'part': 'snippet,contentDetails', 'id': video_id})
        if len(result.get('items', [])) != 1:
            raise ValueError('Video unavailable or invalid ID')
        item = result['items'][0]
        snippet = item['snippet']
        return {'video_id': item['id'], 'title': snippet['title'],
                'channel_id': snippet['channelId'], 'channel_title': snippet['channelTitle'],
                'video_published_at_utc': snippet['publishedAt'],
                'duration': item['contentDetails']['duration']}


def collect(api, event, hours=72, max_pages=1000):
    rows, seen, tokens = [], set(), set()
    token = None
    status = {'pagination_complete': False, 'pages': 0, 'error': None,
              'duplicate_ids': 0, 'video_id': event['video_id']}
    try:
        for _ in range(max_pages):
            params = {'part': 'snippet', 'videoId': event['video_id'],
                      'maxResults': 100, 'order': 'time', 'textFormat': 'plainText'}
            if token:
                params['pageToken'] = token
            page = api('commentThreads', params)
            status['pages'] += 1
            now = datetime.now(timezone.utc).isoformat()
            for item in page.get('items', []):
                comment = item['snippet']['topLevelComment']
                if comment['id'] in seen:
                    status['duplicate_ids'] += 1
                    continue
                seen.add(comment['id'])
                s = comment['snippet']
                state, reason = eligibility(s['publishedAt'], s['updatedAt'],
                                            event['video_published_at_utc'], hours)
                rows.append(dict(comment_id=comment['id'], video_id=event['video_id'],
                    event_id=event['event_id'], text_display=s['textDisplay'],
                    published_at_utc=s['publishedAt'], updated_at_utc=s['updatedAt'],
                    collected_at_utc=now, like_count_at_collection=s.get('likeCount', 0),
                    language='und', eligibility_status=state, exclusion_reason=reason))
            token = page.get('nextPageToken')
            if not token:
                status['pagination_complete'] = True
                break
            if token in tokens:
                raise ValueError('Repeated pagination token')
            tokens.add(token)
        if token and not status['pagination_complete']:
            status['error'] = 'page_limit_reached'
    except (RuntimeError, ValueError, KeyError) as error:
        status['error'] = str(error)
        LOG.warning('Collection interrupted: %s', status['error'])
    return rows, status
