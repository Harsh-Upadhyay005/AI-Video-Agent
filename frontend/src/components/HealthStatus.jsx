import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import './HealthStatus.css';

function HealthStatus() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      setLoading(true);
      const data = await apiClient.checkHealth();
      setHealth(data);
      setError(null);
    } catch (err) {
      setError('Backend not connected');
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !health) {
    return <div className="health-status loading">Connecting to backend...</div>;
  }

  if (error) {
    return (
      <div className="health-status error">
        <span>[something wrong] {error}</span>
        <button onClick={checkHealth} className="retry-btn">Retry</button>
      </div>
    );
  }

  return (
    <div className="health-status success">
      <span>[okay] Backend connected</span>
      <small>{health?.service}</small>
    </div>
  );
}

export default HealthStatus;
