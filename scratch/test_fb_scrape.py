import os
import sys
import time
import json
import re
from playwright.sync_api import sync_playwright

def check_port_open(port):
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except Exception:
        return False

def get_latest_fb_video():
    if not check_port_open(9222):
        print("Chrome on port 9222 is not running.")
        return None

    print("Connecting to Chrome on port 9222...")
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.new_page()
            
            # Go to FB Page
            url = "https://www.facebook.com/profile.php?id=61585764748589"
            print(f"Navigating to {url}...")
            page.goto(url)
            time.sleep(5)
            
            # Scroll to load more content
            page.evaluate("window.scrollBy(0, 1000);")
            time.sleep(4)
            
            # Get script tag contents
            scripts = page.locator("script").evaluate_all("elements => elements.map(el => el.textContent || '')")
            
            video_ids = []
            reel_ids = []
            
            # Search for video and reel IDs using regex
            for script in scripts:
                if not script:
                    continue
                # video_id pattern
                for m in re.finditer(r'"video_id"\s*:\s*"(\d+)"', script):
                    video_ids.append(m.group(1))
                # video id pattern inside typenames
                for m in re.finditer(r'"video":\{"__typename":"Video","id":"(\d+)"', script):
                    video_ids.append(m.group(1))
                # reel_id pattern
                for m in re.finditer(r'"reel":\{"id":"(\d+)"', script):
                    reel_ids.append(m.group(1))
                # reel url pattern
                for m in re.finditer(r'facebook\.com/reel/(\d+)', script):
                    reel_ids.append(m.group(1))
            
            # Unique lists
            video_ids = list(dict.fromkeys(video_ids))
            reel_ids = list(dict.fromkeys(reel_ids))
            
            print(f"Found Video IDs in scripts: {video_ids}")
            print(f"Found Reel IDs in scripts: {reel_ids}")
            
            page.close()
            browser.close()
            
            # Form URLs
            urls = []
            for r_id in reel_ids:
                urls.append(f"https://www.facebook.com/reel/{r_id}")
            for v_id in video_ids:
                urls.append(f"https://www.facebook.com/watch/?v={v_id}")
                
            print(f"Constructed URLs: {urls}")
            if urls:
                return urls[0]
        except Exception as e:
            print(f"Error during scrape: {e}")
        return None

if __name__ == "__main__":
    latest = get_latest_fb_video()
    print(f"RESULT: {latest}")
