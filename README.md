📝 Let's Create an Amazing README!
bashcd /Users/kelechianyanwu/video-annotation-system
nano README.md
Paste this complete README:
markdown# 🎬 Video Annotation System

A full-stack GPU-enabled video annotation web application built for research labs. Features frame-by-frame annotation, real-time GPU monitoring, async processing, and user authentication.

![Version](https://img.shields.io/badge/version-0.5.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Features

### 🎥 Video Management
- Support for 12 video formats (MP4, AVI, MOV, MKV, FLV, WMV, WebM, M4V, MPG, MPEG, 3GP, TS, MTS)
- Streaming video playback with HTTP range request support
- Video browser with metadata display
- Automatic video indexing

### ✏️ Annotation Tools
- **Bounding Box**: Draw rectangular regions
- **Polygon**: Multi-point shape annotation
- **Freehand**: Free-form drawing
- **Keypoint**: Single point marking
- Frame-by-frame annotation
- Auto-save and auto-load annotations
- Export to JSON and COCO formats

### 🚀 Advanced Processing
- **Async Frame Extraction**: Non-blocking background processing
- **Real-time Progress Tracking**: Visual progress bar with status updates
- **Configurable Parameters**: Adjustable FPS and quality settings
- Multi-threaded processing

### 🖥️ GPU Management
- Real-time GPU monitoring (NVIDIA GPUs)
- Memory usage tracking
- Temperature monitoring
- GPU utilization statistics
- Job queue management

### 🔐 Authentication & Security
- JWT token-based authentication
- Role-based access control (Admin/User)
- Secure password hashing (SHA256)
- Protected API endpoints
- Session management

### 🗄️ Database
- PostgreSQL for production-grade data storage
- Relational data model with foreign keys
- Database indexes for fast queries
- Support for concurrent users

---

## 🏗️ Architecture

### Backend (FastAPI + Python)
backend/
├── main.py              # App initialization & routing
├── auth.py              # Authentication utilities
├── database.py          # Database connection
├── models.py            # SQLAlchemy models
├── requirements.txt     # Python dependencies
└── api/v1/             # Modular routers
├── videos.py        # Video streaming & listing
├── frames.py        # Frame extraction
├── annotations.py   # Annotation management
├── gpu.py          # GPU monitoring
├── jobs.py         # Job queue
└── auth.py         # Authentication endpoints

### Frontend (React)
frontend/
├── src/
│   ├── App.js           # Main application
│   ├── AuthContext.js   # Authentication state
│   ├── Login.js         # Login page
│   ├── VideoAnnotator.js # Annotation interface
│   └── GPUDashboard.js   # GPU monitoring UI
└── public/

### Database Schema
- **videos**: Video metadata and file information
- **annotations**: Frame-based annotation data
- **jobs**: Background job tracking
- **users**: User accounts and permissions

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.14+**
- **Node.js 16+**
- **PostgreSQL 14+**
- **FFmpeg** (for frame extraction)
- **NVIDIA GPU** (optional, for GPU monitoring)

### 1️⃣ Database Setup

```bash
# Install PostgreSQL (macOS)
brew install postgresql@14

# Start PostgreSQL
brew services start postgresql@14

# Create database
createdb video_annotation_db
```

### 2️⃣ Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will run at: **http://localhost:8000**

API Documentation: **http://localhost:8000/docs**

### 3️⃣ Frontend Setup

```bash
# Navigate to frontend (in new terminal)
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

Frontend will run at: **http://localhost:3000**

### 4️⃣ Create First Admin User

```bash
curl -X POST "http://localhost:8000/api/auth/create-first-admin?username=admin&email=admin@lab.com&password=admin123"
```

### 5️⃣ Login

Open http://localhost:3000 and login with:
- **Username**: admin
- **Password**: admin123

---

## 📚 Usage Guide

### Adding Videos

Place video files in the `test_videos/` directory:
```bash
cp your_video.mp4 test_videos/
```

Videos will automatically appear in the application.

### Annotating Videos

1. **Select a video** from the sidebar
2. Click **"Annotate Mode"**
3. Click **"Extract Frames"** (if not already extracted)
4. Wait for progress bar to complete
5. Use annotation tools to mark frames:
   - **Box**: Click and drag to draw rectangles
   - **Polygon**: Click to place points, double-click to complete
   - **Freehand**: Click and drag to draw freely
   - **Point**: Click to place keypoints
6. Click **"Save"** to store annotations
7. Export annotations via **"Export JSON"** or **"Export COCO"**

### Managing Users (Admin Only)

#### Via API Documentation:
1. Go to http://localhost:8000/docs
2. Click **"Authorize"** and enter: `Bearer YOUR_TOKEN`
3. Use **POST /api/auth/register** to create users

#### Via Terminal:
```bash
# Login to get token
TOKEN=$(curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | jq -r '.access_token')

# Create a new user
curl -X POST "http://localhost:8000/api/auth/register?username=researcher1&email=researcher1@lab.com&password=pass123&is_admin=false" \
  -H "Authorization: Bearer $TOKEN"
```

#### View All Users:
```bash
psql video_annotation_db -c "SELECT id, username, email, is_admin, created_at FROM users;"
```

### GPU Monitoring

Click **"GPU & Jobs"** tab to:
- View real-time GPU statistics
- Monitor memory usage
- Track GPU temperature
- Submit and manage processing jobs

---

## 🔧 Configuration

### Backend Configuration

**`backend/auth.py`** - Update security settings:
```python
SECRET_KEY = "your-super-secret-key-change-in-production"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
```

**`backend/database.py`** - Database connection:
```python
DATABASE_URL = "postgresql://localhost/video_annotation_db"
```

**`backend/api/v1/videos.py`** - Video directory:
```python
VIDEO_DIR = "../test_videos"
```

### Frontend Configuration

**`frontend/src/App.js`** - API endpoint:
```javascript
const API_BASE = 'http://localhost:8000';
```

---

## 📡 API Endpoints

### Authentication
- `POST /api/auth/create-first-admin` - Create first admin (no auth required)
- `POST /api/auth/register` - Create user (admin only)
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info
- `GET /api/auth/users` - List all users (admin only)
- `DELETE /api/auth/users/{user_id}` - Delete user (admin only)

### Videos
- `GET /api/videos` - List all videos
- `GET /api/videos/stream/{filename}` - Stream video with range support

### Frames
- `POST /api/extract-frames/{filename}` - Start async frame extraction
- `GET /api/extract-frames/{video_name}/progress` - Get extraction progress
- `GET /api/frames/{video_name}` - List extracted frames
- `GET /api/frame-image/{video_name}/{frame}` - Get frame image

### Annotations
- `POST /api/annotations/{video_name}` - Save annotations
- `GET /api/annotations/{video_name}` - Load annotations
- `GET /api/annotations/{video_name}/export?format=json` - Export as JSON
- `GET /api/annotations/{video_name}/export?format=coco` - Export as COCO

### GPU & Jobs
- `GET /api/gpu/status` - Get GPU statistics
- `GET /api/jobs` - List all jobs
- `POST /api/jobs/submit` - Submit new job
- `GET /api/jobs/{job_id}` - Get job status
- `DELETE /api/jobs/{job_id}` - Cancel job

---

## 🗃️ Database Schema

### Videos Table
```sql
CREATE TABLE videos (
    id SERIAL PRIMARY KEY,
    filename VARCHAR UNIQUE NOT NULL,
    filepath VARCHAR NOT NULL,
    size_bytes INTEGER,
    size_mb FLOAT,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    frames_extracted INTEGER DEFAULT 0
);
```

### Annotations Table
```sql
CREATE TABLE annotations (
    id SERIAL PRIMARY KEY,
    video_id INTEGER REFERENCES videos(id),
    frame_index INTEGER NOT NULL,
    annotation_type VARCHAR NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    is_admin INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);
```

### Jobs Table
```sql
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR UNIQUE NOT NULL,
    status VARCHAR DEFAULT 'queued',
    task_type VARCHAR NOT NULL,
    video_name VARCHAR,
    gpu_id INTEGER DEFAULT 0,
    parameters JSONB,
    progress INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

---

## 🛠️ Development

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Structure

The backend follows a modular router pattern:
- Each feature has its own router file
- Database models are centralized
- Authentication is handled via dependency injection
- All routes are versioned (`/api/v1/`)

### Adding New Features

1. Create new router in `backend/api/v1/`
2. Define SQLAlchemy models in `backend/models.py`
3. Register router in `backend/main.py`
4. Create React components in `frontend/src/`

---

## 🚧 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill process if needed
kill -9 <PID>

# Ensure virtual environment is activated
source venv/bin/activate
```

### Database connection errors
```bash
# Check PostgreSQL is running
brew services list

# Restart PostgreSQL
brew services restart postgresql@14

# Verify database exists
psql -l | grep video_annotation_db
```

### Frontend can't connect to backend
- Ensure backend is running on port 8000
- Check CORS settings in `backend/main.py`
- Verify API_BASE URL in `frontend/src/App.js`

### Frame extraction fails
```bash
# Install FFmpeg
brew install ffmpeg

# Verify installation
ffmpeg -version
```

### GPU monitoring not working
- NVIDIA GPU required
- Install nvidia-ml-py: `pip install nvidia-ml-py`
- Check GPU drivers are installed

---

## 📦 Dependencies

### Backend
- **FastAPI** - Modern web framework
- **SQLAlchemy** - ORM for database
- **PostgreSQL** - Production database
- **python-jose** - JWT tokens
- **pynvml** - GPU monitoring
- **aiofiles** - Async file operations
- **FFmpeg** - Video processing

### Frontend
- **React** - UI framework
- **axios** - HTTP client
- **CSS3** - Styling

---

## 🔮 Future Enhancements

- [ ] Video upload interface
- [ ] Real-time collaborative annotation
- [ ] Advanced annotation tools (3D boxes, tracking)
- [ ] Model training integration
- [ ] Annotation quality metrics
- [ ] Export to more formats (YOLO, Pascal VOC)
- [ ] User activity logging
- [ ] Admin dashboard with analytics
- [ ] Mobile app support
- [ ] Cloud deployment guides

---

## 📄 License

MIT License - See LICENSE file for details

---

## 👥 Contributors

**Kelechi Anyanwu** - Initial development

**Supervisor**: Brendon Penner

**Infrastructure**: Karlo

---

## 🙏 Acknowledgments

Built for university research lab to enable efficient video annotation workflows for computer vision projects.

---

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review API documentation at http://localhost:8000/docs
3. Contact the development team

---

## 🔄 Version History

### v0.5.0 (Current)
- ✅ User authentication system
- ✅ JWT token-based security
- ✅ Role-based access control

### v0.4.0
- ✅ Code modularization
- ✅ Organized router structure
- ✅ Improved maintainability

### v0.3.0
- ✅ PostgreSQL migration
- ✅ Production database
- ✅ Concurrent user support

### v0.2.0
- ✅ Async frame extraction
- ✅ Real-time progress tracking
- ✅ 12 video format support

### v0.1.0
- ✅ Initial release
- ✅ Basic annotation tools
- ✅ Video streaming
- ✅ GPU monitoring
