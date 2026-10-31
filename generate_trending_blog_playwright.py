#!/usr/bin/env python3
"""
QuizViral AI - Trending Blog Post Generator (Playwright & Gemini)
================================================================
This script automates the full SEO blog generation pipeline using Playwright
to control Chrome (port 9224):
1. Navigates to Google Trends (US) to scrape the top 5 trending topics.
2. Prompts Gemini to select the easiest/most interesting topic for a quiz video.
3. Performs Google Autocomplete Suggestion research by typing the topic + ' a', ' b', ' y', ' z'.
4. Generates a 1500+ words SEO-optimized blog post in both HTML (for Ghost) and Markdown (for Vercel frontend).
5. Generates a landscape header image (16:9) and a vertical Pinterest image (9:16) using Gemini, downloading both.
6. Uploads the landscape header to Ghost CMS and publishes the post to Ghost CMS Admin API v2.
7. Updates the frontend data file `blogPosts.js`, updates sitemap.xml, and triggers Vercel/GitHub deployments.
8. Automatically triggers Pinterest syndication using the vertical image.
"""

import os
import sys
import re
import json
import time
import random
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import subprocess
import hmac
import hashlib
import base64
from datetime import datetime
from playwright.sync_api import sync_playwright

# Set UTF-8 encoding for standard output and error to prevent CP1252 charmap crashes on Windows
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

# ==================== CONFIGURATION ====================
CHROME_PROFILE_PATH = r"C:\Users\hamza\Downloads\python development\browser automation\gemini video points\bulk scheduling fb videos\chrome_profile"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BLOG_POSTS_FILE = os.path.join(SCRIPT_DIR, "frontend", "src", "data", "blogPosts.js")
CHATGPT_CONFIG_FILE = os.path.join(SCRIPT_DIR, "chatgpt_config.json")

# Ghost CMS Credentials (loaded from environment variables, falls back to local values)
GHOST_API_URL = os.environ.get("GHOST_API_URL", "")
GHOST_ADMIN_API_KEY = os.environ.get("GHOST_ADMIN_API_KEY", "")
GHOST_API_VERSION = os.environ.get("GHOST_API_VERSION", "v2")
CTA_URL = os.environ.get("CTA_URL", "https://quizviral-nine.vercel.app")
BLOG_BASE_URL = os.environ.get("BLOG_BASE_URL", "https://quizviral-nine.vercel.app/blog")
PUBLISH_STATUS = os.environ.get("PUBLISH_STATUS", "published") # Default to "published"
GSC_PROPERTY = os.environ.get("GSC_PROPERTY", "https://quizviral-nine.vercel.app/")

import difflib

# Content Safety Filter for Topic Selection
SAFETY_KEYWORDS = [
    "senator", "congressman", "congresswoman", "election", "politician", 
    "governor", "president", "white house", "court", "lawsuit", 
    "sued", "indicted", "arrested", "cancer", "illness", "disease", 
    "diagnosis", "died", "death", "tragedy", "killing", "murder", 
    "accident", "hospital", "funeral", "trial", "guilty", "verdict",
    "senate", "congress", "republican", "democrat", "biden", "trump"
]

def is_safe_topic(topic):
    topic_lower = topic.lower()
    for kw in SAFETY_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", topic_lower) or kw in topic_lower:
            return False
    return True

DAILY_POST_TARGET = 3

PRODUCT_SEEDS = [
    # Cluster 1: High-Volume Trivia & Knowledge Searches (50k+ Monthly Searches)
    {
        "topic": "hard general knowledge quiz questions with answers",
        "keywords": ["general knowledge quiz", "hard trivia questions", "general knowledge test", "pub quiz general knowledge"],
        "angle": "Curate an elite set of brain-testing general knowledge questions that challenge even trivia masters, with thorough explanations for each answer."
    },
    {
        "topic": "world geography trivia quiz with country capitals",
        "keywords": ["geography trivia questions", "world capitals quiz", "country flags quiz", "world geography test"],
        "angle": "Challenge readers with intriguing borders, obscure world capitals, and country geography trivia designed for vertical video creators."
    },
    {
        "topic": "science and space trivia questions for adults",
        "keywords": ["science trivia questions", "space quiz", "astronomy trivia", "hard science questions"],
        "angle": "Explore mind-bending astronomical facts, quantum oddities, and human biology secrets that make viral short-form quiz videos."
    },
    {
        "topic": "trick questions with answers that test your brain",
        "keywords": ["trick questions with answers", "brain teasers", "riddles for adults", "lateral thinking puzzles"],
        "angle": "Share deceptive, mind-bending riddles and trick questions that force viewers to comment, debate, and rewatch short videos."
    },
    {
        "topic": "animal kingdom extreme facts quiz",
        "keywords": ["animal trivia questions", "nature quiz", "weird animal facts", "wildlife trivia"],
        "angle": "Highlight the bizarre, unbelievable defense mechanisms and habits of the animal world that captivate social media viewers."
    },
    {
        "topic": "history timeline quiz ancient civilizations to modern era",
        "keywords": ["history trivia questions", "ancient history quiz", "world history trivia", "historical events quiz"],
        "angle": "Test readers on turning points in human history, famous empires, and historical mysteries that ignite curiosity."
    },
    {
        "topic": "marvel cinematic universe ultimate trivia quiz",
        "keywords": ["marvel trivia questions", "mcu quiz", "avengers trivia", "superhero trivia"],
        "angle": "Deep dive into MCU lore, Easter eggs, comic book origins, and character trivia for passionate superhero communities."
    },
    {
        "topic": "90s nostalgia pop culture trivia questions and answers",
        "keywords": ["90s trivia questions", "90s pop culture quiz", "retro 90s quiz", "90s nostalgia trivia"],
        "angle": "Tap into retro nostalgia with 90s cartoons, music hits, iconic movies, and childhood memories that trigger massive shares."
    },
    {
        "topic": "2000s music and movies nostalgia trivia quiz",
        "keywords": ["2000s trivia", "2000s music quiz", "y2k pop culture", "2000s movie trivia"],
        "angle": "Relive the Y2K era with memorable chart-toppers, blockbuster releases, and early internet culture quiz questions."
    },
    {
        "topic": "world cup football and soccer records trivia",
        "keywords": ["football trivia questions", "soccer quiz", "world cup records", "champions league trivia"],
        "angle": "Cover historic goals, legendary players, iconic World Cup moments, and unbelievable stats that sports fans argue over."
    },
    {
        "topic": "nba basketball history and legendary records quiz",
        "keywords": ["nba trivia questions", "basketball quiz", "nba records", "basketball legends quiz"],
        "angle": "Analyze legendary buzzer beaters, championship dynasties, and individual NBA records that make great short quiz videos."
    },
    {
        "topic": "classic movie quotes and film trivia challenge",
        "keywords": ["movie trivia questions", "film quotes quiz", "cinema trivia", "famous movie quotes"],
        "angle": "Test movie buffs on unforgettable cinematic lines, Oscar records, and behind-the-scenes movie trivia."
    },
    {
        "topic": "video game history and gaming lore quiz",
        "keywords": ["gaming trivia questions", "video game quiz", "retro gaming trivia", "gaming lore quiz"],
        "angle": "Challenge gamers with hidden secrets, development Easter eggs, and historic milestones across Nintendo, PlayStation, and PC gaming."
    },
    {
        "topic": "pub quiz general knowledge rounds and ideas",
        "keywords": ["pub quiz questions", "trivia night ideas", "pub quiz rounds", "trivia night questions"],
        "angle": "Provide ready-to-use pub quiz rounds with varied difficulty, perfect for social trivia nights and community engagement."
    },
    {
        "topic": "bible trivia questions and answers for adults",
        "keywords": ["bible trivia questions", "scripture quiz", "bible trivia with answers", "old testament new testament quiz"],
        "angle": "Cover meaningful scripture passages, historical figures, and biblical stories formatted for respectful, engaging community quizzes."
    },
    {
        "topic": "food and international cuisine trivia quiz",
        "keywords": ["food trivia questions", "cuisine quiz", "international food facts", "cooking trivia"],
        "angle": "Reveal culinary origins, exotic ingredients, and surprising food science facts that make delicious visual content."
    },

    # Cluster 2: High-Demand YouTube Automation & Faceless Creator Topics
    {
        "topic": "faceless YouTube quiz channel ideas",
        "keywords": ["faceless youtube channel", "quiz channel ideas", "youtube channel ideas", "faceless creator"],
        "angle": "Explain how creators can launch a faceless channel in high-demand niches using QuizViral AI. Highlight specific channel concepts."
    },
    {
        "topic": "best quiz niches for Shorts",
        "keywords": ["quiz niches", "youtube shorts niches", "best niches for shorts", "viral shorts ideas"],
        "angle": "Detail the top performing trivia and quiz categories on YouTube Shorts and TikTok, explaining why short-form attention spans love them."
    },
    {
        "topic": "quiz video monetization breakdown",
        "keywords": ["quiz channel monetization", "youtube shorts monetization", "make money with quizzes", "youtube partner program"],
        "angle": "Analyze the revenue potential of automated quiz channels, explaining RPM, CPM, and how to combine YPP with other revenue streams."
    },
    {
        "topic": "CSV bulk video workflow tips",
        "keywords": ["bulk video creation", "csv import workflow", "scale youtube shorts", "video generator workflow"],
        "angle": "Provide a step-by-step guide on using spreadsheet templates to import 100+ questions and generate bulk videos in minutes."
    },
    {
        "topic": "how to build a viral trivia brand",
        "keywords": ["viral trivia channel", "build a trivia brand", "social media branding", "community engagement"],
        "angle": "Discuss the importance of logo, color themes, consistent templates, and community polls to build a loyal subscriber base."
    },
    {
        "topic": "YouTube Shorts vs TikTok for quiz channels",
        "keywords": ["youtube shorts vs tiktok", "short form video platforms", "quiz video reach", "audience demographics"],
        "angle": "Compare the algorithm differences, monetization features, and audience behavior on YouTube Shorts and TikTok for trivia channels."
    },
    {
        "topic": "how to write engaging trivia questions",
        "keywords": ["trivia questions", "engaging quiz questions", "how to write quizzes", "interactive content"],
        "angle": "Provide tips on crafting questions that balance difficulty, hook the viewer in the first 3 seconds, and encourage comments."
    },
    {
        "topic": "automated faceless channel mistakes to avoid",
        "keywords": ["faceless channel mistakes", "youtube automation mistakes", "scaled content abuse", "helpful content guidelines"],
        "angle": "Point out common pitfalls like poor audio quality, repetitive templates, and lack of unique angles, showing how to avoid them."
    },
    {
        "topic": "boosting audience retention on short quiz videos",
        "keywords": ["audience retention", "video watch time", "shorts retention tips", "viewer engagement"],
        "angle": "Explain tactical tricks like countdown timers, audio cues, and visual suspense to keep viewers watching until the very end."
    },
    {
        "topic": "leveraging trending news for quiz videos",
        "keywords": ["trending quiz videos", "real time content", "news trivia", "google trends workflow"],
        "angle": "Show how to quickly capitalize on trending sports matches, celebrity events, or pop culture news by spinning up timely quiz videos."
    },
    {
        "topic": "best faceless youtube niches with high cpm",
        "keywords": ["high cpm youtube niches", "faceless channel cpm", "best youtube niches 2026", "highest paying shorts niches"],
        "angle": "Analyze RPM and CPM numbers across finance, tech, trivia, and luxury niches, showing how to maximize revenue on Shorts."
    },
    {
        "topic": "how to get 10 million views on youtube shorts",
        "keywords": ["how to get views on shorts", "youtube shorts algorithm", "10 million shorts views", "viral shorts strategy"],
        "angle": "Break down the exact retention, swipe-away rate, and pacing formula needed to hit YouTube's 10M Shorts views monetization milestone."
    },
    {
        "topic": "copyright safe music and audio for faceless shorts",
        "keywords": ["copyright free music for youtube", "royalty free shorts audio", "sound effects for quiz videos", "youtube audio library"],
        "angle": "Guide creators on picking high-energy, copyright-cleared background music and sound effects that prevent Content ID claims."
    },
    {
        "topic": "how to hook viewers in the first 3 seconds on shorts",
        "keywords": ["youtube shorts hooks", "how to hook viewers", "first 3 seconds video hook", "shorts retention rate"],
        "angle": "Analyze visual and psychological hooks that drop swipe-away rates below 20% and trigger algorithmic recommendation loops."
    },
    {
        "topic": "interactive community polls and quiz strategies for creators",
        "keywords": ["youtube community tab polls", "interactive quiz posts", "grow subscribers with polls", "community engagement tips"],
        "angle": "Demonstrate how combining daily YouTube community polls with daily Shorts creates an unstoppable subscriber growth flywheel."
    }
]

# Alternate structural/phrasing templates for Turn 3 monetization section
TEMPLATES = [
    {
        "name": "Side Hustle Blueprint",
        "prompt": (
            "Write this final section using a 'Side Hustle Case Study & Step-by-Step Blueprint' structure:\n"
            "1. Use the header '<h2>Step-by-Step Guide: Launching a Quiz Channel from Scratch</h2>'. "
            "Write a practical step-by-step blueprint of how a creator can launch a channel today using QuizViral AI's "
            "1-click bulk generation from CSV spreadsheet imports, using engaging background loops (Minecraft, Space, Nature), "
            "and generating natural AI voiceovers. Explain the workflow clearly.\n"
            "2. Use the header '<h2>Monetizing Your Channel: Beyond Ad Revenue</h2>'. Explain the YouTube Partner Program (YPP) "
            "Shorts requirements (10M views in 90 days) but focus heavily on alternative monetization channels: affiliate marketing, "
            "print-on-demand merchandise, and digital trivia downloads.\n"
            "3. Use the header '<h2>Answers to Common Questions</h2>'. Provide 3 FAQs addressing time-commitment, "
            "channel originalization, and copyright safety."
        )
    },
    {
        "name": "Retention Masterclass",
        "prompt": (
            "Write this final section using a 'High-Growth Traffic & Retention Masterclass' structure:\n"
            "1. Use the header '<h2>Virality Blueprint: How QuizViral AI Automates Retention</h2>'. Focus on the psychology of "
            "viewer retention, explaining how QuizViral AI's background loops (Minecraft, Space, Nature) and realistic TTS voiceovers "
            "hook short attention spans. Detail how the CSV bulk workflow allows testing 100+ quiz video variations quickly.\n"
            "2. Use the header '<h2>The Math of a Successful Shorts Channel</h2>'. Detail the economics of the YouTube Partner Program (YPP), "
            "specifically the 10M views in 90 days requirement. Explain RPM/CPM and how to supplement it with high-ticket affiliate links "
            "and digital trivia packs.\n"
            "3. Use the header '<h2>Quiz Creator FAQ</h2>'. Provide 3 FAQs focusing on algorithm optimization, Shorts vs TikTok, "
            "and picking a viral quiz niche."
        )
    },
    {
        "name": "Efficiency Guide",
        "prompt": (
            "Write this final section using an 'Automation Tool Comparison & Efficiency Guide' structure:\n"
            "1. Use the header '<h2>Why CSV Bulk Creation Beats Manual Editing</h2>'. Compare traditional manual video editing tools "
            "with QuizViral AI's 1-click bulk generation from spreadsheet data. Focus on efficiency, template customization, and voiceovers.\n"
            "2. Use the header '<h2>Scaling to Monetization: A 90-Day Plan</h2>'. Outline a timeline-based roadmap to hit the "
            "YPP monetization threshold (10M Shorts views in 90 days) by leveraging daily bulk uploads. Explain how to sell digital "
            "trivia books and sponsorships along the way.\n"
            "3. Use the header '<h2>Frequently Asked Questions</h2>'. Provide 3 FAQs addressing daily upload frequency, managing "
            "multiple channels, and voiceover realism."
        )
    },
    {
        "name": "Creator Economy Strategy",
        "prompt": (
            "Write this final section using a 'Creator Economy & Content Strategy Analyst' structure:\n"
            "1. Use the header '<h2>Leveraging SaaS Automation for Modern Content Brands</h2>'. Analyze the rise of faceless YouTube channels, "
            "showing how QuizViral AI's automated voiceovers and video loops (Minecraft parkour, space, nature) lower the barrier to entry "
            "for creators using CSV imports.\n"
            "2. Use the header '<h2>Unlocking Multi-Stream Revenue on YouTube</h2>'. Explain the monetization roadmap, including the YPP baseline "
            "(10M Shorts views in 90 days) and how creators can build long-term value via email lists, custom merchandise, and digital downloads.\n"
            "3. Use the header '<h2>FAQ for Video Creators</h2>'. Provide 3 FAQs addressing monetization approval, channel growth expectations, "
            "and content originalization."
        )
    }
]

