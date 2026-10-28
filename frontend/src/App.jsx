import React, { useState, useEffect } from 'react';
import { AlertTriangle } from 'lucide-react';
import Header from './components/Header';
import VibeCheckModal from './components/VibeCheckModal';
import TickerSelector from './components/TickerSelector';
import PriceBanner from './components/PriceBanner';
import MultiAgentDebate from './components/MultiAgentDebate';
import WhyThisWhyNow from './components/WhyThisWhyNow';
import RagSourceViewerModal from './components/RagSourceViewerModal';
import SentimentTimeline from './components/SentimentTimeline';
import PortfolioHeatmapSimulator from './components/PortfolioHeatmapSimulator';
import ResiliencyControls from './components/ResiliencyControls';
import DeveloperAuditDrawer from './components/DeveloperAuditDrawer';
import BacktestSimulator from './components/BacktestSimulator';
import ExportMemoModal from './components/ExportMemoModal';
import PortfolioRebalancer from './components/PortfolioRebalancer';
import MacroStressSimulator from './components/MacroStressSimulator';

import {
  checkSystemHealth,
  getStocks,
  runMultiAgentAnalysis,
  getPortfolio,
  getStoredUserProfile,
  updateStoredUserProfile,
} from './services/api';

import {
  MOCK_STOCKS,
  MOCK_ANALYSES,
  MOCK_USER_PORTFOLIO,
} from './services/mockData';

