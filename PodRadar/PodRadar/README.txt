PodRadar - Personal AI YouTube/Podcast Agent
=============================================

FILE STRUCTURE:
  main.py               - Phase 1: Hotkey listener + launches popup
  config.py             - Phase 1: Your API keys go here
  channels.json         - Your channel list (edit in Notepad anytime)
  agents/
    voice_agent.py      - Phase 1: Popup UI + mic + Whisper
    finder_agent.py     - Phase 2: YouTube search + transcript
    analyzer_agent.py   - Phase 3: Groq LLM analysis
    output_agent.py     - Phase 4: HTML generation + browser open
    watcher_agent.py    - Phase 5: Daily 6PM channel checker
    reminder_agent.py   - Phase 5: Unread video reminders every 2hr
  templates/
    summary.html        - Phase 4: Jinja2 HTML output template
  output/               - All HTML summaries saved here (auto-created)
  data/
    seen_videos.json    - Tracks which videos you have read

BUILD ORDER:
  Phase 1 - Environment setup + Hotkey + Popup window
  Phase 2 - YouTube search + Transcript fetch
  Phase 3 - Groq LLM analysis
  Phase 4 - HTML output + browser auto-open
  Phase 5 - Daily watcher + reminder notifications
