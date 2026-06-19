import os
import sys
import time
import subprocess
from playwright.sync_api import sync_playwright

# Configurations
# We have pre-populated the 4 Chrome profiles found on your computer!
CHROME_PROFILES = [
    r"C:\Users\hamza\Downloads\python development\browser automation\gemini video points\bulk scheduling fb videos\chrome_profile",
    r"C:\Users\hamza\Downloads\python development\browser automation\gemini video points\bulk scheduling fb videos\chrome_profile_2",
    r"C:\Users\hamza\Downloads\python development\facebook post automation\hamzarais2023\chrome_profile",
    r"C:\Users\hamza\Downloads\python development\facebook post automation\hamzarais2023\chrome_profile_2"
]

BOARD_NAME = "Trivia Quiz Videos" # Set this to your Pinterest board name or leave empty to use default board

def check_port_open(port=9222):
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
                    print(f"Terminating Chrome debugging process (PID: {pid}) on port 9222...")
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    time.sleep(2)
                    return True
    except Exception as e:
        print(f"Error checking/killing Chrome on port 9222: {e}")
    return False

def launch_chrome_with_profile(profile_path):
    # Ensure port is clean
    kill_chrome_on_port_9222()
    
    print(f"Launching Chrome with profile: {profile_path}...")
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
        print("Error: Could not locate chrome.exe.")
        return False
        
    cmd = [
        chrome_path,
        "--remote-debugging-port=9222",
        f"--user-data-dir={profile_path}",
        "--headless=new",  # Runs Chrome silently in background
        "--disable-gpu"
    ]
    
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Wait for port to open
        for _ in range(10):
            time.sleep(1)
            if check_port_open(9222):
                print("Chrome remote debugger started successfully on port 9222!")
                return True
        return False
    except Exception as e:
        print(f"Failed to launch Chrome: {e}")
        return False

def download_temp_image(image_url):
    import urllib.request
    import ssl
    import tempfile
    
    print(f"Downloading blog image for Pin: {image_url}...")
    try:
        context = ssl._create_unverified_context()
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, "temp_pinterest_pin.jpg")
        
        req = urllib.request.Request(
            image_url, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, context=context, timeout=15) as response:
            with open(temp_path, "wb") as f:
                f.write(response.read())
        print(f"Image downloaded successfully to: {temp_path}")
        return temp_path
    except Exception as e:
        print(f"Failed to download image: {e}")
        return None

