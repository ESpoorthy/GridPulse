/**
 * Banner to clearly indicate demo/synthetic data is being displayed.
 */

import { AlertTriangle } from 'lucide-react';

export function DemoDataBanner() {
  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <h4 className="text-sm font-semibold text-yellow-900 mb-1">
            Demo Data Notice
          </h4>
          <p className="text-sm text-yellow-800">
            You are viewing synthetic demo data for UI development. Real data will be
            provided by the FastAPI backend once implemented.
          </p>
        </div>
      </div>
    </div>
  );
}
