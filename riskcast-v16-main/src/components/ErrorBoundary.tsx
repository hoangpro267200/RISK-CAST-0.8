import React from 'react';
import { captureException, captureMessage } from '../services/errorTracking';
import { ErrorState } from './states/ErrorState';

export type ErrorBoundaryFallbackRenderProps = {
  error: Error;
  reset: () => void;
};

export type ErrorBoundaryFallback =
  | React.ReactNode
  | ((props: ErrorBoundaryFallbackRenderProps) => React.ReactNode);

export interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: ErrorBoundaryFallback;
  resetKeys?: readonly unknown[];
  context?: Record<string, unknown>;
  onError?: (error: Error, info: React.ErrorInfo) => void;
  onReset?: () => void;
  title?: string;
  description?: string;
}

type ErrorBoundaryState = {
  error: Error | null;
  errorId: string | null;
};

function createErrorId(): string {
  const rnd = Math.random().toString(36).slice(2);
  return `err_${Date.now().toString(36)}_${rnd}`;
}

function arraysShallowEqual(a: readonly unknown[] | undefined, b: readonly unknown[] | undefined): boolean {
  if (a === b) return true;
  if (!a || !b) return false;
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i += 1) {
    if (!Object.is(a[i], b[i])) return false;
  }
  return true;
}

function buildClipboardReport(params: {
  error: Error;
  errorId: string | null;
  componentStack?: string;
  context?: Record<string, unknown>;
}): string {
  const { error, errorId, componentStack, context } = params;
  const lines: string[] = [];
  lines.push('RISKCAST ISSUE REPORT');
  lines.push(`ErrorId: ${errorId ?? 'unknown'}`);
  lines.push(`Message: ${error.message}`);
  lines.push(`Name: ${error.name}`);
  if (error.stack) lines.push(`Stack:\n${error.stack}`);
  if (componentStack) lines.push(`ComponentStack:\n${componentStack}`);
  if (context && Object.keys(context).length > 0) {
    lines.push(`Context:\n${JSON.stringify(context, null, 2)}`);
  }
  return lines.join('\n\n');
}

async function copyToClipboard(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
    return false;
  } catch {
    return false;
  }
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null, errorId: null };
  private lastErrorInfo: React.ErrorInfo | null = null;

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error, errorId: createErrorId() };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo): void {
    this.lastErrorInfo = info;
    captureException(error, {
      errorId: this.state.errorId,
      componentStack: info.componentStack,
      ...this.props.context,
    });
    this.props.onError?.(error, info);
  }

  componentDidUpdate(prevProps: Readonly<ErrorBoundaryProps>): void {
    if (this.state.error && !arraysShallowEqual(prevProps.resetKeys, this.props.resetKeys)) {
      this.reset();
    }
  }

  private reset = (): void => {
    this.props.onReset?.();
    this.setState({ error: null, errorId: null });
  };

  private reportIssue = async (): Promise<void> => {
    const error = this.state.error;
    if (!error) return;

    const report = buildClipboardReport({
      error,
      errorId: this.state.errorId || null,
      componentStack: this.lastErrorInfo?.componentStack ?? undefined,
      context: this.props.context,
    });

    const copied = await copyToClipboard(report);
    if (copied) {
      captureMessage('User copied error report to clipboard', 'info', {
        errorId: this.state.errorId,
        ...this.props.context,
      });
      alert('Error report copied to clipboard. Please paste it into your issue tracker.');
      return;
    }

    captureMessage('Clipboard API unavailable; showing report prompt', 'warning', {
      errorId: this.state.errorId,
      ...this.props.context,
    });
    window.prompt('Copy the error report below:', report);
  };

  render(): React.ReactNode {
    const { error } = this.state;
    if (!error) return this.props.children;

    const fallback = this.props.fallback;
    if (typeof fallback === 'function') {
      return fallback({ error, reset: this.reset });
    }
    if (fallback) return fallback;

    return (
      <ErrorState
        type="generic"
        title={this.props.title ?? 'Something went wrong'}
        description={this.props.description ?? 'An unexpected error occurred. You can retry or report this issue.'}
        error={error}
        errorId={this.state.errorId || undefined}
        onRetry={this.reset}
        onReport={this.reportIssue}
      />
    );
  }
}

