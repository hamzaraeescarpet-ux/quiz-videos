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
HEADLESS = True

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
    by using highly targeted, unique selectors scoped within the Pin Builder editor,
    along with language-independent structural fallbacks.
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
            
    # Structural Fallback for Title
    if not fields["title"]:
        all_inputs = page.locator('input[type="text"]:not([readonly])')
        for i in range(all_inputs.count()):
            inp = all_inputs.nth(i)
            if inp.is_visible():
                # The first visible text input is typically the title
                fields["title"] = inp
                break

    # Structural Fallback for Description
    if not fields["desc"]:
        editables = page.locator('[contenteditable="true"], textarea')
        for i in range(editables.count()):
            el = editables.nth(i)
            if el.is_visible():
                if fields["title"] and el.element_handle() == fields["title"].element_handle():
                    continue
                fields["desc"] = el
                break

    # Structural Fallback for Link
    if not fields["link"]:
        all_inputs = page.locator('input[type="text"]:not([readonly]), input[type="url"]:not([readonly])')
        visible_inputs = []
        for i in range(all_inputs.count()):
            inp = all_inputs.nth(i)
            if inp.is_visible():
                if fields["title"] and inp.element_handle() == fields["title"].element_handle():
                    continue
                # Skip search input fields
                placeholder = inp.get_attribute("placeholder") or ""
                inp_id = inp.get_attribute("id") or ""
                inp_class = inp.get_attribute("class") or ""
                if any(x in placeholder.lower() or x in inp_id.lower() or x in inp_class.lower() for x in ["search", "select", "board", "find"]):
                    continue
                visible_inputs.append(inp)
        if visible_inputs:
            # Destination link is usually the last text/url input
            fields["link"] = visible_inputs[-1]
            
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
                    
                # 3. Fill the Description (Pinterest contenteditable needs keyboard, not fill)
                print("Description aur blog link fill kar rahe hai...")
                target_desc = fields["desc"]
                if target_desc:
                    target_desc.scroll_into_view_if_needed()
                    time.sleep(1.5)
                    target_desc.click()
                    time.sleep(1.5)
                    # Pinterest rich-text div ignores .fill() — use keyboard in chunks
                    page.keyboard.press("Control+A")
                    page.keyboard.press("Delete")
                    time.sleep(0.5)
                    desc_text = pin_data["description"]
                    chunk_size = 200
                    for i in range(0, len(desc_text), chunk_size):
                        page.keyboard.type(desc_text[i:i+chunk_size])
                        time.sleep(0.3)
                    print("Description filled successfully.")
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
                        '[data-test-id*="board" i]',
                        '[data-testid*="board" i]',
                        'button[id*="board" i]',
                        'button[class*="board" i]',
                        '[aria-label*="board" i]',
                        '[aria-label*="बोर्ड" i]'
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
                        time.sleep(4)
                        
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
                            
                        # Retry up to 3 times — Pinterest dropdown is flaky
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
                                    print(f"Board '{BOARD_NAME}' selected! (attempt {_attempt+1})")
                                    board_selected = True
                                    time.sleep(3)
                                    break
                                except Exception:
                                    pass
                            time.sleep(2)
                        if not board_selected:
                            print(f"Board '{BOARD_NAME}' not found in dropdown. Default board will be used.")
                            try:
                                page.locator("body").click(position={"x": 10, "y": 10}, force=True)
                            except Exception:
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
                    'button[type="submit"]',
                    'button:has-text("Publish")',
                    'button:has-text("Save")',
                    'button:has-text("सहेजें")',
                    'button:has-text("प्रकाशित करें")',
                    'button[aria-label*="Publish" i]',
                    'button[aria-label*="Save" i]',
                    'button[aria-label*="सहेजें" i]',
                    'button[aria-label*="प्रकाशित" i]',
                    'div[role="button"]:has-text("Publish")',
                    'div[role="button"]:has-text("Save")',
                    'div[role="button"]:has-text("सहेजें")'
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
                        
                # Fallback: scan all buttons if nothing matched
                if not target_publish:
                    all_buttons = page.locator('button')
                    for i in range(all_buttons.count()):
                        btn = all_buttons.nth(i)
                        try:
                            if btn.is_visible():
                                btn_id = btn.get_attribute("id") or ""
                                btn_class = btn.get_attribute("class") or ""
                                btn_text = btn.inner_text() or ""
                                if any(x in btn_id.lower() or x in btn_class.lower() or x in btn_text.lower() for x in ["publish", "save", "submit", "create", "सहेजें", "प्रकाशित"]):
                                    target_publish = btn
                                    break
                        except Exception:
                            continue
                            
                if target_publish:
                    target_publish.scroll_into_view_if_needed()
                    time.sleep(1.5)
                    # Wait up to 20s for publish button to become enabled (image upload delay)
                    for _w in range(10):
                        try:
                            is_disabled = target_publish.get_attribute("disabled") is not None
                            aria_disabled = target_publish.get_attribute("aria-disabled")
                            if not is_disabled and aria_disabled != "true":
                                break
                        except Exception:
                            break
                        print(f"Publish button disabled hai, image upload ka wait ({_w+1}/10)...")
                        time.sleep(2)
                    print("Publish/Save button click kar rahe hai...")
                    target_publish.click()
                    print("Publish click ho gaya! 20 seconds wait kar rahe hai...")
                    time.sleep(20)
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
    # Step 2: If logged out, just print warning and skip, no manual intervention needed!
    if result == "logged_out":
        expected_id = ACCOUNT_IDS[idx] if idx < len(ACCOUNT_IDS) else "Pinterest Account"
        print(f"⚠️ Profile {idx + 1} logged in nahi hai (Expected Account: {expected_id}). Skipping this profile...")
        return False
        
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
            
        # Add a delay between profiles (except for the last profile) to make it feel human
        if idx < len(CHROME_PROFILES) - 1:
            import random
            delay_sec = random.randint(35, 65)
            print(f"Waiting for {delay_sec} seconds before starting the next profile (human touch delay)...")
            time.sleep(delay_sec)
            
    print(f"\n=================== PINTEREST SYNDICATION COMPLETE ({successful_pins}/{len(CHROME_PROFILES)} posted) ===================")
    
    # Cleanup temp file
    try:
        if os.path.exists(local_image):
            os.remove(local_image)
    except Exception:
        pass

if __name__ == "__main__":
    # Check if user wants to login manually to a specific profile
    if len(sys.argv) > 1 and sys.argv[1] == "--login":
        try:
            profile_num = int(sys.argv[2])
            if 1 <= profile_num <= len(CHROME_PROFILES):
                idx = profile_num - 1
                profile_path = CHROME_PROFILES[idx]
                expected_id = ACCOUNT_IDS[idx]
                print("\n" + "="*80)
                print(f"👉 Profile {profile_num} ({expected_id}) par log in karne ke liye Chrome open kiya ja raha hai...")
                print("Kripya open hui browser window me login/signin karein.")
                print("Kaam poora hone ke baad, browser window ko close kar dein ya terminal me ENTER press karein...")
                print("="*80 + "\n")
                
                if launch_chrome_with_profile(profile_path, headless_mode=False):
                    input("\nLog in karne ke baad browser window ko close karein ya exit karne ke liye yahan ENTER press karein...")
                    kill_chrome_on_port_9222()
                else:
                    print("Failed to start Chrome.")
            else:
                print(f"Invalid profile number. Choose between 1 and {len(CHROME_PROFILES)}")
        except Exception as e:
            print(f"Error launching login mode: {e}")
            print("Usage: python pinterest_auto_pin.py --login <profile_number_1_to_4>")
        sys.exit(0)

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
