from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import uuid
from database import get_db
from models import Job

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("")
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


@router.post("/submit")
async def submit_job(job_data: dict, db: Session = Depends(get_db)):
    """Submit a new job to database"""
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


@router.get("/{job_id}")
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


@router.delete("/{job_id}")
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
