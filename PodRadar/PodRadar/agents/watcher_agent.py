# watcher_agent.py
# Uses saved channel_id from channels.json — zero quota cost for ID lookup.

import sys
import os
import json
import html as html_lib
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from googleapiclient.discovery import build
from plyer import notification
from config import YOUTUBE_API_KEY

DATA_DIR      = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
SEEN_PATH     = os.path.join(DATA_DIR, "seen_videos.json")
CHANNELS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "channels.json")


def load_seen():
    if not os.path.exists(SEEN_PATH):
        return {}
    with open(SEEN_PATH, "r") as f:
        try:
            return json.load(f)
        except:
            return {}


def save_seen(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SEEN_PATH, "w") as f:
        json.dump(data, f, indent=2)


def load_channels():
    with open(CHANNELS_PATH, "r") as f:
        data = json.load(f)
    return data["channels"]


def fetch_recent_videos(youtube, channel_id, channel_name):
    """
    Fetches videos from a channel uploaded in the last 24 hours.
    Uses channel_id directly — no search quota cost.
    """
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

    try:
        response = youtube.search().list(
            channelId=channel_id,
            part="snippet",
            type="video",
            order="date",
            publishedAfter=since,
            maxResults=3
        ).execute()

        videos = []
        for item in response.get("items", []):
            video_id = item["id"]["videoId"]
            snippet  = item["snippet"]
            videos.append({
                "id":          video_id,
                "title":       html_lib.unescape(snippet["title"]),
                "channel":     html_lib.unescape(snippet["channelTitle"]),
                "date":        snippet["publishedAt"][:10],
                "url":         f"https://www.youtube.com/watch?v={video_id}",
                "thumbnail":   snippet["thumbnails"]["high"]["url"],
                "description": snippet.get("description", "")
            })
        return videos

    except Exception as e:
        print(f"[Watcher] Error fetching '{channel_name}': {e}")
        return []


def send_notification(title, channel, html_path):
    try:
        notification.notify(
            title=f"🎙 PodRadar — {channel}",
            message=f"{title[:100]}",
            app_name="PodRadar",
            timeout=10
        )
        import webbrowser
        webbrowser.open(f"file:///{html_path.replace(os.sep, '/')}")
        print(f"[Watcher] 🔔 Notified: {title[:60]}")
    except Exception as e:
        print(f"[Watcher] Notification error: {e}")


def run():
    print(f"\n[Watcher] ===== Daily check — {datetime.now().strftime('%Y-%m-%d %H:%M')} =====")

    from agents.finder_agent   import fetch_transcript
    from agents.analyzer_agent import run as analyze
    from agents.output_agent   import run as generate_output

    youtube  = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    channels = load_channels()
    seen     = load_seen()
    new_count = 0

    for ch in channels:
        name       = ch["name"]
        channel_id = ch.get("channel_id")

        if not channel_id:
            print(f"[Watcher] ⚠ No channel_id for '{name}' — run get_channel_ids.py first")
            continue

        print(f"[Watcher] Checking: {name}")
        recent = fetch_recent_videos(youtube, channel_id, name)

        for video in recent:
            vid_id = video["id"]

            if vid_id in seen:
                print(f"[Watcher] Already seen: {video['title'][:50]}")
                continue

            print(f"[Watcher] 🆕 New: {video['title'][:60]}")

            try:
                transcript = fetch_transcript(vid_id)
                if not transcript:
                    transcript = video["description"] or "No transcript available."
                if len(transcript) > 12000:
                    transcript = transcript[:12000]

                analysis  = analyze(video, transcript)
                html_path = generate_output(video, analysis)
                send_notification(video["title"], video["channel"], html_path)
                new_count += 1

            except Exception as e:
                print(f"[Watcher] ❌ Failed: {video['title'][:40]} — {e}")

    print(f"[Watcher] ===== Done. {new_count} new video(s) processed. =====\n")


if __name__ == "__main__":
    run()