from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
import aiofiles
import os
from sqlalchemy.orm import Session
from database import get_db
from models import Video
from fastapi import APIRouter, HTTPException, Request, Depends, UploadFile, File
import shutil

router = APIRouter(prefix="/api/videos", tags=["videos"])

VIDEO_DIR = "../test_videos"

def is_video_file(filename: str) -> bool:
    """Check if file has a video extension"""
    video_extensions = [
        '.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm',
        '.m4v', '.mpg', '.mpeg', '.3gp', '.ts', '.mts'
    ]
    return any(filename.lower().endswith(ext) for ext in video_extensions)


@router.get("")
def list_videos(db: Session = Depends(get_db)):
    """List all video files in the video directory"""
    try:
        if not os.path.exists(VIDEO_DIR):
            raise HTTPException(status_code=404, detail=f"Video directory not found: {VIDEO_DIR}")
        
        all_files = os.listdir(VIDEO_DIR)
        video_files = [f for f in all_files if is_video_file(f)]
        
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
            from models import Annotation
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


@router.get("/stream/{filename}")
async def stream_video(filename: str, request: Request):
    """Stream a video file with range request support"""
    filepath = os.path.join(VIDEO_DIR, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Video not found: {filename}")
    
    if not is_video_file(filename):
        raise HTTPException(status_code=400, detail=f"File is not a video: {filename}")
    
    file_size = os.path.getsize(filepath)
    range_header = request.headers.get('range')
    
    start = 0
    end = file_size - 1
    
    if range_header:
        range_value = range_header.replace("bytes=", "")
        if "-" in range_value:
            parts = range_value.split("-")
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if parts[1] else file_size - 1
    
    content_length = end - start + 1
    
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
    
    headers = {
        'Content-Range': f'bytes {start}-{end}/{file_size}',
        'Accept-Ranges': 'bytes',
        'Content-Length': str(content_length),
        'Content-Type': 'video/mp4',
    }
    
    status_code = 206 if range_header else 200
    
    return StreamingResponse(
        file_chunk_generator(),
        status_code=status_code,
        headers=headers,
        media_type='video/mp4'
    )

@router.post("/upload")
async def upload_video(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a video file"""
    try:
        # Validate file type
        if not is_video_file(file.filename):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Supported formats: .mp4, .avi, .mov, .mkv, .flv, .wmv, .webm, .m4v, .mpg, .mpeg, .3gp, .ts, .mts"
            )
        
        # Create video directory if it doesn't exist
        if not os.path.exists(VIDEO_DIR):
            os.makedirs(VIDEO_DIR)
        
        # Save file
        file_path = os.path.join(VIDEO_DIR, file.filename)
        
        # Check if file already exists
        if os.path.exists(file_path):
            raise HTTPException(
                status_code=400,
                detail=f"File '{file.filename}' already exists"
            )
        
        # Write file in chunks
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file stats
        file_stats = os.stat(file_path)
        
        # Add to database
        db_video = Video(
            filename=file.filename,
            filepath=file_path,
            size_bytes=file_stats.st_size,
            size_mb=round(file_stats.st_size / (1024 * 1024), 2)
        )
        db.add(db_video)
        db.commit()
        db.refresh(db_video)
        
        return {
            "success": True,
            "message": f"Video '{file.filename}' uploaded successfully",
            "video": {
                "filename": file.filename,
                "size_mb": round(file_stats.st_size / (1024 * 1024), 2),
                "path": file_path
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))