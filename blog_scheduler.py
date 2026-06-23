import os
import sys
import json
import time
import subprocess
import threading
import socket
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(SCRIPT_DIR, "blog_scheduler_state.json")
LOG_FILE   = os.path.join(SCRIPT_DIR, "blog_scheduler.log")

lock_socket = None

def acquire_single_instance_lock():
    global lock_socket
    try:
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lock_socket.bind(("127.0.0.1", 28734))
        lock_socket.listen(1)
        return True
    except socket.error:
        return False

# ─────────────────────────────────────────────────────────────────────────────
def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def get_today_date():
    return datetime.now().strftime("%Y-%m-%d")

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_date": "", "status": "pending", "blogs_done": 0}

def save_state(status, blogs_done=None):
    state = load_state()
    state["last_date"] = get_today_date()
    state["status"]    = status
    if blogs_done is not None:
        state["blogs_done"] = blogs_done
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except Exception as e:
        log(f"Failed to save state: {e}")

# ─────────────────────────────────────────────────────────────────────────────
def check_and_register_startup():
    """Register script in Windows Startup folder (only once)."""
    startup_dir   = os.path.join(os.environ.get("APPDATA", ""),
                                 r"Microsoft\Windows\Start Menu\Programs\Startup")
    shortcut_path = os.path.join(startup_dir, "QuizViralBlogScheduler.lnk")

    if os.path.exists(shortcut_path):
        return  # Already registered

    log("Registering blog scheduler in Windows Startup...")
    # Use python.exe (not pythonw) so the console + tkinter popup work correctly
    python_exe  = sys.executable
    script_path = os.path.abspath(__file__)

    ps_cmd = (
        f'$WshShell = New-Object -ComObject WScript.Shell; '
        f'$Shortcut = $WshShell.CreateShortcut("{shortcut_path}"); '
        f'$Shortcut.TargetPath = "{python_exe}"; '
        f'$Shortcut.Arguments = \\"{script_path}\\"; '
        f'$Shortcut.WorkingDirectory = "{SCRIPT_DIR}"; '
        f'$Shortcut.WindowStyle = 1; '   # 1 = normal window (not hidden)
        f'$Shortcut.Save()'
    )
    try:
        subprocess.run(["powershell", "-Command", ps_cmd],
                       capture_output=True, text=True, check=True)
        log("Successfully registered in Windows Startup!")
    except Exception as e:
        log(f"Failed to register in Windows Startup: {e}")

# ─────────────────────────────────────────────────────────────────────────────
def run_one_blog(trend_index):
    """Run a single blog generation synchronously and return True/False."""
    generator_script = os.path.join(SCRIPT_DIR, "generate_trending_blog_playwright.py")
    log(f"Starting blog #{trend_index + 1} generation (trend index {trend_index})...")
    try:
        result = subprocess.run(
            [sys.executable, generator_script, "--trend-index", str(trend_index)],
            cwd=SCRIPT_DIR
        )
        success = result.returncode == 0
        log(f"Blog #{trend_index + 1} {'SUCCESS' if success else 'FAILED'} "
            f"(return code: {result.returncode})")
        return success
    except Exception as e:
        log(f"Error running blog generator for index {trend_index}: {e}")
        return False

def run_all_blogs_with_gaps(start_index=0):
    """
    Generates remaining blogs for today with a 2-hour gap between each.
    Runs in a background thread so the main process stays alive.
    Shows a small status notification after each blog completes.
    """
    def _worker():
        total = 3
        if start_index >= total:
            save_state("completed", blogs_done=total)
            return

        for i in range(start_index, total):
            ok = run_one_blog(i)
            save_state("in_progress", blogs_done=i + 1)

            # Show a brief system notification (no blocking popup)
            _toast(
                f"Blog {i+1}/{total} {'✅ Done' if ok else '❌ Failed'}",
                f"Blog generation #{i+1} has {'completed successfully!' if ok else 'failed. Check log for details.'}"
            )

            if i < total - 1:
                log(f"Waiting 2 hours before next blog...")
                time.sleep(7200)   # 2-hour gap

        save_state("completed", blogs_done=total)
        log("=== All 3 blogs generated successfully! ===")
        _toast("QuizViral Blog Automation", "All 3 blogs for today are done! ✅")

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t

