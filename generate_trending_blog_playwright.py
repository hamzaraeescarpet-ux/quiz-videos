import os
import sys
import re
import json
import time
import xml.etree.ElementTree as ET
import urllib.request
import subprocess
from datetime import datetime
from playwright.sync_api import sync_playwright

# ==================== CONFIGURATION ====================
# आपके Chrome Profile का पाथ (लॉगिन सेशन बनाए रखने के लिए)
CHROME_PROFILE_PATH = r"C:\Users\hamza\Downloads\python development\browser automation\gemini video points\bulk scheduling fb videos\chrome_profile_2"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BLOG_POSTS_FILE = os.path.join(SCRIPT_DIR, "frontend", "src", "data", "blogPosts.js")
# ========================================================

def get_trending_keyword(index=0):
    """Google Trends RSS Feed से ट्रेंडिंग कीवर्ड निकालता है (100% फ़्री)"""
    print(f"Fetching trending keyword at index {index} from Google Trends...")
    url = "https://trends.google.com/trending/rss?geo=US"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
        
        root = ET.fromstring(xml_data)
        items = root.findall(".//item")
        if items and len(items) > index:
            title = items[index].find("title").text
            print(f"Trending topic found at index {index}: {title}")
            return title
        else:
            print(f"Index {index} out of bounds (found {len(items)} items). Using fallback.")
            return f"TikTok Quiz Videos {index}"
    except Exception as e:
        print(f"Error fetching trends: {e}. Falling back to default keyword.")
        return f"TikTok Quiz Videos {index}"

# =============================================================================
# IMAGE CASCADE: Pixabay → Pexels → Unsplash → Wikipedia
# All free, all HD, 3 API keys each for rotation & rate-limit bypass
# =============================================================================
_PIXABAY_KEYS = [
    "54314916-5f365780e5c27849c23bc950f",   # hamzaraeescarpet
    "56417685-c45a05a6f9a78c8d4170368f9",   # deshkikhabar
    "56417696-67f37932e14092cf9a67139f9",   # aajkikhabar34
]
_PEXELS_KEYS = [
    "NqX67bkvlFlTSnZmIFSFNIchLP0ARNW0X2OfaTWJvp7IJNXsIzOWQ1bH",  # hamzaraeescarpet
    "GT9G57i8szub34xyk134pm4BbdVwgKzYsvjCFTer1lyF7u9nhe1vxrBT",  # aajkikhabar34
    "PKiIguzl3Pox7aMpM7PKb4iX7kKi2JJJC6r2pidstpUAFgHdA6HgM2CL",  # deshkikhabar34
]
_pix_idx = 0
_pex_idx = 0

def _get_pixabay_key():
    global _pix_idx
    k = _PIXABAY_KEYS[_pix_idx % len(_PIXABAY_KEYS)]
    _pix_idx += 1
    return k

def _get_pexels_key():
    global _pex_idx
    k = _PEXELS_KEYS[_pex_idx % len(_PEXELS_KEYS)]
    _pex_idx += 1
    return k

