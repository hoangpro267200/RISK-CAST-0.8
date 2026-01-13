import { useMemo, useState } from 'react';
import type { LayerData, RiskLevel } from '../types';
import { GlassCard } from './GlassCard';
import { BadgeRisk } from './BadgeRisk';
import { ArrowUpDown } from 'lucide-react';

interface LayersTableProps {
  layers: LayerData[];
  onSelectLayer?: (layerName: string) => void;
}

function getRiskLevel(score: number): RiskLevel {
  if (score < 40) return 'LOW';
  if (score < 70) return 'MEDIUM';
  return 'HIGH';
}

export function LayersTable({ layers, onSelectLayer }: LayersTableProps) {
  const [sortByScoreDesc, setSortByScoreDesc] = useState(true);

  const sortedLayers = useMemo(() => {
    const copy = (layers || []).slice();
    copy.sort((a, b) => {
      const diff = (b.score ?? 0) - (a.score ?? 0);
      return sortByScoreDesc ? diff : -diff;
    });
    return copy;
  }, [layers, sortByScoreDesc]);

  const onRowActivate = (layerName: string) => {
    if (!onSelectLayer) return;
    onSelectLayer(layerName);
  };

  return (
    <GlassCard>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl">Risk Layers Detail</h2>
        <button
          type="button"
          onClick={() => setSortByScoreDesc((v) => !v)}
          className="flex items-center gap-1 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent-primary)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-bg-primary)]"
          aria-label={`Sort by score ${sortByScoreDesc ? 'ascending' : 'descending'}`}
        >
          <ArrowUpDown className="w-4 h-4" />
          Sort
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left py-3 px-4 text-sm font-medium text-[var(--color-text-muted)]">Layer</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-[var(--color-text-muted)]">Contribution</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-[var(--color-text-muted)]">Status</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-[var(--color-text-muted)]">Score</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-[var(--color-text-muted)]">Notes</th>
            </tr>
          </thead>

          <tbody>
            {sortedLayers.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-8 text-center text-white/40">
                  <div className="text-sm">No layer data available</div>
                  <div className="text-xs text-white/30 mt-1">Layer data is required for this table</div>
                </td>
              </tr>
            ) : (
              sortedLayers.map((layer) => {
              const clickable = Boolean(onSelectLayer);
              return (
                <tr
                  key={layer.name}
                  className={`border-b border-white/5 hover:bg-white/5 transition-colors ${clickable ? 'cursor-pointer' : ''}`}
                  role={clickable ? 'button' : undefined}
                  tabIndex={clickable ? 0 : -1}
                  onClick={() => clickable && onRowActivate(layer.name)}
                  onKeyDown={(e) => {
                    if (!clickable) return;
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      onRowActivate(layer.name);
                    }
                  }}
                  aria-label={clickable ? `Open trace for ${layer.name}` : undefined}
                >
                  <td className="py-4 px-4 text-sm font-medium text-white">{layer.name}</td>
                  <td className="py-4 px-4 text-sm text-[var(--color-text-secondary)]">
                    {layer.contribution}%
                  </td>
                  <td className="py-4 px-4">
                    <span
                      className={`text-xs px-2 py-1 rounded-full ${
                        layer.status === 'ALERT'
                          ? 'bg-red-500/20 text-red-400'
                          : layer.status === 'WARNING'
                          ? 'bg-amber-500/20 text-amber-400'
                          : 'bg-green-500/20 text-green-400'
                      }`}
                    >
                      {layer.status}
                    </span>
                  </td>
                  <td className="py-4 px-4 flex items-center">
                    <BadgeRisk level={getRiskLevel(layer.score)} size="sm" />
                    <span className="ml-2 text-sm">{layer.score}</span>
                  </td>
                  <td className="py-4 px-4 text-sm text-[var(--color-text-secondary)]">{layer.notes}</td>
                </tr>
              );
            })
            )}
          </tbody>
        </table>
      </div>
    </GlassCard>
  );
}




