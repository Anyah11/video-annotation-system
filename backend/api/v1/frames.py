from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
import subprocess
import shutil
import threading
import time
from datetime import datetime

router = APIRouter(prefix="/api", tags=["frames"])

VIDEO_DIR = "../test_videos"
extraction_progress = {}


@router.post("/extract-frames/{filename}")
async def extract_frames(filename: str, fps: int = 5, quality: int = 2):
    """Start asynchronous frame extraction"""
    video_path = os.path.join(VIDEO_DIR, filename)
    
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video not found")
    
    video_name = os.path.splitext(filename)[0]
    
    if video_name in extraction_progress:
        if extraction_progress[video_name]['status'] == 'running':
            return {
                "message": "Extraction already in progress",
                "progress": extraction_progress[video_name]
            }
    
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
    """Background thread function for frame extraction"""
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


@router.get("/extract-frames/{video_name}/progress")
def get_extraction_progress(video_name: str):
    """Get the progress of frame extraction"""
    if video_name not in extraction_progress:
        return {
            "status": "not_started",
            "progress": 0,
            "message": "No extraction in progress"
        }
    
    return extraction_progress[video_name]


@router.get("/frames/{video_name}")
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


@router.get("/frame-image/{video_name}/{frame_filename}")
async def get_frame_image(video_name: str, frame_filename: str):
    """Serve a specific frame image"""
    frames_dir = os.path.join(VIDEO_DIR, f"{video_name}_frames")
    frame_path = os.path.join(frames_dir, frame_filename)
    
    if not os.path.exists(frame_path):
        raise HTTPException(status_code=404, detail="Frame not found")
    
    return FileResponse(frame_path, media_type="image/jpeg")
