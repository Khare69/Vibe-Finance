import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  TrendingDown,
  TrendingUp,
  Zap,
  RotateCcw,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  Clock,
  DollarSign,
  Layers,
  HelpCircle,
  Activity
} from 'lucide-react';
import { runPortfolioStressTest } from '../services/api';

export default function MacroStressSimulator({ portfolio, activeTicker = 'NVDA' }) {
  const [selectedScenario, setSelectedScenario] = useState('rate_hike_2022');
  const [stressResult, setStressResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let isCancelled = false;
    async function executeStressTest() {
      setIsLoading(true);
      try {
        const res = await runPortfolioStressTest({ scenarioId: selectedScenario });
        if (!isCancelled && res) {
          setStressResult(res);
        }
      } catch (err) {
        console.error('Failed to run stress test:', err);
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }
    executeStressTest();

    return () => {
      isCancelled = true;
    };
  }, [selectedScenario, portfolio?.total_value]);

  const totalValue = stressResult?.baseline_total_value || portfolio?.total_value || 500000;
  const projectedPnL = stressResult?.portfolio_pnl_delta ?? -73000;
  const drawdownPct = stressResult?.portfolio_drawdown_pct ?? -14.6;
  const isLoss = drawdownPct < 0;
  const shockedBeta = stressResult?.shocked_portfolio_beta ?? 1.15;
  const cashBuffer = stressResult?.cash_buffer;
  const assetImpacts = stressResult?.asset_impacts || [];
  const scenarioInfo = stressResult?.scenario || {};
  const agentGuidance = stressResult?.agent_guidance || {};

  return (
    <div className="bg-[#0f172a] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide uppercase">
              Macro Shock Stress-Testing Engine
            </h3>
            <p className="text-xs text-slate-400">
              Factor-based stress simulations across active holdings & SEBI compliance guardrails
            </p>
          </div>
        </div>

        {/* Scenario Selector Pills */}
        <div className="flex flex-wrap items-center gap-1.5 p-1 bg-slate-900 border border-slate-800 rounded-xl text-xs">
          <button
            type="button"
            onClick={() => setSelectedScenario('rate_hike_2022')}
            className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
              selectedScenario === 'rate_hike_2022'
                ? 'bg-rose-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            2022 Rates
          </button>
          <button
            type="button"
            onClick={() => setSelectedScenario('covid_liquidity_2020')}
            className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
              selectedScenario === 'covid_liquidity_2020'
                ? 'bg-rose-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            2020 Liquidity
          </button>
          <button
            type="button"
            onClick={() => setSelectedScenario('crude_supply_shock')}
            className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
              selectedScenario === 'crude_supply_shock'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Oil & Stagflation
          </button>
          <button
            type="button"
            onClick={() => setSelectedScenario('tech_multiple_pullback_2024')}
            className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
              selectedScenario === 'tech_multiple_pullback_2024'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            2024 Tech Pullback
          </button>
        </div>
      </div>

      {/* Scenario Overview Card */}
      <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h4 className="text-sm font-bold text-white">{scenarioInfo.name || 'Macro Factor Shock'}</h4>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                Horizon: {scenarioInfo.recovery_horizon_months || '12-16 Months'}
              </span>
            </div>
            <p className="text-xs text-slate-400">{scenarioInfo.description}</p>
          </div>
          <div className="text-right shrink-0">
            <span className="text-[10px] text-slate-500 uppercase font-bold block">
              Projected Portfolio Impact
            </span>
            <div className={`text-lg font-mono font-bold flex items-center justify-end gap-1 ${
              isLoss ? 'text-rose-400' : 'text-emerald-400'
            }`}>
              {isLoss ? <TrendingDown className="w-4 h-4" /> : <TrendingUp className="w-4 h-4" />}
              <span>{isLoss ? '' : '+'}{drawdownPct}%</span>
              <span className="text-xs text-slate-400">
                ({isLoss ? '-' : '+'}₹{Math.abs(projectedPnL).toLocaleString()})
              </span>
            </div>
            <span className="text-[10px] font-mono text-slate-400 block">
              Post-Shock Beta: <strong className="text-indigo-400">{shockedBeta}</strong>
            </span>
          </div>
        </div>

        {/* Cash Buffer & Ruin Probability Bar */}
        {cashBuffer && (
          <div className="pt-3 border-t border-slate-800/80 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
            <div className="bg-slate-950/70 p-2.5 rounded-lg border border-slate-800/80">
              <span className="text-slate-500 text-[10px] block font-sans">Cash Buffer Balance</span>
              <span className="font-bold text-slate-200">
                ₹{cashBuffer.cash_amount?.toLocaleString()} ({cashBuffer.cash_pct_after_shock}%)
              </span>
            </div>
            <div className="bg-slate-950/70 p-2.5 rounded-lg border border-slate-800/80">
              <span className="text-slate-500 text-[10px] block font-sans">Liquidity Adequacy</span>
              <span className={`font-bold ${
                cashBuffer.adequacy_rating?.includes('STRONG')
                  ? 'text-emerald-400'
                  : cashBuffer.adequacy_rating?.includes('ADEQUATE')
                  ? 'text-indigo-400'
                  : 'text-amber-400'
              }`}>
                {cashBuffer.adequacy_rating?.replace(/_/g, ' ')}
              </span>
            </div>
            <div className="bg-slate-950/70 p-2.5 rounded-lg border border-slate-800/80">
              <span className="text-slate-500 text-[10px] block font-sans">Projected Ruin Probability</span>
              <span className="font-bold text-emerald-400">
                {cashBuffer.projected_ruin_probability_pct}% (Low Tail Risk)
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Asset-by-Asset Impact Breakdown Table */}
      {assetImpacts.length > 0 && (
        <div className="space-y-2">
          <div className="flex justify-between items-center text-xs">
            <span className="font-bold uppercase tracking-wider text-slate-400">
              Asset-by-Asset Stress Impact Breakdown
            </span>
            <span className="text-[10px] font-mono text-slate-500">
              {assetImpacts.length} Active Holdings Evaluated
            </span>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-900/80 text-[10px] uppercase text-slate-400 font-bold border-b border-slate-800">
                <tr>
                  <th className="p-2.5">Asset</th>
                  <th className="p-2.5">Sector</th>
                  <th className="p-2.5">Beta</th>
                  <th className="p-2.5 text-right">Pre-Shock Value</th>
                  <th className="p-2.5 text-right">Factor Shock</th>
                  <th className="p-2.5 text-right">PnL Delta (₹)</th>
                  <th className="p-2.5 text-right">Post-Shock Value</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {assetImpacts.map((asset, idx) => {
                  const assetLoss = asset.pnl_delta < 0;
                  return (
                    <tr key={idx} className="hover:bg-slate-900/50 transition-colors">
                      <td className="p-2.5 font-bold text-white">
                        {asset.ticker}
                        <span className="text-[10px] text-slate-500 font-sans block truncate max-w-[120px]">
                          {asset.company_name}
                        </span>
                      </td>
                      <td className="p-2.5 text-slate-300">{asset.sector}</td>
                      <td className="p-2.5 text-slate-400">{asset.beta}</td>
                      <td className="p-2.5 text-right text-slate-200">
                        ₹{asset.original_value?.toLocaleString()}
                      </td>
                      <td className={`p-2.5 text-right font-bold ${
                        asset.shock_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'
                      }`}>
                        {asset.shock_pct >= 0 ? '+' : ''}{asset.shock_pct}%
                      </td>
                      <td className={`p-2.5 text-right font-bold ${
                        assetLoss ? 'text-rose-400' : 'text-emerald-400'
                      }`}>
                        {assetLoss ? '-' : '+'}₹{Math.abs(asset.pnl_delta)?.toLocaleString()}
                      </td>
                      <td className="p-2.5 text-right text-slate-100 font-bold">
                        ₹{asset.shocked_value?.toLocaleString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Autonomous Agent Defensive Re-calibration */}
      <div className="space-y-2">
        <div className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Agent Response Calibration During This Shock
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <span className="text-indigo-400 font-bold block mb-1">Quant Agent:</span>
            <span className="text-slate-300 text-[11px] leading-relaxed">
              {agentGuidance.quant || 'MOMENTUM ROTATION: Exit breakdown assets below 200-SMA.'}
            </span>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <span className="text-violet-400 font-bold block mb-1">Fundamental RAG:</span>
            <span className="text-slate-300 text-[11px] leading-relaxed">
              {agentGuidance.rag || 'RISING DISCOUNT RATE: DCF multiple compression across earnings transcripts.'}
            </span>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <span className="text-amber-400 font-bold block mb-1">Risk Manager:</span>
            <span className="text-slate-300 text-[11px] leading-relaxed">
              {agentGuidance.risk || 'DEFENSIVE BUFFER: Enforce max drawdown boundary constraints.'}
            </span>
          </div>
        </div>
      </div>

      {/* Statutory SEBI Regulatory Compliance Guardrail */}
      <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 flex items-start gap-2.5 text-xs font-sans">
        <ShieldCheck className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <span className="font-bold block uppercase tracking-wide text-[11px]">
            SEBI Regulatory Compliance Guardrail (Research Analyst & Investment Adviser Regulations)
          </span>
          <p className="text-[11px] text-amber-200/90 leading-relaxed">
            All macroeconomic shock simulations, portfolio drawdown percentages, and multi-agent stance calibrations are hypothetical algorithmic models designed exclusively for educational and stress-testing purposes. They DO NOT constitute registered investment advice or personalized portfolio management recommendations under SEBI (Investment Advisers) Regulations, 2013 or SEBI (Research Analysts) Regulations, 2014. Consult a SEBI-registered Investment Adviser (RIA) before committing capital.
          </p>
        </div>
      </div>
    </div>
  );
}
