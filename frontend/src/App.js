import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';
import VideoAnnotator from './VideoAnnotator';
import GPUDashboard from './GPUDashboard';

const API_BASE = 'http://localhost:8000';

function App() {
  const [videos, setVideos] = useState([]);
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [mode, setMode] = useState('view');

  useEffect(() => {
    loadVideos();
  }, []);

  const loadVideos = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/api/videos`);
      setVideos(response.data.videos);
      setLoading(false);
    } catch (err) {
      setError('Failed to load videos. Make sure backend is running!');
      setLoading(false);
      console.error('Error loading videos:', err);
    }
  };

  const handleVideoSelect = (video) => {
    setSelectedVideo(video);
    setMode('view');
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>🎥 Video Annotation System</h1>
        <p>Laboratory Video Browser & Annotation Tool</p>
      </header>

      <div className="app-container">
        <aside className="sidebar">
          <h2>Videos ({videos.length})</h2>
          
          {loading && <p className="loading">Loading videos...</p>}
          {error && <p className="error">{error}</p>}
          
          <div className="video-list">
            {videos.map((video, index) => (
              <div
                key={index}
                className={`video-item ${selectedVideo?.filename === video.filename ? 'active' : ''}`}
                onClick={() => handleVideoSelect(video)}
              >
                <div className="video-icon">🎬</div>
                <div className="video-info">
                  <div className="video-name">{video.filename}</div>
                  <div className="video-size">{video.size_mb} MB</div>
                </div>
              </div>
            ))}
          </div>
        </aside>

        <main className="main-content">
          {selectedVideo ? (
            <div>
              <div className="mode-switcher">
                <button 
                  className={mode === 'view' ? 'active' : ''}
                  onClick={() => setMode('view')}
                >
                  👁️ View Mode
                </button>
                <button 
                  className={mode === 'annotate' ? 'active' : ''}
                  onClick={() => setMode('annotate')}
                >
                  ✏️ Annotate Mode
                </button>
                <button 
                  className={mode === 'gpu' ? 'active' : ''}
                  onClick={() => setMode('gpu')}
                >
                  🖥️ GPU & Jobs
                </button>
              </div>

              {mode === 'view' ? (
                <div className="video-player-container">
                  <h2>{selectedVideo.filename}</h2>
                  <video
                    key={selectedVideo.filename}
                    controls
                    autoPlay
                    className="video-player"
                  >
                    <source
                      src={`${API_BASE}/api/stream/${selectedVideo.filename}`}
                      type="video/mp4"
                    />
                    Your browser doesn't support video playback.
                  </video>
                  
                  <div className="video-details">
                    <p><strong>File:</strong> {selectedVideo.filename}</p>
                    <p><strong>Size:</strong> {selectedVideo.size_mb} MB</p>
                    <p><strong>Path:</strong> {selectedVideo.path}</p>
                  </div>
                </div>
              ) : mode === 'annotate' ? (
                <VideoAnnotator video={selectedVideo} apiBase={API_BASE} />
              ) : mode === 'gpu' ? (
                <GPUDashboard apiBase={API_BASE} />
              ) : null}
            </div>
          ) : (
            <div className="no-video">
              <h2>👈 Select a video to start</h2>
              <p>Choose from the list on the left</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
