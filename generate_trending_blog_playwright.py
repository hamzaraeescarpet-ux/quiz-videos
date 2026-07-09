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
        # "--headless=new", # Removed to enable visual (headful) mode
        "--disable-gpu",
        "--no-first-run",
        "--disable-default-apps",
        "--disable-session-crashed-bubble",
        "--hide-crash-restore-bubble",
        "--disable-blink-features=AutomationControlled",
        "--window-position=0,0",
        "--window-size=1280,720",
        "--start-maximized"
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

def wait_for_chatgpt_response(page, max_wait_seconds=600):
    print("Waiting for ChatGPT response...")
    start_time = time.time()
    
    # Wait for the generation to start (give it a few seconds to toggle buttons)
    time.sleep(4)
    
    last_text = ""
    stable_count = 0
    
    while time.time() - start_time < max_wait_seconds:
        # Check Stop button visibility in ChatGPT
        stop_btns = page.locator("button[data-testid='stop-button'], button[aria-label='Stop generating'], button[aria-label*='Stop' i]").all()
        is_stop_visible = False
        for btn in stop_btns:
            try:
                if btn.is_visible():
                    is_stop_visible = True
                    break
            except Exception:
                pass
                
        # Check Send button visibility/enabled state (when done, the send button is enabled)
        send_btns = page.locator("button[data-testid='send-button'], button[aria-label*='Send' i], button.send-button").all()
        is_send_enabled = False
        for btn in send_btns:
            try:
                if btn.is_visible() and btn.is_enabled():
                    is_send_enabled = True
                    break
            except Exception:
                pass
                
        # Get current response text from ChatGPT assistant message block
        responses = page.locator("div[data-message-author-role='assistant'] .markdown, .markdown, .message-content")
        current_text = ""
        if responses.count() > 0:
            try:
                current_text = responses.last.inner_text().strip()
            except Exception:
                pass
            
        # STRICT MODEL RESOLUTION RULE:
        # 1. Stop button must be completely hidden
        # 2. Send button must be visible & active/enabled
        # 3. We must have some response content (> 2 chars) loaded
        if not is_stop_visible and is_send_enabled and len(current_text) > 2:
            print("Generation complete! (Stop button is hidden, Send button is visible & active).")
            return current_text
            
        # Backup text stability check in case of unexpected DOM changes
        if len(current_text) > 2:
            if current_text == last_text:
                stable_count += 1
                if stable_count >= 5: # Stable for 10 seconds
                    print("Generation complete (Text is stable fallback).")
                    return current_text
            else:
                stable_count = 0
                
        last_text = current_text
        time.sleep(2)
        
    responses = page.locator("div[data-message-author-role='assistant'] .markdown, .markdown, .message-content")
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

