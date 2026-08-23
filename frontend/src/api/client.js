// API client for backend communication
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class APIClient {
  constructor(baseURL = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      // Handle non-JSON responses
      const contentType = response.headers.get('content-type');
      let data;
      
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        const text = await response.text();
        data = { message: text };
      }

      if (!response.ok) {
        const errorMessage = data.message || data.detail || `HTTP ${response.status}: ${response.statusText}`;
        throw new Error(errorMessage);
      }

      return data;
    } catch (error) {
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error('Cannot connect to backend. Make sure backend is running on http://localhost:8000');
      }
      console.error('API Error:', error);
      throw error;
    }
  }

  // Health check
  async checkHealth() {
    return this.request('/health');
  }

  async checkDetailedHealth() {
    return this.request('/health/detailed');
  }

  // Video analysis
  async analyzeVideo(source, language = 'english') {
    return this.request('/api/v1/analyze/sync', {
      method: 'POST',
      body: JSON.stringify({ source, language }),
    });
  }

  async analyzeVideoAsync(source, language = 'english') {
    return this.request('/api/v1/analyze', {
      method: 'POST',
      body: JSON.stringify({ source, language }),
    });
  }

  // File upload and analysis
  async uploadAndAnalyze(file, language = 'english', onProgress = null) {
    console.log('=== API CLIENT: uploadAndAnalyze START ===');
    console.log('File:', file);
    console.log('File name:', file?.name);
    console.log('File size:', file?.size);
    console.log('File type:', file?.type);
    console.log('Language:', language);
    console.log('Base URL:', this.baseURL);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('language', language);

    const url = `${this.baseURL}/api/v1/upload`;
    console.log('Request URL:', url);
    console.log('FormData contents:');
    for (let pair of formData.entries()) {
      console.log('  -', pair[0], ':', pair[1]);
    }

    try {
      console.log('Sending fetch request...');
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
        // Don't set Content-Type header - browser will set it with boundary
      });

      console.log('Response received:', response.status, response.statusText);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));

      const contentType = response.headers.get('content-type');
      let data;

      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
        console.log('Response data (JSON):', data);
      } else {
        const text = await response.text();
        console.log('Response data (text):', text);
        data = { message: text };
      }

      if (!response.ok) {
        const errorMessage = data.detail || data.message || `Upload failed with status ${response.status}`;
        console.error('Upload failed:', errorMessage);
        throw new Error(errorMessage);
      }

      console.log('Upload successful, job_id:', data.job_id);

      // If we got a job_id, poll for progress
      if (data.job_id) {
        console.log('Starting progress polling for job:', data.job_id);
        return this.pollJobProgress(data.job_id, onProgress);
      }

      return data;
    } catch (error) {
      console.error('=== API CLIENT: uploadAndAnalyze ERROR ===');
      console.error('Error name:', error.name);
      console.error('Error message:', error.message);
      console.error('Error stack:', error.stack);
      
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error('Cannot connect to backend. Make sure backend is running on http://localhost:8000');
      }
      console.error('Upload Error:', error);
      throw error;
    }
  }

  // Poll job progress using SSE
  async pollJobProgress(jobId, onProgress = null) {
    return new Promise((resolve, reject) => {
      const eventSource = new EventSource(`${this.baseURL}/api/v1/progress/${jobId}`);
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Report progress if callback provided
          if (onProgress && data.progress) {
            onProgress(data.progress);
          }

          // Check if completed
          if (data.status === 'completed' && data.result) {
            eventSource.close();
            resolve(data.result);
          } else if (data.status === 'failed') {
            eventSource.close();
            reject(new Error(data.error || data.message || 'Analysis failed'));
          }
        } catch (err) {
          console.error('Error parsing SSE data:', err);
        }
      };

      eventSource.onerror = (error) => {
        eventSource.close();
        reject(new Error('Lost connection to server. Analysis may still be in progress.'));
      };

      // Timeout after 30 minutes
      setTimeout(() => {
        eventSource.close();
        reject(new Error('Analysis timed out after 30 minutes'));
      }, 30 * 60 * 1000);
    });
  }

  async getAnalysisStatus(jobId) {
    return this.request(`/api/v1/status/${jobId}`);
  }

  // Chat
  async sendChatMessage(question, sessionId = null) {
    return this.request('/api/v1/chat', {
      method: 'POST',
      body: JSON.stringify({ question, session_id: sessionId }),
    });
  }

  async clearChatSession(sessionId) {
    return this.request(`/api/v1/chat/session/${sessionId}`, {
      method: 'DELETE',
    });
  }
}

export default new APIClient();
