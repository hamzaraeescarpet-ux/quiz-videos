#!/usr/bin/env python3
"""
QuizViral AI - Trending Blog Post Generator (Playwright & Gemini)
================================================================
This script automates the full SEO blog generation pipeline using Playwright
to control Chrome (port 9222):
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
CHROME_PROFILE_PATH = r"C:\Users\hamza\Downloads\python development\browser automation\gemini video points\bulk scheduling fb videos\chrome_profile_2"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BLOG_POSTS_FILE = os.path.join(SCRIPT_DIR, "frontend", "src", "data", "blogPosts.js")

# Ghost CMS Credentials (loaded from environment variables, falls back to local values)
GHOST_API_URL = os.environ.get("GHOST_API_URL", "")
GHOST_ADMIN_API_KEY = os.environ.get("GHOST_ADMIN_API_KEY", "")
GHOST_API_VERSION = os.environ.get("GHOST_API_VERSION", "v2")
CTA_URL = os.environ.get("CTA_URL", "https://quizviral-nine.vercel.app")
BLOG_BASE_URL = os.environ.get("BLOG_BASE_URL", "https://quizviral-nine.vercel.app/blog")
PUBLISH_STATUS = os.environ.get("PUBLISH_STATUS", "draft") # Use "draft" to review first

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
    # Inline fallbacks if ghost_blog_automation is not available
    def validate_meta_title(t): return t[:60]
    def validate_meta_description(d): return d[:150]
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
        # "--headless=new", # Removed to enable visual (headful) mode
        "--disable-gpu",
        "--no-first-run",
        "--disable-default-apps",
        "--disable-session-crashed-bubble",
        "--hide-crash-restore-bubble",
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
        keys = ["title", "slug", "excerpt", "meta_title", "meta_description", "html", "markdown"]
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

def wait_for_gemini_response(page, mic_locator, stop_locator, max_wait_seconds=180):
    start_time = time.time()
    generation_done = False
    last_text = ""

    while time.time() - start_time < max_wait_seconds:
        try:
            is_mic_visible = False
            if mic_locator.count() > 0:
                for i in range(mic_locator.count()):
                    if mic_locator.nth(i).is_visible():
                        is_mic_visible = True
                        break

            is_stop_visible = False
            if stop_locator.count() > 0:
                for i in range(stop_locator.count()):
                    if stop_locator.nth(i).is_visible():
                        is_stop_visible = True
                        break

            if is_mic_visible and not is_stop_visible:
                print("Gemini response is ready!")
                generation_done = True
                break
        except Exception:
            break
        time.sleep(2)

    if not generation_done:
        print("Warning: Timed out waiting for mic button. Checking text stability...")
        for _ in range(15):
            time.sleep(2)
            responses = page.locator(".model-response, .message-content, message-content")
            if responses.count() > 0:
                current_text = responses.last.inner_text()
                if current_text == last_text and len(current_text) > 100:
                    break
                last_text = current_text

    responses = page.locator(".model-response, .message-content, message-content")
    if responses.count() > 0:
        return responses.last.inner_text()
    return last_text

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
        time.sleep(6)
        
        # Scrape grid cell row texts
        elements = page.locator('div[role="row"] div[role="gridcell"]').all_inner_texts()
        for el in elements:
            val = el.strip().split('\n')[0]
            if val and len(val) > 2 and len(val) < 40 and not val.isdigit():
                if val not in trends and not any(x in val.lower() for x in ["search", "explore", "trending", "menu", "sign in"]):
                    trends.append(val)
                    
        # Check anchors backup
        if len(trends) < 5:
            anchors = page.locator('td.query a, .trend-card a, tr td a').all_inner_texts()
            for el in anchors:
                val = el.strip()
                if val and len(val) > 2 and len(val) < 40:
                    if val not in trends:
                        trends.append(val)
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
    (e.g., sports/basketball, technology, space, etc.) to comply with Gemini's safety guidelines.
    """
    title_lower = post_title.lower()
    
    # Heuristics for common niches
    concept = "generic conceptual illustration of growth and success"
    if any(x in title_lower for x in ["marvin bagley", "nba", "basketball", "player", "sports"]):
        concept = "a generic basketball action scene on a professional court, with a player silhouette jumping towards a glowing hoop"
    elif any(x in title_lower for x in ["space", "galaxy", "universe", "planet"]):
        concept = "a futuristic space exploration rocket traveling through a vibrant cosmic nebula"
    elif any(x in title_lower for x in ["money", "monetiz", "income", "cash", "wealth"]):
        concept = "a modern abstract design showing upward financial growth charts and glowing digital coins"
    elif any(x in title_lower for x in ["video", "youtube", "tiktok", "shorts", "creator"]):
        concept = "a generic digital content creator setup showing a camera, ring light, and floating neon play icons"
    elif any(x in title_lower for x in ["discover", "seo", "google", "traffic", "search"]):
        concept = "a futuristic digital network globe with connecting data lines and expanding nodes"
    else:
        # General backup: extract main terms and build a generic prompt
        words = [w for w in re.split(r'\W+', post_title) if len(w) > 3]
        if words:
            concept = f"an artistic abstract representation of {', '.join(words[:3])}"
            
    if format_type == "landscape":
        prompt = (
            f"Generate a high-quality landscape illustration (16:9 aspect ratio) representing: {concept}. "
            "Make it clean, professional, and visually engaging. Do not depict any real-life individuals by name or face. "
            "Do not write any text or words on the image."
        )
    else:
        prompt = (
            f"Generate a vertical version (9:16 aspect ratio) of the exact same image (matching the same style, color scheme, and content) representing: {concept}. "
            "Ensure it does not include any text or words on the image."
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

def wait_for_and_download_new_image(page, previous_image_count, output_path):
    """
    Gemini conversation me new image generate hone ka wait karta hai,
    aur usse ya toh download button se ya toh element screenshot se local path par save karta hai.
    """
    print(f"Waiting for new image to generate (expecting image count > {previous_image_count})...")
    
    for attempt in range(40):
        time.sleep(2)
        # Identify image elements
        images = page.locator(".model-response img[src*='googleusercontent.com'], .model-response img[src*='blob:']").all()
        if len(images) > previous_image_count:
            print(f"New image element found (Attempt {attempt+1})! Wait 4s for render...")
            time.sleep(4)
            
            # Tier 1: Download button click
            try:
                download_btns = page.locator("button[aria-label*='Download' i], a[aria-label*='Download' i]").all()
                if len(download_btns) > previous_image_count:
                    print("Found download button. Clicking...")
                    with page.expect_download(timeout=15000) as download_info:
                        download_btns[-1].click()
                    download = download_info.value
                    download.save_as(output_path)
                    print(f"High-res image successfully downloaded via button to: {output_path}")
                    return True
            except Exception as e:
                print(f"Download button failed: {e}. Trying element screenshot as fallback...")
                
            # Tier 2: Screenshot fallback
            try:
                images[-1].screenshot(path=output_path)
                print(f"Successfully captured image element screenshot and saved to: {output_path}")
                return True
            except Exception as se:
                print(f"Screenshot fallback failed: {se}")
                
    print("Error: Image generation timed out or elements could not be resolved.")
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

def submit_prompt_to_gemini(page, prompt_text):
    """Types a prompt into Gemini and submits it using button click or Control+Enter fallback."""
    print("Typing prompt into Gemini...")
    textbox = page.locator("div[role='textbox']").first
    textbox.click()
    textbox.fill(prompt_text)
    time.sleep(1.5)
    
    # Try clicking the send button using various selectors
    clicked = False
    send_button_selectors = [
        "button[aria-label*='Send' i]",
        "button[aria-label*='Submit' i]",
        "button[aria-label*='भेजें' i]",
        "button.send-button",
        "div[role='button'][aria-label*='Send' i]",
        "gmat-icon-button[aria-label*='Send' i]"
    ]
    
    for sel in send_button_selectors:
        loc = page.locator(sel)
        for i in range(loc.count()):
            btn = loc.nth(i)
            if btn.is_visible() and btn.is_enabled():
                print(f"Clicking submit button with selector: {sel}")
                try:
                    btn.click(timeout=3000)
                    clicked = True
                    break
                except Exception:
                    pass
        if clicked:
            break
            
    if not clicked:
        # Fallback: Press Control+Enter inside the textbox to submit
        print("Submit button click failed or not found. Attempting fallback: Control+Enter to submit...")
        textbox.press("Control+Enter")
        clicked = True
        
    time.sleep(2)

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
            page = context.new_page()
            
            # --- 1. Scrape Trends ---
            top_trends = get_trends_from_page_and_rss(page)
            if not top_trends:
                print("No trending topics found. Aborting.")
                page.close()
                browser.close()
                return None
                
            print(f"Top trends to filter: {top_trends}")
            
            # --- 2. Navigate to Gemini to filter trend ---
            print("\n--- STEP 2: Connecting to Gemini for topic filtering ---")
            page.goto("https://gemini.google.com/app/5d22a66bd735a3fe")
            time.sleep(5)
            
            filter_prompt = (
                f"Out of these 5 trending topics: {json.dumps(top_trends)}. "
                "Which one is the easiest and most interesting to write a trivia/quiz blog post about? "
                "Choose exactly one. Respond with ONLY the chosen topic name, and absolutely nothing else."
            )
            
            submit_prompt_to_gemini(page, filter_prompt)
            
            mic_locator = page.locator("button[aria-label*='microphone' i], button[aria-label*='mic' i], button[aria-label*='माइक्रो' i]")
            stop_locator = page.locator("button[aria-label*='Stop' i], button[aria-label*='रोकें' i]")
            
            selected_topic = wait_for_gemini_response(page, mic_locator, stop_locator).strip()
            # Clean possible markdown or quote wrappers by Gemini
            selected_topic = selected_topic.strip('"\'`').replace('\n', '').strip()
            print(f"Gemini selected topic: '{selected_topic}'")
            
            if not selected_topic or len(selected_topic) > 80:
                print("Invalid topic selected by Gemini. Defaulting to first trend.")
                selected_topic = top_trends[0]
                
            # --- 3. Google Search Autocomplete Suggestions ---
            suggestions = get_autocomplete_suggestions(page, selected_topic)
            # Limit to top 15 diverse suggestions to prevent prompt clutter and Google SEO keyword stuffing penalties
            suggestions = suggestions[:15]
            
            # --- 4. Content Generation Prompt (Multi-Turn) ---
            print("\n--- STEP 4: Generating Blog Post Content via Gemini (Multi-Turn) ---")
            page.goto("https://gemini.google.com/app/5d22a66bd735a3fe")
            time.sleep(4)
            
            # TURN 1: Write Introduction Section
            print("\n--- TURN 1: Generating Introduction ---")
            prompt_turn1 = (
                f"We are writing a blog post about the trending topic: \"{selected_topic}\" for QuizViral AI (which automates bulk quiz video creation).\n"
                f"Target Keyword: \"{selected_topic}\"\n"
                f"Additional keywords to include: {json.dumps(suggestions)}.\n\n"
                f"Write a compelling, SEO-optimized Introduction section (minimum 400 words) starting with an <h1> tag containing the target keyword. "
                "Focus on why this topic is trending and how quiz videos can capture this traffic.\n"
                "Respond with ONLY raw HTML body content. Do not include <html>, <head>, or <body> wrappers, and do not wrap in markdown code blocks."
            )
            submit_prompt_to_gemini(page, prompt_turn1)
            raw_intro = wait_for_gemini_response(page, mic_locator, stop_locator, max_wait_seconds=120)
            print("Successfully read Turn 1 (Introduction) response.")
            
            # TURN 2: Write Tutorial & 10 Quiz Questions
            print("\n--- TURN 2: Generating Tutorial & 10 Quiz Questions ---")
            prompt_turn2 = (
                f"Excellent. Now write the second section (minimum 600 words):\n"
                f"- A step-by-step tutorial on how content creators can use QuizViral AI to mass-produce 100+ quiz videos about \"{selected_topic}\" in 1 click using CSV spreadsheet imports, choosing background loops (Minecraft, Space, Nature), and generating natural AI voiceovers.\n"
                f"- Include 10 complete quiz questions about \"{selected_topic}\" with 4 options (A, B, C, D) and specify the correct answer clearly. Format these questions as structured HTML lists or tables.\n\n"
                "Respond with ONLY raw HTML body content using <h2>, <h3>, <p>, <ul>, <li>, etc. Do not wrap in markdown code blocks."
            )
            submit_prompt_to_gemini(page, prompt_turn2)
            raw_tutorial = wait_for_gemini_response(page, mic_locator, stop_locator, max_wait_seconds=150)
            print("Successfully read Turn 2 (Tutorial & Quiz Questions) response.")
            
            # TURN 3: Write Monetization & FAQs
            print("\n--- TURN 3: Generating Monetization & FAQs ---")
            prompt_turn3 = (
                f"Excellent. Now write the final section (minimum 500 words):\n"
                f"- YouTube Quiz Channel Monetization Strategy: securing YPP status (10M shorts views in 90 days), and alternate revenue streams (affiliates, print-on-demand, digital trivia downloads).\n"
                f"- 3 Frequently Asked Questions (FAQs) about automated quiz channels.\n\n"
                "Respond with ONLY raw HTML body content using <h2>, <h3>, <p>, <ul>, <li>, etc. Do not wrap in markdown code blocks."
            )
            submit_prompt_to_gemini(page, prompt_turn3)
            raw_monetization = wait_for_gemini_response(page, mic_locator, stop_locator, max_wait_seconds=120)
            print("Successfully read Turn 3 (Monetization & FAQs) response.")
            
            # Combine the HTML components
            html_content = f"{raw_intro}\n{raw_tutorial}\n{raw_monetization}"
            html_content = clean_markdown_response(html_content)
            
            # TURN 4: Compile Metadata JSON & Markdown version
            print("\n--- TURN 4: Compiling Metadata JSON ---")
            prompt_turn4 = (
                "Awesome. Based on the complete article we just generated, compile the SEO metadata.\n"
                "Respond ONLY with a JSON object in this format. Do not wrap in markdown code blocks:\n"
                "{\n"
                "  \"title\": \"SEO Headline containing the keyword\",\n"
                "  \"slug\": \"url-friendly-slug-with-keyword\",\n"
                "  \"excerpt\": \"Compelling 2-sentence summary of the post\",\n"
                "  \"meta_title\": \"SEO Meta Title (exactly 50-60 characters featuring keywords like 'faceless quiz videos' or 'AI video generator')\",\n"
                "  \"meta_description\": \"SEO Meta Description (exactly 145-150 characters featuring keywords like 'AI video generator' or 'bulk quiz maker')\",\n"
                "  \"markdown\": \"Complete blog post in markdown format (including title, headers, body, 10 quiz questions, and FAQs)\"\n"
                "}"
            )
            submit_prompt_to_gemini(page, prompt_turn4)
            raw_metadata = wait_for_gemini_response(page, mic_locator, stop_locator, max_wait_seconds=90)
            print("Successfully read Turn 4 (Metadata JSON) response.")
            
            cleaned_json = clean_markdown_response(raw_metadata)
            
            # Find and parse JSON
            blog_data = None
            json_match = re.search(r"\{.*\}", cleaned_json, re.DOTALL)
            if json_match:
                try:
                    blog_data = json.loads(json_match.group(0))
                except Exception:
                    blog_data = fallback_json_parser(json_match.group(0))
            else:
                blog_data = fallback_json_parser(cleaned_json)
                
            if not blog_data:
                print("Error: Could not parse metadata JSON from Gemini. Trying custom build...")
                blog_data = {
                    "title": f"The Ultimate Guide to {selected_topic}",
                    "slug": selected_topic.lower().replace(" ", "-"),
                    "excerpt": f"Discover how to create viral quiz videos about {selected_topic} automatically.",
                    "meta_title": f"How to Make Quiz Videos about {selected_topic} Instantly",
                    "meta_description": f"Learn how to create automated faceless quiz videos about {selected_topic} to grow your channel.",
                    "markdown": f"# The Ultimate Guide to {selected_topic}\n\n" + html_content.replace("<p>", "").replace("</p>", "\n\n").replace("<h2>", "## ").replace("</h2>", "\n\n")
                }
            
            # Attach combined HTML
            blog_data["html"] = html_content
            
            # Count current images in Gemini conversation to set baselines
            initial_images = page.locator(".model-response img[src*='googleusercontent.com'], .model-response img[src*='blob:']").all()
            image_baseline = len(initial_images)
            print(f"Initial images count in chat: {image_baseline}")
            
            # --- 5. Generate Landscape Image ---
            print("\n--- STEP 5: Generating Landscape Image (16:9) ---")
            image_prompt = create_safe_image_prompt(blog_data.get("title", selected_topic), format_type="landscape")
            image_prompt += " Generate only one single image. Do not generate multiple options or variations."
            print(f"Image Prompt: {image_prompt}")
            
            submit_prompt_to_gemini(page, image_prompt)
            
            landscape_path = os.path.join(SCRIPT_DIR, "assets", "landscape_image.png")
            os.makedirs(os.path.dirname(landscape_path), exist_ok=True)
            
            success_landscape = wait_for_and_download_new_image(page, image_baseline, landscape_path)
            if success_landscape:
                blog_data["local_image"] = landscape_path
            else:
                print("Failed to obtain landscape image. Using hardcoded fallback.")
                blog_data["local_image"] = None
                
            # Update image baseline for next prompt
            time.sleep(2)
            current_images = page.locator(".model-response img[src*='googleusercontent.com'], .model-response img[src*='blob:']").all()
            image_baseline = len(current_images)
            
            # --- 6. Generate Pinterest Vertical Image ---
            print("\n--- STEP 6: Generating Pinterest Vertical Image (9:16) ---")
            pinterest_prompt = create_safe_image_prompt(blog_data.get("title", selected_topic), format_type="vertical")
            pinterest_prompt += " Generate only one single vertical image. Do not generate multiple options or variations."
            print(f"Pinterest Image Prompt: {pinterest_prompt}")
            
            submit_prompt_to_gemini(page, pinterest_prompt)
            
            pinterest_path = os.path.join(SCRIPT_DIR, "assets", "pinterest_image.png")
            success_pinterest = wait_for_and_download_new_image(page, image_baseline, pinterest_path)
            if success_pinterest:
                blog_data["local_pinterest_image"] = pinterest_path
            else:
                print("Failed to obtain Pinterest vertical image.")
                blog_data["local_pinterest_image"] = None
                
            # Close browser
            page.close()
            browser.close()
            
            blog_data["trendingKeyword"] = selected_topic
            return blog_data
            
        except Exception as e:
            print(f"Exception during Playwright execution: {e}")
            import traceback
            traceback.print_exc()
            
    return None


def get_latest_fb_video():
    # Facebook page video scraping logic (preserved from original code)
    print("Scraping Facebook page for latest video...")
    fb_page_url = "https://www.facebook.com/profile.php?id=61585764748589"
    latest_video_url = "https://www.facebook.com/watch/?v=892872416450589"
    
    if check_port_open(9222):
        try:
            with sync_playwright() as p:
                browser = p.chromium.connect_over_cdp("http://localhost:9222")
                context = browser.contexts[0]
                page = context.new_page()
                page.goto(fb_page_url)
                time.sleep(5)
                page.evaluate("window.scrollBy(0, 1000);")
                time.sleep(4)
                
                scripts = page.locator("script").evaluate_all("elements => elements.map(el => el.textContent || '')")
                video_ids = []
                for script in scripts:
                    if not script: continue
                    for m in re.finditer(r'"video_id"\s*:\s*"(\d+)"', script):
                        video_ids.append(m.group(1))
                
                if video_ids:
                    latest_video_url = f"https://www.facebook.com/watch/?v={video_ids[0]}"
                page.close()
                browser.close()
        except Exception as e:
            print(f"Facebook scrape failed: {e}")
            
    dest_path = os.path.join(SCRIPT_DIR, "frontend", "src", "data", "latestFbVideo.js")
    try:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(f'export const latestFbVideoUrl = "{latest_video_url}";\n')
    except Exception:
        pass

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
        "trendingKeyword": new_post["trendingKeyword"]
    }
    
    new_post_str = json.dumps(post_item, indent=2)
    # Re-align JSON properties names for compatibility with JS parser
    for prop in ["title", "slug", "excerpt", "date", "readTime", "author", "image", "pinterest_image", "metaDescription", "seoKeywords", "content", "trendingKeyword"]:
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
    
    slugs = []
    if os.path.exists(BLOG_POSTS_FILE):
        try:
            with open(BLOG_POSTS_FILE, "r", encoding="utf-8") as f:
                content = f.read()
            slugs = re.findall(r"\bslug:\s*['\"`]([^'\"`]+?)['\"`]", content)
            slugs = list(dict.fromkeys(slugs))
        except Exception:
            pass
            
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        f'  <url><loc>https://quizviral-nine.vercel.app/</loc><lastmod>{today_str}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>',
        f'  <url><loc>https://quizviral-nine.vercel.app/pricing</loc><lastmod>{today_str}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>',
        f'  <url><loc>https://quizviral-nine.vercel.app/blog</loc><lastmod>{today_str}</lastmod><changefreq>daily</changefreq><priority>0.9</priority></url>'
    ]
    for s in slugs:
        xml_lines.append(f'  <url><loc>https://quizviral-nine.vercel.app/blog/{s}</loc><lastmod>{today_str}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>')
    xml_lines.append('</urlset>')
    
    try:
        os.makedirs(os.path.dirname(sitemap_path), exist_ok=True)
        with open(sitemap_path, "w", encoding="utf-8") as f:
            f.write("\n".join(xml_lines) + "\n")
        return True
    except Exception:
        return False

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
        subprocess.run(["git", "add", "."], cwd=SCRIPT_DIR, check=True)
        subprocess.run(["git", "commit", "-m", f"chore(blog): auto-publish post '{title}'"], cwd=SCRIPT_DIR, check=True)
        subprocess.run(["git", "push", "github", "main"], cwd=SCRIPT_DIR, check=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=SCRIPT_DIR, check=True) # Hugging Face
        print("Git Push Completed!")
    except Exception as e:
        print(f"Git push failed: {e}")

