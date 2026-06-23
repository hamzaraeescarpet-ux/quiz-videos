import os
import time
import subprocess
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, "blog_automation_worker.log")
GENERATOR_SCRIPT = os.path.join(SCRIPT_DIR, "generate_trending_blog_playwright.py")

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}\n"
    print(log_line, end="")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception:
        pass

def run_blog_generator(index):
    log_message(f"Starting blog generation for trend index {index}...")
    try:
        cmd = ["python", GENERATOR_SCRIPT, "--trend-index", str(index)]
        result = subprocess.run(cmd, cwd=SCRIPT_DIR, capture_output=True, text=True, encoding="utf-8")
        
        if result.stdout:
            log_message(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            log_message(f"STDERR:\n{result.stderr}")
            
        if result.returncode == 0:
            log_message(f"Successfully finished blog generation for trend index {index}.")
            return True
        else:
            log_message(f"Blog generator failed for trend index {index} with return code {result.returncode}.")
            return False
    except Exception as e:
        log_message(f"Error running blog generator for index {index}: {e}")
        return False

def main():
    log_message("=== Starting Daily Blog Automation Task (3 Blogs, 2-hour interval) ===")
    
    # 1st Blog
    run_blog_generator(0)
    
    # Sleep 2 hours (7200 seconds)
    log_message("Sleeping for 2 hours before generating the 2nd blog...")
    time.sleep(7200)
    
    # 2nd Blog
    run_blog_generator(1)
    
    # Sleep 2 hours (7200 seconds)
    log_message("Sleeping for 2 hours before generating the 3rd blog...")
    time.sleep(7200)
    
    # 3rd Blog
    run_blog_generator(2)
    
    log_message("=== Daily Blog Automation Task Completed successfully ===")

if __name__ == "__main__":
    main()
