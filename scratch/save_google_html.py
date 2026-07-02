import os
import sys
import time
from playwright.sync_api import sync_playwright

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME_PROFILE_PATH = r"C:\Users\hamza\Downloads\python development\browser automation\gemini video points\bulk scheduling fb videos\chrome_profile_2"

sys.path.append(SCRIPT_DIR)
from generate_trending_blog_playwright import launch_chrome_if_needed, kill_chrome_on_port_9222

def save_html():
    launch_chrome_if_needed()
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.new_page()
            
            print("Navigating to Google Search...")
            page.goto("https://www.google.com/search?q=July+4th+Trivia")
            time.sleep(5)
            
            html_content = page.content()
            
            # Save HTML
            out_path = os.path.join(SCRIPT_DIR, "scratch", "google_search.html")
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(html_content)
                
            print(f"HTML saved to {out_path}")
            
            # Let's do a quick scan of text containing question marks
            print("\nSearching text nodes with '?'...")
            spans = page.locator("span, div").evaluate_all(
                "elements => elements.map(el => el.innerText).filter(t => t && t.includes('?') && t.length > 10 && t.length < 150)"
            )
            print("Found potential questions:", list(set(spans))[:10])
            
            # Let's scan all anchors with /search?q=
            print("\nSearching search links...")
            links = page.locator("a").evaluate_all(
                "elements => elements.map(el => ({text: el.innerText, href: el.getAttribute('href')})).filter(o => o.href && o.href.includes('/search') && o.text && o.text.trim().length > 3)"
            )
            print("Found potential search links:", links[:15])
            
            page.close()
            browser.close()
        except Exception as e:
            print(f"Error: {e}")
        finally:
            kill_chrome_on_port_9222()

if __name__ == "__main__":
    save_html()
