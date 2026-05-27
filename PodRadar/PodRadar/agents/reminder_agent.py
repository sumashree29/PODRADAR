# reminder_agent.py
# Sends ONE reminder at a time, highest priority first.
# Supports 4 priority levels.
# New channels auto-assigned priority based on their category.

import sys
import os
import json
import webbrowser
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plyer import notification

DATA_DIR      = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
SEEN_PATH     = os.path.join(DATA_DIR, "seen_videos.json")
SNOOZE_PATH   = os.path.join(DATA_DIR, "snoozed.json")
OUTPUT_DIR    = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
CHANNELS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "channels.json")

# ── Auto-priority rules — category → priority ────────────────────────────────
# When a new channel is added to channels.json without a priority field,
# this map assigns one automatically based on its category.
AUTO_PRIORITY_RULES = {
    "tech and ai":             1,
    "podcasts and growth":     2,
    "research and learning":   3,
    "health and wellness":     4,
}

# Priority display labels
PRIORITY_LABELS = {
    1: "🔴 P1 · Tech & AI",
    2: "🟠 P2 · Podcasts",
    3: "🟡 P3 · Research",
    4: "🟢 P4 · Health",
}


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r") as f:
        try:
            return json.load(f)
        except:
            return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def get_priority_map():
    """
    Returns {channel_name_lower: priority} from channels.json.
    If a channel has no priority field, auto-assigns based on category.
    If category is also unknown, defaults to priority 2.
    """
    channels_data = load_json(CHANNELS_PATH, {})
    channels      = channels_data.get("channels", [])
    auto_rules    = channels_data.get("_priority_guide", {}).get("auto_rules", {})

    priority_map = {}
    updated      = False

    for ch in channels:
        name     = ch.get("name", "")
        category = ch.get("category", "")

        if "priority" in ch:
            priority_map[name.lower()] = ch["priority"]
        else:
            # Auto-assign from auto_rules in JSON first
            auto_p = auto_rules.get(category)

            # Fall back to hardcoded AUTO_PRIORITY_RULES
            if auto_p is None:
                auto_p = AUTO_PRIORITY_RULES.get(category.lower(), 2)

            ch["priority"] = auto_p
            priority_map[name.lower()] = auto_p
            print(f"[Reminder] Auto-assigned priority {auto_p} to '{name}' ({category})")
            updated = True

    # Save back if any channels got auto-assigned
    if updated:
        channels_data["channels"] = channels
        save_json(CHANNELS_PATH, channels_data)
        print("[Reminder] channels.json updated with auto-assigned priorities.")

    return priority_map


def pick_next_video(seen, snoozed_today, priority_map):
    """
    From all unread videos, picks the single highest priority one
    that hasn't been snoozed this cycle.
    Priority 1 first → 2 → 3 → 4.
    """
    candidates = []

    for vid_id, info in seen.items():
        if info.get("read", False):
            continue
        if vid_id in snoozed_today:
            continue

        channel_lower = info.get("channel", "").lower()
        priority      = priority_map.get(channel_lower, 2)
        candidates.append((priority, vid_id, info))

    if not candidates:
        return None, None

    candidates.sort(key=lambda x: x[0])
    _, vid_id, info = candidates[0]
    return vid_id, info


def run():
    now_hour = datetime.now().hour
    today    = datetime.now().strftime("%Y-%m-%d")

    # Only remind between 6 PM (18) and 10 PM (22)
    if not (18 <= now_hour <= 22):
        print("[Reminder] Outside reminder window (6PM–10PM). Exiting.")
        return

    seen         = load_json(SEEN_PATH, {})
    snooze_data  = load_json(SNOOZE_PATH, {})
    priority_map = get_priority_map()

    snoozed_today = snooze_data.get(today, [])

    # Count unread per priority level
    unread_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    for info in seen.values():
        if not info.get("read", False):
            ch_priority = priority_map.get(info.get("channel", "").lower(), 2)
            unread_counts[ch_priority] = unread_counts.get(ch_priority, 0) + 1

    total_unread = sum(unread_counts.values())

    if total_unread == 0:
        print("[Reminder] No unread videos. All caught up!")
        return

    print(f"[Reminder] Unread — P1:{unread_counts[1]} P2:{unread_counts[2]} "
          f"P3:{unread_counts[3]} P4:{unread_counts[4]}")

    vid_id, info = pick_next_video(seen, snoozed_today, priority_map)

    if not vid_id:
        print("[Reminder] All unread videos snoozed for today. Done.")
        return

    title        = info.get("title", "New Video")
    channel      = info.get("channel", "")
    html_file    = info.get("html_file", "")
    html_path    = os.path.join(OUTPUT_DIR, html_file)
    priority_num = priority_map.get(channel.lower(), 2)
    p_label      = PRIORITY_LABELS.get(priority_num, "")
    remaining    = total_unread - 1
    remaining_text = f"{remaining} more unread" if remaining > 0 else "no more after this"

    print(f"[Reminder] Now: [{p_label}] {title[:60]}")
    print(f"[Reminder] {remaining_text}")

    try:
        notification.notify(
            title=f"{p_label} — {channel}",
            message=f"{title[:80]}\n({remaining_text})",
            app_name="PodRadar",
            timeout=12
        )

        if os.path.exists(html_path):
            webbrowser.open(f"file:///{html_path.replace(os.sep, '/')}")

    except Exception as e:
        print(f"[Reminder] Notification error: {e}")

    # Input prompt
    print(f"\n  's' + Enter → Snooze (skip today, remind next cycle)")
    print(f"  'd' + Enter → Done  (mark as read, move to next video)")
    print(f"  Enter only  → No action (same video reminds next cycle)\n")

    try:
        import msvcrt, time
        print("[Reminder] Waiting 15 seconds...")
        start  = time.time()
        choice = ""
        while time.time() - start < 15:
            if msvcrt.kbhit():
                choice = input().strip().lower()
                break
            time.sleep(0.2)
    except:
        choice = ""

    if choice == "d":
        seen[vid_id]["read"] = True
        save_json(SEEN_PATH, seen)
        print(f"[Reminder] ✅ Marked as read: {title[:50]}")

    elif choice == "s":
        snoozed_today.append(vid_id)
        snooze_data[today] = snoozed_today
        save_json(SNOOZE_PATH, snooze_data)
        print(f"[Reminder] 💤 Snoozed for today: {title[:50]}")

    else:
        print(f"[Reminder] No action. Will remind again next cycle.")


if __name__ == "__main__":
    run()
