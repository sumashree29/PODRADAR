# get_channel_ids.py
# Run this ONCE to find and save all channel IDs into channels.json
# Delete this file after running.

import json
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from googleapiclient.discovery import build
from config import YOUTUBE_API_KEY

CHANNELS_PATH = "channels.json"

with open(CHANNELS_PATH, "r") as f:
    data = json.load(f)

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
channels = data["channels"]
updated = 0

for ch in channels:
    if ch.get("channel_id"):
        print(f"[Skip] Already have ID for: {ch['name']}")
        continue

    try:
        response = youtube.search().list(
            q=ch["name"],
            part="snippet",
            type="channel",
            maxResults=1
        ).execute()

        items = response.get("items", [])
        if items:
            ch["channel_id"] = items[0]["id"]["channelId"]
            print(f"[OK] {ch['name']} → {ch['channel_id']}")
            updated += 1
        else:
            print(f"[Miss] No result for: {ch['name']}")

        time.sleep(0.5)  # be gentle with quota

    except Exception as e:
        print(f"[Error] {ch['name']}: {e}")
        print("[!] Quota likely hit. Run again tomorrow to get remaining channels.")
        break

data["channels"] = channels
with open(CHANNELS_PATH, "w") as f:
    json.dump(data, f, indent=2)

print(f"\nDone. {updated} channel IDs saved to channels.json.")