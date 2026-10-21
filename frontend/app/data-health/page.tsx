/**
 * Trust starts at the source - Figma Design Implementation
 * 
 * Display dataset quality metrics, coverage, and validation status.
 * Uses real API data when backend is available, falls back to demo data.
 */

'use client';

import { LoadingState } from '@/components/ui/LoadingSpinner';
import { ErrorState } from '@/components/ui/ErrorState';
import { getDemoDataHealthData } from '@/lib/demoData';
import { demoModeEnabled } from '@/lib/utils';
import { DemoDataBanner } from '@/components/ui/DemoDataBanner';
import { fetchDataHealth } from '@/lib/api';
import { DataHealthData } from '@/lib/types';
import { Calendar, CheckCircle2, AlertTriangle } from 'lucide-react';
import { useState, useEffect } from 'react';

export default function DataHealthPage() {
  const [healthData, setHealthData] = useState<DataHealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      
      try {
        const apiData = await fetchDataHealth();
        
        if (apiData) {
          setHealthData(apiData);
        } else if (demoModeEnabled()) {
          setHealthData(getDemoDataHealthData());
        } else {
          setError('Validated dataset health is unavailable. Run scripts/train_models.py, or add ?demo=1 for synthetic preview data.');
        }
      } catch {
        if (demoModeEnabled()) setHealthData(getDemoDataHealthData());
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
        <LoadingState message="Loading data health metrics..." />
      </div>
    );
  }
  
  if (error || !healthData) {
    return (
      <div className="p-8">
        <ErrorState
          message="Failed to Load Data"
          detail={error || "Could not load data health metrics"}
          retry={() => window.location.reload()}
        />
      </div>
    );
  }

  if (!healthData.isDemo) {
    const stats = healthData.statistics;
    const quality = healthData.quality;
    return <div className="min-h-screen p-6 md:p-10 text-[#e8f0ec]"><header className="mb-8 border-b border-[#29383d] pb-5"><p className="text-sm text-[#93a7ab]">GridPulse / Data trust</p><h1 className="mt-2 text-3xl">Dataset quality</h1><p className="mt-2 text-sm text-[#93a7ab]">{healthData.datasetName} · {healthData.sourceFile}</p></header>
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{[['Raw source rows',quality.totalRows.toLocaleString()],['Missing or invalid target readings',`${quality.missingRows.toLocaleString()} (${quality.missingPercentage}%)`],['Eligible hourly observations',`${quality.coverage.eligibleHours.toLocaleString()} / ${quality.coverage.totalHours.toLocaleString()}`],['Hourly coverage',`${quality.coverage.coveragePercentage}%`]].map(([label,value])=><article key={label} className="rounded-lg border border-[#29383d] bg-[#121d21] p-5"><p className="text-sm text-[#93a7ab]">{label}</p><p className="mt-3 text-2xl font-mono">{value}</p></article>)}</section>
      <section className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{[['Duplicate rows excluded',quality.duplicateRowsExcluded],['Timestamp parse failures',quality.timestampParseFailures],['Missing minute timestamps',quality.missingMinuteTimestamps],['Hours excluded by coverage',quality.excludedHourlyIntervals]].map(([label,value])=><article key={label} className="rounded-lg border border-[#29383d] bg-[#121d21] p-4"><p className="text-xs text-[#93a7ab]">{label}</p><p className="mt-2 text-xl font-mono">{Number(value).toLocaleString()}</p></article>)}</section>
      <section className="mt-6 grid gap-5 lg:grid-cols-2"><article className="rounded-lg border border-[#29383d] bg-[#121d21] p-5"><h2 className="mb-4 font-medium">Hourly mean active power by hour (kW)</h2><div className="space-y-2">{healthData.hourlyDistribution.map(item=><div key={item.hour} className="flex justify-between border-b border-[#29383d] py-2 text-sm"><span>{String(item.hour).padStart(2,'0')}:00 · {item.sampleCount.toLocaleString()} readings</span><span>{item.avgPower.toFixed(3)} kW</span></div>)}</div></article><article className="rounded-lg border border-[#29383d] bg-[#121d21] p-5"><h2 className="mb-4 font-medium">Validated target statistics (kW)</h2><dl className="space-y-3 text-sm">{Object.entries({Minimum:stats.min,Median:stats.median,Mean:stats.mean,Maximum:stats.max,'Standard deviation':stats.std}).map(([label,value])=><div key={label} className="flex justify-between"><dt className="text-[#93a7ab]">{label}</dt><dd className="font-mono">{value.toFixed(4)}</dd></div>)}</dl><p className="mt-5 text-xs text-[#93a7ab]">Source window: {new Date(quality.dateRange.start).toLocaleString()} to {new Date(quality.dateRange.end).toLocaleString()}</p></article></section>
      <section className="mt-6 rounded-lg border border-[#29383d] bg-[#121d21] p-5"><h2 className="mb-3 font-medium">Validation: {quality.validationStatus}</h2>{quality.warnings.length ? <ul className="list-disc space-y-1 pl-5 text-sm text-[#f3bd75]">{quality.warnings.map((warning,index)=><li key={`${index}-${warning}`}>{warning}</li>)}</ul> : <p className="text-sm text-[#93a7ab]">No validation warnings were recorded.</p>}</section>
      <p className="mt-5 text-xs text-[#6b7f84]">Power is measured in kW. This household dataset is historical and is not live telemetry.</p></div>;
  }
  
  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <header className="border-b border-[#29383d] px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <span className="text-[#93a7ab] text-sm">Workspace / Data trust</span>
        </div>
        <div className="flex items-center gap-4 text-[#93a7ab] text-xs">
          <span>VALIDATION · {healthData.quality.dateRange.start.slice(0, 10)} – {healthData.quality.dateRange.end.slice(0, 10)}</span>
          <button className="p-1.5 hover:bg-[#1a2b30] rounded"><Calendar className="w-4 h-4" /></button>
        </div>
      </header>
      {healthData.isDemo && <div className="px-8 pt-5"><DemoDataBanner /></div>}
      
      {/* Main Content */}
      <div className="flex-1 overflow-auto px-8 py-6">
        {/* Page Title */}
        <div className="mb-6">
          <p className="text-[#bcf58a] text-[10px] font-mono mb-2">05 / DATA FOUNDATION</p>
          <div className="flex items-center justify-between">
            <h1 className="text-[#e8f0ec] text-[34px] font-medium">Trust starts at the source.</h1>
            <button className="bg-[#18252a] border border-[#29383d] px-4 py-2 rounded text-[#e8f0ec] text-sm hover:bg-[#1a2b30]">
              Export dataset
            </button>
          </div>
          <p className="text-[#93a7ab] text-sm mt-2">
            Inspect the dataset, understand its gaps, and trace every prediction back to validated observations.
          </p>
        </div>
        
        {/* Dataset Header */}
        <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-5 mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-[#2a3d44] p-2 rounded">
              <svg className="w-5 h-5 text-[#bcf58a]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
              </svg>
            </div>
            <div>
              <h2 className="text-[#e8f0ec] text-base font-medium">UCI household electricity observations</h2>
              <p className="text-[#93a7ab] text-xs">UCI-HOUSEHOLD / household_power_consumption.txt / v1.0</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="bg-[#bcf58a] text-[#0c1215] text-[9px] font-bold px-2 py-0.5 rounded uppercase">DEMO DATA</span>
            <span className="bg-[#f3bd75] bg-opacity-20 border border-[#f3bd75] border-opacity-30 text-[#f3bd75] text-[9px] font-bold px-2 py-1 rounded uppercase">
              VALIDATED WITH GAPS
            </span>
          </div>
        </div>
        
        {/* Quick Stats */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-5">
            <p className="text-[#93a7ab] text-[11px] mb-2">Raw completeness</p>
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-[#e8f0ec] text-[32px] font-mono leading-none">99.74</span>
              <span className="text-[#93a7ab] text-sm">%</span>
            </div>
            <p className="text-[#93a7ab] text-[10px]">6,670 present / 6,688 expected</p>
          </div>
          
          <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-5">
            <p className="text-[#93a7ab] text-[11px] mb-2">Missing hourly records</p>
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-[#e8f0ec] text-[32px] font-mono leading-none">18</span>
              <span className="text-[#93a7ab] text-sm">hours</span>
            </div>
            <p className="text-[#93a7ab] text-[10px]">12 filled for features · 6 excluded</p>
          </div>
          
          <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-5">
            <p className="text-[#93a7ab] text-[11px] mb-2">Ingestion lag</p>
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-[#e8f0ec] text-[32px] font-mono leading-none">7</span>
              <span className="text-[#93a7ab] text-sm">min</span>
            </div>
            <p className="text-[#93a7ab] text-[10px]">Within the 15-minute freshness target</p>
          </div>
          
          <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-5">
            <p className="text-[#93a7ab] text-[11px] mb-2">Historical coverage</p>
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-[#e8f0ec] text-[32px] font-mono leading-none">287</span>
              <span className="text-[#93a7ab] text-sm">days</span>
            </div>
            <p className="text-[#93a7ab] text-[10px]">01 Jan–Selected data period · dataset time</p>
          </div>
        </div>
        
        {/* Every Hour Accounted For */}
        <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-6 mb-6">
          <div className="mb-4">
            <h3 className="text-[#e8f0ec] text-sm font-medium mb-1">Every hour accounted for</h3>
            <p className="text-[#93a7ab] text-xs">
              Raw record availability · 15 Sep-Selected data period · each cell is one hour
            </p>
          </div>
          
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-4 text-[10px]">
              <div className="flex items-center gap-2">
                <div className="w-3 h-2 bg-[#9cdccb]"></div>
                <span className="text-[#93a7ab]">Present</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-2 bg-[#f3bd75]"></div>
                <span className="text-[#93a7ab]">Missing in source</span>
              </div>
            </div>
            <button className="text-[#e8f0ec] text-xs">Last 30 days</button>
          </div>
          
          {/* Heatmap Grid */}
          <div className="space-y-1 mb-4">
            {Array.from({ length: 24 }, (_, hour) => (
              <div key={hour} className="flex gap-1">
                <div className="w-8 text-[10px] text-[#6b7f84] text-right pt-0.5">{hour.toString().padStart(2, '0')}</div>
                {Array.from({ length: 30 }, (_, day) => (
                  <div
                    key={day}
                    className={`w-3 h-2 rounded-sm ${
                      (hour === 6 && day === 10) || (hour === 12 && (day === 10 || day === 18)) || (hour === 18 && day === 22)
                        ? 'bg-[#f3bd75]'
                        : 'bg-[#9cdccb]'
                    }`}
                  />
                ))}
              </div>
            ))}
          </div>
          
          <div className="flex items-center justify-between text-[10px] text-[#6b7f84] border-t border-[#29383d] pt-3">
            <span>dataset time</span>
            <div className="flex gap-8">
              <span>15 SEP</span>
              <span>23 SEP</span>
              <span>01 OCT</span>
              <span>09 OCT</span>
              <span>14 OCT</span>
            </div>
          </div>
          
          <p className="text-[#93a7ab] text-[10px] mt-4">
            MISSING: 18R2 / 720 HOURS · 97.5%
          </p>
          <p className="text-[#6b7f84] text-[10px] mt-2">
            All 18 source gaps occurred in September. The latest 14 days are complete. 336 / 336 hours.
          </p>
        </div>
        
        {/* Pipeline & Validation */}
        <div className="grid grid-cols-[1fr_400px] gap-5">
          <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-6">
            <div className="mb-4">
              <h3 className="text-[#e8f0ec] text-sm font-medium mb-1">From source to forecast</h3>
              <p className="text-[#93a7ab] text-xs">Latest validated observations · timestamps are interval starts, in dataset time</p>
            </div>
            
            <div className="overflow-x-auto mb-4">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-[#29383d] text-[#6b7f84] text-left">
                    <th className="py-2 px-3 font-medium">hour_start</th>
                    <th className="py-2 px-3 font-medium">meter_id</th>
                    <th className="py-2 px-3 font-medium text-right">mean_active_power_kW</th>
                    <th className="py-2 px-3 font-medium">quality_flag</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-[#29383d]">
                    <td className="py-2 px-3 text-[#e8f0ec] font-mono">2026-10-14 20:00</td>
                    <td className="py-2 px-3 text-[#93a7ab] font-mono">UCI-HOUSEHOLD</td>
                    <td className="py-2 px-3 text-right text-[#e8f0ec] font-mono">234.0</td>
                    <td className="py-2 px-3">
                      <span className="text-[#9cdccb] text-[10px]">Observed</span>
                    </td>
                  </tr>
                  <tr className="border-b border-[#29383d]">
                    <td className="py-2 px-3 text-[#e8f0ec] font-mono">2026-10-14 21:00</td>
                    <td className="py-2 px-3 text-[#93a7ab] font-mono">UCI-HOUSEHOLD</td>
                    <td className="py-2 px-3 text-right text-[#e8f0ec] font-mono">186.0</td>
                    <td className="py-2 px-3">
                      <span className="text-[#9cdccb] text-[10px]">Observed</span>
                    </td>
                  </tr>
                  <tr className="border-b border-[#29383d]">
                    <td className="py-2 px-3 text-[#e8f0ec] font-mono">2026-10-14 22:00</td>
                    <td className="py-2 px-3 text-[#93a7ab] font-mono">UCI-HOUSEHOLD</td>
                    <td className="py-2 px-3 text-right text-[#e8f0ec] font-mono">166.0</td>
                    <td className="py-2 px-3">
                      <span className="text-[#9cdccb] text-[10px]">Observed</span>
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-[#e8f0ec] font-mono">2026-10-14 23:00</td>
                    <td className="py-2 px-3 text-[#93a7ab] font-mono">UCI-HOUSEHOLD</td>
                    <td className="py-2 px-3 text-right text-[#e8f0ec] font-mono">150.0</td>
                    <td className="py-2 px-3">
                      <span className="text-[#9cdccb] text-[10px]">Observed</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            
            <p className="text-[#93a7ab] text-[10px]">Showing latest 4 records · ascending time</p>
            <button className="text-[#bcf58a] text-xs font-medium mt-2 hover:underline">
              Open full explorer →
            </button>
          </div>
          
          <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[#e8f0ec] text-sm font-medium">Validation report</h3>
              <span className="bg-[#bcf58a] bg-opacity-20 border border-[#bcf58a] border-opacity-30 text-[#bcf58a] text-[9px] font-bold px-2 py-1 rounded uppercase">
                5 PASS · 1 WARN
              </span>
            </div>
            
            <div className="space-y-3">
              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-[#9cdccb] mt-0.5 shrink-0" />
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-0.5">
                    <p className="text-[#e8f0ec] text-xs font-medium">Schema & types</p>
                    <span className="text-[#9cdccb] text-[10px]">4 / 4 fields valid</span>
                  </div>
                </div>
              </div>
              
              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-[#9cdccb] mt-0.5 shrink-0" />
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-0.5">
                    <p className="text-[#e8f0ec] text-xs font-medium">Timestamp order</p>
                    <span className="text-[#9cdccb] text-[10px]">Strictly increasing</span>
                  </div>
                </div>
              </div>
              
              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-[#9cdccb] mt-0.5 shrink-0" />
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-0.5">
                    <p className="text-[#e8f0ec] text-xs font-medium">Duplicate timestamps</p>
                    <span className="text-[#9cdccb] text-[10px]">0 duplicates</span>
                  </div>
                </div>
              </div>
              
              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-[#9cdccb] mt-0.5 shrink-0" />
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-0.5">
                    <p className="text-[#e8f0ec] text-xs font-medium">Consumption range</p>
                    <span className="text-[#9cdccb] text-[10px]">0-900 kW check passed</span>
                  </div>
                </div>
              </div>
              
              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-[#9cdccb] mt-0.5 shrink-0" />
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-0.5">
                    <p className="text-[#e8f0ec] text-xs font-medium">Freshness</p>
                    <span className="text-[#9cdccb] text-[10px]">7 min / target ≤15 min</span>
                  </div>
                </div>
              </div>
              
              <div className="flex items-start gap-2.5">
                <AlertTriangle className="w-4 h-4 text-[#f3bd75] mt-0.5 shrink-0" />
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-0.5">
                    <p className="text-[#e8f0ec] text-xs font-medium">Missingness</p>
                    <span className="text-[#f3bd75] text-[10px]">18 raw hours absent</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="mt-4 pt-4 border-t border-[#29383d]">
              <p className="text-[#6b7f84] text-[10px] leading-relaxed">
                LAST RUN · Selected data period 00:07 dataset time
              </p>
            </div>
          </div>
        </div>
        
        {/* Footer Note */}
        <div className="mt-6 bg-[#121d21] border border-[#29383d] rounded-lg p-4 flex items-start gap-3">
          <svg className="w-4 h-4 text-[#93a7ab] mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-[#93a7ab] text-xs leading-relaxed">
            <strong className="text-[#e8f0ec]">Missing-data policy:</strong> gaps of ≤2 hours are interpolated for training features only. 
            Six hours in a longer gap are excluded: raw values remain unchanged, imputed targets are never used to score model accuracy.
          </p>
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
