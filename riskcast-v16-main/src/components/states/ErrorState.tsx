import React from 'react';
import { AlertTriangle, CloudOff, RefreshCw, Bug, BarChart3 } from 'lucide-react';
import { GlassCard } from '../GlassCard';

export type ErrorStateType = 'generic' | 'chart' | 'data' | 'network';

export interface ErrorStateProps {
  type?: ErrorStateType;
  title?: string;
  description?: string;
  error?: unknown;
  errorId?: string;
  variant?: 'card' | 'inline';
  onRetry?: () => void;
  onReport?: () => void;
  className?: string;
  showDetails?: boolean;
}

function defaultShowDetails(): boolean {
  try {
    const mode = (import.meta as unknown as { env?: { MODE?: string } }).env?.MODE;
    return mode === 'development' || mode === 'test';
  } catch {
    return false;
  }
}

function normalizeErrorMessage(err: unknown): string {
  if (!err) return '—';
  if (err instanceof Error) return err.message || err.name;
  if (typeof err === 'string') return err;
  try {
    return JSON.stringify(err);
  } catch {
    return String(err);
  }
}

function Icon({ type }: { type: ErrorStateType }) {
  switch (type) {
    case 'network':
      return <CloudOff className="w-10 h-10 text-white/25" />;
    case 'chart':
      return <BarChart3 className="w-10 h-10 text-white/25" />;
    case 'data':
      return <Bug className="w-10 h-10 text-white/25" />;
    default:
      return <AlertTriangle className="w-10 h-10 text-white/25" />;
  }
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  type = 'generic',
  title,
  description,
  error,
  errorId,
  onRetry,
  onReport,
  variant = 'card',
  className = '',
  showDetails = defaultShowDetails(),
}) => {
  const computedTitle =
    title ??
    (type === 'network'
      ? 'Network error'
      : type === 'chart'
        ? 'Chart failed to render'
        : type === 'data'
          ? 'Data error'
          : 'Unexpected error');

  const computedDescription =
    description ??
    (type === 'network'
      ? 'We could not reach the server. Check your connection and try again.'
      : type === 'chart'
        ? 'This visualization could not be displayed. You can retry or view other sections.'
        : type === 'data'
          ? 'Some required data is missing or invalid. Try reloading or switching views.'
          : 'An unexpected problem occurred.');

  const content = (
    <div className="flex flex-col items-center justify-center py-10 text-center">
      <Icon type={type} />
      <h3 className="mt-4 text-lg font-medium text-white/80">{computedTitle}</h3>
      <p className="mt-2 text-sm text-white/50 max-w-md">{computedDescription}</p>
      {errorId ? <p className="mt-3 text-xs text-white/30">Error ID: {errorId}</p> : null}

      <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
        {onRetry ? (
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/15 border border-white/10 text-white/80 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent-primary)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-bg-primary)]"
          >
            <RefreshCw className="w-4 h-4" />
            Retry
          </button>
        ) : null}

        {onReport ? (
          <button
            type="button"
            onClick={onReport}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-white/70 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent-primary)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-bg-primary)]"
          >
            <Bug className="w-4 h-4" />
            Report issue
          </button>
        ) : null}
      </div>

      {showDetails && error ? (
        <details className="mt-6 w-full max-w-2xl text-left">
          <summary className="cursor-pointer text-xs text-white/40 hover:text-white/60 transition-colors">
            Technical details
          </summary>
          <pre className="mt-3 p-4 rounded-xl bg-black/30 border border-white/10 text-xs text-white/60 overflow-x-auto whitespace-pre-wrap">
            {normalizeErrorMessage(error)}
          </pre>
        </details>
      ) : null}
    </div>
  );

  if (variant === 'inline') {
    return <div className={className}>{content}</div>;
  }

  return <GlassCard className={className}>{content}</GlassCard>;
};

export const ChartErrorState: React.FC<Omit<ErrorStateProps, 'type'>> = (props) => {
  return (
    <ErrorState
      type="chart"
      title={props.title ?? 'Chart failed to render'}
      description={
        props.description ?? 'This chart encountered an error. You can retry, or continue using other sections.'
      }
      {...props}
    />
  );
};

