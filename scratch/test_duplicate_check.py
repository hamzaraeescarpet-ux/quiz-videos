import sys
import os

# Import generate_trending_blog_playwright to test is_keyword_already_published
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))
from generate_trending_blog_playwright import is_keyword_already_published

test_keywords = [
    "rocket launch today",
    "rocket launch",
    "global shipping",
    "m&ms trivia",
    "emma navarro",
    "new untried keyword 123"
]

print("Testing is_keyword_already_published:")
for kw in test_keywords:
    res = is_keyword_already_published(kw)
    print(f"  '{kw}' -> {res}")