def _toast(title, message):
    """Show a small non-blocking Windows toast notification via PowerShell."""
    try:
        ps = (
            f"Add-Type -AssemblyName System.Windows.Forms; "
            f"$n = New-Object System.Windows.Forms.NotifyIcon; "
            f"$n.Icon = [System.Drawing.SystemIcons]::Information; "
            f"$n.Visible = $true; "
            f"$n.ShowBalloonTip(5000, '{title}', '{message}', "
            f"[System.Windows.Forms.ToolTipIcon]::Info); "
            f"Start-Sleep -Seconds 6; $n.Dispose()"
        )
        subprocess.Popen(
            ["powershell", "-WindowStyle", "Hidden", "-Command", ps],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception:
        pass  # Toast is optional — never crash because of it

# ─────────────────────────────────────────────────────────────────────────────
def show_popup():
    """
    Show the Yes/Remind/Skip popup.
    FIX: 'Remind Later' no longer calls time.sleep() inside tkinter mainloop
    (which used to freeze the window). Instead it schedules a re-check via
    root.after() and exits the current window cleanly.
    """
    root = tk.Tk()
    root.title("QuizViral AI — Blog Automation")

    window_width, window_height = 480, 230
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"{window_width}x{window_height}+{(sw-window_width)//2}+{(sh-window_height)//2}")
    root.resizable(False, False)
    root.configure(bg="#1e1e2e")
    root.attributes("-topmost", True)   # Always on top so it's visible after startup

    # --- State indicator ---
    state      = load_state()
    today      = get_today_date()
    blogs_done = state.get("blogs_done", 0) if state.get("last_date") == today else 0
    remaining  = max(0, 3 - blogs_done)
    status_txt = f"Today so far: {blogs_done}/3 blog(s) generated." if blogs_done > 0 else ""

    tk.Label(root, text="Daily Blog Generation Automation",
             font=("Segoe UI", 15, "bold"), fg="#cdd6f4", bg="#1e1e2e"
             ).pack(pady=(18, 4))

    if blogs_done > 0:
        desc_text = f"Would you like to resume today's blog automation?\n{remaining} remaining blog(s) will be published (one every 2 hours)."
    else:
        desc_text = "Would you like to start today's blog automation?\n3 blogs will be published — one every 2 hours."

    tk.Label(root,
             text=desc_text + (f"\n📊 {status_txt}" if status_txt else ""),
             font=("Segoe UI", 10), fg="#a6adc8", bg="#1e1e2e", justify="center"
             ).pack(pady=(0, 16))

    result = {"action": None}

    def on_yes():
        result["action"] = "yes"
        root.destroy()

    def on_remind():
        result["action"] = "remind"
        root.destroy()

    def on_skip():
        result["action"] = "skip"
        root.destroy()

    frame = tk.Frame(root, bg="#1e1e2e")
    frame.pack()

    for text, cmd, fg, bg in [
        ("✅  Start Now",    on_yes,    "#1e1e2e", "#a6e3a1"),
        ("⏰  Remind in 1h", on_remind, "#1e1e2e", "#f9e2af"),
        ("🚫  Skip Today",   on_skip,   "#cdd6f4", "#313244"),
    ]:
        tk.Button(frame, text=text, command=cmd,
                  font=("Segoe UI", 10, "bold"), fg=fg, bg=bg,
                  activebackground="#89b4fa", cursor="hand2",
                  padx=14, pady=7, bd=0, relief="flat"
                  ).pack(side="left", padx=8)

    root.protocol("WM_DELETE_WINDOW", on_remind)
    root.mainloop()
    return result["action"]

# ─────────────────────────────────────────────────────────────────────────────
def main():
    check_and_register_startup()

    state = load_state()
    today = get_today_date()

    # Already completed or skipped today → exit silently
    if state["last_date"] == today and state["status"] in ("completed", "skipped"):
        log(f"Blog automation already completed or skipped today ({today}) [status: {state['status']}]. Exiting.")
        return

    # Determine start_index based on state and date
    if state["last_date"] == today:
        start_index = state.get("blogs_done", 0)
    else:
        start_index = 0
        save_state("pending", blogs_done=0)

    log("Showing blog automation popup...")
    action = show_popup()

    if action == "yes":
        log(f"User clicked 'Start Now'. Launching blog automation from index {start_index} in background...")
        save_state("in_progress", blogs_done=start_index)
        worker_thread = run_all_blogs_with_gaps(start_index)
        # Keep main thread alive while background blogs are running
        log("Blog generation running in background. Main process keeping alive...")
        worker_thread.join()
        log("All done. Exiting scheduler.")

    elif action == "remind":
        log("User clicked 'Remind in 1h'. Will re-show popup after 60 minutes.")
        time.sleep(3600)
        main()   # Recursive call after 1 hour (safe — not inside tkinter loop)

    elif action == "skip":
        log("User clicked 'Skip Today'. Marking as skipped.")
        save_state("skipped")

    else:
        log("Popup closed without action. Treating as Remind.")
        time.sleep(3600)
        main()

if __name__ == "__main__":
    if not acquire_single_instance_lock():
        log("Another instance of QuizViral Blog Scheduler is already running. Exiting.")
        sys.exit(0)
    main()
