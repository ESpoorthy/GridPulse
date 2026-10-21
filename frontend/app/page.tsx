/**
 * Intelligence Overview Page - Figma Design Implementation
 * 
 * Displays key metrics, energy horizon chart, and intelligence briefing.
 * Uses real API data when backend is available, falls back to demo data.
 */

'use client';

import { LoadingState } from '@/components/ui/LoadingSpinner';
import { ErrorState } from '@/components/ui/ErrorState';
import { getDemoOverviewData, getDemoRecentConsumption } from '@/lib/demoData';
import { demoModeEnabled } from '@/lib/utils';
import { DemoDataBanner } from '@/components/ui/DemoDataBanner';
import { fetchOverview } from '@/lib/api';
import { OverviewData } from '@/lib/types';
import { ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area } from 'recharts';
import { Calendar } from 'lucide-react';
import { useState, useEffect } from 'react';

export default function IntelligenceOverviewPage() {
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      
      try {
        const apiData = await fetchOverview();
        
        if (apiData) {
          setOverview(apiData);
        } else if (demoModeEnabled()) {
          setOverview(getDemoOverviewData());
        } else {
          setError('The API has no overview data. Start the backend with validated dataset artifacts, or add ?demo=1 for synthetic preview data.');
        }
      } catch {
        if (demoModeEnabled()) setOverview(getDemoOverviewData());
        else setError('Could not reach the API. Add ?demo=1 to view synthetic preview data.');
      } finally {
        setLoading(false);
      }
    }
    
    loadData();
  }, []);
  
  if (loading) {
    return (
      <div className="p-8">
        <LoadingState message="Loading overview data..." />
      </div>
    );
  }
  
  if (error || !overview) {
    return (
      <div className="p-8">
        <ErrorState
          message="Failed to Load Data"
          detail={error || "Could not load overview data"}
          retry={() => window.location.reload()}
        />
      </div>
    );
  }
  
  const recentData = overview.recentConsumption || (overview.isDemo ? getDemoRecentConsumption() : []);
  
  // Split data into observed and forecast for chart
  const observedData = recentData.map(p => ({
    timestamp: new Date(p.timestamp).getTime(),
    time: new Date(p.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
    observed: p.power,
  }));
  
  const forecastData: typeof observedData = [];
  
  const chartData = [...observedData, ...forecastData];

  if (!overview.isDemo) {
    return <div className="min-h-screen p-6 md:p-10 text-[#e8f0ec]">
      <header className="mb-8 border-b border-[#29383d] pb-5"><p className="text-[#93a7ab] text-sm">GridPulse / Intelligence</p><h1 className="mt-2 text-3xl">Historical power overview</h1><p className="mt-2 text-sm text-[#93a7ab]">UCI household data · last observed {new Date(overview.lastUpdated).toLocaleString()}</p></header>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[['Latest hourly mean', `${overview.currentPower.toFixed(3)} kW`], ['Latest day mean', `${overview.dailyAverage.toFixed(3)} kW`], ['Weekly mean change', `${overview.weeklyChange.toFixed(2)}% (${overview.weeklyTrend})`], ['Anomaly flags · 7 days', String(overview.anomalyCount)]].map(([label, value]) => <section key={label} className="rounded-lg border border-[#29383d] bg-[#121d21] p-5"><p className="text-sm text-[#93a7ab]">{label}</p><p className="mt-3 text-2xl font-mono">{value}</p>{label==='Latest day mean'&&<p className="mt-2 text-xs text-[#93a7ab]">Coverage {overview.dailyCoveragePercentage}% · {overview.dailyObservedHours}/{overview.dailyExpectedHours} available hourly intervals</p>}</section>)}
      </div>
      <section className="mt-6 rounded-lg border border-[#29383d] bg-[#121d21] p-5"><h2 className="mb-4 font-medium">Recent observed hourly mean active power (kW)</h2><div className="h-[340px]"><ResponsiveContainer width="100%" height="100%"><ComposedChart data={observedData}><CartesianGrid stroke="#29383d"/><XAxis dataKey="time" tick={{fill:'#93a7ab',fontSize:10}}/><YAxis unit=" kW" tick={{fill:'#93a7ab',fontSize:10}}/><Tooltip/><Line type="monotone" dataKey="observed" stroke="#9cdccb" dot={false}/></ComposedChart></ResponsiveContainer></div></section>
      <p className="mt-5 text-xs text-[#6b7f84]">Source: {overview.dataSource}. Historical household observations; no live meter connection.</p>
    </div>;
  }
  
  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <header className="border-b border-[#29383d] px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <span className="text-[#93a7ab] text-sm">Workspace / Intelligence</span>
        </div>
        <div className="flex items-center gap-4 text-[#93a7ab] text-xs">
          <span>OBSERVATION · {new Date(overview.lastUpdated).toLocaleString()}</span>
          <button className="p-1.5 hover:bg-[#1a2b30] rounded"><Calendar className="w-4 h-4" /></button>
        </div>
      </header>
      {overview.isDemo && <div className="px-8 pt-5"><DemoDataBanner /></div>}
      
      {/* Main Content */}
      <div className="flex-1 overflow-auto px-8 py-6">
        {/* Page Title */}
        <div className="mb-6">
          <p className="text-[#bcf58a] text-[10px] font-mono mb-2">01 / ENERGY INTELLIGENCE</p>
          <div className="flex items-center justify-between">
            <h1 className="text-[#e8f0ec] text-[34px] font-medium">Intelligence overview</h1>
            <button className="bg-[#18252a] border border-[#29383d] px-4 py-2 rounded text-[#e8f0ec] text-sm hover:bg-[#1a2b30]">
              Export report
            </button>
          </div>
          <p className="text-[#93a7ab] text-sm mt-2">
            Understand the last 24 hours. See what comes next. Know where to look closer.
          </p>
        </div>
        
        <div className="bg-[#18252a] border border-[#29383d] px-4 py-2 rounded-lg mb-6 flex items-center gap-2">
          <span className="text-[#93a7ab] text-xs">Latest observation · {new Date(overview.lastUpdated).toLocaleString()}</span>
          <span className="text-[#6b7f84] text-xs ml-auto">Hourly mean active power · kW</span>
        </div>
        
        {/* KPI Cards */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-5">
            <p className="text-[#93a7ab] text-[11px] mb-2">Mean observed power · latest day</p>
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-[#e8f0ec] text-[32px] font-mono leading-none">{overview.dailyAverage.toFixed(3)}</span>
              <span className="text-[#93a7ab] text-sm">kW</span>
            </div>
            <p className="text-[#93a7ab] text-[10px]">Mean of valid hourly observations</p>
          </div>
          
          <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-5">
            <p className="text-[#93a7ab] text-[11px] mb-2">Latest observed power</p>
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-[#e8f0ec] text-[32px] font-mono leading-none">{overview.currentPower.toFixed(3)}</span>
              <span className="text-[#93a7ab] text-sm">kW</span>
            </div>
            <p className="text-[#b9adff] text-[10px]">Latest valid hourly observation</p>
          </div>
          
          <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-5">
            <p className="text-[#93a7ab] text-[11px] mb-2">Weekly mean change</p>
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-[#e8f0ec] text-[32px] font-mono leading-none">{overview.weeklyChange.toFixed(1)}</span>
              <span className="text-[#93a7ab] text-sm">%</span>
            </div>
            <p className="text-[#f3bd75] text-[10px]">Compared with the prior seven-day mean</p>
          </div>
          
          <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-5">
            <p className="text-[#93a7ab] text-[11px] mb-2">Anomalies · latest 7 days</p>
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-[#e8f0ec] text-[32px] font-mono leading-none">{overview.anomalyCount}</span>
            </div>
            <p className="text-[#93a7ab] text-[10px]">Seasonal baseline flags</p>
          </div>
        </div>
        
        {/* The Energy Horizon Chart */}
        <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-6 mb-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-[#e8f0ec] text-sm font-medium mb-1">The energy horizon</h2>
              <p className="text-[#93a7ab] text-[11px]">
                Historical hourly mean active power. Forecasts are shown on the Forecast screen.
              </p>
            </div>
            <div className="flex items-center gap-4">
              <button className="bg-[#18252a] border border-[#29383d] px-3 py-1.5 rounded text-[#e8f0ec] text-xs">
                Hourly
              </button>
              <button className="bg-[#18252a] border border-[#29383d] px-3 py-1.5 rounded text-[#e8f0ec] text-xs flex items-center gap-2">
                <Calendar className="w-3 h-3" />
                14-Selected data period
              </button>
            </div>
          </div>
          
          <div className="flex items-center gap-6 mb-4 text-[10px]">
            <div className="flex items-center gap-2">
              <div className="w-3 h-0.5 bg-[#9cdccb]"></div>
              <span className="text-[#93a7ab]">Observed</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-0.5 bg-[#b9adff] border-t-2 border-dashed"></div>
              <span className="text-[#93a7ab]">Forecast</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-[#b9adff] opacity-20"></div>
              <span className="text-[#93a7ab]">90% prediction interval</span>
            </div>
          </div>
          
          <div className="h-[280px] -mx-2">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#29383d" vertical={false} />
                <XAxis 
                  dataKey="time" 
                  tick={{ fill: '#6b7f84', fontSize: 10 }}
                  stroke="#29383d"
                  tickLine={false}
                  interval={6}
                />
                <YAxis 
                  tick={{ fill: '#6b7f84', fontSize: 10 }}
                  stroke="#29383d"
                  tickLine={false}
                  label={{ value: 'kW', angle: 0, position: 'top', fill: '#6b7f84', fontSize: 10, offset: 10 }}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#121d21', 
                    border: '1px solid #29383d',
                    borderRadius: '0.5rem',
                    fontSize: '11px',
                    color: '#e8f0ec'
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="upper"
                  stroke="none"
                  fill="#b9adff"
                  fillOpacity={0.15}
                />
                <Area
                  type="monotone"
                  dataKey="lower"
                  stroke="none"
                  fill="#b9adff"
                  fillOpacity={0.15}
                />
                <Line 
                  type="monotone" 
                  dataKey="observed" 
                  stroke="#9cdccb" 
                  strokeWidth={2}
                  dot={false}
                />
                <Line 
                  type="monotone" 
                  dataKey="forecast" 
                  stroke="#b9adff" 
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          
          <p className="text-[#6b7f84] text-[9px] mt-4">
            Historical observations only · No prediction interval is shown on this chart.
          </p>
          <p className="text-[#6b7f84] text-[9px] text-right mt-2">48 hours / dataset time</p>
        </div>
        
        {/* Intelligence Briefing */}
        <div className="grid grid-cols-[2fr_1fr] gap-5">
          <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-[#e8f0ec] text-sm font-medium mb-1">Worth a closer look</h3>
                <p className="text-[#93a7ab] text-[11px]">
                  3 flagged hours in the last 7 days · 2 separate episodes
                </p>
              </div>
              <span className="bg-[#f3bd75] bg-opacity-20 border border-[#f3bd75] border-opacity-30 text-[#f3bd75] text-[9px] font-bold px-2 py-1 rounded uppercase">
                REVIEW SUGGESTED
              </span>
            </div>
            
            <div className="bg-[#18252a] border border-[#29383d] rounded-lg p-4">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h4 className="text-[#e8f0ec] text-sm font-medium mb-1">An elevated evening load</h4>
                  <p className="text-[#93a7ab] text-xs">
                    Selected observation window exceeded the expected range. A later shutdown is one hypothesis, not a confirmed cause.
                  </p>
                </div>
                <span className="text-[#f3bd75] text-2xl font-bold leading-none">+37.9%</span>
              </div>
              <p className="text-[#6b7f84] text-[10px] mb-2">vs historical baseline</p>
              <button className="text-[#bcf58a] text-xs font-medium flex items-center gap-1 hover:underline">
                Investigate episode →
              </button>
            </div>
          </div>
          
          <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[#e8f0ec] text-sm font-medium">Tomorrow, in context</h3>
              <span className="bg-[#b9adff] bg-opacity-20 border border-[#b9adff] border-opacity-30 text-[#b9adff] text-[9px] font-bold px-2 py-1 rounded uppercase">
                FORECAST
              </span>
            </div>
            
            <div className="mb-4">
              <h4 className="text-[#e8f0ec] text-base font-medium mb-2">A softer evening peak is expected.</h4>
              <p className="text-[#93a7ab] text-xs mb-1">Forecast peak time</p>
              <div className="flex items-baseline gap-2">
                <span className="text-[#e8f0ec] text-2xl font-mono">286</span>
                <span className="text-[#93a7ab] text-sm">kW</span>
              </div>
            </div>
            
            <p className="text-[#93a7ab] text-[10px] leading-relaxed">
              80% interval at peak: 244-328 kW. Wider ranges reflect greater uncertainty, not higher consumption.
            </p>
          </div>
        </div>
        
        {/* Footer */}
        <div className="mt-8 pt-4 border-t border-[#29383d] flex items-center justify-between text-[10px] text-[#6b7f84]">
          <span>UCI-HOUSEHOLD / ELECTRICITY / HOURLY kW / dataset time</span>
          <span>Demo data · Estimates are not operational guarantees</span>
        </div>
      </div>
    </div>
  );
}
