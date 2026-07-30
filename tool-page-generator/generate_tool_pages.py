#!/usr/bin/env python3
"""
Tool Landing Page Content Generator
Generates unique niche-specific content for each quiz-maker tool landing page
using Groq API (same pattern as ghost_blog_automation.py).

Usage:
    python3 generate_tool_pages.py                     # generate all niches
    python3 generate_tool_pages.py --niche gaming       # generate one niche
    python3 generate_tool_pages.py --dry-run            # print only, no files
"""

import json
import os
import sys
import requests
import time
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.dirname(SCRIPT_DIR)
NICHES_PATH = os.path.join(SCRIPT_DIR, "niches.json")
OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "frontend", "public", "data", "tool-pages")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-specdec"


def load_niches():
    with open(NICHES_PATH, "r") as f:
        return json.load(f)


def get_groq_key():
    key = os.environ.get("GROQ_API_KEY")
    if key:
        return key
    try:
        with open(os.path.join(SCRIPT_DIR, ".groq_key"), "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        pass
    return None


def generate_niche_content(groq_key, niche_obj):
    slug = niche_obj["slug"]
    niche = niche_obj["niche"]
    print(f"\n{'='*60}")
    print(f"Generating content for: {niche} ({slug})")
    print(f"{'='*60}")

    system_prompt = (
        "You are an expert SEO content creator for QuizViral AI, "
        "a SaaS platform that generates bulk faceless quiz videos for YouTube Shorts, TikTok, "
        "and Instagram Reels in one click. You are writing niche-specific landing page content "
        "for quiz-maker tool pages. Every piece of content must be genuinely unique — "
        "do not reuse examples across niches."
    )

    user_prompt = f"""
    Generate SEO-optimized content for a tool landing page about creating "{niche}" quizzes.
    The URL will be /tools/{slug}-quiz-maker on QuizViral AI.

    Return ONLY a raw JSON object (no markdown code blocks, just the JSON) with these exact keys:

    1. "hero_headline": A powerful, niche-specific hero headline (max 12 words) that includes the niche name. Example: "Create Addictive {niche} Quiz Videos in Seconds"

    2. "example_questions": An array of exactly 3 unique, specific quiz questions for this niche. Each question must have:
       - "question": The question text
       - "options": Array of 4 answer options
       - "answer": The correct answer (must match one option exactly)
       These must be REAL, niche-specific examples — NOT generic. For "history", use actual historical events with correct dates. For "gaming", use real game titles. For "anime", use real anime series.

    3. "faq": An array of exactly 3 FAQ objects, each with:
       - "question": The FAQ question (SEO-friendly, natural language)
       - "answer": 2-3 sentence answer with helpful detail
       Make the FAQ questions unique per niche — they should reflect genuine questions someone in that niche would ask.

    4. "cta": A compelling CTA line using the exact format "Create your [niche] quiz now" but with niche-specific action words.

    JSON TEMPLATE:
    {{
      "slug": "{slug}",
      "niche": "{niche}",
      "hero_headline": "...",
      "example_questions": [
        {{"question": "...", "options": ["A", "B", "C", "D"], "answer": "A"}}
      ],
      "faq": [
        {{"question": "...", "answer": "..."}}
      ],
      "cta": "Create your [niche] quiz now"
    }}

    IMPORTANT: Make the examples genuinely specific and unique to this niche. Do NOT use the same examples across different niches.
    """

    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.8,
        "max_tokens": 2000
    }

    try:
        response = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=60)
        if response.status_code != 200:
            print(f"  ERROR HTTP {response.status_code}: {response.text}")
            return None

        res_data = response.json()
        raw_json_str = res_data["choices"][0]["message"]["content"].strip()

        if raw_json_str.startswith("```"):
            raw_json_str = re.sub(r"^```(json)?", "", raw_json_str, flags=re.IGNORECASE).strip()
            if raw_json_str.endswith("```"):
                raw_json_str = raw_json_str[:-3].strip()

        content_data = json.loads(raw_json_str)
        content_data["slug"] = slug
        content_data["niche"] = niche
        print(f"  SUCCESS: Generated content for {niche}")
        return content_data

    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def save_content(content_data, dry_run=False):
    slug = content_data["slug"]
    output_path = os.path.join(OUTPUT_DIR, f"{slug}.json")

    if dry_run:
        print(f"\n  [DRY-RUN] Would save to: {output_path}")
        print(f"  Headline: {content_data['hero_headline']}")
        print(f"  Questions: {len(content_data.get('example_questions', []))}")
        print(f"  FAQ items: {len(content_data.get('faq', []))}")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(content_data, f, indent=2)
    print(f"  SAVED: {output_path}")


def main():
    dry_run = "--dry-run" in sys.argv
    single_niche = None

    for i, arg in enumerate(sys.argv):
        if arg == "--niche" and i + 1 < len(sys.argv):
            single_niche = sys.argv[i + 1]

    niches = load_niches()

    if single_niche:
        niches = [n for n in niches if n["slug"] == single_niche]
        if not niches:
            print(f"ERROR: Niche '{single_niche}' not found in niches.json")
            sys.exit(1)

    groq_key = get_groq_key()
    if not groq_key:
        print("ERROR: GROQ_API_KEY not found.")
        print("Set GROQ_API_KEY environment variable or create tool-page-generator/.groq_key file")
        sys.exit(1)

    print(f"Loaded {len(niches)} niches from {NICHES_PATH}")
    total = len(niches)

    for idx, niche_obj in enumerate(niches, 1):
        content = generate_niche_content(groq_key, niche_obj)
        if content:
            save_content(content, dry_run=dry_run)
        else:
            print(f"  FAILED: {niche_obj['niche']}")
        if idx < total:
            time.sleep(2)  # rate limit buffer

    print(f"\n{'='*60}")
    print(f"Done! Generated content for {total} niches.")
    if not dry_run:
        print(f"Output directory: {OUTPUT_DIR}")
        print(f"Files: {os.listdir(OUTPUT_DIR)}")


if __name__ == "__main__":
    main()