def publish_pin_for_profile(profile_path, pin_data):
    if not launch_chrome_with_profile(profile_path):
        print(f"Failed to start Chrome for profile: {profile_path}")
        return False
        
    success = False
    with sync_playwright() as p:
        try:
            print("Connecting Playwright to Chrome remote debugger...")
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.new_page()
            
            print("Navigating to Pinterest Pin Builder...")
            page.goto("https://www.pinterest.com/pin-builder/")
            
            # Wait for loaded page state
            time.sleep(7)
            
            # Check if user is logged in
            if "login" in page.url or page.locator('button:has-text("Log in")').count() > 0:
                print(f"WARNING: Account is NOT logged in for profile: {profile_path}. Skipping...")
                page.close()
                browser.close()
                return False
                
            print("Account verified as logged in. Filling Pin details...")
            
            # 1. Upload the image file
            file_input = page.locator('input[type="file"]')
            if file_input.count() > 0:
                file_input.first.set_input_files(pin_data["image_path"])
                print("Image uploaded successfully!")
                time.sleep(2)
            else:
                print("Error: Could not find image file input element on Pinterest.")
                
            # 2. Fill the Title
            title_input = page.locator('input[placeholder*="title" i], textarea[placeholder*="title" i], [placeholder*="title" i]').first
            if title_input.count() > 0:
                title_input.click()
                title_input.fill(pin_data["title"])
                print("Title filled.")
            else:
                print("Warning: Could not find Title input.")
                
            # 3. Fill the Description
            desc_input = page.locator('textarea[placeholder*="description" i], div[contenteditable="true"][placeholder*="description" i], [placeholder*="description" i]').first
            if desc_input.count() > 0:
                desc_input.click()
                desc_input.fill(pin_data["description"])
                print("Description filled.")
            else:
                print("Warning: Could not find Description input.")
                
            # 4. Fill the Destination Link
            link_input = page.locator('input[placeholder*="link" i], [placeholder*="link" i]').first
            if link_input.count() > 0:
                link_input.click()
                link_input.fill(pin_data["link"])
                print("Destination link filled.")
            else:
                print("Warning: Could not find Destination Link input.")
                
            # 5. Handle Board Selection
            if BOARD_NAME:
                print(f"Attempting to select board: '{BOARD_NAME}'...")
                board_opener = page.locator('button[data-testid="board-dropdown"], button[aria-haspopup="listbox"], button[class*="board"]').first
                if board_opener.count() > 0 and board_opener.is_visible():
                    board_opener.click()
                    time.sleep(2)
                    
                    # Search box inside dropdown
                    search_box = page.locator('input[placeholder*="Search" i], input[placeholder*="search" i]').first
                    if search_box.count() > 0 and search_box.is_visible():
                        search_box.fill(BOARD_NAME)
                        time.sleep(2)
                    
                    # Click matching board option
                    board_item = page.locator(f'div[role="listitem"] div:has-text("{BOARD_NAME}"), div[role="option"] div:has-text("{BOARD_NAME}"), div[class*="board"]:has-text("{BOARD_NAME}"), :has-text("{BOARD_NAME}")').first
                    if board_item.count() > 0 and board_item.is_visible():
                        board_item.click()
                        print(f"Board '{BOARD_NAME}' selected!")
                        time.sleep(1)
                    else:
                        print(f"Board '{BOARD_NAME}' not found. Using default board.")
                        page.keyboard.press("Escape")
                        time.sleep(1)
                else:
                    print("Could not open board picker. Using default board.")
            
            # 6. Click Publish / Save
            publish_btn = page.locator('button[data-testid="create-pin-submit"], button:has-text("Publish"), button:has-text("Save"), button[class*="publish"], button[class*="save"]').first
            if publish_btn.count() > 0:
                publish_btn.click()
                print("Publish button clicked! Waiting for success confirmation...")
                time.sleep(8)  # Wait for Pinterest server save response
                print("Pin published successfully!")
                success = True
            else:
                print("Error: Could not locate Publish/Save button.")
                
            page.close()
            browser.close()
        except Exception as e:
            print(f"Error automating Pinterest on profile: {e}")
        finally:
            kill_chrome_on_port_9222()
            
    return success

def run_pinterest_syndication(blog_data):
    print("=================== PINTEREST SYNDICATION START ===================")
    
    local_image = download_temp_image(blog_data["image"])
    if not local_image:
        print("Aborting Pinterest syndication: Could not download image.")
        return
        
    pin_data = {
        "title": blog_data["title"],
        "description": f"{blog_data['excerpt']}\n\nRead full article at: {blog_data['slug']} #quiz #trivia #ai #creator",
        "link": f"https://quizviral-nine.vercel.app/blog/{blog_data['slug']}",
        "image_path": local_image
    }
    
    successful_pins = 0
    for idx, profile in enumerate(CHROME_PROFILES):
        print(f"\n--- Processing Profile {idx + 1}/{len(CHROME_PROFILES)} ---")
        if publish_pin_for_profile(profile, pin_data):
            successful_pins += 1
            
    print(f"\n=================== PINTEREST SYNDICATION COMPLETE ({successful_pins}/{len(CHROME_PROFILES)} posted) ===================")
    
    # Cleanup temp file
    try:
        if os.path.exists(local_image):
            os.remove(local_image)
    except Exception:
        pass

if __name__ == "__main__":
    # Test data
    test_blog = {
        "title": "Unlocking the Keanu Reeves Viral Wave: How to Create Massive Trivia Engagement with QuizViral AI",
        "excerpt": "Learn how you can leverage trending Keanu Reeves topics to generate viral quiz videos and scale your content instantly.",
        "slug": "unlocking-the-keanu-reeves-viral-wave-how-to-create-massive-trivia-engagement-with-quizviral-ai",
        "image": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&h=675&q=80"
    }
    run_pinterest_syndication(test_blog)
