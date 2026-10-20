/**
 * The next 24 hours - Figma Design Implementation
 * 
 * Displays 24-hour energy consumption forecast with detailed hourly outlook.
 * Uses real API data when backend is available, falls back to demo data.
 */

'use client';

import { LoadingState } from '@/components/ui/LoadingSpinner';
import { ErrorState } from '@/components/ui/ErrorState';
import { getDemoForecastData } from '@/lib/demoData';
import { fetchForecast } from '@/lib/api';
import { ForecastData } from '@/lib/types';
import { ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area } from 'recharts';
import { Calendar, Info } from 'lucide-react';
import { useState, useEffect } from 'react';

export default function ForecastingPage() {
  const [forecastData, setForecastData] = useState<ForecastData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      
      try {
        const apiData = await fetchForecast();
        
        if (apiData) {
          setForecastData(apiData);
        } else {
          setForecastData(getDemoForecastData());
        }
      } catch {
        setError('Failed to load forecast data');
        setForecastData(getDemoForecastData());
      } finally {
        setLoading(false);
      }
    }
    
    loadData();
  }, []);
  
  if (loading) {
    return (
      <div className="p-8">
        <LoadingState message="Loading forecast data..." />
      </div>
    );
  }
  
  if (error || !forecastData) {
    return (
      <div className="p-8">
        <ErrorState
          message="Failed to Load Data"
          detail={error || "Could not load forecast data"}
          retry={() => window.location.reload()}
        />
      </div>
    );
  }
  
  const chartData = [
    ...forecastData.historical.map(p => ({
      time: new Date(p.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
      observed: p.actual,
    })),
    ...forecastData.forecast.map(p => ({
      time: new Date(p.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
      forecast: p.predicted,
      lower: p.lower,
      upper: p.upper,
    }))
  ];
  
  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <header className="border-b border-[#29383d] px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <span className="text-[#93a7ab] text-sm">Workspace / Forecast</span>
        </div>
        <div className="flex items-center gap-4 text-[#93a7ab] text-xs">
          <span>SNAPSHOT 15 OCT 2026 · 00:10 UTC</span>
          <button className="p-1.5 hover:bg-[#1a2b30] rounded"><Calendar className="w-4 h-4" /></button>
        </div>
      </header>
      
      {/* Main Content */}
      <div className="flex-1 overflow-auto px-8 py-6">
        {/* Page Title */}
        <div className="mb-6">
          <p className="text-[#bcf58a] text-[10px] font-mono mb-2">02 / PREDICTIVE INTELLIGENCE</p>
          <div className="flex items-center justify-between">
            <h1 className="text-[#e8f0ec] text-[34px] font-medium">The next 24 hours</h1>
            <button className="bg-[#18252a] border border-[#29383d] px-4 py-2 rounded text-[#e8f0ec] text-sm hover:bg-[#1a2b30]">
              Export forecast
            </button>
          </div>
          <p className="text-[#93a7ab] text-sm mt-2">
            A consumption outlook with uncertainty in view. Predictions, not promises.
          </p>
        </div>
        
        {/* Model Selection Controls */}
        <div className="flex items-center gap-3 mb-6">
          <button className="bg-[#18252a] border border-[#29383d] px-3 py-2 rounded text-[#e8f0ec] text-xs flex items-center gap-2">
            LightGBM v2.4
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <button className="bg-[#18252a] border border-[#29383d] px-3 py-2 rounded text-[#e8f0ec] text-xs flex items-center gap-2">
            <Calendar className="w-3 h-3" />
            15 Oct 2026 · 24 hours
          </button>
          <button className="bg-[#18252a] border border-[#29383d] px-3 py-2 rounded text-[#e8f0ec] text-xs">
            90% interval
          </button>
          <div className="ml-auto flex items-center gap-2">
            <span className="bg-[#bcf58a] text-[#0c1215] text-[9px] font-bold px-2 py-0.5 rounded uppercase">DEMO</span>
            <span className="bg-[#b9adff] bg-opacity-20 border border-[#b9adff] border-opacity-30 text-[#b9adff] text-[9px] font-bold px-2 py-1 rounded uppercase">
              FORECAST READY
            </span>
          </div>
        </div>
        
        {/* Summary KPIs */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-5">
            <p className="text-[#93a7ab] text-[11px] mb-2">Predicted daily consumption</p>
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-[#e8f0ec] text-[32px] font-mono leading-none">4,796</span>
              <span className="text-[#93a7ab] text-sm">kWh</span>
            </div>
            <p className="text-[#93a7ab] text-[10px]">Sum of 24 hourly point predictions</p>
          </div>
          
          <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-5">
            <p className="text-[#93a7ab] text-[11px] mb-2">Change vs 14 October</p>
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-[#e8f0ec] text-[32px] font-mono leading-none">−4.4</span>
              <span className="text-[#93a7ab] text-sm">%</span>
            </div>
            <p className="text-[#93a7ab] text-[10px]">220 kWh below the observed day</p>
          </div>
          
          <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-5">
            <p className="text-[#93a7ab] text-[11px] mb-2">Predicted peak · 18:00</p>
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-[#e8f0ec] text-[32px] font-mono leading-none">286</span>
              <span className="text-[#93a7ab] text-sm">kWh</span>
            </div>
            <p className="text-[#93a7ab] text-[10px]">90% interval: 244-328 kWh</p>
          </div>
          
          <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-5">
            <p className="text-[#93a7ab] text-[11px] mb-2">Hold-out mean absolute error</p>
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-[#e8f0ec] text-[32px] font-mono leading-none">12.8</span>
              <span className="text-[#93a7ab] text-sm">kWh</span>
            </div>
            <p className="text-[#93a7ab] text-[10px]">01-14 Oct · hourly error, 24h horizon</p>
          </div>
        </div>
        
        {/* Forecast Chart */}
        <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-6 mb-6">
          <div className="mb-4">
            <h2 className="text-[#e8f0ec] text-sm font-medium mb-1">From measured to modeled</h2>
            <p className="text-[#93a7ab] text-[11px]">
              12 hours of observed context → 24 hourly forecasts for 15 October
            </p>
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
                  interval={4}
                />
                <YAxis 
                  tick={{ fill: '#6b7f84', fontSize: 10 }}
                  stroke="#29383d"
                  tickLine={false}
                  label={{ value: 'kWh', angle: 0, position: 'top', fill: '#6b7f84', fontSize: 10, offset: 10 }}
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
          
          <div className="flex items-center gap-2 mt-4 text-[#93a7ab] text-[10px]">
            <Info className="w-3 h-3" />
            <span>The shaded range is a pointwise 90% prediction interval. It is not an interval for the daily total.</span>
          </div>
          
          <p className="text-[#6b7f84] text-[9px] text-right mt-2">ISSUED 15 OCT · 00:08 UTC</p>
        </div>
        
        {/* Hourly Outlook & Model Details */}
        <div className="grid grid-cols-[2fr_1fr] gap-5">
          <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[#e8f0ec] text-sm font-medium">Hourly outlook</h3>
              <button className="text-[#bcf58a] text-xs font-medium hover:underline">
                View all 24 hours →
              </button>
            </div>
            <p className="text-[#93a7ab] text-[11px] mb-4">
              Selected checkpoints · timestamps mark the start of each one-hour interval
            </p>
            
            <div className="space-y-0">
              <div className="grid grid-cols-[100px_1fr_1fr_1fr] gap-4 py-2 text-[10px] text-[#6b7f84] border-b border-[#29383d]">
                <div>Hour · UTC</div>
                <div className="text-right">Forecast</div>
                <div className="text-right">Lower 90%</div>
                <div className="text-right">Upper 90%</div>
              </div>
              
              {forecastData.forecast.slice(0, 6).map((point, idx) => (
                <div 
                  key={idx} 
                  className={`grid grid-cols-[100px_1fr_1fr_1fr] gap-4 py-2.5 text-xs ${
                    idx === 4 ? 'bg-[#2a3d44] bg-opacity-30' : ''
                  } ${idx !== 5 ? 'border-b border-[#29383d]' : ''}`}
                >
                  <div className="text-[#e8f0ec] font-mono">
                    {new Date(point.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                    {idx === 4 && ' · peak'}
                  </div>
                  <div className="text-[#e8f0ec] text-right font-mono">{(point.predicted ?? 0).toFixed(0)} kWh</div>
                  <div className="text-[#93a7ab] text-right font-mono">{point.lower?.toFixed(0) || 'N/A'} kWh</div>
                  <div className="text-[#93a7ab] text-right font-mono">{point.upper?.toFixed(0) || 'N/A'} kWh</div>
                </div>
              ))}
            </div>
          </div>
          
          <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[#e8f0ec] text-sm font-medium">Behind this forecast</h3>
              <span className="bg-[#bcf58a] bg-opacity-20 border border-[#bcf58a] border-opacity-30 text-[#bcf58a] text-[9px] font-bold px-2 py-1 rounded uppercase">
                SELECTED MODEL
              </span>
            </div>
            
            <div className="mb-6">
              <h4 className="text-[#e8f0ec] text-lg font-medium mb-2">{forecastData.modelName}</h4>
              <p className="text-[#6b7f84] text-[10px] mb-3">v2.4 / refit 14 Oct</p>
              <p className="text-[#93a7ab] text-xs leading-relaxed mb-4">
                Uses recent consumption, hour of day, weekday and lagged demand. No weather or occupancy inputs.
              </p>
              
              <div className="flex items-center justify-between py-2 border-b border-[#29383d]">
                <span className="text-[#93a7ab] text-[10px]">90% interval coverage on holdout</span>
                <span className="text-[#e8f0ec] text-sm font-mono">88.7%</span>
              </div>
            </div>
            
            <p className="text-[#6b7f84] text-[10px] leading-relaxed">
              Plan for the range, not only the center line. Unusual operational changes can fall outside this outlook.
            </p>
          </div>
        </div>
        
        {/* Footer */}
        <div className="mt-8 pt-4 border-t border-[#29383d] flex items-center justify-between text-[10px] text-[#6b7f84]">
          <span>NB-01 / ELECTRICITY / HOURLY kWh / UTC</span>
          <span>Demo data · Estimates are not operational guarantees</span>
        </div>
      </div>
    </div>
  );
}
