import React, { useState, useEffect, useRef } from 'react';
import { Youtube, Upload, Sparkles, FileAudio, X, Check, Loader2, Play, FileText, AlertCircle } from 'lucide-react';
import apiClient from '../api/client';
import type { AnalysisData } from '../types/analysis';

interface AudioVideoAnalyzerProps {
  onAnalysisComplete: (result: AnalysisData) => void;
  existingResult: AnalysisData | null;
}

type InputMode = 'url' | 'file';
type Language = 'english' | 'hinglish';

function AudioVideoAnalyzer({ onAnalysisComplete, existingResult }: AudioVideoAnalyzerProps) {
  const [url, setUrl] = useState('');
  const [language, setLanguage] = useState<Language>('english');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisData | null>(existingResult);
  const [inputMode, setInputMode] = useState<InputMode>('url');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (existingResult && existingResult.type !== 'pdf') {
      setResult(existingResult);
    }
  }, [existingResult]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    console.log('=== AudioVideoAnalyzer: handleSubmit CALLED ===');
    
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
      let data: AnalysisData;
      
      if (inputMode === 'url') {
        data = await apiClient.analyzeVideoAsync(url, language);
      } else {
        data = await apiClient.uploadAndAnalyze(selectedFile!, language, (progress) => {
          setUploadProgress(progress);
        });
      }

      const analysis: AnalysisData = {
        ...data,
        type: data.type === 'audio' ? 'audio' : 'video',
        job_id: data.job_id,
      };
      
      setResult(analysis);
      if (onAnalysisComplete) {
        onAnalysisComplete(analysis);
      }
    } catch (err) {
      console.error('Analysis error:', err);
      setError(err instanceof Error ? err.message : 'Analysis failed');
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

  const validateAndSetFile = (file: File) => {
    const validExtensions = [
      '.mp3', '.mp4', '.wav', '.m4a', '.flac', '.ogg', '.aac', 
      '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'
    ];
    const fileExt = '.' + file.name.split('.').pop()?.toLowerCase();
    
    if (!validExtensions.includes(fileExt)) {
      setError(`Unsupported file type: ${fileExt}`);
      return;
    }

    const maxSize = 500 * 1024 * 1024;
    if (file.size > maxSize) {
      setError(`File too large: ${(file.size / 1024 / 1024).toFixed(1)}MB. Maximum: 500MB`);
      return;
    }

    setSelectedFile(file);
    setError(null);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === "dragenter" || e.type === "dragover");
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files?.[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="w-full">
      {result ? (
        <div className="space-y-6">
          {/* Results Header */}
          <div className="flex items-center justify-between pb-4 border-b border-[#1A1A1A]/10">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#D9CCF5]/40 text-[#1A1A1A] text-xs font-semibold uppercase tracking-wider mb-2">
                <Sparkles className="w-3.5 h-3.5" />
                Analysis Complete
              </div>
              <h2 className="font-['Baskervville',serif] text-2xl text-[#1A1A1A]">
                {result.title}
              </h2>
            </div>
            <button
              onClick={handleNewAnalysis}
              className="px-4 py-2 rounded-xl bg-white border-2 border-[#1A1A1A]/20 text-[#1A1A1A] text-sm font-semibold hover:border-[#1A1A1A] transition-all flex items-center gap-2"
            >
              <Play className="w-4 h-4" />
              New Analysis
            </button>
          </div>

          {/* Results Grid */}
          <div className="grid gap-4">
            {result.summary && (
              <div className="bg-[#FDFCF0] rounded-2xl border border-[#1A1A1A]/10 p-5">
                <h3 className="text-sm font-bold uppercase tracking-wider text-[#1A1A1A] mb-3 flex items-center gap-2">
                  <FileText className="w-4 h-4" />
                  Summary
                </h3>
                <p className="text-sm text-[#1A1A1A] leading-relaxed">{result.summary}</p>
              </div>
            )}

            {result.action_items && (
              <div className="bg-[#FDFCF0] rounded-2xl border border-[#1A1A1A]/10 p-5">
                <h3 className="text-sm font-bold uppercase tracking-wider text-[#1A1A1A] mb-3 flex items-center gap-2">
                  <Check className="w-4 h-4" />
                  Action Items
                </h3>
                <pre className="text-sm text-[#1A1A1A] whitespace-pre-wrap font-sans">{result.action_items}</pre>
              </div>
            )}

            {result.key_decisions && (
              <div className="bg-[#FDFCF0] rounded-2xl border border-[#1A1A1A]/10 p-5">
                <h3 className="text-sm font-bold uppercase tracking-wider text-[#1A1A1A] mb-3 flex items-center gap-2">
                  <Sparkles className="w-4 h-4" />
                  Key Decisions
                </h3>
                <pre className="text-sm text-[#1A1A1A] whitespace-pre-wrap font-sans">{result.key_decisions}</pre>
              </div>
            )}

            {result.open_questions && (
              <div className="bg-[#FDFCF0] rounded-2xl border border-[#1A1A1A]/10 p-5">
                <h3 className="text-sm font-bold uppercase tracking-wider text-[#1A1A1A] mb-3 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  Open Questions
                </h3>
                <pre className="text-sm text-[#1A1A1A] whitespace-pre-wrap font-sans">{result.open_questions}</pre>
              </div>
            )}

            {result.transcript && (
              <details className="bg-[#FDFCF0] rounded-2xl border border-[#1A1A1A]/10 p-5 group">
                <summary className="text-sm font-bold uppercase tracking-wider text-[#1A1A1A] cursor-pointer flex items-center gap-2">
                  <FileText className="w-4 h-4" />
                  Full Transcript (Click to expand)
                </summary>
                <pre className="mt-4 text-xs text-[#8A8A8A] whitespace-pre-wrap font-mono max-h-96 overflow-y-auto">
                  {result.transcript}
                </pre>
              </details>
            )}
          </div>

          {/* Next Step */}
          <div className="bg-[#D9CCF5]/20 rounded-2xl border-2 border-[#D9CCF5]/40 p-4 text-center">
            <p className="text-sm text-[#1A1A1A]">
              💬 Ready to explore more? <strong>Scroll down</strong> to the chat section to ask questions about this content!
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Input Mode Selector */}
          <div className="flex justify-center gap-3 mb-6">
            <button
              type="button"
              onClick={() => {
                setInputMode('url');
                setSelectedFile(null);
                setError(null);
              }}
              disabled={loading}
              className={`px-6 py-3 rounded-xl font-semibold text-sm transition-all flex items-center gap-2 ${
                inputMode === 'url'
                  ? 'bg-[#1A1A1A] text-white'
                  : 'bg-[#FDFCF0] border-2 border-[#1A1A1A]/15 text-[#1A1A1A] hover:border-[#1A1A1A]/40'
              }`}
            >
              <Youtube className="w-4 h-4" />
              YouTube URL
            </button>
            <button
              type="button"
              onClick={() => {
                setInputMode('file');
                setUrl('');
                setError(null);
              }}
              disabled={loading}
              className={`px-6 py-3 rounded-xl font-semibold text-sm transition-all flex items-center gap-2 ${
                inputMode === 'file'
                  ? 'bg-[#1A1A1A] text-white'
                  : 'bg-[#FDFCF0] border-2 border-[#1A1A1A]/15 text-[#1A1A1A] hover:border-[#1A1A1A]/40'
              }`}
            >
              <Upload className="w-4 h-4" />
              Upload File
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {inputMode === 'url' ? (
              <div className="space-y-2">
                <label htmlFor="url" className="block text-sm font-semibold text-[#1A1A1A]">
                  YouTube URL
                </label>
                <input
                  id="url"
                  type="text"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://www.youtube.com/watch?v=..."
                  disabled={loading}
                  className="w-full px-4 py-3 rounded-xl border-2 border-[#1A1A1A]/15 bg-[#FDFCF0] text-[#1A1A1A] placeholder-[#8A8A8A] focus:outline-none focus:ring-2 focus:ring-[#D9CCF5] focus:border-transparent transition-all"
                />
              </div>
            ) : (
              <div className="space-y-2">
                <label className="block text-sm font-semibold text-[#1A1A1A]">
                  Upload Audio or Video File
                </label>
                
                <div
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                  className={`relative rounded-2xl border-2 border-dashed transition-all ${
                    dragActive
                      ? 'border-[#D9CCF5] bg-[#D9CCF5]/10'
                      : selectedFile
                      ? 'border-[#1A1A1A]/20 bg-[#FDFCF0]'
                      : 'border-[#1A1A1A]/15 bg-[#FDFCF0] hover:border-[#1A1A1A]/30'
                  }`}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".mp3,.mp4,.wav,.m4a,.flac,.ogg,.aac,.avi,.mov,.mkv,.webm,.flv,.wmv"
                    onChange={(e) => e.target.files?.[0] && validateAndSetFile(e.target.files[0])}
                    className="hidden"
                    disabled={loading}
                  />
                  
                  {selectedFile ? (
                    <div className="p-6 flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-[#D9CCF5]/30 flex items-center justify-center shrink-0">
                        <FileAudio className="w-6 h-6 text-[#1A1A1A]" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-sm text-[#1A1A1A] truncate">
                          {selectedFile.name}
                        </div>
                        <div className="text-xs text-[#8A8A8A]">
                          {formatFileSize(selectedFile.size)}
                        </div>
                      </div>
                      {!loading && (
                        <button
                          type="button"
                          onClick={() => setSelectedFile(null)}
                          className="w-8 h-8 rounded-lg bg-[#1A1A1A]/10 hover:bg-[#1A1A1A]/20 flex items-center justify-center transition-colors"
                        >
                          <X className="w-4 h-4 text-[#1A1A1A]" />
                        </button>
                      )}
                    </div>
                  ) : (
                    <div className="p-8 text-center space-y-4">
                      <div className="w-16 h-16 mx-auto rounded-full bg-[#D9CCF5]/20 flex items-center justify-center">
                        <Upload className="w-8 h-8 text-[#1A1A1A]" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-[#1A1A1A] mb-1">
                          Drag and drop your file here
                        </p>
                        <p className="text-xs text-[#8A8A8A]">or</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={loading}
                        className="px-6 py-2 rounded-xl bg-[#1A1A1A] text-white text-sm font-semibold hover:bg-black transition-all"
                      >
                        Browse Files
                      </button>
                      <p className="text-xs text-[#8A8A8A]">
                        <strong>Audio:</strong> MP3, WAV, M4A, FLAC, OGG, AAC
                        <br />
                        <strong>Video:</strong> MP4, AVI, MOV, MKV, WebM, FLV, WMV
                        <br />
                        Max size: 500MB
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Language Selector */}
            <div className="space-y-2">
              <label htmlFor="language" className="block text-sm font-semibold text-[#1A1A1A]">
                Language
              </label>
              <select
                id="language"
                value={language}
                onChange={(e) => setLanguage(e.target.value as Language)}
                disabled={loading}
                className="w-full px-4 py-3 rounded-xl border-2 border-[#1A1A1A]/15 bg-[#FDFCF0] text-[#1A1A1A] focus:outline-none focus:ring-2 focus:ring-[#D9CCF5] focus:border-transparent transition-all"
              >
                <option value="english">English</option>
                <option value="hinglish">Hinglish</option>
              </select>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || (inputMode === 'url' && !url.trim()) || (inputMode === 'file' && !selectedFile)}
              className="w-full px-6 py-4 rounded-xl bg-[#1A1A1A] text-white font-semibold hover:bg-black transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  {uploadProgress > 0 && uploadProgress < 100
                    ? `Uploading... ${uploadProgress}%`
                    : 'Processing...'}
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  {inputMode === 'url' ? 'Analyze Video' : 'Analyze Media'}
                </>
              )}
            </button>
          </form>

          {/* Loading State */}
          {loading && (
            <div className="bg-[#D9CCF5]/20 rounded-2xl border border-[#D9CCF5]/40 p-6 text-center space-y-3">
              <div className="flex justify-center">
                <div className="w-12 h-12 rounded-full bg-[#1A1A1A] flex items-center justify-center">
                  <Loader2 className="w-6 h-6 text-[#D9CCF5] animate-spin" />
                </div>
              </div>
              <div>
                <p className="text-sm font-semibold text-[#1A1A1A]">
                  {uploadProgress > 0 && uploadProgress < 100
                    ? `Uploading file... ${uploadProgress}%`
                    : `Processing ${inputMode === 'url' ? 'video' : 'media'}...`}
                </p>
                <p className="text-xs text-[#8A8A8A] mt-1">
                  This may take 2-10 minutes. We're {inputMode === 'url' && 'downloading, '}
                  transcribing audio, and creating a searchable index.
                </p>
              </div>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="bg-red-50 rounded-2xl border-2 border-red-200 p-6">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-red-100 flex items-center justify-center shrink-0">
                  <AlertCircle className="w-5 h-5 text-red-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-sm font-bold text-red-900 mb-1">Error</h3>
                  <p className="text-sm text-red-700">{error}</p>
                  <p className="text-xs text-red-600 mt-2">
                    Make sure the backend is running and the {inputMode === 'url' ? 'URL is valid' : 'file format is supported'}.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default AudioVideoAnalyzer;
