import React, { useState, useRef, useEffect } from 'react';
import './VideoAnnotator.css';
import axios from 'axios';

const VideoAnnotator = ({ video, apiBase }) => {
  const canvasRef = useRef(null);
  const imageRef = useRef(null);
  
  const [frames, setFrames] = useState([]);
  const [currentFrameIndex, setCurrentFrameIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [extractionProgress, setExtractionProgress] = useState(0);
  const [extractionMessage, setExtractionMessage] = useState('');
  const [framesExtracted, setFramesExtracted] = useState(false);
  
  // Drawing state
  const [currentTool, setCurrentTool] = useState('box');
  const [isDrawing, setIsDrawing] = useState(false);
  const [startPos, setStartPos] = useState({ x: 0, y: 0 });
  const [currentBox, setCurrentBox] = useState(null);
  const [polygonPoints, setPolygonPoints] = useState([]);
  const [freehandPath, setFreehandPath] = useState([]);
  const [annotations, setAnnotations] = useState({});

  const videoName = video.filename.replace(/\.[^/.]+$/, "");

  useEffect(() => {
    checkFrames();
  }, []);

  useEffect(() => {
    if (framesExtracted && frames.length > 0) {
      loadAnnotations();
    }
  }, [framesExtracted, frames]);

  const checkFrames = async () => {
    try {
      const response = await axios.get(`${apiBase}/api/frames/${videoName}`);
      setFrames(response.data.frames);
      setFramesExtracted(true);
    } catch (err) {
      setFramesExtracted(false);
    }
  };

  // NEW: Async frame extraction with progress tracking!
  const extractFrames = async () => {
    setExtracting(true);
    setExtractionProgress(0);
    setExtractionMessage('Starting extraction...');
    
    try {
      // Start extraction
      const response = await axios.post(`${apiBase}/api/extract-frames/${video.filename}?fps=5`);
      
      if (!response.data.success) {
        alert('Failed to start extraction');
        setExtracting(false);
        return;
      }
      
      // Poll for progress
      let progress = 0;
      let attempts = 0;
      const maxAttempts = 300; // 5 minutes max
      
      while (progress < 100 && attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second
        attempts++;
        
        try {
          const progressResponse = await axios.get(`${apiBase}/api/extract-frames/${videoName}/progress`);
          const data = progressResponse.data;
          
          progress = data.progress || 0;
          setExtractionProgress(progress);
          setExtractionMessage(data.message || 'Extracting...');
          
          if (data.status === 'completed') {
            // Load the frames
            const framesResponse = await axios.get(`${apiBase}/api/frames/${videoName}`);
            setFrames(framesResponse.data.frames);
            setFramesExtracted(true);
            setExtractionMessage(`✅ Extracted ${framesResponse.data.frame_count} frames!`);
            setTimeout(() => {
              setExtracting(false);
              setExtractionProgress(0);
            }, 2000);
            break;
          } else if (data.status === 'failed') {
            alert(`❌ Frame extraction failed: ${data.message}`);
            setExtracting(false);
            setExtractionProgress(0);
            break;
          }
        } catch (pollError) {
          console.error('Error polling progress:', pollError);
        }
      }
      
      if (attempts >= maxAttempts) {
        alert('Frame extraction timed out. The video might be too large.');
        setExtracting(false);
      }
      
    } catch (err) {
      alert('Error extracting frames: ' + err.message);
      console.error(err);
      setExtracting(false);
      setExtractionProgress(0);
    }
  };

  const loadAnnotations = async () => {
    try {
      const response = await axios.get(`${apiBase}/api/annotations/${videoName}`);
      if (response.data.annotations) {
        const convertedAnnotations = {};
        Object.keys(response.data.annotations).forEach(key => {
          convertedAnnotations[parseInt(key)] = response.data.annotations[key];
        });
        setAnnotations(convertedAnnotations);
        console.log(`Loaded ${response.data.annotation_count} annotations`);
      }
    } catch (err) {
      console.log('No existing annotations found');
    }
  };

  const saveAnnotations = async () => {
    try {
      const response = await axios.post(
        `${apiBase}/api/annotations/${videoName}`,
        annotations
      );
      alert(`✅ Saved ${response.data.annotation_count} annotations!`);
    } catch (err) {
      alert('Error saving annotations: ' + err.message);
      console.error(err);
    }
  };

  const exportAnnotations = async (format = 'json') => {
    try {
      const url = `${apiBase}/api/annotations/${videoName}/export?format=${format}`;
      window.open(url, '_blank');
    } catch (err) {
      alert('Error exporting annotations: ' + err.message);
    }
  };

  const getCurrentFrameUrl = () => {
    if (frames.length === 0) return null;
    return `${apiBase}/api/frame-image/${videoName}/${frames[currentFrameIndex]}`;
  };

  const drawAnnotations = () => {
    const canvas = canvasRef.current;
    const image = imageRef.current;
    if (!canvas || !image) return;

    const ctx = canvas.getContext('2d');
    canvas.width = image.width;
    canvas.height = image.height;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    const frameAnnotations = annotations[currentFrameIndex] || [];
    
    frameAnnotations.forEach((annotation, index) => {
      ctx.strokeStyle = '#667eea';
      ctx.fillStyle = '#667eea';
      ctx.lineWidth = 3;

      if (annotation.type === 'box') {
        ctx.strokeRect(annotation.x, annotation.y, annotation.width, annotation.height);
        ctx.fillRect(annotation.x, annotation.y - 25, 80, 25);
        ctx.fillStyle = 'white';
        ctx.font = 'bold 14px Arial';
        ctx.fillText(`Box ${index + 1}`, annotation.x + 5, annotation.y - 7);
      } 
      else if (annotation.type === 'polygon') {
        if (annotation.points && annotation.points.length > 0) {
          ctx.beginPath();
          ctx.moveTo(annotation.points[0].x, annotation.points[0].y);
          annotation.points.forEach(point => {
            ctx.lineTo(point.x, point.y);
          });
          ctx.closePath();
          ctx.stroke();
          
          annotation.points.forEach(point => {
            ctx.beginPath();
            ctx.arc(point.x, point.y, 4, 0, 2 * Math.PI);
            ctx.fill();
          });
          
          ctx.fillRect(annotation.points[0].x, annotation.points[0].y - 25, 100, 25);
          ctx.fillStyle = 'white';
          ctx.font = 'bold 14px Arial';
          ctx.fillText(`Polygon ${index + 1}`, annotation.points[0].x + 5, annotation.points[0].y - 7);
        }
      }
      else if (annotation.type === 'freehand') {
        if (annotation.path && annotation.path.length > 1) {
          ctx.beginPath();
          ctx.moveTo(annotation.path[0].x, annotation.path[0].y);
          annotation.path.forEach(point => {
            ctx.lineTo(point.x, point.y);
          });
          ctx.stroke();
          
          ctx.fillRect(annotation.path[0].x, annotation.path[0].y - 25, 110, 25);
          ctx.fillStyle = 'white';
          ctx.font = 'bold 14px Arial';
          ctx.fillText(`Freehand ${index + 1}`, annotation.path[0].x + 5, annotation.path[0].y - 7);
        }
      }
      else if (annotation.type === 'point') {
        ctx.beginPath();
        ctx.arc(annotation.x, annotation.y, 6, 0, 2 * Math.PI);
        ctx.fill();
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 2;
        ctx.stroke();
        
        ctx.fillStyle = '#667eea';
        ctx.fillRect(annotation.x + 10, annotation.y - 15, 85, 25);
        ctx.fillStyle = 'white';
        ctx.font = 'bold 14px Arial';
        ctx.fillText(`Point ${index + 1}`, annotation.x + 15, annotation.y + 3);
      }
    });
    
    ctx.strokeStyle = '#48bb78';
    ctx.fillStyle = '#48bb78';
    ctx.lineWidth = 3;
    ctx.setLineDash([5, 5]);

    if (currentTool === 'box' && currentBox) {
      ctx.strokeRect(currentBox.x, currentBox.y, currentBox.width, currentBox.height);
    }
    else if (currentTool === 'polygon' && polygonPoints.length > 0) {
      ctx.beginPath();
      ctx.moveTo(polygonPoints[0].x, polygonPoints[0].y);
      polygonPoints.forEach(point => {
        ctx.lineTo(point.x, point.y);
      });
      ctx.stroke();
      
      polygonPoints.forEach(point => {
        ctx.beginPath();
        ctx.arc(point.x, point.y, 4, 0, 2 * Math.PI);
        ctx.fill();
      });
    }
    else if (currentTool === 'freehand' && freehandPath.length > 1) {
      ctx.beginPath();
      ctx.moveTo(freehandPath[0].x, freehandPath[0].y);
      freehandPath.forEach(point => {
        ctx.lineTo(point.x, point.y);
      });
      ctx.stroke();
    }

    ctx.setLineDash([]);
  };

  useEffect(() => {
    drawAnnotations();
  }, [annotations, currentFrameIndex, currentBox, polygonPoints, freehandPath]);

  const handleImageLoad = () => {
    drawAnnotations();
  };

  const handleMouseDown = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    if (currentTool === 'box') {
      setIsDrawing(true);
      setStartPos({ x, y });
      setCurrentBox({ x, y, width: 0, height: 0 });
    }
    else if (currentTool === 'freehand') {
      setIsDrawing(true);
      setFreehandPath([{ x, y }]);
    }
    else if (currentTool === 'point') {
      const frameAnnotations = annotations[currentFrameIndex] || [];
      setAnnotations({
        ...annotations,
        [currentFrameIndex]: [...frameAnnotations, { type: 'point', x, y }]
      });
    }
  };

  const handleMouseMove = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    if (currentTool === 'box' && isDrawing) {
      setCurrentBox({
        x: startPos.x,
        y: startPos.y,
        width: x - startPos.x,
        height: y - startPos.y
      });
    }
    else if (currentTool === 'freehand' && isDrawing) {
      setFreehandPath(prev => [...prev, { x, y }]);
    }
  };

  const handleMouseUp = () => {
    if (currentTool === 'box' && isDrawing && currentBox) {
      if (Math.abs(currentBox.width) > 10 && Math.abs(currentBox.height) > 10) {
        const normalizedBox = {
          type: 'box',
          x: currentBox.width < 0 ? currentBox.x + currentBox.width : currentBox.x,
          y: currentBox.height < 0 ? currentBox.y + currentBox.height : currentBox.y,
          width: Math.abs(currentBox.width),
          height: Math.abs(currentBox.height),
        };
        
        const frameAnnotations = annotations[currentFrameIndex] || [];
        setAnnotations({
          ...annotations,
          [currentFrameIndex]: [...frameAnnotations, normalizedBox]
        });
      }
      setIsDrawing(false);
      setCurrentBox(null);
    }
    else if (currentTool === 'freehand' && isDrawing) {
      if (freehandPath.length > 5) {
        const frameAnnotations = annotations[currentFrameIndex] || [];
        setAnnotations({
          ...annotations,
          [currentFrameIndex]: [...frameAnnotations, { type: 'freehand', path: freehandPath }]
        });
      }
      setIsDrawing(false);
      setFreehandPath([]);
    }
  };

  const handleCanvasClick = (e) => {
    if (currentTool === 'polygon') {
      const canvas = canvasRef.current;
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      setPolygonPoints(prev => [...prev, { x, y }]);
    }
  };

  const finishPolygon = () => {
    if (polygonPoints.length > 2) {
      const frameAnnotations = annotations[currentFrameIndex] || [];
      setAnnotations({
        ...annotations,
        [currentFrameIndex]: [...frameAnnotations, { type: 'polygon', points: polygonPoints }]
      });
    }
    setPolygonPoints([]);
  };

  const cancelPolygon = () => {
    setPolygonPoints([]);
  };

  const goToNextFrame = () => {
    if (currentFrameIndex < frames.length - 1) {
      setCurrentFrameIndex(currentFrameIndex + 1);
      setPolygonPoints([]);
      setFreehandPath([]);
    }
  };

  const goToPrevFrame = () => {
    if (currentFrameIndex > 0) {
      setCurrentFrameIndex(currentFrameIndex - 1);
      setPolygonPoints([]);
      setFreehandPath([]);
    }
  };

  const goToFrame = (index) => {
    setCurrentFrameIndex(index);
    setPolygonPoints([]);
    setFreehandPath([]);
  };

  const deleteLastBox = () => {
    const frameAnnotations = annotations[currentFrameIndex] || [];
    if (frameAnnotations.length === 0) return;
    
    setAnnotations({
      ...annotations,
      [currentFrameIndex]: frameAnnotations.slice(0, -1)
    });
  };

  const clearCurrentFrame = () => {
    const newAnnotations = { ...annotations };
    delete newAnnotations[currentFrameIndex];
    setAnnotations(newAnnotations);
  };

  const getTotalAnnotations = () => {
    return Object.values(annotations).reduce((sum, boxes) => sum + boxes.length, 0);
  };

  const getCurrentFrameAnnotations = () => {
    return annotations[currentFrameIndex] || [];
  };

  if (!framesExtracted) {
    return (
      <div className="video-annotator">
        <h2>🎬 {video.filename}</h2>
        <div className="extract-frames-panel">
          <div className="info-box">
            <h3>📹 Frame Extraction Required</h3>
            <p>To annotate this video, we first need to extract frames.</p>
            <p>This will create individual JPEG images from the video.</p>
            <ul>
              <li>Extracts 5 frames per second</li>
              <li>High quality JPEGs</li>
              <li>Runs in background - won't freeze the app!</li>
            </ul>
          </div>
          
          {/* PROGRESS BAR! */}
          {extracting && (
            <div className="progress-container">
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${extractionProgress}%` }}
                />
              </div>
              <p className="progress-text">{extractionMessage} ({extractionProgress}%)</p>
            </div>
          )}
          
          <button 
            className="extract-button"
            onClick={extractFrames}
            disabled={extracting}
          >
            {extracting ? `⏳ Extracting... ${extractionProgress}%` : '🎬 Extract Frames'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="video-annotator">
      <h2>🎨 Frame-Based Annotation: {video.filename}</h2>
      
      <div className="annotation-stats">
        <span>Frame {currentFrameIndex + 1} of {frames.length}</span>
        <span>•</span>
        <span>{getCurrentFrameAnnotations().length} annotations on this frame</span>
        <span>•</span>
        <span>{getTotalAnnotations()} total annotations</span>
      </div>

      <div className="tool-selector">
        <button 
          className={currentTool === 'box' ? 'active' : ''}
          onClick={() => { setCurrentTool('box'); setPolygonPoints([]); }}
          title="Bounding Box"
        >
          ⬜ Box
        </button>
        <button 
          className={currentTool === 'polygon' ? 'active' : ''}
          onClick={() => { setCurrentTool('polygon'); setPolygonPoints([]); }}
          title="Polygon - Click points, then Finish"
        >
          ⬟ Polygon
        </button>
        <button 
          className={currentTool === 'freehand' ? 'active' : ''}
          onClick={() => { setCurrentTool('freehand'); setPolygonPoints([]); }}
          title="Freehand Drawing"
        >
          ✏️ Freehand
        </button>
        <button 
          className={currentTool === 'point' ? 'active' : ''}
          onClick={() => { setCurrentTool('point'); setPolygonPoints([]); }}
          title="Keypoint - Click to mark"
        >
          📍 Point
        </button>
        
        {currentTool === 'polygon' && polygonPoints.length > 0 && (
          <>
            <button onClick={finishPolygon} className="finish-polygon">
              ✓ Finish ({polygonPoints.length} points)
            </button>
            <button onClick={cancelPolygon} className="cancel-polygon">
              ✗ Cancel
            </button>
          </>
        )}
      </div>

      <div className="frame-viewer">
        <div className="canvas-container">
          <img
            ref={imageRef}
            src={getCurrentFrameUrl()}
            alt={`Frame ${currentFrameIndex + 1}`}
            onLoad={handleImageLoad}
            className="frame-image"
          />
          <canvas
            ref={canvasRef}
            className="annotation-canvas"
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            onClick={handleCanvasClick}
            style={{ cursor: 'crosshair' }}
          />
        </div>
      </div>

      <div className="controls-panel">
        <div className="navigation-controls">
          <button onClick={goToPrevFrame} disabled={currentFrameIndex === 0}>
            ⏮ Previous
          </button>
          <span className="frame-counter">
            Frame {currentFrameIndex + 1} / {frames.length}
          </span>
          <button onClick={goToNextFrame} disabled={currentFrameIndex === frames.length - 1}>
            Next ⏭
          </button>
        </div>

        <div className="annotation-controls">
          <button onClick={deleteLastBox} disabled={getCurrentFrameAnnotations().length === 0}>
            🗑️ Delete Last
          </button>
          <button onClick={clearCurrentFrame} disabled={getCurrentFrameAnnotations().length === 0}>
            ❌ Clear Frame
          </button>
          <button onClick={saveAnnotations} disabled={getTotalAnnotations() === 0}>
            💾 Save
          </button>
          <button onClick={() => exportAnnotations('json')} disabled={getTotalAnnotations() === 0}>
            📥 Export JSON
          </button>
          <button onClick={() => exportAnnotations('coco')} disabled={getTotalAnnotations() === 0}>
            📥 Export COCO
          </button>
        </div>
      </div>

      <div className="frame-timeline">
        <h3>Frame Timeline</h3>
        <div className="thumbnail-strip">
          {frames.map((frame, index) => {
            const hasAnnotations = annotations[index] && annotations[index].length > 0;
            return (
              <div
                key={index}
                className={`thumbnail ${currentFrameIndex === index ? 'active' : ''} ${hasAnnotations ? 'annotated' : ''}`}
                onClick={() => goToFrame(index)}
                title={`Frame ${index + 1}${hasAnnotations ? ` (${annotations[index].length} annotations)` : ''}`}
              >
                <img src={`${apiBase}/api/frame-image/${videoName}/${frame}`} alt={`Frame ${index + 1}`} />
                {hasAnnotations && <div className="annotation-badge">{annotations[index].length}</div>}
              </div>
            );
          })}
        </div>
      </div>

      {getCurrentFrameAnnotations().length > 0 && (
        <div className="annotations-list">
          <h3>Annotations on Frame {currentFrameIndex + 1}</h3>
          <div className="box-list">
            {getCurrentFrameAnnotations().map((annotation, index) => (
              <div key={index} className="box-item">
                <span className="box-number">
                  {annotation.type === 'box' && '⬜'} 
                  {annotation.type === 'polygon' && '⬟'}
                  {annotation.type === 'freehand' && '✏️'}
                  {annotation.type === 'point' && '📍'}
                  {' '}{annotation.type} {index + 1}
                </span>
                <span className="box-coords">
                  {annotation.type === 'box' && `x: ${Math.round(annotation.x)}, y: ${Math.round(annotation.y)}, w: ${Math.round(annotation.width)}, h: ${Math.round(annotation.height)}`}
                  {annotation.type === 'polygon' && `${annotation.points.length} points`}
                  {annotation.type === 'freehand' && `${annotation.path.length} points`}
                  {annotation.type === 'point' && `x: ${Math.round(annotation.x)}, y: ${Math.round(annotation.y)}`}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoAnnotator;