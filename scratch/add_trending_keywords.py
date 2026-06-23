import os
import re

BLOG_POSTS_FILE = r"frontend/src/data/blogPosts.js"

# Read the file
with open(BLOG_POSTS_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# Let's map titles/slugs to the trending keywords based on check_posts.py output
mappings = {
    "How to Automate YouTube Shorts and Create 100+ Viral Videos": "rocket launch today",
    "How to Automate YouTube Shorts and Create 100+ Viral Videos Fast": "rocket launch",
    "How to Automate YouTube Shorts and Create 100+ Quiz Videos Fast": "global shipping",
    "Capitalizing on the M&Ms Trend: How to Build a Viral Faceless Quiz Channel in One Click with QuizViral AI": "m&ms trivia",
    "How to Ride the Dodgers Score Trend: Turn Viral MLB Stats into Faceless Trivia Content with QuizViral AI": "dodgers score trivia",
    "Geopolitics, Global Trade, and Group Chats: Monetizing the": "is the strait of hormuz open trivia",
    "Unlocking the Keanu Reeves Viral Wave: How to Create Massive Trivia Engagement with QuizViral AI": "keanu reeves trivia",
    "Oscars, Outfits, and Algorithms: How to Turn Michael B. Jordan Trends into Viral Revenue with QuizViral AI": "michael b jordan trivia",
    "Hitting a Home Run with Sports Trends: How to Turn the Seth Brown Minor League Release into Viral Views Using QuizViral AI": "seth brown minor league release trivia",
    "Fueling Your Feed: How to Turn the Trending": "gas trivia",
    "Riding the": "what is a data breach trivia",
    "Capitalizing on High-Profile Legal News: How to Turn Samuel Alito Trends into Viral Trivia Traffic with QuizViral AI": "samuel alito trivia",
    "How to Build a Faceless Trivia Channel on TikTok (Complete Growth Guide)": "faceless TikTok channel",
    "The Ultimate ChatGPT Prompt Strategy for Viral Trivia Videos": "ChatGPT trivia prompt",
    "How Google Discover Works: A Creator": "Google Discover optimization"
}

# We can find matches for each title and insert the trendingKeyword field.
# Let's do this line by line or using re.sub.
# Since titles might be slightly different or truncated in regex, let's write a precise replacement.

modified_content = content
count = 0

for title_key, trend_val in mappings.items():
    # Find title definition in file
    # We want to match: title: "title_key..." or title: 'title_key...' or title: `title_key...`
    # Escape special characters in title_key
    escaped_title = re.escape(title_key)
    
    # We match title line: title: <quote><optional text><title_key><optional text><quote>
    # e.g., title: "How to Ride the Dodgers Score Trend: Turn Viral MLB Stats into Faceless Trivia Content with QuizViral AI",
    # Or for truncated ones: title: "Geopolitics, Global Trade, and Group Chats: Monetizing the ..."
    pattern = rf'(title:\s*[\'\"]{escaped_title}.*?[\'\"]\s*,)'
    match = re.search(pattern, modified_content)
    if match:
        matched_str = match.group(1)
        # Check if trendingKeyword is already present in this block
        # We can find the start of the object { before this title
        # Let's see if we can find trendingKeyword in the 50 characters before or after the title
        title_idx = match.start()
        surrounding = modified_content[max(0, title_idx-100):min(len(modified_content), title_idx+200)]
        if "trendingKeyword:" in surrounding:
            print(f"Skipping '{title_key}', already has trendingKeyword.")
            continue
            
        # Replace the title line to include trendingKeyword: "trend_val", right below/above it
        replacement = f'trendingKeyword: "{trend_val}",\n  {matched_str}'
        modified_content = modified_content.replace(matched_str, replacement, 1)
        print(f"Added trendingKeyword for '{title_key}' -> '{trend_val}'")
        count += 1
    else:
        print(f"Could not find title matching: '{title_key}'")

if count > 0:
    with open(BLOG_POSTS_FILE, "w", encoding="utf-8") as f:
        f.write(modified_content)
    print(f"Successfully updated blogPosts.js with {count} trendingKeywords!")
else:
    print("No updates made to blogPosts.js.")
