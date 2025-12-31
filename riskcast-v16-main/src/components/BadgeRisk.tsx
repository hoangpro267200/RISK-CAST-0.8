import React from 'react';
import type { RiskLevel } from '../types';

interface BadgeRiskProps {
  level: RiskLevel;
  size?: 'sm' | 'md' | 'lg';
}

export const BadgeRisk: React.FC<BadgeRiskProps> = ({ level, size = 'md' }) => {
  const colorMap = {
    LOW: 'bg-green-500/20 text-green-400',
    MEDIUM: 'bg-amber-500/20 text-amber-400',
    HIGH: 'bg-red-500/20 text-red-400',
  };

  const sizeMap = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-3 py-1',
    lg: 'text-base px-4 py-1.5',
  };

  return (
    <span className={`rounded-full font-medium ${colorMap[level]} ${sizeMap[size]}`}>
      {level}
    </span>
  );
};




