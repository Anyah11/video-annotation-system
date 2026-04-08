from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import json
import tempfile
from database import get_db
from models import Video, Annotation

router = APIRouter(prefix="/api/annotations", tags=["annotations"])

VIDEO_DIR = "../test_videos"


@router.post("/{video_name}")
async def save_annotations(video_name: str, annotations: dict, db: Session = Depends(get_db)):
    """Save annotations for a video to PostgreSQL"""
    try:
        # Get or create video record
        video_filename = f"{video_name}.mp4"
        db_video = db.query(Video).filter(Video.filename == video_filename).first()
        
        if not db_video:
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


@router.get("/{video_name}")
def load_annotations(video_name: str, db: Session = Depends(get_db)):
    """Load annotations for a video from PostgreSQL"""
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


@router.get("/{video_name}/export")
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
