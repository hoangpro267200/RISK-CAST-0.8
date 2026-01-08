import { useState, useEffect, useRef } from 'react';
import { X, Check, AlertCircle } from 'lucide-react';

interface InlineEditorProps {
  isOpen: boolean;
  field: string;
  label: string;
  value: unknown;
  type: 'text' | 'number' | 'date' | 'select' | 'checkbox' | 'textarea';
  options?: Array<{ value: string; label: string }>;
  position: { x: number; y: number };
  onSave: (value: unknown) => void;
  onClose: () => void;
}

export function InlineEditor({ isOpen, field, label, value, type, options, position, onSave, onClose }: InlineEditorProps) {
  const [localValue, setLocalValue] = useState<unknown>(value);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setLocalValue(value);
    setError(null);
  }, [value, field]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Handle click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSave = () => {
    // Basic validation
    if (type === 'number' && isNaN(Number(localValue))) {
      setError('Please enter a valid number');
      return;
    }
    if (type === 'date' && !localValue) {
      setError('Please select a date');
      return;
    }

    onSave(localValue);
    onClose();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && type !== 'textarea') {
      e.preventDefault();
      handleSave();
    }
  };

  // Adjust position to stay within viewport
  const adjustedPosition = {
    x: Math.min(position.x, window.innerWidth - 320),
    y: Math.min(position.y, window.innerHeight - 200),
  };

  const renderInput = () => {
    switch (type) {
      case 'select':
        return (
          <select
            ref={inputRef as React.RefObject<HTMLSelectElement>}
            value={String(localValue ?? '')}
            onChange={(e) => setLocalValue(e.target.value)}
            className="w-full bg-[#0a1628] border border-white/20 rounded-lg px-3 py-2.5 text-white focus:outline-none focus:border-cyan-500"
          >
            <option value="">Select...</option>
            {options?.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        );

      case 'checkbox':
        return (
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              ref={inputRef as React.RefObject<HTMLInputElement>}
              type="checkbox"
              checked={Boolean(localValue)}
              onChange={(e) => setLocalValue(e.target.checked)}
              className="w-5 h-5 rounded border-white/20 bg-[#0a1628] text-cyan-500 focus:ring-cyan-500"
            />
            <span className="text-white">{Boolean(localValue) ? 'Yes' : 'No'}</span>
          </label>
        );

      case 'textarea':
        return (
          <textarea
            ref={inputRef as React.RefObject<HTMLTextAreaElement>}
            value={String(localValue ?? '')}
            onChange={(e) => setLocalValue(e.target.value)}
            rows={3}
            className="w-full bg-[#0a1628] border border-white/20 rounded-lg px-3 py-2.5 text-white focus:outline-none focus:border-cyan-500 resize-none"
          />
        );

      case 'date':
        return (
          <input
            ref={inputRef as React.RefObject<HTMLInputElement>}
            type="date"
            value={String(localValue ?? '')}
            onChange={(e) => setLocalValue(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full bg-[#0a1628] border border-white/20 rounded-lg px-3 py-2.5 text-white focus:outline-none focus:border-cyan-500"
          />
        );

      case 'number':
        return (
          <input
            ref={inputRef as React.RefObject<HTMLInputElement>}
            type="number"
            value={String(localValue ?? '')}
            onChange={(e) => setLocalValue(e.target.value ? Number(e.target.value) : '')}
            onKeyDown={handleKeyDown}
            className="w-full bg-[#0a1628] border border-white/20 rounded-lg px-3 py-2.5 text-white focus:outline-none focus:border-cyan-500"
          />
        );

      default:
        return (
          <input
            ref={inputRef as React.RefObject<HTMLInputElement>}
            type="text"
            value={String(localValue ?? '')}
            onChange={(e) => setLocalValue(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full bg-[#0a1628] border border-white/20 rounded-lg px-3 py-2.5 text-white focus:outline-none focus:border-cyan-500"
          />
        );
    }
  };

  return (
    <div
      ref={containerRef}
      className="fixed z-50 w-72 backdrop-blur-xl bg-[#0d1f35]/95 border border-white/20 rounded-2xl shadow-2xl"
      style={{
        left: adjustedPosition.x,
        top: adjustedPosition.y,
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
        <div>
          <div className="text-white font-medium text-sm">{label}</div>
          <div className="text-white/40 text-xs">{field}</div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 hover:bg-white/10 rounded-lg transition-colors"
        >
          <X className="w-4 h-4 text-white/50" />
        </button>
      </div>

      {/* Body */}
      <div className="p-4">
        {renderInput()}

        {error && (
          <div className="mt-2 flex items-center gap-2 text-red-400 text-xs">
            <AlertCircle className="w-3.5 h-3.5" />
            {error}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-end gap-2 px-4 py-3 border-t border-white/10">
        <button
          onClick={onClose}
          className="px-3 py-1.5 text-white/60 hover:text-white text-sm transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleSave}
          className="px-4 py-1.5 bg-cyan-500 hover:bg-cyan-400 text-white text-sm rounded-lg transition-colors flex items-center gap-1.5"
        >
          <Check className="w-3.5 h-3.5" />
          Save
        </button>
      </div>
    </div>
  );
}

