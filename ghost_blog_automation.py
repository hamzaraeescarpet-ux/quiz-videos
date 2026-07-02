#!/usr/bin/env python3
"""
Ghost CMS & Groq API Blog Automation Script
===========================================
This script automates the generation and publishing of SEO-optimized blog posts
to Ghost CMS using the Groq API. It includes custom JWT authentication for the
Ghost Admin API (v2 or newer), automated meta title/description optimization,
smart interlinking to existing blogs, and automatic alt-text insertion.

Setup Instructions:
-------------------
1. Install dependencies:
   pip install requests

2. Configure environment variables (or edit the FALLBACK_CONFIG dictionary below):
   - GHOST_API_URL: Your Ghost site Admin API URL (e.g., https://your-blog.ghost.io)
   - GHOST_ADMIN_API_KEY: Your Ghost Admin API key (format: 'id:secret')
   - GROQ_API_KEY: Your Groq API key (starts with 'gsk_')
   - GROQ_MODEL: Groq LLM model to use (default: 'llama-3.3-70b-specdec')

Usage:
------
- To run a test generation (dry run) without publishing:
  python ghost_blog_automation.py --topic "YouTube Trivia Niche Strategy" --keyword "faceless quiz videos" --dry-run

- To generate and publish directly:
  python ghost_blog_automation.py --topic "YouTube Trivia Niche Strategy" --keyword "faceless quiz videos"
"""

import os
import sys
import re
import json
import time
import hmac
import hashlib
import base64
import argparse
import urllib.parse
from datetime import datetime

# ==================== CONFIGURATION ====================
# You can set these environment variables in Hugging Face Space Settings (Secrets).
# Fallback hardcoded values can be placed in this dictionary for local testing.
FALLBACK_CONFIG = {
    "GHOST_API_URL": "",          # e.g., "https://blog.quizviral.ai" or "http://localhost:2368"
    "GHOST_ADMIN_API_KEY": "",    # e.g., "60ad3f7c...:9f8a2c1..." (id:secret)
    "GHOST_API_VERSION": "v2",    # "v2" is default, also supports "v3", "v4", or "v5"
    "GROQ_API_KEY": "",           # Your Groq API Key
    "GROQ_MODEL": "llama-3.3-70b-specdec", # Groq model to use
    "CTA_URL": "https://quizviral-nine.vercel.app",  # Call to Action link
    "BLOG_BASE_URL": "https://quizviral-nine.vercel.app/blog", # Base URL for your blog post slugs
    "PUBLISH_STATUS": "draft"    # Use "draft" to review first, or "published"
}

def get_config(key):
    """Retrieves config from environment variables, falling back to hardcoded dictionary."""
    return os.environ.get(key, FALLBACK_CONFIG.get(key, ""))

# ==================== TASK 1: GHOST JWT AUTHENTICATION ====================

def base64url_encode(data: bytes) -> str:
    """Helper to perform base64url encoding as specified by JWT standard."""
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def create_jwt(api_key: str, version: str = "v2") -> str:
    """
    Generates a signed JSON Web Token (JWT) using standard libraries (no PyJWT dependency).
    Authenticates with Ghost Admin API.
    """
    if not api_key or ":" not in api_key:
        raise ValueError("Invalid Ghost Admin API Key format. Must be 'id:secret'")
        
    key_id, secret_hex = api_key.split(':')
    
    # Define JWT Header
    header = {
        "alg": "HS256",
        "typ": "JWT",
        "kid": key_id
    }
    
    # Define JWT Payload
    # Ghost expects audience based on version
    if version.lower() in ["v2", "v3"]:
        audience = f"/{version}/admin/"
    else:
        audience = "/admin/"
        
    now = int(time.time())
    payload = {
        "iat": now,
        "exp": now + 300, # Token expires in 5 minutes
        "aud": audience
    }
    
    # Encode header & payload to JSON bytes
    header_json = json.dumps(header, separators=(',', ':')).encode('utf-8')
    payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    
    # Construct unsigned token
    unsigned_token = base64url_encode(header_json) + "." + base64url_encode(payload_json)
    
    # Convert hex secret to raw bytes
    try:
        secret_bytes = bytes.fromhex(secret_hex)
    except ValueError as e:
        raise ValueError(f"Secret part of the API key is not valid hex: {e}")
        
    # Sign token using HMAC SHA-256
    signature = hmac.new(secret_bytes, unsigned_token.encode('utf-8'), hashlib.sha256).digest()
    
    # Return full signed token
    signed_token = unsigned_token + "." + base64url_encode(signature)
    return signed_token


