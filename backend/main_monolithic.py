from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
import aiofiles
from typing import Optional
import os
from pathlib import Path
import subprocess
import shutil
import threading
import time
from datetime import datetime
from sqlalchemy.orm import Session
import json

# Database imports
from database import get_db, init_db
from models import Video, Annotation, Job

# Create the FastAPI application
app = FastAPI(title="Video Annotation Backend")

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()
    print("✅ Database initialized!")

# Allow frontend to connect (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration - video directory path
VIDEO_DIR = "../test_videos"  # Path to your videos folder

# Global dictionary to track extraction progress
extraction_progress = {}

# Helper function to check if file is a video
def is_video_file(filename: str) -> bool:
    """Check if file has a video extension - NOW SUPPORTS MORE FORMATS!"""
    video_extensions = [
        '.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm',
        '.m4v', '.mpg', '.mpeg', '.3gp', '.ts', '.mts'
    ]
    return any(filename.lower().endswith(ext) for ext in video_extensions)

# ===== ENDPOINTS START HERE =====

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "Video Annotation Backend is running!",
        "status": "online",
        "version": "0.3.0 - PostgreSQL Edition"
    }

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Endpoint to list all videos
@app.get("/api/videos")
def list_videos(db: Session = Depends(get_db)):
    """
    List all video files in the video directory
    Returns: List of video files with metadata
    """
    try:
        # Check if directory exists
        if not os.path.exists(VIDEO_DIR):
            raise HTTPException(status_code=404, detail=f"Video directory not found: {VIDEO_DIR}")
        
        # Get all files in directory
        all_files = os.listdir(VIDEO_DIR)
        
        # Filter only video files
        video_files = [f for f in all_files if is_video_file(f)]
        
        # Get detailed info for each video
        videos = []
        for filename in video_files:
            filepath = os.path.join(VIDEO_DIR, filename)
            file_stats = os.stat(filepath)
            
            # Check if video exists in database
            db_video = db.query(Video).filter(Video.filename == filename).first()
            
            # If not in DB, add it
            if not db_video:
                db_video = Video(
                    filename=filename,
                    filepath=filepath,
                    size_bytes=file_stats.st_size,
                    size_mb=round(file_stats.st_size / (1024 * 1024), 2)
                )
                db.add(db_video)
                db.commit()
                db.refresh(db_video)
            
            # Get annotation count from database
            annotation_count = db.query(Annotation).filter(Annotation.video_id == db_video.id).count()
            
            videos.append({
                "filename": filename,
                "path": filepath,
                "size_bytes": file_stats.st_size,
                "size_mb": round(file_stats.st_size / (1024 * 1024), 2),
                "modified": file_stats.st_mtime,
                "annotation_count": annotation_count
            })
        
        return {
            "count": len(videos),
            "videos": videos,
            "directory": VIDEO_DIR
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to stream video file
@app.get("/api/stream/{filename}")
async def stream_video(filename: str, request: Request):
    """
    Stream a video file with range request support for large files
    """
    filepath = os.path.join(VIDEO_DIR, filename)
    
    # Check if file exists
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Video not found: {filename}")
    
    # Check if it's a video file
    if not is_video_file(filename):
        raise HTTPException(status_code=400, detail=f"File is not a video: {filename}")
    
    # Get file size
    file_size = os.path.getsize(filepath)
    
    # Get range header from request
    range_header = request.headers.get('range')
    
    # Parse range
    start = 0
    end = file_size - 1
    
    if range_header:
        # Range format: "bytes=start-end"
        range_value = range_header.replace("bytes=", "")
        if "-" in range_value:
            parts = range_value.split("-")
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if parts[1] else file_size - 1
    
    # Calculate content length
    content_length = end - start + 1
    
    # Stream the file chunk
    async def file_chunk_generator():
        async with aiofiles.open(filepath, mode='rb') as video_file:
            await video_file.seek(start)
            remaining = content_length
            chunk_size = 1024 * 1024  # 1MB chunks
            
            while remaining > 0:
                read_size = min(chunk_size, remaining)
                data = await video_file.read(read_size)
                if not data:
                    break
                remaining -= len(data)
                yield data
    
    # Set headers
    headers = {
        'Content-Range': f'bytes {start}-{end}/{file_size}',
        'Accept-Ranges': 'bytes',
        'Content-Length': str(content_length),
        'Content-Type': 'video/mp4',
    }
    
    # Return 206 Partial Content if range request, otherwise 200
    status_code = 206 if range_header else 200
    
    return StreamingResponse(
        file_chunk_generator(),
        status_code=status_code,
        headers=headers,
        media_type='video/mp4'
    )

# ASYNC FRAME EXTRACTION
@app.post("/api/extract-frames/{filename}")
async def extract_frames(filename: str, fps: int = 5, quality: int = 2, db: Session = Depends(get_db)):
    """
    Start asynchronous frame extraction
    Returns immediately with a task ID
    
    Args:
        filename: Video filename
        fps: Frames per second to extract (default: 5)
        quality: JPEG quality 1-31, lower is better (default: 2)
    """
    video_path = os.path.join(VIDEO_DIR, filename)
    
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video not found")
    
    video_name = os.path.splitext(filename)[0]
    
    # Check if extraction is already running
    if video_name in extraction_progress:
        if extraction_progress[video_name]['status'] == 'running':
            return {
                "message": "Extraction already in progress",
                "progress": extraction_progress[video_name]
            }
    
    # Initialize progress tracking
    task_id = f"{video_name}_{int(time.time())}"
    extraction_progress[video_name] = {
        "task_id": task_id,
        "status": "running",
        "progress": 0,
        "total_frames": 0,
        "extracted_frames": 0,
        "started_at": datetime.now().isoformat(),
        "message": "Starting frame extraction..."
    }
    
    # Start extraction in background thread
    thread = threading.Thread(
        target=extract_frames_background,
        args=(filename, fps, quality, video_name)
    )
    thread.daemon = True
    thread.start()
    
    return {
        "success": True,
        "message": "Frame extraction started in background",
        "task_id": task_id,
        "video_name": video_name
    }


def extract_frames_background(filename: str, fps: int, quality: int, video_name: str):
    """
    Background thread function for frame extraction
    """
    try:
        video_path = os.path.join(VIDEO_DIR, filename)
        frames_dir = os.path.join(VIDEO_DIR, f"{video_name}_frames")
        
        extraction_progress[video_name]['message'] = "Preparing directories..."
        extraction_progress[video_name]['progress'] = 5
        
        if os.path.exists(frames_dir):
            shutil.rmtree(frames_dir)
        
        os.makedirs(frames_dir)
        
        output_pattern = os.path.join(frames_dir, "frame_%04d.jpg")
        
        extraction_progress[video_name]['message'] = "Extracting frames with FFmpeg..."
        extraction_progress[video_name]['progress'] = 10
        
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', f'fps={fps}',
            '-q:v', str(quality),
            output_pattern,
            '-y'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            extraction_progress[video_name]['status'] = 'failed'
            extraction_progress[video_name]['message'] = f"FFmpeg error: {result.stderr[:200]}"
            extraction_progress[video_name]['progress'] = 0
            return
        
        extraction_progress[video_name]['progress'] = 90
        extraction_progress[video_name]['message'] = "Counting frames..."
        
        frames = [f for f in os.listdir(frames_dir) if f.endswith('.jpg')]
        frames.sort()
        
        extraction_progress[video_name]['status'] = 'completed'
        extraction_progress[video_name]['progress'] = 100
        extraction_progress[video_name]['total_frames'] = len(frames)
        extraction_progress[video_name]['extracted_frames'] = len(frames)
        extraction_progress[video_name]['message'] = f"Successfully extracted {len(frames)} frames"
        extraction_progress[video_name]['completed_at'] = datetime.now().isoformat()
        
    except Exception as e:
        extraction_progress[video_name]['status'] = 'failed'
        extraction_progress[video_name]['message'] = str(e)
        extraction_progress[video_name]['progress'] = 0


@app.get("/api/extract-frames/{video_name}/progress")
def get_extraction_progress(video_name: str):
    """Get the progress of frame extraction"""
    if video_name not in extraction_progress:
        return {
            "status": "not_started",
            "progress": 0,
            "message": "No extraction in progress"
        }
    
    return extraction_progress[video_name]


@app.get("/api/frames/{video_name}")
def list_frames(video_name: str):
    """List all extracted frames for a video"""
    frames_dir = os.path.join(VIDEO_DIR, f"{video_name}_frames")
    
    if not os.path.exists(frames_dir):
        raise HTTPException(status_code=404, detail="Frames not extracted yet")
    
    frames = [f for f in os.listdir(frames_dir) if f.endswith('.jpg')]
    frames.sort()
    
    return {
        "video": video_name,
        "frame_count": len(frames),
        "frames": frames,
        "frames_dir": frames_dir
    }


@app.get("/api/frame-image/{video_name}/{frame_filename}")
async def get_frame_image(video_name: str, frame_filename: str):
    """Serve a specific frame image"""
    frames_dir = os.path.join(VIDEO_DIR, f"{video_name}_frames")
    frame_path = os.path.join(frames_dir, frame_filename)
    
    if not os.path.exists(frame_path):
        raise HTTPException(status_code=404, detail="Frame not found")
    
    return FileResponse(frame_path, media_type="image/jpeg")

# POSTGRESQL ANNOTATIONS - NEW!
@app.post("/api/annotations/{video_name}")
async def save_annotations(video_name: str, annotations: dict, db: Session = Depends(get_db)):
    """
    Save annotations for a video to PostgreSQL
    """
    try:
        # Get or create video record
        video_filename = f"{video_name}.mp4"  # Assume .mp4, adjust if needed
        db_video = db.query(Video).filter(Video.filename == video_filename).first()
        
        if not db_video:
            # Create video record if it doesn't exist
            video_path = os.path.join(VIDEO_DIR, video_filename)
            if os.path.exists(video_path):
                file_stats = os.stat(video_path)
                db_video = Video(
                    filename=video_filename,
                    filepath=video_path,
                    size_bytes=file_stats.st_size,
                    size_mb=round(file_stats.st_size / (1024 * 1024), 2)
                )
                db.add(db_video)
                db.commit()
                db.refresh(db_video)
            else:
                raise HTTPException(status_code=404, detail="Video not found")
        
        # Delete existing annotations for this video
        db.query(Annotation).filter(Annotation.video_id == db_video.id).delete()
        
        # Save new annotations
        total_annotations = 0
        for frame_idx, boxes in annotations.items():
            frame_idx = int(frame_idx)
            
            for box in boxes:
                annotation = Annotation(
                    video_id=db_video.id,
                    frame_index=frame_idx,
                    annotation_type=box.get('type', 'box'),
                    data=box
                )
                db.add(annotation)
                total_annotations += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": "Annotations saved to database",
            "annotation_count": total_annotations
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/annotations/{video_name}")
def load_annotations(video_name: str, db: Session = Depends(get_db)):
    """
    Load annotations for a video from PostgreSQL
    """
    try:
        # Find video
        video_filename = f"{video_name}.mp4"
        db_video = db.query(Video).filter(Video.filename == video_filename).first()
        
        if not db_video:
            return {"annotations": {}, "message": "No annotations found"}
        
        # Load annotations
        db_annotations = db.query(Annotation).filter(Annotation.video_id == db_video.id).all()
        
        # Convert to frontend format
        annotations = {}
        for ann in db_annotations:
            frame_idx = str(ann.frame_index)
            if frame_idx not in annotations:
                annotations[frame_idx] = []
            annotations[frame_idx].append(ann.data)
        
        return {
            "annotations": annotations,
            "annotation_count": len(db_annotations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/annotations/{video_name}/export")
def export_annotations(video_name: str, format: str = "json", db: Session = Depends(get_db)):
    """Export annotations in different formats"""
    try:
        video_filename = f"{video_name}.mp4"
        db_video = db.query(Video).filter(Video.filename == video_filename).first()
        
        if not db_video:
            raise HTTPException(status_code=404, detail="No annotations found")
        
        db_annotations = db.query(Annotation).filter(Annotation.video_id == db_video.id).all()
        
        if format == "json":
            # Convert to JSON format
            annotations = {}
            for ann in db_annotations:
                frame_idx = str(ann.frame_index)
                if frame_idx not in annotations:
                    annotations[frame_idx] = []
                annotations[frame_idx].append(ann.data)
            
            # Save to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                json.dump(annotations, f, indent=2)
                temp_path = f.name
            
            return FileResponse(
                temp_path,
                media_type="application/json",
                filename=f"{video_name}_annotations.json"
            )
        
        elif format == "coco":
            # Convert to COCO format
            coco_format = {
                "images": [],
                "annotations": [],
                "categories": [{"id": 1, "name": "object"}]
            }
            
            annotation_id = 1
            frames = {}
            
            for ann in db_annotations:
                if ann.frame_index not in frames:
                    frames[ann.frame_index] = True
                    coco_format["images"].append({
                        "id": ann.frame_index,
                        "file_name": f"frame_{ann.frame_index:04d}.jpg",
                        "width": 1920,
                        "height": 1080
                    })
                
                if ann.annotation_type == 'box':
                    coco_format["annotations"].append({
                        "id": annotation_id,
                        "image_id": ann.frame_index,
                        "category_id": 1,
                        "bbox": [ann.data["x"], ann.data["y"], ann.data["width"], ann.data["height"]],
                        "area": ann.data["width"] * ann.data["height"],
                        "iscrowd": 0
                    })
                    annotation_id += 1
            
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                json.dump(coco_format, f, indent=2)
                temp_path = f.name
            
            return FileResponse(
                temp_path,
                media_type="application/json",
                filename=f"{video_name}_coco.json"
            )
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GPU Monitoring (unchanged)
try:
    import pynvml
    GPU_AVAILABLE = True
    pynvml.nvmlInit()
except:
    GPU_AVAILABLE = False
    print("Warning: NVIDIA GPU monitoring not available")


@app.get("/api/gpu/status")
def get_gpu_status():
    """Get status of all GPUs"""
    if not GPU_AVAILABLE:
        return {
            "available": False,
            "message": "GPU monitoring not available on this system",
            "gpus": []
        }
    
    try:
        device_count = pynvml.nvmlDeviceGetCount()
        gpus = []
        
        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            name = pynvml.nvmlDeviceGetName(handle)
            
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            memory_total = mem_info.total / (1024 ** 3)
            memory_used = mem_info.used / (1024 ** 3)
            memory_free = mem_info.free / (1024 ** 3)
            
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            gpu_util = util.gpu
            
            try:
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            except:
                temp = 0
            
            try:
                procs = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
                process_count = len(procs)
            except:
                process_count = 0
            
            gpus.append({
                "id": i,
                "name": name,
                "memory_total_gb": round(memory_total, 2),
                "memory_used_gb": round(memory_used, 2),
                "memory_free_gb": round(memory_free, 2),
                "memory_usage_percent": round((memory_used / memory_total) * 100, 1),
                "gpu_utilization_percent": gpu_util,
                "temperature_c": temp,
                "process_count": process_count,
                "available": gpu_util < 80 and memory_used < memory_total * 0.9
            })
        
        return {
            "available": True,
            "gpu_count": device_count,
            "gpus": gpus
        }
        
    except Exception as e:
        return {
            "available": False,
            "message": f"Error reading GPU status: {str(e)}",
            "gpus": []
        }


# POSTGRESQL JOBS - NEW!
@app.get("/api/jobs")
def list_jobs(db: Session = Depends(get_db)):
    """List all submitted jobs from database"""
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    
    return {
        "jobs": [
            {
                "job_id": job.job_id,
                "status": job.status,
                "task_type": job.task_type,
                "video_name": job.video_name,
                "gpu_id": job.gpu_id,
                "parameters": job.parameters,
                "progress": job.progress,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            }
            for job in jobs
        ]
    }


@app.post("/api/jobs/submit")
async def submit_job(job_data: dict, db: Session = Depends(get_db)):
    """Submit a new job to database"""
    import uuid
    
    job_id = str(uuid.uuid4())[:8]
    
    job = Job(
        job_id=job_id,
        status="queued",
        task_type=job_data.get("task_type", "unknown"),
        video_name=job_data.get("video_name", ""),
        gpu_id=job_data.get("gpu_id", 0),
        parameters=job_data.get("parameters", {})
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    return {
        "success": True,
        "job_id": job_id,
        "message": f"Job {job_id} submitted successfully",
        "job": {
            "job_id": job.job_id,
            "status": job.status,
            "task_type": job.task_type,
            "created_at": job.created_at.isoformat()
        }
    }


@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Get status of a specific job"""
    job = db.query(Job).filter(Job.job_id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job": {
            "job_id": job.job_id,
            "status": job.status,
            "task_type": job.task_type,
            "video_name": job.video_name,
            "gpu_id": job.gpu_id,
            "progress": job.progress,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        }
    }


@app.delete("/api/jobs/{job_id}")
def cancel_job(job_id: str, db: Session = Depends(get_db)):
    """Cancel a job"""
    job = db.query(Job).filter(Job.job_id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job.status = "cancelled"
    db.commit()
    
    return {
        "success": True,
        "message": f"Job {job_id} cancelled"
    }