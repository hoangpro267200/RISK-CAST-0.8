import React from 'react';
import { Users, FlaskConical } from 'lucide-react';

interface ViewModeToggleProps {
  mode: 'executive' | 'analyst';
  onChange: (mode: 'executive' | 'analyst') => void;
}

export function ViewModeToggle({ mode, onChange }: ViewModeToggleProps) {
  const onKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      e.preventDefault();
      onChange('executive');
    }
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      e.preventDefault();
      onChange('analyst');
    }
  };

  return (
    <div className="flex flex-col items-end gap-2">
      {/* Toggle Buttons */}
      <div
        className="flex items-center gap-1 p-1 bg-black/40 rounded-lg border border-white/10"
        role="tablist"
        aria-label="View mode"
        onKeyDown={onKeyDown}
      >
        <button
          type="button"
          onClick={() => onChange('executive')}
          role="tab"
          aria-selected={mode === 'executive'}
          aria-controls="executive-panel"
          tabIndex={mode === 'executive' ? 0 : -1}
          className={`
            flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all
            focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent-primary)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-bg-primary)]
            ${
              mode === 'executive'
                ? 'bg-white/10 text-white shadow-sm'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }
          `}
        >
          <Users className="w-4 h-4" />
          Executive
        </button>

        <button
          type="button"
          onClick={() => onChange('analyst')}
          role="tab"
          aria-selected={mode === 'analyst'}
          aria-controls="analyst-panel"
          tabIndex={mode === 'analyst' ? 0 : -1}
          className={`
            flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all
            focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent-primary)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-bg-primary)]
            ${
              mode === 'analyst'
                ? 'bg-white/10 text-white shadow-sm'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }
          `}
        >
          <FlaskConical className="w-4 h-4" />
          Analyst
        </button>
      </div>

      {/* Mode Label */}
      <div className="text-xs text-gray-400" aria-live="polite">
        You are viewing:{' '}
        {mode === 'executive' ? (
          <span className="text-blue-400 font-medium">Executive Summary</span>
        ) : (
          <span className="text-purple-400 font-medium">Analyst Deep Dive</span>
        )}
      </div>
    </div>
  );
}




