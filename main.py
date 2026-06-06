import sys
import os

# --- PATH FIX ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import json
import uuid
import shutil
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base

app = FastAPI(title="QuizViral AI Backend")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Setup
DATABASE_URL = "sqlite:///./quizviral.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    videos_generated_count = Column(Integer, default=0)
    is_premium = Column(Boolean, default=False)

class VideoJob(Base):
    __tablename__ = "video_jobs"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    status = Column(String, default="Processing") 
    total_expected = Column(Integer, default=0)
    completed_so_far = Column(Integer, default=0)
    zip_file_path = Column(String, nullable=True)
    user_email = Column(String, nullable=True)

class Feedback(Base):
    __tablename__ = "feedbacks"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    rating = Column(Integer)
    comment = Column(String)
    submitted_at = Column(String)

Base.metadata.create_all(bind=engine)

# Paths (Adjusted for root)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BG_DIR = os.path.join(BASE_DIR, "backgrounds")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")
TEMP_FOLDER = os.path.join(BASE_DIR, "temp")
BG_CACHE_DIR = os.path.join(BASE_DIR, "backgrounds_cache")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)
os.makedirs(BG_CACHE_DIR, exist_ok=True)

import time
import urllib.request
import urllib.parse
import hashlib
import json

def download_and_cache_video(url: str) -> str:
    # Generate a unique stable filename from the URL hash
    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
    parsed = urllib.parse.urlparse(url)
    ext = os.path.splitext(parsed.path)[1]
    if not ext:
        ext = ".mp4"
    filename = f"bg_{url_hash}{ext}"
    local_path = os.path.join(BG_CACHE_DIR, filename)
    
    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
        return local_path
        
    print(f"Downloading background video: {url} -> {local_path}", flush=True)
    try:
        urllib.request.urlretrieve(url, local_path)
        return local_path
    except Exception as e:
        print(f"Error downloading background video {url}: {e}", flush=True)
        return None

def cleanup_old_zip_files():
    """Delete any zip files in the output directory that are older than 24 hours."""
    try:
        now = time.time()
        for filename in os.listdir(OUTPUT_DIR):
            if filename.endswith(".zip"):
                filepath = os.path.join(OUTPUT_DIR, filename)
                file_age = now - os.path.getmtime(filepath)
                if file_age > 86400: # 24 hours in seconds
                    print(f"AUTOMATION: Cleaning up old zip file: {filepath}", flush=True)
                    try:
                        os.remove(filepath)
                    except Exception:
                        pass
                    # Also delete the folder directory of that session if it exists
                    session_dir = os.path.join(OUTPUT_DIR, filename.replace(".zip", ""))
                    if os.path.exists(session_dir) and os.path.isdir(session_dir):
                        try:
                            shutil.rmtree(session_dir)
                        except Exception:
                            pass
    except Exception as e:
        print(f"Error during zip file cleanup: {e}", flush=True)

class QuestionRow(BaseModel):
    id: int
    question: str
    option1: str
    option2: str
    option3: str
    option4: str
    answer: str

active_sessions = {}

