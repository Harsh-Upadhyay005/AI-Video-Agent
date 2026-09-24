import React, { useState, useEffect, useRef } from "react";
import { MessageSquare, Send, Bot, User, RefreshCw, Copy, Check, AlertCircle } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { AnalysisData, Message } from "../types/analysis";
import apiClient from "../api/client";

interface InteractiveChatProps {
  currentAnalysis: AnalysisData | null;
}

const PRESET_VIDEO_QUESTIONS = [
  "What are the main decisions made in this video?",
  "List all action items with assigned tasks.",
  "Summarize the technical architecture in 3 points.",
  "What are the key risks or open questions mentioned?"
];

const PRESET_PDF_QUESTIONS = [
  "Summarize the executive findings of this document.",
  "What are the primary action items and deadlines?",
  "Extract key architectural or strategic decisions.",
  "What potential risks or open questions are noted?"
];

export const InteractiveChat: React.FC<InteractiveChatProps> = ({ currentAnalysis }) => {
  const isPdf = currentAnalysis?.type === "pdf";

  const [messages, setMessages] = useState<Message[]>([
    {
      id: "init",
      sender: "assistant",
      text: currentAnalysis
        ? `Hello! I have analyzed "${currentAnalysis.title}". Ask me anything about the content, key takeaways, decisions, or timestamps!`
        : "Hello! Select or analyze a video, audio recording, or PDF document above, then ask me anything about the content.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [inputQuestion, setInputQuestion] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (currentAnalysis) {
      setMessages([
        {
          id: "init-analysis",
          sender: "assistant",
          text: `Loaded analysis for "${currentAnalysis.title}". I'm ready to answer any questions based on the full ${
            currentAnalysis.type === "pdf" ? "document content" : "transcript"
          }!`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    }
  }, [currentAnalysis]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const handleSendQuestion = async (qText?: string) => {
    const question = qText || inputQuestion.trim();
    if (!question) return;

    console.log('=== InteractiveChat: Sending question ===');
    console.log('Question:', question);
    console.log('Current analysis:', currentAnalysis);

    const userMsg: Message = {
      id: Date.now().toString(),
      sender: "user",
      text: question,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInputQuestion("");
    setIsTyping(true);

    try {
      const sessionId = currentAnalysis?.job_id || null;
      const data = await apiClient.sendChatMessage(question, sessionId);
      
      console.log('  Response received:', data);
      
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: "assistant",
        text: data.answer || "No response received.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      
      setMessages(prev => [...prev, aiMsg]);
      setIsTyping(false);
      
    } catch (error) {
      console.error('=== InteractiveChat: Request ERROR ===');
      console.error('Error object:', error);
      console.error('Error type:', error?.constructor?.name);
      console.error('Error message:', error instanceof Error ? error.message : String(error));
      
      // Log additional error details if available
      if (error && typeof error === 'object') {
        console.error('Error details:', {
          status: (error as any).status,
          statusText: (error as any).statusText,
          data: (error as any).data,
          isNetworkError: (error as any).isNetworkError
        });
      }
      
      setIsTyping(false);
      
      // Extract meaningful error message
      let errorMessage = 'Unknown error occurred';
      let helpText = 'Please try again or check the console for details.';
      
      if (error instanceof Error) {
        errorMessage = error.message;
        
        // Provide context-specific help based on error
        if (errorMessage.includes('No transcript available') || 
            errorMessage.includes('No RAG chain')) {
          helpText = 'Please analyze a video or upload a PDF document first before asking questions.';
        } else if (errorMessage.includes('Cannot connect') || 
                   errorMessage.includes('Failed to fetch') ||
                   (error as any).isNetworkError) {
          helpText = 'Cannot connect to the backend server. Please make sure it\'s running on http://localhost:8000';
          errorMessage = 'Backend connection failed';
        } else if (errorMessage.includes('400')) {
          helpText = 'The request was invalid. This might be due to missing required fields or incorrect data format.';
        } else if (errorMessage.includes('404') || errorMessage.includes('No transcript found')) {
          helpText = 'This analysis session is no longer on the server (it may have expired after a restart). Analyze the video or PDF again, then ask your question.';
        } else if (errorMessage.includes('500')) {
          helpText = 'The server encountered an error. Check the backend logs for more details.';
        } else if (errorMessage.includes('timeout') || errorMessage.includes('timed out')) {
          helpText = 'The request took too long. The document might be too large or the server is overloaded.';
        }
      } else if (typeof error === 'object' && error !== null) {
        // Handle raw error objects (shouldn't happen now, but be safe)
        errorMessage = JSON.stringify(error);
        console.warn('Received non-Error object:', error);
      } else {
        errorMessage = String(error);
      }
      
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: "assistant",
        text: `  **Error:** ${errorMessage}\n\n${helpText}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      
      setMessages(prev => [...prev, errorMsg]);
    }
  };

  const handleCopyMessage = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const currentQuestions = isPdf ? PRESET_PDF_QUESTIONS : PRESET_VIDEO_QUESTIONS;

  return (
    <section id="chat" className="py-12 sm:py-16 px-4 sm:px-6 bg-[#FDFCF0] border-t border-[#1A1A1A]/10">
      <div className="max-w-4xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-[#D9CCF5]/60 text-[#1A1A1A] text-xs font-semibold uppercase tracking-wider mb-2">
            <MessageSquare className="w-3.5 h-3.5" /> Interactive Vector RAG Chat
          </div>
          <h2 className="font-['Baskervville',serif] text-3xl sm:text-4xl text-[#1A1A1A]">
            Ask Anything About <span className="text-[#8A8A8A]">{isPdf ? "The Document" : "The Media"}</span>
          </h2>
        </div>

        {/* Chat Window Container */}
        <div className="rounded-3xl border-2 border-[#1A1A1A] bg-white shadow-xl overflow-hidden flex flex-col h-[520px]">
          {/* Top Chat Bar */}
          <div className="p-4 bg-[#FDFCF0] border-b border-[#1A1A1A]/10 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-[#1A1A1A] text-[#D9CCF5] flex items-center justify-center font-bold">
                <Bot className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-[#1A1A1A]">AI Assistant</h4>
                <p className="text-[10px] text-[#8A8A8A]">Vector RAG Engine • Sub-10ms Semantic Search</p>
              </div>
            </div>
            {currentAnalysis && (
              <span className="text-[11px] font-mono text-[#1A1A1A]/80 bg-[#D9CCF5]/40 px-2.5 py-1 rounded-full border border-[#D9CCF5]">
                Context: {currentAnalysis.title?.length > 25 ? currentAnalysis.title.substring(0, 25) + "..." : currentAnalysis.title || "Document"}
              </span>
            )}
          </div>

          {/* Preset Chips */}
          <div className="p-3 bg-[#FDFCF0]/40 border-b border-[#1A1A1A]/5 flex items-center gap-2 overflow-x-auto">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-[#8A8A8A] shrink-0 pl-1">
              Suggestions:
            </span>
            {currentQuestions.map((pq, idx) => (
              <button
                key={idx}
                onClick={() => handleSendQuestion(pq)}
                disabled={isTyping}
                className="px-3 py-1 rounded-xl border border-[#1A1A1A]/15 bg-white text-xs font-medium text-[#1A1A1A] hover:bg-[#D9CCF5]/40 transition-colors shrink-0"
              >
                {pq}
              </button>
            ))}
          </div>

          {/* Messages Body */}
          <div className="flex-1 p-4 sm:p-6 overflow-y-auto space-y-4 bg-[#FDFCF0]/20">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex gap-3 ${m.sender === "user" ? "justify-end" : "justify-start"}`}
              >
                {m.sender === "assistant" && (
                  <div className="w-7 h-7 rounded-lg bg-[#1A1A1A] text-[#D9CCF5] flex items-center justify-center shrink-0 mt-0.5">
                    <Bot className="w-3.5 h-3.5" />
                  </div>
                )}
                <div
                  className={`max-w-md sm:max-w-xl p-4 rounded-2xl text-xs sm:text-sm leading-relaxed relative group ${
                    m.sender === "user"
                      ? "bg-[#1A1A1A] text-white rounded-br-none shadow-xs [&_strong]:text-[#D9CCF5] [&_em]:text-[#D9CCF5]/90 [&_code]:bg-white/10 [&_code]:px-1 [&_code]:rounded [&_ul]:list-disc [&_ul]:ml-4 [&_ol]:list-decimal [&_ol]:ml-4 [&_li]:my-0.5 [&_h1]:text-base [&_h1]:font-bold [&_h1]:mb-1 [&_h2]:text-sm [&_h2]:font-bold [&_h2]:mb-1 [&_h3]:text-sm [&_h3]:font-semibold [&_h3]:mb-1 [&_p]:my-1"
                      : "bg-white border border-[#1A1A1A]/15 text-[#1A1A1A] rounded-bl-none shadow-xs [&_strong]:text-[#1A1A1A] [&_strong]:font-bold [&_em]:text-[#8A8A8A] [&_code]:bg-[#FDFCF0] [&_code]:px-1 [&_code]:rounded [&_code]:border [&_code]:border-[#1A1A1A]/10 [&_ul]:list-disc [&_ul]:ml-4 [&_ol]:list-decimal [&_ol]:ml-4 [&_li]:my-0.5 [&_h1]:text-base [&_h1]:font-bold [&_h1]:mb-1 [&_h2]:text-sm [&_h2]:font-bold [&_h2]:mb-1 [&_h3]:text-sm [&_h3]:font-semibold [&_h3]:mb-1 [&_p]:my-1"
                  }`}
                >
                  <div className="markdown-content">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.text}</ReactMarkdown>
                  </div>
                  <div className="mt-2 flex items-center justify-between border-t border-current/10 pt-1.5 text-[10px] opacity-70">
                    <span>{m.timestamp}</span>
                    <button
                      onClick={() => handleCopyMessage(m.id, m.text)}
                      className="hover:opacity-100 transition-opacity"
                    >
                      {copiedId === m.id ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                    </button>
                  </div>
                </div>
                {m.sender === "user" && (
                  <div className="w-7 h-7 rounded-lg bg-[#D9CCF5] text-[#1A1A1A] flex items-center justify-center shrink-0 font-bold text-xs mt-0.5">
                    <User className="w-3.5 h-3.5" />
                  </div>
                )}
              </div>
            ))}

            {isTyping && (
              <div className="flex items-center gap-2 text-xs text-[#8A8A8A] font-medium p-2">
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#1A1A1A]" />
                <span>AI is searching vector context...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Bar */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendQuestion();
            }}
            className="p-3 bg-white border-t border-[#1A1A1A]/10 flex items-center gap-2"
          >
            <input
              type="text"
              value={inputQuestion}
              onChange={(e) => setInputQuestion(e.target.value)}
              placeholder={`Ask a question about the ${isPdf ? "PDF document" : "media transcript"}...`}
              className="flex-1 px-4 py-2.5 rounded-xl border border-[#1A1A1A]/15 bg-[#FDFCF0]/50 text-xs sm:text-sm text-[#1A1A1A] placeholder-[#8A8A8A] focus:outline-none focus:ring-2 focus:ring-[#D9CCF5]"
            />
            <button
              type="submit"
              disabled={!inputQuestion.trim() || isTyping}
              className="px-4 py-2.5 rounded-xl bg-[#1A1A1A] text-white font-semibold text-xs hover:bg-black transition-all flex items-center gap-1.5 shadow-xs disabled:opacity-50"
            >
              <span>Send</span>
              <Send className="w-3.5 h-3.5 text-[#D9CCF5]" />
            </button>
          </form>
        </div>
      </div>
    </section>
  );
};
