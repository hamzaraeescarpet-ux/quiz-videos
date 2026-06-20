import os
import sys
import time
import re
import json
import subprocess
from playwright.sync_api import sync_playwright

# Configurations
# We have mapped your 4 Chrome profiles to your specific Pinterest accounts!
# Profile 1 (Index 0) -> hamzaraeescarpet
# Profile 2 (Index 1) -> hamzarais2023
# Profile 3 (Index 2) -> hamzarais354
# Profile 4 (Index 3) -> deshkikhabar79
CHROME_PROFILES = [
    r"C:\Users\hamza\Downloads\python development\browser automation\gemini video points\bulk scheduling fb videos\chrome_profile",
    r"C:\Users\hamza\Downloads\python development\browser automation\gemini video points\bulk scheduling fb videos\chrome_profile_2",
    r"C:\Users\hamza\Downloads\facebook post automation\hamzarais2023\chrome_profile",
    r"C:\Users\hamza\Downloads\facebook post automation\hamzarais2023\chrome_profile_2"
]

ACCOUNT_IDS = [
    "hamzaraeescarpet",
    "hamzarais2023",
    "hamzarais354",
    "deshkikhabar79"
]

BOARD_NAME = "Trivia Quiz Videos" # Set this to your Pinterest board name or leave empty to use default board

# HEADLESS Mode: Set to True to run invisibly in the background. It will automatically open headfully if login is needed!
HEADLESS = False

def check_port_open(port=9222):
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except Exception:
        return False

