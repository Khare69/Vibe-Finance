import React, { useState } from 'react';
import {
  PieChart,
  ShieldAlert,
  ArrowUpRight,
  TrendingDown,
  TrendingUp,
  AlertOctagon,
  CheckCircle,
  HelpCircle,
  Briefcase,
  Play,
  RotateCcw,
} from 'lucide-react';
import { simulateTrade } from '../services/api';

export default function PortfolioHeatmapSimulator({
  portfolio,
  userProfile,
  activeTicker,
  selectedTicker,
  currentPrice = 240,
}) {
  const currentSelected = selectedTicker || activeTicker || 'RELIANCE';
  const [tradeAction, setTradeAction] = useState('BUY');
  const [tradeQuantity, setTradeQuantity] = useState(15);
  const [tradeTicker, setTradeTicker] = useState(currentSelected);
  const [simResult, setSimResult] = useState(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [showNudgeModal, setShowNudgeModal] = useState(false);

  // Update ticker if activeTicker / selectedTicker changes
  React.useEffect(() => {
    if (currentSelected) setTradeTicker(currentSelected);
  }, [currentSelected]);

  // Baseline ticker price lookup for Indian NSE equities
  const TICKER_PRICES = {
    RELIANCE: 2845.50,
    TCS: 3915.00,
    INFY: 1825.40,
    HDFCBANK: 1650.00,
    TATAMOTORS: 940.00,
    ICICIBANK: 1210.00,
    ITC: 475.00,
    COCHINSHIP: 1580.00,
    ZOMATO: 260.00,
    CDSL: 1420.00,
  };

  const handleSimulateTrade = async (e) => {
    if (e) e.preventDefault();
    setIsSimulating(true);

    // Use current active price only if the trade matches the actively viewed ticker; otherwise use ticker's base price
    const resolvedPrice = (tradeTicker === activeTicker && currentPrice)
      ? currentPrice
      : (TICKER_PRICES[tradeTicker] || 150.0);

    try {
      const res = await simulateTrade({
        ticker: tradeTicker,
        action: tradeAction,
        quantity: Number(tradeQuantity),
        price: resolvedPrice,
        userProfile,
      });

      setSimResult(res);
      if (res.warning_triggered) {
        setShowNudgeModal(true);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsSimulating(false);
    }
  };

  const sectorAllocation = portfolio?.sector_allocations?.map((s, idx) => ({
    sector: s.sector,
    percentage: s.allocation_pct ?? s.percentage ?? 25,
    color: ['#6366f1', '#10b981', '#38bdf8', '#f59e0b', '#94a3b8'][idx % 5],
  })) || portfolio?.sector_allocation || [
    { sector: 'IT Services', percentage: 46.5, color: '#6366f1' },
    { sector: 'Energy / Retail', percentage: 26.5, color: '#10b981' },
    { sector: 'Consumer Tech', percentage: 14.0, color: '#38bdf8' },
    { sector: 'Cash Reserve', percentage: 13.0, color: '#94a3b8' },
  ];

  const portfolioBeta = portfolio?.portfolio_beta ?? 0.88;
  const portfolioCash = portfolio?.cash ?? 450000;

  return (
    <div className="bg-[#0f172a] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <Briefcase className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide uppercase">
              Portfolio Risk Heatmap & "What-If" Simulator
            </h3>
            <p className="text-xs text-slate-400">
              Interactive allocation modeling with pre-trade behavioral guardrail checks
            </p>
          </div>
        </div>

        {/* Portfolio Macro Metrics */}
        <div className="flex items-center gap-4 text-xs font-mono bg-slate-900/80 px-3 py-1.5 rounded-xl border border-slate-800">
          <div>
            <span className="text-slate-500 text-[10px] block">Portfolio Beta</span>
            <span className="font-bold text-white">
              {portfolioBeta} ({Number(portfolioBeta) > 1.1 ? 'Aggressive' : 'Defensive'})
            </span>
          </div>
          <div className="border-l border-slate-800 pl-3">
            <span className="text-slate-500 text-[10px] block">Cash Reserve</span>
            <span className="font-bold text-emerald-400">
              ₹{Number(portfolioCash).toLocaleString()}
            </span>
          </div>
        </div>
      </div>

      {/* Sector Allocation Heatmap Grid */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs text-slate-400 font-semibold">
          <span>Current Sector Risk Distribution:</span>
          <span>Max Cap: 50% per Sector</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {sectorAllocation.map((s, idx) => {
            const isHigh = s.percentage > 45;
            return (
              <div
                key={idx}
                className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 relative overflow-hidden"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-semibold text-slate-300 truncate">
                    {s.sector}
                  </span>
                  <span className="font-mono text-xs font-bold text-white">
                    {s.percentage}%
                  </span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${s.percentage}%`,
                      backgroundColor: s.color,
                    }}
                  />
                </div>
                {isHigh && (
                  <span className="text-[10px] text-amber-400 font-semibold mt-1 block">
                    Near allocation threshold
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* "What-If" Trade Simulator Form */}
      <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="text-xs font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
            <Play className="w-3.5 h-3.5" /> "What-If" Trade Execution Simulator
          </div>
          <span className="text-[11px] text-slate-500">
            Tests how an order shifts your concentration & beta before executing
          </span>
        </div>

        <form onSubmit={handleSimulateTrade} className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          {/* Action */}
          <div>
            <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Action</label>
            <select
              value={tradeAction}
              onChange={(e) => setTradeAction(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 text-xs rounded-lg px-2.5 py-2 text-white focus:outline-none focus:border-indigo-500 font-mono"
            >
              <option value="BUY">BUY</option>
              <option value="SELL">SELL / TRIM</option>
            </select>
          </div>

          {/* Ticker */}
          <div>
            <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Stock (NSE / BSE)</label>
            <select
              value={tradeTicker}
              onChange={(e) => setTradeTicker(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 text-xs rounded-lg px-2.5 py-2 text-white focus:outline-none focus:border-indigo-500 font-mono font-bold"
            >
              <option value="RELIANCE">RELIANCE (Energy & Retail | Beta 1.05)</option>
              <option value="TCS">TCS (IT Services | Beta 0.68)</option>
              <option value="INFY">INFY (IT Services | Beta 0.82)</option>
              <option value="HDFCBANK">HDFCBANK (Financials | Beta 0.95)</option>
              <option value="TATAMOTORS">TATAMOTORS (Automotive | Beta 1.35)</option>
              <option value="ICICIBANK">ICICIBANK (Financials | Beta 1.10)</option>
              <option value="ITC">ITC (FMCG | Beta 0.55)</option>
              <option value="COCHINSHIP">COCHINSHIP (Defense & Shipyard | Beta 1.65)</option>
              <option value="ZOMATO">ZOMATO (Consumer Tech | Beta 1.45)</option>
              <option value="CDSL">CDSL (Capital Markets | Beta 1.25)</option>
              {!['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'TATAMOTORS', 'ICICIBANK', 'ITC', 'COCHINSHIP', 'ZOMATO', 'CDSL'].includes(tradeTicker) && (
                <option value={tradeTicker}>{tradeTicker} (Active Equity)</option>
              )}
            </select>
          </div>

          {/* Quantity */}
          <div>
            <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Quantity</label>
            <input
              type="number"
              min="1"
              value={tradeQuantity}
              onChange={(e) => setTradeQuantity(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 text-xs rounded-lg px-2.5 py-2 text-white focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>

          {/* Execute Sim Button */}
          <div className="flex items-end">
            <button
              type="submit"
              disabled={isSimulating}
              className="w-full py-2 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white rounded-lg text-xs font-bold transition-all shadow-md shadow-indigo-600/30 flex items-center justify-center gap-1.5"
            >
              <Play className="w-3 h-3" />
              <span>Simulate Order</span>
            </button>
          </div>
        </form>

        {/* Permanent Inline Simulation Results Card */}
        {simResult && (
          <div className="mt-4 p-4 rounded-xl bg-slate-950/80 border border-slate-700/70 space-y-4 animate-in fade-in duration-300">
            {/* Header / Badges */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800/80 gap-2">
              <div className="flex items-center gap-2">
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider font-mono ${
                  simResult.action === 'BUY' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                }`}>
                  {simResult.action} {simResult.quantity} × {simResult.ticker}
                </span>
                <span className="text-xs font-mono text-slate-300">
                  @ ₹{Number(simResult.price).toLocaleString('en-IN', { minimumFractionDigits: 2 })} = 
                  <strong className="text-white ml-1">₹{Number(simResult.trade_amount || (simResult.quantity * simResult.price)).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</strong>
                </span>
              </div>
              <div className="flex items-center gap-2">
                {simResult.warning_triggered ? (
                  <span className="flex items-center gap-1 text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-amber-500/15 text-amber-400 border border-amber-500/30">
                    <ShieldAlert className="w-3 h-3" />
                    Behavioral Nudge Active
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                    <CheckCircle className="w-3 h-3" />
                    SEBI Mandate Compliant
                  </span>
                )}
                <button
                  type="button"
                  onClick={() => setSimResult(null)}
                  className="text-slate-500 hover:text-slate-300 p-1 rounded transition-colors"
                  title="Clear Simulation"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Before-vs-After Metrics Grid */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 text-xs font-mono">
              {/* Metric 1: Cash Reserve */}
              <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                <span className="text-slate-400 text-[10px] uppercase font-bold block mb-1">Cash Reserve Shift</span>
                <div className="flex items-baseline gap-1.5 flex-wrap">
                  <span className="text-slate-400 text-xs line-through">₹{Number(simResult.current_cash || (portfolio?.cash ?? 100000)).toLocaleString('en-IN')}</span>
                  <span className="text-slate-500 text-xs">➔</span>
                  <span className={`text-sm font-bold ${simResult.action === 'BUY' ? 'text-amber-400' : 'text-emerald-400'}`}>
                    ₹{Number(simResult.projected_cash ?? (simResult.current_cash - simResult.trade_amount)).toLocaleString('en-IN')}
                  </span>
                </div>
                <span className="text-[10px] text-slate-500 block mt-1">
                  Net Delta: {simResult.action === 'BUY' ? '-' : '+'}₹{Number(simResult.trade_amount).toLocaleString('en-IN')}
                </span>
              </div>

              {/* Metric 2: Portfolio Beta */}
              <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                <span className="text-slate-400 text-[10px] uppercase font-bold block mb-1">Portfolio Beta</span>
                <div className="flex items-baseline gap-1.5">
                  <span className="text-slate-400 text-xs">{simResult.portfolio_delta?.current_beta ?? portfolioBeta}</span>
                  <span className="text-slate-500 text-xs">➔</span>
                  <span className={`text-sm font-bold ${
                    Number(simResult.portfolio_delta?.projected_beta) > 1.1 ? 'text-rose-400' : 'text-emerald-400'
                  }`}>
                    {simResult.portfolio_delta?.projected_beta}
                  </span>
                </div>
                <span className="text-[10px] text-slate-500 block mt-1">
                  Risk Profile: {Number(simResult.portfolio_delta?.projected_beta) > 1.1 ? 'Aggressive' : (Number(simResult.portfolio_delta?.projected_beta) > 0.85 ? 'Balanced' : 'Defensive')}
                </span>
              </div>

              {/* Metric 3: Sector Concentration */}
              <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                <span className="text-slate-400 text-[10px] uppercase font-bold block mb-1">
                  {simResult.sector || 'Sector'} Concentration
                </span>
                <div className="flex items-baseline gap-1.5">
                  <span className="text-slate-400 text-xs">{simResult.portfolio_delta?.current_tech_pct}%</span>
                  <span className="text-slate-500 text-xs">➔</span>
                  <span className={`text-sm font-bold ${
                    Number(simResult.portfolio_delta?.projected_tech_pct) > 40 ? 'text-rose-400' : 'text-indigo-400'
                  }`}>
                    {simResult.portfolio_delta?.projected_tech_pct}%
                  </span>
                </div>
                <span className="text-[10px] text-slate-500 block mt-1">
                  Max Cap Limit: 50.0%
                </span>
              </div>

              {/* Metric 4: Statutory Charges */}
              <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                <span className="text-slate-400 text-[10px] uppercase font-bold block mb-1">Est. STT & Charges</span>
                <div className="text-sm font-bold text-slate-200">
                  ₹{Number(simResult.estimated_stt_charges || (simResult.trade_amount * 0.00115)).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
                <span className="text-[10px] text-slate-500 block mt-1">
                  NSE Delivery (0.115% rate)
                </span>
              </div>
            </div>

            {/* Assessment Box */}
            <div className={`p-3 rounded-xl border text-xs leading-relaxed ${
              simResult.warning_triggered
                ? 'bg-amber-500/10 border-amber-500/30 text-amber-200'
                : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-200'
            }`}>
              <div className="flex items-start gap-2">
                {simResult.warning_triggered ? (
                  <AlertOctagon className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                ) : (
                  <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                )}
                <div>
                  <div className="font-semibold">{simResult.nudge_message}</div>
                  {simResult.suggested_alternative && (
                    <div className="mt-1 text-[11px] opacity-90 text-indigo-300">
                      <strong>SEBI Advisory Recommendation:</strong> {simResult.suggested_alternative}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Legal Footnote */}
            <div className="text-[10px] text-slate-500 flex items-center justify-between border-t border-slate-900 pt-2">
              <span>{simResult.regulatory_compliance_guardrail?.framework || 'SEBI (Investment Advisers) Regulations, 2013'}</span>
              <span>Marginal portfolio reweighting simulation • No capital committed</span>
            </div>
          </div>
        )}
      </div>

      {/* Behavioral Nudge Modal / Alert Interceptor */}
      {showNudgeModal && simResult && simResult.warning_triggered && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in">
          <div className="w-full max-w-lg bg-[#0f172a] border border-amber-500/40 rounded-2xl shadow-2xl p-6 space-y-4">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400">
                <AlertOctagon className="w-7 h-7" />
              </div>
              <div>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  Behavioral Nudge Triggered
                </span>
                <h3 className="text-lg font-bold text-white mt-1">
                  Hold on! Let's Review This Order
                </h3>
              </div>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              {simResult.nudge_message}
            </p>

            {/* Before vs After Delta Table */}
            <div className="bg-slate-900/90 rounded-xl border border-slate-800 p-3 space-y-2 text-xs font-mono">
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wide">
                Projected Portfolio Delta Impact
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="p-2 bg-slate-950/70 rounded-lg">
                  <span className="text-slate-500 block text-[10px]">{simResult.sector || 'Sector'} Exposure</span>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-slate-300">{simResult.portfolio_delta?.current_tech_pct}%</span>
                    <span className="text-rose-400 font-bold">➔ {simResult.portfolio_delta?.projected_tech_pct}%</span>
                  </div>
                </div>
                <div className="p-2 bg-slate-950/70 rounded-lg">
                  <span className="text-slate-500 block text-[10px]">Portfolio Beta</span>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-slate-300">{simResult.portfolio_delta?.current_beta}</span>
                    <span className="text-rose-400 font-bold">➔ {simResult.portfolio_delta?.projected_beta}</span>
                  </div>
                </div>
              </div>
            </div>

            {simResult.suggested_alternative && (
              <div className="p-3 rounded-xl bg-indigo-950/30 border border-indigo-500/20 text-xs text-indigo-300">
                <span className="font-bold block text-indigo-200">Suggested Action:</span>
                {simResult.suggested_alternative}
              </div>
            )}

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowNudgeModal(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 rounded-lg"
              >
                Cancel Order
              </button>
              <button
                type="button"
                onClick={() => setShowNudgeModal(false)}
                className="px-4 py-2 text-xs font-semibold text-white bg-amber-600 hover:bg-amber-500 rounded-lg"
              >
                Proceed with Caution
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