def get_blog_image(keyword):
    """
    Fetches an HD blog featured image using a 4-tier cascade:
      1. Pixabay  (HD/4K, 3 rotating keys) — PRIMARY
      2. Pexels   (HD/4K, 3 rotating keys) — SECONDARY
      3. Unsplash (napi search, unofficial but widely used) — TERTIARY
      4. Wikipedia thumbnail — LAST RESORT
    Returns a landscape image URL (1200x675 / 16:9) suitable for blog headers.
    """
    import ssl
    import urllib.parse
    ssl_ctx = ssl._create_unverified_context()

    # Use a richer query for blog-style imagery
    query = f"{keyword} technology creator" if "quiz" in keyword.lower() else keyword
    encoded = urllib.parse.quote(query)

    # ------------------------------------------------------------------
    # TIER 1: Pixabay (HD photos, 3 rotating API keys)
    # ------------------------------------------------------------------
    print(f"[BlogImage] Trying Pixabay for: '{query}'...")
    for _ in range(len(_PIXABAY_KEYS)):
        api_key = _get_pixabay_key()
        try:
            url = (
                f"https://pixabay.com/api/?key={api_key}"
                f"&q={encoded}&image_type=photo&per_page=5"
                f"&safesearch=true&min_width=1200&order=popular"
                f"&orientation=horizontal"
            )
            req = urllib.request.Request(url, headers={'User-Agent': 'QuizViralBot/2.0'})
            with urllib.request.urlopen(req, timeout=10, context=ssl_ctx) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                hits = data.get("hits", [])
                if target_publish:
                    target_publish.scroll_into_view_if_needed()
                    time.sleep(1.5)
                    # Wait for button to be enabled (image might still be uploading)
                    for _w in range(10):
                        try:
                            is_disabled = target_publish.get_attribute("disabled") is not None
                            aria_disabled = target_publish.get_attribute("aria-disabled")
                            if not is_disabled and aria_disabled != "true":
                                break
                        except Exception:
                            break
                        print(f"Publish button abhi disabled hai, 2 sec wait kar rahe hai... ({_w+1}/10)")
                        time.sleep(2)
                    print("Publish/Save button click kar rahe hai...")
                    target_publish.click()
                    print("Publish click ho gaya! Completion ke liye wait kar rahe hai (20 seconds)...")
                    time.sleep(20)  # Wait for Pinterest to process
                    print("Pin published successfully!")
                if hits:
                    img = hits[0]
                    img_url = (
                        img.get("fullHDURL") or
                        img.get("largeImageURL") or
                        img.get("webformatURL")
                    )
                    if img_url:
                        print(f"[BlogImage] Pixabay SUCCESS: {img_url[:80]}...")
                        return img_url
        except Exception as e:
            print(f"[BlogImage] Pixabay attempt failed: {e}")

    # ------------------------------------------------------------------
    # TIER 2: Pexels (HD photos, 3 rotating API keys)
    # ------------------------------------------------------------------
    print(f"[BlogImage] Pixabay failed — trying Pexels...")
    for _ in range(len(_PEXELS_KEYS)):
        api_key = _get_pexels_key()
        try:
            url = f"https://api.pexels.com/v1/search?query={encoded}&per_page=5&size=large&orientation=landscape"
            req = urllib.request.Request(
                url,
                headers={'Authorization': api_key, 'User-Agent': 'QuizViralBot/2.0'}
            )
            with urllib.request.urlopen(req, timeout=10, context=ssl_ctx) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                photos = data.get("photos", [])
                if photos:
                    src = photos[0].get("src", {})
                    img_url = src.get("large2x") or src.get("original") or src.get("large")
                    if img_url:
                        print(f"[BlogImage] Pexels SUCCESS: {img_url[:80]}...")
                        return img_url
        except Exception as e:
            print(f"[BlogImage] Pexels attempt failed: {e}")

    # ------------------------------------------------------------------
    # TIER 3: Unsplash (unofficial napi, reliable enough as tertiary)
    # ------------------------------------------------------------------
    print(f"[BlogImage] Pexels failed — trying Unsplash napi...")
    try:
        search_url = f"https://unsplash.com/napi/search/photos?query={encoded}&per_page=5"
        req = urllib.request.Request(
            search_url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=10, context=ssl_ctx) as response:
            data = json.loads(response.read().decode('utf-8'))
            results = data.get("results", [])
            if results:
                base_url = results[0]["urls"]["regular"].split("?")[0]
                img_url = f"{base_url}?auto=format&fit=crop&w=1200&h=675&q=80"
                print(f"[BlogImage] Unsplash SUCCESS: {img_url[:80]}...")
                return img_url
    except Exception as e:
        print(f"[BlogImage] Unsplash napi failed: {e}")

    # ------------------------------------------------------------------
    # TIER 4: Wikipedia thumbnail (last resort)
    # ------------------------------------------------------------------
    print(f"[BlogImage] Unsplash failed — trying Wikipedia fallback...")
    try:
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(keyword)}&utf8=&format=json&srlimit=1"
        req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10, context=ssl_ctx) as response:
            search_data = json.loads(response.read().decode('utf-8'))
            search_results = search_data.get("query", {}).get("search", [])
            if search_results:
                best_title = search_results[0]["title"]
                image_url_api = f"https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&piprop=thumbnail&pithumbsize=1280&titles={urllib.parse.quote(best_title)}&redirects=1"
                req2 = urllib.request.Request(image_url_api, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req2, timeout=10, context=ssl_ctx) as response2:
                    img_data = json.loads(response2.read().decode('utf-8'))
                    pages = img_data.get("query", {}).get("pages", {})
                    for page_id, page_data in pages.items():
                        if "thumbnail" in page_data:
                            wiki_img = page_data["thumbnail"]["source"]
                            print(f"[BlogImage] Wikipedia SUCCESS: {wiki_img}")
                            return wiki_img
    except Exception as e:
        print(f"[BlogImage] Wikipedia fallback failed: {e}")

    # Hardcoded safe fallback
    print("[BlogImage] All sources failed. Using hardcoded fallback image.")
    return "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?auto=format&fit=crop&w=1200&h=675&q=80"

