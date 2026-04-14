import React, { useState, useRef } from 'react';
import axios from 'axios';
import './VideoUpload.css';

function VideoUpload({ apiBase, onUploadComplete }) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const fileInputRef = useRef(null);

  const supportedFormats = [
    '.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', 
    '.webm', '.m4v', '.mpg', '.mpeg', '.3gp', '.ts', '.mts'
  ];

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = async (file) => {
    setError(null);
    setSuccess(null);

    // Validate file type
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();
    if (!supportedFormats.includes(fileExt)) {
      setError(`Invalid file type. Supported formats: ${supportedFormats.join(', ')}`);
      return;
    }

    // Upload file
    const formData = new FormData();
    formData.append('file', file);

    try {
      setUploading(true);
      setProgress(0);

      const response = await axios.post(`${apiBase}/api/videos/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setProgress(percentCompleted);
        },
      });

      setSuccess(`✅ ${response.data.message}`);
      setUploading(false);
      setProgress(0);

      // Notify parent component
      if (onUploadComplete) {
        onUploadComplete();
      }

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);

    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.');
      setUploading(false);
      setProgress(0);
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current.click();
  };

  return (
    <div className="video-upload-container">
      <h3>📤 Upload Video</h3>
      
      <div
        className={`upload-area ${dragActive ? 'drag-active' : ''} ${uploading ? 'uploading' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={!uploading ? handleButtonClick : undefined}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={supportedFormats.join(',')}
          onChange={handleChange}
          style={{ display: 'none' }}
          disabled={uploading}
        />

        {uploading ? (
          <div className="upload-progress">
            <div className="spinner"></div>
            <p>Uploading... {progress}%</p>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>
        ) : (
          <div className="upload-prompt">
            <div className="upload-icon">📁</div>
            <p className="upload-text">
              <strong>Click to browse</strong> or drag and drop
            </p>
            <p className="upload-formats">
              Supported: MP4, AVI, MOV, MKV, FLV, WMV, WebM, and more
            </p>
          </div>
        )}
      </div>

      {error && (
        <div className="upload-message error">
          ❌ {error}
        </div>
      )}

      {success && (
        <div className="upload-message success">
          {success}
        </div>
      )}
    </div>
  );
}

export default VideoUpload;