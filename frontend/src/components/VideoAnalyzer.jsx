import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import './VideoAnalyzer.css';

function VideoAnalyzer({ onAnalysisComplete, existingResult }) {
  const [url, setUrl] = useState('');
  const [language, setLanguage] = useState('english');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(existingResult);

  // Update result when existingResult prop changes
  useEffect(() => {
    if (existingResult) {
      setResult(existingResult);
    }
  }, [existingResult]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await apiClient.analyzeVideo(url, language);
      setResult(data);
      onAnalysisComplete(data);
    } catch (err) {
      setError(err.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const handleNewAnalysis = () => {
    setResult(null);
    setUrl('');
    setError(null);
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
          <form onSubmit={handleSubmit} className="analyzer-form">
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

            <button type="submit" disabled={loading} className="analyze-btn">
              {loading ? ' Analyzing... (This may take 2-10 minutes)' : ' Analyze Video'}
            </button>
          </form>

          {loading && (
            <div className="loading-message">
              <div className="spinner"></div>
              <p>Processing video... This may take several minutes depending on video length.</p>
              <small>The backend is downloading, transcribing, and analyzing the video.</small>
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

