from database import init_db, SessionLocal
from models import Video, Annotation, Job

# Create all tables
print("Creating database tables...")
init_db()

# Test inserting data
db = SessionLocal()

try:
    # Create a test video
    video = Video(
        filename="test_video.mp4",
        filepath="/path/to/test_video.mp4",
        size_bytes=1000000,
        size_mb=1.0,
        frames_extracted=10
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    print(f"✅ Created video: {video.filename} (ID: {video.id})")
    
    # Create a test annotation
    annotation = Annotation(
        video_id=video.id,
        frame_index=0,
        annotation_type="box",
        data={"x": 100, "y": 200, "width": 50, "height": 50}
    )
    db.add(annotation)
    db.commit()
    print(f"✅ Created annotation for video {video.filename}")
    
    # Create a test job
    job = Job(
        job_id="test123",
        status="queued",
        task_type="training",
        video_name="test_video.mp4",
        gpu_id=0
    )
    db.add(job)
    db.commit()
    print(f"✅ Created job: {job.job_id}")
    
    # Query data
    all_videos = db.query(Video).all()
    print(f"\n📊 Total videos in database: {len(all_videos)}")
    
    all_annotations = db.query(Annotation).all()
    print(f"📊 Total annotations in database: {len(all_annotations)}")
    
    all_jobs = db.query(Job).all()
    print(f"📊 Total jobs in database: {len(all_jobs)}")
    
    # Clean up test data
    db.query(Annotation).delete()
    db.query(Video).delete()
    db.query(Job).delete()
    db.commit()
    print("\n✅ Test data cleaned up!")
    
    print("\n🎉 All database tests passed! PostgreSQL is ready!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()