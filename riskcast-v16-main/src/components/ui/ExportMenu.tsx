/**
 * ExportMenu Component
 * 
 * Enterprise export dropdown for Results page.
 * Provides PDF, CSV, Excel export and shareable link.
 */

import React, { useState, useRef, useEffect } from 'react';
import { 
  Download, 
  FileText, 
  FileSpreadsheet, 
  Link2, 
  ChevronDown,
  Check,
  Loader2
} from 'lucide-react';

export interface ExportMenuProps {
  onExportPDF: () => Promise<void>;
  onExportCSV: () => Promise<void>;
  onExportExcel: () => Promise<void>;
  onCopyLink: () => Promise<boolean>;
  isExporting?: boolean;
  disabled?: boolean;
  className?: string;
}

type ExportAction = 'pdf' | 'csv' | 'excel' | 'link';

export const ExportMenu: React.FC<ExportMenuProps> = ({
  onExportPDF,
  onExportCSV,
  onExportExcel,
  onCopyLink,
  isExporting = false,
  disabled = false,
  className = ''
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [lastAction, setLastAction] = useState<ExportAction | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  // Close on Escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen]);

  const handleAction = async (action: ExportAction) => {
    setLastAction(action);
    setShowSuccess(false);

    try {
      switch (action) {
        case 'pdf':
          await onExportPDF();
          break;
        case 'csv':
          await onExportCSV();
          break;
        case 'excel':
          await onExportExcel();
          break;
        case 'link':
          const success = await onCopyLink();
          if (success) {
            setShowSuccess(true);
            setTimeout(() => setShowSuccess(false), 2000);
          }
          break;
      }
    } finally {
      if (action !== 'link') {
        setIsOpen(false);
      }
    }
  };

  const menuItems: Array<{
    id: ExportAction;
    label: string;
    description: string;
    icon: React.ReactNode;
  }> = [
    {
      id: 'pdf',
      label: 'Export PDF',
      description: 'Print-friendly report',
      icon: <FileText className="w-4 h-4" />
    },
    {
      id: 'csv',
      label: 'Export CSV',
      description: 'Data for spreadsheets',
      icon: <FileSpreadsheet className="w-4 h-4" />
    },
    {
      id: 'excel',
      label: 'Export Excel',
      description: 'Full workbook format',
      icon: <FileSpreadsheet className="w-4 h-4" />
    },
    {
      id: 'link',
      label: 'Copy Share Link',
      description: 'Share with team members',
      icon: <Link2 className="w-4 h-4" />
    }
  ];

  return (
    <div ref={menuRef} className={`relative ${className}`}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled || isExporting}
        aria-expanded={isOpen}
        aria-haspopup="menu"
        aria-label="Export options"
        className={`
          flex items-center gap-2 px-4 py-2 
          bg-white/5 hover:bg-white/10 
          border border-white/10 hover:border-white/20
          rounded-xl text-sm font-medium text-white/80 hover:text-white
          transition-all duration-200
          focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900
          disabled:opacity-50 disabled:cursor-not-allowed
        `}
      >
        {isExporting ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Download className="w-4 h-4" />
        )}
        <span className="hidden sm:inline">Export</span>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div 
          role="menu"
          aria-orientation="vertical"
          className={`
            absolute right-0 top-full mt-2 w-64 z-50
            bg-slate-800/95 backdrop-blur-xl
            border border-white/10 rounded-xl
            shadow-2xl shadow-black/50
            py-2 overflow-hidden
            animate-in fade-in slide-in-from-top-2 duration-200
          `}
        >
          <div className="px-3 py-2 border-b border-white/10">
            <p className="text-xs font-medium text-white/60 uppercase tracking-wider">
              Export Options
            </p>
          </div>

          {menuItems.map((item) => (
            <button
              key={item.id}
              role="menuitem"
              onClick={() => handleAction(item.id)}
              disabled={isExporting && lastAction === item.id}
              className={`
                w-full flex items-center gap-3 px-3 py-2.5
                hover:bg-white/5 
                transition-colors duration-150
                focus-visible:outline-none focus-visible:bg-white/10
                disabled:opacity-50
              `}
            >
              <div className={`
                w-8 h-8 rounded-lg flex items-center justify-center
                ${item.id === 'pdf' ? 'bg-red-500/10 text-red-400' :
                  item.id === 'csv' ? 'bg-green-500/10 text-green-400' :
                  item.id === 'excel' ? 'bg-emerald-500/10 text-emerald-400' :
                  'bg-blue-500/10 text-blue-400'}
              `}>
                {isExporting && lastAction === item.id ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : showSuccess && lastAction === item.id ? (
                  <Check className="w-4 h-4" />
                ) : (
                  item.icon
                )}
              </div>
              <div className="flex-1 text-left">
                <p className="text-sm font-medium text-white">{item.label}</p>
                <p className="text-xs text-white/50">{item.description}</p>
              </div>
              {showSuccess && lastAction === item.id && (
                <span className="text-xs text-green-400 font-medium">Copied!</span>
              )}
            </button>
          ))}

          <div className="px-3 py-2 border-t border-white/10 mt-1">
            <p className="text-xs text-white/40">
              Exports include current view data
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExportMenu;
