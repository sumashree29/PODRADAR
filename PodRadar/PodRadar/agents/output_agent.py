# output_agent - Code will be written in Phase 4
# output_agent.py
# Generates a dark-themed HTML summary page and opens it in the browser.

import sys
import os
import json
import webbrowser
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output"
)
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
)
SEEN_VIDEOS_PATH = os.path.join(DATA_DIR, "seen_videos.json")


def safe_filename(text):
    """Converts a string into a safe filename."""
    text = re.sub(r'[\\/*?:"<>|]', "", text)
    text = text.replace(" ", "_")
    return text[:50]


def load_seen_videos():
    if not os.path.exists(SEEN_VIDEOS_PATH):
        return {}
    with open(SEEN_VIDEOS_PATH, "r") as f:
        try:
            return json.load(f)
        except:
            return {}


def save_seen_videos(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SEEN_VIDEOS_PATH, "w") as f:
        json.dump(data, f, indent=2)


def generate_html(video, analysis, output_path,):
    """Generates the full HTML summary page as a string."""

    # Build people cards HTML
    people_html = ""
    for person in analysis.get("people_mentioned", []):
        name = person.get("name", "")
        role = person.get("role", "")
        links = person.get("links", {})

        yt_btn = f'<a href="{links["youtube"]}" target="_blank" class="social-btn yt">▶ YouTube</a>' if links.get("youtube") else ""
        tw_btn = f'<a href="{links["twitter"]}" target="_blank" class="social-btn tw">𝕏 Twitter</a>' if links.get("twitter") else ""
        li_btn = f'<a href="{links["linkedin"]}" target="_blank" class="social-btn li">in LinkedIn</a>' if links.get("linkedin") else ""

        people_html += f"""
        <div class="person-card">
            <div class="person-info">
                <span class="person-name">{name}</span>
                <span class="person-role">{role}</span>
            </div>
            <div class="person-links">
                {yt_btn}{tw_btn}{li_btn}
            </div>
        </div>"""

    if not people_html:
        people_html = '<p class="muted">No notable people mentioned in this video.</p>'

    # Build key points HTML
    key_points_html = "".join(
        f"<li>{point}</li>" for point in analysis.get("key_points", [])
    )

    # Build action items HTML
    action_items_html = "".join(
        f"<li>{item}</li>" for item in analysis.get("action_items", [])
    )

    category = analysis.get("video_category", "other").upper()
    summary = analysis.get("summary", "").replace("\n", "<br>")
    video_id = video["id"]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{video['title']} — PodRadar</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  :root {{
    --bg:        #0a0a0f;
    --surface:   #111118;
    --border:    #1e1e2e;
    --accent:    #00d4aa;
    --accent2:   #7c6aff;
    --text:      #e2e2e8;
    --muted:     #5a5a72;
    --yt-red:    #ff4444;
    --tw-blue:   #1d9bf0;
    --li-blue:   #0a66c2;
  }}

  body {{
    font-family: 'DM Sans', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    padding: 40px 20px 80px;
  }}

  .container {{
    max-width: 780px;
    margin: 0 auto;
  }}

  /* ── Header ── */
  .header {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 32px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border);
  }}
  .logo {{ font-size: 18px; font-weight: 600; color: var(--accent); }}
  .generated-at {{ margin-left: auto; font-size: 12px; color: var(--muted); font-family: 'DM Mono', monospace; }}

  /* ── Hero ── */
  .hero {{
    position: relative;
    border-radius: 16px;
    overflow: hidden;
    margin-bottom: 28px;
    border: 1px solid var(--border);
  }}
  .thumbnail {{
    width: 100%;
    height: 280px;
    object-fit: cover;
    display: block;
    filter: brightness(0.6);
  }}
  .hero-overlay {{
    position: absolute;
    bottom: 0; left: 0; right: 0;
    padding: 24px;
    background: linear-gradient(transparent, rgba(0,0,0,0.92));
  }}
  .category-badge {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1.5px;
    background: var(--accent);
    color: #0a0a0f;
    margin-bottom: 8px;
    font-family: 'DM Mono', monospace;
  }}
  .video-title {{
    font-size: 22px;
    font-weight: 600;
    line-height: 1.3;
    margin-bottom: 8px;
  }}
  .video-meta {{
    font-size: 13px;
    color: #aaa;
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    align-items: center;
  }}
  .video-meta a {{
    color: var(--accent);
    text-decoration: none;
    font-weight: 500;
  }}
  .video-meta a:hover {{ text-decoration: underline; }}

  /* ── Sections ── */
  .section {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 24px;
    margin-bottom: 16px;
  }}
  .section-title {{
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.8px;
    color: var(--accent);
    text-transform: uppercase;
    font-family: 'DM Mono', monospace;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .section-title::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
  }}

  /* Summary */
  .summary-text {{
    font-size: 15px;
    line-height: 1.8;
    color: var(--text);
    font-weight: 300;
  }}

  /* Lists */
  .styled-list {{
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }}
  .styled-list li {{
    font-size: 14px;
    line-height: 1.6;
    padding-left: 20px;
    position: relative;
    color: #ccc;
  }}
  .styled-list li::before {{
    content: '▸';
    position: absolute;
    left: 0;
    color: var(--accent);
    font-size: 12px;
    top: 2px;
  }}

  /* Action items get accent2 */
  .action-list li::before {{ color: var(--accent2); content: '→'; }}

  /* People */
  .person-card {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    padding: 14px 0;
    border-bottom: 1px solid var(--border);
  }}
  .person-card:last-child {{ border-bottom: none; padding-bottom: 0; }}
  .person-info {{ display: flex; flex-direction: column; gap: 3px; }}
  .person-name {{ font-size: 15px; font-weight: 500; }}
  .person-role {{ font-size: 12px; color: var(--muted); }}
  .person-links {{ display: flex; gap: 8px; flex-wrap: wrap; }}

  .social-btn {{
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
    text-decoration: none;
    transition: opacity 0.15s;
  }}
  .social-btn:hover {{ opacity: 0.8; }}
  .social-btn.yt {{ background: rgba(255,68,68,0.15); color: var(--yt-red); border: 1px solid rgba(255,68,68,0.3); }}
  .social-btn.tw {{ background: rgba(29,155,240,0.15); color: var(--tw-blue); border: 1px solid rgba(29,155,240,0.3); }}
  .social-btn.li {{ background: rgba(10,102,194,0.15); color: #4d94ff; border: 1px solid rgba(10,102,194,0.3); }}

  /* Bottom buttons */
  .action-bar {{
    display: flex;
    gap: 12px;
    margin-top: 24px;
    flex-wrap: wrap;
  }}
  .btn {{
    padding: 12px 24px;
    border-radius: 10px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    border: none;
    font-family: 'DM Sans', sans-serif;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    transition: opacity 0.15s, transform 0.1s;
  }}
  .btn:hover {{ opacity: 0.85; transform: translateY(-1px); }}
  .btn-primary {{ background: var(--accent); color: #0a0a0f; }}
  .btn-secondary {{ background: var(--surface); color: var(--text); border: 1px solid var(--border); }}
  .btn-read {{ background: var(--accent2); color: #fff; }}
  .btn-read.done {{ background: #2a2a3a; color: var(--muted); cursor: default; }}

  .muted {{ color: var(--muted); font-size: 14px; }}
</style>
</head>
<body>
<div class="container">

  <!-- Header -->
  <div class="header">
    <span class="logo">🎙 PodRadar</span>
    <span class="generated-at">Generated {datetime.now().strftime("%d %b %Y, %I:%M %p")}</span>
  </div>

  <!-- Hero -->
  <div class="hero">
    <img class="thumbnail" src="{video['thumbnail']}" alt="Video thumbnail"
         onerror="this.style.display='none'">
    <div class="hero-overlay">
      <div class="category-badge">{category}</div>
      <div class="video-title">{video['title']}</div>
      <div class="video-meta">
        <span>📺 {video['channel']}</span>
        <span>📅 {video['date']}</span>
        <a href="{video['url']}" target="_blank">▶ Watch on YouTube</a>
      </div>
    </div>
  </div>

  <!-- Summary -->
  <div class="section">
    <div class="section-title">Summary</div>
    <p class="summary-text">{summary}</p>
  </div>

  <!-- Key Points -->
  <div class="section">
    <div class="section-title">Key Points</div>
    <ul class="styled-list">{key_points_html}</ul>
  </div>

  <!-- Action Items -->
  <div class="section">
    <div class="section-title">Action Items — Do This Week</div>
    <ul class="styled-list action-list">{action_items_html}</ul>
  </div>

  <!-- People to Follow -->
  <div class="section">
    <div class="section-title">People to Follow</div>
    {people_html}
  </div>

  <!-- Action Bar -->
  <div class="action-bar">
    <a href="{video['url']}" target="_blank" class="btn btn-primary">▶ Watch Full Video</a>
    <button class="btn btn-read" id="markReadBtn"
            onclick="markAsRead('{video_id}')">✓ Mark as Read</button>
  </div>

</div>

<script>
  // Mark as Read — calls local Python server to update seen_videos.json
  function markAsRead(videoId) {{
    const btn = document.getElementById('markReadBtn');
    btn.textContent = '✓ Marked as Read';
    btn.classList.add('done');
    btn.disabled = true;

    fetch('http://localhost:7734/mark_read?id=' + videoId)
      .then(() => console.log('Marked as read'))
      .catch(() => {{
        // Silently fail — file update happens at open time anyway
        console.log('Could not reach local server (normal if agent already exited)');
      }});
  }}
</script>
</body>
</html>"""

    return html


def run(video, analysis):
    """
    Main entry point for Phase 4.
    Generates HTML, saves it, opens in browser, updates seen_videos.json.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Build filename
    date_str = datetime.now().strftime("%Y-%m-%d")
    channel_safe = safe_filename(video["channel"])
    title_safe = safe_filename(video["title"])
    filename = f"{date_str}_{channel_safe}_{title_safe}.html"
    output_path = os.path.join(OUTPUT_DIR, filename)

    # Generate and save HTML
    html = generate_html(video, analysis, output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[Output] HTML saved → {output_path}")

    # Update seen_videos.json
    seen = load_seen_videos()
    seen[video["id"]] = {
        "title": video["title"],
        "channel": video["channel"],
        "date": video["date"],
        "url": video["url"],
        "html_file": filename,
        "read": False,
        "notified_at": datetime.now().isoformat()
    }
    save_seen_videos(seen)
    print(f"[Output] seen_videos.json updated.")

    # Open in browser
    webbrowser.open(f"file:///{output_path.replace(os.sep, '/')}")
    print(f"[Output] ✅ Opened in browser.")

    return output_path


# ── Quick test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_video = {
        "id": "test123",
        "title": "Master Your Sleep and Be More Alert When Awake",
        "channel": "Andrew Huberman",
        "date": "2024-01-15",
        "url": "https://www.youtube.com/watch?v=nm1TxQj9IsQ",
        "thumbnail": "https://i.ytimg.com/vi/nm1TxQj9IsQ/hqdefault.jpg",
        "description": ""
    }
    test_analysis = {
        "summary": "This episode covers the neuroscience of sleep. Andrew Huberman explains how adenosine builds up during the day and creates sleep pressure. Morning sunlight is critical for setting your circadian rhythm. Caffeine works by blocking adenosine receptors. You should avoid caffeine after 2 PM. Keeping your room cool helps initiate and maintain sleep. Non-sleep deep rest protocols can help recover lost sleep quickly.",
        "key_points": [
            "Adenosine accumulates during wakefulness and drives sleep pressure",
            "Morning sunlight within 30 minutes of waking sets circadian rhythm",
            "Caffeine blocks adenosine receptors — avoid after 2 PM",
            "Room temperature of 65–68°F is optimal for sleep",
            "NSDR and yoga nidra can substitute for lost sleep"
        ],
        "action_items": [
            "Get outside within 30 minutes of waking for 10 minutes of sunlight",
            "Set a caffeine cutoff at 2 PM starting this week",
            "Lower your bedroom thermostat to 67°F before sleep",
            "Try a 10-minute NSDR protocol after lunch if feeling drowsy"
        ],
        "people_mentioned": [
            {
                "name": "Andrew Huberman",
                "role": "Neuroscientist, Stanford Professor, Podcast Host",
                "links": {
                    "youtube": "https://youtube.com/@hubermanlab",
                    "twitter": "https://twitter.com/hubermanlab",
                    "linkedin": None
                }
            }
        ],
        "video_category": "health"
    }
    run(test_video, test_analysis)