export default function App() {
  // System & Profile State
  const [systemHealth, setSystemHealth] = useState(null);
  const [userProfile, setUserProfile] = useState({
    risk_level: 'conservative',
    investment_horizon: 'medium',
    panic_sell_tendency: 0.8,
    preferred_sectors: ['Energy', 'Tech'],
    portfolio_cash: 250000,
  });

  // Stock & Analysis State - initialized with instant baseline data so screen never flashes blank
  const [stocks, setStocks] = useState(MOCK_STOCKS);
  const [selectedTicker, setSelectedTicker] = useState('RELIANCE');
  const [analysis, setAnalysis] = useState(MOCK_ANALYSES['RELIANCE']);
  const [portfolio, setPortfolio] = useState(MOCK_USER_PORTFOLIO);
  const [isLoading, setIsLoading] = useState(false);

  // Modals & UI Controls
  const [explainMode, setExplainMode] = useState('beginner'); // 'beginner' | 'expert'
  const [isVibeCheckOpen, setIsVibeCheckOpen] = useState(false);
  const [isDevDrawerOpen, setIsDevDrawerOpen] = useState(false);
  const [isExportMemoOpen, setIsExportMemoOpen] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState(null);

  // Fault Injection Toggles
  const [staleMode, setStaleMode] = useState(false);
  const [ragTimeoutMode, setRagTimeoutMode] = useState(false);

  // Initialize data on mount
  useEffect(() => {
    async function init() {
      const [health, stockList, port, storedProf] = await Promise.all([
        checkSystemHealth(),
        getStocks(),
        getPortfolio(),
        getStoredUserProfile().catch(() => null),
      ]);
      setSystemHealth(health);
      setStocks(stockList);
      setPortfolio(port);
      if (storedProf && storedProf.risk_level) {
        setUserProfile(storedProf);
      }
    }
    init();
  }, []);

  // Fetch / run analysis whenever ticker, profile, or fault toggles change
  useEffect(() => {
    async function fetchAnalysis() {
      setIsLoading(true);
      try {
        const result = await runMultiAgentAnalysis({
          ticker: selectedTicker,
          userProfile,
          explainMode,
          simulatedStaleData: staleMode,
          simulatedRagTimeout: ragTimeoutMode,
        });
        setAnalysis(result);
      } catch (err) {
        console.error('Failed to run analysis:', err);
      } finally {
        setIsLoading(false);
      }
    }
    fetchAnalysis();
  }, [selectedTicker, userProfile, staleMode, ragTimeoutMode]);

  const handleResetFaults = () => {
    setStaleMode(false);
    setRagTimeoutMode(false);
  };

  const currentPrice = analysis?.price_data?.current_price || 2845.50;

  return (
    <div className="min-h-screen bg-[#080c14] text-slate-100 flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Sticky Header */}
      <Header
        systemHealth={systemHealth}
        userProfile={userProfile}
        onOpenVibeCheck={() => setIsVibeCheckOpen(true)}
        onOpenDevDrawer={() => setIsDevDrawerOpen(true)}
        onOpenExportMemo={() => setIsExportMemoOpen(true)}
        staleMode={staleMode}
        ragTimeoutMode={ragTimeoutMode}
      />

      {/* Backend Offline / Demo Snapshot Warning Banner */}
      {(systemHealth?.is_backend_offline || analysis?.is_offline_mock) && (
        <div className="bg-amber-500/10 border-b border-amber-500/30 px-4 py-2.5 text-center text-xs text-amber-300 flex items-center justify-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            <strong>Demo Mode (Backend Offline):</strong> FastAPI backend is unreachable. Displaying local demo snapshot. Run <code className="bg-amber-950/60 px-1.5 py-0.5 rounded text-amber-200 font-mono text-[11px]">start_backend.bat</code> to connect live multi-agent intelligence.
          </span>
        </div>
      )}

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 lg:px-8 py-6 space-y-6">
        {/* Watchlist & Ticker Selector */}
        <TickerSelector
          stocks={stocks}
          selectedTicker={selectedTicker}
          onSelectTicker={(ticker) => setSelectedTicker(ticker)}
          isLoading={isLoading}
        />

        {/* Loading Overlay or Price Banner */}
        {isLoading && !analysis ? (
          <div className="bg-[#0f172a] border border-slate-800 rounded-2xl p-12 text-center animate-pulse">
            <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <h3 className="text-base font-bold text-white">
              Agents Analyzing {selectedTicker}...
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Quant calculating momentum · RAG scanning SEC/SEBI filings · Risk Manager evaluating constraints
            </p>
          </div>
        ) : (
          analysis && (
            <>
              {/* Live Price & Day Change Banner */}
              <PriceBanner
                analysis={analysis}
                isStale={staleMode}
                isRagTimeout={ragTimeoutMode}
              />

              {/* Multi-Agent Debate Section (Quant, RAG Fundamental, Behavioral Risk) */}
              <MultiAgentDebate
                analysis={analysis}
                onOpenCitation={(cite) => setSelectedCitation(cite)}
              />

              {/* 'Why This, Why Now?' Decomposition & ELI5 Toggle */}
              <WhyThisWhyNow
                synthesis={analysis.synthesis}
                explainMode={explainMode}
                onToggleExplainMode={(mode) => setExplainMode(mode)}
              />

              {/* 2-Column Grid: Sentiment Shift Timeline & Portfolio Risk Heatmap */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <SentimentTimeline sentimentData={analysis.sentiment_shift} />
                <PortfolioHeatmapSimulator
                  portfolio={portfolio}
                  userProfile={userProfile}
                  activeTicker={selectedTicker}
                  currentPrice={currentPrice}
                />
              </div>

              {/* Advanced Risk Tools: Portfolio Rebalancer & Macro Stress Testing */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <PortfolioRebalancer
                  portfolio={portfolio}
                  userProfile={userProfile}
                  onRebalanceComplete={() => {
                    // Refresh portfolio state on rebalance
                    getPortfolio().then(setPortfolio).catch(console.error);
                  }}
                />
                <MacroStressSimulator
                  portfolio={portfolio}
                  activeTicker={selectedTicker}
                />
              </div>

              {/* Historical Backtesting Simulator */}
              <BacktestSimulator activeTicker={selectedTicker} />

              {/* Resiliency & Fault Injection Toggles */}
              <ResiliencyControls
                staleMode={staleMode}
                ragTimeoutMode={ragTimeoutMode}
                onToggleStale={setStaleMode}
                onToggleRagTimeout={setRagTimeoutMode}
                onReset={handleResetFaults}
              />
            </>
          )
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-[#080c14] py-6 px-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          <span>
            Vibe Finance · Multi-Agent Explainable AI Architecture · Built for resilient financial reasoning
          </span>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setIsDevDrawerOpen(true)}
              className="text-indigo-400 hover:text-indigo-300 font-mono text-xs"
            >
              Session Telemetry
            </button>
            <span>v1.0.0 Production</span>
          </div>
        </div>
      </footer>

      {/* Vibe Check Onboarding / Calibration Modal */}
      <VibeCheckModal
        isOpen={isVibeCheckOpen}
        onClose={() => setIsVibeCheckOpen(false)}
        userProfile={userProfile}
        onSaveProfile={(newProf) => {
          setUserProfile(newProf);
          updateStoredUserProfile(newProf).catch(console.error);
        }}
      />

      {/* Highlight-to-Source RAG Footnote Viewer Modal */}
      <RagSourceViewerModal
        isOpen={!!selectedCitation}
        citation={selectedCitation}
        onClose={() => setSelectedCitation(null)}
      />

      {/* Developer View / Session Audit Inspector Drawer */}
      <DeveloperAuditDrawer
        isOpen={isDevDrawerOpen}
        onClose={() => setIsDevDrawerOpen(false)}
        telemetry={analysis?.telemetry}
        agents={analysis?.agents}
        rawAnalysis={analysis}
      />

      {/* Exportable Investment Decision Memo Modal */}
      <ExportMemoModal
        isOpen={isExportMemoOpen}
        onClose={() => setIsExportMemoOpen(false)}
        analysis={analysis}
        userProfile={userProfile}
      />
    </div>
  );
}
