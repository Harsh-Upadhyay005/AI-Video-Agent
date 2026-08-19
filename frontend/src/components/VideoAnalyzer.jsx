import React, { useState, useEffect, useRef } from 'react';
import apiClient from '../api/client';
import './VideoAnalyzer.css';

function VideoAnalyzer({ onAnalysisComplete, existingResult }) {
  const [url, setUrl] = useState('');
  const [language, setLanguage] = useState('english');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(existingResult);
  const [inputMode, setInputMode] = useState('url'); // 'url' or 'file'
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef(null);

  // Update result when existingResult prop changes
  useEffect(() => {
    if (existingResult) {
      setResult(existingResult);
    }
  }, [existingResult]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate input based on mode
    if (inputMode === 'url' && !url.trim()) {
      setError('Please enter a YouTube URL');
      return;
    }
    if (inputMode === 'file' && !selectedFile) {
      setError('Please select a file');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setUploadProgress(0);

    try {
      let data;
      
      if (inputMode === 'url') {
        // YouTube URL analysis
        data = await apiClient.analyzeVideo(url, language);
      } else {
        // File upload analysis
        data = await apiClient.uploadAndAnalyze(selectedFile, language, (progress) => {
          setUploadProgress(progress);
        });
      }
      
      setResult(data);
      onAnalysisComplete(data);
    } catch (err) {
      setError(err.message || 'Analysis failed');
    } finally {
      setLoading(false);
      setUploadProgress(0);
    }
  };

  const handleNewAnalysis = () => {
    setResult(null);
    setUrl('');
    setSelectedFile(null);
    setError(null);
    setUploadProgress(0);
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      validateAndSetFile(file);
    }
  };

  const validateAndSetFile = (file) => {
    // Validate file type
    const validExtensions = ['.mp3', '.mp4', '.wav', '.m4a', '.flac', '.ogg', '.aac', '.avi', '.mov', '.mkv', '.webm', '.flv'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!validExtensions.includes(fileExt)) {
      setError(`Unsupported file type: ${fileExt}. Supported: ${validExtensions.join(', ')}`);
      return;
    }

    // Validate file size (500MB max)
    const maxSize = 500 * 1024 * 1024; // 500MB
    if (file.size > maxSize) {
      setError(`File too large: ${(file.size / 1024 / 1024).toFixed(1)}MB. Maximum: 500MB`);
      return;
    }

    setSelectedFile(file);
    setError(null);
  };

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
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="video-analyzer">
      {result ? (
        <div className="results-container">
          <div className="results-header">
            <h2> Analysis Results</h2>
            <button onClick={handleNewAnalysis} className="new-analysis-btn">
               Analyze New Video
            </button>
          </div>

          <div className="results">
            <div className="result-section">
              <h3> {result.title}</h3>
            </div>

            <div className="result-section">
              <h3> Summary</h3>
              <div className="content">{result.summary}</div>
            </div>

            <div className="result-section">
              <h3> Action Items</h3>
              <pre className="content">{result.action_items}</pre>
            </div>

            <div className="result-section">
              <h3> Key Decisions</h3>
              <pre className="content">{result.key_decisions}</pre>
            </div>

            <div className="result-section">
              <h3> Open Questions</h3>
              <pre className="content">{result.open_questions}</pre>
            </div>

            <div className="result-section collapsible">
              <details>
                <summary> Full Transcript (Click to expand)</summary>
                <pre className="content transcript">{result.transcript}</pre>
              </details>
            </div>
          </div>

          <div className="next-step">
            <p> Ready to explore more? Switch to the <strong>Chat</strong> tab to ask questions about this video!</p>
          </div>
        </div>
      ) : (
        <>
          {/* Input Mode Selector */}
          <div className="input-mode-selector">
            <button
              type="button"
              className={`mode-btn ${inputMode === 'url' ? 'active' : ''}`}
              onClick={() => {
                setInputMode('url');
                setSelectedFile(null);
                setError(null);
              }}
              disabled={loading}
            >
              🔗 YouTube URL
            </button>
            <button
              type="button"
              className={`mode-btn ${inputMode === 'file' ? 'active' : ''}`}
              onClick={() => {
                setInputMode('file');
                setUrl('');
                setError(null);
              }}
              disabled={loading}
            >
              📁 Upload File
            </button>
          </div>

          <form onSubmit={handleSubmit} className="analyzer-form">
            {inputMode === 'url' ? (
              /* YouTube URL Input */
              <div className="form-group">
                <label htmlFor="url">YouTube URL</label>
                <input
                  id="url"
                  type="text"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://www.youtube.com/watch?v=..."
                  required
                  disabled={loading}
                />
              </div>
            ) : (
              /* File Upload Input */
              <div className="form-group">
                <label>Upload Audio or Video File</label>
                
                <div
                  className={`file-drop-zone ${dragActive ? 'drag-active' : ''} ${selectedFile ? 'has-file' : ''}`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".mp3,.mp4,.wav,.m4a,.flac,.ogg,.aac,.avi,.mov,.mkv,.webm,.flv"
                    onChange={handleFileSelect}
                    style={{ display: 'none' }}
                    disabled={loading}
                  />
                  
                  {selectedFile ? (
                    <div className="selected-file-info">
                      <div className="file-icon">📄</div>
                      <div className="file-details">
                        <div className="file-name">{selectedFile.name}</div>
                        <div className="file-size">{formatFileSize(selectedFile.size)}</div>
                      </div>
                      {!loading && (
                        <button
                          type="button"
                          className="remove-file-btn"
                          onClick={() => setSelectedFile(null)}
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  ) : (
                    <div className="drop-zone-content">
                      <div className="drop-icon">📤</div>
                      <p className="drop-text">Drag and drop your file here</p>
                      <p className="drop-or">or</p>
                      <button
                        type="button"
                        className="browse-btn"
                        onClick={handleBrowseClick}
                        disabled={loading}
                      >
                        Browse Files
                      </button>
                      <p className="file-info">
                        Supported: MP3, MP4, WAV, M4A, FLAC, OGG, AAC, AVI, MOV, MKV, WebM, FLV
                        <br />
                        Max size: 500MB
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            <div className="form-group">
              <label htmlFor="language">Language</label>
              <select
                id="language"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                disabled={loading}
              >
                <option value="english">English</option>
                <option value="hinglish">Hinglish</option>
              </select>
            </div>

            <button type="submit" disabled={loading || (inputMode === 'url' && !url.trim()) || (inputMode === 'file' && !selectedFile)} className="analyze-btn">
              {loading ? (
                uploadProgress > 0 && uploadProgress < 100 ? 
                  `⬆️ Uploading... ${uploadProgress}%` : 
                  '⚙️ Analyzing... (This may take 2-10 minutes)'
              ) : (
                inputMode === 'url' ? '▶️ Analyze Video' : '▶️ Analyze File'
              )}
            </button>
          </form>

          {loading && (
            <div className="loading-message">
              <div className="spinner"></div>
              {uploadProgress > 0 && uploadProgress < 100 ? (
                <p>Uploading file... {uploadProgress}%</p>
              ) : (
                <>
                  <p>Processing {inputMode === 'url' ? 'video' : 'file'}... This may take several minutes.</p>
                  <small>The backend is {inputMode === 'url' ? 'downloading, ' : ''}transcribing, and analyzing the content.</small>
                </>
              )}
            </div>
          )}

          {error && (
            <div className="error-message">
              <h3> Error</h3>
              <p>{error}</p>
              <small>Make sure the backend is running and the URL is valid.</small>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default VideoAnalyzer;

