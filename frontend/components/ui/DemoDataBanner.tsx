/**
 * Banner to clearly indicate demo/synthetic data is being displayed.
 */

import { AlertTriangle } from 'lucide-react';

export function DemoDataBanner() {
  return (
    <div role="status" className="bg-[#302919] border border-[#765d30] rounded-lg p-4 mb-6">
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-[#f3bd75] mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <h4 className="text-sm font-semibold text-[#f3bd75] mb-1">
            Synthetic demo mode
          </h4>
          <p className="text-sm text-[#e8d7b5]">
            These illustrative values are synthetic and are not observations or model results from the UCI dataset.
          </p>
        </div>
      </div>
    </div>
  );
}
