import React, { useState, useEffect } from 'react';
import './index.css';
import { Header } from './components/Header';
import { WisprHero } from './components/WisprHero';
import { DictationPlayground } from './components/DictationPlayground';
import { FeatureShowcase } from './components/FeatureShowcase';
import { InteractiveChat } from './components/InteractiveChat';
import { Footer } from './components/Footer';
import PDFAnalyzer from './components/PDFAnalyzer';
import AudioVideoAnalyzer from './components/AudioVideoAnalyzer';
import ErrorBoundary from './components/ErrorBoundary';
import type { AnalysisData } from './types/analysis';

type ViewType = 'home' | 'studio';
type AnalyzerType = 'audio-video' | 'pdf';

function App() {
  const [activeView, setActiveView] = useState<ViewType>('home');
  const [studioUrl, setStudioUrl] = useState<string>('');
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisData | null>(null);
  const [analyzerType, setAnalyzerType] = useState<AnalyzerType>('audio-video');

  // Scroll to top on mount/refresh
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  // Load last analysis result from localStorage if available
  useEffect(() => {
    const saved = localStorage.getItem('lastStudioAnalysis');
    if (saved) {
      try {
        const parsed = JSON.parse(saved) as AnalysisData;
        setCurrentAnalysis(parsed);
      } catch (e) {
        console.error('Failed to parse cached analysis:', e);
        // Clear invalid data
        localStorage.removeItem('lastStudioAnalysis');
      }
    }
  }, []);

  const handleStartAnalysis = (url: string) => {
    setStudioUrl(url);
    setActiveView('studio');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleExplorePresets = () => {
    setActiveView('studio');
    setTimeout(() => {
      const el = document.getElementById('studio');
      el?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  const handleAnalysisReady = (result: AnalysisData) => {
    console.log('=== App: Analysis ready callback ===');
    console.log('Result:', result);
    setCurrentAnalysis(result);
    
    try {
      localStorage.setItem('lastStudioAnalysis', JSON.stringify(result));
    } catch (e) {
      console.error('Failed to cache analysis to localStorage:', e);
    }
  };

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-[#FDFCF0] text-[#1A1A1A] font-sans overflow-x-hidden">
        {/* Floating Navbar */}
        <Header
          activeView={activeView}
          onNavigateToHome={() => setActiveView('home')}
          onNavigateToStudio={() => {
            setActiveView('studio');
            window.scrollTo({ top: 0, behavior: 'smooth' });
          }}
        />

        {/* Main Content Pages */}
        {activeView === 'home' ? (
          <div className="animate-fade-in">
            {/* Draggable Testimonial Hero grid with search card */}
            <WisprHero
              onStartAnalysis={handleStartAnalysis}
              onExplorePresets={handleExplorePresets}
              onNavigateToStudio={() => setActiveView('studio')}
            />

            {/* Typing WPM Comparison & speech cleanup lab */}
            <DictationPlayground />

            {/* Clean product feature grid */}
            <FeatureShowcase />

            {/* Start Flowing Callout & footer links */}
            <Footer onNavigateToStudio={() => {
              setActiveView('studio');
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }} />
          </div>
        ) : (
          <div className="pt-20 bg-[#FDFCF0] min-h-screen flex flex-col animate-fade-in">
            <div className="flex-1 pb-16">
              {/* Analyzer Type Selector */}
              <section className="py-8 px-4 sm:px-6">
                <div className="max-w-6xl mx-auto">
                  <div className="flex justify-center gap-4 mb-8">
                    <button
                      onClick={() => {
                        console.log('Switching to audio-video analyzer');
                        setAnalyzerType('audio-video');
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                      }}
                      className={`px-6 py-3 rounded-xl font-semibold text-sm transition-all ${
                        analyzerType === 'audio-video'
                          ? 'bg-[#1A1A1A] text-white shadow-lg'
                          : 'bg-white border-2 border-[#1A1A1A]/20 text-[#1A1A1A] hover:border-[#1A1A1A]'
                      }`}
                    >
                      🎬 Audio / Video / YouTube
                    </button>
                    <button
                      onClick={() => {
                        console.log('Switching to PDF analyzer');
                        setAnalyzerType('pdf');
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                      }}
                      className={`px-6 py-3 rounded-xl font-semibold text-sm transition-all ${
                        analyzerType === 'pdf'
                          ? 'bg-[#1A1A1A] text-white shadow-lg'
                          : 'bg-white border-2 border-[#1A1A1A]/20 text-[#1A1A1A] hover:border-[#1A1A1A]'
                      }`}
                    >
                      📄 PDF Documents
                    </button>
                  </div>

                  {/* Conditional Analyzer Rendering */}
                  <ErrorBoundary>
                    <div className="bg-white rounded-3xl border-2 border-[#1A1A1A] shadow-xl p-6">
                      {analyzerType === 'audio-video' ? (
                        <AudioVideoAnalyzer
                          onAnalysisComplete={handleAnalysisReady}
                          existingResult={currentAnalysis}
                        />
                      ) : (
                        <PDFAnalyzer
                          onAnalysisComplete={handleAnalysisReady}
                          existingResult={currentAnalysis}
                        />
                      )}
                    </div>
                  </ErrorBoundary>
                </div>
              </section>

              {/* Vector RAG Chat Assistant */}
              {currentAnalysis && (
                <ErrorBoundary>
                  <InteractiveChat currentAnalysis={currentAnalysis} />
                </ErrorBoundary>
              )}
            </div>

            {/* Looping footer */}
            <Footer onNavigateToStudio={() => window.scrollTo({ top: 0, behavior: 'smooth' })} />
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
}

export default App;
