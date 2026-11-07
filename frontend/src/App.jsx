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
import AuthModal from './components/AuthModal';

import {
  checkSystemHealth,
  getStocks,
  runMultiAgentAnalysis,
  streamMultiAgentAnalysis,
  getPortfolio,
  getStoredUserProfile,
  updateStoredUserProfile,
  getCurrentUser,
  logoutUser,
} from './services/api';

import {
  MOCK_STOCKS,
  MOCK_ANALYSES,
  MOCK_USER_PORTFOLIO,
} from './services/mockData';

export default function App() {
  // System & Profile State
  const [systemHealth, setSystemHealth] = useState(null);
  const [currentUser, setCurrentUser] = useState({
    id: 'default_user',
    username: 'demo_user',
    role: 'investor',
    is_authenticated: false,
  });
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
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState(null);

  // Fault Injection Toggles
  const [staleMode, setStaleMode] = useState(false);
  const [ragTimeoutMode, setRagTimeoutMode] = useState(false);

  // Streaming Telemetry & Execution State
  const [streamEvents, setStreamEvents] = useState([]);
  const [streamStep, setStreamStep] = useState('');

  // Reload user and tenant data
  const refreshTenantData = async () => {
    try {
      const [userRes, port, storedProf] = await Promise.all([
        getCurrentUser().catch(() => null),
        getPortfolio().catch(() => MOCK_USER_PORTFOLIO),
        getStoredUserProfile().catch(() => null),
      ]);
      if (userRes && userRes.user) {
        setCurrentUser({ ...userRes.user, is_authenticated: !!userRes.is_authenticated });
      }
      if (port) setPortfolio(port);
      if (storedProf && storedProf.risk_level) {
        setUserProfile(storedProf);
      }
    } catch (e) {
      console.error('Error refreshing tenant data:', e);
    }
  };

  // Initialize data on mount
  useEffect(() => {
    async function init() {
      const [health, stockList] = await Promise.all([
        checkSystemHealth(),
        getStocks(),
      ]);
      setSystemHealth(health);
      setStocks(stockList);
      await refreshTenantData();
    }
    init();
  }, []);

  const handleAuthSuccess = async (user) => {
    setCurrentUser({ ...user, is_authenticated: true });
    await refreshTenantData();
  };

  const handleLogout = async () => {
    logoutUser();
    setCurrentUser({
      id: 'default_user',
      username: 'demo_user',
      role: 'investor',
      is_authenticated: false,
    });
    await refreshTenantData();
  };

  // Fetch / stream analysis whenever ticker, profile, or fault toggles change
  useEffect(() => {
    let isCancelled = false;

    async function fetchAnalysis() {
      setIsLoading(true);
      setStreamEvents([]);
      setStreamStep(`Connecting live state graph stream for ${selectedTicker}...`);

      try {
        const result = await streamMultiAgentAnalysis({
          ticker: selectedTicker,
          userProfile,
          explainMode,
          simulatedStaleData: staleMode,
          simulatedRagTimeout: ragTimeoutMode,
          onEvent: (event) => {
            if (!isCancelled) {
              setStreamEvents((prev) => [...prev, event]);
              if (event.type === 'node_start') {
                setStreamStep(`Executing ${event.payload?.node}...`);
              } else if (event.type === 'node_complete') {
                setStreamStep(`Completed ${event.payload?.node}`);
              }
            }
          },
          onError: (err) => {
            if (!isCancelled) {
              console.warn('Stream error handled by fallback:', err);
              setStreamStep('Stream interrupted. Fallback engaged.');
            }
          },
        });

        if (!isCancelled && result) {
          setAnalysis(result);
        }
      } catch (err) {
        console.error('Failed to run analysis:', err);
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    fetchAnalysis();

    return () => {
      isCancelled = true;
    };
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
        currentUser={currentUser}
        onOpenVibeCheck={() => setIsVibeCheckOpen(true)}
        onOpenDevDrawer={() => setIsDevDrawerOpen(true)}
        onOpenExportMemo={() => setIsExportMemoOpen(true)}
        onOpenAuthModal={() => setIsAuthModalOpen(true)}
        onLogout={handleLogout}
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
          onSelectTicker={setSelectedTicker}
        />

        {/* Real-time Price & Provenance Header */}
        <PriceBanner
          analysis={analysis}
          priceData={analysis?.price_data}
          companyName={analysis?.company_name}
          ticker={selectedTicker}
          userProfile={userProfile}
          isStale={staleMode}
          isRagTimeout={ragTimeoutMode}
        />

        {/* Explain Mode Switcher (Beginner vs. Expert Trader) */}
        <div className="flex items-center justify-between bg-slate-900/40 border border-slate-800/80 px-4 py-3 rounded-xl">
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Explanation Tone:
            </span>
            <div className="flex bg-slate-950/80 p-1 rounded-lg border border-slate-800">
              <button
                onClick={() => setExplainMode('beginner')}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${
                  explainMode === 'beginner'
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Beginner Intuitive
              </button>
              <button
                onClick={() => setExplainMode('expert')}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${
                  explainMode === 'expert'
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Quant Trader Pro
              </button>
            </div>
          </div>

          {/* Active Streaming Node Indicator */}
          {isLoading && (
            <div className="flex items-center gap-2 text-xs font-mono text-indigo-400 animate-pulse">
              <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
              <span>{streamStep || 'Reasoning across state graph...'}</span>
            </div>
          )}
        </div>

        {/* Core Multi-Agent Adversarial Debate & Synthesis Grid */}
        <MultiAgentDebate
          analysis={analysis}
          agents={analysis?.agents}
          debate={analysis?.debate}
          synthesis={analysis?.synthesis}
          regulatoryGuardrail={analysis?.regulatory_compliance_guardrail}
          explainMode={explainMode}
          onOpenCitation={(cit) => setSelectedCitation(cit)}
          onSelectCitation={(cit) => setSelectedCitation(cit)}
          selectedTicker={selectedTicker}
        />

        {/* Grounding & Explainability: Why This Stock, Why Right Now? */}
        <WhyThisWhyNow
          ticker={selectedTicker}
          synthesis={analysis?.synthesis}
          quantResult={analysis?.agents?.quant}
          ragResult={analysis?.agents?.rag}
          behavioralResult={analysis?.agents?.behavioral_risk}
          priceData={analysis?.price_data}
          explainMode={explainMode}
        />

        {/* Institutional Backtesting & Walk-Forward Validation Engine */}
        <BacktestSimulator
          ticker={selectedTicker}
        />

        {/* Institutional Macroeconomic Stress-Testing Simulator */}
        <MacroStressSimulator
          portfolio={portfolio}
        />

        {/* Two-Column Grid: Sentiment Timeline & Dynamic Portfolio Heatmap */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SentimentTimeline
            sentimentShift={analysis?.sentiment_shift}
            ticker={selectedTicker}
          />

          <PortfolioHeatmapSimulator
            portfolio={portfolio}
            currentPrice={currentPrice}
            userProfile={userProfile}
            selectedTicker={selectedTicker}
          />
        </div>

        {/* Portfolio Rebalancer & Trade Optimization Panel */}
        <PortfolioRebalancer
          portfolio={portfolio}
          selectedTicker={selectedTicker}
          synthesis={analysis?.synthesis}
          userProfile={userProfile}
        />

        {/* Architecture Resiliency & Fault Injection Showcase */}
        <ResiliencyControls
          staleMode={staleMode}
          ragTimeoutMode={ragTimeoutMode}
          onToggleStale={() => setStaleMode(!staleMode)}
          onToggleRagTimeout={() => setRagTimeoutMode(!ragTimeoutMode)}
          onResetFaults={handleResetFaults}
          telemetry={analysis?.telemetry}
        />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-[#06090e] py-6 px-4 lg:px-8 text-xs text-slate-500 mt-12">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-center sm:text-left">
          <div className="space-y-1">
            <span className="block font-medium text-slate-400">
              VibeFinance · Explainable Multi-Agent Financial Research & Stress-Testing Architecture
            </span>
            <span className="block text-[10px] text-slate-500 max-w-3xl leading-relaxed">
              SEBI Statutory Disclaimer: Algorithmic modeling and quantitative research prototype only. Does not constitute registered investment advice or portfolio recommendations under SEBI (Investment Advisers) Regulations, 2013 or SEBI (Research Analysts) Regulations, 2014. Consult a SEBI-registered Investment Adviser (RIA) before committing capital.
            </span>
          </div>
          <div className="flex items-center gap-4 shrink-0">
            <button
              onClick={() => setIsDevDrawerOpen(true)}
              className="text-indigo-400 hover:text-indigo-300 font-mono text-xs"
            >
              Session Telemetry
            </button>
            <span className="font-mono text-[10px] text-slate-500">v1.0.0 Grounded</span>
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
        streamEvents={streamEvents}
      />

      {/* Exportable Investment Decision Memo Modal */}
      <ExportMemoModal
        isOpen={isExportMemoOpen}
        onClose={() => setIsExportMemoOpen(false)}
        analysis={analysis}
        userProfile={userProfile}
      />

      {/* User Authentication & Tenant Modal */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onAuthSuccess={handleAuthSuccess}
        activeUser={currentUser}
      />
    </div>
  );
}