# Keep old name as alias for backward compatibility
def get_unsplash_image(keyword):
    return get_blog_image(keyword)

def check_port_open(port):

    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except Exception:
        return False

def launch_chrome_if_needed():
    if check_port_open(9222):
        print("Chrome remote debugger is already running. Closing it to launch fresh in headless mode...")
        kill_chrome_on_port_9222()
        time.sleep(2)
        
    print("Launching Chrome in headless mode...")
    
    # Common Chrome executable paths on Windows
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
        # Check if it's on PATH
        import shutil
        chrome_path = shutil.which("chrome") or shutil.which("chrome.exe")
        
    if not chrome_path:
        print("Error: Could not locate chrome.exe on this system automatically.")
        return False
        
    cmd = [
        chrome_path,
        "--remote-debugging-port=9222",
        f"--user-data-dir={CHROME_PROFILE_PATH}",
        "--headless=new",
        "--disable-gpu"
    ]
    
    print(f"Launching Chrome: {' '.join(cmd)}")
    try:
        # Start Chrome detached in the background
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Wait a few seconds for Chrome to spin up and bind the port
        if target_board_opener:
                        target_board_opener.scroll_into_view_if_needed()
                        time.sleep(1.5)
                        target_board_opener.click()
                        time.sleep(4) # Delay for dropdown animation
                        
                        search_box = page.locator(
                             '[role="listbox"] input, '
                             '[class*="dropdown"] input, '
                             '[data-testid="board-dropdown"] input, '
                             '[data-test-id="board-dropdown"] input'
                         ).first
                        if search_box.count() > 0 and search_box.is_visible():
                            search_box.click()
                            time.sleep(1.5)
                            search_box.fill(BOARD_NAME)
                            time.sleep(3)
                            
                        # Try board selection up to 3 times (Pinterest dropdown can be flaky)
                        board_selected = False
                        for _attempt in range(3):
                            board_item = page.locator(
                                f'div[role="listitem"] div:has-text("{BOARD_NAME}"), '
                                f'div[role="option"]:has-text("{BOARD_NAME}"), '
                                f'div[role="option"] span:has-text("{BOARD_NAME}"), '
                                f'[data-test-id*="board"]:has-text("{BOARD_NAME}")'
                            ).first
                            if board_item.count() > 0:
                                try:
                                    board_item.wait_for(state="visible", timeout=5000)
                                    board_item.click()
                                    print(f"Board '{BOARD_NAME}' select ho gaya! (attempt {_attempt+1})")
                                    board_selected = True
                                    time.sleep(3)
                                    break
                                except Exception:
                                    pass
                            time.sleep(2)
                        if not board_selected:
                            print(f"Board '{BOARD_NAME}' dropdown mein nahi mila. Default board use hoga.")
                            page.keyboard.press("Escape")
                            time.sleep(2)
        for _ in range(8):
            time.sleep(1)
            if check_port_open(9222):
                print("Chrome started and listening on port 9222 successfully!")
                return True
        print("Warning: Chrome launched but port 9222 is still not responsive.")
        print("Hint: If normal Google Chrome is already running, close all its windows completely (or end it from Task Manager) and run the script again so it can open in debugging mode.")
        return False
    except Exception as e:
        print(f"Failed to launch Chrome subprocess: {e}")
        return False

