from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import aiofiles
from typing import Optional
import os
from pathlib import Path
import subprocess
import shutil
from fastapi.responses import FileResponse

# Create the FastAPI application
app = FastAPI(title="Video Annotation Backend")

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

# Helper function to check if file is a video
def is_video_file(filename: str) -> bool:
    """Check if file has a video extension"""
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm']
    return any(filename.lower().endswith(ext) for ext in video_extensions)

# ===== ENDPOINTS START HERE =====

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "Video Annotation Backend is running!",
        "status": "online",
        "version": "0.1.0"
    }

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# API info endpoint
@app.get("/api/info")
def api_info():
    return {
        "project": "GPU-Enabled Video Annotation System",
        "endpoints": [
            "/",
            "/health", 
            "/api/info",
            "/docs"
        ]
    }

# Endpoint to list all videos
@app.get("/api/videos")
def list_videos():
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
            
            videos.append({
                "filename": filename,
                "path": filepath,
                "size_bytes": file_stats.st_size,
                "size_mb": round(file_stats.st_size / (1024 * 1024), 2),
                "modified": file_stats.st_mtime
            })
        
        return {
            "count": len(videos),
            "videos": videos,
            "directory": VIDEO_DIR
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to get info about a specific video
@app.get("/api/videos/{filename}")
def get_video_info(filename: str):
    """
    Get detailed information about a specific video file
    """
    filepath = os.path.join(VIDEO_DIR, filename)
    
    # Check if file exists
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Video not found: {filename}")
    
    # Check if it's actually a video file
    if not is_video_file(filename):
        raise HTTPException(status_code=400, detail=f"File is not a video: {filename}")
    
    # Get file stats
    file_stats = os.stat(filepath)
    
    return {
        "filename": filename,
        "path": filepath,
        "size_bytes": file_stats.st_size,
        "size_mb": round(file_stats.st_size / (1024 * 1024), 2),
        "size_gb": round(file_stats.st_size / (1024 * 1024 * 1024), 2),
        "modified": file_stats.st_mtime,
        "exists": True
    }

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

@app.post("/api/extract-frames/{filename}")
async def extract_frames(filename: str, fps: int = 5):
    """
    Extract frames from video at specified FPS
    fps: frames per second to extract (default: 5 = extract 5 frames per second)
    """
    video_path = os.path.join(VIDEO_DIR, filename)
    
    # Check if video exists
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Create frames directory for this video
    video_name = os.path.splitext(filename)[0]
    frames_dir = os.path.join(VIDEO_DIR, f"{video_name}_frames")
    
    # Remove old frames if they exist
    if os.path.exists(frames_dir):
        shutil.rmtree(frames_dir)
    
    os.makedirs(frames_dir)
    
    # FFmpeg command to extract frames
    output_pattern = os.path.join(frames_dir, "frame_%04d.jpg")
    
    try:
        # Extract frames using FFmpeg
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', f'fps={fps}',  # Extract at specified FPS
            '-q:v', '2',  # High quality (1-31, lower is better)
            output_pattern
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"FFmpeg error: {result.stderr}")
        
        # Count extracted frames
        frames = [f for f in os.listdir(frames_dir) if f.endswith('.jpg')]
        frames.sort()
        
        return {
            "success": True,
            "video": filename,
            "frames_dir": frames_dir,
            "frame_count": len(frames),
            "fps": fps,
            "frames": frames
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/frames/{video_name}")
def list_frames(video_name: str):
    """
    List all extracted frames for a video
    """
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
    """
    Serve a specific frame image
    """
    frames_dir = os.path.join(VIDEO_DIR, f"{video_name}_frames")
    frame_path = os.path.join(frames_dir, frame_filename)
    
    if not os.path.exists(frame_path):
        raise HTTPException(status_code=404, detail="Frame not found")
    
    from fastapi.responses import FileResponse
    return FileResponse(frame_path, media_type="image/jpeg")

@app.post("/api/annotations/{video_name}")
async def save_annotations(video_name: str, annotations: dict):
    """
    Save annotations for a video
    """
    annotations_dir = os.path.join(VIDEO_DIR, "annotations")
    
    # Create annotations directory if it doesn't exist
    if not os.path.exists(annotations_dir):
        os.makedirs(annotations_dir)
    
    # Save as JSON file
    annotation_file = os.path.join(annotations_dir, f"{video_name}_annotations.json")
    
    try:
        import json
        with open(annotation_file, 'w') as f:
            json.dump(annotations, f, indent=2)
        
        return {
            "success": True,
            "message": "Annotations saved successfully",
            "file": annotation_file,
            "annotation_count": sum(len(boxes) for boxes in annotations.values())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/annotations/{video_name}")
def load_annotations(video_name: str):
    """
    Load annotations for a video
    """
    annotations_dir = os.path.join(VIDEO_DIR, "annotations")
    annotation_file = os.path.join(annotations_dir, f"{video_name}_annotations.json")
    
    if not os.path.exists(annotation_file):
        return {"annotations": {}, "message": "No annotations found"}
    
    try:
        import json
        with open(annotation_file, 'r') as f:
            annotations = json.load(f)
        
        return {
            "annotations": annotations,
            "annotation_count": sum(len(boxes) for boxes in annotations.values()),
            "file": annotation_file
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/annotations/{video_name}/export")
def export_annotations(video_name: str, format: str = "json"):
    """
    Export annotations in different formats (JSON, COCO, YOLO)
    """
    annotations_dir = os.path.join(VIDEO_DIR, "annotations")
    annotation_file = os.path.join(annotations_dir, f"{video_name}_annotations.json")
    
    if not os.path.exists(annotation_file):
        raise HTTPException(status_code=404, detail="No annotations found")
    
    try:
        import json
        with open(annotation_file, 'r') as f:
            annotations = json.load(f)
        
        if format == "json":
            # Return raw JSON format
            return FileResponse(
                annotation_file,
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
            for frame_idx, boxes in annotations.items():
                frame_idx = int(frame_idx)
                
                # Add image info
                coco_format["images"].append({
                    "id": frame_idx,
                    "file_name": f"frame_{frame_idx:04d}.jpg",
                    "width": 1920,  # You might want to get actual dimensions
                    "height": 1080
                })
                
                # Add annotations
                for box in boxes:
                    coco_format["annotations"].append({
                        "id": annotation_id,
                        "image_id": frame_idx,
                        "category_id": 1,
                        "bbox": [box["x"], box["y"], box["width"], box["height"]],
                        "area": box["width"] * box["height"],
                        "iscrowd": 0
                    })
                    annotation_id += 1
            
            # Save and return COCO format
            coco_file = os.path.join(annotations_dir, f"{video_name}_coco.json")
            with open(coco_file, 'w') as f:
                json.dump(coco_format, f, indent=2)
            
            return FileResponse(
                coco_file,
                media_type="application/json",
                filename=f"{video_name}_coco.json"
            )
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# GPU Monitoring
try:
    import pynvml
    GPU_AVAILABLE = True
    pynvml.nvmlInit()
except:
    GPU_AVAILABLE = False
    print("Warning: NVIDIA GPU monitoring not available")


@app.get("/api/gpu/status")
def get_gpu_status():
    """
    Get status of all GPUs
    """
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
            
            # Get memory info
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            memory_total = mem_info.total / (1024 ** 3)  # Convert to GB
            memory_used = mem_info.used / (1024 ** 3)
            memory_free = mem_info.free / (1024 ** 3)
            
            # Get utilization
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            gpu_util = util.gpu
            
            # Get temperature
            try:
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            except:
                temp = 0
            
            # Get running processes
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


@app.get("/api/jobs")
def list_jobs():
    """
    List all submitted jobs
    """
    jobs_dir = os.path.join(VIDEO_DIR, "jobs")
    
    if not os.path.exists(jobs_dir):
        os.makedirs(jobs_dir)
        return {"jobs": []}
    
    import json
    jobs = []
    
    for filename in os.listdir(jobs_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(jobs_dir, filename)
            with open(filepath, 'r') as f:
                job_data = json.load(f)
                jobs.append(job_data)
    
    # Sort by creation time (newest first)
    jobs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return {"jobs": jobs}


@app.post("/api/jobs/submit")
async def submit_job(job_data: dict):
    """
    Submit a new job to run on GPU
    """
    jobs_dir = os.path.join(VIDEO_DIR, "jobs")
    
    if not os.path.exists(jobs_dir):
        os.makedirs(jobs_dir)
    
    import json
    from datetime import datetime
    import uuid
    
    # Generate job ID
    job_id = str(uuid.uuid4())[:8]
    
    # Create job record
    job = {
        "job_id": job_id,
        "status": "queued",
        "task_type": job_data.get("task_type", "unknown"),
        "video_name": job_data.get("video_name", ""),
        "gpu_id": job_data.get("gpu_id", 0),
        "parameters": job_data.get("parameters", {}),
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None,
        "progress": 0,
        "logs": []
    }
    
    # Save job file
    job_file = os.path.join(jobs_dir, f"{job_id}.json")
    with open(job_file, 'w') as f:
        json.dump(job, f, indent=2)
    
    return {
        "success": True,
        "job_id": job_id,
        "message": f"Job {job_id} submitted successfully",
        "job": job
    }


@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    """
    Get status of a specific job
    """
    jobs_dir = os.path.join(VIDEO_DIR, "jobs")
    job_file = os.path.join(jobs_dir, f"{job_id}.json")
    
    if not os.path.exists(job_file):
        raise HTTPException(status_code=404, detail="Job not found")
    
    import json
    with open(job_file, 'r') as f:
        job = json.load(f)
    
    return {"job": job}


@app.delete("/api/jobs/{job_id}")
def cancel_job(job_id: str):
    """
    Cancel a job
    """
    jobs_dir = os.path.join(VIDEO_DIR, "jobs")
    job_file = os.path.join(jobs_dir, f"{job_id}.json")
    
    if not os.path.exists(job_file):
        raise HTTPException(status_code=404, detail="Job not found")
    
    import json
    with open(job_file, 'r') as f:
        job = json.load(f)
    
    job["status"] = "cancelled"
    
    with open(job_file, 'w') as f:
        json.dump(job, f, indent=2)
    
    return {
        "success": True,
        "message": f"Job {job_id} cancelled"
    }
