/**
 * Formatting utilities
 */

/**
 * Format a date/time as relative time (e.g., "2 minutes ago")
 */
export function formatRelativeTime(dateString: string | null | undefined): string {
  if (!dateString) {
    return 'Never';
  }

  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSeconds = Math.floor(diffMs / 1000);
    const diffMinutes = Math.floor(diffSeconds / 60);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSeconds < 60) {
      return 'Just now';
    } else if (diffMinutes < 60) {
      return `${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
      return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    } else if (diffDays < 7) {
      return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    } else {
      // For older dates, show actual date
      return date.toLocaleDateString();
    }
  } catch {
    return 'Invalid date';
  }
}

/**
 * Format a number as percentage
 */
export function formatPercent(value: number, decimals: number = 0): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Format a number with commas
 */
export function formatNumber(value: number): string {
  return value.toLocaleString();
}
