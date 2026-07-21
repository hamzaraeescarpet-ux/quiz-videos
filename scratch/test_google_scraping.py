import os
import sys
import time
import re
import urllib.parse
from playwright.sync_api import sync_playwright

# Set paths
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME_PROFILE_PATH = r"C:\Users\hamza\Downloads\python development\browser automation\gemini video points\bulk scheduling fb videos\chrome_profile"

# Import helper functions from main file
sys.path.append(SCRIPT_DIR)
from generate_trending_blog_playwright import launch_chrome_if_needed, kill_chrome_on_port_9222

def scrape_trends_and_search():
    # Launch Chrome on 9222
    launched = launch_chrome_if_needed()
    if not launched:
        print("Failed to launch Chrome.")
        return
        
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.new_page()
            
            # --- 1. Scrape Google Trends ---
            print("\n--- STEP 1: Scraping Google Trends US ---")
            page.goto("https://trends.google.com/trending?geo=US")
            time.sleep(5)
            
            trends = []
            # Selector A: modern grid cell entries
            elements = page.locator('div[role="row"] div[role="gridcell"]').all_inner_texts()
            for el in elements:
                val = el.strip().split('\n')[0]
                if val and len(val) > 2 and len(val) < 40 and not val.isdigit():
                    if val not in trends and not any(x in val.lower() for x in ["search", "explore", "trending", "menu", "sign in"]):
                        trends.append(val)
            
            # Selector B: table anchors
            if len(trends) < 5:
                anchors = page.locator('td.query a, .trend-card a, tr td a').all_inner_texts()
                for el in anchors:
                    val = el.strip()
                    if val and len(val) > 2 and len(val) < 40:
                        if val not in trends:
                            trends.append(val)
                            
            print("Found trends:", trends[:10])
            top_5 = trends[:5]
            print("Top 5 Trends selected:", top_5)
            
            if not top_5:
                print("Failed to get trends. Using fallbacks.")
                top_5 = ["July 4th Trivia", "US National Parks", "Minecraft Update 2026", "Viral YouTube Shorts", "Space Exploration"]
                
            # Pick the first one for search test
            selected_topic = top_5[0]
            print(f"\nSelected topic for Google Search suggestion scraping: '{selected_topic}'")
            
            # --- 2. Autocomplete Suggestions on Google ---
            print("\n--- STEP 2: Scraping Google Search Autocomplete Suggestions ---")
            page.goto("https://www.google.com")
            time.sleep(3)
            
            # Find search bar
            search_box = page.locator('textarea[name="q"], input[name="q"], [title="Search"]').first
            search_box.click()
            time.sleep(1)
            
            suggestions = set()
            letters_to_test = ['a', 'b', 'y', 'z']
            
            for letter in letters_to_test:
                query = f"{selected_topic} {letter}"
                print(f"Typing: '{query}'...")
                search_box.fill(query)
                time.sleep(2) # Wait for suggestions dropdown
                
                # Scrape suggestion dropdown elements
                # Google autocomplete suggestions list items are typically inside role="presentation" or role="option"
                sugg_elements = page.locator('ul[role="listbox"] li div[role="option"] span').all_inner_texts()
                if not sugg_elements:
                    # Alternative selector
                    sugg_elements = page.locator('ul[role="listbox"] li span').all_inner_texts()
                    
                for el in sugg_elements:
                    val = el.strip()
                    if val and val.lower() != query.lower():
                        # Sometimes Google highlights the bolded rest of the suggestion
                        # so we construct the full phrase if it's just the suggestion
                        suggestions.add(val)
                        
            print(f"Total autocomplete suggestions found: {len(suggestions)}")
            print("Suggestions:", list(suggestions)[:15])
            
            # --- 3. People Also Ask & Related Searches ---
            print("\n--- STEP 3: Scraping Google Search PAA & Related Searches ---")
            # Search the topic directly
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(selected_topic)}" if 'urllib' in sys.modules else f"https://www.google.com/search?q={selected_topic.replace(' ', '+')}"
            print(f"Navigating directly to search results: {search_url}")
            page.goto(search_url)
            time.sleep(4)
            
            # People Also Ask (PAA) questions
            paa_questions = set()
            # PAA elements usually have data-q attribute or are in accordion list
            paa_elements = page.locator('div[data-q], div[class*="related-question-pair"] span').all_inner_texts()
            for el in paa_elements:
                val = el.strip()
                if val.endswith('?') and len(val) > 10:
                    paa_questions.add(val)
                    
            print(f"People Also Ask questions found: {len(paa_questions)}")
            print("PAA Questions:", list(paa_questions)[:10])
            
            # Related Searches
            related_searches = set()
            # Related searches are usually links containing search queries at the bottom
            related_elements = page.locator('div[class*="related-searches"] a, div.L55Fcf a, a[href*="search?q="]').all_inner_texts()
            for el in related_elements:
                val = el.strip()
                # Skip pagination links or empty links
                if val and not val.isdigit() and len(val) > 3 and val.lower() != "next":
                    related_searches.add(val)
                    
            print(f"Related Searches found: {len(related_searches)}")
            print("Related Searches:", list(related_searches)[:10])
            
            page.close()
            browser.close()
        except Exception as e:
            print(f"Error during scraping: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    try:
        scrape_trends_and_search()
    finally:
        kill_chrome_on_port_9222()
