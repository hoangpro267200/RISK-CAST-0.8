import React from 'react';

interface ChartToggleProps {
  activeChart: 'fan' | 'loss';
  onChange: (chart: 'fan' | 'loss') => void;
}

export const ChartToggle: React.FC<ChartToggleProps> = ({ activeChart, onChange }) => {
  return (
    <div className="flex items-center gap-2 p-1 bg-black/40 rounded-lg border border-white/10">
      <button
        type="button"
        onClick={() => onChange('fan')}
        className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
          activeChart === 'fan'
            ? 'bg-white/10 text-white'
            : 'text-gray-400 hover:text-white hover:bg-white/5'
        }`}
      >
        Risk Projections
      </button>
      <button
        type="button"
        onClick={() => onChange('loss')}
        className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
          activeChart === 'loss'
            ? 'bg-white/10 text-white'
            : 'text-gray-400 hover:text-white hover:bg-white/5'
        }`}
      >
        Financial Loss
      </button>
    </div>
  );
};




