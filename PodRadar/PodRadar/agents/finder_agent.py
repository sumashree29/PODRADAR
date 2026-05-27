# finder_agent.py
# Searches YouTube for the best matching video and fetches its transcript.

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from config import YOUTUBE_API_KEY


def parse_query(query):
    """
    Extracts channel name and topic from raw query.
    Matches against known channels in channels.json.
    """
    channels_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "channels.json"
    )
    with open(channels_path, "r") as f:
        data = json.load(f)

    known_channels = [c["name"].lower() for c in data["channels"]]
    query_clean = query.lower().replace(",", " ").strip()

    for ch in known_channels:
        if ch in query_clean:
            topic = query_clean.replace(ch, "").strip()
            for word in ["summarize", "latest", "video", "podcast",
                         "episode", "on", "about", "the"]:
                topic = topic.replace(word, "").strip()
            topic = " ".join(topic.split())  # remove extra spaces
            return ch.title(), topic if topic else "latest"

    return None, query_clean


def search_youtube(channel_name, topic):
    """
    Searches YouTube Data API v3.
    Returns video dict with metadata.
    """
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    search_query = f"{channel_name} {topic}" if channel_name else topic
    print(f"[Finder] Searching YouTube: '{search_query}'")

    response = youtube.search().list(
        q=search_query,
        part="snippet",
        type="video",
        maxResults=5,
        order="relevance",
        relevanceLanguage="en"
    ).execute()

    items = response.get("items", [])
    if not items:
        raise Exception(f"No YouTube results found for: {search_query}")

    item = items[0]
    video_id = item["id"]["videoId"]
    snippet = item["snippet"]

    # Clean HTML entities from title
    import html
    video = {
        "id": video_id,
        "title": html.unescape(snippet["title"]),
        "channel": html.unescape(snippet["channelTitle"]),
        "date": snippet["publishedAt"][:10],
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "thumbnail": snippet["thumbnails"]["high"]["url"],
        "description": snippet.get("description", "")
    }

    print(f"[Finder] Found: '{video['title']}' by {video['channel']}")
    return video


def fetch_transcript(video_id):
    """
    Fetches full transcript using updated youtube-transcript-api.
    Falls back to None if unavailable.
    """
    try:
        ytt = YouTubeTranscriptApi()
        fetched = ytt.fetch(video_id)
        # fetched is a list of snippet dicts with 'text' key
        text = " ".join([entry.text for entry in fetched])
        print(f"[Finder] Transcript fetched — {len(text)} characters.")
        return text

    except Exception as e:
        print(f"[Finder] No transcript available ({e}) — using fallback.")
        return None


def run(query):
    """
    Main entry point for Phase 2.
    Returns dict with video metadata + transcript.
    """
    channel, topic = parse_query(query)
    print(f"[Finder] Channel: {channel or 'Not specified'} | Topic: {topic}")

    video = search_youtube(channel, topic)
    transcript = fetch_transcript(video["id"])

    if not transcript:
        transcript = video["description"]
        if not transcript:
            raise Exception("No transcript and no description available.")
        print("[Finder] Using video description as transcript fallback.")

    if len(transcript) > 12000:
        transcript = transcript[:12000]
        print("[Finder] Transcript trimmed to 12,000 characters.")

    return {"video": video, "transcript": transcript}


# ── Quick test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    data = run("Andrew Huberman sleep")
    print("\n--- VIDEO ---")
    print(f"Title     : {data['video']['title']}")
    print(f"Channel   : {data['video']['channel']}")
    print(f"URL       : {data['video']['url']}")
    print(f"Transcript: {data['transcript'][:300]}...")