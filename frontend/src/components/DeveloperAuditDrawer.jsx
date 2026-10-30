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
} from 'lucide-react';
import { uploadRagDocument } from '../services/api';

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
            className={`pb-2.5 font-semibold transition-colors border-b-2 ${
              activeTab === 'rag'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Ingest to RAG Corpus
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
                    <span className="font-mono text-amber-400 font-bold">{riskLatency} ms</span>
                  </div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-amber-500 h-full rounded-full"
                      style={{ width: `${Math.min(100, (riskLatency / totalMs) * 100)}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Vector RAG Telemetry */}
              <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 space-y-3">
                <div className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                  <Database className="w-4 h-4 text-violet-400" />
                  Vector Database & Retrieval Telemetry
                </div>
                <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                  <div className="p-2.5 bg-slate-950 rounded-lg">
                    <span className="text-slate-500 block text-[10px]">Vector Search Time</span>
                    <span className="text-slate-200 font-bold">
                      {telemetry?.vector_retrieval_ms || 128} ms
                    </span>
                  </div>
                  <div className="p-2.5 bg-slate-950 rounded-lg">
                    <span className="text-slate-500 block text-[10px]">Documents Scanned</span>
                    <span className="text-slate-200 font-bold">
                      {telemetry?.documents_scanned || 8} Filings
                    </span>
                  </div>
                </div>
              </div>

              {/* Degraded Status info if active */}
              {telemetry?.degraded_data && (
                <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-300 space-y-1">
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
                        <div className="text-slate-300 bg-slate-900/80 p-2 rounded overflow-x-auto text-[10px] text-slate-300">
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
              <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 space-y-1">
                <div className="font-bold text-white flex items-center gap-1.5 text-sm">
                  <UploadCloud className="w-4 h-4 text-indigo-400" />
                  Live Dynamic Document Ingestion
                </div>
                <p className="text-slate-400 text-xs">
                  Upload an earnings call excerpt, SEC 10-Q filing, or SEBI circular. The RAG engine will chunk, extract sentiment polarity, and dynamically index it into the active vector corpus.
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
                  <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Filing / Text Content</label>
                  <textarea
                    rows={6}
                    value={uploadContent}
                    onChange={(e) => setUploadContent(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 text-xs rounded-lg p-2.5 text-white font-mono leading-relaxed"
                    placeholder="Paste regulatory text, earnings call management remarks, or broker research notes..."
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
          <span>Engine: Vibe-Orchestrator-v1.0</span>
          <span>Status: 200 OK</span>
        </div>
      </div>
    </div>
  );
}