def fallback_json_parser(raw_json):
    """
    Standard json.loads fails if Gemini generates unescaped double quotes inside strings.
    This fallback uses regex and substring slicing to extract the fields.
    """
    try:
        keys = ["title", "excerpt", "metaDescription", "seoKeywords", "content"]
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
                    
            if key == "seoKeywords":
                if val_str.startswith("["):
                    val_str = val_str[1:]
                if val_str.endswith("]"):
                    val_str = val_str[:-1]
                items = []
                for item in re.split(r',', val_str):
                    item = item.strip().strip('"\'')
                    if item:
                        items.append(item)
                data[key] = items
            else:
                if val_str.startswith('"'):
                    val_str = val_str[1:]
                if val_str.endswith('"'):
                    val_str = val_str[:-1]
                    
                val_str = val_str.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
                data[key] = val_str
                
        if "title" in data and "content" in data:
            return data
    except Exception as e:
        print(f"Fallback regex parser failed: {e}")
    return None

def generate_blog_content_via_playwright(trend_keyword):
    """Playwright का उपयोग करके localhost:9222 पर चल रहे Chrome के ज़रिए विशिष्ट Gemini Chat से फ़्री ब्लॉग पोस्ट लिखवाता है"""
    
    # Ensure Chrome is running on port 9222
    launched = launch_chrome_if_needed()
    if not launched:
        print("Error: Could not connect to Chrome because it could not be started.")
        return None
        
    print(f"Connecting to running Chrome on port 9222 for trend: {trend_keyword}...")
    
    # -----------------------------------------------------------------------
    # CORRECT SEO STRATEGY:
    # Target keyword = what creators actually Google (high volume)
    # Trending topic = just the content HOOK/ANGLE inside the article
    # -----------------------------------------------------------------------
    prompt = f"""You are an expert SEO content writer. Your goal is to write a blog post that ranks on Google.

The product is QuizViral AI: a tool that lets content creators generate 100+ viral faceless trivia/quiz videos in 1 click by importing a CSV file. It auto-generates voiceovers (TTS), adds ticking clock sounds, shows 4 answer options with a reveal animation, and supports Minecraft, Space, Nature background videos for YouTube Shorts, TikTok, Instagram Reels, and Facebook Reels.

Today's trending news topic: "{trend_keyword}"

---

YOUR TASK:
Write an SEO blog post that targets ONE of the following HIGH-VOLUME keywords that real content creators actually type into Google:

KEYWORD POOL (pick the ONE that fits best with "{trend_keyword}"):
- "how to make quiz videos for youtube"
- "how to start a faceless youtube channel in 2025"
- "best quiz video maker free"
- "viral youtube shorts ideas 2025"
- "how to make money with a faceless youtube channel"
- "how to make 100 youtube shorts fast"
- "faceless youtube channel ideas that make money"
- "how to automate youtube shorts"
- "best ai video generator for youtube"
- "tiktok quiz ideas that go viral"
- "how to grow youtube channel fast 2025"
- "youtube quiz channel monetization strategy"

HOW TO USE THE TRENDING TOPIC "{trend_keyword}":
- Use it as a REAL EXAMPLE inside the article
- e.g. "For example, right now '{trend_keyword}' is trending — here is how you can make a quiz video about it in minutes using QuizViral AI..."
- Do NOT make it the main keyword. It is just a timely hook to make the article feel fresh.

STRUCTURE REQUIREMENTS:
- Title: Must include the chosen high-volume keyword EXACTLY (60-70 chars)
- Introduction: Hook + why this topic matters for creators right now (mention "{trend_keyword}" as a current example)
- At least 5 H2 sections covering the main keyword topic in depth
- A practical step-by-step section showing how QuizViral AI solves the problem
- 10 real example quiz questions about "{trend_keyword}" (shows the tool in action)
- A monetization/income section (creators love this)
- 2 FAQ blocks at the end (helps get Google featured snippets)
- Include 2 links to https://quizviral-nine.vercel.app
- Minimum 1,500 words total

CRITICAL JSON FORMATTING RULES:
1. Inside JSON string values, do NOT use double quotes ("). Use single quotes (') instead.
2. Double quotes ONLY for JSON property names and to wrap top-level string values.
3. JSON must be 100% valid.
4. The 'title' must contain the chosen high-volume keyword exactly.
5. The 'seoKeywords' must have 8-10 long-tail keywords that real users actually search.

Respond ONLY with this JSON (no markdown code blocks):
{{
  "title": "Title containing the chosen high-volume keyword (60-70 chars)",
  "excerpt": "2-3 sentence summary using the main keyword naturally + mention of {trend_keyword} as a timely hook",
  "metaDescription": "Under 155 chars, includes main keyword, compelling CTA",
  "seoKeywords": ["how to make quiz videos for youtube", "faceless youtube channel 2025", "viral quiz video maker", "youtube shorts automation", "how to make money faceless youtube", "best ai quiz video generator", "quiz video ideas 2025", "QuizViral AI"],
  "content": "Full 1500+ word Markdown blog post. Start with # [Title]. Use H2/H3 headings, include 10 quiz questions about {trend_keyword}, step-by-step QuizViral AI tutorial, monetization tips, 2 FAQ blocks, 2 links to https://quizviral-nine.vercel.app"
}}
"""



    with sync_playwright() as p:
        try:
            # Port 9222 पर चल रहे Chrome से कनेक्ट करें
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
        except Exception as e:
            print(f"Failed to connect to Chrome on port 9222: {e}")
            return None

        # डिफ़ॉल्ट कांटेक्स्ट का उपयोग करें
        context = browser.contexts[0]
        # विशिष्ट Gemini Chat URL पर जाएं
        page = context.new_page()
        page.goto("https://gemini.google.com/app/5d22a66bd735a3fe")
        time.sleep(5)

        print("Typing prompt into Gemini...")
        textbox = page.locator("div[role='textbox']")
        textbox.click()
        textbox.fill(prompt)
        time.sleep(1)

        print("Submitting prompt...")
        # Send बटन क्लिक करें
        submit_btn = page.locator("button[aria-label*='Send' i], button[aria-label*='Submit' i], button[aria-label*='भेजें' i], button[class*='send-button']").first
        submit_btn.click()

        print("Waiting for Gemini to finish generating (until the mic button icon reappears)...")
        time.sleep(3)  # Give it a moment to transition to thinking/stop state

        # Locators to detect when Gemini goes back to the ready state (has mic button)
        mic_locator = page.locator("button[aria-label*='microphone' i], button[aria-label*='mic' i], button[aria-label*='माइक्रो' i]")
        stop_locator = page.locator("button[aria-label*='Stop' i], button[aria-label*='रोकें' i]")
        
        start_time = time.time()
        max_wait_seconds = 180  # 3 minutes max
        generation_done = False
        last_text = ""

        while time.time() - start_time < max_wait_seconds:
            # Check if mic button is visible
            is_mic_visible = False
            if mic_locator.count() > 0:
                for i in range(mic_locator.count()):
                    if mic_locator.nth(i).is_visible():
                        is_mic_visible = True
                        break

            # Check if stop button is visible (Gemini is still generating)
            is_stop_visible = False
            if stop_locator.count() > 0:
                for i in range(stop_locator.count()):
                    if stop_locator.nth(i).is_visible():
                        is_stop_visible = True
                        break

            print(f"Waiting for Gemini... (Mic visible: {is_mic_visible}, Stop visible: {is_stop_visible})")

            # If mic button is visible and stop button is NOT visible, we are done
            if is_mic_visible and not is_stop_visible:
                print("Gemini response is ready (Mic button is back and Stop button is gone)!")
                generation_done = True
                break

            time.sleep(2)

        # Fallback text stability check if mic detection timed out
        if not generation_done:
            print("Warning: Timed out waiting for mic button state. Using stable text fallback...")
            for _ in range(15):
                time.sleep(2)
                responses = page.locator(".model-response, .message-content, message-content")
                if responses.count() > 0:
                    current_text = responses.last.inner_text()
                    if current_text == last_text and len(current_text) > 100:
                        break
                    last_text = current_text

        # Fetch the final response text
        responses = page.locator(".model-response, .message-content, message-content")
        if responses.count() > 0:
            final_response = responses.last.inner_text()
        else:
            final_response = last_text

        print("Successfully read Gemini response.")
        page.close()
        browser.close()

        # JSON ढूँढें
        json_match = re.search(r"\{.*\}", final_response, re.DOTALL)
        if json_match:
            raw_json = json_match.group(0).strip()
            raw_json = raw_json.replace("{trend_keyword}", trend_keyword)
            try:
                return json.loads(raw_json)
            except Exception as e:
                print(f"Standard JSON parser failed: {e}. Trying custom regex fallback...")
                parsed_data = fallback_json_parser(raw_json)
                if parsed_data:
                    return parsed_data
                print(f"Error parsing JSON from Gemini response: {e}")
                print(f"Raw response was: {final_response}")
                return None
        else:
            print("No JSON block found in the response.")
            print(f"Raw response was: {final_response}")
            return None

