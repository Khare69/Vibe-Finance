import React, { useState } from 'react';
import {
  X,
  Terminal,
  Activity,
  Cpu,
  Database,
  Shield,
  Clock,
  Layers,
  Copy,
  Check,
  UploadCloud,
  FilePlus,
  Sparkles,
  Search,
  Filter,
  CheckCircle2,
  Calendar,
  Table as TableIcon
} from 'lucide-react';
import { uploadRagDocument, searchRagCorpus } from '../services/api';

export default function DeveloperAuditDrawer({
  isOpen,
  onClose,
  telemetry,
  agents,
  rawAnalysis,
  streamEvents = [],
}) {
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState('telemetry'); // 'telemetry' | 'stream' | 'rag' | 'json'

  // RAG Explorer & Upload Sub-tabs
  const [ragSubMode, setRagSubMode] = useState('search'); // 'search' | 'upload'

  // Interactive Hybrid Search State
  const [searchTicker, setSearchTicker] = useState('HDFCBANK');
  const [searchQuery, setSearchQuery] = useState('Gross Non-Performing Assets GNPA');
  const [searchMode, setSearchMode] = useState('hybrid'); // 'hybrid' | 'bm25' | 'dense'
  const [searchAsOfDate, setSearchAsOfDate] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState(null);

  // RAG upload state
  const [uploadTicker, setUploadTicker] = useState('RELIANCE');
  const [uploadTitle, setUploadTitle] = useState('Q4 Earnings & Guidance');
  const [uploadSection, setUploadSection] = useState('Operational Update');
  const [uploadContent, setUploadContent] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);

  if (!isOpen) return null;

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(rawAnalysis, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const quantLatency = agents?.quant?.latency_ms || 115;
  const ragLatency = agents?.rag?.latency_ms || 342;
  const riskLatency = agents?.behavioral_risk?.latency_ms || 85;
  const totalMs = telemetry?.total_execution_ms || quantLatency + ragLatency + riskLatency;

  const handleSearchRag = async (e) => {
    e.preventDefault();
    setIsSearching(true);
    setSearchResults(null);
    try {
      const res = await searchRagCorpus({
        ticker: searchTicker,
        query: searchQuery,
        topK: 3,
        asOfDate: searchAsOfDate || null,
        mode: searchMode,
      });
      setSearchResults(res);
    } catch (err) {
      setSearchResults({ status: 'ERROR', error: err.message, citations: [] });
    } finally {
      setIsSearching(false);
    }
  };

  const handleUploadRag = async (e) => {
    e.preventDefault();
    if (!uploadContent.trim()) return;
    setIsUploading(true);
    setUploadResult(null);
    try {
      const res = await uploadRagDocument({
        ticker: uploadTicker,
        document_title: uploadTitle,
        section: uploadSection,
        content: uploadContent,
      });
      setUploadResult({ success: true, data: res });
      setUploadContent('');
    } catch (err) {
      setUploadResult({ success: false, error: err.message });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-xs animate-in fade-in">
      <div className="w-full max-w-xl h-full bg-[#0b1120] border-l border-slate-800 shadow-2xl flex flex-col">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Terminal className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white tracking-tight">
                Developer Session Audit & Telemetry
              </h2>
              <p className="text-[11px] text-slate-400">
                Agent latency, vector retrieval profiling & calibrated confidence
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab switcher */}
        <div className="flex border-b border-slate-800 bg-slate-950 px-5 pt-2 gap-4 text-xs">
          <button
            onClick={() => setActiveTab('telemetry')}
            className={`pb-2.5 font-semibold transition-colors border-b-2 ${
              activeTab === 'telemetry'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Latency & Pipeline Metrics
          </button>
          <button
            onClick={() => setActiveTab('stream')}
            className={`pb-2.5 font-semibold transition-colors border-b-2 ${
              activeTab === 'stream'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            StateGraph & Live Stream
          </button>
          <button
            onClick={() => setActiveTab('rag')}
            className={`pb-2.5 font-semibold transition-colors border-b-2 flex items-center gap-1.5 ${
              activeTab === 'rag'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            Hybrid RAG Inspector
          </button>
          <button
            onClick={() => setActiveTab('json')}
            className={`pb-2.5 font-semibold transition-colors border-b-2 ${
              activeTab === 'json'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Raw Multi-Agent JSON
          </button>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {activeTab === 'telemetry' ? (
            <>
              {/* Total Execution Banner */}
              <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">
                    Total Pipeline Latency
                  </span>
                  <div className="text-2xl font-mono font-black text-white">
                    {totalMs} <span className="text-xs text-indigo-400 font-sans">ms</span>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">
                    Confidence Calibration
                  </span>
                  <div className="text-2xl font-mono font-black text-emerald-400">
                    {telemetry?.confidence_score || 63}%
                  </div>
                </div>
              </div>

              {/* Per-Agent Latency Waterfall */}
              <div className="space-y-3">
                <div className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Per-Agent Execution Latency
                </div>

                {/* Quant */}
                <div className="p-3 rounded-xl bg-slate-900/40 border border-slate-800 space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="font-semibold text-slate-200">Quant Momentum Agent</span>
                    <span className="font-mono text-indigo-400 font-bold">{quantLatency} ms</span>
                  </div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-indigo-500 h-full rounded-full"
                      style={{ width: `${Math.min(100, (quantLatency / totalMs) * 100)}%` }}
                    />
                  </div>
                </div>

                {/* Fundamental RAG */}
                <div className="p-3 rounded-xl bg-slate-900/40 border border-slate-800 space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="font-semibold text-slate-200">Fundamental RAG Agent</span>
                    <span className="font-mono text-violet-400 font-bold">{ragLatency} ms</span>
                  </div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-violet-500 h-full rounded-full"
                      style={{ width: `${Math.min(100, (ragLatency / totalMs) * 100)}%` }}
                    />
                  </div>
                </div>

                {/* Behavioral Risk */}
                <div className="p-3 rounded-xl bg-slate-900/40 border border-slate-800 space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="font-semibold text-slate-200">Behavioral Risk Manager</span>
                    <span className="font-mono text-emerald-400 font-bold">{riskLatency} ms</span>
                  </div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-emerald-500 h-full rounded-full"
                      style={{ width: `${Math.min(100, (riskLatency / totalMs) * 100)}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Data Health & Circuit Breakers */}
              <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 space-y-2">
                <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                  <Shield className="w-4 h-4 text-indigo-400" /> Circuit-Breaker Status
                </span>
                <div className="grid grid-cols-2 gap-2 font-mono text-[11px]">
                  <div className="p-2 rounded bg-slate-950 border border-slate-800/80">
                    <span className="text-slate-500 block text-[10px]">PRICE FEED</span>
                    <span className="text-emerald-400 font-bold">LIVE_SOCKET</span>
                  </div>
                  <div className="p-2 rounded bg-slate-950 border border-slate-800/80">
                    <span className="text-slate-500 block text-[10px]">RAG TIMEOUT</span>
                    <span className="text-emerald-400 font-bold">NORMAL (342ms)</span>
                  </div>
                </div>
              </div>

              {/* Active Degraded Telemetry Warnings */}
              {telemetry?.degraded_data && (
                <div className="p-3.5 bg-amber-500/10 border border-amber-500/30 rounded-xl text-amber-300 text-xs">
                  <span className="font-bold uppercase tracking-wide block">Degraded Mode Telemetry</span>
                  <p>{telemetry.degraded_reason || 'System is running with active fallback indicators.'}</p>
                </div>
              )}
            </>
          ) : activeTab === 'stream' ? (
            <div className="space-y-4 text-xs">
              {/* Header Info */}
              <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 space-y-1">
                <div className="font-bold text-white flex items-center gap-1.5 text-sm">
                  <Activity className="w-4 h-4 text-emerald-400" />
                  StateGraph Orchestrator & Live SSE Telemetry
                </div>
                <p className="text-slate-400 text-xs">
                  Real-time Server-Sent Events emitted across state machine graph transitions: Market Context &rarr; Parallel Analysts &rarr; Debate Arbitration &rarr; Convergence Guard &rarr; Synthesis.
                </p>
              </div>

              {/* StateGraph Execution Trace */}
              {rawAnalysis?.execution_trace && rawAnalysis.execution_trace.length > 0 && (
                <div className="space-y-2">
                  <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider block">
                    State Graph Node Execution Trace
                  </span>
                  <div className="space-y-1.5">
                    {rawAnalysis.execution_trace.map((step, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800/80 flex items-center justify-between font-mono"
                      >
                        <div className="flex items-center gap-2">
                          <span className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center text-[10px] font-bold">
                            {idx + 1}
                          </span>
                          <span className="font-semibold text-slate-200">{step.node}</span>
                          <span className="text-[10px] text-slate-500 uppercase px-1.5 py-0.5 rounded bg-slate-800">
                            {step.status}
                          </span>
                        </div>
                        <span className="text-emerald-400 font-bold">{step.duration_ms} ms</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Live SSE Stream Event Feed */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">
                    Server-Sent Event (SSE) Stream Feed ({streamEvents.length} events)
                  </span>
                  <span className="flex items-center gap-1.5 text-[10px] text-emerald-400 font-mono">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping inline-block" />
                    LIVE_SOCKET
                  </span>
                </div>

                {streamEvents.length === 0 ? (
                  <div className="p-4 rounded-xl bg-slate-900/30 border border-dashed border-slate-800 text-center text-slate-500">
                    No active stream events captured for this session yet. Events are recorded during analysis execution.
                  </div>
                ) : (
                  <div className="space-y-2 max-h-[45vh] overflow-y-auto pr-1">
                    {streamEvents.map((evt, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 rounded-lg bg-slate-950 border border-slate-800/90 text-[11px] font-mono space-y-1"
                      >
                        <div className="flex justify-between items-center text-slate-400">
                          <span className="text-indigo-400 font-bold">
                            event: <span className="text-emerald-400">{evt.type}</span>
                          </span>
                          <span className="text-[10px] text-slate-500">
                            {evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : `#${idx + 1}`}
                          </span>
                        </div>
                        <div className="text-slate-300 bg-slate-900/80 p-2 rounded overflow-x-auto text-[10px]">
                          {typeof evt.payload === 'object'
                            ? JSON.stringify(evt.payload, null, 2)
                            : String(evt.payload)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : activeTab === 'rag' ? (
            <div className="space-y-4 text-xs">
              {/* RAG Sub-Tab Navigation */}
              <div className="flex rounded-xl bg-slate-950 p-1 border border-slate-800 gap-1">
                <button
                  type="button"
                  onClick={() => setRagSubMode('search')}
                  className={`flex-1 py-1.5 rounded-lg font-semibold flex items-center justify-center gap-1.5 transition-all ${
                    ragSubMode === 'search'
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Search className="w-3.5 h-3.5" />
                  <span>Hybrid Search & Inspector</span>
                </button>
                <button
                  type="button"
                  onClick={() => setRagSubMode('upload')}
                  className={`flex-1 py-1.5 rounded-lg font-semibold flex items-center justify-center gap-1.5 transition-all ${
                    ragSubMode === 'upload'
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <UploadCloud className="w-3.5 h-3.5" />
                  <span>Ingest Document / Table</span>
                </button>
              </div>

              {ragSubMode === 'search' ? (
                /* Interactive Hybrid Search Explorer */
                <div className="space-y-4">
                  <div className="bg-slate-900/60 p-3.5 rounded-xl border border-slate-800 space-y-1">
                    <div className="font-bold text-white flex items-center gap-1.5 text-xs">
                      <Cpu className="w-3.5 h-3.5 text-indigo-400" />
                      Multi-Stage Hybrid Retrieval Explorer (BM25 + Dense RRF)
                    </div>
                    <p className="text-slate-400 text-[11px]">
                      Test exact financial keyword retrieval vs dense vector embeddings, with live Reciprocal Rank Fusion scores and strict Point-in-Time date filtering.
                    </p>
                  </div>

                  <form onSubmit={handleSearchRag} className="space-y-3 bg-slate-950/60 p-3.5 rounded-xl border border-slate-800">
                    <div className="grid grid-cols-2 gap-2.5">
                      <div>
                        <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Target Ticker</label>
                        <input
                          type="text"
                          value={searchTicker}
                          onChange={(e) => setSearchTicker(e.target.value.toUpperCase())}
                          className="w-full bg-slate-900 border border-slate-800 text-xs rounded-lg px-2.5 py-1.5 text-white font-mono"
                          placeholder="e.g. HDFCBANK, RELIANCE"
                          required
                        />
                      </div>
                      <div>
                        <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Retrieval Mode</label>
                        <select
                          value={searchMode}
                          onChange={(e) => setSearchMode(e.target.value)}
                          className="w-full bg-slate-900 border border-slate-800 text-xs rounded-lg px-2.5 py-1.5 text-white font-mono"
                        >
                          <option value="hybrid">Hybrid (BM25 + Dense RRF)</option>
                          <option value="bm25">BM25 Okapi Lexical Only</option>
                          <option value="dense">Dense Vector Only</option>
                        </select>
                      </div>
                    </div>

                    <div>
                      <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Search Query / Financial Ratio</label>
                      <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 text-xs rounded-lg px-2.5 py-1.5 text-white font-mono"
                        placeholder="e.g. Net Interest Margin 3.45%, Gross NPA, EBITDA contraction"
                        required
                      />
                    </div>

                    <div>
                      <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">
                        Point-in-Time Constraint (as_of_date)
                      </label>
                      <input
                        type="date"
                        value={searchAsOfDate}
                        onChange={(e) => setSearchAsOfDate(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 text-xs rounded-lg px-2.5 py-1.5 text-white font-mono"
                      />
                      <span className="text-[10px] text-slate-500 block mt-0.5">
                        Leave blank for latest filings, or pick a date to test zero look-ahead bias.
                      </span>
                    </div>

                    <button
                      type="submit"
                      disabled={isSearching}
                      className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-bold transition-all flex items-center justify-center gap-1.5 text-xs shadow-sm shadow-indigo-600/30"
                    >
                      <Search className="w-3.5 h-3.5" />
                      <span>{isSearching ? 'Executing Hybrid Retrieval...' : 'Execute Hybrid Retrieval'}</span>
                    </button>
                  </form>

                  {/* Search Results Display */}
                  {searchResults && (
                    <div className="space-y-3">
                      <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 px-1">
                        <span>Status: <strong className="text-white">{searchResults.status}</strong></span>
                        <span>{searchResults.documents_scanned} scanned in {searchResults.retrieval_ms}ms</span>
                      </div>

                      {searchResults.citations?.length === 0 ? (
                        <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800 text-center text-slate-500 text-xs font-mono">
                          {searchResults.status === 'NO_POINT_IN_TIME_FILINGS'
                            ? `Point-in-time filter strictly excluded all filings published after ${searchAsOfDate}.`
                            : 'No matching regulatory documents found for this candidate query.'}
                        </div>
                      ) : (
                        searchResults.citations?.map((c, i) => (
                          <div key={i} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                            <div className="flex items-start justify-between gap-2">
                              <div>
                                <span className="font-bold text-slate-100 text-xs block">{c.document_title}</span>
                                <span className="text-[10px] font-mono text-indigo-400">{c.section} · {c.filing_date}</span>
                              </div>
                              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 shrink-0">
                                Relevance: {Math.round((c.relevance_score || 0.85) * 100)}%
                              </span>
                            </div>

                            <p className="text-xs text-slate-300 leading-relaxed font-sans bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/60">
                              "{c.excerpt}"
                            </p>

                            {/* Scoring Diagnostic Strip */}
                            <div className="grid grid-cols-3 gap-2 text-[10px] font-mono pt-1 text-center">
                              <div className="p-1.5 rounded bg-slate-900 border border-slate-800">
                                <span className="text-slate-500 block">BM25 Okapi</span>
                                <span className="text-amber-400 font-bold">{c.bm25_score ?? 0}</span>
                              </div>
                              <div className="p-1.5 rounded bg-slate-900 border border-slate-800">
                                <span className="text-slate-500 block">Dense Cosine</span>
                                <span className="text-indigo-400 font-bold">{c.similarity_cosine ?? 0}</span>
                              </div>
                              <div className="p-1.5 rounded bg-slate-900 border border-slate-800">
                                <span className="text-slate-500 block">RRF Score</span>
                                <span className="text-cyan-400 font-bold">{c.rrf_score ?? 0}</span>
                              </div>
                            </div>

                            {/* Structured Table Preview if present */}
                            {c.structured_table && (
                              <div className="mt-2 pt-2 border-t border-slate-900">
                                <span className="text-[10px] font-bold text-violet-400 flex items-center gap-1 mb-1">
                                  <TableIcon className="w-3 h-3" /> {c.structured_table.title || 'Structured Table'}
                                </span>
                                <div className="overflow-x-auto rounded border border-slate-800 bg-slate-900/40 p-1.5">
                                  <table className="w-full text-[10px] text-left">
                                    <thead>
                                      <tr className="text-slate-400 border-b border-slate-800">
                                        {c.structured_table.headers?.map((h, hi) => (
                                          <th key={hi} className="p-1 font-semibold">{h}</th>
                                        ))}
                                      </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-800/40">
                                      {c.structured_table.rows?.map((r, ri) => (
                                        <tr key={ri} className="text-slate-300">
                                          {r.map((cell, ci) => (
                                            <td key={ci} className="p-1 font-mono">{cell}</td>
                                          ))}
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              </div>
                            )}
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </div>
              ) : (
                /* Dynamic Document Ingestion Form */
                <div className="space-y-4">
                  <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 space-y-1">
                    <div className="font-bold text-white flex items-center gap-1.5 text-sm">
                      <UploadCloud className="w-4 h-4 text-indigo-400" />
                      Live Dynamic Document & Table Ingestion
                    </div>
                    <p className="text-slate-400 text-xs">
                      Upload an earnings call excerpt, SEC 10-Q filing, SEBI circular, or markdown table. The engine automatically chunks, normalizes tables, extracts sentiment polarity, and updates both BM25 and vector indices.
                    </p>
                  </div>

                  <form onSubmit={handleUploadRag} className="space-y-3">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Ticker</label>
                        <input
                          type="text"
                          value={uploadTicker}
                          onChange={(e) => setUploadTicker(e.target.value.toUpperCase())}
                          className="w-full bg-slate-950 border border-slate-800 text-xs rounded-lg px-2.5 py-2 text-white font-mono"
                          placeholder="e.g. RELIANCE, NVDA"
                          required
                        />
                      </div>
                      <div>
                        <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Section</label>
                        <input
                          type="text"
                          value={uploadSection}
                          onChange={(e) => setUploadSection(e.target.value)}
                          className="w-full bg-slate-950 border border-slate-800 text-xs rounded-lg px-2.5 py-2 text-white font-mono"
                          placeholder="e.g. Guidance / Risk"
                          required
                        />
                      </div>
                    </div>

                    <div>
                      <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Document Title</label>
                      <input
                        type="text"
                        value={uploadTitle}
                        onChange={(e) => setUploadTitle(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 text-xs rounded-lg px-2.5 py-2 text-white font-mono"
                        placeholder="e.g. FY25 Annual Report"
                        required
                      />
                    </div>

                    <div>
                      <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Filing / Text Content (Supports Markdown Tables)</label>
                      <textarea
                        rows={6}
                        value={uploadContent}
                        onChange={(e) => setUploadContent(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 text-xs rounded-lg p-2.5 text-white font-mono leading-relaxed"
                        placeholder="Paste regulatory text or markdown table e.g. | Metric | Q3 FY26 |..."
                        required
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={isUploading}
                      className="w-full py-2.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white rounded-lg font-bold transition-all shadow-md shadow-indigo-600/30 flex items-center justify-center gap-2"
                    >
                      <FilePlus className="w-4 h-4" />
                      <span>{isUploading ? 'Chunking & Indexing...' : 'Index Document into RAG Corpus'}</span>
                    </button>
                  </form>

                  {uploadResult && uploadResult.success && (
                    <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-300 flex items-start gap-2">
                      <Check className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-bold block">Document Successfully Indexed!</span>
                        <span className="text-[11px] text-emerald-400/80">
                          Created {uploadResult.data.chunks_created} vector chunks for {uploadResult.data.ticker}. Active corpus size: {uploadResult.data.total_corpus_documents} documents.
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-400">Payload inspection:</span>
                <button
                  onClick={handleCopyJson}
                  className="flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300"
                >
                  {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? 'Copied' : 'Copy JSON'}</span>
                </button>
              </div>
              <pre className="p-4 bg-slate-950 rounded-xl border border-slate-800 text-[11px] font-mono text-emerald-400 overflow-x-auto max-h-[60vh]">
                {JSON.stringify(rawAnalysis, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/60 text-[11px] text-slate-500 flex justify-between">
          <span>Engine: Vibe-Orchestrator-v1.0 (Hybrid BM25 + Dense RRF)</span>
          <span>Status: 200 OK</span>
        </div>
      </div>
    </div>
  );
}
