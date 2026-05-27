# analyzer_agent - Code will be written in Phase 3
# analyzer_agent.py
# Sends transcript to Groq (Llama 3.3 70B) and returns structured JSON analysis.

import sys
import os
import json
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are an expert content analyst. You analyze YouTube video transcripts and return structured JSON.

Your response must be ONLY valid JSON — no explanation, no markdown, no code blocks, no preamble.
Return exactly this structure:

{
  "summary": "6 to 8 lines of plain English summary of the entire video",
  "key_points": [
    "Key point 1",
    "Key point 2",
    "Key point 3",
    "Key point 4",
    "Key point 5"
  ],
  "action_items": [
    "Specific thing I can do this week based on this video",
    "Another actionable step",
    "Another actionable step"
  ],
  "people_mentioned": [
    {
      "name": "Full Name",
      "role": "What they do — researcher, founder, doctor, etc."
    }
  ],
  "video_category": "one of: tech, health, podcast, research, finance, growth, education, other"
}

Rules:
- summary must be 6 to 8 lines, plain English, no jargon
- key_points must have 4 to 6 items
- action_items must have 3 to 5 concrete things to do this week
- people_mentioned: only real people explicitly spoken about in the video, not the host unless notable
- if no people are mentioned, return an empty list for people_mentioned
- video_category must be exactly one word from the list above
- Return ONLY the JSON object. Nothing else.
"""

def build_user_prompt(video, transcript):
    return f"""Video Title: {video['title']}
Channel: {video['channel']}
Date: {video['date']}
URL: {video['url']}

Transcript:
{transcript}

Analyze this video and return the structured JSON."""


def clean_json_response(text):
    """
    Strips markdown fences or extra text if Groq returns them.
    Extracts the JSON object reliably.
    """
    text = text.strip()
    # Remove markdown code fences if present
    text = re.sub(r"^```(?:json)?", "", text, flags=re.MULTILINE)
    text = re.sub(r"```$", "", text, flags=re.MULTILINE)
    text = text.strip()

    # Find the first { and last } to extract just the JSON object
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object found in Groq response.")
    return text[start:end]


def run(video, transcript):
    """
    Main entry point for Phase 3.
    Takes video dict and transcript string from Phase 2.
    Returns parsed analysis dict.
    """
    print("[Analyzer] Sending transcript to Groq (Llama 3.3 70B)...")

    user_prompt = build_user_prompt(video, transcript)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt}
        ],
        temperature=0.3,      # low temp = consistent structured output
        max_tokens=2000,
        response_format={"type": "json_object"}  # forces JSON mode
    )

    raw = response.choices[0].message.content
    print("[Analyzer] Response received. Parsing JSON...")

    try:
        cleaned = clean_json_response(raw)
        analysis = json.loads(cleaned)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"[Analyzer] JSON parse error: {e}")
        print(f"[Analyzer] Raw response was:\n{raw[:500]}")
        raise Exception("Groq returned invalid JSON. Try again.")

    # Validate all required keys exist
    required = ["summary", "key_points", "action_items",
                "people_mentioned", "video_category"]
    for key in required:
        if key not in analysis:
            analysis[key] = [] if key != "summary" else "Summary not available."

    print(f"[Analyzer] ✅ Analysis complete. Category: {analysis.get('video_category')}")
    print(f"[Analyzer] People mentioned: {[p['name'] for p in analysis.get('people_mentioned', [])]}")

    # Now find social profiles for people mentioned
    if analysis.get("people_mentioned"):
        print("[Analyzer] Finding social profiles for mentioned people...")
        analysis["people_mentioned"] = enrich_people(analysis["people_mentioned"])

    return analysis


def enrich_people(people):
    """
    For each person mentioned, finds their YouTube, Twitter, LinkedIn
    using DuckDuckGo search. Adds links to each person dict.
    """
    from ddgs import DDGS

    enriched = []
    with DDGS() as ddgs:
        for person in people:
            name = person.get("name", "")
            if not name:
                continue

            links = {"youtube": None, "twitter": None, "linkedin": None}

            try:
                # YouTube channel
                yt_results = list(ddgs.text(
                    f"{name} YouTube channel", max_results=2))
                for r in yt_results:
                    if "youtube.com" in r.get("href", ""):
                        links["youtube"] = r["href"]
                        break

                # Twitter/X
                tw_results = list(ddgs.text(
                    f"{name} Twitter", max_results=2))
                for r in tw_results:
                    href = r.get("href", "")
                    if "twitter.com" in href or "x.com" in href:
                        links["twitter"] = href
                        break

                # LinkedIn
                li_results = list(ddgs.text(
                    f"{name} LinkedIn", max_results=2))
                for r in li_results:
                    if "linkedin.com/in/" in r.get("href", ""):
                        links["linkedin"] = r["href"]
                        break

            except Exception as e:
                print(f"[Analyzer] Could not find links for {name}: {e}")

            person["links"] = links
            enriched.append(person)
            print(f"[Analyzer] {name} → YT:{bool(links['youtube'])} "
                  f"TW:{bool(links['twitter'])} LI:{bool(links['linkedin'])}")

    return enriched


# ── Quick test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Test with dummy data — replace with real transcript to test properly
    test_video = {
        "id": "test123",
        "title": "Master Your Sleep & Be More Alert When Awake",
        "channel": "Andrew Huberman",
        "date": "2024-01-15",
        "url": "https://www.youtube.com/watch?v=nm1TxQj9IsQ",
        "thumbnail": "",
        "description": ""
    }

    test_transcript = """
    Welcome to the Huberman Lab podcast. Today we discuss sleep and wakefulness.
    The key to good sleep is understanding adenosine and cortisol rhythms.
    Dr. Matthew Walker, author of Why We Sleep, has shown that adults need
    7 to 9 hours of sleep per night. Sunlight exposure in the morning sets
    your circadian rhythm. Avoid caffeine after 2 PM. Keep your room cool,
    around 65 to 68 degrees Fahrenheit. Avoid screens 1 hour before bed.
    Non sleep deep rest protocols like yoga nidra can help recover lost sleep.
    Dr. Satchin Panda's research on time restricted eating also affects sleep quality.
    """

    result = run(test_video, test_transcript)

    print("\n--- ANALYSIS RESULT ---")
    print(f"Category   : {result['video_category']}")
    print(f"Summary    : {result['summary'][:200]}...")
    print(f"Key Points : {result['key_points']}")
    print(f"Actions    : {result['action_items']}")
    print(f"People     : {[p['name'] for p in result['people_mentioned']]}")