import re
import os

BLOG_POSTS_FILE = r"frontend/src/data/blogPosts.js"

if os.path.exists(BLOG_POSTS_FILE):
    with open(BLOG_POSTS_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    titles = re.findall(r"title:\s*['\"`](.*?)['\"`]", content)
    slugs = re.findall(r"slug:\s*['\"`](.*?)['\"`]", content)
    seoKeywords = re.findall(r"seoKeywords:\s*\[(.*?)\]", content, re.DOTALL)
    
    print(f"Total posts: {len(titles)}")
    for i in range(len(titles)):
        t = titles[i] if i < len(titles) else "N/A"
        s = slugs[i] if i < len(slugs) else "N/A"
        k = seoKeywords[i].strip().replace("\n", " ") if i < len(seoKeywords) else "N/A"
        print(f"Post {i+1}:")
        print(f"  Title: {t}")
        print(f"  Slug: {s}")
        print(f"  Keywords: {k}")
else:
    print("File not found")
