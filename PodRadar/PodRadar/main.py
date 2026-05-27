# main.py
# Phase 1 + 2 + 3 + 4 connected. Full pipeline.

import keyboard
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.voice_agent import show_popup
from agents.finder_agent import run as find_video
from agents.analyzer_agent import run as analyze
from agents.output_agent import run as generate_output

def handle_trigger():
    print("[PodRadar] Hotkey detected — opening popup...")
    query = show_popup()

    if not query:
        print("[PodRadar] No input. Exiting.")
        return

    print(f"[PodRadar] Query: {query}")

    try:
        print("[PodRadar] Phase 2 — Searching YouTube...")
        data = find_video(query)
        print(f"[PodRadar] ✅ Video: {data['video']['title']}")

        print("[PodRadar] Phase 3 — Analyzing with Groq...")
        analysis = analyze(data["video"], data["transcript"])
        print(f"[PodRadar] ✅ Analysis done.")

        print("[PodRadar] Phase 4 — Generating HTML output...")
        path = generate_output(data["video"], analysis)
        print(f"[PodRadar] ✅ Done. Summary opened in browser.")
        print("[PodRadar] All phases complete. Waiting for next hotkey...")

    except Exception as e:
        print(f"[PodRadar] ❌ Error: {e}")

def main():
    print("[PodRadar] Running. Press Win+Shift+P to open the popup.")
    print("[PodRadar] Press Ctrl+C to stop.")
    keyboard.add_hotkey("windows+shift+p", handle_trigger)
    keyboard.wait()

if __name__ == "__main__":
    main()