# ==================== TASK 2 & 3: SEO OPTIMIZATION LOGIC ====================

def slugify(text):
    """Converts a title into a clean, SEO-friendly URL slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')

def validate_meta_title(title):
    """
    Enforces a strict 50-60 character length limit.
    Ensures at least one high-intent keyword is included.
    """
    keywords = ["faceless quiz videos", "AI video generator", "bulk quiz maker"]
    title = title.strip()
    
    # 1. Inject keyword if missing
    has_kw = any(kw.lower() in title.lower() for kw in keywords)
    if not has_kw:
        # Append a keyword while respecting maximum limit
        phrase = " | AI Video Generator"
        if len(title) + len(phrase) <= 60:
            title += phrase
        else:
            title = title[:60 - len(phrase)] + phrase
            
    # 2. Strict character bounds enforcement (50-60 chars)
    if len(title) < 50:
        # Pad with relevant branding text
        padding = " | QuizViral AI Generator"
        title = (title + padding)[:60]
        if len(title) < 50:
            title = title.ljust(50, '.')
    elif len(title) > 60:
        # Truncate and add ellipsis
        title = title[:57] + "..."
        
    return title

def validate_meta_description(desc):
    """
    Enforces a strict 145-150 character length limit.
    Ensures at least one high-intent keyword is included.
    """
    keywords = ["faceless quiz videos", "AI video generator", "bulk quiz maker"]
    desc = desc.strip()
    
    # 1. Inject keywords if missing
    has_kw = any(kw.lower() in desc.lower() for kw in keywords)
    if not has_kw:
        suffix = " Create shorts fast with our bulk quiz maker and AI video generator."
        desc = (desc + suffix)[:150]
        
    # 2. Strict character bounds enforcement (145-150 chars)
    if len(desc) < 145:
        # Pad with optimized description content
        padding = " Build viral automated quiz channels easily. Import questions, select background videos, generate TTS voiceovers, and export vertical clips."
        desc = (desc + padding)[:150]
        if len(desc) < 145:
            desc = desc.ljust(145, '.')
    elif len(desc) > 150:
        # Truncate and add ellipsis
        desc = desc[:147] + "..."
        
    return desc

def load_existing_blogs(script_dir):
    """
    Tries to read existing blogs from the frontend workspace to gather interlinks.
    Returns a dictionary of {slug: title}.
    """
    # Pre-populate with target 10-15 blogs for robust fallback interlinking
    blogs = {
        "how-to-automate-youtube-shorts-scale-fast-with-quizviral-ai": "How to Automate YouTube Shorts: Scale Fast with QuizViral AI",
        "how-to-automate-youtube-shorts-scale-a-faceless-quiz-channel-fast": "How to Automate YouTube Shorts: Scale a Faceless Quiz Channel Fast",
        "how-google-discover-works-creator-guide": "How Google Discover Works: A Creator's Guide to Driving Free Traffic",
        "how-to-make-quiz-videos-for-youtube": "How to Make Quiz Videos for YouTube",
        "faceless-youtube-channel-ideas-that-make-money": "Faceless YouTube Channel Ideas That Make Money",
        "best-ai-video-generator-for-youtube": "Best AI Video Generator for YouTube",
        "how-to-automate-youtube-shorts": "How to Automate YouTube Shorts",
        "how-to-make-100-youtube-shorts-fast": "How to Make 100 YouTube Shorts Fast",
        "tiktok-quiz-ideas-that-go-viral": "TikTok Quiz Ideas That Go Viral",
        "youtube-quiz-channel-monetization-strategy": "YouTube Quiz Channel Monetization Strategy",
        "best-quiz-video-maker-free": "Best Quiz Video Maker Free",
        "how-to-start-a-faceless-youtube-channel": "How to Start a Faceless YouTube Channel"
    }
    
    # Try reading frontend/src/data/blogPosts.js if present in workspace
    blog_posts_path = os.path.join(script_dir, "frontend", "src", "data", "blogPosts.js")
    if os.path.exists(blog_posts_path):
        try:
            with open(blog_posts_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Simple regex search for slug and title matches
            slugs = re.findall(r"\bslug:\s*['\"`]([^'\"`]+?)['\"`]", content)
            titles = re.findall(r"\btitle:\s*['\"`]([^'\"`]+?)['\"`]", content)
            
            # Map discovered articles
            for s, t in zip(slugs, titles):
                blogs[s] = t
        except Exception as e:
            print(f"[Warning] Could not parse local blogPosts.js: {e}")
            
    return blogs

def apply_smart_interlinking(html_content, blogs_dict, cta_url, blog_base_url="https://quizviral-nine.vercel.app/blog", cta_text="QuizViral AI"):
    """
    Scans the HTML body content and inserts:
      1. A target CTA link back to the QuizViral AI product.
      2. Hyperlinks to 10-15 existing blogs based on keyword matching.
    It replaces only the FIRST occurrence of a matching keyword and ignores tags or attribute text.
    """
    # Split text content by HTML tags to prevent modifying tag structures or attributes
    parts = re.split(r'(<[^>]+>)', html_content)
    
    # Setup keywords mapping to slugs
    blog_keywords = {
        "how-to-automate-youtube-shorts-scale-fast-with-quizviral-ai": ["automate youtube shorts", "youtube shorts automation"],
        "how-to-automate-youtube-shorts-scale-a-faceless-quiz-channel-fast": ["scale a faceless quiz channel", "faceless quiz channel fast"],
        "how-google-discover-works-creator-guide": ["google discover", "discover feed"],
        "how-to-make-quiz-videos-for-youtube": ["make quiz videos", "quiz videos for youtube"],
        "faceless-youtube-channel-ideas-that-make-money": ["faceless youtube channel", "faceless channel ideas"],
        "best-ai-video-generator-for-youtube": ["best ai video generator", "ai video generator"],
        "how-to-make-100-youtube-shorts-fast": ["make 100 youtube shorts"],
        "tiktok-quiz-ideas-that-go-viral": ["tiktok quiz", "viral tiktok quizzes"],
        "youtube-quiz-channel-monetization-strategy": ["quiz channel monetization"],
        "best-quiz-video-maker-free": ["best quiz video maker", "bulk quiz maker"],
        "how-to-start-a-faceless-youtube-channel": ["start a faceless youtube channel"]
    }
    
    # Merge any other items discovered dynamically
    for slug in blogs_dict:
        if slug not in blog_keywords:
            phrase = slug.replace("-", " ")
            blog_keywords[slug] = [phrase]
            
    linked_slugs = set()
    cta_linked = False
    
    for i in range(len(parts)):
        # If it is an HTML tag, skip modifying it
        if parts[i].startswith('<') and parts[i].endswith('>'):
            continue
            
        text = parts[i]
        
        # 1. Apply CTA Link (QuizViral AI)
        if not cta_linked:
            # Match word "QuizViral AI" case insensitively
            pattern = re.compile(rf'\b({re.escape(cta_text)})\b', re.IGNORECASE)
            match = pattern.search(text)
            if match:
                matched_text = match.group(1)
                text = pattern.sub(f'<a href="{cta_url}" target="_blank" rel="noopener">{matched_text}</a>', text, count=1)
                cta_linked = True
                
        # 2. Apply Blog Interlinks
        for slug, keywords in blog_keywords.items():
            if slug in linked_slugs:
                continue
                
            for kw in keywords:
                pattern = re.compile(rf'\b({re.escape(kw)})\b', re.IGNORECASE)
                match = pattern.search(text)
                if match:
                    matched_text = match.group(1)
                    full_link = f"{blog_base_url}/{slug}".replace("//blog", "/blog")
                    text = pattern.sub(f'<a href="{full_link}">{matched_text}</a>', text, count=1)
                    linked_slugs.add(slug)
                    break # Link only one keyword phrase per blog post
                    
        parts[i] = text
        
    return "".join(parts)

def set_image_alt_tags(html_content, keyword, post_title):
    """
    Scans the HTML content for <img> tags and automatically populates/replaces
    empty or generic alt attributes with keyword-rich descriptions for SEO.
    """
    # Match <img ... src="url" ...> or <img ... src='url' ...>
    img_pattern = re.compile(r'<img\s+([^>]*?)src=(["\'])(.*?)\2([^>]*?)>', re.IGNORECASE)
    img_counter = [0]
    
    def repl(match):
        img_counter[0] += 1
        attrs_before = match.group(1)
        quote_char = match.group(2)
        src = match.group(3)
        attrs_after = match.group(4)
        
        all_attrs = attrs_before + " " + attrs_after
        
        # Formulate SEO optimized description including the keyword and the post title
        seo_alt = f"{post_title} - {keyword} - QuizViral AI illustration"
        if img_counter[0] > 1:
            seo_alt += f" part {img_counter[0]}"
            
        alt_match = re.search(r'\balt=(["\'])(.*?)\1', all_attrs, re.IGNORECASE)
        
        if alt_match:
            existing_alt = alt_match.group(2)
            # If alt is blank or generic, overwrite it
            if not existing_alt.strip() or existing_alt.lower() in ["image", "img", "placeholder", "graphic"]:
                new_attrs_before = re.sub(r'\balt=(["\'])(.*?)\1', f'alt={quote_char}{seo_alt}{quote_char}', attrs_before, flags=re.IGNORECASE)
                new_attrs_after = re.sub(r'\balt=(["\'])(.*?)\1', f'alt={quote_char}{seo_alt}{quote_char}', attrs_after, flags=re.IGNORECASE)
                return f'<img {new_attrs_before}src={quote_char}{src}{quote_char}{new_attrs_after}>'
            else:
                # Keep custom alt
                return match.group(0)
        else:
            # alt is completely missing, inject it
            return f'<img {attrs_before}src={quote_char}{src}{quote_char} alt={quote_char}{seo_alt}{quote_char}{attrs_after}>'
            
    return img_pattern.sub(repl, html_content)


# ==================== TASK 3: CONTENT GENERATION (GROQ API) ====================

def generate_blog_content(groq_key, model, topic, keyword):
    """
    Sends request to the Groq API to generate an SEO-optimized blog post in JSON format.
    The response includes title, excerpt, metadata, and HTML content.
    """
    import requests
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }
    
    system_prompt = (
        "You are an expert SEO content creator and copywriter for QuizViral AI. "
        "QuizViral AI is a SaaS platform that generates bulk faceless quiz videos "
        "for platforms like YouTube Shorts, TikTok, and Instagram Reels in one click from CSV uploads. "
        "Your task is to write high-quality, comprehensive, and well-researched blog posts "
        "which are at least 1000+ words. Respond directly in JSON format. "
        "All HTML output should be clean body content, starting with an H1 tag."
    )
    
    user_prompt = f"""
    Write a comprehensive, long-form, well-researched blog post (minimum 1000 words) about: "{topic}".
    
    KEYWORD REQUIREMENT:
    Target Keyword: "{keyword}"
    Make sure the keyword is naturally integrated throughout the text and is part of the H1 heading.
    
    FORMAT REQUIREMENT:
    Return ONLY a raw JSON response. Use the exact keys listed in the template.
    Do NOT include code block format wrappers (like ```json). Just start directly with {{ and end with }}.
    
    The blog post HTML must start directly with an <h1> tag containing the target keyword.
    Inside the HTML, use standard tags: <h2>, <h3>, <p>, <ul>, <li>, <strong>, <em>, <blockquote>.
    Include a step-by-step tutorial on how to use QuizViral AI to automate video generation.
    Do NOT include <html>, <head> or <body> wrappers.
    Include at least one illustrative <img> tag with a source from Unsplash, e.g.:
    <img src="https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7" alt="placeholder">

    JSON Output Template:
    {{
      "title": "A catchy, SEO-friendly headline",
      "slug": "url-friendly-slug-with-keyword",
      "excerpt": "A compelling 2-sentence summary of the article.",
      "meta_title": "Meta title exactly 50-60 characters featuring keywords like 'faceless quiz videos' or 'AI video generator'",
      "meta_description": "Meta description exactly 145-150 characters featuring keywords like 'AI video generator' or 'bulk quiz maker'",
      "html": "<h1>Target Keyword Title</h1><h2>Introduction</h2><p>...</p>"
    }}
    """
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.7,
        "max_tokens": 4000
    }
    
    print(f"Contacting Groq API using model '{model}' for topic: '{topic}'...")
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            print(f"Groq API Error HTTP {response.status_code}: {response.text}")
            return None
            
        res_data = response.json()
        raw_json_str = res_data["choices"][0]["message"]["content"].strip()
        
        # Clean up any potential markdown wrap by the LLM
        if raw_json_str.startswith("```"):
            # Remove leading ```json or ```
            raw_json_str = re.sub(r"^```(json)?", "", raw_json_str, flags=re.IGNORECASE).strip()
            if raw_json_str.endswith("```"):
                raw_json_str = raw_json_str[:-3].strip()
                
        post_data = json.loads(raw_json_str)
        return post_data
        
    except Exception as e:
        print(f"Exception occurred while calling Groq API: {e}")
        return None

# ==================== PUBLISHING LOGIC ====================

def publish_to_ghost(api_url, api_key, version, post_data, status="draft"):
    """
    Publishes the optimized blog post to the Ghost Admin API.
    """
    import requests
    
    api_url = api_url.rstrip('/')
    
    # 1. Generate Auth Token
    try:
        jwt_token = create_jwt(api_key, version=version)
    except Exception as e:
        print(f"Failed to generate JWT: {e}")
        return False, str(e)
        
    # 2. Build Ghost CMS Admin URL
    if version.lower() in ["v2", "v3"]:
        url = f"{api_url}/ghost/api/{version}/admin/posts/?source=html"
    else:
        url = f"{api_url}/ghost/api/admin/posts/?source=html"
        
    headers = {
        "Authorization": f"Ghost {jwt_token}",
        "Content-Type": "application/json"
    }
    
    # 3. Formulate Payload
    payload = {
        "posts": [
            {
                "title": post_data["title"],
                "slug": post_data["slug"],
                "html": post_data["html"],
                "custom_excerpt": post_data.get("excerpt", ""),
                "meta_title": post_data["meta_title"],
                "meta_description": post_data["meta_description"],
                "status": status
            }
        ]
    }
    
    print(f"Sending request to Ghost Admin API ({version}) at: {url}...")
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code in [200, 201]:
            resp_json = response.json()
            post_id = resp_json.get("posts", [{}])[0].get("id", "Unknown")
            print(f"SUCCESS! Published post '{post_data['title']}' to Ghost CMS. ID: {post_id}")
            return True, resp_json
        else:
            err_msg = f"HTTP {response.status_code}: {response.text}"
            print(f"ERROR: Ghost CMS rejected post creation. Details: {err_msg}")
            return False, err_msg
    except Exception as e:
        err_msg = str(e)
        print(f"ERROR: Failed to connect to Ghost server: {err_msg}")
        return False, err_msg

# ==================== MAIN EXECUTION ====================

def main():
    parser = argparse.ArgumentParser(description="Automate SEO blog posts for QuizViral AI using Groq and Ghost CMS.")
    parser.add_argument("--topic", type=str, required=True, help="The topic of the blog post to write.")
    parser.add_argument("--keyword", type=str, required=True, help="The main target keyword for SEO optimization.")
    parser.add_argument("--status", type=str, default=None, choices=["draft", "published"], help="Override default publish status.")
    parser.add_argument("--dry-run", action="store_true", help="Perform generation, optimization, and local interlinking but do not publish to Ghost.")
    parser.add_argument("--model", type=str, default=None, help="Override default Groq model.")
    args = parser.parse_args()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Load configuration parameters
    ghost_url = get_config("GHOST_API_URL")
    ghost_key = get_config("GHOST_ADMIN_API_KEY")
    ghost_ver = get_config("GHOST_API_VERSION") or "v2"
    groq_key = get_config("GROQ_API_KEY")
    groq_model = args.model or get_config("GROQ_MODEL") or "llama-3.3-70b-specdec"
    cta_url = get_config("CTA_URL") or "https://quizviral-nine.vercel.app"
    blog_base_url = get_config("BLOG_BASE_URL") or "https://quizviral-nine.vercel.app/blog"
    post_status = args.status or get_config("PUBLISH_STATUS") or "draft"
    
    print("\n--- Starting Ghost SEO Blog Automation ---")
    print(f"Topic: {args.topic}")
    print(f"Target Keyword: {args.keyword}")
    print(f"Groq Model: {groq_model}")
    print(f"Post Status: {post_status}")
    print(f"Dry-run mode: {args.dry-run}")
    
    # API key check (when not running dry-run)
    if not args.dry-run:
        if not ghost_url or not ghost_key:
            print("ERROR: Ghost credentials (GHOST_API_URL, GHOST_ADMIN_API_KEY) are missing.")
            print("Configure them in your Environment Secrets or edit the FALLBACK_CONFIG dictionary.")
            sys.exit(1)
            
    if not groq_key:
        print("ERROR: GROQ_API_KEY is missing. Setup this environment secret first.")
        sys.exit(1)
        
    # Step 1: Generate Content
    post_data = generate_blog_content(groq_key, groq_model, args.topic, args.keyword)
    if not post_data or "html" not in post_data:
        print("ERROR: Content generation failed.")
        sys.exit(1)
        
    print(f"\nSuccessfully generated article draft: '{post_data.get('title')}'")
    
    # Step 2: Validate and Optimize Title & Description (SEO Strict Constraints)
    meta_title = validate_meta_title(post_data.get("meta_title", ""))
    meta_description = validate_meta_description(post_data.get("meta_description", ""))
    
    post_data["meta_title"] = meta_title
    post_data["meta_description"] = meta_description
    
    # Enforce lowercase URL friendly slug
    post_data["slug"] = slugify(post_data.get("slug") or post_data.get("title", "post"))
    
    print(f"Optimized Meta Title (Length {len(meta_title)}): '{meta_title}'")
    print(f"Optimized Meta Description (Length {len(meta_description)}): '{meta_description}'")
    print(f"SEO Slug: '{post_data['slug']}'")
    
    # Step 3: Parse existing blogs for interlinking
    existing_blogs = load_existing_blogs(script_dir)
    print(f"Loaded {len(existing_blogs)} existing blogs to scan for interlinks.")
    
    # Step 4: Apply Smart Interlinking & CTA Link
    raw_html = post_data["html"]
    interlinked_html = apply_smart_interlinking(raw_html, existing_blogs, cta_url, blog_base_url)
    
    # Step 5: Automate Image Alt-Text insertion
    optimized_html = set_image_alt_tags(interlinked_html, args.keyword, post_data.get("title", ""))
    
    # Step 6: Validate H1 tag at the beginning of the post body
    if not optimized_html.strip().startswith("<h1"):
        print("H1 tag missing at the beginning. Prepending target keyword-rich H1 tag...")
        h1_tag = f"<h1>{post_data.get('title', args.topic)}</h1>\n"
        optimized_html = h1_tag + optimized_html.strip()
        
    post_data["html"] = optimized_html
    
    # Estimate word count
    words = len(re.findall(r'\b\w+\b', re.sub('<[^<]+?>', '', optimized_html)))
    print(f"Final Optimized Post Word Count: {words} words")
    
    if args.dry-run:
        print("\n================ [DRY RUN - GENERATED OUTPUT] ================")
        print(f"Title: {post_data['title']}")
        print(f"Slug: {post_data['slug']}")
        print(f"Excerpt: {post_data['excerpt']}")
        print(f"Meta Title: {post_data['meta_title']}")
        print(f"Meta Description: {post_data['meta_description']}")
        print(f"HTML Body Content Sample:\n{post_data['html'][:600]}...\n[Truncated]")
        print("==============================================================")
        
        # Save output to scratch directory for verification
        scratch_dir = os.path.join(script_dir, "scratch")
        os.makedirs(scratch_dir, exist_ok=True)
        test_out_path = os.path.join(scratch_dir, "test_post_out.json")
        with open(test_out_path, "w", encoding="utf-8") as f:
            json.dump(post_data, f, indent=2)
        print(f"Dry run outputs saved to scratch file: {test_out_path}")
        print("Dry run completed successfully.")
        return
        
    # Step 7: Publish to Ghost CMS
    success, result = publish_to_ghost(ghost_url, ghost_key, ghost_ver, post_data, status=post_status)
    if success:
        print("\nBlog post generated, optimized, and published successfully!")
    else:
        print(f"\nFailed to publish. Error: {result}")
        sys.exit(1)

if __name__ == "__main__":
    main()
