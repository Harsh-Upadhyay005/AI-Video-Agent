import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, MicOff, Sparkles, Check, RefreshCw, ChevronDown, ChevronUp } from "lucide-react";

const SAMPLE_RAW_TEXTS = [
  {
    title: "Messy Dictation Memo",
    raw: "Umm, hope your week has started well… I was talking to Cheyene earlier but reception was really bad and I think their going to handle the first part of the project, but I'm not totally sure. Also, I told the team the new timeline should be ready by Friday, although it's probably going to slip. There's been a lot of back and forth and honestly the whole thing's been kind of chaotic, like nobody really knows what's going on so can you check in with them and see if the notes from yesterday's meeting were sent out, or if they're still waiting. I think Cheyene mentioned it but didn't confirm, and now I'm a little lost.",
    polished: {
      summary: "Cheyene is likely managing phase 1, but confirmation is needed alongside yesterday's meeting notes.",
      actionItems: [
        "Check in with team regarding yesterday's meeting notes dispatch.",
        "Confirm with Cheyene if phase 1 ownership is officially assigned.",
        "Update project schedule before potential Friday deadline slip."
      ],
      keyDecision: "Phase 1 work handed off to Cheyene; timeline review scheduled for Friday."
    }
  },
  {
    title: "Product Strategy Brainstorm",
    raw: "So yeah like basically we were thinking about adding like video transcription features to the landing page... like when users paste a link it should automatically download the audio and convert it to clean text with Whisper, and then use LLMs to extract action items, so like users don't have to manually take notes during 2 hour long Zoom meetings, you know what I mean?",
    polished: {
      summary: "Proposal to integrate automated Whisper audio transcription and LLM-powered action item extraction for long meeting videos.",
      actionItems: [
        "Implement automatic YouTube/Audio downloader pipeline.",
        "Integrate OpenAI Whisper engine for accurate speech-to-text.",
        "Generate key meeting takeaways and structured action lists via LLM."
      ],
      keyDecision: "Prioritize automated video summary feature to eliminate manual meeting note-taking."
    }
  }
];

