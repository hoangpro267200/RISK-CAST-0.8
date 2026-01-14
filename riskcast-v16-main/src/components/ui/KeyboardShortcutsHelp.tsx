/**
 * KeyboardShortcutsHelp Component
 * 
 * Modal/panel showing available keyboard shortcuts.
 */

import React from 'react';
import { X, Keyboard } from 'lucide-react';

export interface ShortcutItem {
  key: string;
  modifiers?: string[];
  description: string;
}

export interface KeyboardShortcutsHelpProps {
  isOpen: boolean;
  onClose: () => void;
  shortcuts?: ShortcutItem[];
}

const DEFAULT_SHORTCUTS: ShortcutItem[] = [
  { key: '1', description: 'Go to Overview tab' },
  { key: '2', description: 'Go to Analytics tab' },
  { key: '3', description: 'Go to Decisions tab' },
  { key: 'R', description: 'Refresh data' },
  { key: '/', description: 'Open AI Advisor' },
  { key: 'K', modifiers: ['Ctrl'], description: 'Open command palette' },
  { key: 'E', modifiers: ['Ctrl'], description: 'Export results' },
  { key: 'Esc', description: 'Close panels/modals' }
];

export const KeyboardShortcutsHelp: React.FC<KeyboardShortcutsHelpProps> = ({
  isOpen,
  onClose,
  shortcuts = DEFAULT_SHORTCUTS
}) => {
  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[300]"
        onClick={onClose}
      />

      {/* Modal */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="shortcuts-title"
        className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-[301] w-full max-w-md"
      >
        <div className="bg-slate-800/95 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl shadow-black/50 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center">
                <Keyboard className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <h2 id="shortcuts-title" className="text-lg font-semibold text-white">
                  Keyboard Shortcuts
                </h2>
                <p className="text-xs text-white/50">Power user navigation</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 text-white/50 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
              aria-label="Close shortcuts help"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Shortcuts List */}
          <div className="px-6 py-4 space-y-2 max-h-80 overflow-y-auto">
          {shortcuts.map((shortcut) => (
            <div
              key={`${shortcut.key}-${shortcut.description}`}
                className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-white/5 transition-colors"
              >
                <span className="text-sm text-white/80">{shortcut.description}</span>
                <div className="flex items-center gap-1">
                  {shortcut.modifiers?.map((mod) => (
                    <React.Fragment key={mod}>
                      <kbd className="px-2 py-1 text-xs font-mono bg-white/10 border border-white/20 rounded text-white/70">
                        {mod}
                      </kbd>
                      <span className="text-white/30">+</span>
                    </React.Fragment>
                  ))}
                  <kbd className="px-2 py-1 text-xs font-mono bg-white/10 border border-white/20 rounded text-white/70 min-w-[28px] text-center">
                    {shortcut.key}
                  </kbd>
                </div>
              </div>
            ))}
          </div>

          {/* Footer */}
          <div className="px-6 py-3 border-t border-white/10 bg-white/5">
            <p className="text-xs text-white/40 text-center">
              Press <kbd className="px-1.5 py-0.5 bg-white/10 rounded text-white/60 mx-1">?</kbd> to toggle this help
            </p>
          </div>
        </div>
      </div>
    </>
  );
};

export default KeyboardShortcutsHelp;
