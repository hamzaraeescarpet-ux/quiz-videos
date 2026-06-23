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

# Set UTF-8 encoding for standard output and error to prevent CP1252 charmap crashes on Windows
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

# ==================== CONFIGURATION ====================
# आपके Chrome Profile का पाथ (लॉगिन सेशन बनाए रखने के लिए)
CHROME_PROFILE_PATH = r"C:\Users\hamza\Downloads\python development\browser automation\gemini video points\bulk scheduling fb videos\chrome_profile_2"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BLOG_POSTS_FILE = os.path.join(SCRIPT_DIR, "frontend", "src", "data", "blogPosts.js")
# ========================================================


# Topics to SKIP — US legal/medical ad-spend keywords that pollute trends
_SKIP_KEYWORDS = [
    "lawyer", "attorney", "lawsuit", "accident", "injury", "mesothelioma",
    "rehab", "treatment center", "drug rehab", "insurance", "settlement",
    "compensation", "mortgage", "loan", "credit", "debt", "bankruptcy",
    "addiction", "detox", "clinic", "hospital", "cancer", "disease",
    "symptoms", "diagnosis", "medicare", "medicaid", "tax relief",
    "car crash", "truck accident", "slip and fall", "personal injury",
    "class action", "malpractice", "dui", "divorce", "custody",
]

def _is_relevant_topic(topic):
    """Returns True if topic is relevant (pop culture, sports, tech, entertainment)."""
    topic_lower = topic.lower()
    # Skip if any spam keyword is in the topic
    for skip in _SKIP_KEYWORDS:
        if skip in topic_lower:
            return False
    # Skip very short or generic topics
    if len(topic.strip()) < 4:
        return False
    return True

def is_keyword_already_published(keyword):
    """Checks if a blog post matching this keyword already exists in blogPosts.js"""
    if not os.path.exists(BLOG_POSTS_FILE):
        return False
    try:
        with open(BLOG_POSTS_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Extract fields using regex
        titles = re.findall(r"title:\s*['\"`](.*?)['\"`]", content)
        slugs = re.findall(r"slug:\s*['\"`](.*?)['\"`]", content)
        trending_keywords = re.findall(r"trendingKeyword:\s*['\"`](.*?)['\"`]", content)
        
        keyword_lower = keyword.lower().strip()
        
        # 1. Direct check on trendingKeyword field
        for tk in trending_keywords:
            tk_lower = tk.lower().strip()
            if keyword_lower == tk_lower or keyword_lower in tk_lower or tk_lower in keyword_lower:
                return True
                
        # 2. Direct check on title and slug
        for t in titles:
            if keyword_lower in t.lower():
                return True
        for s in slugs:
            if keyword_lower.replace(" ", "-") in s.lower() or s.lower().replace("-", " ") in keyword_lower:
                return True
                
        # 3. Check inside seoKeywords arrays
        seo_blocks = re.findall(r"seoKeywords:\s*\[(.*?)\]", content, re.DOTALL)
        for block in seo_blocks:
            keywords_in_block = [k.strip().strip("'\"`").lower() for k in block.split(",") if k.strip()]
            for kw in keywords_in_block:
                if keyword_lower == kw or keyword_lower in kw or kw in keyword_lower:
                    # Avoid false positives on very common words
                    if len(keyword_lower) > 3 and keyword_lower not in ["quiz", "viral", "shorts", "youtube", "best", "free"]:
                        return True
                
        # 4. Word overlap check to avoid duplicate themes
        words = [w for w in re.split(r'\W+', keyword_lower) if len(w) > 3]
        if words:
            for t in titles:
                t_lower = t.lower()
                if all(w in t_lower for w in words):
                    return True
    except Exception as e:
        print(f"Error checking duplicate posts: {e}")
    return False



def get_trending_keyword(index=0):
    """
    Google Trends RSS Feed se trending keyword nikalta hai.
    Spam/irrelevant topics (lawyers, rehab etc) ko skip karta hai.
    Agar koi relevant topic nahi milta, creator-friendly fallback use karta hai.
    """
    print(f"Fetching trending keywords from Google Trends (want index ~{index})...")

    # Curated fallbacks if Google Trends gives only garbage
    CREATOR_FALLBACKS = [
        "viral YouTube Shorts ideas",
        "faceless YouTube channel tips",
        "how to grow on TikTok 2025",
        "best AI tools for content creators",
        "YouTube automation income",
        "trending quiz topics for YouTube",
        "viral trivia video ideas",
        "how to go viral on Instagram Reels",
    ]

    # Try both US and IN trends to get variety
    geo_list = ["US"]
    all_topics = []

    for geo in geo_list:
        url = f"https://trends.google.com/trending/rss?geo={geo}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
            root = ET.fromstring(xml_data)
            items = root.findall(".//item")
            for item in items:
                title_el = item.find("title")
                if title_el is not None and title_el.text:
                    all_topics.append(title_el.text.strip())
        except Exception as e:
            print(f"Google Trends ({geo}) fetch failed: {e}")

    # Filter relevant topics
    relevant = [t for t in all_topics if _is_relevant_topic(t)]
    print(f"Total trends fetched: {len(all_topics)}, Relevant after filtering: {len(relevant)}")

    if relevant:
        # Pick by index (mod to stay in bounds)
        picked = relevant[index % len(relevant)]
        print(f"Selected trending topic: '{picked}'")
        return picked

    # Nothing relevant — use creator-friendly fallback
    fallback = CREATOR_FALLBACKS[index % len(CREATOR_FALLBACKS)]
    print(f"No relevant trends found. Using creator fallback: '{fallback}'")
    return fallback



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
        "--disable-gpu",
        "--no-first-run",
        "--disable-default-apps",
        "--disable-session-crashed-bubble",
        "--hide-crash-restore-bubble",
    ]
    
    print(f"Launching Chrome: {' '.join(cmd)}")
    try:
        # Start Chrome detached in the background
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Wait for Chrome to spin up and bind the port
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
        keys = ["title", "excerpt", "metaDescription", "seoKeywords", "content", "outline"]
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
                
        if "title" in data:
            return data
    except Exception as e:
        print(f"Fallback regex parser failed: {e}")
    return None

