import React, { useState, useEffect } from 'react';
import './index.css';
import { Header } from './components/Header';
import { WisprHero } from './components/WisprHero';
import { DictationPlayground } from './components/DictationPlayground';
import { FeatureShowcase } from './components/FeatureShowcase';
import { VideoAnalyzerStudio } from './components/VideoAnalyzerStudio';
import { InteractiveChat } from './components/InteractiveChat';
import { Footer } from './components/Footer';

function App() {
  const [activeView, setActiveView] = useState('home');
  const [studioUrl, setStudioUrl] = useState('');
  const [currentAnalysis, setCurrentAnalysis] = useState(null);

  // Scroll to top on mount/refresh
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  // Load last analysis result from localStorage if available
  useEffect(() => {
    const saved = localStorage.getItem('lastStudioAnalysis');
    if (saved) {
      try {
        setCurrentAnalysis(JSON.parse(saved));
      } catch (e) {
        console.error('Failed to parse cached analysis:', e);
      }
    }
  }, []);

  const handleStartAnalysis = (url) => {
    setStudioUrl(url);
    setActiveView('studio');
    // Scroll to the top of the studio workspace
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleExplorePresets = () => {
    setActiveView('studio');
    // Scroll down to the studio presets card
    setTimeout(() => {
      const el = document.getElementById('studio');
      el?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  const handleAnalysisReady = (result) => {
    setCurrentAnalysis(result);
    // Cache result in localStorage
    localStorage.setItem('lastStudioAnalysis', JSON.stringify(result));
  };

  return (
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
        <div className="pt-20 bg-[#FDFCF0] min-h-screen flex flex-col justify-between animate-fade-in">
          <div className="flex-1 pb-16">
            {/* Functional Video Agent Studio (transcribing + presets) */}
            <VideoAnalyzerStudio
              initialSource={studioUrl}
              onAnalysisReady={handleAnalysisReady}
            />

            {/* Vector RAG Chat Assistant */}
            <InteractiveChat currentAnalysis={currentAnalysis} />
          </div>

          {/* Looping footer */}
          <Footer onNavigateToStudio={() => window.scrollTo({ top: 0, behavior: 'smooth' })} />
        </div>
      )}
    </div>
  );
}

export default App;
