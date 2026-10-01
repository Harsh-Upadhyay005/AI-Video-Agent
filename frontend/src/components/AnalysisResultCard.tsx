import { useState } from 'react';
import type React from 'react';
import { Sparkles, Play, FileText, ChevronDown, ChevronUp, MessageSquare } from 'lucide-react';
import type { AnalysisData } from '../types/analysis';

interface AnalysisResultCardProps {
  analysis: AnalysisData;
  onReset: () => void;
}

export const AnalysisResultCard: React.FC<AnalysisResultCardProps> = ({ analysis, onReset }) => {
  const [expanded, setExpanded] = useState(false);
  const isPdf = analysis.type === 'pdf';

  return (
    <div className="space-y-6">
      {/* Top Header Row */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-4 border-b border-[#1A1A1A]/10">
        <div className="space-y-2 min-w-0">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#E5D7FA] text-[#1A1A1A] text-[10px] sm:text-xs font-semibold uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5 text-[#1A1A1A]" />
            <span>ANALYSIS COMPLETE</span>
          </div>
          <h2 className="font-['Baskervville',serif] text-2xl sm:text-3xl md:text-4xl text-[#1A1A1A] tracking-tight break-words">
            {analysis.title || 'Untitled Document'}
          </h2>
        </div>

        <button
          onClick={onReset}
          className="self-start sm:self-auto px-4 py-2 sm:py-2.5 rounded-xl border border-[#1A1A1A]/20 bg-white hover:bg-[#FDFCF0] text-xs sm:text-sm font-semibold text-[#1A1A1A] transition-all flex items-center gap-2 shadow-xs hover:border-[#1A1A1A]/40 shrink-0"
        >
          {isPdf ? (
            <>
              <FileText className="w-4 h-4 text-[#1A1A1A]" />
              <span>New Document</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 text-[#1A1A1A] fill-current" />
              <span>New Analysis</span>
            </>
          )}
        </button>
      </div>

      {/* Expandable Full Transcript / Document Section */}
      <div className="space-y-2">
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="w-full p-3.5 sm:p-4 rounded-xl bg-[#FDFCF0] border border-[#1A1A1A]/10 hover:border-[#1A1A1A]/30 transition-all flex items-center justify-between text-left group"
        >
          <div className="flex items-center gap-2 sm:gap-2.5 text-xs sm:text-sm font-bold text-[#1A1A1A]">
            <FileText className="w-4 h-4 text-[#8A8A8A] group-hover:text-[#1A1A1A] transition-colors" />
            <span className="tracking-wide">
              {isPdf ? 'FULL DOCUMENT TEXT (CLICK TO EXPAND)' : 'FULL TRANSCRIPT (CLICK TO EXPAND)'}
            </span>
          </div>
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-[#8A8A8A] group-hover:text-[#1A1A1A]" />
          ) : (
            <ChevronDown className="w-4 h-4 text-[#8A8A8A] group-hover:text-[#1A1A1A]" />
          )}
        </button>

        {expanded && (
          <div className="p-4 sm:p-5 rounded-xl bg-[#FDFCF0]/60 border border-[#1A1A1A]/10 max-h-96 overflow-y-auto text-xs sm:text-sm text-[#1A1A1A]/90 whitespace-pre-wrap font-sans leading-relaxed animate-fade-in">
            {analysis.transcript || 'No transcript text available.'}
          </div>
        )}
      </div>

      {/* Explore More Callout */}
      <div className="p-3.5 sm:p-4 rounded-xl bg-[#F5EFFF] border border-[#D9CCF5] flex items-center justify-center gap-2 text-center">
        <MessageSquare className="w-4 h-4 text-[#6D5A9E] shrink-0" />
        <p className="text-xs sm:text-sm text-[#1A1A1A]">
          Ready to explore more?{' '}
          <span className="font-bold">Scroll down to the chat section</span> to ask questions about this content!
        </p>
      </div>
    </div>
  );
};
