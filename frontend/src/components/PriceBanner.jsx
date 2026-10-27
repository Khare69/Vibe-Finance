import React, { useState, useEffect, useRef } from 'react';
import {
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Clock,
  BarChart3,
  ChevronDown,
  ChevronUp,
  Activity,
  Layers
} from 'lucide-react';
import { createChart, ColorType } from 'lightweight-charts';
import { getStockHistory } from '../services/api';

export default function PriceBanner({ analysis, isStale, isRagTimeout }) {
  const [showChart, setShowChart] = useState(false);
  const [timeframe, setTimeframe] = useState('1M');
  const [historyBars, setHistoryBars] = useState([]);
  const [isLoadingChart, setIsLoadingChart] = useState(false);
  const chartContainerRef = useRef(null);
  const chartInstanceRef = useRef(null);

  if (!analysis) return null;

  const { company_name, ticker, price_data, timestamp, synthesis } = analysis;
  const isPositive = (price_data?.change_percent || 0) >= 0;
  const feedStatus = price_data?.feed_status || (isStale ? 'STALE_FALLBACK_EOD' : 'LIVE');
  const symbol = price_data?.symbol || (['NVDA', 'AAPL', 'TSLA'].includes(ticker?.toUpperCase()) ? '$' : '₹');
  const macroRegime = synthesis?.macro_regime;

  // Mini Sparkline Points
  const sparkPoints = isPositive
    ? [20, 24, 22, 28, 26, 32, 30, 36, 34, 40]
    : [40, 36, 38, 30, 32, 26, 28, 22, 24, 18];
  const maxP = Math.max(...sparkPoints);
  const minP = Math.min(...sparkPoints);
  const sparkSvgPath = sparkPoints
    .map((val, i) => {
      const x = (i / (sparkPoints.length - 1)) * 90;
      const y = 35 - ((val - minP) / (maxP - minP || 1)) * 25;
      return `${i === 0 ? 'M' : 'L'}${x},${y}`;
    })
    .join(' ');

  // Fetch OHLCV history bars when chart is toggled or ticker/timeframe changes
  useEffect(() => {
    if (!showChart) return;
    let isCancelled = false;

    async function loadBars() {
      setIsLoadingChart(true);
      try {
        const bars = await getStockHistory(ticker, timeframe);
        if (!isCancelled) {
          setHistoryBars(bars);
        }
      } catch (err) {
        console.error('Error loading history bars:', err);
      } finally {
        if (!isCancelled) setIsLoadingChart(false);
      }
    }
    loadBars();

    return () => {
      isCancelled = true;
    };
  }, [showChart, ticker, timeframe]);

  // Render TradingView Lightweight Chart
  useEffect(() => {
    if (!showChart || !chartContainerRef.current || historyBars.length === 0) return;

    // Dispose prior instance
    if (chartInstanceRef.current) {
      chartInstanceRef.current.remove();
      chartInstanceRef.current = null;
    }

    const container = chartContainerRef.current;
    const chart = createChart(container, {
      layout: {
        background: { type: ColorType.Solid, color: '#0b1120' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: '#1e293b' },
        horzLines: { color: '#1e293b' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: '#334155',
      },
      timeScale: {
        borderColor: '#334155',
        timeVisible: true,
      },
      height: 280,
    });

    // Add Candlestick Series
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#10b981',
      downColor: '#f43f5e',
      borderVisible: false,
      wickUpColor: '#10b981',
      wickDownColor: '#f43f5e',
    });

    const candleData = historyBars.map((b) => ({
      time: b.time,
      open: b.open,
      high: b.high,
      low: b.low,
      close: b.close,
    }));
    candleSeries.setData(candleData);

    // Add Volume Series
    const volumeSeries = chart.addHistogramSeries({
      color: '#6366f1',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
    });
    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });
    const volumeData = historyBars.map((b) => ({
      time: b.time,
      value: b.volume || 1000000,
      color: b.close >= b.open ? '#10b98144' : '#f43f5e44',
    }));
    volumeSeries.setData(volumeData);

    chart.timeScale().fitContent();
    chartInstanceRef.current = chart;

    const handleResize = () => {
      if (chartContainerRef.current && chartInstanceRef.current) {
        chartInstanceRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartInstanceRef.current) {
        chartInstanceRef.current.remove();
        chartInstanceRef.current = null;
      }
    };
  }, [showChart, historyBars]);

  return (
    <div className="space-y-3">
      {/* Degraded Alert Banner if active */}
      {(feedStatus === 'STALE_FALLBACK_EOD' || isStale) && (
        <div className="bg-amber-500/10 border border-amber-500/40 rounded-xl p-3 flex items-start gap-3 text-amber-300 animate-in fade-in duration-300">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="text-xs">
            <span className="font-bold uppercase tracking-wider block">
              Market Feed Degraded: Fallback EOD Active
            </span>
            <span>
              Real-time websocket feed disconnected or delayed. Using previous close EOD metrics. An automatic -{price_data?.confidence_penalty ? Math.round(price_data.confidence_penalty) : 25} point confidence penalty has been applied to consensus scoring.
            </span>
          </div>
        </div>
      )}

      {isRagTimeout && (
        <div className="bg-rose-500/10 border border-rose-500/40 rounded-xl p-3 flex items-start gap-3 text-rose-300 animate-in fade-in duration-300">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div className="text-xs">
            <span className="font-bold uppercase tracking-wider block">
              RAG Corpus Vector Timeout
            </span>
            <span>
              Fundamental SEC/SEBI retrieval timed out. Pure Quantitative Momentum & Behavioral risk fallbacks are maintaining system operational continuity.
            </span>
          </div>
        </div>
      )}

      {/* Main Price & Volume Card */}
      <div className="bg-[#0f172a]/90 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h1 className="text-2xl font-black text-white tracking-tight">
                {company_name}
              </h1>
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                {ticker}
              </span>
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                  feedStatus.includes('LIVE')
                    ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                    : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                }`}
              >
                {feedStatus}
              </span>
            </div>
            <div className="flex items-center gap-4 text-xs text-slate-400 flex-wrap">
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-slate-500" />
                As of: {new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
              <span>52W H: {symbol}{price_data?.high_52w || 'N/A'}</span>
              <span>52W L: {symbol}{price_data?.low_52w || 'N/A'}</span>
              {macroRegime && (
                <span className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-indigo-300">
                  Regime: {macroRegime.regime_title}
                </span>
              )}
            </div>
          </div>

          {/* Price & Sparkline & Volume Stats */}
          <div className="flex items-center gap-6">
            {/* Mini Sparkline Chart */}
            <div className="hidden sm:flex flex-col items-end">
              <span className="text-[10px] text-slate-500 uppercase tracking-wider mb-0.5">20D Trend</span>
              <svg width="90" height="35" className="overflow-visible">
                <path
                  d={sparkSvgPath}
                  fill="none"
                  stroke={isPositive ? '#10b981' : '#f43f5e'}
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>

            {/* Price & Change */}
            <div className="text-right">
              <div className="text-2xl font-mono font-extrabold text-white">
                {symbol}
                {price_data?.current_price?.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </div>
              <div
                className={`text-xs font-mono font-bold flex items-center justify-end gap-1 ${
                  isPositive ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {isPositive ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                {isPositive ? '+' : ''}
                {price_data?.change_percent}%
              </div>
            </div>

            {/* Volume Anomaly */}
            <div className="pl-6 border-l border-slate-800 text-left">
              <div className="text-[10px] uppercase font-semibold text-slate-400 flex items-center gap-1">
                <BarChart3 className="w-3 h-3 text-indigo-400" /> Volume Surge
              </div>
              <div className="text-sm font-mono font-bold text-slate-200 mt-0.5">
                {price_data?.volume_anomaly_ratio}x avg
              </div>
              <div className="text-[10px] text-slate-500">
                {price_data?.volume_anomaly_ratio > 1.4 ? 'Spike detected' : 'Standard flow'}
              </div>
            </div>
          </div>
        </div>

        {/* Toggle TradingView Chart Button */}
        <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
          <button
            type="button"
            onClick={() => setShowChart(!showChart)}
            className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1.5 transition-colors py-1"
          >
            <Activity className="w-4 h-4 text-indigo-400" />
            <span>{showChart ? 'Hide Interactive Candlestick Chart' : 'Show TradingView Candlestick Chart (OHLCV)'}</span>
            {showChart ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {showChart && (
            <div className="flex items-center gap-1 text-[11px] font-mono bg-slate-900 border border-slate-800 p-0.5 rounded-lg">
              <button
                type="button"
                onClick={() => setTimeframe('1M')}
                className={`px-2.5 py-1 rounded ${timeframe === '1M' ? 'bg-indigo-600 text-white font-bold' : 'text-slate-400 hover:text-white'}`}
              >
                1M
              </button>
              <button
                type="button"
                onClick={() => setTimeframe('3M')}
                className={`px-2.5 py-1 rounded ${timeframe === '3M' ? 'bg-indigo-600 text-white font-bold' : 'text-slate-400 hover:text-white'}`}
              >
                3M
              </button>
            </div>
          )}
        </div>

        {/* Interactive Candlestick Chart Container */}
        {showChart && (
          <div className="space-y-2 pt-2 animate-in fade-in duration-300">
            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <span className="font-mono flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500 inline-block"></span> Bullish Close
                <span className="w-2.5 h-2.5 rounded-sm bg-rose-500 inline-block ml-2"></span> Bearish Close
                <span className="text-slate-500 ml-2">| Pan and scroll to zoom</span>
              </span>
              {isLoadingChart && <span className="text-indigo-400 font-mono">Loading OHLCV bars...</span>}
            </div>
            <div
              ref={chartContainerRef}
              className="w-full rounded-xl overflow-hidden border border-slate-800 bg-[#0b1120]"
              style={{ minHeight: '280px' }}
            />
          </div>
        )}
      </div>
    </div>
  );
}
