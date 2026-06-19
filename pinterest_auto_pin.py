import os
import sys
import time
import re
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

# HEADLESS Mode: Set to False to open Chrome visibly (highly recommended for debugging and manual verification)
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
        
    # Optimized performance flags to prevent Chrome background tasks from hogging internet bandwidth
    cmd = [
        chrome_path,
        "--remote-debugging-port=9222",
        "--remote-debugging-address=127.0.0.1",
        f"--user-data-dir={profile_path}",
        "--disable-gpu",
        "--disable-background-networking",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-breakpad",
        "--disable-client-side-phishing-detection",
        "--disable-default-apps",
        "--disable-hang-monitor",
        "--disable-prompt-on-repost",
        "--disable-sync",
        "--metrics-recording-only",
        "--no-first-run",
        "--safebrowsing-disable-auto-update"
    ]
    if HEADLESS:
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

def get_safe_input(page, selectors, exclude_keywords=["search"]):
    """Helper to locate a visible input element while strictly excluding global navigation search inputs"""
    for sel in selectors:
        loc = page.locator(sel)
        count = loc.count()
        for i in range(count):
            el = loc.nth(i)
            try:
                if el.is_visible():
                    placeholder = el.get_attribute("placeholder") or ""
                    el_id = el.get_attribute("id") or ""
                    aria_label = el.get_attribute("aria-label") or ""
                    name = el.get_attribute("name") or ""
                    
                    combined = (placeholder + el_id + aria_label + name).lower()
                    if any(kw in combined for kw in exclude_keywords):
                        continue
                    return el
            except Exception:
                continue
    return None

