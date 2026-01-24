/**
 * Risk Score Gauge Component
 * Circular gauge displaying risk score percentage
 */

interface RiskScoreGaugeProps {
  score: number; // 0-1 range
  size?: number;
  className?: string;
}

export function RiskScoreGauge({ score, size = 120, className = '' }: RiskScoreGaugeProps) {
  const percentage = Math.round(score * 100);
  const radius = (size - 20) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score * circumference);

  // Color based on score
  let strokeColor = 'rgb(34, 197, 94)'; // green
  if (percentage > 70) strokeColor = 'rgb(239, 68, 68)'; // red
  else if (percentage > 40) strokeColor = 'rgb(251, 191, 36)'; // yellow

  return (
    <div className={`relative inline-flex items-center justify-center ${className}`} style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="rgba(255, 255, 255, 0.1)"
          strokeWidth="8"
          fill="none"
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={strokeColor}
          strokeWidth="8"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="transition-all duration-500"
        />
      </svg>
      {/* Center text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold text-white">{percentage}%</span>
        <span className="text-xs text-white/60 mt-1">Risk Score</span>
      </div>
    </div>
  );
}
