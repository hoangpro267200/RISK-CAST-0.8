import React, { useState, useMemo, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { BarChart3, Brain, Shield, ChevronDown, ChevronUp } from 'lucide-react';
import type { LayerData, ScenarioDataPoint, FinancialMetrics, RiskDriverAttribution, LayerTrace } from '../types';
import { GlassCard } from './GlassCard';
import { RiskScenarioFanChart } from './RiskScenarioFanChart';
import { FinancialModule } from './FinancialModule';
import { RiskContributionWaterfall } from './RiskContributionWaterfall';
import { LayersTable } from './LayersTable';
import { ChartToggle } from './ChartToggle';
import { ChartTooltipGlass } from './ChartTooltipGlass';
// EmptyState and LoadingState removed - using inline fallbacks

interface EvidenceLayerProps {
  layers: LayerData[];
  overallScore: number;
  riskScenarioProjections?: ScenarioDataPoint[];
  etd?: string;
  eta?: string;
  drivers?: RiskDriverAttribution[];
  financial?: FinancialMetrics | null;
  traces?: Record<string, LayerTrace>;
  onSelectLayer?: (layerName: string) => void;
}

export function EvidenceLayer({
  layers,
  overallScore,
  riskScenarioProjections,
  etd,
  eta,
  drivers,
  financial,
  traces,
  onSelectLayer,
}: EvidenceLayerProps) {
  const [expanded, setExpanded] = useState(false);
  const [activeChart, setActiveChart] = useState<'fan' | 'loss'>('fan');
  const [chartsReady, setChartsReady] = useState(false);

  // Prepare top drivers for executive summary
  const topDrivers = useMemo(() => {
    if (!drivers || drivers.length === 0) return [];

    return [...drivers]
      .sort((a, b) => b.contributionPct - a.contributionPct)
      .slice(0, 3);
  }, [drivers]);

  useEffect(() => {
    if (expanded) {
      // Delay chart rendering slightly to ensure container dimensions are ready
      const timer = setTimeout(() => setChartsReady(true), 100);
      return () => clearTimeout(timer);
    } else {
      setChartsReady(false);
    }
  }, [expanded]);

  return (
    <div className="space-y-6 mt-12">
      {/* Section Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-white">Evidence Layer</h2>
          <p className="text-white/60 mt-1">Audit trail and supporting data for risk assessment</p>
        </div>

        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors text-white/80"
        >
          {expanded ? (
            <>
              <ChevronUp className="w-4 h-4" />
              Collapse
            </>
          ) : (
            <>
              <ChevronDown className="w-4 h-4" />
              Expand Evidence
            </>
          )}
        </button>
      </div>

      {/* Executive Summary (always visible) */}
      <GlassCard>
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20">
            <Brain className="w-6 h-6 text-blue-400" />
          </div>

          <div className="flex-1">
            <h3 className="text-lg font-medium text-white mb-2">Key Evidence Summary</h3>

            {topDrivers.length > 0 ? (
              <div className="space-y-3">
                <p className="text-white/70">
                  This shipment's risk score of <span className="text-white font-medium">{overallScore}</span> is
                  primarily driven by:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {topDrivers.map((driver) => (
                    <div
                      key={driver.id}
                      className="p-3 rounded-lg bg-white/5 border border-white/10"
                    >
                      <div className="text-sm font-medium text-white">{driver.label}</div>
                      <div className="text-xs text-white/60 mt-1">
                        {driver.contributionPct}% impact • {driver.direction}
                      </div>
                      <div className="text-xs text-white/40 mt-2">
                        {driver.evidence?.note || 'No evidence note available'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-white/60">No driver attribution data available.</p>
            )}
          </div>
        </div>
      </GlassCard>

      {/* Expandable Detailed Evidence */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className="space-y-6 overflow-hidden"
          >
            {/* Chart Toggle */}
            <ChartToggle activeChart={activeChart} onChange={setActiveChart} />

            {/* Charts Container */}
            <GlassCard>
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-purple-500/10 border border-purple-500/20">
                    <BarChart3 className="w-5 h-5 text-purple-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-medium text-white">
                      {activeChart === 'fan' ? 'Risk Scenario Projections' : 'Financial Loss Distribution'}
                    </h3>
                    <p className="text-sm text-white/60">
                      {activeChart === 'fan'
                        ? 'Projected risk evolution with uncertainty bounds'
                        : 'Expected financial impact distribution'}
                    </p>
                  </div>
                </div>

                <div className="relative">
                  <ChartTooltipGlass />

                  <div className="chart-container">
                    {activeChart === 'fan' ? (
                      <div style={{ height: '450px', minHeight: '450px', minWidth: '300px', width: '100%', position: 'relative', display: 'block' }}>
                      {chartsReady ? (
                        riskScenarioProjections && etd && eta ? (
                          <RiskScenarioFanChart data={riskScenarioProjections} etd={etd} eta={eta} />
                        ) : (
                          <div className="h-full flex flex-col items-center justify-center text-white/40 space-y-3">
                            <BarChart3 className="w-12 h-12 text-white/20" />
                            <div className="text-sm">No projection data</div>
                            <div className="text-xs text-white/30">Risk scenario projections are unavailable for this shipment.</div>
                          </div>
                        )
                      ) : (
                        <div className="h-full flex flex-col items-center justify-center text-white/40">
                          <div className="animate-pulse text-sm">Loading chart...</div>
                        </div>
                      )}
                      </div>
                    ) : (
                      <div style={{ height: '450px', minHeight: '450px', minWidth: '300px', width: '100%', position: 'relative', display: 'block' }}>
                        {chartsReady && financial && financial.lossCurve && financial.lossCurve.length > 0 ? (
                          <FinancialModule financial={financial} />
                        ) : (
                          <div className="h-full flex flex-col items-center justify-center text-white/40 space-y-3">
                            <Shield className="w-12 h-12 text-white/20" />
                            <div className="text-sm">Financial data not available</div>
                            <div className="text-xs text-white/30">Loss curve data is required for this view</div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </GlassCard>

            {/* Layer Contribution Waterfall */}
            <RiskContributionWaterfall
              layers={layers}
              overallScore={overallScore}
                  onBarClick={onSelectLayer}
            />

            {/* Layers Table */}
            <LayersTable layers={layers} onSelectLayer={onSelectLayer} />

            {/* Trace metadata (minimal, audit-friendly) */}
            {traces ? (
              <GlassCard>
                <div className="text-sm font-medium text-white mb-3">Trace Metadata (Available)</div>
                <div className="text-xs text-white/60">
                  {Object.keys(traces).length} layer trace(s) available. Click a layer row to open the trace drawer.
                </div>
              </GlassCard>
            ) : null}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}




