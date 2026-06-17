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

def get_unsplash_image(keyword):
    """Wikipedia PageImages से मैचिंग इमेज खोजता है, फ़ेल होने पर Unsplash के HD फ़ॉलबैक का उपयोग करता है"""
    import ssl
    import json
    import urllib.parse
    import urllib.request
    
    # Try Wikipedia first for a highly relevant contextual image
    try:
        context = ssl._create_unverified_context()
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(keyword)}&utf8=&format=json&srlimit=1"
        req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
        with urllib.request.urlopen(req, timeout=10, context=context) as response:
            search_data = json.loads(response.read().decode('utf-8'))
            search_results = search_data.get("query", {}).get("search", [])
            if search_results:
                best_title = search_results[0]["title"]
                
                image_url_api = f"https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&piprop=thumbnail&pithumbsize=1280&titles={urllib.parse.quote(best_title)}&redirects=1"
                req2 = urllib.request.Request(image_url_api, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
                with urllib.request.urlopen(req2, timeout=10, context=context) as response2:
                    img_data = json.loads(response2.read().decode('utf-8'))
                    pages = img_data.get("query", {}).get("pages", {})
                    for page_id, page_data in pages.items():
                        if "thumbnail" in page_data:
                            wiki_img = page_data["thumbnail"]["source"]
                            print(f"Wikipedia Image Found for {keyword}: {wiki_img}")
                            return wiki_img
    except Exception as e:
        print(f"Wikipedia image fetch failed: {e}. Using Unsplash fallback.")

    # Unsplash Fallback
    image_url = "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?auto=format&fit=crop&w=1200&q=80"
    if "game" in keyword.lower() or "sports" in keyword.lower():
        image_url = "https://images.unsplash.com/photo-1486427944299-d1955d23e317?auto=format&fit=crop&w=1200&q=80"
    elif "movie" in keyword.lower() or "show" in keyword.lower() or "star" in keyword.lower():
        image_url = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=1200&q=80"
    elif "tech" in keyword.lower() or "ai" in keyword.lower() or "google" in keyword.lower():
        image_url = "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80"
    return image_url

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
        print("Chrome is already running with remote debugging on port 9222.")
        return True
        
    print("Chrome is not running on port 9222. Attempting to launch it automatically...")
    
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
        f"--user-data-dir={CHROME_PROFILE_PATH}"
    ]
    
    print(f"Launching Chrome: {' '.join(cmd)}")
    try:
        # Start Chrome detached in the background
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Wait a few seconds for Chrome to spin up and bind the port
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
    
    prompt = f"""
Write a detailed, professional blog post in Markdown format connecting the today's trending topic "{trend_keyword}" with our product "QuizViral AI".

QuizViral AI is a tool that allows creators to create 100+ viral faceless quiz/trivia videos in just 1-click by importing a CSV file. It automates voiceovers, adds ticking clock sounds, and center-crops background videos (like Minecraft or Space) for TikTok, YouTube Shorts, and Reels.

Explain how creators can capitalize on this trending topic "{trend_keyword}" by making interactive trivia/quiz videos using QuizViral AI and how they can monetize it to get massive views.

You MUST respond ONLY with a JSON object. Do not wrap it in markdown code blocks like ```json.

CRITICAL JSON FORMATTING RULES:
1. Inside the JSON string values (especially the 'content', 'excerpt', and 'title' keys), do NOT use double quotes ("). If you want to quote anything (e.g. 'Which President nominated...' or 'QuizViral AI'), you MUST use single quotes (') instead.
2. Double quotes (") must ONLY be used as JSON property names and to wrap string values.
3. Ensure the JSON is 100% valid.

JSON format:
{{
  "title": "SEO-optimized title connecting {trend_keyword} and QuizViral AI",
  "excerpt": "A short 1-2 sentence summary of the article",
  "metaDescription": "A 150-character SEO description",
  "seoKeywords": ["{trend_keyword} trivia", "QuizViral AI", "faceless channel", "viral quiz"],
  "content": "Markdown content here starting with '# Title'. Include H2 subheadings, bullet points, and at least two links to https://quizviral-nine.vercel.app."
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
        submit_btn = page.locator("button[aria-label*='Send'], button[aria-label*='Submit'], button[class*='send-button']").first
        submit_btn.click()

        print("Waiting for Gemini to generate the response...")
        time.sleep(15)

        # जब तक रिस्पॉन्स आना बंद न हो जाए (Stable state), वेट करें
        last_text = ""
        stable_count = 0
        for _ in range(30): # अधिकतम 30 सेकंड और वेट करें
            time.sleep(2)
            responses = page.locator(".model-response, .message-content, message-content")
            if responses.count() > 0:
                current_text = responses.last.inner_text()
                if current_text == last_text and len(current_text) > 100:
                    stable_count += 1
                    if stable_count >= 3:
                        break
                else:
                    stable_count = 0
                last_text = current_text

        final_response = last_text
        page.close() # केवल हमारे द्वारा खोले गए पेज को बंद करें, पूरे ब्राउज़र को नहीं

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

def main():
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
    
    # 5. Build and Push
    if success:
        print("Running build verification...")
        build_res = subprocess.run(["npm", "run", "build"], cwd=os.path.join(SCRIPT_DIR, "frontend"), shell=True)
        if build_res.returncode == 0:
            git_push_changes(blog_data["title"])
        else:
            print("Local build check failed! Aborting Git Push to avoid breaking production.")

if __name__ == "__main__":
    main()
