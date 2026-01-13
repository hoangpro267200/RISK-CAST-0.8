import { Leaf, Cloud, Anchor, TrendingUp, Search, Shield } from 'lucide-react';
import type { ModulesState } from './types';

interface IntelligenceModulesProps {
  modules: ModulesState;
  onToggle: (key: keyof ModulesState) => void;
}

export function IntelligenceModules({ modules, onToggle }: IntelligenceModulesProps) {
  const moduleConfig = [
    {
      key: 'esg' as const,
      label: 'ESG Score',
      icon: Leaf,
      description: 'Environmental, Social & Governance',
      gradient: 'from-green-500 to-emerald-500',
    },
    {
      key: 'weather' as const,
      label: 'Weather',
      icon: Cloud,
      description: 'Route weather forecast',
      gradient: 'from-blue-500 to-cyan-500',
    },
    {
      key: 'portCongestion' as const,
      label: 'Port Congestion',
      icon: Anchor,
      description: 'Port delay prediction',
      gradient: 'from-amber-500 to-orange-500',
    },
    {
      key: 'carrierPerformance' as const,
      label: 'Carrier',
      icon: TrendingUp,
      description: 'Carrier reliability score',
      gradient: 'from-purple-500 to-pink-500',
    },
    {
      key: 'marketScanner' as const,
      label: 'Market Scanner',
      icon: Search,
      description: 'Market rate analysis',
      gradient: 'from-indigo-500 to-blue-500',
    },
    {
      key: 'insurance' as const,
      label: 'Insurance',
      icon: Shield,
      description: 'Coverage recommendation',
      gradient: 'from-teal-500 to-cyan-500',
    },
  ];

  return (
    <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-[20px] p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-white font-medium">Intelligence Modules</h3>
          <p className="text-white/40 text-xs mt-1">Select risk analysis components</p>
        </div>
        <div className="text-white/40 text-sm">
          {Object.values(modules).filter(Boolean).length}/6 enabled
        </div>
      </div>

      {/* Module Grid */}
      <div className="grid grid-cols-3 gap-4">
        {moduleConfig.map(({ key, label, icon: Icon, description, gradient }) => {
          const isActive = modules[key];
          
          return (
            <div
              key={key}
              className={`
                relative cursor-pointer rounded-xl p-4 
                border transition-all duration-300
                ${isActive 
                  ? 'bg-white/10 border-white/20' 
                  : 'bg-white/5 border-white/10 opacity-60 hover:opacity-80'
                }
              `}
              onClick={() => onToggle(key)}
            >
              {/* Icon */}
              <div className={`
                w-10 h-10 rounded-xl flex items-center justify-center mb-3
                ${isActive 
                  ? `bg-gradient-to-br ${gradient}` 
                  : 'bg-white/10'
                }
              `}>
                <Icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-white/50'}`} />
              </div>

              {/* Content */}
              <div className="mb-3">
                <div className={`font-medium text-sm ${isActive ? 'text-white' : 'text-white/70'}`}>
                  {label}
                </div>
                <div className="text-white/40 text-xs mt-0.5">{description}</div>
              </div>

              {/* Toggle */}
              <div className={`
                w-10 h-5 rounded-full relative transition-colors duration-200
                ${isActive ? 'bg-cyan-500' : 'bg-white/20'}
              `}>
                <div className={`
                  absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform duration-200
                  ${isActive ? 'translate-x-5' : 'translate-x-0.5'}
                `} />
              </div>

              {/* Active Indicator */}
              {isActive && (
                <div className="absolute top-2 right-2 w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

