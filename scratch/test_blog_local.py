#!/usr/bin/env python3
"""
Test script for verifying SEO optimization, smart interlinking,
and JWT generation logic of ghost_blog_automation.py.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Ensure project root is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ghost_blog_automation import (
    create_jwt,
    slugify,
    validate_meta_title,
    validate_meta_description,
    apply_smart_interlinking,
    set_image_alt_tags
)

class TestBlogAutomation(unittest.TestCase):
    
    def test_jwt_generation(self):
        print("Testing JWT generation...")
        api_key = "5c10e055f1027c0001f35f2a:b2d56a362a71bf64c1e4c7d0d0c3298c56fa769f34f89d5345a557b49463e275"
        token = create_jwt(api_key, version="v2")
        
        # Verify JWT format: header.payload.signature
        parts = token.split('.')
        self.assertEqual(len(parts), 3)
        print("-> JWT structure is correct (3 parts).")
        
    def test_slugify(self):
        print("Testing slugify...")
        self.assertEqual(slugify("How to Automate YouTube Shorts in 2025!"), "how-to-automate-youtube-shorts-in-2025")
        self.assertEqual(slugify("  QuizViral AI: Bulk Video Generator  "), "quizviral-ai-bulk-video-generator")
        print("-> Slugify function works correctly.")
        
    def test_meta_title_seo(self):
        print("Testing meta title SEO optimization...")
        
        # Scenario 1: Missing keywords, too short
        short_title = "My custom blog post"
        optimized = validate_meta_title(short_title)
        self.assertTrue(50 <= len(optimized) <= 60, f"Length {len(optimized)} not in 50-60 range")
        self.assertTrue("AI Video Generator" in optimized or "faceless quiz videos" in optimized or "bulk quiz maker" in optimized)
        
        # Scenario 2: Keyword present, too short
        short_kw_title = "Faceless quiz videos guide"
        optimized = validate_meta_title(short_kw_title)
        self.assertTrue(50 <= len(optimized) <= 60)
        
        # Scenario 3: Too long
        long_title = "How to automate YouTube Shorts and create hundreds of viral faceless quiz videos using QuizViral AI bulk video generator"
        optimized = validate_meta_title(long_title)
        self.assertTrue(50 <= len(optimized) <= 60)
        self.assertTrue(optimized.endswith("..."))
        print("-> Meta title validations are correct.")
        
    def test_meta_description_seo(self):
        print("Testing meta description SEO optimization...")
        
        # Scenario 1: Too short, missing keywords
        short_desc = "Learn how to make a blog."
        optimized = validate_meta_description(short_desc)
        self.assertTrue(145 <= len(optimized) <= 150, f"Length {len(optimized)} not in 145-150 range")
        self.assertTrue("bulk quiz maker" in optimized or "faceless quiz videos" in optimized or "AI video generator" in optimized)
        
        # Scenario 2: Too long
        long_desc = "Learn how to automate YouTube Shorts with QuizViral AI bulk quiz maker. We write long form descriptions that are definitely over the limit of one hundred and fifty characters to check if the truncation works as expected without any bugs."
        optimized = validate_meta_description(long_desc)
        self.assertTrue(145 <= len(optimized) <= 150, f"Length {len(optimized)} was {len(optimized)}")
        self.assertTrue(optimized.endswith("..."))
        print("-> Meta description validations are correct.")
        
    def test_smart_interlinking(self):
        print("Testing smart interlinking...")
        blogs = {
            "how-to-automate-youtube-shorts-scale-fast-with-quizviral-ai": "How to Automate YouTube Shorts: Scale Fast with QuizViral AI",
            "how-google-discover-works-creator-guide": "How Google Discover Works: A Creator's Guide"
        }
        
        # Test content with keywords "QuizViral AI", "automate YouTube Shorts", and "Google Discover"
        html = (
            "<p>We love using QuizViral AI. It is an amazing platform.</p>"
            "<p>You should learn to automate YouTube Shorts because it drives traffic.</p>"
            "<div>Check out our tips on google discover as well.</div>"
            "<a href='https://another-link.com'>Do not modify automate YouTube Shorts inside existing links</a>"
        )
        
        linked = apply_smart_interlinking(html, blogs, "https://quizviral-nine.vercel.app", "https://quizviral-nine.vercel.app/blog")
        
        # Verify CTA link
        self.assertTrue('href="https://quizviral-nine.vercel.app"' in linked)
        # Verify blog 1 link
        self.assertTrue('href="https://quizviral-nine.vercel.app/blog/how-to-automate-youtube-shorts-scale-fast-with-quizviral-ai"' in linked)
        # Verify blog 2 link
        self.assertTrue('href="https://quizviral-nine.vercel.app/blog/how-google-discover-works-creator-guide"' in linked)
        # Verify existing link was NOT modified
        self.assertTrue("<a href='https://another-link.com'>Do not modify automate YouTube Shorts inside existing links</a>" in linked)
        print("-> Smart interlinking successfully injects links and respects existing tag bounds.")
        
    def test_image_alt_tags(self):
        print("Testing image alt tag assignment...")
        html = (
            "<p>Here is an image:</p>"
            "<img src='https://unsplash.com/123.jpg'>"
            "<img src='https://unsplash.com/456.jpg' alt=''>"
            "<img src='https://unsplash.com/789.jpg' alt='custom alt to preserve'>"
        )
        
        updated = set_image_alt_tags(html, "faceless quiz videos", "How to automate YouTube shorts")
        
        # Verify first image got alt tag
        self.assertTrue("alt='How to automate YouTube shorts - faceless quiz videos - QuizViral AI illustration'" in updated)
        # Verify second image (empty alt) got updated
        self.assertTrue("alt='How to automate YouTube shorts - faceless quiz videos - QuizViral AI illustration part 2'" in updated)
        # Verify third image (custom alt) was preserved
        self.assertTrue("alt='custom alt to preserve'" in updated)
        print("-> Alt tag heuristic works correctly.")

if __name__ == "__main__":
    unittest.main()
