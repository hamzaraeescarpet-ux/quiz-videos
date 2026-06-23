@echo off
cd /d "%~dp0"
echo Starting Trending Blog Generator...
python generate_trending_blog_playwright.py
pause
