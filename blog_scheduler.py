import os
import sys
import json
import time
import subprocess
from datetime import datetime
import tkinter as tk

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(SCRIPT_DIR, "blog_scheduler_state.json")

def get_today_date():
    return datetime.now().strftime("%Y-%m-%d")

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_date": "", "status": "pending"}

def save_state(status):
    state = {"last_date": get_today_date(), "status": status}
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except Exception as e:
        print(f"Failed to save state: {e}")

def check_and_register_startup():
    startup_dir = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")
    shortcut_path = os.path.join(startup_dir, "QuizViralBlogScheduler.lnk")
    
    if os.path.exists(shortcut_path):
        return
        
    print("Registering blog scheduler in Windows Startup...")
    pythonw_exe = sys.executable.replace("python.exe", "pythonw.exe")
    script_path = os.path.abspath(__file__)
    working_dir = SCRIPT_DIR
    
    # PowerShell command to create the Startup shortcut (run minimized/hidden)
    ps_cmd = (
        f'$WshShell = New-Object -ComObject WScript.Shell; '
        f'$Shortcut = $WshShell.CreateShortcut("{shortcut_path}"); '
        f'$Shortcut.TargetPath = "{pythonw_exe}"; '
        f'$Shortcut.Arguments = "{script_path}"; '
        f'$Shortcut.WorkingDirectory = "{working_dir}"; '
        f'$Shortcut.WindowStyle = 7; '
        f'$Shortcut.Save()'
    )
    
    try:
        subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True, check=True)
        print("Successfully registered in Windows Startup!")
    except Exception as e:
        print(f"Failed to register in Windows Startup: {e}")

def run_automation_in_background():
    worker_script = os.path.join(SCRIPT_DIR, "blog_automation_worker.py")
    try:
        if sys.platform == "win32":
            # DETACHED_PROCESS flag = 0x00000008
            subprocess.Popen([sys.executable, worker_script], creationflags=0x00000008)
        else:
            subprocess.Popen([sys.executable, worker_script])
    except Exception as e:
        print(f"Failed to launch worker: {e}")

def show_popup():
    root = tk.Tk()
    root.title("QuizViral AI Blog Automation")
    
    # Center window
    window_width = 460
    window_height = 200
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    root.resizable(False, False)
    
    # Dark modern colors
    root.configure(bg="#1e1e2e")
    
    label_title = tk.Label(
        root, 
        text="Daily Blog Generation Automation", 
        font=("Segoe UI", 16, "bold"), 
        fg="#cdd6f4", 
        bg="#1e1e2e"
    )
    label_title.pack(pady=(20, 10))
    
    label_desc = tk.Label(
        root, 
        text="Would you like to start the daily blog automation?\nThis will generate 3 distinct blogs (one every 2 hours).",
        font=("Segoe UI", 10),
        fg="#a6adc8",
        bg="#1e1e2e",
        justify="center"
    )
    label_desc.pack(pady=(0, 20))
    
    def on_yes():
        save_state("completed")
        run_automation_in_background()
        root.destroy()
        
    def on_remind():
        root.destroy()
        # Sleep 1 hour, then run again
        time.sleep(3600)
        main()
        
    def on_skip():
        save_state("skipped")
        root.destroy()

    btn_frame = tk.Frame(root, bg="#1e1e2e")
    btn_frame.pack()
    
    btn_yes = tk.Button(
        btn_frame, 
        text="Yes, Start Now", 
        command=on_yes,
        font=("Segoe UI", 10, "bold"),
        fg="#1e1e2e",
        bg="#a6e3a1",  # Pastel green
        activebackground="#89b4fa",
        cursor="hand2",
        padx=12,
        pady=6,
        bd=0
    )
    btn_yes.grid(row=0, column=0, padx=10)
    
    btn_remind = tk.Button(
        btn_frame, 
        text="Remind Later", 
        command=on_remind,
        font=("Segoe UI", 10),
        fg="#1e1e2e",
        bg="#f9e2af",  # Pastel yellow
        activebackground="#f2cdcd",
        cursor="hand2",
        padx=12,
        pady=6,
        bd=0
    )
    btn_remind.grid(row=0, column=1, padx=10)
    
    btn_skip = tk.Button(
        btn_frame, 
        text="Skip Today", 
        command=on_skip,
        font=("Segoe UI", 10),
        fg="#cdd6f4",
        bg="#313244",  # Muted dark button
        activebackground="#45475a",
        cursor="hand2",
        padx=12,
        pady=6,
        bd=0
    )
    btn_skip.grid(row=0, column=2, padx=10)
    
    root.protocol("WM_DELETE_WINDOW", on_remind)
    root.mainloop()

def main():
    # Register script in Windows Startup on first execution
    check_and_register_startup()
    
    state = load_state()
    today = get_today_date()
    
    # If completed or skipped today, exit silently
    if state["last_date"] == today and state["status"] in ("completed", "skipped"):
        print(f"Blog automation for today ({today}) is already marked as {state['status']}. Exiting.")
        return
        
    show_popup()

if __name__ == "__main__":
    main()