def update_blog_posts_file(new_post):
    """Generated ब्लॉग को frontend/src/data/blogPosts.js में ऑटोमैटिक जोड़ता है"""
    print(f"Adding new blog post to {BLOG_POSTS_FILE}...")
    with open(BLOG_POSTS_FILE, "r", encoding="utf-8") as f:
        file_content = f.read()
    
    match = re.search(r"export const blogPosts = \[(.*)\];\s*$", file_content, re.DOTALL)
    if not match:
        print("Could not parse blogPosts.js file structure.")
        return False
        
    posts_array_content = match.group(1).strip()
    
    new_post_str = json.dumps(new_post, indent=2)
    new_post_str = new_post_str.replace('"slug":', 'slug:')
    new_post_str = new_post_str.replace('"title":', 'title:')
    new_post_str = new_post_str.replace('"excerpt":', 'excerpt:')
    new_post_str = new_post_str.replace('"date":', 'date:')
    new_post_str = new_post_str.replace('"readTime":', 'readTime:')
    new_post_str = new_post_str.replace('"author":', 'author:')
    new_post_str = new_post_str.replace('"image":', 'image:')
    new_post_str = new_post_str.replace('"metaDescription":', 'metaDescription:')
    new_post_str = new_post_str.replace('"seoKeywords":', 'seoKeywords:')
    new_post_str = new_post_str.replace('"content":', 'content:')

    if posts_array_content:
        updated_array = new_post_str + ",\n  " + posts_array_content
    else:
        updated_array = new_post_str
        
    updated_file_content = f"export const blogPosts = [\n  {updated_array}\n];\n"
    
    with open(BLOG_POSTS_FILE, "w", encoding="utf-8") as f:
        f.write(updated_file_content)
    print("blogPosts.js updated successfully!")
    return True