def publish_pin_for_profile(profile_path, pin_data, idx):
    if not launch_chrome_with_profile(profile_path):
        print(f"Failed to start Chrome for profile: {profile_path}")
        return False
        
    success = False
    with sync_playwright() as p:
        try:
            print("Connecting Playwright to Chrome remote debugger (using 127.0.0.1 to prevent loopback lag)...")
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0]
            page = context.new_page()
            
            # Set viewport to 1280x800 to make sure all components are visible on screen
            page.set_viewport_size({"width": 1280, "height": 800})
            
            # Navigate to Pinterest Pin Builder with a retry loop to handle page load errors/redirection aborts
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
            
            # Wait up to 15s for either Title Input (logged-in) OR Login Button (logged-out) to appear
            print("Pinterest components load hone ka wait kar rahe hai...")
            try:
                page.wait_for_selector(
                    'input[placeholder*="title" i], textarea[placeholder*="title" i], button:has-text("Log in"), button:has-text("Log In"), a[href*="login"]',
                    timeout=15000
                )
            except Exception:
                pass
                
            # Double check login state
            is_logged_out = False
            has_login_btn = (
                page.locator('button:has-text("Log in")').is_visible() or 
                page.locator('button:has-text("Log In")').is_visible() or 
                "login" in page.url
            )
            
            # Check if title input is visible
            has_title_input = False
            title_input_loc = page.locator('input[placeholder*="title" i], textarea[placeholder*="title" i]')
            if title_input_loc.count() > 0:
                for i in range(title_input_loc.count()):
                    if title_input_loc.nth(i).is_visible():
                        has_title_input = True
                        break
                        
            if has_login_btn or (not has_title_input and "pin-builder" not in page.url):
                is_logged_out = True
                
            if is_logged_out:
                expected_id = ACCOUNT_IDS[idx] if idx < len(ACCOUNT_IDS) else "Pinterest Account"
                print("\n" + "="*80)
                print(f"👉 [IMPORTANT ALERT] Profile {idx + 1} logged in nahi hai! (Expected Account: {expected_id})")
                print(f"Bhai, kripya open hui Chrome Window me Pinterest Account '{expected_id}' par log in/sign in karein.")
                print("Log in hone ke baad jab aap Pinterest home feed ya Pin Builder page par pahunch/navigate ho jayein,")
                print("tab yahan terminal me ENTER press karein aur automation continue ho jayegi...")
                print("="*80 + "\n")
                
                input("Manually log in karne ke baad ENTER press karein...")
                print("Settle hone ke liye 5 seconds wait kar rahe hai...")
                time.sleep(5)
                
                # Re-navigate to Pin Builder after login with retry loop
                for attempt in range(3):
                    try:
                        page.goto("https://www.pinterest.com/pin-builder/", wait_until="domcontentloaded", timeout=45000)
                        break
                    except Exception as e:
                        if attempt == 2:
                            raise e
                        print(f"Navigation error (attempt {attempt + 1}/3): {e}. Retrying in 5 seconds...")
                        time.sleep(5)
            
            print("Account verified as logged in. Filling Pin details with deliberate human delays...")
            time.sleep(3)
            
            # 1. Upload the image file
            print("Blog image upload kar rahe hai...")
            file_input = page.locator('input[type="file"]')
            if file_input.count() > 0:
                file_input.first.set_input_files(pin_data["image_path"])
                print("Image upload complete!")
                time.sleep(5) # Delay after upload
            else:
                print("Error: Could not find image file input element on Pinterest.")
                
            # 2. Fill the Title
            print("Title fill kar rahe hai...")
            title_selectors = [
                '[data-testid="pin-builder-title"]',
                'textarea[id*="title" i]',
                'input[id*="title" i]',
                'textarea[placeholder*="title" i]',
                'input[placeholder*="title" i]',
                'textarea[placeholder*="Title" i]',
                'input[placeholder*="Title" i]'
            ]
            target_title = get_safe_input(page, title_selectors)
            if target_title:
                target_title.scroll_into_view_if_needed()
                time.sleep(1.5)
                target_title.click()
                time.sleep(1.5)
                target_title.fill("")
                time.sleep(1.5)
                target_title.fill(pin_data["title"])
                print(f"Title filled successfully: {pin_data['title']}")
                time.sleep(3) # Delay after typing title
            else:
                print("Warning: Could not find Title input.")
                
            # 3. Fill the Description
            print("Description aur blog link fill kar rahe hai...")
            desc_selectors = [
                '[data-testid="pin-builder-description"]',
                'div[role="textbox"][placeholder*="about" i]',
                'div[contenteditable="true"][placeholder*="about" i]',
                'textarea[placeholder*="about" i]',
                'textarea[placeholder*="description" i]',
                'div[role="textbox"][id*="description" i]',
                'textarea[id*="description" i]'
            ]
            target_desc = get_safe_input(page, desc_selectors)
            if target_desc:
                target_desc.scroll_into_view_if_needed()
                time.sleep(1.5)
                target_desc.click()
                time.sleep(1.5)
                target_desc.fill("")
                time.sleep(1.5)
                target_desc.fill(pin_data["description"])
                print("Description field filled successfully with full blog post URL.")
                time.sleep(4) # Delay after typing description
            else:
                print("Warning: Could not find Description input.")
                
            # 4. Fill the Destination Link
            print("Destination blog link fill kar rahe hai...")
            link_selectors = [
                '[data-testid="pin-builder-link"]',
                'input[placeholder*="link" i]',
                'input[placeholder*="website" i]',
                'input[placeholder*="URL" i]',
                'input[id*="link" i]',
                'input[aria-label*="link" i]'
            ]
            target_link = get_safe_input(page, link_selectors)
            if target_link:
                target_link.scroll_into_view_if_needed()
                time.sleep(1.5)
                target_link.click()
                time.sleep(1.5)
                target_link.fill("")
                time.sleep(1.5)
                target_link.fill(pin_data["link"])
                print(f"Destination link field filled: {pin_data['link']}")
                time.sleep(3) # Delay after typing link
            else:
                print("Warning: Could not find Destination Link input.")
                
            # 5. Handle Product Tagging (New requested Feature)
            print("Product Tag lagane ki koshish kar rahe hai...")
            try:
                # Search for Tag products button on the page
                tag_btn = page.locator(
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
                    
                    # Look for search or URL input
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
                        print(f"Product tag search me link fill kiya: {pin_data['link']}")
                        time.sleep(5) # wait for results
                        
                        # Click the first product result or image
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
                            
                            # Click Done/Save button
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
                                print("Done button nahi mila. Esc pressing...")
                                page.keyboard.press("Escape")
                                time.sleep(2)
                        else:
                            print("Product result image nahi mila. Esc pressing...")
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
                    '[data-testid="board-dropdown"]',
                    'button[aria-label*="Select board" i]',
                    'button[aria-label*="board" i]',
                    'div[role="button"][aria-label*="board" i]',
                    'button[class*="board" i]',
                    'button:has-text("Select")'
                ]
                target_board_opener = None
                for sel in board_opener_selectors:
                    loc = page.locator(sel)
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
                    print("Board dropdown open ho gaya, search kar rahe hai...")
                    time.sleep(4) # Delay for dropdown animation
                    
                    # Search box inside dropdown
                    search_box = page.locator('[role="listbox"] input, [class*="dropdown"] input, input[placeholder*="Search"]').first
                    if search_box.count() > 0 and search_box.is_visible():
                        search_box.click()
                        time.sleep(1.5)
                        search_box.fill(BOARD_NAME)
                        print(f"Board search input me '{BOARD_NAME}' type kiya...")
                        time.sleep(3)
                    
                    # Click matching board option
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
                        print(f"Board '{BOARD_NAME}' nahi mila list me. Default board use karenge.")
                        page.keyboard.press("Escape")
                        time.sleep(2)
                else:
                    print("Could not open board picker. Default board use kiya jayega.")
            
            # 7. Click Publish / Save
            print("Publish button locate kar rahe hai...")
            publish_btn = page.locator(
                'button[data-testid="board-dropdown-select-button"], '
                'button[data-testid="create-pin-submit"], '
                'button:has-text("Publish"), '
                'button:has-text("Save"), '
                'button[aria-label*="Publish" i], '
                'button[aria-label*="Save" i], '
                'div[role="button"]:has-text("Publish"), '
                'div[role="button"]:has-text("Save")'
            )
            target_publish = None
            if publish_btn.count() > 0:
                for i in range(publish_btn.count()):
                    if publish_btn.nth(i).is_visible():
                        target_publish = publish_btn.nth(i)
                        break
            if target_publish:
                target_publish.scroll_into_view_if_needed()
                time.sleep(1.5)
                print("Publish/Save button click kar rahe hai...")
                target_publish.click()
                print("Publish click ho gaya! Completion process ke liye 15 seconds wait kar rahe hai...")
                time.sleep(15)  # Wait for Pinterest to process
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
