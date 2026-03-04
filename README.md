# 🎥 GPU-Enabled Video Annotation System

A web-based application for remote video annotation with GPU-accelerated task execution. Built for laboratory research workflows.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![React](https://img.shields.io/badge/React-18+-61dafb.svg)

## 🌟 Features

- **Video Streaming**: Play videos remotely with seek support
- **Frame-Based Annotation**: Extract frames and annotate with multiple tools
  - Bounding boxes
  - Polygons  
  - Freehand drawing
  - Keypoints
- **Persistent Storage**: Save and load annotations
- **GPU Monitoring**: Real-time GPU utilization, memory, and temperature
- **Job Management**: Submit and track GPU tasks
- **Export Formats**: JSON and COCO format support

## 🏗️ Architecture
```
┌─────────────┐         HTTP          ┌─────────────┐
│  Frontend   │ ←──────────────────→  │   Backend   │
│  (React)    │                       │  (FastAPI)  │
│  Port 3000  │                       │  Port 8000  │
└─────────────┘                       └─────────────┘
                                            ↓
                                      ┌─────────────┐
                                      │ File System │
                                      │  - Videos   │
                                      │  - Frames   │
                                      │  - Annotations
                                      └─────────────┘
```

## 📦 Prerequisites

Before you begin, make sure you have:

- **Python 3.8+** - [Download here](https://www.python.org/downloads/)
- **Node.js 14+** - [Download here](https://nodejs.org/)
- **FFmpeg** - For video frame extraction
  - Mac: `brew install ffmpeg`
  - Ubuntu: `sudo apt install ffmpeg`
  - Windows: [Download from ffmpeg.org](https://ffmpeg.org/download.html)
- **Git** - [Download here](https://git-scm.com/downloads)
- **(Optional) NVIDIA GPU** - For GPU monitoring features

## 🚀 Quick Start (Local Development)

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/Anyah11/video-annotation-system.git
cd video-annotation-system
```

### 2️⃣ Set Up Backend
```bash
# Navigate to backend folder
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn python-multipart aiofiles pynvml

# Save dependencies (optional)
pip freeze > requirements.txt
```

### 3️⃣ Set Up Frontend

Open a **NEW terminal window** (keep backend terminal open), then:
```bash
# Navigate to frontend folder
cd video-annotation-system/frontend

# Install dependencies
npm install
```

### 4️⃣ Add Test Videos
```bash
# Create test videos folder (if it doesn't exist)
mkdir -p test_videos

# Add your video files to this folder
# Supported formats: .mp4, .avi, .mov, .mkv, .webm
```

### 5️⃣ Start the Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

Your browser should automatically open to `http://localhost:3000`

If not, manually visit: **http://localhost:3000**

### 6️⃣ Using the Application

1. **View Videos**
   - Click on any video in the left sidebar
   - Video will play in the main area

2. **Annotate Videos**
   - Click "✏️ Annotate Mode" button
   - Click "🎬 Extract Frames" (first time only, takes 10-60 seconds)
   - Select annotation tool (Box, Polygon, Freehand, Point)
   - Draw on the frame
   - Click "💾 Save" to persist annotations

3. **Monitor GPUs & Submit Jobs**
   - Click "🖥️ GPU & Jobs" button
   - View real-time GPU stats (if NVIDIA GPU available)
   - Submit computational tasks
   - Track job status

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **FFmpeg** - Video frame extraction
- **pynvml** - NVIDIA GPU monitoring
- **aiofiles** - Async file operations

### Frontend
- **React** - UI framework
- **Axios** - HTTP client
- **HTML5 Canvas** - Annotation drawing

## 📁 Project Structure
```
video-annotation-system/
├── backend/
│   ├── main.py                 # FastAPI application & all endpoints
│   ├── requirements.txt        # Python dependencies
│   └── venv/                   # Virtual environment (not in git)
├── frontend/
│   ├── src/
│   │   ├── App.js             # Main React component
│   │   ├── VideoAnnotator.js  # Annotation interface
│   │   ├── GPUDashboard.js    # GPU monitoring UI
│   │   └── *.css              # Styles
│   ├── public/
│   └── package.json
├── test_videos/               # Your video files (not in git)
├── .gitignore
└── README.md
```

## 🔧 Configuration

### Change Video Directory

Edit `backend/main.py`:
```python
VIDEO_DIR = "../test_videos"  # Change to your video location
```

### Change API URL (if deploying)

Edit `frontend/src/App.js`, `VideoAnnotator.js`, `GPUDashboard.js`:
```javascript
const API_BASE = 'http://localhost:8000';  // Change to your server URL
```

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api/videos` | GET | List all videos |
| `/api/stream/{filename}` | GET | Stream video with range support |
| `/api/extract-frames/{filename}` | POST | Extract frames from video (5 fps) |
| `/api/frames/{video_name}` | GET | List extracted frames |
| `/api/frame-image/{video_name}/{frame}` | GET | Get specific frame image |
| `/api/annotations/{video_name}` | GET | Load annotations |
| `/api/annotations/{video_name}` | POST | Save annotations |
| `/api/annotations/{video_name}/export` | GET | Export annotations (JSON/COCO) |
| `/api/gpu/status` | GET | Get GPU statistics |
| `/api/jobs` | GET | List all jobs |
| `/api/jobs/submit` | POST | Submit new GPU job |
| `/api/jobs/{job_id}` | GET | Get job status |
| `/api/jobs/{job_id}` | DELETE | Cancel job |

Visit `http://localhost:8000/docs` for interactive API documentation!

## 🐛 Troubleshooting

### Backend won't start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`
- **Solution:** Make sure virtual environment is activated: `source venv/bin/activate`

**Error:** `Address already in use`
- **Solution:** Port 8000 is busy. Kill the process or use a different port:
```bash
  uvicorn main:app --reload --port 8001
```

### Frontend won't start

**Error:** `npm: command not found`
- **Solution:** Install Node.js from https://nodejs.org/

**Error:** `CORS error` in browser console
- **Solution:** Make sure backend is running and CORS middleware is enabled in `main.py`

### Videos won't play

**Error:** Video shows play button with line through it
- **Solution:** 
  1. Check that video file exists in `test_videos/`
  2. Make sure backend is running
  3. Try a smaller video file first (< 50MB)

### Frame extraction fails

**Error:** `FFmpeg error`
- **Solution:** Install FFmpeg:
  - Mac: `brew install ffmpeg`
  - Ubuntu: `sudo apt install ffmpeg`

### GPU monitoring shows "not available"

- **Solution:** This is normal if you don't have an NVIDIA GPU. The app still works - GPU features just won't show data.


## 📝 License

This project is for educational and research purposes.

## 👤 Author

**Kelechi Anyanwu**
- GitHub: [@Anyah11](https://github.com/Anyah11)

## 🙏 Acknowledgments

- Supervisor: Brendon Penner
- Lab Infrastructure Support: Karlo