def submit_prompt_to_chatgpt(page, prompt_text):
    """Types a prompt into ChatGPT and submits it using button click or Enter fallback."""
    print("Waiting for ChatGPT input box to be ready...")
    textbox = page.locator("#prompt-textarea, textarea[id='prompt-textarea']").first
    try:
        textbox.wait_for(state="visible", timeout=30000)
    except Exception as e:
        print(f"Warning: Input box wait timed out: {e}")
        
    print("Typing prompt into ChatGPT...")
    textbox.click()
    textbox.fill(prompt_text)
    time.sleep(0.5)
    
    # Trigger input change listeners by typing space and backspace
    textbox.press(" ")
    time.sleep(0.2)
    textbox.press("Backspace")
    time.sleep(1)
    
    # Try clicking the send button using various selectors
    clicked = False
    send_button_selectors = [
        "button[data-testid='send-button']",
        "button[aria-label*='Send' i]",
        "button.send-button"
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
        # Fallback: Press Enter inside the textbox to submit in ChatGPT
        print("Submit button click failed or not found. Attempting fallback: Enter to submit...")
        textbox.press("Enter")
        clicked = True
        
    time.sleep(2)

def submit_and_wait_for_response(page, prompt_text, max_wait_seconds=180, max_retries=2):
    """
    Submits a prompt to ChatGPT and waits for the response.
    If the response fails, times out, or returns empty, reloads the page (retaining thread history) and retries.
    """
    active_url = page.url
    for attempt in range(max_retries + 1):
        if attempt > 0:
            print(f"\n--- Retrying Prompt Submission (Attempt {attempt + 1}/{max_retries + 1}) ---")
            print("Reloading the page...")
            try:
                page.reload()
                time.sleep(8) # Wait for page reload to stabilize
            except Exception as re:
                print(f"Page reload failed: {re}. Navigating back to active thread URL...")
                try:
                    page.goto(active_url)
                    time.sleep(8)
                except Exception:
                    pass
                
        # Submit the prompt
        try:
            submit_prompt_to_chatgpt(page, prompt_text)
        except Exception as se:
            print(f"Submission failed: {se}. Retrying reload...")
            continue
            
        # Wait for the response
        response_text = wait_for_chatgpt_response(page, max_wait_seconds=max_wait_seconds)
        
        # If response is valid, return it!
        if response_text and len(response_text.strip()) > 5:
            # Update the active thread URL in case it changed
            try:
                active_url = page.url
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
            
            # Create main Gemini page
            gemini_page = context.new_page()
            
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
            gemini_page.goto("https://chatgpt.com/c/6a47d525-af3c-83e8-9b33-a5c2b2669d17")
            
            # Wait for text box to load in ChatGPT
            textbox = gemini_page.locator("#prompt-textarea, textarea[id='prompt-textarea']").first
            try:
                textbox.wait_for(state="visible", timeout=30000)
            except Exception:
                pass
            time.sleep(5)
            
            filter_prompt = (
                f"Out of these 5 trending topics: {json.dumps(top_trends)}. "
                "Which one is the easiest and most interesting to write a trivia/quiz blog post about? "
                "Choose exactly one. Respond with ONLY the chosen topic name, and absolutely nothing else."
            )
            
            selected_topic = submit_and_wait_for_response(gemini_page, filter_prompt, max_wait_seconds=120)
            # Clean possible markdown or quote wrappers by ChatGPT
            selected_topic = selected_topic.strip('"\'`').replace('\n', '').strip()
            print(f"ChatGPT selected topic: '{selected_topic}'")
            
            if not selected_topic or len(selected_topic) > 80:
                print("Invalid topic selected by ChatGPT. Defaulting to first trend.")
                selected_topic = top_trends[0]
                
            # --- 3. Google Search Autocomplete Suggestions ---
            # We use a temporary page for autocomplete so gemini_page doesn't navigate away
            print("\n--- STEP 3: Scraping Google Autocomplete ---")
            search_page = context.new_page()
            suggestions = get_autocomplete_suggestions(search_page, selected_topic)
            search_page.close()
            
            # Limit to top 15 diverse suggestions to prevent prompt clutter and Google SEO keyword stuffing penalties
            suggestions = suggestions[:15]
            
            # --- 4. Get Image Prompts from ChatGPT (BEFORE content generation to save quota and verify first) ---
            print("\n--- STEP 4: Requesting Image Prompts from ChatGPT ---")
            prompt_image_prompts = (
                f"For the selected trending topic \"{selected_topic}\", write two photorealistic image prompts:\n"
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
            prompt_turn1 = (
                f"We are writing a blog post about the trending topic: \"{selected_topic}\".\n"
                f"Target Keyword: \"{selected_topic}\"\n"
                f"Additional keywords to include: {json.dumps(suggestions)}.\n\n"
                f"Write a compelling, SEO-optimized Introduction section (minimum 400 words) starting with an <h1> tag containing the target keyword. "
                f"Focus strictly on \"{selected_topic}\", why it is currently trending, its significance, background, and key facts. "
                "Do NOT mention quiz videos, video creators, bulk quiz makers, or QuizViral AI here. Focus 100% on the topic itself.\n"
                "Respond with ONLY raw HTML body content. Do not include <html>, <head>, or <body> wrappers, and do not wrap in markdown code blocks."
            )
            raw_intro = submit_and_wait_for_response(gemini_page, prompt_turn1, max_wait_seconds=150)
            print("Successfully read Turn 1 (Introduction) response.")
            
            # TURN 2: Write Tutorial & 10 Quiz Questions
            print("\n--- TURN 2: Generating Tutorial & 10 Quiz Questions ---")
            prompt_turn2 = (
                f"Excellent. Now write the second section (minimum 600 words):\n"
                f"- Go deeper into details, history, analysis, or current events about \"{selected_topic}\" to provide maximum value to the reader.\n"
                f"- Include 10 complete quiz questions about \"{selected_topic}\" with 4 options (A, B, C, D) and specify the correct answer clearly. Format these questions as structured HTML lists or tables.\n\n"
                "Do NOT mention video creation tools, AI generators, or QuizViral AI here. Focus 100% on the topic itself. "
                "Respond with ONLY raw HTML body content using <h2>, <h3>, <p>, <ul>, <li>, etc. Do not wrap in markdown code blocks."
            )
            raw_tutorial = submit_and_wait_for_response(gemini_page, prompt_turn2, max_wait_seconds=180)
            print("Successfully read Turn 2 (Tutorial & Quiz Questions) response.")
            
            # TURN 3: Write Monetization & FAQs
            print("\n--- TURN 3: Generating Monetization & FAQs ---")
            prompt_turn3 = (
                f"Excellent. Now write the final section (minimum 500 words):\n"
                f"- Introduce QuizViral AI: Explain how content creators can leverage the viral interest in \"{selected_topic}\" by using QuizViral AI to mass-produce 100+ quiz videos about \"{selected_topic}\" in 1 click using CSV spreadsheet imports, choosing background loops (Minecraft, Space, Nature), and generating natural AI voiceovers.\n"
                f"- YouTube Quiz Channel Monetization Strategy: securing YPP status (10M shorts views in 90 days), and alternate revenue streams (affiliates, print-on-demand, digital trivia downloads).\n"
                f"- 3 Frequently Asked Questions (FAQs) about automated quiz channels.\n\n"
                "Respond with ONLY raw HTML body content using <h2>, <h3>, <p>, <ul>, <li>, etc. Do not wrap in markdown code blocks."
            )
            raw_monetization = submit_and_wait_for_response(gemini_page, prompt_turn3, max_wait_seconds=150)
            print("Successfully read Turn 3 (Monetization & FAQs) response.")
            
            # Combine the HTML components
            html_content = f"{raw_intro}\n{raw_tutorial}\n{raw_monetization}"
            html_content = clean_markdown_response(html_content)
            
            # TURN 4: SEO Metadata compilation (Simplified JSON format)
            print("\n--- TURN 4: Compiling SEO Metadata ---")
            prompt_turn4 = (
                "Awesome. Based on the complete article we just generated, compile the SEO metadata.\n"
                "Respond ONLY with a JSON object in this format. Do not wrap in markdown code blocks:\n"
                "{\n"
                "  \"title\": \"SEO Headline containing the keyword (strictly about the topic itself, e.g. secrets/history/stardom of the topic. DO NOT mention quiz, video, or QuizViral in the title)\",\n"
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
            return blog_data
            
        except Exception as e:
            print(f"Exception during Playwright execution: {e}")
            import traceback
            traceback.print_exc()
            

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
                context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
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
