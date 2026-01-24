/**
 * Risk Factors Chart Component
 * Bar chart displaying risk factors
 */

interface RiskFactorsChartProps {
  factors: Record<string, number>;
  className?: string;
}

export function RiskFactorsChart({ factors, className = '' }: RiskFactorsChartProps) {
  const entries = Object.entries(factors)
    .map(([key, value]) => ({
      name: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      value: value * 100, // Convert to percentage
    }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 5); // Top 5 factors

  const maxValue = Math.max(...entries.map(e => e.value), 1);

  return (
    <div className={`space-y-3 ${className}`}>
      {entries.map((factor) => (
        <div key={factor.name} className="space-y-1">
          <div className="flex justify-between text-sm">
            <span className="text-white/80">{factor.name}</span>
            <span className="text-white font-medium">{factor.value.toFixed(1)}%</span>
          </div>
          <div className="h-2 bg-white/10 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500"
              style={{ width: `${(factor.value / maxValue) * 100}%` }}
            />
          </div>
        </div>
      ))}
      {entries.length === 0 && (
        <p className="text-white/50 text-sm text-center py-4">No risk factors available</p>
      )}
    </div>
  );
}