def clean_markdown_response(text):
    """Clean up markdown response by removing leading/trailing code blocks or fluff."""
    text = text.strip()
    # Remove leading ```markdown or ```
    text = re.sub(r"^```markdown\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    # Remove trailing ```
    if text.endswith("```"):
        text = text[:-3].strip()
    return text

def wait_for_gemini_response(page, mic_locator, stop_locator, max_wait_seconds=180):
    """Wait for Gemini response to finish generating and return the response text."""
    start_time = time.time()
    generation_done = False
    last_text = ""

    while time.time() - start_time < max_wait_seconds:
        try:
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
                print("Gemini response is ready!")
                generation_done = True
                break

        except Exception as loop_err:
            err_name = type(loop_err).__name__
            print(f"Warning: {err_name} during wait loop — page may have navigated. Falling back to text check...")
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

    return final_response

def generate_blog_content_via_playwright(trend_keyword):
    """Playwright का उपयोग करके localhost:9222 पर चल रहे Chrome के ज़रie 2-Turn dialogue से फ़्री ब्लॉग पोस्ट लिखवाता है"""
    
    # Ensure Chrome is running on port 9222
    launched = launch_chrome_if_needed()
    if not launched:
        print("Error: Could not connect to Chrome because it could not be started.")
        return None
        
    print(f"Connecting to running Chrome on port 9222 for trend: {trend_keyword}...")
    
    # TURN 1 PROMPT: Metadata & Outline creation
    prompt_metadata = f"""You are an expert SEO content writer. Your goal is to plan a highly optimized blog post for "QuizViral AI".
Product details: QuizViral AI lets creators make 100+ viral faceless quiz/trivia videos in 1 click via CSV import. Features include TTS voiceovers, ticking clocks, answer reveal animations, and Minecraft/Space/Nature background videos.

Today's trending news topic: "{trend_keyword}"

YOUR TASK:
Step 1: Choose the single best SEO high-volume keyword from this keyword pool:
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

Step 2: Create a metadata block and a detailed article outline for this post.
The outline should use H2 headings, targeting the chosen SEO keyword. It should include sections covering the chosen keyword, a step-by-step tutorial of QuizViral AI, 10 quiz questions about "{trend_keyword}", a monetization strategies section, and FAQ ideas.

CRITICAL JSON FORMATTING RULES:
1. Inside JSON values, do NOT use double quotes ("). Use single quotes (') instead.
2. Double quotes ONLY for JSON property names and to wrap top-level values.
3. Respond ONLY with the JSON format (no markdown code blocks, no text before or after).

Format:
{{
  "title": "SEO Title containing the chosen high-volume keyword (60-70 chars)",
  "excerpt": "2-3 sentence summary using the main keyword naturally + mention of {trend_keyword} as a timely hook",
  "metaDescription": "Under 155 chars, includes main keyword, compelling CTA",
  "seoKeywords": ["keyword 1", "keyword 2", "keyword 3", "QuizViral AI"],
  "outline": "Detailed outline of the blog post structure with H2 and H3 headings"
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

        # -------------------------------------------------------------
        # TURN 1: Send Metadata Prompt & Receive JSON
        # -------------------------------------------------------------
        print("Typing metadata prompt into Gemini (Turn 1)...")
        textbox = page.locator("div[role='textbox']")
        textbox.click()
        textbox.fill(prompt_metadata)
        time.sleep(1)

        print("Submitting metadata prompt...")
        submit_btn = page.locator("button[aria-label*='Send' i], button[aria-label*='Submit' i], button[aria-label*='भेजें' i], button[class*='send-button']").first
        submit_btn.click()

        print("Waiting for Gemini to finish Turn 1...")
        time.sleep(3)
        mic_locator = page.locator("button[aria-label*='microphone' i], button[aria-label*='mic' i], button[aria-label*='माइक्रो' i]")
        stop_locator = page.locator("button[aria-label*='Stop' i], button[aria-label*='रोकें' i]")
        
        turn1_response = wait_for_gemini_response(page, mic_locator, stop_locator)
        print("Successfully read Turn 1 response.")

        # JSON ढूँढें
        meta_data = None
        json_match = re.search(r"\{.*\}", turn1_response, re.DOTALL)
        if json_match:
            raw_json = json_match.group(0).strip()
            raw_json = raw_json.replace("{trend_keyword}", trend_keyword)
            try:
                meta_data = json.loads(raw_json)
            except Exception as e:
                print(f"Standard JSON parser failed for Turn 1: {e}. Trying custom regex fallback...")
                meta_data = fallback_json_parser(raw_json)
        else:
            print("No JSON block found in Turn 1 response. Trying custom regex fallback...")
            meta_data = fallback_json_parser(turn1_response)

        if not meta_data or "title" not in meta_data:
            print("Error: Could not parse metadata or outline from Gemini Turn 1.")
            print(f"Raw response was: {turn1_response}")
            page.close()
            browser.close()
            kill_chrome_on_port_9222()
            return None

        # -------------------------------------------------------------
        # TURN 2: Send Content Prompt & Receive Pure Markdown
        # -------------------------------------------------------------
        outline = meta_data.get("outline", "Detailed blog sections")
        title = meta_data.get("title", "SEO Blog Post")
        
        prompt_content = f"""Excellent outline. Now, write the complete, extremely in-depth and high-quality blog post in Markdown format following that outline.

Outline to follow:
{outline}

REQUIREMENTS:
- Word Count: Minimum 1,500 words. Make the paragraphs highly informative, engaging, and detailed. No short fluffy paragraphs.
- Title: Start directly with '# {title}' at the very beginning of the article.
- Headings: Use proper H2 and H3 markdown tags.
- Example Section: Include 10 complete quiz questions about '{trend_keyword}' (with 4 multiple-choice options each and the correct answer indicated).
- Product Integration: Write a step-by-step guide on how content creators can make a quiz video about '{trend_keyword}' in 1 click using QuizViral AI.
- Links: Naturally include exactly 2 links to https://quizviral-nine.vercel.app in the article body (e.g. as '[QuizViral AI](https://quizviral-nine.vercel.app)').
- FAQs: Include 2 FAQs at the end.
- Formatting: Wrap the entire article (starting from the H1 title '# {title}' to the end) inside a single markdown code block (code fence). Do not write anything outside the code block. Start writing the post immediately.
"""

        print("Typing content prompt into Gemini (Turn 2)...")
        textbox.click()
        textbox.fill(prompt_content)
        time.sleep(1)

        print("Submitting content prompt...")
        submit_btn.click()

        print("Waiting for Gemini to finish Turn 2 (Writing full blog post)...")
        time.sleep(3)
        
        turn2_response = wait_for_gemini_response(page, mic_locator, stop_locator, max_wait_seconds=240)
        print("Successfully read Turn 2 response.")

        page.close()
        browser.close()
        kill_chrome_on_port_9222()

        # Clean markdown and attach to meta_data
        markdown_content = clean_markdown_response(turn2_response)
        
        # Replace template placeholders
        markdown_content = markdown_content.replace("{trend_keyword}", trend_keyword)
        markdown_content = markdown_content.replace("{title}", title)

        meta_data["content"] = markdown_content
        return meta_data

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
    new_post_str = new_post_str.replace('"trendingKeyword":', 'trendingKeyword:')
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

        # 1. Google Trends से कीवर्ड लें (Check for duplicate topics to prevent double posting)
        attempts = 0
        max_attempts = 15
        trend = None
        
        while attempts < max_attempts:
            candidate_trend = get_trending_keyword(trend_index + attempts)
            if not is_keyword_already_published(candidate_trend):
                trend = candidate_trend
                break
            else:
                print(f"Keyword '{candidate_trend}' has already been published in blogPosts.js. Trying next trend...")
                attempts += 1
                
        if not trend:
            trend = get_trending_keyword(trend_index)
            print(f"Warning: All fetched trends are already published. Defaulting to: '{trend}'")
        
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
        blog_data["trendingKeyword"] = trend
        
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
