/**
 * Better models. Measured fairly. - Figma Design Implementation
 *
 * Compare ML model performance with fair benchmarking.
 * Uses real API data when backend is available, falls back to demo data.
 */

'use client';

import { LoadingState } from '@/components/ui/LoadingSpinner';
import { ErrorState } from '@/components/ui/ErrorState';
import { getDemoModelComparisonData } from '@/lib/demoData';
import { demoModeEnabled } from '@/lib/utils';
import { DemoDataBanner } from '@/components/ui/DemoDataBanner';
import { fetchModelMetrics } from '@/lib/api';
import { ModelComparisonData } from '@/lib/types';
import { Calendar, CheckCircle2 } from 'lucide-react';
import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function ModelsPage() {
  const [comparisonData, setComparisonData] = useState<ModelComparisonData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);

      try {
        const apiData = await fetchModelMetrics();

        if (apiData) {
          setComparisonData(apiData);
        } else if (demoModeEnabled()) {
          setComparisonData(getDemoModelComparisonData());
        } else {
          setError('Experiment metrics are unavailable. Run scripts/train_models.py, or add ?demo=1 for synthetic preview data.');
        }
      } catch {
        if (demoModeEnabled()) setComparisonData(getDemoModelComparisonData());
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
        <LoadingState message="Loading model metrics..." />
      </div>
    );
  }

  if (error || !comparisonData) {
    return (
      <div className="p-8">
        <ErrorState
          message="Failed to Load Data"
          detail={error || "Could not load model metrics"}
          retry={() => window.location.reload()}
        />
      </div>
    );
  }

  const horizonData = comparisonData.models.map((model) => ({ name: model.name, MAE: model.mae, RMSE: model.rmse }));

  if (!comparisonData.isDemo) {
    const recursiveTest = comparisonData.recursiveTest;
    return <div className="min-h-screen p-6 md:p-10 text-[#e8f0ec]"><header className="mb-8 border-b border-[#29383d] pb-5"><p className="text-sm text-[#93a7ab]">GridPulse / Models</p><h1 className="mt-2 text-3xl">24-hour recursive comparison</h1><p className="mt-2 text-sm text-[#93a7ab]">One-step held-out test period: {new Date(comparisonData.evaluationPeriod.start).toLocaleString()} – {new Date(comparisonData.evaluationPeriod.end).toLocaleString()}</p></header>
      <section className="mb-5 rounded-lg border border-[#29383d] bg-[#121d21] p-5"><p className="text-sm text-[#93a7ab]">Selected by {comparisonData.selectionMetric}</p><p className="mt-2 text-2xl">{comparisonData.bestModel}</p><p className="mt-2 text-xs text-[#93a7ab]">Recursive {comparisonData.forecastHorizon}-hour MAE/RMSE use validation windows. The separate test columns below are rolling one-step scores and are not 24-hour scores.</p></section>
      <section className="mb-5 rounded-lg border border-[#29383d] bg-[#121d21] p-5"><p className="text-sm text-[#93a7ab]">Selected model · held-out recursive {comparisonData.forecastHorizon}-hour test ({recursiveTest?.forecast_origins ?? 0} origins / {recursiveTest?.evaluated_hours ?? 0} target hours)</p><div className="mt-3 flex flex-wrap gap-8 text-sm"><span>MAE <strong className="ml-2 font-mono">{recursiveTest?.metrics.mae.toFixed(4) ?? 'Unavailable'} kW</strong></span><span>RMSE <strong className="ml-2 font-mono">{recursiveTest?.metrics.rmse.toFixed(4) ?? 'Unavailable'} kW</strong></span></div><p className="mt-2 text-xs text-[#93a7ab]">Step groups: 1–6h {recursiveTest?.step_group_metrics.hours_1_6?.mae.toFixed(4) ?? 'Unavailable'} MAE · 7–12h {recursiveTest?.step_group_metrics.hours_7_12?.mae.toFixed(4) ?? 'Unavailable'} MAE · 13–24h {recursiveTest?.step_group_metrics.hours_13_24?.mae.toFixed(4) ?? 'Unavailable'} MAE (kW).</p></section>
      <section className="overflow-x-auto rounded-lg border border-[#29383d] bg-[#121d21] p-5"><table className="w-full text-left text-sm"><thead className="text-[#93a7ab]"><tr><th className="p-2">Model</th><th className="p-2">24h validation MAE (kW)</th><th className="p-2">24h validation RMSE (kW)</th><th className="p-2">Origins</th><th className="p-2">1h test MAE (kW)</th><th className="p-2">1h test RMSE (kW)</th></tr></thead><tbody>{comparisonData.models.map(model=><tr key={model.name} className="border-t border-[#29383d]"><td className="p-2">{model.name}</td><td className="p-2 font-mono">{model.recursiveValidation?.mae.toFixed(4) ?? 'Unavailable'}</td><td className="p-2 font-mono">{model.recursiveValidation?.rmse.toFixed(4) ?? 'Unavailable'}</td><td className="p-2">{model.recursiveValidation?.forecastOrigins.toLocaleString() ?? 'Unavailable'}</td><td className="p-2 font-mono">{model.mae.toFixed(4)}</td><td className="p-2 font-mono">{model.rmse.toFixed(4)}</td></tr>)}</tbody></table></section></div>;
  }

  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <header className="border-b border-[#29383d] px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <span className="text-[#93a7ab] text-sm">Workspace / Models</span>
        </div>
        <div className="flex items-center gap-4 text-[#93a7ab] text-xs">
          <span>TEST PERIOD · {new Date(comparisonData.evaluationPeriod.start).toLocaleDateString()} – {new Date(comparisonData.evaluationPeriod.end).toLocaleDateString()}</span>
          <button className="p-1.5 hover:bg-[#1a2b30] rounded"><Calendar className="w-4 h-4" /></button>
        </div>
      </header>
      {comparisonData.isDemo && <div className="px-8 pt-5"><DemoDataBanner /></div>}

      {/* Main Content */}
      <div className="flex-1 overflow-auto px-8 py-6">
        {/* Page Title */}
        <div className="mb-6">
          <p className="text-[#bcf58a] text-[10px] font-mono mb-2">04 / MODEL BENCHMARK</p>
          <div className="flex items-center justify-between">
            <h1 className="text-[#e8f0ec] text-[34px] font-medium">Better models. Measured fairly.</h1>
            <button className="bg-[#18252a] border border-[#29383d] px-4 py-2 rounded text-[#e8f0ec] text-sm hover:bg-[#1a2b30]">
              Export benchmark
            </button>
          </div>
          <p className="text-[#93a7ab] text-sm mt-2">
            Compare predictive accuracy, uncertainty and inference cost on the same held-out hours.
          </p>
        </div>

        {/* Evaluation Controls */}
        <div className="flex items-center gap-3 mb-6">
          <button className="bg-[#18252a] border border-[#29383d] px-3 py-2 rounded text-[#e8f0ec] text-xs flex items-center gap-2">
            <Calendar className="w-3 h-3" />
            01-Selected data period
          </button>
          <button className="bg-[#18252a] border border-[#29383d] px-3 py-2 rounded text-[#e8f0ec] text-xs">
            24-hour horizon
          </button>
          <button className="bg-[#18252a] border border-[#29383d] px-3 py-2 rounded text-[#e8f0ec] text-xs">
            UCI-HOUSEHOLD · hourly
          </button>
          <div className="ml-auto flex items-center gap-2">
            <span className="bg-[#bcf58a] text-[#0c1215] text-[9px] font-bold px-2 py-0.5 rounded uppercase">DEMO</span>
            <span className="bg-[#bcf58a] bg-opacity-20 border border-[#bcf58a] border-opacity-30 text-[#bcf58a] text-[9px] font-bold px-2 py-1 rounded uppercase">
              COMPLETED EVALUATION
            </span>
          </div>
        </div>

        {/* Selected Model Spotlight */}
        <div className="bg-gradient-to-r from-[#1a2b30] to-[#121d21] border border-[#29383d] rounded-lg p-6 mb-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-[#bcf58a] bg-opacity-20 p-3 rounded-full">
                <CheckCircle2 className="w-6 h-6 text-[#bcf58a]" />
              </div>
              <div>
                <p className="text-[#93a7ab] text-xs mb-1">SELECTED FOR FORECASTING</p>
                <h2 className="text-[#e8f0ec] text-2xl font-medium mb-1 flex items-center gap-2">
                  {comparisonData.bestModel}
                  <svg className="w-5 h-5 text-[#bcf58a]" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </h2>
                <p className="text-[#93a7ab] text-sm">Lowest MAE across all horizon groups</p>
              </div>
            </div>
            <div className="text-right">
              <div className="flex items-baseline gap-2 justify-end mb-1">
                <span className="text-[#bcf58a] text-4xl font-mono leading-none">43.1%</span>
              </div>
              <p className="text-[#93a7ab] text-xs">lower MAE vs seasonal naive</p>
            </div>
          </div>
        </div>

        <p className="text-[#6b7f84] text-xs mb-6">
          14 daily origins. 336 identical target hours. Hourly energy forecasts evaluated over 01-Latest observation day.
          All candidates use the same split, forecast horizon and scoring rules. Lower error is better.
        </p>

        {/* Benchmark Results Table */}
        <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-6 mb-6">
          <h3 className="text-[#e8f0ec] text-sm font-medium mb-4">Benchmark results</h3>
          <p className="text-[#93a7ab] text-xs mb-4">
            Held-out evaluation · Chronological held-out test window
          </p>

          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-[#29383d] text-[#6b7f84] text-left">
                  <th className="py-3 px-3 font-medium">Model</th>
                  <th className="py-3 px-3 font-medium text-right">MAE ↓</th>
                  <th className="py-3 px-3 font-medium text-right">RMSE ↓</th>
                  <th className="py-3 px-3 font-medium text-right">WAPE ↓</th>
                  <th className="py-3 px-3 font-medium text-right">90% coverage¹</th>
                  <th className="py-3 px-3 font-medium text-right">Inference²</th>
                  <th className="py-3 px-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {comparisonData.models.slice(0, 3).map((model, idx) => (
                  <tr
                    key={idx}
                    className={`border-b border-[#29383d] ${
                      model.name === comparisonData.bestModel ? 'bg-[#1a2b30]' : ''
                    }`}
                  >
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-2">
                        <span className="text-[#6b7f84] text-[10px]">{(idx + 1).toString().padStart(2, '0')}</span>
                        <span className="text-[#e8f0ec] font-medium">{model.name}</span>
                      </div>
                    </td>
                    <td className="py-3 px-3 text-right">
                      <span className="text-[#e8f0ec] font-mono">{(model.mae ?? 0).toFixed(1)} kW</span>
                    </td>
                    <td className="py-3 px-3 text-right">
                      <span className="text-[#93a7ab] font-mono">{(model.rmse ?? 0).toFixed(1)} kW</span>
                    </td>
                    <td className="py-3 px-3 text-right">
                      <span className="text-[#93a7ab] font-mono">6.4%</span>
                    </td>
                    <td className="py-3 px-3 text-right">
                      <span className="text-[#93a7ab] font-mono">88.7%</span>
                    </td>
                    <td className="py-3 px-3 text-right">
                      <span className="text-[#93a7ab] font-mono">{model.trainingTime ? `${model.trainingTime.toFixed(0)} ms` : '2 ms'}</span>
                    </td>
                    <td className="py-3 px-3">
                      <span className={`text-[9px] font-bold px-2 py-1 rounded ${
                        model.name === comparisonData.bestModel
                          ? 'bg-[#bcf58a] bg-opacity-20 text-[#bcf58a]'
                          : model.isBaseline
                          ? 'bg-[#6b7f84] bg-opacity-20 text-[#93a7ab]'
                          : 'bg-[#b9adff] bg-opacity-20 text-[#b9adff]'
                      }`}>
                        {model.name === comparisonData.bestModel ? 'Selected' : model.isBaseline ? 'Baseline' : 'Candidate'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-4 text-[10px] text-[#6b7f84] space-y-1">
            <p>¹ Pointwise interval coverage: target 90%. Intervals calibrated on 17-30 Sep, before the test window.</p>
            <p>² Mean inference time for one 24-hour batch on the same CPU. Forecast uses selected model and 14 Oct.</p>
          </div>
        </div>

        {/* Accuracy & Comparison Cards */}
        <div className="grid grid-cols-[2fr_1fr] gap-5">
          <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-6">
            <div className="mb-4">
              <h3 className="text-[#e8f0ec] text-sm font-medium mb-1">One-step holdout error by model</h3>
              <p className="text-[#93a7ab] text-xs">
                All models use the same chronological test observations. Metrics are in kW.
              </p>
            </div>

            <div className="flex items-center gap-6 mb-4 text-[10px]">
              <div className="flex items-center gap-2">
                <div className="w-3 h-0.5 bg-[#bcf58a]"></div>
                <span className="text-[#93a7ab]">MAE</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-0.5 bg-[#b9adff]"></div>
                <span className="text-[#93a7ab]">RMSE</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-0.5 bg-[#6b7f84]"></div>
                <span className="text-[#93a7ab]">kW error</span>
              </div>
            </div>

            <div className="h-[280px] -mx-2">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={horizonData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#29383d" vertical={false} />
                  <XAxis
                    dataKey="name"
                    tick={{ fill: '#6b7f84', fontSize: 10 }}
                    stroke="#29383d"
                    tickLine={false}
                    label={{ value: 'Lead-time from forecast origin', position: 'bottom', fill: '#6b7f84', fontSize: 10, offset: 0 }}
                  />
                  <YAxis
                    tick={{ fill: '#6b7f84', fontSize: 10 }}
                    stroke="#29383d"
                    tickLine={false}
                    label={{ value: 'Error / kW', angle: 0, position: 'top', fill: '#6b7f84', fontSize: 10, offset: 10 }}
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
                    dataKey="MAE"
                    stroke="#bcf58a"
                    strokeWidth={2}
                    dot={{ r: 4, fill: '#bcf58a' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="RMSE"
                    stroke="#b9adff"
                    strokeWidth={2}
                    dot={{ r: 4, fill: '#b9adff' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-[#121d21] border border-[#29383d] rounded-lg p-6">
            <h3 className="text-[#e8f0ec] text-sm font-medium mb-4">A fair comparison, by design</h3>

            <div className="space-y-4">
              <div>
                <h4 className="text-[#e8f0ec] text-xs font-medium mb-1">No future leakage</h4>
                <p className="text-[#93a7ab] text-[10px] leading-relaxed">
                  Tuning ended 30 Sep. Model parameters are frozen during evaluation;
                  lag inputs use only past observations.
                </p>
              </div>

              <div>
                <h4 className="text-[#e8f0ec] text-xs font-medium mb-1">Same target hours</h4>
                <p className="text-[#93a7ab] text-[10px] leading-relaxed">
                  14 non-overlapping, daily 24-hour origins. All 336 target hours are observed;
                  no imputed targets are scored.
                </p>
              </div>

              <div>
                <h4 className="text-[#e8f0ec] text-xs font-medium mb-1">Calibration is separate</h4>
                <p className="text-[#93a7ab] text-[10px] leading-relaxed">
                  Pointwise interval coverage: target 90%. Intervals calibrated on 17-30 Sep,
                  before the test window.
                </p>
              </div>
            </div>
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
