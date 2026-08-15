import React, { useState, useRef, useEffect } from 'react';
import apiClient from '../api/client';
import './ChatInterface.css';

function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const data = await apiClient.sendChatMessage(input);
      const assistantMessage = {
        role: 'assistant',
        content: data.answer,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage = {
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error.message}`,
        timestamp: new Date().toISOString(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    if (window.confirm('Clear all messages?')) {
      setMessages([]);
    }
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h3>💬 Chat with Your Transcript</h3>
        <button onClick={clearChat} className="clear-btn">Clear</button>
      </div>

      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-state">
            <p>👋 Ask me anything about the transcript!</p>
            <div className="suggestions">
              <p>Try asking:</p>
              <button onClick={() => setInput('What are the main points discussed?')}>
                What are the main points discussed?
              </button>
              <button onClick={() => setInput('Summarize the key decisions')}>
                Summarize the key decisions
              </button>
              <button onClick={() => setInput('What action items were assigned?')}>
                What action items were assigned?
              </button>
            </div>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role} ${msg.isError ? 'error' : ''}`}>
              <div className="message-avatar">
                {msg.role === 'user' ? '👤' : '🤖'}
              </div>
              <div className="message-content">
                <div className="message-header">
                  <strong>{msg.role === 'user' ? 'You' : 'AI Assistant'}</strong>
                  <small>{new Date(msg.timestamp).toLocaleTimeString()}</small>
                </div>
                <p>{msg.content}</p>
              </div>
            </div>
          ))
        )}
        {loading && (
          <div className="message assistant typing">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={sendMessage} className="chat-input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about the transcript..."
          disabled={loading}
          className="chat-input"
        />
        <button type="submit" disabled={loading || !input.trim()} className="send-btn">
          {loading ? '⏳' : '📤'}
        </button>
      </form>
    </div>
  );
}

export default ChatInterface;