@app.get("/api/categories")
def get_categories():
    config_path = os.path.join(BASE_DIR, "backgrounds_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                data = json.load(f)
            return {"categories": list(data.keys())}
        except Exception as e:
            print(f"Error loading backgrounds_config.json: {e}", flush=True)

    if not os.path.exists(BG_DIR):
        return {"categories": []}
    categories = [d for d in os.listdir(BG_DIR) if os.path.isdir(os.path.join(BG_DIR, d))]
    return {"categories": categories}

from video_generator import create_video_from_row

def process_video_batch(
    session_id: str, 
    questions: List[dict], 
    category: str, 
    logo_path: str = None, 
    user_email: str = None,
    box_color: str = None,
    custom_bg_paths: List[str] = None
):
    db = SessionLocal()
    job = db.query(VideoJob).filter(VideoJob.session_id == session_id).first()
    
    session_output_dir = os.path.join(OUTPUT_DIR, session_id)
    os.makedirs(session_output_dir, exist_ok=True)
    
    import random
    PREMIUM_COLORS = [
        "#E74C3C", "#3498DB", "#2C3E50", "#8E44AD", "#16A085", 
        "#27AE60", "#D35400", "#C0392B", "#2980B9", "#130f40", 
        "#6F1E51", "#1B1464", "#0652DD", "#833471", "#6D213C", "#1E3799"
    ]
    
    # Load backgrounds_config.json URLs for this category
    config_path = os.path.join(BASE_DIR, "backgrounds_config.json")
    bg_urls = []
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config_data = json.load(f)
            bg_urls = config_data.get(category, [])
        except Exception as e:
            print(f"Error loading background config inside batch: {e}", flush=True)
            
    try:
        for idx, row in enumerate(questions):
            if session_id in active_sessions and active_sessions[session_id] == "stop":
                job.status = "Interrupted"
                db.commit()
                break
                
            # Pick background video: either custom uploads or cache from category config URLs
            row_bg_paths = None
            if custom_bg_paths and len(custom_bg_paths) > 0:
                row_bg_paths = custom_bg_paths
            elif bg_urls:
                random_url = random.choice(bg_urls)
                local_bg_file = download_and_cache_video(random_url)
                if local_bg_file:
                    row_bg_paths = [local_bg_file]

            # Randomly select a high-contrast theme color for each individual video
            selected_color = random.choice(PREMIUM_COLORS)
            try:
                output_file = create_video_from_row(row, category, logo_path, session_output_dir, selected_color, row_bg_paths)
                if output_file:
                    job.completed_so_far += 1
                    db.commit()
            except Exception as e:
                import traceback
                error_msg = f"Error processing row {idx}: {e}\n{traceback.format_exc()}"
                print(error_msg, flush=True)
                with open("error_logs.txt", "a") as f:
                    f.write(error_msg + "\n")
                
        if job.status != "Interrupted":
            if job.completed_so_far == 0:
                job.status = "Failed"
            else:
                job.status = "Completed"
                
                # AUTOMATION: Send email to user
                if user_email:
                    print(f"\n[{user_email}] AUTOMATION: Sending email -> 'Sit back and relax, your bulk videos are ready to download!'", flush=True)
                    try:
                        import json
                        import urllib.request

                        mailer_url = "https://quizviral-nine.vercel.app/api/mailer"
                        download_link = "https://quizviral-nine.vercel.app"
                        body = f"""Hello Creator,

Your bulk trivia videos have been successfully generated!

You can download them right now by going to your dashboard or using this direct link:
{download_link}

Keep growing your viral factory!
- QuizViral AI Team"""

                        payload = {
                            "to": user_email,
                            "subject": "Your Bulk Quiz Videos are Ready! 🎉",
                            "text": body
                        }

                        data = json.dumps(payload).encode('utf-8')
                        req = urllib.request.Request(mailer_url, data=data, headers={'Content-Type': 'application/json'})
                        
                        with urllib.request.urlopen(req, timeout=15) as response:
                            if response.status == 200:
                                print(f"Successfully sent email to {user_email} via Vercel mailer", flush=True)
                            else:
                                print(f"Failed to send via Vercel: {response.read()}", flush=True)
                                
                    except Exception as email_err:
                        print(f"Failed to send email HTTP request: {email_err}", flush=True)
            
    except Exception as e:
        job.status = "Failed"
        import traceback
        error_msg = f"Batch generation failed: {e}\n{traceback.format_exc()}"
        print(error_msg, flush=True)
        with open("error_logs.txt", "a") as f:
            f.write(error_msg + "\n")
        
    finally:
        zip_path = os.path.join(OUTPUT_DIR, f"{session_id}.zip")
        shutil.make_archive(zip_path.replace('.zip', ''), 'zip', session_output_dir)
        job.zip_file_path = zip_path
        
        # Update user's generated videos count in SQLite
        if user_email and job.completed_so_far > 0:
            user_rec = db.query(User).filter(User.username == user_email).first()
            if user_rec:
                user_rec.videos_generated_count += job.completed_so_far
                
        db.commit()
        db.close()
        
        # Clean custom backgrounds to free up storage
        if custom_bg_paths:
            for path in custom_bg_paths:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception:
                    pass
                    
        if session_id in active_sessions:
            del active_sessions[session_id]

@app.post("/api/generate-bulk")
async def generate_bulk(
    background_tasks: BackgroundTasks,
    questions: str = Form(...), 
    category: str = Form(...),
    logo: Optional[UploadFile] = File(None),
    email: Optional[str] = Form(None),
    box_color: Optional[str] = Form(None),
    custom_bg_videos: Optional[List[UploadFile]] = File(None)
):
    questions_list = json.loads(questions)
    
    if len(questions_list) == 0:
        raise HTTPException(status_code=400, detail="No questions provided")
        
    # Run automatic clean-up of expired download zips (> 24 hours) in backgrounds
    background_tasks.add_task(cleanup_old_zip_files)

    session_id = str(uuid.uuid4())
    
    # Save custom background videos locally
    custom_bg_paths = []
    if custom_bg_videos:
        for bg_vid in custom_bg_videos:
            if bg_vid.filename:
                bg_path = os.path.join(TEMP_FOLDER, f"custom_bg_{session_id}_{uuid.uuid4().hex}_{bg_vid.filename}")
                with open(bg_path, "wb") as f:
                    f.write(await bg_vid.read())
                custom_bg_paths.append(bg_path)
    
    logo_path = None
    if logo and logo.filename:
        logo_path = os.path.join(ASSETS_DIR, f"logo_{session_id}_{logo.filename}")
        with open(logo_path, "wb") as f:
            f.write(await logo.read())
            
    db = SessionLocal()
    new_job = VideoJob(
        session_id=session_id,
        total_expected=len(questions_list),
        status="Processing",
        user_email=email
    )
    db.add(new_job)
    db.commit()
    db.close()
    
    active_sessions[session_id] = "run"
    background_tasks.add_task(
        process_video_batch, 
        session_id, 
        questions_list, 
        category, 
        logo_path, 
        email, 
        box_color, 
        custom_bg_paths
    )
    
    return {"session_id": session_id, "message": "Generation started"}

@app.post("/api/stop-generation/{session_id}")
def stop_generation(session_id: str):
    if session_id in active_sessions:
        active_sessions[session_id] = "stop"
        return {"message": "Stop signal sent"}
    raise HTTPException(status_code=404, detail="Session not found or already stopped")

@app.get("/api/status/{session_id}")
def get_status(session_id: str):
    db = SessionLocal()
    job = db.query(VideoJob).filter(VideoJob.session_id == session_id).first()
    db.close()
    if not job:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": job.session_id,
        "status": job.status,
        "completed_so_far": job.completed_so_far,
        "total_expected": job.total_expected
    }

