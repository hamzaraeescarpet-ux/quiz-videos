"""
Blog Automation Worker - Smart Daily Scheduler
===============================================
Ye script PC startup pe Windows Task Scheduler se automatically run hoti hai.

Kaam karne ka tarika:
- Din mein 3 baar blog publish karta hai (2-2 ghante ke gap se)
- Jab teen blogs ho jayein, agli subah tak wait karta hai
- PC band ho jaye aur dobara on ho to yahi state se resume karta hai
- State file (blog_scheduler_state.json) mein daily progress track hoti hai
"""

import os
import sys
import time
import subprocess
import json
from datetime import datetime, date, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE    = os.path.join(SCRIPT_DIR, "blog_automation_worker.log")
STATE_FILE  = os.path.join(SCRIPT_DIR, "blog_scheduler_state.json")
GENERATOR_SCRIPT = os.path.join(SCRIPT_DIR, "generate_trending_blog_playwright.py")

# --- Config ---
BLOGS_PER_DAY    = 3      # Ek din mein kitne blogs
GAP_BETWEEN_BLOGS = 7200  # 2 ghante (seconds) ka gap blogs ke beech
NEXT_DAY_HOUR    = 8      # Aglay din is ghante (8 AM) se shuru hoga
NEXT_DAY_MINUTE  = 0

# ── Logging ──────────────────────────────────────────────────────────────────

def log(msg):
    ts  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

# ── State Management ─────────────────────────────────────────────────────────

def load_state():
    """State file padhta hai. Nahi mili to fresh state deta hai."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log(f"State file read error: {e}. Fresh state se shuru ho raha hoon.")
    return {"last_date": "", "blogs_published_today": 0, "status": "idle"}

def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        log(f"State save error: {e}")

# ── Blog Generator ────────────────────────────────────────────────────────────

def run_blog_generator(blog_num):
    """generate_trending_blog_playwright.py chalata hai aur result deta hai."""
    log(f"Blog #{blog_num} generation shuru ho raha hai...")
    try:
        result = subprocess.run(
            [sys.executable, GENERATOR_SCRIPT],
            cwd=SCRIPT_DIR,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode == 0:
            log(f"Blog #{blog_num} successfully publish ho gaya!")
            return True
        else:
            log(f"Blog #{blog_num} fail hua (return code: {result.returncode}).")
            return False
    except Exception as e:
        log(f"Blog #{blog_num} run karne mein error: {e}")
        return False

# ── Wait Helpers ──────────────────────────────────────────────────────────────

def sleep_with_heartbeat(seconds, reason=""):
    """Sleep karta hai, har 5 min mein heartbeat log deta hai."""
    if reason:
        log(f"Wait: {reason} ({seconds//60} min {seconds%60} sec)")
    end_time = time.time() + seconds
    while True:
        remaining = end_time - time.time()
        if remaining <= 0:
            break
        # Har 5 dakike mein ek log line
        chunk = min(300, remaining)
        time.sleep(chunk)
        if time.time() < end_time:
            mins_left = int((end_time - time.time()) // 60)
            log(f"  ... abhi bhi wait kar raha hoon ({mins_left} min baaki)")

def seconds_until_next_day_start():
    """Agle din NEXT_DAY_HOUR:NEXT_DAY_MINUTE tak kitne seconds baaki hain."""
    now = datetime.now()
    tomorrow = date.today() + timedelta(days=1)
    next_start = datetime(tomorrow.year, tomorrow.month, tomorrow.day,
                          NEXT_DAY_HOUR, NEXT_DAY_MINUTE, 0)
    delta = (next_start - now).total_seconds()
    return max(int(delta), 60)  # Kam se kam 1 minute

# ── Main Loop ─────────────────────────────────────────────────────────────────

def main():
    log("=" * 60)
    log("Blog Automation Worker START")
    log(f"Script: {GENERATOR_SCRIPT}")
    log(f"Daily target: {BLOGS_PER_DAY} blogs, gap: {GAP_BETWEEN_BLOGS//3600}h")
    log("=" * 60)

    while True:
        today_str = date.today().isoformat()
        state = load_state()

        # Agar state purana hai to reset karo
        if state.get("last_date") != today_str:
            log(f"Naya din ({today_str}) - daily counter reset ho raha hai.")
            state = {
                "last_date": today_str,
                "blogs_published_today": 0,
                "status": "running"
            }
            save_state(state)

        blogs_done = state.get("blogs_published_today", 0)
        log(f"Aaj ({today_str}) ab tak {blogs_done}/{BLOGS_PER_DAY} blogs publish hue hain.")

        # Agar aaj ka target pura ho gaya
        if blogs_done >= BLOGS_PER_DAY:
            wait_secs = seconds_until_next_day_start()
            log(f"Aaj ka target ({BLOGS_PER_DAY} blogs) pura! Kal {NEXT_DAY_HOUR:02d}:{NEXT_DAY_MINUTE:02d} AM tak so raha hoon...")
            state["status"] = "completed_today"
            save_state(state)
            sleep_with_heartbeat(wait_secs, reason=f"Next day start ({NEXT_DAY_HOUR:02d}:{NEXT_DAY_MINUTE:02d} AM)")
            continue  # Loop phir chalega, naya din check hoga

        # Ek ek blog publish karo
        for blog_num in range(blogs_done + 1, BLOGS_PER_DAY + 1):
            # State update karo — running
            state["status"] = "running"
            save_state(state)

            success = run_blog_generator(blog_num)

            # Published count update karo
            state = load_state()  # dobara padho (prevent race)
            if state.get("last_date") != today_str:
                # Din badal gaya to bahar nikal jao
                break
            state["blogs_published_today"] = state.get("blogs_published_today", 0) + 1
            state["last_date"] = today_str
            state["status"] = "running"
            save_state(state)

            log(f"Progress: {state['blogs_published_today']}/{BLOGS_PER_DAY} blogs aaj k liye.")

            # Agar ye aakhri blog nahi hai to gap lo
            if blog_num < BLOGS_PER_DAY:
                sleep_with_heartbeat(
                    GAP_BETWEEN_BLOGS,
                    reason=f"Blog #{blog_num+1} k liye 2 ghante ka gap"
                )

                # Gap k baad check karo: kya aaj ka din wahi hai?
                if date.today().isoformat() != today_str:
                    log("Gap k dauran din badal gaya. Nayi cycle shuru hogi.")
                    break

        # Sab blogs ho gaye? Kal tak wait karo
        state = load_state()
        if state.get("blogs_published_today", 0) >= BLOGS_PER_DAY:
            wait_secs = seconds_until_next_day_start()
            log(f"Aaj ka target pura! Kal {NEXT_DAY_HOUR:02d}:{NEXT_DAY_MINUTE:02d} AM tak so raha hoon...")
            state["status"] = "completed_today"
            save_state(state)
            sleep_with_heartbeat(wait_secs, reason="Next day")


if __name__ == "__main__":
    main()