# ==================== ORCHESTRATOR ====================

def main():
    try:
        # 0. Facebook Video scraper update
        get_latest_fb_video()
        
        # 1. Run Playwright-Gemini flow (Scrapes Trends, Suggestions, Content, and Images)
        blog_data = run_blog_generator_playwright()
        
        if not blog_data:
            print("Blog automation generation failed.")
            return
            
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
        
        # Fallback image URL
        blog_data["image"] = ghost_image_url or "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?auto=format&fit=crop&w=1200&h=675&q=80"
        
        # Set Pinterest image path
        blog_data["pinterest_image"] = blog_data.get("local_pinterest_image") or blog_data["image"]
        
        # 6. Publish to Ghost CMS
        if GHOST_API_URL and GHOST_ADMIN_API_KEY:
            success, result = publish_to_ghost_cms(
                GHOST_API_URL, GHOST_ADMIN_API_KEY, GHOST_API_VERSION, blog_data, status=PUBLISH_STATUS
            )
            if not success:
                print(f"Ghost CMS publish failed: {result}")
        else:
            print("Ghost CMS credentials not set. Skipping publishing to Ghost.")
            
        # 7. Update blogPosts.js for the Vercel React Frontend
        success_js = update_blog_posts_file(blog_data)
        
        if success_js:
            # 8. Sitemap and IndexNow
            generate_sitemap_from_posts()
            ping_indexnow(blog_data["slug"])
            
            # 9. Build and push changes to trigger deployment
            print("Running build verification...")
            build_res = subprocess.run(["npm", "run", "build"], cwd=os.path.join(SCRIPT_DIR, "frontend"), shell=True)
            if build_res.returncode == 0:
                git_push_changes(blog_data["title"])
                
                # 10. Trigger Pinterest Auto-Pin syndication using the vertical image!
                try:
                    from pinterest_auto_pin import run_pinterest_syndication
                    print("Initiating Pinterest syndication...")
                    run_pinterest_syndication(blog_data)
                except Exception as e:
                    print(f"Pinterest syndication failed: {e}")
            else:
                print("Local build check failed! Aborting Git Push & Pinterest pinning to avoid breaking production.")
                
    finally:
        # Always terminate Chrome debug instance
        kill_chrome_on_port_9222()

if __name__ == "__main__":
    main()