def reset_chrome_crash_state(profile_path):
    """Resets the Chrome crash state in Preferences file to completely disable the 'Restore pages' popup"""
    paths = [
        os.path.join(profile_path, "Default", "Preferences"),
        os.path.join(profile_path, "Preferences")
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                print(f"Resetting Chrome crash/restore state in: {p}...")
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().strip()
                    if not content:
                        continue
                    data = json.loads(content)
                
                # Modify crash state preferences
                modified = False
                if "profile" in data and isinstance(data["profile"], dict):
                    if "exit_type" in data["profile"]:
                        data["profile"]["exit_type"] = "Normal"
                        modified = True
                if "exit_state_classified" in data:
                    data["exit_state_classified"] = "Normal"
                    modified = True
                    
                if modified:
                    with open(p, "w", encoding="utf-8") as f:
                        json.dump(data, f)
                    print(f"Successfully cleared Chrome crash popup state!")
            except Exception as e:
                print(f"Could not reset Preferences file crash state: {e}")

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

def launch_chrome_with_profile(profile_path, headless_mode=False):
    # Ensure port is clean
    kill_chrome_on_port_9222()
    
    # Clear session crash popup state in Chrome JSON preferences
    reset_chrome_crash_state(profile_path)
    
    print(f"Launching Chrome (Headless={headless_mode}) with profile: {profile_path}...")
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
        
    # Use standard Chrome flags that don't block background networking or resource loading,
    # and disable automation indicators to prevent bot detection.
    cmd = [
        chrome_path,
        "--remote-debugging-port=9222",
        "--remote-debugging-address=127.0.0.1",
        f"--user-data-dir={profile_path}",
        "--no-first-run",
        "--disable-default-apps",
        "--disable-sync",
        "--disable-session-crashed-bubble",
        "--hide-crash-restore-bubble",
        "--disable-blink-features=AutomationControlled"
    ]
    if headless_mode:
        cmd.extend(["--headless=new"])
        
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

def format_pinterest_title(title):
    """Shortens the blog title to fit Pinterest's strict limit and makes it attractive (strictly under 70 chars)"""
    title = title.strip()
    
    # Remove outer quotes if any
    title = re.sub(r'^["\'`]+|["\'`]+$', '', title)
    
    # Try split by common dividers to get a punchy part
    for divider in [":", "-", "|"]:
        if divider in title:
            parts = title.split(divider)
            for part in parts:
                cleaned_part = part.strip()
                if 25 <= len(cleaned_part) <= 70:
                    return cleaned_part
                    
    # Default truncation under 70 characters at a word boundary
    if len(title) > 70:
        truncated = title[:67]
        last_space = truncated.rfind(" ")
        if last_space > 20:
            return truncated[:last_space] + "..."
        return truncated + "..."
    return title

def format_pinterest_description(title, excerpt, url):
    """Creates a rich description within Pinterest's 500-char limit including the post link"""
    header = f"💡 {title}\n\n"
    cta = f"\n\nRead the full blog post and take the interactive quiz here:\n👉 {url}\n\nCreate viral trivia quizzes instantly with QuizViral AI!\n#quiz #trivia #viral #quizviral #contentcreator"
    
    # Calculate space left for excerpt
    max_excerpt_len = 500 - len(header) - len(cta) - 10 # buffer
    
    cleaned_excerpt = excerpt.strip()
    if len(cleaned_excerpt) > max_excerpt_len:
        truncated = cleaned_excerpt[:max_excerpt_len]
        last_space = truncated.rfind(" ")
        if last_space > 20:
            cleaned_excerpt = truncated[:last_space] + "..."
        else:
            cleaned_excerpt = truncated + "..."
            
    desc = f"{header}{cleaned_excerpt}{cta}"
    
    # Final safety check to truncate to exactly 500 characters
    if len(desc) > 500:
        desc = desc[:497] + "..."
    return desc

def find_builder_fields(page):
    """
    Scans the Pin Builder page and detects Title, Description, and Link fields
    by using highly targeted, unique selectors scoped within the Pin Builder editor.
    """
    fields = {"title": None, "desc": None, "link": None}
    
    # 1. Locate Title Input
    title_selectors = [
        '#storyboard-selector-title',
        '[data-test-id="storyboard-selector-title"]',
        'input[placeholder*="Tell everyone" i]',
        'input[placeholder*="Pin is about" i]',
        '[data-testid="pin-builder-title"]',
        'textarea[placeholder*="title" i]',
        'input[placeholder*="title" i]',
        '[aria-label*="title" i]'
    ]
    for sel in title_selectors:
        loc = page.locator(sel)
        if loc.count() > 0 and loc.first.is_visible():
            fields["title"] = loc.first
            break
            
    # 2. Locate Description Textbox (typically contenteditable div or textarea)
    desc_selectors = [
        'div.public-DraftEditor-content',
        '[data-test-id="editor-with-mentions"]',
        '[aria-label*="Describe your Pin" i]',
        '[aria-label*="Describe" i]',
        '[data-test-id="storyboard-description-field-container"] [contenteditable="true"]',
        '[data-testid="pin-builder-description"]',
        'div[role="textbox"][placeholder*="about" i]',
        '[aria-label*="description" i]',
        'textarea[placeholder*="description" i]'
    ]
    for sel in desc_selectors:
        loc = page.locator(sel)
        if loc.count() > 0 and loc.first.is_visible():
            fields["desc"] = loc.first
            break
            
    # 3. Locate Destination Link Input
    link_selectors = [
        '#WebsiteField',
        '[data-test-id="WebsiteField"]',
        'input[placeholder*="Add a link" i]',
        '[data-testid="pin-builder-link"]',
        'input[placeholder*="link" i]',
        'input[placeholder*="website" i]',
        'input[placeholder*="url" i]',
        '[aria-label*="link" i]'
    ]
    for sel in link_selectors:
        loc = page.locator(sel)
        if loc.count() > 0 and loc.first.is_visible():
            fields["link"] = loc.first
            break
            
    return fields

def publish_pin_for_profile(profile_path, pin_data, idx):
    # This wrapper triggers the Playwright automation flow, and switches Chrome 
    # back to headful mode dynamically if a manual login is required.
    
    def execute_flow(headless_mode):
        if not launch_chrome_with_profile(profile_path, headless_mode=headless_mode):
            print(f"Failed to start Chrome for profile: {profile_path}")
            return "failed"
            
        with sync_playwright() as p:
            try:
                print(f"Connecting Playwright (Headless={headless_mode}) to Chrome remote debugger...")
                browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                context = browser.contexts[0]
                page = context.new_page()
                page.set_viewport_size({"width": 1280, "height": 800})
                
                # Navigate to Pin Builder with a retry loop
                print("Navigating to Pinterest Pin Builder...")
                for attempt in range(3):
                    try:
                        page.goto("https://www.pinterest.com/pin-builder/", wait_until="domcontentloaded", timeout=45000)
                        break
                    except Exception as e:
                        if attempt == 2:
                            raise e
                        print(f"Navigation error (attempt {attempt + 1}/3): {e}. Retrying in 5 seconds...")
                        time.sleep(5)
                
                # Wait 10s for the page elements to settle/render
                print("Pinterest components load hone ka wait kar rahe hai (10 seconds)...")
                time.sleep(10)
                
                fields = find_builder_fields(page)
                
                # Verify login state
                is_logged_out = False
                if not fields["title"] and not fields["desc"]:
                    print("Re-checking elements in 5 seconds to prevent false logout trigger...")
                    time.sleep(5)
                    fields = find_builder_fields(page)
                    if not fields["title"] and not fields["desc"]:
                        is_logged_out = True
                        
                if is_logged_out:
                    page.close()
                    browser.close()
                    return "logged_out"
                    
                print("Account verified as logged in. Filling Pin details...")
                time.sleep(3)
                
                # 1. Upload the image file
                print("Blog image upload kar rahe hai...")
                file_input = page.locator('input[type="file"]')
                if file_input.count() > 0:
                    file_input.first.set_input_files(pin_data["image_path"])
                    print("Image upload complete!")
                    time.sleep(5)
                else:
                    print("Error: Could not find image file input element.")
                    
                # 2. Fill the Title
                print("Title fill kar rahe hai...")
                target_title = fields["title"]
                if target_title:
                    target_title.scroll_into_view_if_needed()
                    time.sleep(1.5)
                    target_title.click()
                    time.sleep(1.5)
                    target_title.fill("")
                    time.sleep(1.5)
                    target_title.fill(pin_data["title"])
                    print(f"Title filled: {pin_data['title']}")
                    time.sleep(3)
                else:
                    print("Warning: Could not find Title input.")
                    
                # 3. Fill the Description
                print("Description aur blog link fill kar rahe hai...")
                target_desc = fields["desc"]
                if target_desc:
                    target_desc.scroll_into_view_if_needed()
                    time.sleep(1.5)
                    target_desc.click()
                    time.sleep(1.5)
                    target_desc.fill("")
                    time.sleep(1.5)
                    target_desc.fill(pin_data["description"])
                    print("Description filled successfully with full blog post URL.")
                    time.sleep(4)
                else:
                    print("Warning: Could not find Description input.")
                    
                # 4. Fill the Destination Link
                print("Destination blog link fill kar rahe hai...")
                target_link = fields["link"]
                if target_link:
                    target_link.scroll_into_view_if_needed()
                    time.sleep(1.5)
                    target_link.click()
                    time.sleep(1.5)
                    target_link.fill("")
                    time.sleep(1.5)
                    target_link.fill(pin_data["link"])
                    print(f"Destination link filled: {pin_data['link']}")
                    time.sleep(3)
                else:
                    print("Warning: Could not find Destination Link input.")
                    
                # Find container scope for subsequent operations
                container_selectors = [
                    'div[data-testid="pin-builder"]',
                    'div[class*="pin-builder" i]',
                    'div[class*="PinBuilder" i]',
                    'div[class*="creationCard" i]',
                    'div[class*="workspace" i]'
                ]
                scope = None
                for sel in container_selectors:
                    loc = page.locator(sel)
                    if loc.count() > 0 and loc.first.is_visible():
                        scope = loc.first
                        break
                if not scope:
                    scope = page
                    
                # 5. Handle Product Tagging
                print("Product Tag lagane ki koshish kar rahe hai...")
                try:
                    tag_btn = scope.locator(
                        'button:has-text("Tag products"), '
                        '[aria-label*="Tag products" i], '
                        '[data-testid="tag-button"], '
                        'button:has-text("Tag"), '
                        '[aria-label*="tag" i]'
                    )
                    target_tag_btn = None
                    if tag_btn.count() > 0:
                        for i in range(tag_btn.count()):
                            if tag_btn.nth(i).is_visible():
                                target_tag_btn = tag_btn.nth(i)
                                break
                    if target_tag_btn:
                        target_tag_btn.scroll_into_view_if_needed()
                        time.sleep(1.5)
                        print("Tag products button mil gaya. Click kar rahe hai...")
                        target_tag_btn.click()
                        time.sleep(4)
                        
                        tag_input = page.locator(
                            'input[placeholder*="url" i], '
                            'input[placeholder*="link" i], '
                            'input[placeholder*="search" i], '
                            'input[placeholder*="Search" i]'
                        ).first
                        if tag_input.count() > 0 and tag_input.is_visible():
                            tag_input.click()
                            time.sleep(1.5)
                            tag_input.fill(pin_data["link"])
                            time.sleep(1.5)
                            tag_input.press("Enter")
                            print(f"Product tag link fill kiya: {pin_data['link']}")
                            time.sleep(5)
                            
                            first_result = page.locator(
                                'div[role="listitem"] img, '
                                '[data-testid*="product" i] img, '
                                'div[class*="product"] img, '
                                'canvas'
                            ).first
                            if first_result.count() > 0 and first_result.is_visible():
                                first_result.click()
                                print("Product result select kiya.")
                                time.sleep(3)
                                
                                done_btn = page.locator(
                                    'button:has-text("Done"), '
                                    'button:has-text("Save"), '
                                    'button:has-text("Create")'
                                )
                                target_done = None
                                if done_btn.count() > 0:
                                    for i in range(done_btn.count()):
                                        if done_btn.nth(i).is_visible():
                                            target_done = done_btn.nth(i)
                                            break
                                if target_done:
                                    target_done.click()
                                    print("Product tag apply ho gaya!")
                                    time.sleep(3)
                                else:
                                    page.keyboard.press("Escape")
                                    time.sleep(2)
                            else:
                                page.keyboard.press("Escape")
                                time.sleep(2)
                        else:
                            print("Tag input field nahi mila.")
                    else:
                        print("Tag products button page par nahi mila. Skipping optional product tagging...")
                except Exception as tag_err:
                    print(f"Product tagging process skip ho gaya (Issue): {tag_err}")
                    
                # 6. Handle Board Selection
                if BOARD_NAME:
                    print(f"Board '{BOARD_NAME}' select karne ki koshish kar rahe hai...")
                    board_opener_selectors = [
                        '[data-test-id="board-dropdown-select-button"]',
                        '[data-testid="board-dropdown"]',
                        'button[aria-haspopup="listbox"]',
                        'button[aria-haspopup="true"]',
                        'button[id*="board" i]',
                        'button[class*="board" i]',
                        '[aria-label*="board" i]'
                    ]
                    target_board_opener = None
                    for sel in board_opener_selectors:
                        loc = scope.locator(sel)
                        count = loc.count()
                        for i in range(count):
                            el = loc.nth(i)
                            if el.is_visible():
                                target_board_opener = el
                                break
                        if target_board_opener:
                            break
                            
                    if target_board_opener:
                        target_board_opener.scroll_into_view_if_needed()
                        time.sleep(1.5)
                        target_board_opener.click()
                        time.sleep(4) # Delay for dropdown animation
                        
                        search_box = page.locator('[role="listbox"] input, [class*="dropdown"] input, input[placeholder*="Search"]').first
                        if search_box.count() > 0 and search_box.is_visible():
                            search_box.click()
                            time.sleep(1.5)
                            search_box.fill(BOARD_NAME)
                            time.sleep(3)
                            
                        board_item = page.locator(
                            f'div[role="listitem"] div:has-text("{BOARD_NAME}"), '
                            f'div[role="option"] div:has-text("{BOARD_NAME}"), '
                            f'div[class*="board"]:has-text("{BOARD_NAME}"), '
                            f':has-text("{BOARD_NAME}")'
                        ).first
                        if board_item.count() > 0 and board_item.is_visible():
                            board_item.click()
                            print(f"Board '{BOARD_NAME}' select ho gaya!")
                            time.sleep(3)
                        else:
                            page.keyboard.press("Escape")
                            time.sleep(2)
                    else:
                        print("Could not open board picker. Default board use kiya jayega.")
                        
                # 7. Click Publish / Save
                print("Publish button locate kar rahe hai...")
                publish_selectors = [
                    '[data-test-id="board-dropdown-save-button"]',
                    '[data-testid="board-dropdown-save-button"]',
                    '[data-test-id="create-pin-submit"]',
                    '[data-testid="create-pin-submit"]',
                    'button:has-text("Publish")',
                    'button:has-text("Save")',
                    'button[aria-label*="Publish" i]',
                    'button[aria-label*="Save" i]',
                    'div[role="button"]:has-text("Publish")',
                    'div[role="button"]:has-text("Save")'
                ]
                target_publish = None
                for sel in publish_selectors:
                    loc = page.locator(sel)
                    count = loc.count()
                    for i in range(count):
                        btn = loc.nth(i)
                        try:
                            if btn.is_visible():
                                target_publish = btn
                                break
                        except Exception:
                            continue
                    if target_publish:
                        break
                        
                if target_publish:
                    target_publish.scroll_into_view_if_needed()
                    time.sleep(1.5)
                    print("Publish/Save button click kar rahe hai...")
                    target_publish.click()
                    print("Publish click ho gaya! Completion ke liye wait kar rahe hai (15 seconds)...")
                    time.sleep(15)  # Wait for Pinterest to process
                    print("Pin published successfully!")
                    page.close()
                    browser.close()
                    return "success"
                else:
                    print("Error: Could not locate Publish/Save button.")
                    page.close()
                    browser.close()
                    return "failed"
            except Exception as ex:
                print(f"Error during execution: {ex}")
                try:
                    page.close()
                    browser.close()
                except Exception:
                    pass
                return "failed"
            finally:
                kill_chrome_on_port_9222()

    # Step 1: Run in Headless mode by default (True)
    result = execute_flow(headless_mode=HEADLESS)
    
    # Step 2: If logged out, override to headful mode and let user login manually
    if result == "logged_out":
        expected_id = ACCOUNT_IDS[idx] if idx < len(ACCOUNT_IDS) else "Pinterest Account"
        print("\n" + "="*80)
        print(f"👉 [IMPORTANT ALERT] Profile {idx + 1} logged in nahi hai! (Expected Account: {expected_id})")
        print(f"Humne Chrome ko visible/headful mode me open kiya hai taaki aap login kar sakein.")
        print(f"Kripya open hui Chrome Window me '{expected_id}' account par log in/sign in karein.")
        print("Log in hone ke baad jab Pinterest homepage ya Pin Builder load ho jaye,")
        print("tab yahan terminal me ENTER press karein aur automation continue ho jayegi...")
        print("="*80 + "\n")
        
        # Start Chrome in headful mode so user can see and log in
        if not launch_chrome_with_profile(profile_path, headless_mode=False):
            print("Failed to start headful Chrome.")
            return False
            
        input("Manually log in karne ke baad ENTER press karein...")
        print("Settle hone ke liye 5 seconds wait kar rahe hai...")
        time.sleep(5)
        
        # Execute the flow again in headful mode to complete publishing
        result = execute_flow(headless_mode=False)
        
    return result == "success"

def extract_js_field(content, field_name):
    """Robust regex parser to extract javascript object field values regardless of quotes type"""
    pattern = rf'(?:["\']?{field_name}["\']?)\s*:\s*([\"\'`])(.*?)\1\s*(?:,|$)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        val = match.group(2)
        # Unescape quotes and common characters
        val = val.replace('\\"', '"').replace("\\'", "'").replace('\\n', '\n')
        return val
    return None

def get_latest_blog_post():
    """Reads the latest blog post directly from frontend/src/data/blogPosts.js"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        blog_file_path = os.path.join(script_dir, "frontend", "src", "data", "blogPosts.js")
        
        if not os.path.exists(blog_file_path):
            print(f"Blog posts file not found at: {blog_file_path}")
            return None
            
        with open(blog_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Find the first object in the blogPosts array
        array_match = re.search(r"export const blogPosts = \[\s*\{(.*?)\}\s*(?:,|\s*\])", content, re.DOTALL)
        if not array_match:
            # Fallback to search any first object after blogPosts
            array_match = re.search(r"blogPosts\s*=\s*\[\s*\{(.*?)\}", content, re.DOTALL)
            
        if array_match:
            object_str = array_match.group(1)
            
            blog_data = {}
            for field in ["title", "slug", "excerpt", "image"]:
                val = extract_js_field(object_str, field)
                if val:
                    blog_data[field] = val
                    
            if "title" in blog_data and "slug" in blog_data:
                print(f"Loaded latest blog post: '{blog_data['title']}'")
                return blog_data
    except Exception as e:
        print(f"Failed to read latest blog post from file: {e}")
    return None

def run_pinterest_syndication(blog_data):
    print("=================== PINTEREST SYNDICATION START ===================")
    
    # Pre-check for image field
    image_url = blog_data.get("image")
    if not image_url:
        print("Aborting Pinterest syndication: 'image' field not found in blog post data.")
        return
        
    local_image = download_temp_image(image_url)
    if not local_image:
        print("Aborting Pinterest syndication: Could not download image.")
        return
        
    full_url = f"https://quizviral-nine.vercel.app/blog/{blog_data['slug']}"
    
    # We truncate the title to 70 characters for Pinterest's strict character limits
    short_title = format_pinterest_title(blog_data["title"])
    
    # Generate long, rich description containing the full blog post URL
    rich_description = format_pinterest_description(blog_data["title"], blog_data.get("excerpt", ""), full_url)
    
    pin_data = {
        "title": short_title,
        "description": rich_description,
        "link": full_url,
        "image_path": local_image
    }
    
    successful_pins = 0
    for idx, profile in enumerate(CHROME_PROFILES):
        print(f"\n--- Processing Profile {idx + 1}/{len(CHROME_PROFILES)} ---")
        if publish_pin_for_profile(profile, pin_data, idx):
            successful_pins += 1
            
    print(f"\n=================== PINTEREST SYNDICATION COMPLETE ({successful_pins}/{len(CHROME_PROFILES)} posted) ===================")
    
    # Cleanup temp file
    try:
        if os.path.exists(local_image):
            os.remove(local_image)
    except Exception:
        pass

if __name__ == "__main__":
    # If executed standalone, automatically fetch the latest post and syndicate it!
    print("Pinterest Auto-Pinning standalone run initiated.")
    latest_blog = get_latest_blog_post()
    if latest_blog:
        run_pinterest_syndication(latest_blog)
    else:
        print("Could not load latest blog post. Using fallback test post...")
        test_blog = {
            "title": "Unlocking the Keanu Reeves Viral Wave: How to Create Massive Trivia Engagement with QuizViral AI",
            "excerpt": "Learn how you can leverage trending Keanu Reeves topics to generate viral quiz videos and scale your content instantly.",
            "slug": "unlocking-the-keanu-reeves-viral-wave-how-to-create-massive-trivia-engagement-with-quizviral-ai",
            "image": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&h=675&q=80"
        }
        run_pinterest_syndication(test_blog)
