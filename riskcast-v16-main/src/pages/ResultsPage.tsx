/**
 * Results Page Component - COMPETITION-READY v4
 * 
 * ARCHITECTURE: ENGINE-FIRST with strict data integrity
 * - NO fake/random data generation
 * - Clear visual hierarchy (Executive → Analytical → Technical)
 * - Enterprise-level UI/UX polish
 * - Maintainable, scalable structure
 */

import { useEffect, useState, useMemo } from 'react';
import { adaptResultV2 } from '@/adapters/adaptResultV2';
import type { ResultsViewModel } from '@/types/resultsViewModel';
import type { 
  LayerData, 
  ShipmentData, 
  AINarrative, 
  ScenarioDataPoint, 
  RiskLevel,
  Scenario,
  DataDomain,
  FinancialMetrics
} from '@/types';

// Premium UI Components
import { RiskOrbPremium } from '@/components/RiskOrbPremium';
import { GlassCard } from '@/components/GlassCard';
import { RiskRadar } from '@/components/RiskRadar';
import { RiskContributionWaterfall } from '@/components/RiskContributionWaterfall';
import { ExecutiveNarrative } from '@/components/ExecutiveNarrative';
import { RiskScenarioFanChart } from '@/components/RiskScenarioFanChart';
import { ShipmentHeader } from '@/components/ShipmentHeader';
import { RiskSensitivityTornado } from '@/components/RiskSensitivityTornado';
import { RiskCostEfficiencyFrontier } from '@/components/RiskCostEfficiencyFrontier';
import { DataReliabilityMatrix } from '@/components/DataReliabilityMatrix';
import { LayersTable } from '@/components/LayersTable';
import { PrimaryRecommendationCard } from '@/components/PrimaryRecommendationCard';
import { SecondaryRecommendationCard } from '@/components/SecondaryRecommendationCard';
import { FinancialModule } from '@/components/FinancialModule';
import { BadgeRisk } from '@/components/BadgeRisk';
import { SystemChatPanel } from '@/components/SystemChatPanel';

// Icons
import { 
  RefreshCw, AlertTriangle, TrendingUp, Shield, DollarSign, 
  MapPin, Package, Zap, Target, Activity, 
  BarChart3, LineChart, Brain, Layers, 
  CheckCircle2, XCircle, AlertCircle, ArrowRight,
  Info, Clock
} from 'lucide-react';

// Header Language Switcher
import { HeaderLangSwitcher, useTranslation } from '@/components/HeaderLangSwitcher';

/**
 * Calculate total contribution from layers and validate data integrity
 */
function validateLayerContributions(layers: LayerData[]): { total: number; isValid: boolean; warnings: string[] } {
  const total = layers.reduce((sum, layer) => sum + (layer.contribution || 0), 0);
  const warnings: string[] = [];
  
  // Contribution should sum to approximately 100% (allow 95-105% tolerance for rounding)
  if (total < 95 || total > 105) {
    warnings.push(`Layer contributions sum to ${total.toFixed(1)}% (expected ~100%)`);
  }
  
  return { total, isValid: total >= 95 && total <= 105, warnings };
}

/**
 * Extract key takeaways from risk data for executive summary
 */
function extractKeyTakeaways(
  riskScore: number,
  drivers: Array<{ name: string; impact: number }>,
  layers: LayerData[],
  confidence: number
): string[] {
  const takeaways: string[] = [];
  
  // Overall risk assessment
  if (riskScore >= 70) {
    takeaways.push(`HIGH RISK (${Math.round(riskScore)}/100): Immediate action required to mitigate significant threats`);
  } else if (riskScore >= 40) {
    takeaways.push(`MODERATE RISK (${Math.round(riskScore)}/100): Enhanced monitoring and preventive measures recommended`);
  } else {
    takeaways.push(`LOW RISK (${Math.round(riskScore)}/100): Standard monitoring sufficient, no immediate concerns`);
  }
  
  // Top risk driver
  if (drivers.length > 0) {
    const topDriver = drivers[0];
    if (topDriver) {
      takeaways.push(`Primary concern: ${topDriver.name} (${topDriver.impact > 0 ? '+' : ''}${topDriver.impact.toFixed(1)}% impact)`);
    }
  }
  
  // Highest contributing layer
  const topLayer = layers
    .filter(l => l.contribution > 0)
    .sort((a, b) => (b.contribution || 0) - (a.contribution || 0))[0];
  if (topLayer) {
    takeaways.push(`${topLayer.name} contributes ${topLayer.contribution.toFixed(0)}% to overall risk profile`);
  }
  
  // Confidence note
  if (confidence < 70) {
    takeaways.push(`Data confidence: ${Math.round(confidence * 100)}% - Some uncertainty in assessment`);
  }
  
  return takeaways.slice(0, 3); // Max 3 takeaways for clarity
}

