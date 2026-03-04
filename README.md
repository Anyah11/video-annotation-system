<<<<<<< HEAD
# 🎥 GPU-Enabled Video Annotation System

A web-based application for remote video annotation with GPU-accelerated task execution. Built for laboratory research workflows.

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

## 📦 Installation

### Prerequisites
- Python 3.8+
- Node.js 14+
- FFmpeg
- NVIDIA GPU (optional, for GPU features)

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd frontend
npm install
```

## 🚀 Running the Application

### Start Backend
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend
```bash
cd frontend
npm start
```

Open browser to `http://localhost:3000`

## 📖 Usage

1. **View Mode**: Browse and play videos
2. **Annotate Mode**: 
   - Click "Extract Frames" to generate frame images
   - Select annotation tool (Box, Polygon, Freehand, Point)
   - Draw annotations on frames
   - Click "Save" to persist annotations
3. **GPU & Jobs Mode**:
   - Monitor GPU utilization and memory
   - Submit computational tasks
   - Track job status

## 📁 Project Structure
```
video-annotation-system/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   └── venv/               # Virtual environment
├── frontend/
│   ├── src/
│   │   ├── App.js          # Main component
│   │   ├── VideoAnnotator.js
│   │   ├── GPUDashboard.js
│   │   └── *.css
│   ├── public/
│   └── package.json
├── test_videos/            # Video storage
├── .gitignore
└── README.md
```

## 🔧 Configuration

### Video Directory
Edit `backend/main.py`:
```python
VIDEO_DIR = "../test_videos"  # Change to your video directory
```

### API Base URL
Edit `frontend/src/App.js`:
```python
const API_BASE = 'http://localhost:8000';
```

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/videos` | GET | List all videos |
| `/api/stream/{filename}` | GET | Stream video file |
| `/api/extract-frames/{filename}` | POST | Extract frames |
| `/api/frames/{video_name}` | GET | List extracted frames |
| `/api/annotations/{video_name}` | GET/POST | Load/save annotations |
| `/api/gpu/status` | GET | GPU monitoring |
| `/api/jobs` | GET | List jobs |
| `/api/jobs/submit` | POST | Submit new job |

## 🎓 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [FFmpeg Guide](https://ffmpeg.org/documentation.html)

## 📝 License

This project is for educational and research purposes.

## 👤 Author

Kelechi Anyanwu

## 🙏 Acknowledgments

- Supervisor: Brendon Penner
- Lab infrastructure support: Karlo
=======
# video-annotation-system
>>>>>>> f23121e74d23446150d8f3cb6f004e509ddb92d2
