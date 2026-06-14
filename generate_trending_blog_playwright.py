import os
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

BLOG_POSTS_FILE = os.path.join("frontend", "src", "data", "blogPosts.js")
# ========================================================

def get_trending_keyword():
    """Google Trends RSS Feed से आज का सबसे टॉप ट्रेंडिंग कीवर्ड निकालता है (100% फ़्री)"""
    print("Fetching trending keywords from Google Trends...")
    url = "https://trends.google.com/trending/rss?geo=US"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
        
        root = ET.fromstring(xml_data)
        first_item = root.find(".//item")
        title = first_item.find("title").text
        print(f"Top trending topic found: {title}")
        return title
    except Exception as e:
        print(f"Error fetching trends: {e}. Falling back to default keyword.")
        return "TikTok Quiz Videos"

def get_unsplash_image(keyword):
    """Unsplash से टॉपिक से मैचिंग 1200px की हाई-क्वालिटी फ़्री इमेज खोजता है"""
    image_url = "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?auto=format&fit=crop&w=1200&q=80"
    if "game" in keyword.lower() or "sports" in keyword.lower():
        image_url = "https://images.unsplash.com/photo-1486427944299-d1955d23e317?auto=format&fit=crop&w=1200&q=80"
    elif "movie" in keyword.lower() or "show" in keyword.lower() or "star" in keyword.lower():
        image_url = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=1200&q=80"
    elif "tech" in keyword.lower() or "ai" in keyword.lower() or "google" in keyword.lower():
        image_url = "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80"
    return image_url

def generate_blog_content_via_playwright(trend_keyword):
    """Playwright का उपयोग करके localhost:9222 पर चल रहे Chrome के ज़रिए विशिष्ट Gemini Chat से फ़्री ब्लॉग पोस्ट लिखवाता है"""
    print(f"Connecting to running Chrome on port 9222 for trend: {trend_keyword}...")
    
    prompt = f"""
Write a detailed, professional blog post in Markdown format connecting the today's trending topic "{trend_keyword}" with our product "QuizViral AI".

QuizViral AI is a tool that allows creators to create 100+ viral faceless quiz/trivia videos in just 1-click by importing a CSV file. It automates voiceovers, adds ticking clock sounds, and center-crops background videos (like Minecraft or Space) for TikTok, YouTube Shorts, and Reels.

Explain how creators can capitalize on this trending topic "{trend_keyword}" by making interactive trivia/quiz videos using QuizViral AI and how they can monetize it to get massive views.

You MUST respond ONLY with a JSON object. Do not wrap it in markdown code blocks like ```json.
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
            print("कृपया सुनिश्चित करें कि आपने Chrome को इस कमांड से खोला है:")
            print(rf'chrome.exe --remote-debugging-port=9222 --user-data-dir="{CHROME_PROFILE_PATH}"')
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
            try:
                # Replace the exact placeholder string if Gemini forgot to replace it
                raw_json = json_match.group(0).strip()
                raw_json = raw_json.replace("{trend_keyword}", trend_keyword)
                return json.loads(raw_json)
            except Exception as e:
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
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", f"chore(blog): auto-publish post about {title}"], check=True)
        subprocess.run(["git", "push", "github", "main"], check=True)
        subprocess.run(["git", "push", "github", "main:master"], check=True)
        print("Git Push Completed! Vercel build triggered.")
    except Exception as e:
        print(f"Git push failed: {e}")

def main():
    # 1. Google Trends से कीवर्ड लें
    trend = get_trending_keyword()
    
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
        build_res = subprocess.run(["npm", "run", "build"], cwd="frontend", shell=True)
        if build_res.returncode == 0:
            git_push_changes(blog_data["title"])
        else:
            print("Local build check failed! Aborting Git Push to avoid breaking production.")

if __name__ == "__main__":
    main()