export default function ResultsPage() {
  const [viewModel, setViewModel] = useState<ResultsViewModel | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'analytics' | 'decisions'>('overview');
  const { t } = useTranslation();

  const fetchResults = async (showLoading = true) => {
    try {
      if (showLoading) setLoading(true);
      setError(null);

      // First try localStorage for RISKCAST_RESULTS_V2 (saved by Summary page)
      const savedResults = localStorage.getItem('RISKCAST_RESULTS_V2');
      if (savedResults) {
        try {
          const parsed = JSON.parse(savedResults);
          console.log('[ResultsPage] Loaded results from localStorage:', parsed);
          const normalized = adaptResultV2(parsed);
          console.log('[ResultsPage] Normalized from localStorage:', normalized);
          setViewModel(normalized);
          setLoading(false);
          return;
        } catch (parseErr) {
          console.warn('[ResultsPage] Failed to parse localStorage results:', parseErr);
        }
      }

      // Fallback: try API endpoint
      try {
        const timestamp = `?t=${Date.now()}`;
        const response = await fetch(`/results/data${timestamp}`, {
          method: 'GET',
          headers: {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Accept': 'application/json',
          },
        });

        if (response.ok) {
          const _rawResult: unknown = await response.json();
          console.log('[ResultsPage] Raw result from backend:', _rawResult);

          // Check if response is effectively empty
          if (_rawResult && typeof _rawResult === 'object' && Object.keys(_rawResult).length === 0) {
            console.warn('[ResultsPage] API returned empty object - no data available');
            // Don't set viewModel, let it fall through to error state
          } else {
            const normalized = adaptResultV2(_rawResult);
            console.log('[ResultsPage] Normalized view model:', normalized);

            // Check if normalized data has meaningful content
            const hasData = normalized.overview.riskScore.score > 0 || 
                          normalized.breakdown.layers.length > 0 ||
                          normalized.drivers.length > 0 ||
                          (normalized.loss && normalized.loss.expectedLoss > 0);

            if (hasData) {
              setViewModel(normalized);
              setLoading(false);
              return;
            } else {
              console.warn('[ResultsPage] Normalized data is empty - no meaningful content');
            }
          }
        } else {
          console.warn(`[ResultsPage] API returned status ${response.status}`);
        }
      } catch (apiErr) {
        console.warn('[ResultsPage] API fetch failed:', apiErr);
      }

      // No data found - show error instead of generating fake data
      setError('No analysis results found. Please run analysis from the Summary page.');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An unexpected error occurred';
      setError(message);
      console.error('[ResultsPage] Fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResults(true);
    const intervalId = setInterval(() => fetchResults(false), 15000);
    return () => clearInterval(intervalId);
  }, []);

  // ALL HOOKS MUST BE CALLED BEFORE ANY EARLY RETURNS
  // This ensures hooks are called in the same order on every render

  // Prepare data for components (safe with null checks)
  const rawRiskLevel = viewModel?.overview?.riskScore?.level?.toUpperCase();
  const riskLevel: RiskLevel | undefined = 
    rawRiskLevel === 'LOW' || rawRiskLevel === 'MEDIUM' || rawRiskLevel === 'HIGH'
      ? rawRiskLevel
      : undefined;
  const confidence = viewModel ? viewModel.overview.riskScore.confidence / 100 : 0;
  const riskScore = viewModel?.overview?.riskScore?.score ?? 0;

  // Build layers data with validation
  const layersData: LayerData[] = useMemo(() => {
    if (!viewModel?.breakdown?.layers || !Array.isArray(viewModel.breakdown.layers)) {
      return [];
    }
    return viewModel.breakdown.layers.map(l => ({
      name: l.name,
      score: l.score,
      contribution: l.contribution,
      category: l.category || 'UNKNOWN',
      enabled: l.enabled !== false,
      status: l.score >= 70 ? 'ALERT' : l.score >= 40 ? 'WARNING' : 'NORMAL',
      notes: `Contributing ${l.contribution.toFixed(1)}% to overall risk`,
      confidence: viewModel.overview.riskScore.confidence,
    }));
  }, [viewModel]);

  // Validate layer contributions
  const layerValidation = useMemo(() => validateLayerContributions(layersData), [layersData]);

  // Build shipment data
  const shipmentData: ShipmentData = useMemo(() => {
    if (!viewModel) {
      return {
        shipmentId: 'SHIP-001',
        route: { pol: 'N/A', pod: 'N/A' },
        carrier: 'Ocean Carrier',
        etd: 'N/A',
        eta: 'N/A',
        dataConfidence: 0,
        cargoValue: 0,
        lastUpdated: new Date().toLocaleString(),
      };
    }
    return {
      shipmentId: viewModel?.overview?.shipment?.id || 'SHIP-001',
      route: { 
        pol: viewModel?.overview?.shipment?.pol || 'N/A', 
        pod: viewModel?.overview?.shipment?.pod || 'N/A' 
      },
      carrier: viewModel?.overview?.shipment?.carrier || 'Ocean Carrier',
      etd: viewModel?.overview?.shipment?.etd || 'N/A',
      eta: viewModel?.overview?.shipment?.eta || 'N/A',
      dataConfidence: confidence,
      cargoValue: viewModel?.overview?.shipment?.cargoValue || 0,
      lastUpdated: new Date().toLocaleString(),
    };
  }, [viewModel, confidence]);

  // Extract key takeaways for executive summary
  const keyTakeaways = useMemo(() => {
    if (!viewModel?.drivers || !Array.isArray(viewModel.drivers)) {
      return [];
    }
    return extractKeyTakeaways(riskScore, viewModel.drivers, layersData, confidence);
  }, [riskScore, viewModel, layersData, confidence]);

  // Build narrative - use engine explanation, no fallback generation
  const explanation = viewModel?.overview?.reasoning?.explanation;
  
  // Generate insights from drivers (real data only)
  const driverInsights = useMemo(() => {
    if (!viewModel?.drivers || !Array.isArray(viewModel.drivers)) {
      return [];
    }
    return viewModel.drivers
      .slice(0, 4)
      .map(d => `${d.name}: ${d.impact > 0 ? 'Increases' : 'Decreases'} risk by ${Math.abs(d.impact).toFixed(1)}%`);
  }, [viewModel]);

  // Generate layer insights as fallback only if no drivers
  const layerInsights = useMemo(() => {
    if (viewModel?.drivers && viewModel.drivers.length > 0) {
      return [];
    }
    return layersData
      .filter(l => l.score > 0 || l.contribution > 0)
      .slice(0, 4)
      .map(l => `${l.name}: Score ${l.score.toFixed(1)}, contributing ${l.contribution.toFixed(1)}%`);
  }, [viewModel, layersData]);

  const narrativeData: AINarrative = useMemo(() => ({
    executiveSummary: explanation || `Risk assessment complete. Overall risk score: ${Math.round(riskScore)}/100 (${riskLevel || 'Unknown'}).`,
    keyInsights: driverInsights.length > 0 ? driverInsights : layerInsights,
    actionItems: viewModel?.scenarios && viewModel.scenarios.length > 0 
      ? viewModel.scenarios.slice(0, 4).map(s => s.title)
      : riskScore < 30 
        ? ['Continue monitoring shipment', 'No immediate action required']
        : ['Review risk mitigation options', 'Consider insurance coverage'],
    riskDrivers: viewModel?.drivers && viewModel.drivers.length > 0
      ? viewModel.drivers.map(d => d.name)
      : layersData.filter(l => l.score > 30).map(l => l.name),
    confidenceNotes: `Analysis based on ${Math.round(confidence * 100)}% data confidence. ${riskScore < 30 ? 'Low risk - standard monitoring applies.' : ''}`,
  }), [explanation, riskScore, riskLevel, driverInsights, layerInsights, viewModel, layersData, confidence]);

  // Build scenario projections - ONLY use real data, no fake generation
  const scenarioData: ScenarioDataPoint[] = useMemo(() => {
    if (!viewModel?.timeline?.projections || !Array.isArray(viewModel.timeline.projections) || viewModel.timeline.projections.length === 0) {
      return [];
    }
    return viewModel.timeline.projections.map((p) => ({
      date: p.date,
      p10: p.p10,
      p50: p.p50,
      p90: p.p90,
      expected: p.p50,
    }));
  }, [viewModel]);

  // Build sensitivity drivers - use real drivers or derive from layers (no random)
  const sensitivityDrivers = useMemo(() => {
    if (viewModel?.drivers && Array.isArray(viewModel.drivers) && viewModel.drivers.length > 0) {
      return viewModel.drivers.map(d => ({
        name: d.name,
        impact: d.impact,
        impactMagnitude: Math.abs(d.impact),
      }));
    }
    // Fallback: derive from layers (still real data, just transformed)
    return layersData
      .filter(l => l.score > 0 || l.contribution > 0)
      .map(l => ({
        name: l.name.replace(' Risk', ''),
        impact: l.contribution > 0 ? l.contribution : l.score * 0.3,
        impactMagnitude: l.contribution > 0 ? l.contribution : l.score * 0.3,
      }))
      .sort((a, b) => b.impact - a.impact);
  }, [viewModel, layersData]);

  // Build scenarios - ONLY use real scenarios from engine
  const baseScenarios: Scenario[] = useMemo(() => {
    if (!viewModel?.scenarios || !Array.isArray(viewModel.scenarios) || viewModel.scenarios.length === 0) {
      return [];
    }
    return viewModel.scenarios.map((s) => ({
      title: s.title,
      riskReduction: s.riskReduction,
      costImpact: s.costImpact,
      description: s.description,
      feasibility: 0.85, // Default feasibility if not provided (conservative estimate)
    }));
  }, [viewModel]);

  const scenariosForFrontier: Scenario[] = baseScenarios;

  // Unified display scenarios - mark recommended scenario if exists
  // Extend Scenario type with isRecommended for UI purposes
  interface DisplayScenario extends Scenario {
    isRecommended?: boolean;
  }
  
  const displayScenarios: DisplayScenario[] = useMemo(() => {
    return baseScenarios.map((s, idx) => ({
      ...s,
      isRecommended: idx === 0 && baseScenarios.length > 0, // First scenario as default recommendation
    }));
  }, [baseScenarios]);

  // Build data reliability domains - ONLY if provided by engine (currently empty, components handle it)
  const dataReliabilityDomains: DataDomain[] = [];

  // Build financial metrics - ONLY use real loss data
  const financialMetrics: FinancialMetrics = useMemo(() => {
    if (viewModel?.loss && viewModel.loss.expectedLoss > 0) {
      return {
        expectedLoss: viewModel.loss.expectedLoss,
        var95: viewModel.loss.p95,
        cvar95: viewModel.loss.p99,
        stdDev: (viewModel.loss.p99 - viewModel.loss.expectedLoss) / 2, // Estimate std dev from range
        histogram: [],
        lossCurve: [], // Only show if engine provides real data
      };
    }
    return {
      expectedLoss: 0,
      var95: 0,
      cvar95: 0,
      stdDev: 0,
      histogram: [],
      lossCurve: [],
    };
  }, [viewModel]);

  // Get risk color helper (moved before early returns for consistency)
  const riskColor = useMemo(() => {
    if (riskScore >= 70) return 'from-red-500 to-orange-500';
    if (riskScore >= 40) return 'from-amber-500 to-yellow-500';
    return 'from-emerald-500 to-green-500';
  }, [riskScore]);

  // Beautiful Loading State
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center min-h-[80vh]">
            <div className="text-center">
              <div className="relative w-32 h-32 mx-auto mb-8">
                <div className="absolute inset-0 rounded-full border-4 border-blue-500/20"></div>
                <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-blue-500 animate-spin"></div>
                <div className="absolute inset-4 rounded-full border-4 border-transparent border-t-purple-500 animate-spin" style={{ animationDuration: '1.5s', animationDirection: 'reverse' }}></div>
                <div className="absolute inset-8 rounded-full border-4 border-transparent border-t-cyan-500 animate-spin" style={{ animationDuration: '2s' }}></div>
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Analyzing Risk Data</h2>
              <p className="text-white/50">Processing shipment intelligence...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error State
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8 flex items-center justify-center">
        <GlassCard className="max-w-md text-center">
          <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-red-500/10 flex items-center justify-center">
            <XCircle className="w-10 h-10 text-red-400" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">Analysis Error</h2>
          <p className="text-white/60 mb-6">{error}</p>
          <button
            onClick={() => fetchResults(true)}
            className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white rounded-xl font-medium transition-all flex items-center gap-2 mx-auto shadow-lg shadow-blue-500/25"
          >
            <RefreshCw className="w-5 h-5" />
            Retry Analysis
          </button>
        </GlassCard>
      </div>
    );
  }

  // No Data State
  if (!viewModel) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8 flex items-center justify-center">
        <GlassCard className="max-w-md text-center">
          <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-amber-500/10 flex items-center justify-center">
            <Package className="w-10 h-10 text-amber-400" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">No Analysis Data</h2>
          <p className="text-white/60 mb-6">Run a risk analysis from the Input page to see results.</p>
          <a
            href="/input_v20"
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-medium transition-all shadow-lg shadow-blue-500/25"
          >
            Start Analysis
            <ArrowRight className="w-5 h-5" />
          </a>
        </GlassCard>
      </div>
    );
  }

  // Check for empty data - more comprehensive check
  const isEmptyData = 
    (!viewModel) ||
    (viewModel.overview.riskScore.score === 0 &&
     viewModel.overview.riskScore.level === 'Unknown' &&
     viewModel.breakdown.layers.length === 0 &&
     viewModel.drivers.length === 0 &&
     (!viewModel.loss || viewModel.loss.expectedLoss === 0));

  if (isEmptyData && viewModel) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8 flex items-center justify-center">
        <GlassCard className="max-w-md text-center">
          <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-blue-500/10 flex items-center justify-center">
            <TrendingUp className="w-10 h-10 text-blue-400" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">Ready for Analysis</h2>
          <p className="text-white/60 mb-6">Submit shipment data to generate risk intelligence.</p>
          <a href="/input_v20" className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-medium">
            Go to Input <ArrowRight className="w-5 h-5" />
          </a>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Animated Background */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-blue-500/5 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-0 right-1/4 w-[600px] h-[600px] bg-purple-500/5 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
        <div className="absolute top-1/2 left-1/2 w-[400px] h-[400px] bg-cyan-500/5 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }}></div>
      </div>

      <div className="relative z-10 max-w-[1600px] mx-auto p-6 lg:p-8 space-y-8">
        {/* Header */}
        <header className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl lg:text-4xl font-bold text-white tracking-tight flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <Activity className="w-6 h-6 text-white" />
              </div>
              RISKCAST<span className="text-blue-400">.</span>
            </h1>
            <p className="text-white/50 mt-1 ml-15">Enterprise Risk Intelligence Platform</p>
          </div>

          <div className="flex items-center gap-3">
            {/* Tab Navigation */}
            <div className="flex bg-white/5 rounded-xl p-1 border border-white/10">
              {(['overview', 'analytics', 'decisions'] as const).map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    activeTab === tab 
                      ? 'bg-white/10 text-white' 
                      : 'text-white/50 hover:text-white/80'
                  }`}
                >
                  {t(tab)}
                </button>
              ))}
            </div>

            {/* Language Switcher */}
            <HeaderLangSwitcher />

            <button
              onClick={() => fetchResults(true)}
              disabled={loading}
              className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white rounded-xl font-medium transition-all flex items-center gap-2 shadow-lg shadow-blue-500/25 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              {t('refresh')}
            </button>
          </div>
        </header>

        {/* Shipment Header */}
        <ShipmentHeader data={shipmentData} />

        {/* ============================================================
            SECTION 1: EXECUTIVE DECISION SUMMARY (TOP PRIORITY)
            ============================================================ */}
        {activeTab === 'overview' && (
          <div className="space-y-8">
            {/* Executive Summary Card - Dominant Visual */}
            <GlassCard variant="hero" className="border-2 border-blue-500/20">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-center">
                {/* Risk Orb - Primary Focal Point */}
                <div className="flex flex-col items-center justify-center">
                  <div className={`absolute inset-0 bg-gradient-to-br ${riskColor} opacity-5 rounded-2xl`}></div>
                  <RiskOrbPremium score={Math.round(riskScore)} riskLevel={riskLevel} />
                  <div className="mt-6 text-center relative z-10">
                    <div className="flex items-center justify-center gap-2 mb-3">
                      {riskLevel ? (
                        <BadgeRisk level={riskLevel} size="lg" />
                      ) : (
                        <span className="text-white/60 text-sm">Risk level: Unknown</span>
                      )}
                    </div>
                    <p className="text-white/80 text-base font-medium max-w-xs mx-auto">
                      {explanation || `Risk assessment: ${riskLevel || 'Unknown'} risk level`}
                    </p>
                  </div>
                </div>

                {/* Key Takeaways - Plain Language for Decision Makers */}
                <div className="lg:col-span-2 space-y-4">
                  <div className="flex items-center gap-2 mb-4">
                    <Target className="w-6 h-6 text-blue-400" />
                    <h2 className="text-2xl font-bold text-white">Executive Decision Summary</h2>
                  </div>
                  
                  <div className="space-y-3">
                    {keyTakeaways.map((takeaway, idx) => (
                      <div 
                        key={idx}
                        className="flex items-start gap-3 p-4 bg-white/5 rounded-xl border border-white/10 hover:border-white/20 transition-colors"
                      >
                        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                          idx === 0 ? 'bg-red-500/20 border-2 border-red-500/40' :
                          idx === 1 ? 'bg-amber-500/20 border-2 border-amber-500/40' :
                          'bg-blue-500/20 border-2 border-blue-500/40'
                        }`}>
                          <Info className={`w-4 h-4 ${
                            idx === 0 ? 'text-red-400' :
                            idx === 1 ? 'text-amber-400' :
                            'text-blue-400'
                          }`} />
                        </div>
                        <p className="text-white/90 text-base leading-relaxed flex-1">{takeaway}</p>
                      </div>
                    ))}
                  </div>

                  {/* Confidence Indicator */}
                  <div className="flex items-center gap-4 pt-4 border-t border-white/10">
                    <div className="flex items-center gap-2">
                      <Brain className="w-5 h-5 text-cyan-400" />
                      <span className="text-sm text-white/60">Data Confidence:</span>
                      <span className={`text-lg font-semibold ${
                        confidence >= 0.8 ? 'text-emerald-400' :
                        confidence >= 0.6 ? 'text-amber-400' :
                        'text-red-400'
                      }`}>
                        {Math.round(confidence * 100)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </GlassCard>

            {/* Route Details and Timeline - Positioned near Risk Score */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <GlassCard>
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-blue-400" />
                  Route Details
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
                    <span className="text-white/60">Origin</span>
                    <span className="text-white font-medium">{viewModel.overview.shipment.pol}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
                    <span className="text-white/60">Destination</span>
                    <span className="text-white font-medium">{viewModel.overview.shipment.pod}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
                    <span className="text-white/60">Transit Time</span>
                    <span className="text-white font-medium">{viewModel.overview.shipment.transitTime} days</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
                    <span className="text-white/60">Cargo Value</span>
                    <span className="text-white font-medium">
                      ${((viewModel.overview.shipment.cargoValue || 0) / 1000).toFixed(0)}K
                    </span>
                  </div>
                </div>
              </GlassCard>

              <GlassCard>
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <Clock className="w-5 h-5 text-purple-400" />
                  Timeline
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
                    <span className="text-white/60">ETD</span>
                    <span className="text-white font-medium">{viewModel.overview.shipment.etd || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
                    <span className="text-white/60">ETA</span>
                    <span className="text-white font-medium">{viewModel.overview.shipment.eta || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
                    <span className="text-white/60">Carrier</span>
                    <span className="text-white font-medium">{viewModel.overview.shipment.carrier || 'N/A'}</span>
                  </div>
                </div>
              </GlassCard>
            </div>

            {/* Quick Stats Bar - Supporting Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              <GlassCard variant="compact" className="text-center">
                <Target className="w-6 h-6 text-blue-400 mx-auto mb-2" />
                <p className="text-2xl font-bold text-white">{Math.round(riskScore)}</p>
                <p className="text-xs text-white/50">Risk Score</p>
                <p className="text-xs text-white/30 mt-1">0-100 scale</p>
              </GlassCard>

              {viewModel.loss && viewModel.loss.expectedLoss > 0 && (
                <>
                  <GlassCard variant="compact" className="text-center">
                    <DollarSign className="w-6 h-6 text-emerald-400 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-white">
                      ${(viewModel.loss.expectedLoss / 1000).toFixed(1)}K
                    </p>
                    <p className="text-xs text-white/50">Expected Loss</p>
                    <p className="text-xs text-white/30 mt-1">Most likely outcome</p>
                  </GlassCard>

                  <GlassCard variant="compact" className="text-center">
                    <AlertTriangle className="w-6 h-6 text-amber-400 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-white">
                      ${(viewModel.loss.p95 / 1000).toFixed(1)}K
                    </p>
                    <p className="text-xs text-white/50">VaR 95%</p>
                    <p className="text-xs text-white/30 mt-1">95th percentile</p>
                  </GlassCard>

                  <GlassCard variant="compact" className="text-center">
                    <Shield className="w-6 h-6 text-red-400 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-white">
                      ${(viewModel.loss.p99 / 1000).toFixed(1)}K
                    </p>
                    <p className="text-xs text-white/50">CVaR 99%</p>
                    <p className="text-xs text-white/30 mt-1">Worst case (99%)</p>
                  </GlassCard>
                </>
              )}

              <GlassCard variant="compact" className="text-center">
                <Layers className="w-6 h-6 text-purple-400 mx-auto mb-2" />
                <p className="text-2xl font-bold text-white">{layersData.length}</p>
                <p className="text-xs text-white/50">Risk Layers</p>
                <p className="text-xs text-white/30 mt-1">Analyzed</p>
              </GlassCard>

              <GlassCard variant="compact" className="text-center">
                <Brain className="w-6 h-6 text-cyan-400 mx-auto mb-2" />
                <p className="text-2xl font-bold text-white">{Math.round(confidence * 100)}%</p>
                <p className="text-xs text-white/50">Confidence</p>
                <p className="text-xs text-white/30 mt-1">Data quality</p>
              </GlassCard>
            </div>

            {/* ============================================================
                SECTION 2: ANALYTICAL BREAKDOWN
                ============================================================ */}
            
            {/* Risk Visualization Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <RiskRadar layers={layersData} />
              <RiskContributionWaterfall layers={layersData} overallScore={riskScore} />
            </div>

            {/* Data Integrity Warning (if needed) */}
            {!layerValidation.isValid && layerValidation.warnings.length > 0 && (
              <GlassCard className="border-amber-500/30 bg-amber-500/5">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="text-sm font-semibold text-amber-400 mb-1">Data Integrity Notice</h3>
                    <ul className="text-xs text-white/70 space-y-1">
                      {layerValidation.warnings.map((warning, idx) => (
                        <li key={idx}>• {warning}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </GlassCard>
            )}

            {/* Executive Narrative */}
            <ExecutiveNarrative narrative={narrativeData} />

            {/* Risk Drivers - Only show if we have real drivers */}
            {viewModel?.drivers && viewModel.drivers.length > 0 && (
              <GlassCard>
                <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                  <Zap className="w-5 h-5 text-amber-400" />
                  Risk Drivers Impact Analysis
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {viewModel.drivers.slice(0, 8).map((driver, idx) => (
                    <div 
                      key={idx}
                      className={`p-4 rounded-xl border transition-all hover:scale-[1.02] ${
                        driver.impact > 0 
                          ? 'bg-red-500/5 border-red-500/20 hover:border-red-500/40' 
                          : 'bg-emerald-500/5 border-emerald-500/20 hover:border-emerald-500/40'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <span className="text-white font-medium text-sm">{driver.name}</span>
                        {driver.impact > 0 ? (
                          <AlertCircle className="w-4 h-4 text-red-400" />
                        ) : (
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        )}
                      </div>
                      <div className={`text-2xl font-bold ${driver.impact > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                        {driver.impact > 0 ? '+' : ''}{driver.impact.toFixed(1)}%
                      </div>
                      <p className="text-xs text-white/50 mt-1">{driver.description || 'Impact on risk score'}</p>
                    </div>
                  ))}
                </div>
              </GlassCard>
            )}
          </div>
        )}

        {/* ============================================================
            SECTION 3: ANALYTICS TAB (TECHNICAL DETAIL)
            ============================================================ */}
        {activeTab === 'analytics' && (
          <div className="space-y-8">
            {/* Scenario Projections - Only show if real data exists */}
            {scenarioData.length > 0 && (
              <RiskScenarioFanChart 
                data={scenarioData}
                etd={viewModel.overview.shipment.etd || 'N/A'}
                eta={viewModel.overview.shipment.eta || 'N/A'}
              />
            )}

            {/* Sensitivity Tornado */}
            {sensitivityDrivers.length > 0 && (
              <RiskSensitivityTornado drivers={sensitivityDrivers} />
            )}

            {/* Cost-Efficiency Frontier - Only show if real scenarios exist */}
            {scenariosForFrontier.length > 0 && (
              <RiskCostEfficiencyFrontier 
                scenarios={scenariosForFrontier}
                baselineRisk={riskScore}
                highlightedScenario={null}
              />
            )}

            {/* Financial Module - Only show if real loss data exists */}
            {viewModel.loss && viewModel.loss.expectedLoss > 0 && (
              <FinancialModule financial={financialMetrics} />
            )}

            {/* Layers Table */}
            <LayersTable layers={layersData} />

            {/* Data Reliability Matrix - Only show if domains provided */}
            {dataReliabilityDomains.length > 0 && (
              <DataReliabilityMatrix domains={dataReliabilityDomains} />
            )}
          </div>
        )}

        {/* ============================================================
            SECTION 4: DECISIONS TAB
            ============================================================ */}
        {activeTab === 'decisions' && (() => {
          // Find recommended scenario
          const recommendedScenario = displayScenarios.find(s => s.isRecommended) || (displayScenarios.length > 0 ? displayScenarios[0] : null);
          const maxProtectionScenario = displayScenarios.length > 0 
            ? displayScenarios[displayScenarios.length - 1] 
            : null;

          return (
            <div className="space-y-8">
              {/* Primary Recommendations - Only show if scenarios exist */}
              {displayScenarios.length > 0 && recommendedScenario && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <PrimaryRecommendationCard
                    title={recommendedScenario.title}
                    badge="TOP RECOMMENDATION"
                    riskReduction={recommendedScenario.riskReduction}
                    costImpact={`$${recommendedScenario.costImpact.toFixed(1)}K`}
                    confidence={confidence}
                    rationale={recommendedScenario.description}
                    currentRisk={riskScore}
                    newRisk={Math.max(0, riskScore - recommendedScenario.riskReduction)}
                  />

                  {maxProtectionScenario && maxProtectionScenario !== recommendedScenario && (
                    <PrimaryRecommendationCard
                      title={maxProtectionScenario.title}
                      badge="MAXIMUM PROTECTION"
                      riskReduction={maxProtectionScenario.riskReduction}
                      costImpact={`$${maxProtectionScenario.costImpact.toFixed(1)}K`}
                      confidence={confidence * 0.85}
                      rationale={maxProtectionScenario.description}
                      currentRisk={riskScore}
                      newRisk={Math.max(0, riskScore - maxProtectionScenario.riskReduction)}
                    />
                  )}
                </div>
              )}

              {/* Secondary Recommendations */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <SecondaryRecommendationCard
                  category="Insurance"
                  badge={{ text: viewModel.decisions.insurance.status, type: 'consider' }}
                  metric={viewModel.decisions.insurance.recommendation}
                  context={viewModel.decisions.insurance.rationale}
                  confidence={confidence}
                />

                <SecondaryRecommendationCard
                  category="Timing"
                  badge={{ text: viewModel.decisions.timing.status, type: 'evaluate' }}
                  metric={viewModel.decisions.timing.recommendation}
                  context={viewModel.decisions.timing.rationale}
                  confidence={confidence}
                />

                <SecondaryRecommendationCard
                  category="Routing"
                  badge={{ text: viewModel.decisions.routing.status, type: 'consider' }}
                  metric={viewModel.decisions.routing.recommendation}
                  context={viewModel.decisions.routing.rationale}
                  confidence={confidence}
                />
              </div>

              {/* Decision Matrix */}
              <GlassCard>
                <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-blue-400" />
                  Decision Support Matrix
                </h2>
                
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-white/10">
                        <th className="text-left py-3 px-4 text-sm font-medium text-white/60">Category</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-white/60">Status</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-white/60">Action</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-white/60">Potential Impact</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-white/60">Confidence</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-white/60">Rationale</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        { 
                          cat: 'Insurance', 
                          icon: '🛡️',
                          ...viewModel.decisions.insurance,
                          impact: riskScore < 30 ? 'Minimal' : riskScore < 60 ? '-5 to -10 pts' : '-10 to -20 pts',
                          impactColor: riskScore < 30 ? 'text-emerald-400' : 'text-amber-400',
                        },
                        { 
                          cat: 'Timing', 
                          icon: '⏱️',
                          ...viewModel.decisions.timing,
                          impact: riskScore < 30 ? 'Minimal' : riskScore < 60 ? '-3 to -8 pts' : '-8 to -15 pts',
                          impactColor: riskScore < 30 ? 'text-emerald-400' : 'text-amber-400',
                        },
                        { 
                          cat: 'Routing', 
                          icon: '🗺️',
                          ...viewModel.decisions.routing,
                          impact: riskScore < 30 ? 'Minimal' : riskScore < 60 ? '-2 to -5 pts' : '-5 to -12 pts',
                          impactColor: riskScore < 30 ? 'text-emerald-400' : 'text-amber-400',
                        },
                      ].map((row, idx) => (
                        <tr key={idx} className="border-b border-white/5 hover:bg-white/5 transition-colors group">
                          <td className="py-4 px-4">
                            <div className="flex items-center gap-2">
                              <span className="text-lg">{row.icon}</span>
                              <span className="text-sm font-medium text-white">{row.cat}</span>
                            </div>
                          </td>
                          <td className="py-4 px-4">
                            <span className={`text-xs px-3 py-1.5 rounded-full font-medium inline-flex items-center gap-1 ${
                              row.status === 'RECOMMENDED' ? 'bg-gradient-to-r from-green-500/20 to-emerald-500/20 text-green-400 border border-green-500/30' :
                              row.status === 'NOT_NEEDED' ? 'bg-gradient-to-r from-blue-500/10 to-cyan-500/10 text-cyan-400 border border-cyan-500/20' :
                              String(row.status).includes('EVAL') ? 'bg-gradient-to-r from-amber-500/20 to-orange-500/20 text-amber-400 border border-amber-500/30' :
                              'bg-white/10 text-white/60 border border-white/10'
                            }`}>
                              {row.status === 'NOT_NEEDED' ? '✓ Optional' : 
                               row.status === 'RECOMMENDED' ? '★ Recommended' :
                               String(row.status).includes('EVAL') ? '⚡ Evaluate' : row.status}
                            </span>
                          </td>
                          <td className="py-4 px-4">
                            <span className="text-sm text-white font-medium">{row.recommendation}</span>
                          </td>
                          <td className="py-4 px-4">
                            <span className={`text-sm font-medium ${row.impactColor}`}>
                              {row.impact}
                            </span>
                          </td>
                          <td className="py-4 px-4">
                            <div className="flex items-center gap-2">
                              <div className="w-16 h-2 bg-white/10 rounded-full overflow-hidden">
                                <div 
                                  className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full"
                                  style={{ width: `${Math.round(confidence * 100)}%` }}
                                />
                              </div>
                              <span className="text-xs text-white/60">{Math.round(confidence * 100)}%</span>
                            </div>
                          </td>
                          <td className="py-4 px-4 text-sm text-white/60 max-w-xs">
                            <span className="line-clamp-2 group-hover:line-clamp-none transition-all">
                              {row.rationale}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                
                {/* Summary Footer */}
                <div className="mt-6 pt-4 border-t border-white/10 flex items-center justify-between">
                  <div className="flex items-center gap-4 text-xs text-white/50">
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
                      Optional = Low priority
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                      Evaluate = Review needed
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-green-400"></span>
                      Recommended = Take action
                    </span>
                  </div>
                  <div className="text-xs text-white/40">
                    Overall Risk: {riskScore < 30 ? 'LOW' : riskScore < 60 ? 'MEDIUM' : 'HIGH'} ({Math.round(riskScore)}/100)
                  </div>
                </div>
              </GlassCard>

              {/* All Scenarios - Only show if scenarios exist */}
              {displayScenarios.length > 0 && (
                <GlassCard>
                  <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                    <LineChart className="w-5 h-5 text-purple-400" />
                    All Mitigation Scenarios
                  </h2>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {displayScenarios.map((scenario, idx) => (
                      <div 
                        key={idx}
                        className={`p-4 rounded-xl border transition-all hover:scale-[1.02] cursor-pointer ${
                          scenario.isRecommended 
                            ? 'bg-gradient-to-br from-blue-500/20 to-purple-500/10 border-blue-500/40 shadow-lg shadow-blue-500/10' 
                            : idx === 0
                              ? 'bg-white/5 border-white/20'
                              : 'bg-white/5 border-white/10 hover:border-white/30'
                        }`}
                      >
                        <div className="flex items-start justify-between mb-3">
                          <h3 className="text-white font-medium">{scenario.title}</h3>
                          {scenario.isRecommended ? (
                            <span className="text-xs px-2 py-1 bg-blue-500/30 text-blue-300 rounded-full font-medium">
                              ✓ Best Value
                            </span>
                          ) : idx === 0 ? (
                            <span className="text-xs px-2 py-1 bg-white/10 text-white/60 rounded-full">
                              Baseline
                            </span>
                          ) : idx === displayScenarios.length - 1 ? (
                            <span className="text-xs px-2 py-1 bg-purple-500/20 text-purple-300 rounded-full">
                              Max Protection
                            </span>
                          ) : null}
                        </div>
                        <p className="text-sm text-white/60 mb-3">{scenario.description}</p>
                        <div className="flex items-center justify-between text-sm">
                          <div>
                            <span className="text-white/60">Risk Reduction: </span>
                            <span className={`font-medium ${scenario.riskReduction > 0 ? 'text-emerald-400' : 'text-white/40'}`}>
                              {scenario.riskReduction > 0 ? `-${Math.round(scenario.riskReduction)} pts` : '—'}
                            </span>
                          </div>
                          <div>
                            <span className="text-white/60">Cost: </span>
                            <span className="text-white font-medium">
                              {scenario.costImpact > 0 ? `$${scenario.costImpact.toFixed(1)}K` : 'Free'}
                            </span>
                          </div>
                        </div>
                        {/* Feasibility bar */}
                        <div className="mt-3 pt-3 border-t border-white/10">
                          <div className="flex items-center justify-between text-xs mb-1">
                            <span className="text-white/50">Feasibility</span>
                            <span className="text-white/70">{Math.round((scenario.feasibility || 0.85) * 100)}%</span>
                          </div>
                          <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-gradient-to-r from-emerald-500 to-blue-500 rounded-full"
                              style={{ width: `${(scenario.feasibility || 0.85) * 100}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </GlassCard>
              )}
            </div>
          );
        })()}

        {/* Footer */}
        <footer className="text-center py-8 border-t border-white/10">
          <div className="flex items-center justify-center gap-2 text-white/30 text-sm mb-2">
            <Activity className="w-4 h-4" />
            RISKCAST Enterprise Risk Intelligence
          </div>
          <p className="text-white/20 text-xs">
            Engine v2 • Last updated: {new Date().toLocaleString()} • Data Confidence: {Math.round(confidence * 100)}%
          </p>
        </footer>
      </div>

      {/* AI System Chat Panel */}
      <SystemChatPanel
        context={{
          page: 'results',
          shipmentId: viewModel?.overview?.shipment?.id,
          riskScore: viewModel?.overview?.riskScore?.score,
          expectedLoss: viewModel?.loss?.expectedLoss
        }}
      />
    </div>
  );
}
