"""
Blog Automation Worker - Smart Daily Runner (1 Blog / Day)
===========================================================
Ye script PC startup pe ya Windows Task Scheduler se automatically run hoti hai.

Kaam karne ka tarika:
- Din mein SIRF 1 blog publish karta hai (1 Blog Per Day)
- Jab blog publish ho jata hai, browser aur terminal window khud se band (exit) ho jate hain
- Agar aaj ka blog pehle hi publish ho chuka hai, to ye check karke foran band ho jata hai
- Agar koi fail ho, to retry karta hai (max 2 retries)
- State file (blog_scheduler_state.json) mein daily progress track hoti hai
"""

import os
import sys
import time
import subprocess
import json
from datetime import datetime, date

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE    = os.path.join(SCRIPT_DIR, "blog_automation_worker.log")
STATE_FILE  = os.path.join(SCRIPT_DIR, "blog_scheduler_state.json")
GENERATOR_SCRIPT = os.path.join(SCRIPT_DIR, "generate_trending_blog_playwright.py")

# --- Config ---
BLOGS_PER_DAY    = 1      # Ek din mein sirf 1 blog
MAX_RETRIES      = 2      # Agar fail ho to max retries
RETRY_DELAY_SEC  = 120    # 2 minute retry wait

def log(msg):
    ts  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

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

def kill_lingering_browsers():
    """Automation Chrome instances ko band karne ka helper."""
    try:
        # Netstat kill on port 9222
        output = subprocess.check_output("netstat -aon", shell=True).decode('utf-8', errors='ignore')
        for line in output.splitlines():
            if ":9222" in line and "LISTENING" in line:
                parts = line.strip().split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    try:
        # PowerShell CIM kill for any chrome with remote debugging port 9222
        ps_cmd = (
            "powershell -NoProfile -Command \""
            "Get-CimInstance Win32_Process -Filter \\\"Name = 'chrome.exe' AND CommandLine LIKE '%--remote-debugging-port=9222%'\\\" "
            "| ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }\""
        )
        subprocess.run(ps_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def run_blog_generator():
    """generate_trending_blog_playwright.py chalata hai aur result deta hai."""
    log("Daily Blog generation shuru ho raha hai...")
    try:
        result = subprocess.run(
            [sys.executable, GENERATOR_SCRIPT],
            cwd=SCRIPT_DIR,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode == 0:
            log("Daily blog successfully publish ho gaya!")
            return True
        else:
            log(f"Daily blog fail hua (return code: {result.returncode}).")
            return False
    except Exception as e:
        log(f"Daily blog run karne mein error: {e}")
        return False

def main():
    log("=" * 60)
    log("Blog Automation Worker START")
    log(f"Script: {GENERATOR_SCRIPT}")
    log(f"Daily target: {BLOGS_PER_DAY} blog per day")
    log("=" * 60)

    today_str = date.today().isoformat()
    state = load_state()

    # Agar state purane din ka hai to reset karo
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

    # Agar aaj ka 1 blog pehle hi publish ho chuka hai:
    if blogs_done >= BLOGS_PER_DAY:
        log(f"Aaj ka target ({BLOGS_PER_DAY} blog) pehle se pura ho chuka hai!")
        log("Sab kaam complete hai. Automation browser aur terminal band ho rahe hain...")
        state["status"] = "completed_today"
        save_state(state)
        kill_lingering_browsers()
        time.sleep(3)
        sys.exit(0)

    # Blog publish karne ki koshish (with retries)
    success = False
    for attempt in range(1, MAX_RETRIES + 2):
        state["status"] = "running"
        save_state(state)

        success = run_blog_generator()
        if success:
            state = load_state()
            state["blogs_published_today"] = 1
            state["last_date"] = today_str
            state["status"] = "completed_today"
            save_state(state)
            log("=" * 60)
            log(f"SUCCESS: Aaj ka daily blog publish ho gaya (1/{BLOGS_PER_DAY})!")
            log("Kaam poora ho chuka hai. Browser aur terminal window band ho rahe hain...")
            log("=" * 60)
            break
        else:
            if attempt <= MAX_RETRIES:
                log(f"Attempt {attempt} fail hua. {RETRY_DELAY_SEC} seconds baad retry karunga...")
                state["status"] = "retrying"
                save_state(state)
                time.sleep(RETRY_DELAY_SEC)
            else:
                log("All attempts failed for today's blog.")
                state["status"] = "failed"
                save_state(state)

    # Sab kuch band karo: Browser aur Terminal
    kill_lingering_browsers()
    time.sleep(3)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
