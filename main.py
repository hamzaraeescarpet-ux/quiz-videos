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

Base.metadata.create_all(bind=engine)

# Paths (Adjusted for root)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BG_DIR = os.path.join(BASE_DIR, "backgrounds")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")

os.makedirs(OUTPUT_DIR, exist_ok=True)

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
    if not os.path.exists(BG_DIR):
        return {"categories": []}
    categories = [d for d in os.listdir(BG_DIR) if os.path.isdir(os.path.join(BG_DIR, d))]
    return {"categories": categories}

from video_generator import create_video_from_row

def process_video_batch(session_id: str, questions: List[dict], category: str, logo_path: str = None):
    db = SessionLocal()
    job = db.query(VideoJob).filter(VideoJob.session_id == session_id).first()
    
    session_output_dir = os.path.join(OUTPUT_DIR, session_id)
    os.makedirs(session_output_dir, exist_ok=True)
    
    try:
        for idx, row in enumerate(questions):
            if session_id in active_sessions and active_sessions[session_id] == "stop":
                job.status = "Interrupted"
                db.commit()
                break
                
            try:
                output_file = create_video_from_row(row, category, logo_path, session_output_dir)
                if output_file:
                    job.completed_so_far += 1
                    db.commit()
            except Exception as e:
                print(f"Error processing row: {e}")
                
        if job.status != "Interrupted":
            job.status = "Completed"
            
    except Exception as e:
        job.status = "Failed"
        print(f"Batch generation failed: {e}")
        
    finally:
        zip_path = os.path.join(OUTPUT_DIR, f"{session_id}.zip")
        shutil.make_archive(zip_path.replace('.zip', ''), 'zip', session_output_dir)
        job.zip_file_path = zip_path
        db.commit()
        db.close()
        if session_id in active_sessions:
            del active_sessions[session_id]

@app.post("/api/generate-bulk")
async def generate_bulk(
    background_tasks: BackgroundTasks,
    questions: str = Form(...), 
    category: str = Form(...),
    logo: Optional[UploadFile] = File(None)
):
    questions_list = json.loads(questions)
    
    if len(questions_list) == 0:
        raise HTTPException(status_code=400, detail="No questions provided")
        
    session_id = str(uuid.uuid4())
    
    logo_path = None
    if logo and logo.filename:
        logo_path = os.path.join(ASSETS_DIR, f"logo_{session_id}_{logo.filename}")
        with open(logo_path, "wb") as f:
            f.write(await logo.read())
            
    db = SessionLocal()
    new_job = VideoJob(
        session_id=session_id,
        total_expected=len(questions_list),
        status="Processing"
    )
    db.add(new_job)
    db.commit()
    db.close()
    
    active_sessions[session_id] = "run"
    background_tasks.add_task(process_video_batch, session_id, questions_list, category, logo_path)
    
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

# Serve React Frontend (For Hugging Face Spaces & Production)
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="frontend-assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        index_path = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index_path):
            return HTMLResponse(content=open(index_path, "r", encoding="utf-8").read())
        return {"message": "Frontend build not found."}
