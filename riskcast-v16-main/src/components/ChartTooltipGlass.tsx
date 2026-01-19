import React from 'react';

export const ChartTooltipGlass: React.FC = () => {
  return (
    <style>{`
      .recharts-tooltip-wrapper {
        background: rgba(0, 0, 0, 0.9) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(12px) !important;
        padding: 12px !important;
      }
    `}</style>
  );
};