export const DictationPlayground: React.FC = () => {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [customText, setCustomText] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [copied, setCopied] = useState(false);
  const [customResult, setCustomResult] = useState<any>(null);
  const [showPlayground, setShowPlayground] = useState(false);

  // WPM Counter animation
  const [keyboardWpm, setKeyboardWpm] = useState(0);
  const [videoQueryWpm, setvideoQueryWpm] = useState(0);

  useEffect(() => {
    const duration = 1500; // 1.5s
    const steps = 60;
    const stepTime = duration / steps;

    let step = 0;
    const timer = setInterval(() => {
      step++;
      setKeyboardWpm(Math.min(Math.floor((45 / steps) * step), 45));
      setvideoQueryWpm(Math.min(Math.floor((220 / steps) * step), 220));

      if (step >= steps) {
        clearInterval(timer);
      }
    }, stepTime);

    return () => clearInterval(timer);
  }, []);

  const handleRecordToggle = () => {
    if (isRecording) {
      setIsRecording(false);
    } else {
      setIsRecording(true);
      setTimeout(() => {
        setIsRecording(false);
        setCustomText("Umm so basically we need to check if the video transcription pipeline works properly with Hinglish audio clips and output bullet points.");
      }, 3000);
    }
  };

  const handleCleanUpCustom = () => {
    if (!customText.trim()) return;
    setIsProcessing(true);
    setTimeout(() => {
      setIsProcessing(false);
      setCustomResult({
        summary: "Evaluate video transcription pipeline compatibility with Hinglish audio sources and verify structured bullet point output.",
        actionItems: [
          "Test Hinglish speech recognition accuracy.",
          "Verify formatting of extracted takeaways and action items."
        ],
        keyDecision: "Ensure dual-language (English & Hinglish) support in production pipeline."
      });
    }, 1200);
  };

  const sample = SAMPLE_RAW_TEXTS[selectedIndex];
  const currentResult = customResult || sample.polished;

  const handleCopy = () => {
    const textToCopy = `Summary:\n${currentResult.summary}\n\nAction Items:\n${currentResult.actionItems.map((a: string) => `• ${a}`).join('\n')}`;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section id="playground" className="py-16 sm:py-24 px-4 sm:px-6 md:px-8 bg-[#033E35] text-white overflow-hidden relative">
      {/* Decorative Wave BG */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#033E35] via-[#022f28] to-[#033E35] pointer-events-none z-0" />
      
      <div className="max-w-5xl mx-auto relative z-10">
        
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-10 sm:mb-16">
          <h2 className="font-['Baskervville',serif] text-3xl sm:text-5xl md:text-6xl text-white tracking-tight leading-tight">
            120x faster <span className="italic font-light opacity-95 text-[#D9CCF5]">than watching</span>
          </h2>
          <p className="mt-4 sm:mt-6 text-emerald-100/80 text-sm sm:text-base md:text-lg leading-relaxed font-sans max-w-2xl mx-auto font-light">
            Why sit through a two-hour recording? AI Video Agent ingests video streams in seconds, indexing the transcript for immediate, search-optimized answers.
          </p>
        </div>

        {/* Speed Comparison Layout - Redesigned */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 sm:gap-6 items-stretch mb-8 sm:mb-12">
          
          {/* Manual Review Card - Improved Design */}
          <div className="lg:col-span-5 rounded-2xl sm:rounded-3xl border-2 border-emerald-500/30 bg-gradient-to-br from-emerald-950/40 via-emerald-900/20 to-emerald-950/40 p-6 sm:p-8 flex flex-col justify-between min-h-[200px] sm:min-h-[240px] backdrop-blur-sm relative overflow-hidden group hover:border-emerald-500/50 transition-all duration-300">
            {/* Subtle gradient overlay */}
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            
            <div className="relative z-10">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-400/90 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  Manual Review
                </span>
                <span className="text-[10px] text-emerald-300/60 font-mono">Traditional Method</span>
              </div>
              
              <div className="font-['Baskervville',serif] text-5xl sm:text-6xl md:text-7xl font-bold mt-2 text-white">
                {keyboardWpm ? Math.round(keyboardWpm * 1.33) : 0}
                <span className="text-xl sm:text-2xl font-sans text-emerald-300 ml-2 font-normal">mins</span>
              </div>
              
              <div className="mt-4 flex items-center gap-2 text-emerald-200/50 text-xs">
                <div className="w-8 h-0.5 bg-emerald-500/30" />
                <span>Per 1-hour video</span>
              </div>
            </div>
            
            <div className="relative z-10 mt-6 p-4 rounded-xl bg-black/20 border border-emerald-500/10 backdrop-blur-sm">
              <p className="text-xs text-emerald-200/70 leading-relaxed font-mono">
                "Pause video, type bullet points, rewind to hear names, type action items..."
              </p>
            </div>
          </div>

          {/* AI Video Agent Card - Enhanced Design */}
          <div className="lg:col-span-7 rounded-2xl sm:rounded-3xl overflow-hidden relative shadow-2xl min-h-[240px] sm:min-h-[280px] flex flex-col justify-between border-2 border-white/20 backdrop-blur-xl group hover:border-white/40 transition-all duration-300">
            {/* Animated gradient background */}
            <div className="absolute inset-0 bg-gradient-to-br from-purple-900/60 via-indigo-900/50 to-teal-900/60" />
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(167,139,250,0.2),transparent_50%)]" />
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,rgba(52,211,153,0.15),transparent_50%)]" />
            
            {/* Animated grid pattern */}
            <div className="absolute inset-0 opacity-10">
              <div className="absolute inset-0" style={{
                backgroundImage: 'linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)',
                backgroundSize: '50px 50px'
              }} />
            </div>
            
            <div className="relative z-10 p-6 sm:p-8">
              <div className="flex flex-col sm:flex-row justify-between items-start gap-3 mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Sparkles className="w-4 h-4 text-purple-300 animate-pulse" />
                    <span className="text-xs font-bold uppercase tracking-wider text-purple-200">
                      AI Video Agent
                    </span>
                  </div>
                  
                  <div className="font-['Baskervville',serif] text-5xl sm:text-6xl md:text-7xl font-bold text-white">
                    {videoQueryWpm ? Math.round(videoQueryWpm * 0.136) : 0}
                    <span className="text-xl sm:text-2xl font-sans text-purple-200 ml-2 font-normal">secs</span>
                  </div>
                  
                  <div className="mt-3 flex items-center gap-2">
                    <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/10 backdrop-blur-md border border-white/20">
                      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                      <span className="text-[10px] text-white/90 font-semibold uppercase tracking-wider">
                        Vector Indexing Active
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="flex flex-col gap-2 items-end">
                  <div className="px-3 py-1.5 rounded-lg bg-emerald-500/20 border border-emerald-400/30 backdrop-blur-sm">
                    <span className="text-xs font-bold text-emerald-300">120x Faster</span>
                  </div>
                  <div className="text-[10px] text-white/60 font-mono">Real-time processing</div>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-black/30 border border-white/10 backdrop-blur-md">
                <p className="text-xs text-white/80 leading-relaxed italic font-mono">
                  "Transcribing audio stream at 16kHz mono, computing text chunk embeddings, saving vector database..."
                </p>
              </div>
            </div>

            {/* Enhanced Soundwave Visualization */}
            <div className="relative z-10 flex justify-center pb-6 sm:pb-8">
              <div className="flex h-12 sm:h-14 w-40 sm:w-48 items-center justify-center gap-1.5 rounded-2xl border-2 border-white/30 bg-black/50 px-5 shadow-2xl backdrop-blur-xl">
                {[...Array(10)].map((_, i) => (
                  <span
                    key={i}
                    className="w-1 bg-gradient-to-t from-purple-400 to-white rounded-full soundwave-bar"
                    style={{
                      animationDelay: `${i * 0.1}s`,
                      height: `${20 + Math.random() * 40}%`
                    }}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Toggle to Interactive Dictation Playground */}
        <div className="flex justify-center mb-6 sm:mb-8">
          <button
            onClick={() => setShowPlayground(!showPlayground)}
            className="flex items-center gap-2 bg-white/10 hover:bg-white/15 px-5 sm:px-6 py-2.5 sm:py-3 rounded-full text-xs font-bold uppercase tracking-wider transition-all border border-white/10"
          >
            <span>{showPlayground ? "Hide Dictation Lab" : "Open Interactive Dictation Lab"}</span>
            {showPlayground ? <ChevronUp className="w-4 h-4 text-[#D9CCF5]" /> : <ChevronDown className="w-4 h-4 text-[#D9CCF5]" />}
          </button>
        </div>

        {/* Collapsible Interactive Lab */}
        <AnimatePresence>
          {showPlayground && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.4 }}
              className="overflow-hidden space-y-6 pt-2"
            >
              {/* Preset Selector Tabs */}
              <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-3">
                {SAMPLE_RAW_TEXTS.map((s, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setSelectedIndex(idx);
                      setCustomResult(null);
                    }}
                    className={`px-3.5 sm:px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                      selectedIndex === idx && !customResult
                        ? "bg-[#D9CCF5] text-[#0A0A0A] shadow-sm"
                        : "bg-white/5 border border-white/10 text-white hover:bg-white/10"
                    }`}
                  >
                    Preset {idx + 1}: {s.title}
                  </button>
                ))}
              </div>

              {/* Two-Column Comparison Card */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 sm:gap-6 items-stretch">
                {/* Left Column: Raw Input */}
                <div className="flex flex-col justify-between p-5 sm:p-8 rounded-3xl border border-white/15 bg-white/5 shadow-sm backdrop-blur-md">
                  <div>
                    <div className="flex items-center justify-between pb-4 border-b border-white/10 gap-2">
                      <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">
                        Raw Transcript
                      </span>
                      <span className="text-[10px] text-amber-300 bg-amber-950/40 px-2 py-0.5 rounded border border-amber-900 shrink-0">
                        Filler Phrases Included
                      </span>
                    </div>

                    <div className="mt-4">
                      <textarea
                        value={customText || sample.raw}
                        onChange={(e) => {
                          setCustomText(e.target.value);
                          setCustomResult(null);
                        }}
                        rows={6}
                        className="w-full bg-black/30 p-3.5 sm:p-4 rounded-2xl border border-white/10 text-xs leading-relaxed text-zinc-200 focus:outline-none focus:ring-1 focus:ring-[#D9CCF5] resize-none font-mono"
                        placeholder="Type raw dictation or speak..."
                      />
                    </div>
                  </div>

                  {/* Recording & Controls */}
                  <div className="mt-6 flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-white/10">
                    <button
                      onClick={handleRecordToggle}
                      className={`flex items-center gap-2 px-3.5 sm:px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                        isRecording
                          ? "bg-red-600 text-white animate-pulse"
                          : "bg-white/10 hover:bg-white/15 text-white border border-white/10"
                      }`}
                    >
                      {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4 text-red-400" />}
                      <span>{isRecording ? "Recording..." : "Simulate Mic"}</span>
                    </button>

                    <button
                      onClick={handleCleanUpCustom}
                      disabled={isProcessing}
                      className="flex items-center gap-2 px-4 sm:px-5 py-2 rounded-xl bg-white text-black text-xs font-bold hover:bg-emerald-100 transition-all shadow-xs disabled:opacity-50"
                    >
                      {isProcessing ? (
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
                      )}
                      <span>Cleanup Speech</span>
                    </button>
                  </div>
                </div>

                {/* Right Column: AI Output */}
                <div className="flex flex-col justify-between p-5 sm:p-8 rounded-3xl border border-[#D9CCF5]/30 bg-[#FDFCF0] text-[#0A0A0A] shadow-lg relative overflow-hidden">
                  <div>
                    <div className="flex items-center justify-between pb-4 border-b border-black/10">
                      <span className="text-xs font-bold uppercase tracking-wider text-[#1A1A1A] flex items-center gap-1">
                        <Sparkles className="w-4 h-4 text-purple-600" /> Clean Output
                      </span>
                      <button
                        onClick={handleCopy}
                        className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-white border border-black/15 text-xs font-medium text-[#1A1A1A] hover:bg-[#F4F3E8] transition-colors"
                      >
                        {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <span>Copy</span>}
                      </button>
                    </div>

                    {/* Summary Box */}
                    <div className="mt-4 p-3.5 sm:p-4 rounded-xl bg-white border border-black/5">
                      <h4 className="text-[10px] font-bold uppercase tracking-wider text-[#8A8A8A] mb-1">Executive Summary</h4>
                      <p className="text-xs font-medium text-[#1A1A1A] leading-relaxed">
                        {currentResult.summary}
                      </p>
                    </div>

                    {/* Action Items */}
                    <div className="mt-3 p-3.5 sm:p-4 rounded-xl bg-white border border-black/5">
                      <h4 className="text-[10px] font-bold uppercase tracking-wider text-[#8A8A8A] mb-1.5">Action Items</h4>
                      <ul className="space-y-1.5">
                        {currentResult.actionItems.map((item: string, i: number) => (
                          <li key={i} className="flex items-start gap-2 text-xs text-[#1A1A1A]">
                            <span className="w-4.5 h-4.5 rounded-full bg-[#E5D7FA] text-[#1A1A1A] flex items-center justify-center font-bold text-[9px] shrink-0">
                              {i + 1}
                            </span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  <div className="mt-6 pt-4 border-t border-black/10 flex items-center justify-between text-[10px] text-[#8A8A8A]">
                    <span>Latency: ~1.2s</span>
                    <span className="font-semibold text-emerald-600">Accuracy Optimized</span>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

      </div>
    </section>
  );
};
