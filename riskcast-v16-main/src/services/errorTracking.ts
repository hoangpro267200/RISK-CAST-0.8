export type ErrorLevel = 'info' | 'warning' | 'error';

export interface ErrorTracker {
  captureException(error: Error, context?: Record<string, unknown>): void;
  captureMessage(message: string, level: ErrorLevel, context?: Record<string, unknown>): void;
}

class ConsoleErrorTracker implements ErrorTracker {
  captureException(error: Error, context?: Record<string, unknown>): void {
    console.error('[error]', error, context);
  }

  captureMessage(message: string, level: ErrorLevel, context?: Record<string, unknown>): void {
    const payload = { level, message, context };
    if (level === 'error') {
      console.error('[message]', payload);
    } else if (level === 'warning') {
      console.warn('[message]', payload);
    } else {
      console.info('[message]', payload);
    }
  }
}

let tracker: ErrorTracker = new ConsoleErrorTracker();

export function setErrorTracker(next: ErrorTracker): void {
  tracker = next;
}

export function getErrorTracker(): ErrorTracker {
  return tracker;
}

export function captureException(error: Error, context?: Record<string, unknown>): void {
  getErrorTracker().captureException(error, context);
}

export function captureMessage(message: string, level: ErrorLevel, context?: Record<string, unknown>): void {
  getErrorTracker().captureMessage(message, level, context);
}

