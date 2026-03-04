import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './GPUDashboard.css';

const GPUDashboard = ({ apiBase }) => {
  const [gpuStatus, setGpuStatus] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [selectedGpu, setSelectedGpu] = useState(0);
  const [taskType, setTaskType] = useState('training');
  const [videoName, setVideoName] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadGPUStatus();
    loadJobs();
    
    // Refresh every 3 seconds
    const interval = setInterval(() => {
      loadGPUStatus();
      loadJobs();
    }, 3000);
    
    return () => clearInterval(interval);
  }, []);

  const loadGPUStatus = async () => {
    try {
      const response = await axios.get(`${apiBase}/api/gpu/status`);
      setGpuStatus(response.data);
    } catch (err) {
      console.error('Error loading GPU status:', err);
    }
  };

  const loadJobs = async () => {
    try {
      const response = await axios.get(`${apiBase}/api/jobs`);
      setJobs(response.data.jobs);
    } catch (err) {
      console.error('Error loading jobs:', err);
    }
  };

  const submitJob = async () => {
    if (!videoName.trim()) {
      alert('Please enter a video name');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${apiBase}/api/jobs/submit`, {
        task_type: taskType,
        video_name: videoName,
        gpu_id: selectedGpu,
        parameters: {
          epochs: 10,
          batch_size: 32
        }
      });
      
      alert(`✅ Job submitted! ID: ${response.data.job_id}`);
      setVideoName('');
      loadJobs();
    } catch (err) {
      alert('Error submitting job: ' + err.message);
    }
    setLoading(false);
  };

  const cancelJob = async (jobId) => {
    try {
      await axios.delete(`${apiBase}/api/jobs/${jobId}`);
      alert(`Job ${jobId} cancelled`);
      loadJobs();
    } catch (err) {
      alert('Error cancelling job: ' + err.message);
    }
  };

  return (
    <div className="gpu-dashboard">
      <h2>🖥️ GPU & Job Management</h2>

      {/* GPU Status */}
      <div className="gpu-status-section">
        <h3>GPU Status</h3>
        {!gpuStatus && <p>Loading GPU status...</p>}
        
        {gpuStatus && !gpuStatus.available && (
          <div className="no-gpu-warning">
            <p>⚠️ {gpuStatus.message}</p>
            <p className="small-text">Jobs will be queued but won't execute until GPUs are available.</p>
          </div>
        )}

        {gpuStatus && gpuStatus.available && (
          <div className="gpu-grid">
            {gpuStatus.gpus.map((gpu) => (
              <div key={gpu.id} className={`gpu-card ${gpu.available ? 'available' : 'busy'}`}>
                <div className="gpu-header">
                  <h4>GPU {gpu.id}</h4>
                  <span className={`status-badge ${gpu.available ? 'available' : 'busy'}`}>
                    {gpu.available ? 'Available' : 'Busy'}
                  </span>
                </div>
                
                <p className="gpu-name">{gpu.name}</p>
                
                <div className="gpu-stats">
                  <div className="stat">
                    <span className="label">Utilization:</span>
                    <div className="progress-bar">
                      <div 
                        className="progress-fill" 
                        style={{ width: `${gpu.gpu_utilization_percent}%` }}
                      />
                    </div>
                    <span className="value">{gpu.gpu_utilization_percent}%</span>
                  </div>

                  <div className="stat">
                    <span className="label">Memory:</span>
                    <div className="progress-bar">
                      <div 
                        className="progress-fill memory" 
                        style={{ width: `${gpu.memory_usage_percent}%` }}
                      />
                    </div>
                    <span className="value">
                      {gpu.memory_used_gb.toFixed(1)} / {gpu.memory_total_gb.toFixed(1)} GB
                    </span>
                  </div>

                  <div className="stat-row">
                    <span>🌡️ {gpu.temperature_c}°C</span>
                    <span>🔢 {gpu.process_count} processes</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Job Submission */}
      <div className="job-submission-section">
        <h3>Submit New Job</h3>
        <div className="job-form">
          <div className="form-row">
            <label>
              Task Type:
              <select value={taskType} onChange={(e) => setTaskType(e.target.value)}>
                <option value="training">Model Training</option>
                <option value="inference">Inference</option>
                <option value="preprocessing">Preprocessing</option>
                <option value="custom">Custom Task</option>
              </select>
            </label>

            <label>
              Video Name:
              <input 
                type="text" 
                value={videoName}
                onChange={(e) => setVideoName(e.target.value)}
                placeholder="e.g., sample_video"
              />
            </label>

            <label>
              Select GPU:
              <select value={selectedGpu} onChange={(e) => setSelectedGpu(parseInt(e.target.value))}>
                {gpuStatus?.gpus?.map((gpu) => (
                  <option key={gpu.id} value={gpu.id}>
                    GPU {gpu.id} - {gpu.name} {gpu.available ? '(Available)' : '(Busy)'}
                  </option>
                ))}
                {(!gpuStatus || !gpuStatus.gpus || gpuStatus.gpus.length === 0) && (
                  <option value={0}>GPU 0 (Default)</option>
                )}
              </select>
            </label>
          </div>

          <button 
            className="submit-job-btn"
            onClick={submitJob}
            disabled={loading}
          >
            {loading ? '⏳ Submitting...' : '🚀 Submit Job'}
          </button>
        </div>
      </div>

      {/* Jobs List */}
      <div className="jobs-section">
        <h3>Job Queue ({jobs.length})</h3>
        {jobs.length === 0 ? (
          <p className="no-jobs">No jobs submitted yet</p>
        ) : (
          <div className="jobs-list">
            {jobs.map((job) => (
              <div key={job.job_id} className={`job-card status-${job.status}`}>
                <div className="job-header">
                  <div>
                    <span className="job-id">#{job.job_id}</span>
                    <span className="job-type">{job.task_type}</span>
                  </div>
                  <span className={`status-badge ${job.status}`}>
                    {job.status}
                  </span>
                </div>

                <div className="job-details">
                  <p><strong>Video:</strong> {job.video_name}</p>
                  <p><strong>GPU:</strong> {job.gpu_id}</p>
                  <p><strong>Created:</strong> {new Date(job.created_at).toLocaleString()}</p>
                  {job.progress > 0 && (
                    <div className="progress-bar">
                      <div className="progress-fill" style={{ width: `${job.progress}%` }} />
                    </div>
                  )}
                </div>

                {job.status === 'queued' && (
                  <button 
                    className="cancel-btn"
                    onClick={() => cancelJob(job.job_id)}
                  >
                    ❌ Cancel
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default GPUDashboard;