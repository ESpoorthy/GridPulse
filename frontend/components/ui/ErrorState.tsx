/**
 * Error state components for displaying errors gracefully.
 */

import { AlertCircle } from 'lucide-react';

interface ErrorStateProps {
  message: string;
  detail?: string;
  retry?: () => void;
}

export function ErrorState({ message, detail, retry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      <div className="flex items-center justify-center w-12 h-12 rounded-full bg-red-100 mb-4">
        <AlertCircle className="w-6 h-6 text-red-600" />
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{message}</h3>
      {detail && <p className="text-sm text-gray-600 text-center max-w-md mb-4">{detail}</p>}
      {retry && (
        <button
          onClick={retry}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
        >
          Try Again
        </button>
      )}
    </div>
  );
}
