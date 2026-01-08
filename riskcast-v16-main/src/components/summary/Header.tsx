import { Globe, RefreshCw, CheckCircle, AlertCircle, Clock } from 'lucide-react';
import type { SaveState } from './types';

interface HeaderProps {
  saveState: SaveState;
  lastSaved: Date;
}

export function Header({ saveState, lastSaved }: HeaderProps) {
  const getTimeSince = (date: Date) => {
    const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000);
    if (seconds < 60) return 'just now';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ago`;
  };

  const saveStateConfig = {
    saved: {
      icon: CheckCircle,
      text: 'All changes saved',
      color: 'text-green-400',
      show: true,
    },
    saving: {
      icon: RefreshCw,
      text: 'Saving...',
      color: 'text-cyan-400',
      show: true,
      spin: true,
    },
    unsaved: {
      icon: AlertCircle,
      text: 'Unsaved changes',
      color: 'text-orange-400',
      show: true,
      pulse: true,
    },
    error: {
      icon: AlertCircle,
      text: 'Save failed',
      color: 'text-red-400',
      show: true,
    },
  };

  const config = saveStateConfig[saveState];
  const Icon = config.icon;

  return (
    <header className="sticky top-0 z-50 h-[72px] bg-[#0a1628]/80 backdrop-blur-sm border-b border-white/10">
      <div className="h-full px-12 flex items-center justify-between">
        {/* Logo Section */}
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#00D9FF] to-[#0088FF] flex items-center justify-center">
              <span className="text-xl">⚡</span>
            </div>
            <div>
              <div className="text-white tracking-wide">RISKCAST</div>
              <div className="text-white/50 text-xs">FutureOS</div>
            </div>
          </div>

          {/* Save State Indicator */}
          {config.show && (
            <div className={`flex items-center gap-2 text-sm ${config.color}`}>
              <Icon className={`w-4 h-4 ${config.spin ? 'animate-spin' : ''} ${config.pulse ? 'animate-pulse' : ''}`} />
              <span>{config.text}</span>
            </div>
          )}
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-white/40 text-xs">
            <Clock className="w-3 h-3" />
            <span>Last saved: {getTimeSince(lastSaved)}</span>
          </div>
          <button 
            className="p-2.5 border border-white/10 rounded-lg hover:border-[#00D9FF]/50 transition-all"
            title="Change language"
          >
            <Globe className="w-5 h-5 text-white/70" />
          </button>
          <button 
            className="p-2.5 border border-white/10 rounded-lg hover:border-[#00D9FF]/50 transition-all"
            title="Refresh data"
          >
            <RefreshCw className="w-5 h-5 text-white/70" />
          </button>
        </div>
      </div>
    </header>
  );
}

