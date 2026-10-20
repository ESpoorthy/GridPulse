/**
 * Empty state component for when no data is available.
 */

import { FileQuestion } from 'lucide-react';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      <div className="flex items-center justify-center w-12 h-12 rounded-full bg-gray-100 mb-4">
        {icon || <FileQuestion className="w-6 h-6 text-gray-400" />}
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      {description && <p className="text-sm text-gray-600 text-center max-w-md mb-4">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
