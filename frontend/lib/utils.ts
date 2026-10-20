/**
 * Utility functions for GridPulse frontend.
 */

import { type ClassValue, clsx } from 'clsx';

/**
 * Merge Tailwind CSS classes with proper precedence.
 * Later classes override earlier ones.
 */
export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

/**
 * Format a number to specified decimal places.
 */
export function formatNumber(value: number, decimals: number = 2): string {
  return value.toFixed(decimals);
}

/**
 * Format a timestamp to human-readable date/time.
 */
export function formatTimestamp(isoString: string, includeTime: boolean = true): string {
  const date = new Date(isoString);
  
  if (includeTime) {
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }
  
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

/**
 * Format a date range as a readable string.
 */
export function formatDateRange(start: string, end: string): string {
  const startDate = new Date(start);
  const endDate = new Date(end);
  
  const startStr = startDate.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
  
  const endStr = endDate.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
  
  return `${startStr} – ${endStr}`;
}

/**
 * Format relative time (e.g., "2 hours ago").
 */
export function formatRelativeTime(isoString: string): string {
  // For SSR safety, check if we're in browser
  if (typeof window === 'undefined') {
    return formatTimestamp(isoString, false);
  }
  
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return formatTimestamp(isoString, false);
}

/**
 * Format power value with unit (kW).
 */
export function formatPower(kw: number, decimals: number = 2): string {
  return `${formatNumber(kw, decimals)} kW`;
}

/**
 * Format percentage with sign.
 */
export function formatPercentage(value: number, decimals: number = 1, includeSign: boolean = true): string {
  const sign = includeSign && value > 0 ? '+' : '';
  return `${sign}${formatNumber(value, decimals)}%`;
}

/**
 * Get color class for trend indicator.
 */
export function getTrendColor(trend: 'up' | 'down' | 'stable'): string {
  switch (trend) {
    case 'up':
      return 'text-red-600';
    case 'down':
      return 'text-green-600';
    case 'stable':
      return 'text-gray-600';
  }
}

/**
 * Get color class for anomaly severity.
 */
export function getSeverityColor(severity: 'low' | 'medium' | 'high'): string {
  switch (severity) {
    case 'high':
      return 'text-red-600 bg-red-50';
    case 'medium':
      return 'text-orange-600 bg-orange-50';
    case 'low':
      return 'text-yellow-600 bg-yellow-50';
  }
}

/**
 * Get badge color for anomaly severity.
 */
export function getSeverityBadgeClass(severity: 'low' | 'medium' | 'high'): string {
  switch (severity) {
    case 'high':
      return 'bg-red-100 text-red-800 border-red-200';
    case 'medium':
      return 'bg-orange-100 text-orange-800 border-orange-200';
    case 'low':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200';
  }
}

/**
 * Truncate string to max length with ellipsis.
 */
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength - 3) + '...';
}

/**
 * Calculate percentage change between two values.
 */
export function calculatePercentageChange(oldValue: number, newValue: number): number {
  if (oldValue === 0) return 0;
  return ((newValue - oldValue) / oldValue) * 100;
}

/**
 * Debounce function to limit execution rate.
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}
