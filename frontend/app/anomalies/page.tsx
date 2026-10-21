/**
 * Anomaly Investigation - Figma Design Implementation
 * 
 * Displays detected anomalous consumption patterns with review queue.
 * Uses real API data when backend is available, falls back to demo data.
 */

'use client';

import { LoadingState } from '@/components/ui/LoadingSpinner';
import { ErrorState } from '@/components/ui/ErrorState';
import { getDemoAnomalyData } from '@/lib/demoData';
import { demoModeEnabled } from '@/lib/utils';
import { DemoDataBanner } from '@/components/ui/DemoDataBanner';
import { fetchAnomalies } from '@/lib/api';
import { AnomalyData } from '@/lib/types';
import { Calendar, Info } from 'lucide-react';
import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

export default function AnomaliesPage() {
  const [anomalyData, setAnomalyData] = useState<AnomalyData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAnomaly, setSelectedAnomaly] = useState<number>(0);
  
  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      
      try {
        const apiData = await fetchAnomalies();
        
        if (apiData) {
          setAnomalyData(apiData);
        } else if (demoModeEnabled()) {
          setAnomalyData(getDemoAnomalyData());
        } else {
          setError('Validation-calibrated anomaly data is unavailable. Run scripts/train_models.py, or add ?demo=1 for synthetic preview data.');
        }
      } catch {
        if (demoModeEnabled()) setAnomalyData(getDemoAnomalyData());
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
        <LoadingState message="Loading anomaly data..." />
      </div>
    );
  }
  
  if (error || !anomalyData) {
    return (
      <div className="p-8">
        <ErrorState
          message="Failed to Load Data"
          detail={error || "Could not load anomaly data"}
          retry={() => window.location.reload()}
        />
      </div>
    );
  }
  
  const selected = anomalyData.events[selectedAnomaly];
  
  // Deterministic mock chart data for visualization
  const chartData = anomalyData.events.filter(event => event.id === selected?.id).map(event => ({
    hour: new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    observed: event.observedPower,
    baseline: event.expectedPower,
  }));

  if (!anomalyData.isDemo) {
    return <div className="min-h-screen p-6 md:p-10 text-[#e8f0ec]"><header className="mb-8 border-b border-[#29383d] pb-5"><p className="text-sm text-[#93a7ab]">GridPulse / Anomalies</p><h1 className="mt-2 text-3xl">Anomaly investigation</h1><p className="mt-2 text-sm text-[#93a7ab]">{anomalyData.detectionMethod} · {anomalyData.thresholdInfo}</p></header>
      <section className="mb-5 grid gap-4 sm:grid-cols-3">{(['high','medium','low'] as const).map(level=><div key={level} className="rounded-lg border border-[#29383d] bg-[#121d21] p-5"><p className="text-sm capitalize text-[#93a7ab]">{level} severity</p><p className="mt-2 text-2xl font-mono">{anomalyData.severityCounts[level]}</p></div>)}</section>
      <section className="overflow-x-auto rounded-lg border border-[#29383d] bg-[#121d21] p-5"><h2 className="mb-4 font-medium">Observed events · {new Date(anomalyData.period.start).toLocaleDateString()} to {new Date(anomalyData.period.end).toLocaleDateString()}</h2><table className="w-full text-left text-sm"><thead className="text-[#93a7ab]"><tr><th className="p-2">Timestamp</th><th className="p-2">Observed (kW)</th><th className="p-2">Expected (kW)</th><th className="p-2">Deviation</th><th className="p-2">Severity</th><th className="p-2">Reason</th></tr></thead><tbody>{anomalyData.events.map(event=><tr key={event.id} className="border-t border-[#29383d]"><td className="p-2">{new Date(event.timestamp).toLocaleString()}</td><td className="p-2">{event.observedPower.toFixed(3)}</td><td className="p-2">{event.expectedPower.toFixed(3)}</td><td className="p-2">{event.deviation == null ? 'Unavailable' : `${event.deviation.toFixed(1)}%`}</td><td className="p-2 capitalize">{event.severity}</td><td className="p-2">{event.reason}</td></tr>)}</tbody></table>{anomalyData.events.length===0&&<p className="py-6 text-sm text-[#93a7ab]">No anomalies were detected in this observation window.</p>}</section>
      <p className="mt-5 text-xs text-[#6b7f84]">A statistical flag suggests review; it does not establish a fault or cause.</p></div>;
  }
  
  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <header className="border-b border-[#29383d] px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <span className="text-[#93a7ab] text-sm">Workspace / Anomalies</span>
        </div>
        <div className="flex items-center gap-4 text-[#93a7ab] text-xs">
          <span>WINDOW · {new Date(anomalyData.period.start).toLocaleDateString()} – {new Date(anomalyData.period.end).toLocaleDateString()}</span>
          <button className="p-1.5 hover:bg-[#1a2b30] rounded"><Calendar className="w-4 h-4" /></button>
        </div>
      </header>
      {anomalyData.isDemo && <div className="px-8 pt-5"><DemoDataBanner /></div>}
      
      {/* Main Content */}
      <div className="flex-1 overflow-auto px-8 py-6">
        {/* Page Title */}
        <div className="mb-6">
          <p className="text-[#bcf58a] text-[10px] font-mono mb-2">03 / DEVIATION ANALYSIS</p>
          <div className="flex items-center justify-between">
            <h1 className="text-[#e8f0ec] text-[34px] font-medium">Anomaly investigation</h1>
            <button className="bg-[#18252a] border border-[#29383d] px-4 py-2 rounded text-[#e8f0ec] text-sm hover:bg-[#1a2b30]">
              Export investigation
            </button>
          </div>
          <p className="text-[#93a7ab] text-sm mt-2">
            Separate unusual measurements from expected variation. Investigate signals without assuming causes.
          </p>
        </div>
        
        {/* Period Selector */}
        <div className="bg-[#121d21] border border-[#29383d] rounded-lg px-4 py-3 mb-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-[#93a7ab]" />
            <span className="text-[#e8f0ec] text-sm">08-Selected data period</span>
            <span className="text-[#6b7f84] text-xs">dataset time</span>
          </div>
          <div className="flex items-center gap-4 text-xs text-[#93a7ab]">
            <span>3 flagged hours · 2 episodes · 0 reviewed</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="bg-[#bcf58a] text-[#0c1215] text-[9px] font-bold px-2 py-0.5 rounded uppercase">DEMO</span>
            <span className="bg-[#f3bd75] bg-opacity-20 border border-[#f3bd75] border-opacity-30 text-[#f3bd75] text-[9px] font-bold px-2 py-1 rounded uppercase">
              ROBUST BASELINE
            </span>
          </div>
        </div>
        
        {/* Main Grid */}
        <div className="grid grid-cols-[420px_1fr] gap-5">
          {/* Review Queue */}
          <div>
            <h2 className="text-[#e8f0ec] text-sm font-medium mb-3 flex items-center gap-2">
              Review queue
              <button className="text-[#93a7ab] text-xs hover:text-[#e8f0ec]">
                Newest first ▼
              </button>
            </h2>
            
            <div className="space-y-3">
              {anomalyData.events.slice(0, 2).map((event, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedAnomaly(idx)}
                  className={`w-full text-left bg-[#121d21] border rounded-lg p-4 transition-colors ${
                    selectedAnomaly === idx
                      ? 'border-[#bcf58a] bg-[#1a2b30]'
                      : 'border-[#29383d] hover:border-[#3a4d54]'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <span className="text-[#93a7ab] text-[10px]">{new Date(event.timestamp).toLocaleDateString()}</span>
                      <p className="text-[#e8f0ec] text-sm font-medium mt-0.5">{event.reason.split('.')[0]}</p>
                    </div>
                    <span className={`text-2xl font-bold ${
                      (event.deviation ?? 0) > 0 ? 'text-[#f3bd75]' : 'text-[#9cdccb]'
                    }`}>
                      {event.deviation == null ? 'N/A' : `${event.deviation > 0 ? '+' : ''}${event.deviation.toFixed(1)}%`}
                    </span>
                  </div>
                  
                  <p className="text-[#93a7ab] text-xs mb-2">
                    {new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} dataset time · {event.observedPower.toFixed(3)} kW observed.
                  </p>
                  
                  <div className="flex items-center gap-2">
                    <span className="bg-[#f3bd75] bg-opacity-20 text-[#f3bd75] text-[9px] font-bold px-1.5 py-0.5 rounded">
                      Needs review
                    </span>
                  </div>
                </button>
              ))}
            </div>
            
            {/* What is an anomaly */}
            <div className="mt-6 bg-[#121d21] border border-[#29383d] rounded-lg p-4">
              <div className="flex items-start gap-2 mb-2">
                <Info className="w-4 h-4 text-[#93a7ab] mt-0.5 shrink-0" />
                <h3 className="text-[#e8f0ec] text-sm font-medium">What is an anomaly?</h3>
              </div>
              <p className="text-[#93a7ab] text-xs leading-relaxed mb-3">
                Events are flagged when the absolute deviation from the 24-hour seasonal baseline crosses a threshold calibrated on validation residuals.
              </p>
              <p className="text-[#6b7f84] text-[10px] leading-relaxed">
                A flag is a prompt to investigate, not proof of equipment failure or waste.
              </p>
            </div>
          </div>
          
          {/* Detail View */}
          <div>
            {selected && (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-[#e8f0ec] text-lg font-medium">{selected.reason.split('.')[0]}</h2>
                  <button className="text-[#e8f0ec] text-xs hover:underline flex items-center gap-1">
                    ✓ Mark reviewed
                  </button>
                </div>
                
                <p className="text-[#93a7ab] text-sm mb-6">
                  {new Date(selected.timestamp).toLocaleString()} dataset time
                </p>
                
                {/* Chart */}
                <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-6 mb-5">
                  <div className="flex items-center gap-6 mb-4 text-[10px]">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-0.5 bg-[#9cdccb]"></div>
                      <span className="text-[#93a7ab]">Observed</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-0.5 bg-[#6b7f84] border-t-2 border-dashed"></div>
                      <span className="text-[#93a7ab]">Historical baseline</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-[#6b7f84] opacity-20"></div>
                      <span className="text-[#93a7ab]">Severity</span>
                    </div>
                  </div>
                  
                  <div className="h-[240px] -mx-2">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#29383d" vertical={false} />
                        <XAxis 
                          dataKey="hour" 
                          tick={{ fill: '#6b7f84', fontSize: 10 }}
                          stroke="#29383d"
                          tickLine={false}
                          tickFormatter={(v) => `${v.toString().padStart(2, '0')}:00`}
                          interval={3}
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
                        <Line 
                          type="monotone" 
                          dataKey="upperRange" 
                          stroke="none"
                          fill="#6b7f84"
                          fillOpacity={0.1}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="lowerRange" 
                          stroke="none"
                          fill="#6b7f84"
                          fillOpacity={0.1}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="baseline" 
                          stroke="#6b7f84" 
                          strokeWidth={1.5}
                          strokeDasharray="5 5"
                          dot={false}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="observed" 
                          stroke="#9cdccb" 
                          strokeWidth={2}
                          dot={false}
                        />
                        <ReferenceLine x={18} stroke="#f3bd75" strokeWidth={1} label="" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                  
                    <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-[#29383d]">
                    <div>
                      <p className="text-[#6b7f84] text-[10px] mb-1">Observed power</p>
                      <p className="text-[#e8f0ec] text-lg font-mono">{selected.observedPower.toFixed(3)} kW</p>
                    </div>
                    <div>
                      <p className="text-[#6b7f84] text-[10px] mb-1">Historical baseline</p>
                      <p className="text-[#93a7ab] text-lg font-mono">{selected.expectedPower.toFixed(3)} kW</p>
                    </div>
                    <div>
                      <p className="text-[#6b7f84] text-[10px] mb-1">Severity</p>
                      <p className="text-[#f3bd75] text-lg font-mono">{selected.severity}</p>
                    </div>
                    <div>
                    </div>
                  </div>
                </div>
                
                {/* Contributing Signals & Hypothesis */}
                <div className="grid grid-cols-2 gap-5">
                  <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-5">
                    <h3 className="text-[#e8f0ec] text-sm font-medium mb-3">Contributing signals</h3>
                    <p className="text-[#93a7ab] text-xs mb-4">Context, not causal attribution</p>
                    
                    <div className="space-y-3">
                      <div>
                        <div className="flex items-start gap-2 mb-1">
                          <span className="bg-[#2a3d44] text-[#e8f0ec] text-[10px] font-bold px-1.5 py-0.5 rounded">01</span>
                          <div className="flex-1">
                            <p className="text-[#e8f0ec] text-xs font-medium">Persistence</p>
                            <p className="text-[#93a7ab] text-[10px] mt-0.5">
                              Load stayed above its expected range for two hours.
                            </p>
                          </div>
                        </div>
                      </div>
                      
                      <div>
                        <div className="flex items-start gap-2 mb-1">
                          <span className="bg-[#2a3d44] text-[#e8f0ec] text-[10px] font-bold px-1.5 py-0.5 rounded">02</span>
                          <div className="flex-1">
                            <p className="text-[#e8f0ec] text-xs font-medium">Timing</p>
                            <p className="text-[#93a7ab] text-[10px] mt-0.5">
                              Deviation followed the usual late-afternoon ramp.
                            </p>
                          </div>
                        </div>
                      </div>
                      
                      <div>
                        <div className="flex items-start gap-2 mb-1">
                          <span className="bg-[#2a3d44] text-[#e8f0ec] text-[10px] font-bold px-1.5 py-0.5 rounded">03</span>
                          <div className="flex-1">
                            <p className="text-[#e8f0ec] text-xs font-medium">Data quality</p>
                            <p className="text-[#93a7ab] text-[10px] mt-0.5">
                              Both records passed validation; no nearby missing hours.
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-5">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-[#e8f0ec] text-sm font-medium">Working hypothesis</h3>
                      <span className="bg-[#f3bd75] bg-opacity-20 text-[#f3bd75] text-[9px] font-bold px-1.5 py-0.5 rounded uppercase">
                        UNCONFIRMED
                      </span>
                    </div>
                    
                    <p className="text-[#e8f0ec] text-base font-medium mb-3">
                      Activity may have continued beyond the normal shutdown.
                    </p>
                    
                    <p className="text-[#93a7ab] text-xs leading-relaxed mb-4">
                      A schedule change or additional equipment load could explain the pattern. 
                      Occupancy and equipment telemetry are not available.
                    </p>
                    
                    <button className="text-[#bcf58a] text-xs font-medium flex items-center gap-1 hover:underline">
                      → Check the operating schedule
                    </button>
                  </div>
                </div>
              </div>
            )}
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