def git_push_changes(title):
    """Git commit & push automatic runs to trigger Vercel deployment"""
    print("Staging and pushing changes to GitHub...")
    try:
        subprocess.run(["git", "add", "."], cwd=SCRIPT_DIR, check=True)
        subprocess.run(["git", "commit", "-m", f"chore(blog): auto-publish post about {title}"], cwd=SCRIPT_DIR, check=True)
        subprocess.run(["git", "push", "github", "main"], cwd=SCRIPT_DIR, check=True)
        subprocess.run(["git", "push", "github", "main:master"], cwd=SCRIPT_DIR, check=True)
        print("Git Push Completed! Vercel build triggered.")
    except Exception as e:
        print(f"Git push failed: {e}")

def update_sitemap(slug):
    """Automatically adds the new blog post URL to frontend/public/sitemap.xml for SEO indexing"""
    sitemap_path = os.path.join(SCRIPT_DIR, "frontend", "public", "sitemap.xml")
    if not os.path.exists(sitemap_path):
        print(f"Sitemap file not found at {sitemap_path}")
        return False
        
    print(f"Updating sitemap.xml with slug: {slug}...")
    today_str = datetime.now().strftime("%Y-%m-%d")
    new_url = f"https://quizviral-nine.vercel.app/blog/{slug}"
    
    try:
        with open(sitemap_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        if new_url in content:
            print("URL already exists in sitemap.xml. Skipping...")
            return True
            
        new_entry = f"""  <url>
    <loc>{new_url}</loc>
    <lastmod>{today_str}</lastmod>
    <priority>0.8</priority>
  </url>
"""
        
        # Insert right before </urlset>
        if "</urlset>" in content:
            updated_content = content.replace("</urlset>", new_entry + "</urlset>")
            with open(sitemap_path, "w", encoding="utf-8") as f:
                f.write(updated_content)
            print("sitemap.xml updated successfully!")
            return True
        else:
            print("Could not find </urlset> tag in sitemap.xml.")
            return False
    except Exception as e:
        print(f"Failed to update sitemap.xml: {e}")
        return False

def ping_indexnow(slug):
    """Pings IndexNow API to request instant crawling of the new blog URL on Bing/Yahoo/Yandex"""
    import urllib.request
    import urllib.parse
    import ssl
    
    url_to_index = f"https://quizviral-nine.vercel.app/blog/{slug}"
    key = "86b7a1114fbd4f80a501b0dbc2731be3"
    key_location = f"https://quizviral-nine.vercel.app/{key}.txt"
    
    # Build request parameters
    params = {
        "url": url_to_index,
        "key": key,
        "keyLocation": key_location
    }
    encoded_params = urllib.parse.urlencode(params)
    ping_url = f"https://api.indexnow.org/indexnow?{encoded_params}"
    
    print(f"Pinging IndexNow for instant indexing of: {url_to_index}...")
    try:
        context = ssl._create_unverified_context()
        req = urllib.request.Request(ping_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10, context=context) as response:
            status = response.getcode()
            if status == 200:
                print("IndexNow ping successful! Search engines notified.")
                return True
            else:
                print(f"IndexNow ping returned status: {status}")
    except Exception as e:
        print(f"Failed to ping IndexNow: {e}")
    return False

def kill_chrome_on_port_9222():
    """Finds and terminates the Chrome process listening on remote debugging port 9222 on Windows"""
    import subprocess
    print("Attempting to close Chrome remote debugging browser on port 9222...")
    try:
        # Run netstat to find the process ID listening on port 9222
        output = subprocess.check_output("netstat -aon", shell=True).decode('utf-8', errors='ignore')
        for line in output.splitlines():
            if ":9222" in line and "LISTENING" in line:
                # Extract the PID (last token in the line)
                parts = line.strip().split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    print(f"Found Chrome debugger process with PID {pid} listening on port 9222. Terminating...")
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return True
    except Exception as e:
        print(f"Error terminating Chrome process on port 9222: {e}")
    return False

def main():
    try:
        # Parse trend index argument if provided
        trend_index = 0
        if "--trend-index" in sys.argv:
            try:
                idx = sys.argv.index("--trend-index")
                trend_index = int(sys.argv[idx + 1])
            except (ValueError, IndexError):
                pass

        # 1. Google Trends से कीवर्ड लें
        trend = get_trending_keyword(trend_index)
        
        # 2. Unsplash से 1200px इमेज लें
        image_url = get_unsplash_image(trend)
        
        # 3. Playwright से ब्लॉग लिखवाएं
        blog_data = generate_blog_content_via_playwright(trend)
        
        if not blog_data:
            print("Blog generation failed.")
            return
            
        # Metadata जोड़ें
        blog_data["slug"] = blog_data.get("title", trend).lower().replace(" ", "-").replace(":", "").replace("?", "").replace("&", "")
        blog_data["date"] = datetime.now().strftime("%B %d, %Y")
        blog_data["readTime"] = "5 min read"
        blog_data["author"] = "QuizViral AI Team"
        blog_data["image"] = image_url
        
        # 4. blogPosts.js में सेव करें
        success = update_blog_posts_file(blog_data)
        
        # 5. sitemap.xml me save karein aur IndexNow ping karein
        if success:
            update_sitemap(blog_data["slug"])
            ping_indexnow(blog_data["slug"])
        
        # 6. Build and Push
        if success:
            print("Running build verification...")
            build_res = subprocess.run(["npm", "run", "build"], cwd=os.path.join(SCRIPT_DIR, "frontend"), shell=True)
            if build_res.returncode == 0:
                git_push_changes(blog_data["title"])
                # 7. Pinterest Auto-Pin Syndication
                try:
                    from pinterest_auto_pin import run_pinterest_syndication
                    run_pinterest_syndication(blog_data)
                except Exception as e:
                    print(f"Pinterest syndication failed: {e}")
            else:
                print("Local build check failed! Aborting Git Push & Pinterest Pinning to avoid breaking production.")
    finally:
        # Always make sure the browser process is killed before exiting
        kill_chrome_on_port_9222()

if __name__ == "__main__":
    main()
