import React from "react";
import { Mic, Zap, Search, Globe, ShieldCheck, FileCheck, Sparkles } from "lucide-react";

const FEATURES = [
  {
    icon: Mic,
    title: "Dual-Pass Voice Cleanup",
    description: "Strips out vocal stutters, filler words ('umm', 'like', 'basically'), and trailing thoughts to output crisp executive prose."
  },
  {
    icon: Zap,
    title: "Instant Audio Ingestion",
    description: "Extracts high-fidelity audio streams from YouTube URLs or local media files, processed at 16kHz mono resolution."
  },
  {
    icon: Search,
    title: "Vector Search Q&A",
    description: "Indexes video transcripts into localized embeddings for sub-10ms answer retrieval across multi-hour recordings."
  },
  {
    icon: Globe,
    title: "Multilingual Support",
    description: "Engineered specifically for seamless English and Hinglish (Hindi + English) code-switching speech recognition."
  },
  {
    icon: FileCheck,
    title: "Automated Action Extraction",
    description: "Automatically segregates key decisions, action items, task owners, and open questions into structured bullet lists."
  },
  {
    icon: ShieldCheck,
    title: "Privacy First Architecture",
    description: "Runs localized Whisper processing & vector stores locally or on private cloud endpoints with end-to-end security."
  }
];

export const FeatureShowcase: React.FC = () => {
  return (
    <section id="features" className="py-20 px-6 bg-[#FDFCF0] border-t border-[#1A1A1A]/10">
      <div className="max-w-6xl mx-auto">
        {/* Section Header */}
        <div className="text-center max-w-2xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-[#1A1A1A] text-[#FDFCF0] text-xs font-semibold uppercase tracking-wider mb-3">
            <Sparkles className="w-3.5 h-3.5 text-[#D9CCF5]" /> Engineered for Excellence
          </div>
          <h2 className="font-['Baskervville',serif] text-4xl sm:text-5xl text-[#1A1A1A] tracking-tight">
            Why Professionals Choose <span className="text-[#8A8A8A]">AI Video Agent</span>
          </h2>
          <p className="mt-4 text-[#1A1A1A]/80 text-base">
            From raw voice dictation to multi-hour conference recordings, get complete clarity without taking manual notes.
          </p>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {FEATURES.map((f, idx) => {
            const Icon = f.icon;
            return (
              <div
                key={idx}
                className="p-8 rounded-3xl border border-[#1A1A1A]/15 bg-white shadow-xs hover:shadow-lg hover:-translate-y-1 transition-all group"
              >
                <div className="w-12 h-12 rounded-2xl bg-[#D9CCF5] text-[#1A1A1A] flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <Icon className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-[#1A1A1A] mb-2">{f.title}</h3>
                <p className="text-sm text-[#8A8A8A] leading-relaxed">{f.description}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
