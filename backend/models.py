# backend/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Video(Base):
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, nullable=False, index=True)
    filepath = Column(String, nullable=False)
    size_bytes = Column(Integer)
    size_mb = Column(Float)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    frames_extracted = Column(Integer, default=0)
    
    # Relationships
    annotations = relationship("Annotation", back_populates="video", cascade="all, delete-orphan")

class Annotation(Base):
    __tablename__ = "annotations"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    frame_index = Column(Integer, nullable=False, index=True)
    annotation_type = Column(String, nullable=False)  # 'box', 'polygon', 'freehand', 'point'
    data = Column(JSON, nullable=False)  # Stores x, y, width, height, points, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    video = relationship("Video", back_populates="annotations")

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, default="queued")  # queued, running, completed, failed, cancelled
    task_type = Column(String, nullable=False)
    video_name = Column(String)
    gpu_id = Column(Integer, default=0)
    parameters = Column(JSON)
    progress = Column(Integer, default=0)
    logs = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Integer, default=0)  # 0 = regular user, 1 = admin
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)