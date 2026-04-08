from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db

# Import routers
from api.v1 import videos, frames, annotations, gpu, jobs

# Create the FastAPI application
app = FastAPI(
    title="Video Annotation Backend",
    description="GPU-Enabled Video Annotation System with PostgreSQL",
    version="0.4.0 - Modular Edition"
)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()
    print("✅ Database initialized!")
    print("✅ All routers loaded!")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(videos.router)
app.include_router(frames.router)
app.include_router(annotations.router)
app.include_router(gpu.router)
app.include_router(jobs.router)

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "Video Annotation Backend is running!",
        "status": "online",
        "version": "0.4.0 - Modular Edition",
        "routers": ["videos", "frames", "annotations", "gpu", "jobs"]
    }

# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy"}