def parse_blog_posts():
    if not os.path.exists(BLOG_POSTS_FILE):
        return []
    try:
        with open(BLOG_POSTS_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 1. Try direct JSON parsing
        match_json = re.search(r"export const blogPosts = (\[.*\]);?\s*$", content, re.DOTALL)
        if match_json:
            try:
                parsed = json.loads(match_json.group(1).strip())
                if isinstance(parsed, list) and len(parsed) > 0:
                    return parsed
            except Exception:
                pass
                
        # 2. Universal regex parser supporting both quoted (\"title\":) and unquoted (title:)
        match_arr = re.search(r"export const blogPosts = \[(.*)\];\s*$", content, re.DOTALL)
        if not match_arr:
            return []
            
        array_content = match_arr.group(1).strip()
        title_matches = list(re.finditer(r'["\']?\btitle["\']?\s*:', array_content))
        blocks = []
        for i, m in enumerate(title_matches):
            start = m.start()
            end = title_matches[i+1].start() if i+1 < len(title_matches) else len(array_content)
            blocks.append(array_content[start:end])
            
        posts = []
        for block in blocks:
            post = {}
            fields = ["title", "slug", "excerpt", "date", "readTime", "author", "image", "pinterest_image", "metaDescription", "trendingKeyword", "topicSource", "topic_source"]
            for field in fields:
                pattern = rf'["\']?\b{field}["\']?\s*:\s*[\'"`]([^\'"`]+?)[\'"`]'
                f_match = re.search(pattern, block)
                if f_match:
                    post[field] = f_match.group(1).strip()
            
            content_match = re.search(r'["\']?\bcontent["\']?\s*:\s*[\'"`](.*?)[\'"`],?\s*(?:["\']?\b\w+["\']?:|}$)', block, re.DOTALL)
            if content_match:
                post["content"] = content_match.group(1).strip()
            else:
                content_match = re.search(r'["\']?\bcontent["\']?\s*:\s*[\'"`](.*?)[\'"`]', block, re.DOTALL)
                if content_match:
                    post["content"] = content_match.group(1).strip()
            posts.append(post)
        return posts
    except Exception as e:
        print(f"Error parsing blog posts: {e}")
        return []

def determine_next_topic_source(posts):
    today_str = datetime.now().strftime("%B %d, %Y")
    today_posts = [p for p in posts if p.get("date") == today_str]
    
    if len(today_posts) > 0:
        product_today = sum(1 for p in today_posts if p.get("topicSource", p.get("topic_source", "trend")) == "product")
        total_today = len(today_posts)
        if (product_today / total_today) < 0.40:
            return "product"
        else:
            return "trend"
            
    if len(posts) > 0:
        recent_posts = posts[:10]
        product_recent = sum(1 for p in recent_posts if p.get("topicSource", p.get("topic_source", "trend")) == "product")
        total_recent = len(recent_posts)
        if (product_recent / total_recent) < 0.40:
            return "product"
        else:
            return "trend"
            
    return "trend" if random.random() < 0.60 else "product"

def select_next_product_topic(posts):
    existing_slugs_and_titles = []
    for p in posts:
        existing_slugs_and_titles.append(p.get("slug", "").lower().strip())
        existing_slugs_and_titles.append(p.get("title", "").lower().strip())
        existing_slugs_and_titles.append(p.get("trendingKeyword", "").lower().strip())
        
    unused_seeds = []
    for seed in PRODUCT_SEEDS:
        topic_lower = seed["topic"].lower().strip()
        topic_slug = topic_lower.replace(" ", "-")
        is_used = False
        for est in existing_slugs_and_titles:
            if topic_lower == est or topic_slug == est or topic_slug in est:
                is_used = True
                break
        if not is_used:
            unused_seeds.append(seed)
            
    if unused_seeds:
        selected = unused_seeds[0]
        print(f"[Topic Selector] Selected unused product seed topic: '{selected['topic']}'")
        return selected
    else:
        # Dynamic fallback: if all static seeds have been used, pick a category and generate an unpublished variation
        import random
        base_seed = random.choice(PRODUCT_SEEDS)
        curr_year = datetime.now().year
        variant_suffix = random.choice(["Ultimate Edition", f"{curr_year} Strategy", "Master Guide", "Step-by-Step", "Pro Tips"])
        new_topic = f"{base_seed['topic']} {variant_suffix}"
        
        counter = 1
        while any(new_topic.lower() in est for est in existing_slugs_and_titles):
            new_topic = f"{base_seed['topic']} Part {counter}"
            counter += 1
            
        selected = {
            "topic": new_topic,
            "keywords": base_seed["keywords"],
            "angle": f"{base_seed['angle']} Focus on fresh 2026 insights and updated strategies."
        }
        print(f"[Topic Selector] All base seeds used. Generated fresh unique topic: '{selected['topic']}'")
        return selected

def get_string_similarity(str1, str2):
    return difflib.SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

def extract_intro_opening(markdown_content):
    # Convert literal \n escapes to actual newlines
    markdown_content = markdown_content.replace('\\n', '\n')
    # Remove image markdown
    cleaned = re.sub(r'!\[.*?\]\(.*?\)', '', markdown_content)
    # Remove headers (lines starting with #)
    lines = cleaned.split('\n')
    text_lines = []
    for line in lines:
        line_strip = line.strip()
        if not line_strip:
            continue
        if line_strip.startswith('#'):
            continue
        text_lines.append(line_strip)
    
    full_text = " ".join(text_lines)
    return full_text[:100].strip()

def extract_monetization_text(markdown_content):
    # Convert literal \n escapes to actual newlines
    markdown_content = markdown_content.replace('\\n', '\n')
    parts = re.split(r'\n##\s+', markdown_content)
    monetization_parts = []
    for part in parts:
        part_lower = part.lower()
        if "quizviral" in part_lower or "monetiz" in part_lower or "revenue" in part_lower or "shorts views" in part_lower:
            monetization_parts.append(part.strip())
    
    if monetization_parts:
        return "\n".join(monetization_parts)
    
    content_len = len(markdown_content)
    return markdown_content[int(content_len * 0.7):]

## ==================== GOOGLE SEARCH CONSOLE INTEGRATION ====================

def get_gsc_property_identifiers():
    """
    Returns valid GSC property variations to check.
    Supports URL Prefix (https://quizviral-nine.vercel.app/) and Domain Property (sc-domain:quizviral-nine.vercel.app).
    """
    prop = GSC_PROPERTY.rstrip('/') + '/'
    domain = urllib.parse.urlparse(GSC_PROPERTY).netloc
    variants = [prop]
    if domain:
        variants.append(f"sc-domain:{domain}")
    variants.append(prop.rstrip('/'))
    return variants

def request_gsc_indexing_playwright(context, post_url):
    print(f"\n--- Google Search Console URL Inspection for: '{post_url}' ---")
    page = None
    try:
        page = context.new_page()
        post_url_encoded = urllib.parse.quote(post_url, safe="")
        
        # Strategy 1: Direct inspection navigation with properly URL-encoded property
        inspected = False
        properties_to_try = get_gsc_property_identifiers()
        
        for prop in properties_to_try:
            prop_encoded = urllib.parse.quote(prop, safe="")
            direct_url = f"https://search.google.com/search-console/inspect?resource_id={prop_encoded}&id={post_url_encoded}"
            print(f"Trying direct inspection with resource_id '{prop}'...")
            try:
                page.goto(direct_url, timeout=30000)
                time.sleep(5)
                
                page_title = page.title()
                curr_url = page.url.lower()
                body_text = page.locator("body").inner_text()
                
                if "Sign in" in page_title or "accounts.google.com" in curr_url:
                    print("[GSC Notice] Google session expired. Please sign into Google in Chrome profile.")
                    page.close()
                    return
                    
                if "404" in page_title or "welcome" in curr_url or "404. That's an error" in body_text:
                    print(f"[GSC Notice] Property '{prop}' returned 404/welcome. Trying next format...")
                    continue
                    
                inspected = True
                print(f"Direct inspection URL loaded successfully with property '{prop}'!")
                break
            except Exception as direct_err:
                print(f"Direct inspection attempt failed: {direct_err}")
                
        # Strategy 2: If direct navigation didn't work, go to generic GSC home and use the top universal search bar
        if not inspected:
            print("Navigating to GSC Home to use universal search bar...")
            page.goto("https://search.google.com/search-console", timeout=45000)
            time.sleep(5)
            
            search_input = page.locator("input[aria-label*='Inspect any URL' i], input[placeholder*='Inspect any URL' i], input[type='search'], header input[type='text'], #input-wrapper input").first
            try:
                search_input.wait_for(state="visible", timeout=15000)
                print("Found GSC universal search bar. Submitting URL...")
                search_input.click()
                search_input.fill(post_url)
                time.sleep(1)
                search_input.press("Enter")
                inspected = True
                time.sleep(8)
            except Exception as bar_err:
                print(f"Could not submit via universal search bar: {bar_err}")

        # Wait for inspection status to finish retrieving data
        print("Waiting for inspection retrieval to complete...")
        try:
            page.wait_for_selector(
                "button:has-text('Request indexing'), text=Request indexing, text=URL is on Google, text=URL is not on Google, text=Test live URL",
                timeout=30000
            )
        except Exception:
            pass
            
        time.sleep(3)
        page_text = page.locator("body").inner_text()
        
        # Check if already indexed
        is_confirmed_indexed = any(x in page_text for x in ["URL is on Google", "URL is in the Google index"])
        
        # Look for "Request indexing" button
        req_selectors = [
            "button:has-text('Request indexing')",
            "div[role='button']:has-text('Request indexing')",
            "button:has-text('REQUEST INDEXING')",
            "div[role='button']:has-text('REQUEST INDEXING')",
            "[aria-label*='Request indexing' i]"
        ]
        
        clicked = False
        for sel in req_selectors:
            try:
                btn = page.locator(sel).first
                if btn.is_visible() and btn.is_enabled():
                    print(f"Found Request Indexing button ({sel}). Clicking...")
                    btn.click()
                    clicked = True
                    break
            except Exception:
                pass
                
        if not clicked:
            try:
                btn_fallback = page.get_by_text("Request indexing", exact=False).first
                if btn_fallback.is_visible():
                    btn_fallback.click(timeout=4000)
                    clicked = True
                    print("Clicked Request Indexing via get_by_text.")
            except Exception:
                pass

        if clicked:
            print("Request indexing clicked! Waiting for live test to complete (up to 120 seconds)...")
            start_wait = time.time()
            success_detected = False
            
            while time.time() - start_wait < 120:
                body_content = page.locator("body").inner_text()
                
                # Check for success
                if any(k in body_content for k in ["Indexing requested", "added to a priority crawl", "Priority crawl queue"]):
                    print("SUCCESS: Google Search Console confirmed 'Indexing requested'!")
                    success_detected = True
                    break
                elif any(k in body_content for k in ["Quota exceeded", "Daily quota reached", "limit reached", "try again tomorrow"]):
                    print("WARNING: Google Search Console indexing quota reached for today.")
                    break
                time.sleep(3)
                
            # Dismiss confirmation modal
            try:
                got_it = page.locator("button:has-text('Got it'), button:has-text('OK'), button:has-text('Dismiss'), button:has-text('GOT IT')").first
                if got_it.is_visible():
                    got_it.click()
                    print("Dismissed confirmation modal.")
            except Exception:
                pass
        else:
            if is_confirmed_indexed:
                print("URL is confirmed already indexed on Google.")
            else:
                print("Note: 'Request indexing' button was not available or already requested.")

    except Exception as e:
        print(f"Warning: GSC URL inspection encountered an issue: {e}")
    finally:
        if page:
            try:
                page.close()
            except Exception:
                pass

def resubmit_sitemap_gsc_playwright(context):
    print("\n--- Google Search Console Sitemap Resubmission ---")
    page = None
    try:
        page = context.new_page()
        
        # Navigate to Sitemaps page
        sitemaps_loaded = False
        for prop in get_gsc_property_identifiers():
            prop_encoded = urllib.parse.quote(prop, safe="")
            sitemaps_url = f"https://search.google.com/search-console/sitemaps?resource_id={prop_encoded}"
            print(f"Navigating to GSC Sitemaps with resource_id '{prop}'...")
            try:
                page.goto(sitemaps_url, timeout=30000)
                time.sleep(5)
                
                page_title = page.title()
                curr_url = page.url.lower()
                body_text = page.locator("body").inner_text()
                
                if "404" in page_title or "welcome" in curr_url or "404. That's an error" in body_text:
                    print(f"Property '{prop}' sitemaps returned 404/welcome. Trying next format...")
                    continue
                    
                sitemaps_loaded = True
                print(f"Sitemaps page loaded successfully with property '{prop}'!")
                break
            except Exception as se_err:
                print(f"Sitemap page load failed for {prop}: {se_err}")
                
        if not sitemaps_loaded:
            print("Navigating to GSC Sitemaps fallback without resource_id...")
            page.goto("https://search.google.com/search-console/sitemaps", timeout=30000)
            time.sleep(5)
            
        # Locate the 'Add a new sitemap' input field
        print("Looking for sitemap input field...")
        input_selectors = [
            "input[name='sitemapPath']",
            "input[aria-label*='sitemap' i]",
            "input[placeholder*='sitemap' i]",
            "mwc-textfield input",
            "input[type='text']"
        ]
        
        sitemap_input = None
        for sel in input_selectors:
            try:
                elem = page.locator(sel).first
                if elem.is_visible():
                    sitemap_input = elem
                    break
            except Exception:
                pass
                
        if sitemap_input:
            print("Entering 'sitemap.xml' into sitemap field...")
            sitemap_input.click()
            sitemap_input.fill("sitemap.xml")
            time.sleep(1)
            
            submit_selectors = [
                "button:has-text('Submit')",
                "button:has-text('SUBMIT')",
                "div[role='button']:has-text('Submit')",
                "div[role='button']:has-text('SUBMIT')"
            ]
            submitted = False
            for s_sel in submit_selectors:
                try:
                    s_btn = page.locator(s_sel).first
                    if s_btn.is_visible() and s_btn.is_enabled():
                        s_btn.click()
                        submitted = True
                        print(f"Clicked Submit button ({s_sel}).")
                        break
                except Exception:
                    pass
                    
            if not submitted:
                print("Pressing Enter to submit sitemap...")
                sitemap_input.press("Enter")
                submitted = True
                
            time.sleep(5)
            try:
                dismiss_btn = page.locator("button:has-text('Got it'), button:has-text('Dismiss'), button:has-text('OK'), button:has-text('GOT IT')").first
                if dismiss_btn.is_visible():
                    dismiss_btn.click()
                    print("Dismissed sitemap confirmation dialog.")
            except Exception:
                pass
            print("Sitemap resubmission complete!")
        else:
            print("Warning: Could not locate sitemap input field. Saving screenshot for review...")
            screenshot_path = os.path.join(SCRIPT_DIR, "assets", f"gsc_sitemap_failed_{int(time.time())}.png")
            try:
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                page.screenshot(path=screenshot_path)
            except Exception:
                pass
    except Exception as e:
        print(f"Warning: GSC sitemap resubmission failed: {e}")
    finally:
        if page:
            try:
                page.close()
            except Exception:
                pass


def verify_live_sitemap(local_count):
    print(f"\n--- Verifying Live Sitemap (Target Count: {local_count}) ---")
    live_url = "https://quizviral-nine.vercel.app/sitemap.xml"
    
    for attempt in range(5):
        print(f"Fetch attempt {attempt + 1}/5...")
        try:
            import ssl
            context = ssl._create_unverified_context()
            req = urllib.request.Request(
                live_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            with urllib.request.urlopen(req, timeout=15, context=context) as response:
                if response.getcode() == 200:
                    content = response.read()
                    root = ET.fromstring(content)
                    locs = root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                    live_count = len(locs)
                    print(f"  Live sitemap contains {live_count} URLs.")
                    if live_count == local_count:
                        print("  SUCCESS: Live sitemap matches the local sitemap count!")
                        return True
                    else:
                        print(f"  Count mismatch (live: {live_count}, local: {local_count}). Vercel build might still be running...")
                else:
                    print(f"  Received non-200 status code: {response.getcode()}")
        except Exception as e:
            print(f"  Error fetching/parsing live sitemap: {e}")
        
        if attempt < 4:
            time.sleep(30)
            
    print("  WARNING: Live sitemap count does not match local count after 2.5 minutes.")
    print("  This could indicate that Vercel is still building, deployment failed, or there is an edge cache issue.")
    return False

def validate_meta_title_robust(title):
    title = title.strip()
    # Remove any existing trailing dots
    title = re.sub(r'\.{2,}$', '', title).strip()
    
    if len(title) < 40:
        title = f"{title} | QuizViral AI Video Generator"
    elif len(title) < 50:
        title = f"{title} | QuizViral AI"
        
    if len(title) > 60:
        truncated = title[:57]
        last_sep = max(truncated.rfind(' '), truncated.rfind('|'), truncated.rfind('-'))
        if last_sep > 35:
            title = title[:last_sep].strip()
        else:
            title = truncated.strip()
    return title

def validate_meta_description_robust(desc):
    desc = desc.strip()
    # Remove any existing trailing dots
    desc = re.sub(r'\.{2,}$', '', desc).strip()
    
    if len(desc) < 120:
        desc = f"{desc} Create automated viral quiz videos with QuizViral AI bulk video generator."
    elif len(desc) < 140:
        desc = f"{desc} Learn how to turn this topic into viral short-form trivia."
        
    if len(desc) > 160:
        sentence_end = -1
        for match in re.finditer(r'([.!?])(?:\s+|$)', desc[:160]):
            end_idx = match.end(1)
            if 130 <= end_idx <= 160:
                sentence_end = end_idx
        if sentence_end != -1:
            desc = desc[:sentence_end].strip()
        else:
            truncated = desc[:155]
            last_space = truncated.rfind(' ')
            if last_space > 110:
                desc = desc[:last_space].strip() + "."
            else:
                desc = truncated.strip() + "."
    return desc


# Imports from helper script for interlinking and alt-tags
try:
    from ghost_blog_automation import (
        validate_meta_title,
        validate_meta_description,
        apply_smart_interlinking,
        set_image_alt_tags,
        load_existing_blogs
    )
except ImportError:
    validate_meta_title = validate_meta_title_robust
    validate_meta_description = validate_meta_description_robust
    def apply_smart_interlinking(h, b, c, u): return h
    def set_image_alt_tags(h, k, t): return h
    def load_existing_blogs(s): return {}

# ==================== HELPERS ====================

def check_port_open(port):
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except Exception:
        return False

def kill_chrome_on_port_9222():
    print("Checking if port 9222 is busy...")
    try:
        output = subprocess.check_output("netstat -aon", shell=True).decode('utf-8', errors='ignore')
        for line in output.splitlines():
            if ":9222" in line and "LISTENING" in line:
                parts = line.strip().split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    print(f"Terminating Chrome process (PID: {pid}) listening on port 9222...")
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    time.sleep(2)
                    return True
    except Exception as e:
        print(f"Error terminating Chrome process: {e}")
    return False

def launch_chrome_if_needed():
    # Force kill any active debug Chrome instances first to ensure a fresh session with our new flags!
    kill_chrome_on_port_9222()
    
    if check_port_open(9222):
        print("Chrome remote debugger is already running on port 9222.")
        return True
        
    print("Launching Chrome in headful mode for Playwright remote connection...")
    paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Google\Chrome\Application\chrome.exe")
    ]
    
    chrome_path = None
    for p in paths:
        if os.path.exists(p):
            chrome_path = p
            break
            
    if not chrome_path:
        import shutil
        chrome_path = shutil.which("chrome") or shutil.which("chrome.exe")
        
    if not chrome_path:
        print("Error: Could not locate chrome.exe automatically.")
        return False
        
    cmd = [
        chrome_path,
        "--remote-debugging-port=9222",
        f"--user-data-dir={CHROME_PROFILE_PATH}",
        "--disable-extensions",
        "--disable-component-extensions-with-background-pages",
        "--no-default-browser-check",
        "--no-first-run",
        "--disable-default-apps",
        "--disable-sync",
        "--disable-session-crashed-bubble",
        "--hide-crash-restore-bubble",
        "--disable-blink-features=AutomationControlled",
        "--disable-gpu",
        "--window-position=0,0",
        "--window-size=1280,720",
        "--start-maximized",
        "about:blank"
    ]
    
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(8):
            time.sleep(1)
            if check_port_open(9222):
                print("Chrome started and listening on port 9222 successfully!")
                return True
        return False
    except Exception as e:
        print(f"Failed to launch Chrome: {e}")
        return False

def clean_markdown_response(text):
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```markdown\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    if text.endswith("```"):
        text = text[:-3].strip()
    return text

def fallback_json_parser(raw_json):
    try:
        keys = [
            "title", "slug", "excerpt", "meta_title", "meta_description", "html", "markdown",
            "landscape_image_prompt", "landscape_prompt", "image_prompt",
            "vertical_image_prompt", "vertical_prompt", "pinterest_prompt", "pinterest_image_prompt"
        ]
        key_positions = []
        for k in keys:
            pattern = rf'"{k}"\s*:'
            match = re.search(pattern, raw_json)
            if match:
                key_positions.append((match.start(), match.end(), k))
        
        if not key_positions:
            return None
            
        key_positions.sort(key=lambda x: x[0])
        data = {}
        for i, (start, end, key) in enumerate(key_positions):
            if i + 1 < len(key_positions):
                next_start = key_positions[i+1][0]
            else:
                next_start = len(raw_json)
                
            val_str = raw_json[end:next_start].strip()
            if val_str.endswith(","):
                val_str = val_str[:-1].strip()
            if i == len(key_positions) - 1:
                if val_str.endswith("}"):
                    val_str = val_str[:-1].strip()
            
            if val_str.startswith('"'):
                val_str = val_str[1:]
            if val_str.endswith('"'):
                val_str = val_str[:-1]
                
            val_str = val_str.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
            data[key] = val_str
            
        return data
    except Exception as e:
        print(f"Fallback JSON regex parser failed: {e}")
    return None
def extract_assistant_text(element_or_text):
    if not element_or_text:
        return ""
    if hasattr(element_or_text, "inner_text"):
        try:
            text = element_or_text.inner_text().strip()
        except Exception:
            return ""
    else:
        text = str(element_or_text).strip()
    
    # Strip any leading 'ChatGPT said:\n' or 'ChatGPT said:' prefix from UI turn headers
    cleaned = re.sub(r"^ChatGPT said:\s*", "", text, flags=re.IGNORECASE)
    return cleaned.strip()

def get_assistant_messages(page):
    selectors = [
        "div[class*='MarkdownRoot']",
        "[data-content-search-unit-key*='assistant']",
        "[data-content-search-unit-key$=':assistant']",
        "div[data-message-author-role='assistant'] .markdown",
        "div[data-message-author-role='assistant']",
        "article[data-testid^='conversation-turn'] .markdown",
        "article[data-testid^='conversation-turn']",
        "div.agent-turn",
        ".markdown",
        ".message-content"
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel)
            if loc.count() > 0:
                return loc
        except Exception:
            pass
    return page.locator("div[class*='MarkdownRoot']")

def get_chatgpt_send_button(page):
    send_button_selectors = [
        "button[data-testid='send-button']",
        "button[data-testid='fruitjuice-send-button']",
        "button[aria-label*='Send' i]",
        "button[aria-label*='Submit' i]",
        "#send-button",
        "button.send-button",
        "form button[type='submit']",
        "button:has(svg[data-icon='arrow-up'])",
        "button:has(svg path[d*='M.5 1.5'])"
    ]
    for sel in send_button_selectors:
        try:
            loc = page.locator(sel)
            if loc.count() > 0:
                for i in range(loc.count()):
                    btn = loc.nth(i)
                    if btn.is_visible():
                        return btn
        except Exception:
            pass
    return None

def is_chatgpt_send_button_enabled(page):
    btn = get_chatgpt_send_button(page)
    if btn:
        try:
            return btn.is_enabled()
        except Exception:
            pass
    return False

def wait_for_chatgpt_response(page, initial_count=0, initial_last_text="", max_wait_seconds=180):
    print("Waiting for ChatGPT response...")
    start_time = time.time()
    
    # 1. Wait for generation to start (up to 15 seconds)
    generation_started = False
    for _ in range(15):
        stop_btns = page.locator("button[data-testid='stop-button'], button[aria-label='Stop generating'], button[aria-label*='Stop' i], button:has(svg rect)").all()
        if any(b.is_visible() for b in stop_btns):
            generation_started = True
            break
            
        msgs = get_assistant_messages(page)
        curr_count = msgs.count()
        if curr_count > initial_count:
            generation_started = True
            break
        elif curr_count > 0 and curr_count == initial_count:
            try:
                curr_text = extract_assistant_text(msgs.last)
                if curr_text and curr_text != initial_last_text:
                    generation_started = True
                    break
            except Exception:
                pass
                
        time.sleep(1)

    if not generation_started:
        print("Notice: Generation start not detected yet. Checking buttons and Enter key...")
        btn = get_chatgpt_send_button(page)
        if btn and btn.is_visible() and btn.is_enabled():
            try:
                btn.click(timeout=2000)
            except Exception:
                pass
        try:
            page.keyboard.press("Enter")
        except Exception:
            pass
        time.sleep(2)

    last_text = ""
    stable_count = 0
    
    while time.time() - start_time < max_wait_seconds:
        # Check Stop button visibility in ChatGPT
        stop_btns = page.locator("button[data-testid='stop-button'], button[aria-label='Stop generating'], button[aria-label*='Stop' i], button:has(svg rect)").all()
        is_stop_visible = False
        for btn in stop_btns:
            try:
                if btn.is_visible():
                    is_stop_visible = True
                    break
            except Exception:
                pass
                
        # Get latest assistant message text
        msgs = get_assistant_messages(page)
        curr_count = msgs.count()
        current_text = ""
        if curr_count > 0:
            try:
                current_text = extract_assistant_text(msgs.last)
            except Exception:
                pass

        # Is this a genuinely NEW response?
        is_new_message = (curr_count > initial_count) or (current_text != initial_last_text and len(current_text) > 5)
            
        # Completion signals:
        if is_new_message and len(current_text) > 5 and not is_stop_visible:
            # Check turn state or action buttons in modern ChatGPT
            turn_complete = False
            try:
                has_action_btn = page.locator("button[aria-label='Copy'], button[aria-label='Regenerate response']").count() > 0
                has_complete_state = page.locator("[data-talvt-turn-state='complete']").count() > 0
                if has_action_btn or has_complete_state:
                    turn_complete = True
            except Exception:
                pass

            if current_text == last_text:
                stable_count += 1
                if (turn_complete and stable_count >= 1) or stable_count >= 2:
                    print(f"Generation complete! Response length: {len(current_text)} characters.")
                    return current_text
            else:
                stable_count = 0
        elif is_stop_visible:
            stable_count = 0
                
        last_text = current_text
        time.sleep(2)
        
    msgs = get_assistant_messages(page)
    if msgs.count() > 0:
        try:
            final_text = extract_assistant_text(msgs.last)
            if final_text != initial_last_text and len(final_text) > 5:
                return final_text
        except Exception:
            pass
    return ""

def is_keyword_already_published(keyword):
    if not os.path.exists(BLOG_POSTS_FILE):
        return False
    try:
        with open(BLOG_POSTS_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Exact extraction helper
        def extract_quotes(field):
            return re.findall(rf"{field}:\s*['\"`]([^'\"`]+?)['\"`]", content)
            
        titles = extract_quotes("title")
        slugs = extract_quotes("slug")
        trending_keywords = extract_quotes("trendingKeyword")
        
        kw_lower = keyword.lower().strip()
        for tk in trending_keywords:
            if kw_lower == tk.lower().strip() or kw_lower in tk.lower().strip():
                return True
        for t in titles:
            if kw_lower in t.lower():
                return True
        for s in slugs:
            if kw_lower.replace(" ", "-") in s.lower():
                return True
    except Exception as e:
        print(f"Error checking duplicate posts: {e}")
    return False

# ==================== STEP 1: GOOGLE TRENDS US SCRAPING ====================

def get_trends_from_page_and_rss(page):
    """
    Playwright se Google Trends site ko scrape karta hai.
    Sath hi, RSS feed ko backup backup backup ke roop me use karta hai agar block ho jaye.
    """
    trends = []
    print("\n--- STEP 1: Scraping Google Trends US Page ---")
    try:
        page.goto("https://trends.google.com/trending?geo=US")
        # Allow sufficient time for the grid and content to load
        time.sleep(8)
        
        # Extract all visible text lines from the body
        body_text = page.locator("body").inner_text()
        lines = [line.strip() for line in body_text.split("\n") if line.strip()]
        
        for i in range(len(lines) - 1):
            line = lines[i]
            next_line = lines[i+1]
            
            # Check if the next line represents a search volume indicator (e.g. 2M+, 500K+, 10K+)
            # Starts with a number, ends with '+'
            if re.match(r'^\d+.*?\+$', next_line):
                # Clean candidate keyword
                if len(line) > 2 and len(line) < 50:
                    if not any(x in line.lower() for x in ["search", "explore", "trending", "active", "arrow", "percent", "hours ago"]):
                        if line not in trends:
                            trends.append(line)
    except Exception as e:
        print(f"Error scraping Trends page: {e}")

    # Fallback to RSS feed if we got less than 5 items
    if len(trends) < 5:
        print("Scraping page returned less than 5 trends. Launching Google Trends RSS Feed Fallback...")
        try:
            url = "https://trends.google.com/trending/rss?geo=US"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            import ssl
            context = ssl._create_unverified_context()
            with urllib.request.urlopen(req, timeout=10, context=context) as response:
                xml_data = response.read()
            root = ET.fromstring(xml_data)
            items = root.findall(".//item")
            for item in items:
                title_el = item.find("title")
                if title_el is not None and title_el.text:
                    val = title_el.text.strip()
                    if val not in trends:
                        trends.append(val)
        except Exception as ex:
            print(f"Trends RSS Fallback failed: {ex}")
            
    # Filters out already published topics
    filtered_trends = []
    for t in trends:
        if not is_keyword_already_published(t):
            filtered_trends.append(t)
            
    print(f"Discovered {len(trends)} topics. Non-published trends: {len(filtered_trends)}")
    
    # If all published, use original trends
    if not filtered_trends:
        filtered_trends = trends
        
    return filtered_trends[:5]

# ==================== STEP 2: GOOGLE AUTOCOMPLETE RESEARCH ====================

def create_safe_image_prompt(post_title, format_type="landscape"):
    """
    Creates a conceptual, generic image prompt from a post title.
    Removes real names or celebrity references, and focuses on core concepts
    (e.g., sports/basketball, technology, space, etc.) to comply with safety guidelines.
    Ensures that the output style is photorealistic and resembles a real-life photograph.
    """
    title_lower = post_title.lower()
    
    # Heuristics for common niches targeting photorealistic photography
    concept = "a realistic, professional close-up photograph of a clean, modern desk showing signs of success and growth, with warm natural lighting and soft background focus"
    if any(x in title_lower for x in ["marvin bagley", "nba", "basketball", "player", "sports"]):
        concept = "a realistic, professional sports action photograph taken from the court sideline, showing a basketball player silhouette jumping to dunk into a hoop, dramatic arena lighting, motion blur on the player, crisp details on the net and backboard"
    elif any(x in title_lower for x in ["space", "galaxy", "universe", "planet"]):
        concept = "a high-resolution, detailed space exploration photograph of a rocket launching and ascending, shot with a telephoto lens, surrounded by realistic billowing smoke, bright fiery exhaust engine glow, clear blue sky background"
    elif any(x in title_lower for x in ["money", "monetiz", "income", "cash", "wealth"]):
        concept = "a professional, realistic corporate-style close-up photograph of a clean glass table with a smartphone showing stock market growth charts, high-end camera bokeh, warm natural window light reflections, professional office setup"
    elif any(x in title_lower for x in ["video", "youtube", "tiktok", "shorts", "creator"]):
        concept = "a high-quality, realistic photograph of a modern tech setup for content creation, featuring a professional camera on a tripod, a glowing softbox light, and a clean desk background, shot with shallow depth of field"
    elif any(x in title_lower for x in ["discover", "seo", "google", "traffic", "search"]):
        concept = "a high-quality, clean product photo of a glowing digital tablet on a modern workspace desk, displaying elegant server logs and network maps, sharp details, warm background depth"
    else:
        # General backup: extract main terms and build a generic prompt
        words = [w for w in re.split(r'\W+', post_title) if len(w) > 3]
        if words:
            concept = f"a realistic professional photograph representing the theme of {', '.join(words[:3])}, captured with high-end camera equipment, natural shadows, realistic textures, highly detailed"
            
    if format_type == "landscape":
        prompt = (
            f"Generate a high-quality photorealistic landscape photograph (16:9 aspect ratio) representing: {concept}. "
            "Ensure it looks like a real-life, professional camera photo with natural lighting, sharp focus, realistic textures, and shadows. "
            "Do not make it look like an illustration, drawing, 3D render, cartoon, anime, or digital art. "
            "Do not depict any real-life individuals by name or face. "
            "Do not write any text, letters, or words on the image."
        )
    else:
        prompt = (
            f"Generate a vertical version (9:16 aspect ratio) of the exact same image (matching the same style, lighting, realistic photograph format, and content) representing: {concept}. "
            "Ensure it is a realistic photograph and does not include any text, letters, or words on the image."
        )
        
    return prompt

def get_autocomplete_suggestions(page, topic):
    """
    Topic ko Google Search box me dalta hai aur space ke baad letters (a, b, y, z)
    daal kar autocomplete suggestions ko scrape karta hai. (No CAPTCHA block issues).
    """
    print(f"\n--- STEP 2: Performing Google Autocomplete suggestion scraping for: '{topic}' ---")
    suggestions = set()
    
    try:
        page.goto("https://www.google.com")
        time.sleep(3)
        
        search_box = page.locator('textarea[name="q"], input[name="q"], [title="Search"]').first
        search_box.click()
        time.sleep(1)
        
        # Loop through the entire alphabet a to z to harvest all related keywords
        letters = [chr(i) for i in range(ord('a'), ord('z') + 1)]
        for l in letters:
            query = f"{topic} {l}"
            print(f"Typing query suggestion sequence: '{query}'...")
            search_box.fill(query)
            time.sleep(1.5) # Dropdown loading wait
            
            # Scrape suggestion spans
            elements = page.locator('ul[role="listbox"] li div[role="option"] span').all_inner_texts()
            if not elements:
                elements = page.locator('ul[role="listbox"] li span').all_inner_texts()
                
            for el in elements:
                val = el.strip()
                if val and val.lower() != query.lower():
                    # If Google returns only the highlighted suffix, rebuild it
                    if not val.lower().startswith(topic.lower()):
                        val = f"{topic} {val}"
                    suggestions.add(val)
    except Exception as e:
        print(f"Autocomplete suggestions scraping failed: {e}")
        
    print(f"Found {len(suggestions)} suggestions.")
    return list(suggestions)

# ==================== STEP 3: GEMINI IMAGE DOWNLOAD ====================

def get_candidate_images(page):
    all_imgs = page.locator("img").all()
    candidate_imgs = []
    for img in all_imgs:
        try:
            src = img.get_attribute("src") or ""
            # Filter out UI/logo/avatar images
            is_ui_element = any(x in src.lower() for x in ["cot_logo", "orbit", "avatar", "logo", "icon", "static"])
            is_valid_source = src.startswith("http") or src.startswith("blob:")
            
            if is_valid_source and not is_ui_element:
                if img.is_visible():
                    # Validate that it is a reasonably sized image (generated images are large)
                    box = img.bounding_box()
                    if box and box["width"] > 100 and box["height"] > 100:
                        candidate_imgs.append(img)
        except Exception:
            pass
    return candidate_imgs

def download_meta_ai_image(context, prompt, output_path, chat_url):
    """
    Meta AI web interface ke zariye image generate aur download karta hai.
    """
    print(f"Generating image on Meta AI via URL: {chat_url}")
    print(f"Prompt: '{prompt[:100]}...'")
    try:
        page = context.new_page()
        
        # Navigate with retry logic for network/DNS robustness
        max_retries = 3
        for attempt in range(max_retries):
            try:
                page.goto(chat_url, timeout=30000)
                break
            except Exception as ge:
                if attempt == max_retries - 1:
                    raise ge
                print(f"Navigation failed ({ge}). Retrying in 5 seconds...")
                time.sleep(5)
                
        time.sleep(8) # Stabilize load
        
        # Locate the contenteditable input field
        input_element = page.locator('div[contenteditable="true"]').first
        if input_element.count() == 0:
            input_element = page.get_by_role("textbox").first
            
        if input_element.count() == 0:
            print("Error: Could not locate input box on Meta AI page.")
            page.close()
            return False
            
        # Get initial candidate images count before sending the prompt
        initial_candidates = get_candidate_images(page)
        initial_count = len(initial_candidates)
        print(f"Initial generated images in chat history: {initial_count}")
        
        # Fill the prompt
        input_element.click()
        input_element.fill(prompt)
        time.sleep(1)
        
        # Click the Send button
        send_btn = page.locator("button[aria-label='Send']").first
        if send_btn.count() > 0:
            print("Clicking Send button...")
            send_btn.click()
        else:
            print("Pressing Enter to send...")
            input_element.press("Enter")
            
        time.sleep(3)
        
        # Dismiss potential login modal ONLY if it is a real login/signup dialog (prevents image generation cancellation)
        modal_visible = False
        dialogs = page.locator("div[role='dialog'], div[data-slot='dialog-content'], [class*='dialog-overlay']").all()
        for d in dialogs:
            try:
                if d.is_visible():
                    text_content = d.inner_text().lower()
                    if any(kw in text_content for kw in ["log in", "sign up", "continue with", "connect your"]):
                        modal_visible = True
                        break
            except Exception:
                pass
                
        if modal_visible:
            print("Login dialog detected. Dismissing with Escape key...")
            page.keyboard.press("Escape")
            time.sleep(1)
        
        # Dynamic polling: Wait for the number of generated images to increase
        print("Waiting for new images to generate on Meta AI...")
        start_time = time.time()
        generation_timeout = 90  # Allow up to 90 seconds
        new_images_detected = False
        
        while time.time() - start_time < generation_timeout:
            current_candidates = get_candidate_images(page)
            if len(current_candidates) > initial_count:
                print(f"Success: New images detected! Count increased from {initial_count} to {len(current_candidates)}.")
                time.sleep(5) # Let them render completely
                new_images_detected = True
                break
            time.sleep(2)
            
        if not new_images_detected:
            print("Timeout: New images were not generated or detected within 90 seconds.")
            # Fallback check: if there are any candidate images, try using the last 4 anyway
            current_candidates = get_candidate_images(page)
            if not current_candidates:
                try:
                    page.screenshot(path=os.path.join(os.path.dirname(output_path), "meta_ai_generation_failed.png"))
                except Exception:
                    pass
                page.close()
                return False
        else:
            current_candidates = get_candidate_images(page)
            
        # Select from the latest generated images only (history isolation)
        num_new_images = len(current_candidates) - initial_count
        if num_new_images <= 0:
            num_new_images = 1 # Fallback to at least the last image
            
        latest_candidates = current_candidates[-num_new_images:]
        print(f"Selecting from the {len(latest_candidates)} latest generated images (out of {len(current_candidates)} total candidates).")
        selected_img = random.choice(latest_candidates)
        
        # Hover over the selected image to show the download button
        print("Hovering over selected image to reveal download button...")
        selected_img.hover()
        time.sleep(1)
        
        # Also hover over parent element to ensure hover is registered
        try:
            selected_img.locator("xpath=..").hover()
            time.sleep(1)
        except Exception:
            pass
        
        # Search for download button in the image's ancestors (up to 5 levels)
        download_btn = None
        container = selected_img
        for level in range(1, 6):
            try:
                container = container.locator("xpath=..")
                buttons = container.locator("button, div[role='button'], a[role='button']").all()
                for btn in buttons:
                    try:
                        html = btn.evaluate("el => el.outerHTML").lower()
                        aria_label = btn.get_attribute("aria-label") or ""
                        title = btn.get_attribute("title") or ""
                        if any(x in html or x in aria_label.lower() or x in title.lower() for x in ["download", "save"]):
                            download_btn = btn
                            print(f"Found download button inside ancestor at level {level}")
                            break
                    except Exception:
                        pass
                if download_btn:
                    break
            except Exception:
                break
                
        if not download_btn:
            print("Error: Could not locate the download button inside image card.")
            try:
                page.screenshot(path=os.path.join(os.path.dirname(output_path), "meta_ai_download_button_missing.png"))
            except Exception:
                pass
            page.close()
            return False
            
        # Download the file
        print("Clicking download button and saving...")
        try:
            with page.expect_download(timeout=20000) as download_info:
                # Trigger a direct DOM click to prevent layout shifting/zooming
                download_btn.evaluate("el => el.click()")
            download = download_info.value
            download.save_as(output_path)
            print(f"SUCCESS: Image saved to {output_path}")
            page.close()
            return True
        except Exception as de:
            print(f"JS click download failed: {de}. Retrying with Playwright click...")
            try:
                download_btn.scroll_into_view_if_needed()
                time.sleep(1)
                with page.expect_download(timeout=15000) as download_info:
                    download_btn.click()
                download = download_info.value
                download.save_as(output_path)
                print(f"SUCCESS: Image saved to {output_path}")
                page.close()
                return True
            except Exception as de2:
                print(f"Playwright click download failed: {de2}. Retrying with force click...")
                try:
                    with page.expect_download(timeout=10000) as download_info:
                        download_btn.click(force=True)
                    download = download_info.value
                    download.save_as(output_path)
                    print(f"SUCCESS (force click): Image saved to {output_path}")
                    page.close()
                    return True
                except Exception as de3:
                    print(f"Force click download failed: {de3}")
                
        page.close()
        return False
    except Exception as e:
        print(f"Exception in download_meta_ai_image: {e}")
        return False

# ==================== STEP 4: GHOST CMS INTEGRATION ====================

def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def create_jwt(api_key: str, version: str = "v2") -> str:
    key_id, secret_hex = api_key.split(':')
    header = {"alg": "HS256", "typ": "JWT", "kid": key_id}
    audience = f"/{version}/admin/" if version.lower() in ["v2", "v3"] else "/admin/"
    now = int(time.time())
    payload = {"iat": now, "exp": now + 300, "aud": audience}
    
    header_json = json.dumps(header, separators=(',', ':')).encode('utf-8')
    payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    unsigned = base64url_encode(header_json) + "." + base64url_encode(payload_json)
    secret_bytes = bytes.fromhex(secret_hex)
    signature = hmac.new(secret_bytes, unsigned.encode('utf-8'), hashlib.sha256).digest()
    return unsigned + "." + base64url_encode(signature)

def upload_image_to_ghost(api_url, api_key, version, file_path):
    """Local image file ko Ghost CMS image upload API ke zariye upload karta hai."""
    import requests
    
    api_url = api_url.rstrip('/')
    try:
        jwt_token = create_jwt(api_key, version=version)
    except Exception as e:
        print(f"JWT generation error for image upload: {e}")
        return None
        
    url = f"{api_url}/ghost/api/{version}/admin/images/upload/" if version.lower() in ["v2", "v3"] else f"{api_url}/ghost/api/admin/images/upload/"
    headers = {"Authorization": f"Ghost {jwt_token}"}
    
    filename = os.path.basename(file_path)
    mime_type = "image/jpeg" if filename.lower().endswith((".jpg", ".jpeg")) else "image/png"
    
    print(f"Uploading image to Ghost CMS ({filename})...")
    try:
        with open(file_path, "rb") as img_file:
            files = {"file": (filename, img_file, mime_type)}
            response = requests.post(url, files=files, headers=headers)
            
        if response.status_code in [200, 201]:
            resp_data = response.json()
            uploaded_url = resp_data.get("images", [{}])[0].get("url")
            print(f"Ghost CMS image upload SUCCESS: {uploaded_url}")
            return uploaded_url
        else:
            print(f"Ghost CMS image upload FAILED (HTTP {response.status_code}): {response.text}")
    except Exception as e:
        print(f"Ghost CMS image upload Exception: {e}")
    return None

def publish_to_ghost_cms(api_url, api_key, version, post_data, status="draft"):
    """Optimized article content ko Ghost CMS Admin API me create karta hai."""
    import requests
    
    api_url = api_url.rstrip('/')
    try:
        jwt_token = create_jwt(api_key, version=version)
    except Exception as e:
        print(f"JWT generation error for post publish: {e}")
        return False, str(e)
        
    url = f"{api_url}/ghost/api/{version}/admin/posts/?source=html" if version.lower() in ["v2", "v3"] else f"{api_url}/ghost/api/admin/posts/?source=html"
    headers = {
        "Authorization": f"Ghost {jwt_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "posts": [
            {
                "title": post_data["title"],
                "slug": post_data["slug"],
                "html": post_data["html"],
                "custom_excerpt": post_data["excerpt"],
                "meta_title": post_data["meta_title"],
                "meta_description": post_data["meta_description"],
                "feature_image": post_data.get("image"),
                "status": status
            }
        ]
    }
    
    print(f"Publishing blog post to Ghost CMS Admin API: '{post_data['title']}'...")
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code in [200, 201]:
            resp_json = response.json()
            post_id = resp_json.get("posts", [{}])[0].get("id", "Unknown")
            print(f"SUCCESS! Published to Ghost CMS. Post ID: {post_id}")
            return True, resp_json
        else:
            err_msg = f"HTTP {response.status_code}: {response.text}"
            print(f"ERROR: Ghost CMS rejected post creation: {err_msg}")
            return False, err_msg
    except Exception as e:
        err_msg = str(e)
        print(f"ERROR: Ghost CMS publishing exception: {err_msg}")
        return False, err_msg

# ==================== MAIN AUTOMATION FLOW ====================

def load_saved_chatgpt_url():
    """Reads saved ChatGPT chat URL from config file or environment."""
    env_url = os.environ.get("CHATGPT_CHAT_URL", "").strip()
    if env_url and "chatgpt.com/c/" in env_url:
        return env_url
    if os.path.exists(CHATGPT_CONFIG_FILE):
        try:
            with open(CHATGPT_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                url = data.get("chat_url", "").strip()
                if url and "chatgpt.com/c/" in url:
                    return url
        except Exception as e:
            print(f"[ChatGPT Config] Error reading config file: {e}")
    return None

def save_chatgpt_url(url):
    """Saves the current active ChatGPT conversation URL for future runs."""
    try:
        match = re.search(r"(https://chatgpt\.com/c/[a-zA-Z0-9\-]+)", url)
        if match:
            clean_url = match.group(1)
            current_saved = load_saved_chatgpt_url()
            if current_saved != clean_url:
                data = {
                    "chat_url": clean_url,
                    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                with open(CHATGPT_CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                print(f"[ChatGPT Config] Successfully saved persistent chat link for future runs: {clean_url}")
    except Exception as e:
        print(f"[ChatGPT Config] Error saving chat URL: {e}")

def is_chatgpt_error(page):
    """Detects if ChatGPT shows an 'Unable to load conversation' or error state."""
    try:
        error_indicators = [
            "unable to load conversation",
            "unable to find conversation",
            "unable to open chat",
            "conversation not found",
            "chat not found",
            "could not load conversation"
        ]
        body_text = page.locator("body").inner_text(timeout=3000).lower()
        for err in error_indicators:
            if err in body_text:
                return True
        # Check if text box exists and is visible
        for sel in CHATGPT_INPUT_SELECTORS:
            if page.locator(sel).first.is_visible():
                return False
        return True
    except Exception:
        pass
    return False

CHATGPT_INPUT_SELECTORS = [
    "#prompt-textarea",
    "div#prompt-textarea",
    "div[contenteditable='true']#prompt-textarea",
    "div.ProseMirror[contenteditable='true']",
    "[contenteditable='true'][data-id='root']",
    "textarea[id='prompt-textarea']",
    "textarea[data-id='root']",
    "div[contenteditable='true']",
    "textarea",
]

def _get_chatgpt_textbox(page, timeout=30000):
    for sel in CHATGPT_INPUT_SELECTORS:
        try:
            loc = page.locator(sel).first
            if loc.is_visible():
                return loc
        except Exception:
            pass
    combined = ", ".join(CHATGPT_INPUT_SELECTORS)
    textbox = page.locator(combined).first
    try:
        textbox.wait_for(state="visible", timeout=timeout)
    except Exception as e:
        print(f"Warning: Input box wait timed out: {e}")
    return textbox

def navigate_to_chatgpt(page):
    """
    Navigates to the saved ChatGPT chat URL. If the saved chat is invalid,
    deleted, or shows 'Unable to open chat', automatically starts a new chat,
    and prepares to save the new chat URL once created.
    """
    saved_url = load_saved_chatgpt_url()
    
    if saved_url:
        print(f"\n[ChatGPT] Opening saved persistent chat link: {saved_url}")
        try:
            page.goto(saved_url, timeout=45000)
            time.sleep(4)
            if is_chatgpt_error(page):
                print("[ChatGPT] Saved chat is inaccessible or deleted ('Unable to open conversation').")
                print("[ChatGPT] Starting a fresh new chat at https://chatgpt.com/ ...")
                page.goto("https://chatgpt.com/", timeout=45000)
                time.sleep(4)
            else:
                print(f"[ChatGPT] Successfully connected to persistent chat: {saved_url}")
        except Exception as e:
            print(f"[ChatGPT] Error loading saved chat ({e}). Starting a new chat at https://chatgpt.com/ ...")
            page.goto("https://chatgpt.com/", timeout=45000)
            time.sleep(4)
    else:
        print("\n[ChatGPT] No saved chat URL found. Starting a fresh new chat at https://chatgpt.com/ ...")
        page.goto("https://chatgpt.com/", timeout=45000)
        time.sleep(4)

    # Wait for the prompt input box to be visible
    textbox = _get_chatgpt_textbox(page, timeout=30000)
    time.sleep(2)
    return textbox

def enter_text_into_chatgpt(page, textbox, prompt_text):
    """
    Inputs text into ChatGPT's contenteditable ProseMirror / textarea reliably
    so that React / ProseMirror internal doc state updates and the send button is enabled.
    """
    try:
        textbox.click(timeout=5000)
    except Exception:
        try:
            page.keyboard.press("Escape")
            time.sleep(0.3)
            textbox.click(timeout=3000)
        except Exception:
            pass

    time.sleep(0.3)
    # Clear any previous draft/junk
    try:
        page.keyboard.press("ControlOrMeta+A")
        time.sleep(0.1)
        page.keyboard.press("Backspace")
        time.sleep(0.2)
    except Exception:
        pass

    # 1. Primary Method: page.keyboard.insert_text (native CDP Input.insertText)
    try:
        page.keyboard.insert_text(prompt_text)
        time.sleep(0.5)
    except Exception as e:
        print(f"keyboard.insert_text notice: {e}")

    if is_chatgpt_send_button_enabled(page):
        return True

    # 2. Fallback Method: native clipboard paste event
    try:
        escaped_prompt = json.dumps(prompt_text)
        page.evaluate(f"""() => {{
            const el = document.querySelector('#prompt-textarea') || document.querySelector('div[contenteditable="true"]') || document.querySelector('textarea');
            if (el) {{
                el.focus();
                document.execCommand('selectAll', false, null);
                const dt = new DataTransfer();
                dt.setData('text/plain', {escaped_prompt});
                const pasteEvt = new ClipboardEvent('paste', {{
                    clipboardData: dt,
                    bubbles: true,
                    cancelable: true
                }});
                el.dispatchEvent(pasteEvt);
            }}
        }}""")
        time.sleep(0.5)
    except Exception as e:
        print(f"Paste fallback notice: {e}")

    if is_chatgpt_send_button_enabled(page):
        return True

    # 3. Fallback Method: textbox.fill followed by space/backspace
    try:
        textbox.fill(prompt_text)
        time.sleep(0.2)
        textbox.press(" ")
        time.sleep(0.1)
        textbox.press("Backspace")
        time.sleep(0.5)
    except Exception:
        pass

    return is_chatgpt_send_button_enabled(page)

def submit_prompt_to_chatgpt(page, prompt_text):
    """Types a prompt into ChatGPT and submits it using button click or Enter fallback."""
    print("Waiting for ChatGPT input box to be ready...")
    textbox = _get_chatgpt_textbox(page, timeout=30000)
        
    print("Typing prompt into ChatGPT...")
    enter_text_into_chatgpt(page, textbox, prompt_text)
    time.sleep(0.5)

    clicked = False
    btn = get_chatgpt_send_button(page)
    if btn and btn.is_visible() and btn.is_enabled():
        print("Clicking active Send button...")
        try:
            btn.click(timeout=5000)
            clicked = True
        except Exception as e:
            print(f"Send button click failed: {e}")

    if not clicked:
        print("Attempting fallback: Enter to submit...")
        try:
            page.keyboard.press("Enter")
            clicked = True
        except Exception:
            try:
                textbox.press("Enter")
                clicked = True
            except Exception:
                pass
        
    time.sleep(2)

def submit_and_wait_for_response(page, prompt_text, max_wait_seconds=180, max_retries=2):
    """
    Submits a prompt to ChatGPT and waits for the response.
    If the response fails, times out, or returns empty, reloads with domcontentloaded and retries.
    Automatically captures and persists the active conversation URL.
    """
    active_url = page.url
    for attempt in range(max_retries + 1):
        if attempt > 0:
            print(f"\n--- Retrying Prompt Submission (Attempt {attempt + 1}/{max_retries + 1}) ---")
            print("Reloading the page...")
            try:
                page.reload(wait_until="domcontentloaded", timeout=45000)
                time.sleep(5)
            except Exception as re:
                print(f"Page reload notice: {re}. Navigating back to active thread URL...")
                try:
                    page.goto(active_url, wait_until="domcontentloaded", timeout=45000)
                    time.sleep(5)
                except Exception:
                    pass

        # Capture message state before submitting
        msgs = get_assistant_messages(page)
        initial_count = msgs.count()
        initial_last_text = ""
        if initial_count > 0:
            try:
                initial_last_text = extract_assistant_text(msgs.last)
            except Exception:
                pass

        # Submit the prompt
        try:
            submit_prompt_to_chatgpt(page, prompt_text)
        except Exception as se:
            print(f"Submission failed: {se}. Retrying...")
            continue

        # Check if URL updated to a new conversation
        try:
            time.sleep(2)
            if "chatgpt.com/c/" in page.url:
                save_chatgpt_url(page.url)
        except Exception:
            pass

        # Wait for the response
        response_text = wait_for_chatgpt_response(
            page, 
            initial_count=initial_count, 
            initial_last_text=initial_last_text, 
            max_wait_seconds=max_wait_seconds
        )

        # If response is valid, return it!
        if response_text and len(response_text.strip()) > 5:
            try:
                active_url = page.url
                if "chatgpt.com/c/" in active_url:
                    save_chatgpt_url(active_url)
            except Exception:
                pass
            return response_text.strip()

        print("Warning: Received empty or invalid response. Reloading and retrying...")

    return ""

def run_blog_generator_playwright():
    # Ensure Chrome Debugger is running
    launched = launch_chrome_if_needed()
    if not launched:
        print("Error: Could not launch Chrome on port 9222.")
        return None
        
    with sync_playwright() as p:
        try:
            # Connect over CDP
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            # Add stealth script to context to hide Playwright/automation indicators
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Acquire main Gemini/ChatGPT page: reuse existing tab (e.g. the initial about:blank) or create one
            if context.pages:
                gemini_page = context.pages[0]
            else:
                gemini_page = context.new_page()
            
            # Close any other lingering extension or extra tabs from previous session, NEVER closing gemini_page
            for p_tab in list(context.pages):
                if p_tab != gemini_page:
                    tab_url = p_tab.url.lower()
                    if (tab_url.startswith("chrome-extension://") or 
                        tab_url.startswith("chrome://") or 
                        "extension" in tab_url or
                        tab_url == "about:blank"):
                        try:
                            p_tab.close()
                        except Exception:
                            pass

            # Auto-close any unwanted extension tabs that might try to open in the background
            def close_extension_tab(page_obj):
                try:
                    time.sleep(0.5)
                    p_url = page_obj.url.lower()
                    if (p_url.startswith("chrome-extension://") or "chrome-extension" in p_url) and page_obj != gemini_page:
                        print(f"[Chrome] Auto-closed unwanted extension tab: {page_obj.url}")
                        page_obj.close()
                except Exception:
                    pass
            context.on("page", close_extension_tab)

            
            # --- Parse existing blog posts to enforce topic split ---
            posts = parse_blog_posts()
            source = determine_next_topic_source(posts)
            print(f"\n[Topic Selection] Selected source for this run: '{source.upper()}'")
            
            selected_topic = ""
            suggestions = []
            angle = ""
            
            if source == "trend":
                # --- 1. Scrape Trends ---
                # We use a temporary page for trends scraping so gemini_page doesn't navigate away
                print("\n--- STEP 1: Scraping Google Trends ---")
                temp_page = context.new_page()
                top_trends = get_trends_from_page_and_rss(temp_page)
                temp_page.close()
                
                if not top_trends:
                    print("No trending topics found. Aborting.")
                    gemini_page.close()
                    return None
                    
                print(f"Top trends to filter: {top_trends}")
                
                # --- 2. Navigate to ChatGPT to filter trend ---
                print("\n--- STEP 2: Connecting to ChatGPT for topic filtering ---")
                textbox = navigate_to_chatgpt(gemini_page)
                
                remaining_trends = list(top_trends)
                selected_topic = ""
                
                while remaining_trends:
                    filter_prompt = (
                        f"Out of these trending topics: {json.dumps(remaining_trends)}. "
                        "Which one is the easiest and most interesting to write a trivia/quiz blog post about? "
                        "Choose exactly one. Respond with ONLY the chosen topic name, and absolutely nothing else. "
                        "Do NOT select any topic about: active politicians or government officials, "
                        "ongoing legal proceedings or court cases involving named individuals, anyone's illness, death, "
                        "tragedy, or personal hardship, or any other topic that could be seen as insensitive, exploitative, "
                        "or politically divisive for a lighthearted trivia/quiz brand."
                    )
                    
                    candidate = submit_and_wait_for_response(gemini_page, filter_prompt, max_wait_seconds=120)
                    candidate = candidate.strip('"\'`').replace('\n', '').strip()
                    print(f"ChatGPT candidate topic: '{candidate}'")
                    
                    if not candidate or len(candidate) > 80:
                        print("Invalid topic selected by ChatGPT.")
                        if remaining_trends:
                            val = remaining_trends.pop(0)
                            if is_safe_topic(val):
                                selected_topic = val
                                break
                        continue
                        
                    # Check safety filter
                    if is_safe_topic(candidate):
                        selected_topic = candidate
                        print(f"Selected topic '{selected_topic}' passed safety checks.")
                        break
                    else:
                        print(f"Safety Violation: Candidate topic '{candidate}' contains blacklisted keywords. Rejecting and re-picking...")
                        # Remove from pool and retry
                        if candidate in remaining_trends:
                            remaining_trends.remove(candidate)
                        else:
                            # Re-filter pool to remove any matching keywords
                            remaining_trends = [t for t in remaining_trends if is_safe_topic(t)]
                            if not remaining_trends:
                                break
                                
                if not selected_topic:
                    print("No safe trending topics found. Falling back to a default lighthearted topic.")
                    selected_topic = "General Knowledge Trivia"
                    
                # --- 3. Google Search Autocomplete Suggestions ---
                # We use a temporary page for autocomplete so gemini_page doesn't navigate away
                print("\n--- STEP 3: Scraping Google Autocomplete ---")
                search_page = context.new_page()
                suggestions = get_autocomplete_suggestions(search_page, selected_topic)
                search_page.close()
                
                # Limit to top 15 diverse suggestions to prevent prompt clutter and Google SEO keyword stuffing penalties
                suggestions = suggestions[:15]
            else:
                # --- Product Source Topic Selection ---
                product_info = select_next_product_topic(posts)
                selected_topic = product_info["topic"]
                suggestions = product_info["keywords"]
                angle = product_info["angle"]
                print(f"[Topic Selection] Selected product seed topic: '{selected_topic}'")
                print(f"[Topic Selection] Keywords: {suggestions}")
                print(f"[Topic Selection] Angle: {angle}")
                
                # Navigate to ChatGPT for subsequent turns
                print("\n--- STEP 2: Connecting to ChatGPT for content generation ---")
                textbox = navigate_to_chatgpt(gemini_page)
                
            # --- 4. Get Image Prompts from ChatGPT (BEFORE content generation to save quota and verify first) ---
            print("\n--- STEP 4: Requesting Image Prompts from ChatGPT ---")
            prompt_image_prompts = (
                f"For the selected topic \"{selected_topic}\", write two photorealistic image prompts:\n"
                "1. A landscape (16:9) image prompt representing the topic. Make it highly detailed, descriptive, photorealistic, with professional camera settings, specific textures, and natural lighting. Do NOT include laptops, screens, or text.\n"
                "2. A matching vertical (9:16) version of that prompt. Avoid celebrity names.\n"
                "Respond ONLY with a JSON object in this format (no markdown blocks, no other text):\n"
                "{\n"
                "  \"landscape_image_prompt\": \"...\",\n"
                "  \"vertical_image_prompt\": \"...\"\n"
                "}"
            )
            
            raw_prompts_json = submit_and_wait_for_response(gemini_page, prompt_image_prompts, max_wait_seconds=90)
            cleaned_prompts_json = clean_markdown_response(raw_prompts_json)
            json_match_p = re.search(r"\{.*\}", cleaned_prompts_json, re.DOTALL)
            prompts_data = None
            if json_match_p:
                prompts_data = fallback_json_parser(json_match_p.group(0))
            else:
                prompts_data = fallback_json_parser(cleaned_prompts_json)
                
            if not prompts_data:
                print("Warning: Could not parse image prompts JSON. Using default backup prompts.")
                prompts_data = {
                    "landscape_image_prompt": f"A realistic, professional sports/conceptual close-up photograph representing the theme of {selected_topic}, natural lighting, sharp focus",
                    "vertical_image_prompt": f"A realistic, professional sports/conceptual close-up vertical photograph representing the theme of {selected_topic}, natural lighting, sharp focus"
                }
                
            image_prompt = prompts_data.get("landscape_image_prompt") or prompts_data.get("landscape_prompt") or prompts_data.get("image_prompt")
            pinterest_prompt = prompts_data.get("vertical_image_prompt") or prompts_data.get("vertical_prompt") or prompts_data.get("pinterest_prompt") or prompts_data.get("pinterest_image_prompt")
            
            if not image_prompt:
                image_prompt = create_safe_image_prompt(selected_topic, format_type="landscape")
            if not pinterest_prompt:
                pinterest_prompt = create_safe_image_prompt(selected_topic, format_type="vertical")
                
            # --- 5. Generate and Download Images from Meta AI ---
            # Generate landscape image
            print("\n--- STEP 5: Generating Landscape Image (16:9) ---")
            landscape_path = os.path.join(SCRIPT_DIR, "assets", "landscape_image.png")
            os.makedirs(os.path.dirname(landscape_path), exist_ok=True)
            
            success_landscape = download_meta_ai_image(
                context, image_prompt, landscape_path,
                "https://www.meta.ai/prompt/45be4302-feee-40d5-bafd-a3c1892005ef"
            )
            if not success_landscape:
                print("Failed to download landscape image from Meta AI. Aborting blog creation as images are mandatory.")
                gemini_page.close()
                browser.close()
                return None
                
            # Generate Pinterest vertical image
            print("\n--- STEP 6: Generating Pinterest Vertical Image (9:16) ---")
            pinterest_path = os.path.join(SCRIPT_DIR, "assets", "pinterest_image.png")
            
            success_pinterest = download_meta_ai_image(
                context, pinterest_prompt, pinterest_path,
                "https://www.meta.ai/prompt/f4278c21-9a38-4c35-9fd5-8b38ffc2df92"
            )
            if not success_pinterest:
                print("Failed to download Pinterest vertical image from Meta AI. Aborting blog creation as images are mandatory.")
                gemini_page.close()
                browser.close()
                return None
                
            # --- 7. Content Generation Prompt (Multi-Turn) ---
            print("\n--- STEP 7: Generating Blog Post Content via ChatGPT (Multi-Turn) ---")
            
            # TURN 1: Write Introduction Section
            print("\n--- TURN 1: Generating Introduction ---")
            if source == "trend":
                prompt_turn1 = (
                    f"We are writing a blog post about the trending topic: \"{selected_topic}\".\n"
                    f"Target Keyword: \"{selected_topic}\"\n"
                    f"Background research context (use these terms/topics naturally to guide the article, but do not list them out): {json.dumps(suggestions)}.\n\n"
                    f"Write a compelling, SEO-optimized Introduction section (minimum 400 words) starting with an <h1> tag containing the target keyword. "
                    f"Focus strictly on \"{selected_topic}\", why it is currently trending, its significance, background, and key facts. "
                    f"Also, weave in how content creators or YouTubers can leverage this specific trending interest to build highly engaging "
                    f"quiz and trivia videos, introducing QuizViral AI as the tool to instantly bulk-generate these videos from CSV imports.\n"
                    f"Do not list out search queries or keyword variations as a sentence (e.g. 'searches such as X, Y, Z'). Write naturally, as if for a human reader, not an SEO checklist.\n"
                    "Respond with ONLY raw HTML body content. Do not include <html>, <head>, or <body> wrappers, and do not wrap in markdown code blocks."
                )
            else:
                prompt_turn1 = (
                    f"We are writing a blog post about: \"{selected_topic}\".\n"
                    f"Target Keyword: \"{selected_topic}\"\n"
                    f"Background research context (use these terms/topics naturally to guide the article, but do not list them out): {json.dumps(suggestions)}.\n\n"
                    f"Write a compelling, SEO-optimized Introduction section (minimum 400 words) starting with an <h1> tag containing the target keyword. "
                    f"Focus on \"{selected_topic}\", outlining the core strategies, value, and ideas for creators wanting to grow their channels. "
                    f"Weave in how QuizViral AI enables creators to capitalize on this via automated bulk video generation from CSV imports.\n"
                    f"Do not list out search queries or keyword variations as a sentence (e.g. 'searches such as X, Y, Z'). Write naturally, as if for a human reader, not an SEO checklist.\n"
                    "Respond with ONLY raw HTML body content. Do not include <html>, <head>, or <body> wrappers, and do not wrap in markdown code blocks."
                )
            raw_intro = submit_and_wait_for_response(gemini_page, prompt_turn1, max_wait_seconds=150)
            if not raw_intro or len(raw_intro.strip()) < 100:
                print(f"[Error] Turn 1 (Introduction) failed or generated insufficient content (len: {len(raw_intro.strip()) if raw_intro else 0}). Aborting.")
                gemini_page.close()
                browser.close()
                return None
            print("Successfully read Turn 1 (Introduction) response.")
            
            # --- Intro Similarity Check Safeguard ---
            last_10_posts = posts[:10]
            for attempt in range(3):
                plain_new_intro = re.sub(r'<[^>]+>', ' ', raw_intro)
                plain_new_intro = " ".join(plain_new_intro.split())
                new_intro_opening = plain_new_intro[:100].strip()
                
                max_similarity = 0.0
                matched_slug = ""
                for p in last_10_posts:
                    old_intro_opening = extract_intro_opening(p.get("content", ""))
                    similarity = get_string_similarity(new_intro_opening, old_intro_opening)
                    if similarity > max_similarity:
                        max_similarity = similarity
                        matched_slug = p.get("slug", "")
                        
                print(f"Intro opening similarity check (Attempt {attempt+1}/3): max similarity = {max_similarity:.2%} (with '{matched_slug}')")
                if max_similarity <= 0.70:
                    break
                else:
                    print(f"Similarity exceeds 70%! Regenerating introduction...")
                    regen_prompt = (
                        f"The introduction you generated is too similar to our previous blog posts (similarity: {max_similarity:.2%}). "
                        f"Please rewrite the Introduction section for \"{selected_topic}\" from scratch. "
                        "It MUST read as legacy-free, fresh, and meaningfully different from prior posts in its wording, sentence structure, and flow. "
                        "Do not use repetitive patterns. Start with the <h1> tag as before, and respond with ONLY the raw HTML content."
                    )
                    raw_intro = submit_and_wait_for_response(gemini_page, regen_prompt, max_wait_seconds=150)
            
            # TURN 2: Write Tutorial & 10 Quiz Questions
            print("\n--- TURN 2: Generating Tutorial & 10 Quiz Questions ---")
            
            # Get titles and slugs of the last 3 posts to avoid repeating unique details
            recent_post_info = []
            for p in posts[:3]:
                r_title = p.get('title')
                r_slug = p.get('slug')
                if r_title:
                    recent_post_info.append(f"- Title: {r_title} (Slug: {r_slug})")
            recent_context_str = "\n".join(recent_post_info) if recent_post_info else "None"
            
            if source == "trend":
                prompt_turn2 = (
                    f"Excellent. Now write the second section (minimum 600 words):\n"
                    f"- Go deeper into details, history, analysis, or current events about \"{selected_topic}\" to provide maximum value to the reader.\n"
                    f"- Include 10 complete quiz questions about \"{selected_topic}\".\n"
                    f"- SPECIFICITY REQUIREMENT: You must include at least one specific, concrete, non-generic detail in this tutorial section (e.g., a real-world example scenario, a specific statistic/number, or a named recurring content format). To ensure uniqueness and prevent boilerplate, do NOT reuse details, formats, or angles from our recent posts:\n{recent_context_str}\n"
                    f"- FORMATTING RULES FOR QUIZ QUESTIONS: Each of the 10 quiz questions and its 4 options must be a single self-contained block (e.g., a <p> or <h3> containing the question text, followed by an <ul> containing exactly the 4 <li> options with letters A, B, C, D, with the correct answer stated in a separate paragraph or block directly after). You must NEVER use a top-level <ol> wrapping multiple questions together. Numbered list elements (<ol> or restarting list items) must never restart or continue across separate questions.\n"
                    f"- REQUIRED UNIQUE ANGLE: You must include at least one specific, non-generic detail, statistic, or creative angle that connects this specific trend (e.g., specific game details, player stats, or pop culture moments) to quiz-content creation (e.g., explaining how these details can build suspense in a YouTube Short or drive higher comments by debating a polarizing question).\n\n"
                    "Respond with ONLY raw HTML body content using <h2>, <h3>, <p>, <ul>, <li>, etc. Do not wrap in markdown code blocks."
                )
            else:
                prompt_turn2 = (
                    f"Excellent. Now write the second section (minimum 600 words):\n"
                    f"- Go deeper into details, strategies, and tips about \"{selected_topic}\" to provide maximum value to the reader.\n"
                    f"- Specific angle to cover: \"{angle}\"\n"
                    f"- Include 10 complete sample quiz questions or template ideas about \"{selected_topic}\".\n"
                    f"- SPECIFICITY REQUIREMENT: You must include at least one specific, concrete, non-generic detail in this tutorial section (e.g., a real-world example scenario, a specific statistic/number, or a named recurring content format). To ensure uniqueness and prevent boilerplate, do NOT reuse details, formats, or angles from our recent posts:\n{recent_context_str}\n"
                    f"- FORMATTING RULES FOR QUIZ QUESTIONS: Each of the 10 quiz questions and its 4 options must be a single self-contained block (e.g., a <p> or <h3> containing the question text, followed by an <ul> containing exactly the 4 <li> options with letters A, B, C, D, with the correct answer stated in a separate paragraph or block directly after). You must NEVER use a top-level <ol> wrapping multiple questions together. Numbered list elements (<ol> or restarting list items) must never restart or continue across separate questions.\n"
                    f"- REQUIRED UNIQUE ANGLE: You must include at least one specific, non-generic detail, statistic, or creative angle that connects this topic directly to quiz-content creation tips using QuizViral AI.\n\n"
                    "Respond with ONLY raw HTML body content using <h2>, <h3>, <p>, <ul>, <li>, etc. Do not wrap in markdown code blocks."
                )
            raw_tutorial = submit_and_wait_for_response(gemini_page, prompt_turn2, max_wait_seconds=180)
            if not raw_tutorial or len(raw_tutorial.strip()) < 100:
                print(f"[Error] Turn 2 (Tutorial) failed or generated insufficient content (len: {len(raw_tutorial.strip()) if raw_tutorial else 0}). Aborting.")
                gemini_page.close()
                browser.close()
                return None
            print("Successfully read Turn 2 (Tutorial & Quiz Questions) response.")
            
            # TURN 3: Write Monetization & FAQs
            print("\n--- TURN 3: Generating Monetization & FAQs ---")
            selected_template = random.choice(TEMPLATES)
            print(f"Selected Turn 3 monetization template: '{selected_template['name']}'")
            prompt_turn3 = (
                f"Excellent. Now write the final section (minimum 500 words):\n"
                f"{selected_template['prompt']}\n\n"
                f"IMPORTANT: Tailor this template to the context of \"{selected_topic}\" naturally so it feels custom-tailored rather than a generic boilerplate paragraph. "
                "Respond with ONLY raw HTML body content using <h2>, <h3>, <p>, <ul>, <li>, etc. Do not wrap in markdown code blocks."
            )
            raw_monetization = submit_and_wait_for_response(gemini_page, prompt_turn3, max_wait_seconds=150)
            if not raw_monetization or len(raw_monetization.strip()) < 100:
                print(f"[Error] Turn 3 (Monetization) failed or generated insufficient content (len: {len(raw_monetization.strip()) if raw_monetization else 0}). Aborting.")
                gemini_page.close()
                browser.close()
                return None
            print("Successfully read Turn 3 (Monetization & FAQs) response.")
            
            # --- Monetization Similarity Check Safeguard ---
            for attempt in range(3):
                plain_new_monetization = re.sub(r'<[^>]+>', ' ', raw_monetization)
                plain_new_monetization = " ".join(plain_new_monetization.split())
                
                max_similarity = 0.0
                matched_slug = ""
                for p in last_10_posts:
                    old_monetization = extract_monetization_text(p.get("content", ""))
                    plain_old_monetization = re.sub(r'<[^>]+>', ' ', old_monetization)
                    plain_old_monetization = " ".join(plain_old_monetization.split())
                    
                    similarity = get_string_similarity(plain_new_monetization[:500], plain_old_monetization[:500])
                    if similarity > max_similarity:
                        max_similarity = similarity
                        matched_slug = p.get("slug", "")
                        
                print(f"Monetization section similarity check (Attempt {attempt+1}/3): max similarity = {max_similarity:.2%} (with '{matched_slug}')")
                if max_similarity <= 0.70:
                    break
                else:
                    print(f"Similarity exceeds 70%! Regenerating monetization section...")
                    new_template = random.choice([t for t in TEMPLATES if t["name"] != selected_template["name"]])
                    selected_template = new_template
                    print(f"Selected alternate Turn 3 template: '{selected_template['name']}'")
                    regen_prompt = (
                        f"The monetization/FAQ section you generated is too similar to our previous blog posts (similarity: {max_similarity:.2%}). "
                        f"Please rewrite the monetization and FAQ section for \"{selected_topic}\" from scratch. "
                        "It MUST read as meaningfully different from prior posts. Use completely different phrasing, style, and sentence structure.\n"
                        f"Follow this specific template structure:\n{selected_template['prompt']}\n"
                        f"IMPORTANT: Tailor it to the context of \"{selected_topic}\" naturally.\n"
                        "Respond with ONLY raw HTML body content."
                    )
                    raw_monetization = submit_and_wait_for_response(gemini_page, regen_prompt, max_wait_seconds=150)
            
            # Combine the HTML components
            html_content = f"{raw_intro}\n{raw_tutorial}\n{raw_monetization}"
            html_content = clean_markdown_response(html_content)
            
            # TURN 4: SEO Metadata compilation (Simplified JSON format)
            print("\n--- TURN 4: Compiling SEO Metadata ---")
            prompt_turn4 = (
                "Awesome. Based on the complete article we just generated, compile the SEO metadata.\n"
                "Respond ONLY with a JSON object in this format. Do not wrap in markdown code blocks:\n"
                "{\n"
                "  \"title\": \"Compelling, high-CTR headline containing the target keyword (strictly 50-60 characters, curiosity-driven with numbers or hooks like [2026 Guide] or (With Answers) where appropriate. DO NOT mention QuizViral in the title)\",\n"
                "  \"slug\": \"url-friendly-slug-with-keyword (strictly about the topic itself, no quiz/video terms)\",\n"
                "  \"excerpt\": \"Compelling 2-sentence summary of the post (strictly about the topic itself)\",\n"
                "  \"meta_title\": \"SEO Meta Title (exactly 50-60 characters featuring the topic and high-intent keywords naturally at the end)\",\n"
                "  \"meta_description\": \"SEO Meta Description (exactly 145-150 characters featuring the topic and high-intent keywords naturally at the end)\",\n"
                "  \"markdown\": \"Complete blog post in markdown format (including title, headers, body, 10 quiz questions, and FAQs)\"\n"
                "}"
            )
            raw_metadata = submit_and_wait_for_response(gemini_page, prompt_turn4, max_wait_seconds=180)
            print("Successfully read Turn 4 (Metadata) response.")
            
            # Clean ChatGPT response
            cleaned_json = clean_markdown_response(raw_metadata)
            
            # Find and parse JSON
            blog_data = None
            json_match = re.search(r"\{.*\}", cleaned_json, re.DOTALL)
            if json_match:
                try:
                    blog_data = json.loads(json_match.group(0))
                except Exception:
                    # Fallback JSON regex parser
                    blog_data = fallback_json_parser(json_match.group(0))
            else:
                try:
                    blog_data = json.loads(cleaned_json)
                except Exception:
                    blog_data = fallback_json_parser(cleaned_json)
                
            if not blog_data:
                print("Error: Could not parse metadata JSON from ChatGPT. Trying custom build...")
                blog_data = {
                    "title": f"The Ultimate Guide to {selected_topic}",
                    "slug": selected_topic.lower().replace(" ", "-"),
                    "excerpt": f"Discover how to create viral quiz videos about {selected_topic} automatically.",
                    "meta_title": f"How to Make Quiz Videos about {selected_topic} Instantly",
                    "meta_description": f"Learn how to create automated faceless quiz videos about {selected_topic} to grow your channel.",
                    "markdown": f"# The Ultimate Guide to {selected_topic}\n\n" + html_content.replace("<p>", "").replace("</p>", "\n\n").replace("<h2>", "## ").replace("</h2>", "\n\n")
                }
            
            # Attach combined HTML and downloaded image paths
            blog_data["html"] = html_content
            blog_data["local_image"] = landscape_path
            blog_data["local_pinterest_image"] = pinterest_path
            
            # Close browser
            gemini_page.close()
            browser.close()
            
            blog_data["trendingKeyword"] = selected_topic
            blog_data["topic_source"] = source
            return blog_data
            
        except Exception as e:
            print(f"Exception during Playwright execution: {e}")
            import traceback
            traceback.print_exc()
            

def get_latest_fb_video():
    print("Scraping Facebook page for latest video/reel...")
    fb_videos_url = "https://www.facebook.com/profile.php?id=61585764748589&sk=videos"
    latest_video_url = "https://www.facebook.com/watch/?v=892872416450589"
    
    if check_port_open(9222):
        try:
            with sync_playwright() as p:
                browser = p.chromium.connect_over_cdp("http://localhost:9222")
                context = browser.contexts[0]
                context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                page = context.new_page()
                
                print(f"Navigating to Facebook Videos page: {fb_videos_url}")
                page.goto(fb_videos_url, timeout=45000)
                time.sleep(5)
                page.evaluate("window.scrollBy(0, 800);")
                time.sleep(3)
                
                # Scrape all <a> links for video/reel paths
                anchors = page.locator("a").all()
                found_urls = []
                for a in anchors:
                    try:
                        href = a.get_attribute("href") or ""
                        # Exclude navigation tab links like /reel/?s=tab
                        if any(k in href for k in ["/reel/", "/videos/", "/watch/"]) and not href.endswith("?s=tab"):
                            if href.startswith("/"):
                                href = f"https://www.facebook.com{href}"
                            if href not in found_urls:
                                found_urls.append(href)
                    except Exception:
                        pass
                
                if found_urls:
                    latest_video_url = found_urls[0]
                    print(f"Successfully scraped latest Facebook video/reel: '{latest_video_url}'")
                else:
                    # Try regex fallback on HTML
                    html_content = page.content()
                    video_matches = re.findall(r'(?:facebook\.com\/watch\/\?v=|facebook\.com\/.*?\/videos\/|\/reel\/|v=)(\d{10,18})', html_content)
                    if video_matches:
                        latest_video_url = f"https://www.facebook.com/watch/?v={video_matches[0]}"
                        print(f"Scraped latest Facebook video via regex: '{latest_video_url}'")
                
                page.close()
                # DO NOT call browser.close() so Chrome port 9222 stays open for subsequent steps!
        except Exception as e:
            print(f"Facebook video scrape exception: {e}")
            
    dest_path = os.path.join(SCRIPT_DIR, "frontend", "src", "data", "latestFbVideo.js")
    try:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(f'export const latestFbVideoUrl = "{latest_video_url}";\n')
        print(f"Saved latest Facebook video URL to {dest_path}")
    except Exception as e:
        print(f"Failed to update latestFbVideo.js: {e}")

def update_blog_posts_file(new_post):
    print(f"Adding new blog post to {BLOG_POSTS_FILE}...")
    if not os.path.exists(BLOG_POSTS_FILE):
        return False
    with open(BLOG_POSTS_FILE, "r", encoding="utf-8") as f:
        file_content = f.read()
    
    match = re.search(r"export const blogPosts = \[(.*)\];\s*$", file_content, re.DOTALL)
    if not match:
        return False
        
    posts_array_content = match.group(1).strip()
    
    # We store the markdown block inside "content" field
    post_item = {
        "title": new_post["title"],
        "slug": new_post["slug"],
        "excerpt": new_post["excerpt"],
        "date": new_post["date"],
        "readTime": new_post["readTime"],
        "author": new_post["author"],
        "image": new_post["image"],
        "pinterest_image": new_post.get("pinterest_image", ""),
        "metaDescription": new_post["meta_description"],
        "seoKeywords": [new_post["trendingKeyword"], "QuizViral AI"],
        "content": new_post["markdown"],
        "trendingKeyword": new_post["trendingKeyword"],
        "topicSource": new_post.get("topic_source", "trend")
    }
    
    new_post_str = json.dumps(post_item, indent=2)
    # Re-align JSON properties names for compatibility with JS parser
    for prop in ["title", "slug", "excerpt", "date", "readTime", "author", "image", "pinterest_image", "metaDescription", "seoKeywords", "content", "trendingKeyword", "topicSource"]:
        new_post_str = new_post_str.replace(f'"{prop}":', f'{prop}:')

    # Check if slug already exists in blogPosts.js to prevent any duplicate slugs!
    existing_slugs = re.findall(r"slug:\s*['\"`]([^'\"`]+)['\"`]", file_content)
    if new_post["slug"] in existing_slugs:
        curr_year = datetime.now().year
        suffix = 2
        candidate_slug = f"{new_post['slug']}-{curr_year}"
        while candidate_slug in existing_slugs:
            candidate_slug = f"{new_post['slug']}-{curr_year}-v{suffix}"
            suffix += 1
        print(f"[Duplicate Guard] Slug '{new_post['slug']}' already exists! Made unique: '{candidate_slug}'")
        new_post["slug"] = candidate_slug
        post_item["slug"] = candidate_slug
        # Re-serialize with unique slug
        new_post_str = json.dumps(post_item, indent=2)
        for prop in ["title", "slug", "excerpt", "date", "readTime", "author", "image", "pinterest_image", "metaDescription", "seoKeywords", "content", "trendingKeyword", "topicSource"]:
            new_post_str = new_post_str.replace(f'"{prop}":', f'{prop}:')

    if posts_array_content:
        updated_array = new_post_str + ",\n  " + posts_array_content
    else:
        updated_array = new_post_str
        
    updated_file_content = f"export const blogPosts = [\n  {updated_array}\n];\n"
    
    with open(BLOG_POSTS_FILE, "w", encoding="utf-8") as f:
        f.write(updated_file_content)
    print("blogPosts.js updated successfully!")
    return True

def generate_sitemap_from_posts():
    sitemap_path = os.path.join(SCRIPT_DIR, "frontend", "public", "sitemap.xml")
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # Helper to parse different date formats to YYYY-MM-DD
    def parse_w3c_date(date_str):
        if not date_str:
            return today_str
        try:
            # e.g., "July 11, 2026"
            dt = datetime.strptime(date_str.strip(), "%B %d, %Y")
            return dt.strftime("%Y-%m-%d")
        except Exception:
            try:
                # e.g., "June 19, 2026"
                dt = datetime.strptime(date_str.strip(), "%b %d, %Y")
                return dt.strftime("%Y-%m-%d")
            except Exception:
                try:
                    # Already in YYYY-MM-DD
                    dt = datetime.strptime(date_str.strip(), "%Y-%m-%d")
                    return dt.strftime("%Y-%m-%d")
                except Exception:
                    return today_str

    posts = parse_blog_posts()
    
    # Determine the latest blog post date to use as lastmod for / and /blog
    latest_post_date = today_str
    post_dates = []
    for p in posts:
        d_val = p.get("date")
        if d_val:
            post_dates.append(parse_w3c_date(d_val))
            
    if post_dates:
        latest_post_date = max(post_dates)
        
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        '  <url>',
        '    <loc>https://quizviral-nine.vercel.app/</loc>',
        f'    <lastmod>{latest_post_date}</lastmod>',
        '    <changefreq>daily</changefreq>',
        '    <priority>1.0</priority>',
        '  </url>',
        '  <url>',
        '    <loc>https://quizviral-nine.vercel.app/pricing</loc>',
        f'    <lastmod>{today_str}</lastmod>',
        '    <changefreq>weekly</changefreq>',
        '    <priority>0.8</priority>',
        '  </url>',
        '  <url>',
        '    <loc>https://quizviral-nine.vercel.app/blog</loc>',
        f'    <lastmod>{latest_post_date}</lastmod>',
        '    <changefreq>daily</changefreq>',
        '    <priority>0.9</priority>',
        '  </url>'
    ]
    
    # 15 Niche Tool Landing Pages
    tool_niches = [
        "gaming", "history", "movies", "science", "geography", "sports",
        "kids", "anime", "food", "music", "general-knowledge", "bollywood",
        "cricket", "technology", "animals"
    ]
    for niche_slug in tool_niches:
        xml_lines.extend([
            '  <url>',
            f'    <loc>https://quizviral-nine.vercel.app/tools/{niche_slug}</loc>',
            f'    <lastmod>{today_str}</lastmod>',
            '    <changefreq>weekly</changefreq>',
            '    <priority>0.8</priority>',
            '  </url>'
        ])
    
    # Blog Posts
    for p in posts:
        slug = p.get("slug")
        if not slug:
            continue
        p_date = parse_w3c_date(p.get("date"))
        xml_lines.extend([
            '  <url>',
            f'    <loc>https://quizviral-nine.vercel.app/blog/{slug}</loc>',
            f'    <lastmod>{p_date}</lastmod>',
            '    <changefreq>monthly</changefreq>',
            '    <priority>0.7</priority>',
            '  </url>'
        ])
        
    xml_lines.append('</urlset>')
    
    url_count = 3 + len(tool_niches) + len([p for p in posts if p.get("slug")])
    
    try:
        os.makedirs(os.path.dirname(sitemap_path), exist_ok=True)
        with open(sitemap_path, "w", encoding="utf-8") as f:
            f.write("\n".join(xml_lines) + "\n")
        print(f"Sitemap successfully generated at {sitemap_path} with {url_count} URLs.")
        return url_count
    except Exception as e:
        print(f"Error generating sitemap.xml: {e}")
        return 0

def ping_indexnow(slug):
    url_to_index = f"https://quizviral-nine.vercel.app/blog/{slug}"
    key = "86b7a1114fbd4f80a501b0dbc2731be3"
    key_location = f"https://quizviral-nine.vercel.app/{key}.txt"
    ping_url = f"https://api.indexnow.org/indexnow?url={url_to_index}&key={key}&keyLocation={key_location}"
    try:
        import ssl
        context = ssl._create_unverified_context()
        req = urllib.request.Request(ping_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10, context=context) as response:
            if response.getcode() == 200:
                print("IndexNow ping successful.")
    except Exception:
        pass
def git_push_changes(title):
    print("Staging and pushing changes to GitHub...")
    try:
        # Get active branch name
        branch_res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=SCRIPT_DIR, capture_output=True, text=True, check=True)
        active_branch = branch_res.stdout.strip()
        print(f"Detected active git branch: '{active_branch}'")
        
        # Stage and commit on current active branch
        subprocess.run(["git", "add", "."], cwd=SCRIPT_DIR, check=True)
        # Check if there are changes to commit
        status_res = subprocess.run(["git", "status", "--porcelain"], cwd=SCRIPT_DIR, capture_output=True, text=True, check=True)
        if status_res.stdout.strip():
            subprocess.run(["git", "commit", "-m", f"chore(blog): auto-publish post '{title}'"], cwd=SCRIPT_DIR, check=True)
        else:
            print("No changes to commit.")
            
        print("Pulling latest remote changes from GitHub...")
        try:
            subprocess.run(["git", "pull", "--rebase", "github", "main"], cwd=SCRIPT_DIR, check=True)
        except Exception as pull_err:
            print(f"Warning: git pull --rebase failed: {pull_err}")

        print("Pushing to GitHub...")
        subprocess.run(["git", "push", "github", f"{active_branch}:main"], cwd=SCRIPT_DIR, check=True)
        
        # Deploy to Hugging Face Space by creating a temporary branch without blog assets
        try:
            temp_branch = "hf-deploy-temp" if active_branch != "hf-deploy-temp" else "hf-deploy-temp-alt"
            print(f"Preparing temporary branch '{temp_branch}' for Hugging Face deployment via a git worktree...")

            import shutil
            worktree_path = os.path.join(SCRIPT_DIR, ".hf-deploy-worktree")
            # Clean any previous worktree dir/branches first
            try:
                subprocess.run(["git", "worktree", "remove", worktree_path, "--force"], cwd=SCRIPT_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
            try:
                subprocess.run(["git", "worktree", "prune"], cwd=SCRIPT_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
            try:
                subprocess.run(["git", "branch", "-D", temp_branch], cwd=SCRIPT_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
            if os.path.exists(worktree_path):
                try:
                    shutil.rmtree(worktree_path)
                except Exception:
                    pass

            # Create a separate worktree so we don't modify the main working tree and avoid checkout conflicts
            subprocess.run(["git", "worktree", "add", "--detach", worktree_path], cwd=SCRIPT_DIR, check=True)

            # In the worktree, create the orphan temp branch and clean it
            subprocess.run(["git", "checkout", "--orphan", temp_branch], cwd=worktree_path, check=True)
            subprocess.run(["git", "rm", "-rf", "."], cwd=worktree_path, check=True)

            # Checkout files from active branch
            subprocess.run(["git", "checkout", active_branch, "--", "."], cwd=worktree_path, check=True)

            # Exclude blog assets from index
            print("Excluding blog images from Hugging Face deployment index...")
            subprocess.run(["git", "rm", "-r", "--cached", "frontend/public/assets/blog/"], cwd=worktree_path, check=False)
            
            # Delete them from disk in the worktree
            wt_blog_dir = os.path.join(worktree_path, "frontend", "public", "assets", "blog")
            if os.path.exists(wt_blog_dir):
                shutil.rmtree(wt_blog_dir)

            # Commit clean code
            subprocess.run(["git", "commit", "-m", "deploy: update clean code for Hugging Face"], cwd=worktree_path, check=True)

            # Push clean code to Hugging Face Space (origin) main branch
            print("Pushing to Hugging Face Space (origin)...")
            subprocess.run(["git", "push", "origin", f"{temp_branch}:main", "--force"], cwd=worktree_path, check=True)
            print("Hugging Face Space deployment completed successfully!")
            
        except Exception as he:
            print(f"\nWARNING: Hugging Face push failed: {he}. Continuing pipeline...")
        finally:
            # Clean up the temporary worktree and delete the temp branch reference locally
            try:
                subprocess.run(["git", "worktree", "remove", worktree_path, "--force"], cwd=SCRIPT_DIR, check=False)
            except Exception:
                pass
            try:
                subprocess.run(["git", "branch", "-D", temp_branch], cwd=SCRIPT_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
            
        print("Git Push Completed Successfully!")
    except Exception as e:
        print(f"\nCRITICAL ERROR: Git push pipeline failed: {e}")
        raise e

def cleanup_old_blog_data():
    print("Initiating old blog data cleanup to free up space...")
    try:
        # 1. Clean temporary files in local assets directory
        assets_dir = os.path.join(SCRIPT_DIR, "assets")
        if os.path.exists(assets_dir):
            for file_name in os.listdir(assets_dir):
                file_path = os.path.join(assets_dir, file_name)
                # Keep logo, but delete temp images and screenshots
                if os.path.isfile(file_path):
                    if any(x in file_name.lower() for x in ["landscape", "pinterest", "failed", "missing"]):
                        try:
                            os.remove(file_path)
                            print(f"Removed temporary file: {file_name}")
                        except Exception:
                            pass
                            
        # 2. Garbage collect orphaned images in frontend public directory
        public_blog_dir = os.path.join(SCRIPT_DIR, "frontend", "public", "assets", "blog")
        blog_posts_file = os.path.join(SCRIPT_DIR, "frontend", "src", "data", "blogPosts.js")
        
        if os.path.exists(public_blog_dir) and os.path.exists(blog_posts_file):
            # Read active blog posts configuration to check references
            try:
                with open(blog_posts_file, "r", encoding="utf-8") as f:
                    js_content = f.read()
            except Exception as re:
                print(f"Could not read blogPosts.js: {re}")
                return
                
            for file_name in os.listdir(public_blog_dir):
                file_path = os.path.join(public_blog_dir, file_name)
                if os.path.isfile(file_path):
                    # Check if the filename is referenced anywhere in the JS database
                    if file_name not in js_content:
                        try:
                            os.remove(file_path)
                            print(f"Garbage collected orphaned blog image: {file_name}")
                        except Exception as de:
                            print(f"Failed to delete {file_name}: {de}")
                            
        print("Cleanup completed successfully!")
    except Exception as e:
        print(f"Error during old blog data cleanup: {e}")

# ==================== ORCHESTRATOR ====================

def main():
    try:
        # Cleanup old/temporary/orphaned blog files
        cleanup_old_blog_data()
        
        # 0. Facebook Video scraper update
        get_latest_fb_video()
        
        # 1. Run Playwright-Gemini flow (Scrapes Trends, Suggestions, Content, and Images)
        blog_data = run_blog_generator_playwright()
        
        if not blog_data:
            print("Blog automation generation failed.")
            sys.exit(1)
            
        # 2. SEO Title & Description Validation and Sanitization
        meta_title = validate_meta_title(blog_data.get("meta_title", ""))
        meta_description = validate_meta_description(blog_data.get("meta_description", ""))
        
        blog_data["meta_title"] = meta_title
        blog_data["meta_description"] = meta_description
        
        # Lowercase friendly slug
        blog_data["slug"] = blog_data.get("slug", "").lower().replace(" ", "-").replace(":", "").replace("?", "").replace("&", "")
        blog_data["date"] = datetime.now().strftime("%B %d, %Y")
        blog_data["readTime"] = "5 min read"
        blog_data["author"] = "QuizViral AI Team"
        
        # 3. Smart Interlinking
        existing_blogs = load_existing_blogs(SCRIPT_DIR)
        interlinked_html = apply_smart_interlinking(blog_data["html"], existing_blogs, CTA_URL, BLOG_BASE_URL)
        
        # 4. Alt-Tags validation
        optimized_html = set_image_alt_tags(interlinked_html, blog_data["trendingKeyword"], blog_data["title"])
        
        # Ensure H1 tag is present at the beginning of HTML body
        if not optimized_html.strip().startswith("<h1"):
            optimized_html = f"<h1>{blog_data['title']}</h1>\n" + optimized_html.strip()
            
        blog_data["html"] = optimized_html
        
        # 5. Upload Image to Ghost CMS
        ghost_image_url = None
        if blog_data.get("local_image") and os.path.exists(blog_data["local_image"]):
            if GHOST_API_URL and GHOST_ADMIN_API_KEY:
                ghost_image_url = upload_image_to_ghost(
                    GHOST_API_URL, GHOST_ADMIN_API_KEY, GHOST_API_VERSION, blog_data["local_image"]
                )
        
        # Copy generated images to the frontend public assets folder so they can be loaded locally and deployed to Vercel
        public_blog_dir = os.path.join(SCRIPT_DIR, "frontend", "public", "assets", "blog")
        os.makedirs(public_blog_dir, exist_ok=True)
        
        local_landscape_public = None
        if blog_data.get("local_image") and os.path.exists(blog_data["local_image"]):
            dest_landscape = os.path.join(public_blog_dir, f"{blog_data['slug']}-landscape.png")
            try:
                import shutil
                shutil.copy2(blog_data["local_image"], dest_landscape)
                local_landscape_public = f"/assets/blog/{blog_data['slug']}-landscape.png"
                print(f"Copied landscape image to frontend public directory: {local_landscape_public}")
            except Exception as e:
                print(f"Error copying landscape image to frontend: {e}")
                
        local_pinterest_public = None
        if blog_data.get("local_pinterest_image") and os.path.exists(blog_data["local_pinterest_image"]):
            dest_pinterest = os.path.join(public_blog_dir, f"{blog_data['slug']}-pinterest.png")
            try:
                import shutil
                shutil.copy2(blog_data["local_pinterest_image"], dest_pinterest)
                local_pinterest_public = f"/assets/blog/{blog_data['slug']}-pinterest.png"
                print(f"Copied vertical image to frontend public directory: {local_pinterest_public}")
            except Exception as e:
                print(f"Error copying Pinterest image to frontend: {e}")
                
        # Set the image to the uploaded Ghost URL or the local public path
        blog_data["image"] = ghost_image_url or local_landscape_public or "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?auto=format&fit=crop&w=1200&h=675&q=80"
        
        # Prepend the feature image to both the Ghost HTML post body and the local frontend markdown file
        img_src = blog_data["image"]
        if img_src:
            # Ghost card standard format for body images
            blog_data["html"] = f'<figure class="kg-card kg-image-card"><img src="{img_src}" class="kg-image" alt="{blog_data["title"]}" loading="lazy"></figure>\n' + blog_data["html"]
            blog_data["markdown"] = f"![{blog_data['title']}]({img_src})\n\n" + blog_data["markdown"]
            
        # Set Pinterest image path
        blog_data["pinterest_image"] = local_pinterest_public or blog_data["image"]
        
        # 6. Publish to Ghost CMS
        if GHOST_API_URL and GHOST_ADMIN_API_KEY:
            success, result = publish_to_ghost_cms(
                GHOST_API_URL, GHOST_ADMIN_API_KEY, GHOST_API_VERSION, blog_data, status=PUBLISH_STATUS
            )
            if not success:
                print(f"Ghost CMS publish failed: {result}")
        else:
            print("Ghost CMS credentials not set. Skipping publishing to Ghost.")
            
        # CRITICAL SEO QUALITY GUARD: Never publish thin or empty content!
        content_words = len((blog_data.get("markdown") or "").split())
        if content_words < 350:
            print(f"\n[SEO Quality Guard] ERROR: Generated post content has only {content_words} words (< 350).")
            print("[SEO Quality Guard] Aborting blog publication and deploy to prevent Google thin-content penalty!")
            sys.exit(1)


        # 7. Update blogPosts.js for the Vercel React Frontend
        success_js = update_blog_posts_file(blog_data)
        
        if success_js:
            # 8. Sitemap and IndexNow
            sitemap_count = generate_sitemap_from_posts()
            ping_indexnow(blog_data["slug"])
            
            # 9. Build and push changes to trigger deployment
            print("Running build verification...")
            build_res = subprocess.run(["npm", "run", "build"], cwd=os.path.join(SCRIPT_DIR, "frontend"), shell=True)
            if build_res.returncode == 0:
                git_push_changes(blog_data["title"])
                
                # 12. Verify Live Sitemap count after deploy (polls to allow Vercel build to deploy)
                if sitemap_count > 0:
                    verify_live_sitemap(sitemap_count)
                
                # 11. Request indexing on Google Search Console & resubmit sitemap
                try:
                    launched_gsc = launch_chrome_if_needed()
                    if launched_gsc:
                        print("Connecting to Chrome debug instance for Google Search Console tasks...")
                        with sync_playwright() as p:
                            browser = p.chromium.connect_over_cdp("http://localhost:9222")
                            if browser.contexts:
                                context = browser.contexts[0]
                                post_url = f"https://quizviral-nine.vercel.app/blog/{blog_data['slug']}"
                                request_gsc_indexing_playwright(context, post_url)
                                resubmit_sitemap_gsc_playwright(context)
                            browser.close()
                except Exception as gsc_err:
                    print(f"Warning: Google Search Console automation failed: {gsc_err}")
                
                # 10. Trigger Pinterest Auto-Pin syndication using the vertical image!
                try:
                    from pinterest_auto_pin import run_pinterest_syndication
                    print("Initiating Pinterest syndication...")
                    run_pinterest_syndication(blog_data)
                except Exception as e:
                    print(f"Pinterest syndication failed: {e}")
                
                print(f"\nBlog successfully generated and published: {blog_data['title']}")
                sys.exit(0)
            else:
                print("Local build check failed! Aborting Git Push, GSC indexing, & Pinterest pinning to avoid breaking production.")
                sys.exit(1)
        else:
            print("Updating blog posts file failed.")
            sys.exit(1)
                
    finally:
        # Always terminate Chrome debug instance
        kill_chrome_on_port_9222()

if __name__ == "__main__":
    main()