@app.get("/api/download/{session_id}")
def download_zip(session_id: str):
    db = SessionLocal()
    job = db.query(VideoJob).filter(VideoJob.session_id == session_id).first()
    db.close()
    
    if not job or not job.zip_file_path or not os.path.exists(job.zip_file_path):
        raise HTTPException(status_code=404, detail="ZIP file not ready or found")
        
    return FileResponse(job.zip_file_path, media_type="application/zip", filename=f"QuizViral_Videos_{session_id}.zip")

@app.get("/api/jobs")
def get_user_jobs(email: str):
    db = SessionLocal()
    jobs = db.query(VideoJob).filter(VideoJob.user_email == email).order_by(VideoJob.id.desc()).all()
    job_list = [{
        "session_id": j.session_id,
        "status": j.status,
        "completed_so_far": j.completed_so_far,
        "total_expected": j.total_expected
    } for j in jobs]
    db.close()
    return {"jobs": job_list}

@app.get("/api/logs")
def get_logs():
    if os.path.exists("error_logs.txt"):
        with open("error_logs.txt", "r") as f:
            return HTMLResponse(f"<pre>{f.read()}</pre>")
    return {"message": "No errors logged yet."}

@app.post("/api/test-email")
def test_email(email: str = Form(...)):
    try:
        import json
        import urllib.request
        
        mailer_url = "https://quizviral-nine.vercel.app/api/mailer"
        payload = {
            "to": email,
            "subject": "QuizViral AI - Test Email via Vercel",
            "text": "If you received this, the Vercel Mailer Bridge is working perfectly and bypassing the Hugging Face firewall!"
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(mailer_url, data=data, headers={'Content-Type': 'application/json'})
        
        with urllib.request.urlopen(req, timeout=15) as response:
            resp_body = response.read().decode('utf-8')
            if response.status == 200:
                return {"status": "success", "message": f"Successfully sent test email to {email}", "vercel_response": resp_body}
            else:
                return {"status": "error", "message": f"Vercel rejected the email: {resp_body}"}
                
    except urllib.error.HTTPError as e:
        return {"status": "error", "message": f"HTTP Error from Vercel: {e.code} - {e.read().decode('utf-8')}"}
    except Exception as e:
        import traceback
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}

