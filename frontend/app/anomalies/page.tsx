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
        } else {
          setAnomalyData(getDemoAnomalyData());
        }
      } catch {
        setError('Failed to load anomaly data');
        setAnomalyData(getDemoAnomalyData());
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
  const chartData = Array.from({ length: 24 }, (_, i) => {
    const seed = i * 7.3; // Deterministic seed based on hour
    const pseudoRandom = Math.sin(seed) * 10000 - Math.floor(Math.sin(seed) * 10000);
    const observedPower = selected?.observedPower ?? 200;
    const expectedPower = selected?.expectedPower ?? 220;
    return {
      hour: i,
      observed: i === 18 ? observedPower : expectedPower + pseudoRandom * 20 - 10,
      baseline: expectedPower,
      lowerRange: expectedPower * 0.85,
      upperRange: expectedPower * 1.15,
    };
  });
  
  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <header className="border-b border-[#29383d] px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <span className="text-[#93a7ab] text-sm">Workspace / Anomalies</span>
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
            <span className="text-[#e8f0ec] text-sm">08-14 Oct 2026</span>
            <span className="text-[#6b7f84] text-xs">UTC</span>
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
                      <span className="text-[#93a7ab] text-[10px]">14 OCT 2026</span>
                      <p className="text-[#e8f0ec] text-sm font-medium mt-0.5">{event.reason.split('.')[0]}</p>
                    </div>
                    <span className={`text-2xl font-bold ${
                      event.deviation > 0 ? 'text-[#f3bd75]' : 'text-[#9cdccb]'
                    }`}>
                      {event.deviation > 0 ? '+' : ''}{(event.deviation ?? 0).toFixed(1)}%
                    </span>
                  </div>
                  
                  <p className="text-[#93a7ab] text-xs mb-2">
                    {new Date(event.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })} UTC · 
                    two-hour observation · Peak deviation of {(event.observedPower ?? 0).toFixed(0)} kWh above baseline.
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
                An observation outside its historical 90% range with an absolute robust residual score above 3.0.
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
                  14 Oct 2026 · 18:00-20:00 UTC · two one-hour observations
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
                      <span className="text-[#93a7ab]">Historical 90% range</span>
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
                  
                  <div className="grid grid-cols-4 gap-4 mt-4 pt-4 border-t border-[#29383d]">
                    <div>
                      <p className="text-[#6b7f84] text-[10px] mb-1">Observed · 18:00</p>
                      <p className="text-[#e8f0ec] text-lg font-mono">{(selected.observedPower ?? 0).toFixed(0)} kWh</p>
                    </div>
                    <div>
                      <p className="text-[#6b7f84] text-[10px] mb-1">Historical baseline</p>
                      <p className="text-[#93a7ab] text-lg font-mono">{(selected.expectedPower ?? 0).toFixed(0)} kWh</p>
                    </div>
                    <div>
                      <p className="text-[#6b7f84] text-[10px] mb-1">Historical 90% range</p>
                      <p className="text-[#93a7ab] text-lg font-mono">
                        {((selected.expectedPower ?? 0) * 0.85).toFixed(0)}–{((selected.expectedPower ?? 0) * 1.15).toFixed(0)} kWh
                      </p>
                    </div>
                    <div>
                      <p className="text-[#6b7f84] text-[10px] mb-1">Robust residual score</p>
                      <p className="text-[#f3bd75] text-lg font-mono">3.8</p>
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
          <span>NB-01 / ELECTRICITY / HOURLY kWh / UTC</span>
          <span>Demo data · Estimates are not operational guarantees</span>
        </div>
      </div>
    </div>
  );
}
