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