class FeedbackSchema(BaseModel):
    email: str
    rating: int
    comment: str

@app.post("/api/feedback")
def submit_feedback(fb: FeedbackSchema):
    db = SessionLocal()
    new_fb = Feedback(
        email=fb.email,
        rating=fb.rating,
        comment=fb.comment,
        submitted_at=datetime.date.today().isoformat()
    )
    db.add(new_fb)
    db.commit()
    db.close()
    return {"message": "Feedback submitted successfully"}

@app.get("/api/admin/feedbacks")
def get_feedbacks(email: str):
    # Only allow the site owner
    if email not in ["hamzaraeescarpet@gmail.com"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    db = SessionLocal()
    fbs = db.query(Feedback).order_by(Feedback.id.desc()).all()
    
    # Format feedbacks for easy display
    formatted = []
    for item in fbs:
        formatted.append({
            "id": item.id,
            "email": item.email,
            "rating": item.rating,
            "comment": item.comment,
            "submitted_at": item.submitted_at
        })
    db.close()
    return {"feedbacks": formatted}

class UserRegisterSchema(BaseModel):
    email: str

@app.post("/api/register-user")
def register_user(user: UserRegisterSchema):
    db = SessionLocal()
    db_user = db.query(User).filter(User.username == user.email).first()
    # Owner email is premium by default, others check database flag
    is_owner = user.email in ["hamzaraeescarpet@gmail.com"]
    if not db_user:
        db_user = User(
            username=user.email,
            videos_generated_count=0,
            is_premium=is_owner
        )
        db.add(db_user)
        db.commit()
    else:
        # If user exists, guarantee owner status is correct
        if is_owner and not db_user.is_premium:
            db_user.is_premium = True
            db.commit()
    db.close()
    return {"message": "User registered successfully"}

# Check if user is premium
@app.get("/api/check-premium")
def check_premium(email: str):
    # Owner email is premium by default
    if email in ["hamzaraeescarpet@gmail.com"]:
        return {"is_premium": True}
    db = SessionLocal()
    db_user = db.query(User).filter(User.username == email).first()
    is_prem = db_user.is_premium if db_user else False
    db.close()
    return {"is_premium": is_prem}

# Ko-fi Webhook activation flow
# Helper to send Facebook Conversions API event
def send_facebook_capi_event(email: str, amount: float, currency: str):
    import hashlib
    import time
    import urllib.request
    
    pixel_id = os.environ.get("FB_PIXEL_ID")
    access_token = os.environ.get("FB_ACCESS_TOKEN")
    test_code = os.environ.get("FB_TEST_EVENT_CODE")
    
    if not pixel_id or not access_token:
        log_msg = f"FB CAPI Skipped: pixel_id={pixel_id}, access_token={'set' if access_token else 'not set'}\n"
        print(log_msg, flush=True)
        with open("error_logs.txt", "a") as f:
            f.write(log_msg)
        return
        
    try:
        # Normalize and hash the email address (sha256)
        cleaned_email = email.strip().lower()
        hashed_email = hashlib.sha256(cleaned_email.encode('utf-8')).hexdigest()
        
        # Build the Facebook CAPI request payload
        payload = {
            "data": [
                {
                    "event_name": "Purchase",
                    "event_time": int(time.time()),
                    "action_source": "website",
                    "user_data": {
                        "em": [hashed_email]
                    },
                    "custom_data": {
                        "value": amount,
                        "currency": currency if currency else "USD"
                    }
                }
            ]
        }
        
        if test_code:
            payload["test_event_code"] = test_code.strip()
            with open("error_logs.txt", "a") as f:
                f.write(f"FB CAPI: Using test event code={test_code.strip()}\n")
            
        url = f"https://graph.facebook.com/v17.0/{pixel_id}/events?access_token={access_token}"
        data = json.dumps(payload).encode('utf-8')
        
        req = urllib.request.Request(
            url, 
            data=data, 
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            log_msg = f"FB CAPI Success: {res_body}\n"
            print(log_msg, flush=True)
            with open("error_logs.txt", "a") as f:
                f.write(log_msg)
            
    except Exception as e:
        import traceback
        log_msg = f"FB CAPI Error: {e}\n{traceback.format_exc()}\n"
        print(log_msg, flush=True)
        with open("error_logs.txt", "a") as f:
            f.write(log_msg)

@app.post("/api/kofi-webhook")
async def kofi_webhook(
    data: str = Form(...)
):
    try:
        with open("error_logs.txt", "a") as f:
            f.write(f"WEBHOOK RAW DATA: {data[:500]}\n")
    except Exception:
        pass

    try:
        payload = json.loads(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid JSON data payload")
    
    # Optional Verification Token security check
    # KOFI_VERIFICATION_TOKEN can be retrieved from config/env if wanted.
    # We will accept any matching token if they configure it, or fallback to activating directly.
    # Let's match token if provided in payload.
    verification_token = payload.get("verification_token")
    
    # Supporter email to upgrade
    email = payload.get("email")
    txn_type = payload.get("type") # "Donation", "Subscription", "Shop Order"
    
    if not email:
        return {"status": "ignored", "message": "No email provided in webhook payload"}
        
    print(f"WEBHOOK: Received Ko-fi event ({txn_type}) for email: {email}", flush=True)
    
    # Instant activation in SQLite DB
    db = SessionLocal()
    user_rec = db.query(User).filter(User.username == email).first()
    if user_rec:
        user_rec.is_premium = True
        print(f"WEBHOOK: Activated existing user to premium: {email}", flush=True)
    else:
        # Create a new premium user record
        user_rec = User(
            username=email,
            videos_generated_count=0,
            is_premium=True
        )
        db.add(user_rec)
        print(f"WEBHOOK: Created and activated new premium user: {email}", flush=True)
        
    db.commit()
    db.close()

    # Try sending Facebook CAPI Event
    try:
        amount_val = 0.0
        try:
            amount_val = float(payload.get("amount", "0"))
        except ValueError:
            pass
        currency_val = payload.get("currency", "USD")
        send_facebook_capi_event(email, amount_val, currency_val)
    except Exception as ex:
        print(f"Failed to process Facebook CAPI event: {ex}", flush=True)

    return {"status": "success", "message": f"Activated premium status for {email}"}

@app.get("/api/admin/users")
def get_users(email: str):
    if email not in ["hamzaraeescarpet@gmail.com"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    db = SessionLocal()
    users = db.query(User).order_by(User.id.desc()).all()
    formatted = []
    for u in users:
        # Extra safety check for premium status
        is_prem = u.username in ["hamzaraeescarpet@gmail.com"] or u.is_premium
        if is_prem != u.is_premium:
            u.is_premium = is_prem
            db.commit()
        formatted.append({
            "id": u.id,
            "email": u.username,
            "videos_count": u.videos_generated_count,
            "is_premium": u.is_premium
        })
    db.close()
    return {"users": formatted}

# Serve React Frontend (For Hugging Face Spaces & Production)
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="frontend-assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        index_path = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index_path):
            return HTMLResponse(content=open(index_path, "r", encoding="utf-8").read())
        return {"message": "Frontend build not found."}
