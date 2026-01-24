/**
 * Results Page Component - COMPETITION-READY v5
 * 
 * ARCHITECTURE: ENGINE-FIRST with strict data integrity
 * - NO fake/random data generation
 * - Clear visual hierarchy (Executive → Analytical → Technical)
 * - Enterprise-level UI/UX polish
 * - Maintainable, scalable structure
 * 
 * v5 ENHANCEMENTS:
 * - Breadcrumb navigation for context
 * - URL-synced tab state (shareable links)
 * - Skeleton loading states for perceived performance
 * - Keyboard shortcuts for power users
 */

import { useEffect, useState, useMemo, lazy, Suspense } from 'react';
import { adaptResultV2 } from '@/adapters/adaptResultV2';
import type { ResultsViewModel } from '@/types/resultsViewModel';
import type { ValidationContext } from '@/engine/analysisIntegrity';
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

// Core UI Components (loaded immediately)
import { RiskOrbPremium } from '@/components/RiskOrbPremium';
import { GlassCard } from '@/components/GlassCard';
import { ShipmentHeader } from '@/components/ShipmentHeader';
import { BadgeRisk } from '@/components/BadgeRisk';
import { LayersTable } from '@/components/LayersTable';
import { PrimaryRecommendationCard } from '@/components/PrimaryRecommendationCard';
import { SecondaryRecommendationCard } from '@/components/SecondaryRecommendationCard';

// UI Primitives
import { ResultsBreadcrumb } from '@/components/ui/Breadcrumb';
import { SkeletonResultsPage } from '@/components/ui/Skeleton';
import { Tabs } from '@/components/ui/Tabs';
import { ExportMenu } from '@/components/ui/ExportMenu';
import { ChangeIndicator } from '@/components/ui/ChangeIndicator';
import { KeyboardShortcutsHelp } from '@/components/ui/KeyboardShortcutsHelp';
import { CaseStepper } from '@/components/ui/CaseStepper';  // PR #6: Navigation stepper
import { UserMenu } from '@/components/UserMenu';  // Phase 4: Auth System
import { IntegrityPanel, NoDataSection } from '@/components/IntegrityPanel';  // Phase 5: Analysis Integrity

// Hooks
import { useUrlTabState } from '@/hooks/useUrlTabState';
import { useExportResults } from '@/hooks/useExportResults';
import { useResultsKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';
import { useChangeDetection } from '@/hooks/useChangeDetection';
import { useAiDockState } from '@/hooks/useAiDockState';

// Lazy load heavy chart components (Phase 5 - Performance optimization)
const RiskRadar = lazy(() => import('@/components/RiskRadar').then(m => ({ default: m.RiskRadar })));
const RiskContributionWaterfall = lazy(() => import('@/components/RiskContributionWaterfall').then(m => ({ default: m.RiskContributionWaterfall })));
const ExecutiveNarrative = lazy(() => import('@/components/ExecutiveNarrative').then(m => ({ default: m.ExecutiveNarrative })));
const RiskScenarioFanChart = lazy(() => import('@/components/RiskScenarioFanChart').then(m => ({ default: m.RiskScenarioFanChart })));
const RiskSensitivityTornado = lazy(() => import('@/components/RiskSensitivityTornado').then(m => ({ default: m.RiskSensitivityTornado })));
const RiskCostEfficiencyFrontier = lazy(() => import('@/components/RiskCostEfficiencyFrontier').then(m => ({ default: m.RiskCostEfficiencyFrontier })));
const DataReliabilityMatrix = lazy(() => import('@/components/DataReliabilityMatrix').then(m => ({ default: m.DataReliabilityMatrix })));
const FinancialModule = lazy(() => import('@/components/FinancialModule').then(m => ({ default: m.FinancialModule })));
const SystemChatPanel = lazy(() => import('@/components/SystemChatPanel').then(m => ({ default: m.SystemChatPanel })));

// Sprint 1: Algorithm Explainability (P0 Critical)
const AlgorithmExplainabilityPanel = lazy(() => import('@/components/AlgorithmExplainabilityPanel').then(m => ({ default: m.AlgorithmExplainabilityPanel })));

// Sprint 2: Insurance & Logistics (P1 High)
const InsuranceUnderwritingPanel = lazy(() => import('@/components/InsuranceUnderwritingPanel').then(m => ({ default: m.InsuranceUnderwritingPanel })));
const LogisticsRealismPanel = lazy(() => import('@/components/LogisticsRealismPanel').then(m => ({ default: m.LogisticsRealismPanel })));

// Sprint 3: Risk Disclosure & Chart Enhancements (P1 High)
const RiskDisclosurePanel = lazy(() => import('@/components/RiskDisclosurePanel').then(m => ({ default: m.RiskDisclosurePanel })));
const FactorContributionWaterfall = lazy(() => import('@/components/FactorContributionWaterfall').then(m => ({ default: m.FactorContributionWaterfall })));

// Narrative Generator Service
import { generateNarrativeViewModel } from '@/services/narrativeGenerator';

// Note: ExecutiveNarrative is also lazy loaded above

// Chart loading fallback
const ChartLoader = () => (
  <div className="flex items-center justify-center p-8 bg-white/5 rounded-xl border border-white/10">
    <div className="text-center">
      <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
      <p className="text-white/60 text-sm">Đang tải biểu đồ...</p>
    </div>
  </div>
);

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
import { ProtectedRoute } from '@/components/ProtectedRoute';  // Phase 4: Auth System
import { shouldProtectRoute } from '@/config/auth';  // Phase 4: Auth System

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

// Tab type definition
type ResultsTab = 'overview' | 'analytics' | 'decisions';
const VALID_TABS = ['overview', 'analytics', 'decisions'] as const;

function ResultsPageContent() {
  const [viewModel, setViewModel] = useState<ResultsViewModel | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // URL-synced tab state (P0 - #4)
  const { activeTab, setActiveTab } = useUrlTabState<ResultsTab>({
    defaultTab: 'overview',
    validTabs: VALID_TABS,
    paramName: 'tab'
  });
  
  const { t } = useTranslation();
  
  // Export functionality (P0 - #3)
  const { 
    exportPDF, 
    exportCSV, 
    exportExcel, 
    copyShareLink, 
    isExporting 
  } = useExportResults(viewModel);

  // Change detection (P1 - #9)
  const { hasChanges, changes, clearChanges } = useChangeDetection(viewModel);
  
  // Keyboard shortcuts help state
  const [showShortcutsHelp, setShowShortcutsHelp] = useState(false);
  
  // AI Dock state (from context)
  const { toggle: toggleAiDock } = useAiDockState();

  // Keyboard shortcuts (P1 - #8)
  useResultsKeyboardShortcuts({
    onTabOverview: () => setActiveTab('overview'),
    onTabAnalytics: () => setActiveTab('analytics'),
    onTabDecisions: () => setActiveTab('decisions'),
    onRefresh: () => fetchResults(true, true),
    onToggleCommandPalette: () => toggleAiDock(),
    onEscape: () => setShowShortcutsHelp(false)
  }, !loading && !showShortcutsHelp);

  // Show shortcuts help with ? key
  useEffect(() => {
    const handleQuestionMark = (e: KeyboardEvent) => {
      if (e.key === '?' && !loading) {
        e.preventDefault();
        setShowShortcutsHelp(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleQuestionMark);
    return () => window.removeEventListener('keydown', handleQuestionMark);
  }, [loading]);

  const [autoRetryAttempted, setAutoRetryAttempted] = useState(false);

  const fetchResults = async (showLoading = true, forceRefresh = false) => {
    try {
      if (showLoading) setLoading(true);
      setError(null);

      // Load expected context for integrity validation
      let expectedContext: ValidationContext = {};
      try {
        const contextStr = localStorage.getItem('RISKCAST_EXPECTED_CONTEXT');
        if (contextStr) {
          expectedContext = JSON.parse(contextStr);
          console.log('[ResultsPage] Loaded expected context:', expectedContext);
        }
      } catch (e) {
        console.warn('[ResultsPage] Failed to load expected context:', e);
      }

      // First try localStorage for RISKCAST_RESULTS_V2 (saved by Summary page)
      // Skip localStorage if forceRefresh is true (user clicked refresh button)
      if (!forceRefresh) {
        const savedResults = localStorage.getItem('RISKCAST_RESULTS_V2');
        if (savedResults) {
          try {
            const parsed = JSON.parse(savedResults);
            console.log('[ResultsPage] Loaded results from localStorage:', parsed);
            
            // Pass context to adapter (which will use it for integrity validation)
            const normalized = adaptResultV2(parsed, expectedContext);
            console.log('[ResultsPage] Normalized from localStorage:', normalized);
            
            // Check if integrity validation failed due to stale data
            // Only treat actual errors as blocking, not warnings
            const blockingErrors = normalized.integrity?.issues.filter(i => 
              i.severity === 'error' && (
                i.code === 'INPUT_HASH_MISMATCH' || 
                i.code === 'CARGO_VALUE_MISMATCH' ||
                i.code === 'RUN_ID_MISMATCH'
              )
            ) || [];
            
            if (normalized.integrity?.status === 'invalid' && blockingErrors.length > 0) {
              console.warn('[ResultsPage] Stale data detected - clearing and fetching fresh');
              localStorage.removeItem('RISKCAST_RESULTS_V2');
              localStorage.removeItem('RISKCAST_EXPECTED_CONTEXT');
              // Fall through to API fetch
            } else {
              // Use data even if there are warnings (like CASE_ID_MISMATCH)
              setViewModel(normalized);
              setLoading(false);
              return;
            }
          } catch (parseErr) {
            console.warn('[ResultsPage] Failed to parse localStorage results:', parseErr);
          }
        }
      } else {
        // Clear localStorage when force refreshing to get fresh data from API
        console.log('[ResultsPage] Force refresh - clearing localStorage and fetching from API');
        localStorage.removeItem('RISKCAST_RESULTS_V2');
        localStorage.removeItem('RISKCAST_EXPECTED_CONTEXT');
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
          const responseData: unknown = await response.json();
          console.log('[ResultsPage] Raw response from backend:', responseData);

          // Handle standard response format: {success: true, data: {...}}
          let _rawResult: unknown = responseData;
          if (
            responseData &&
            typeof responseData === 'object' &&
            'success' in responseData &&
            'data' in responseData
          ) {
            const wrapped = responseData as { success: boolean; data: unknown };
            // Extract actual result from data.result or use data directly
            _rawResult = (wrapped.data as { result?: unknown })?.result || wrapped.data;
            console.log('[ResultsPage] Extracted result from wrapped response:', _rawResult);
          }

          // Check if response is effectively empty
          if (_rawResult && typeof _rawResult === 'object' && Object.keys(_rawResult).length === 0) {
            console.warn('[ResultsPage] API returned empty object - no data available');
            // Don't set viewModel, let it fall through to error state
          } else {
            // Pass context to adapter for integrity validation
            const normalized = adaptResultV2(_rawResult, expectedContext);
            console.log('[ResultsPage] Normalized view model:', normalized);

            // Check if normalized data has meaningful content
            // More lenient check - accept data if we have ANY meaningful fields
            const hasData = 
              (normalized.overview.riskScore.score !== undefined && normalized.overview.riskScore.score !== null) ||
              normalized.breakdown.layers.length > 0 ||
              normalized.drivers.length > 0 ||
              (normalized.loss && normalized.loss.expectedLoss !== null) ||
              normalized.overview.shipment.id ||
              normalized.overview.shipment.pol ||
              normalized.overview.shipment.pod;

            if (hasData) {
              setViewModel(normalized);
              setLoading(false);
              return;
            } else {
              console.warn('[ResultsPage] Normalized data is empty - no meaningful content');
              // Don't immediately fail - try to use what we have
              if (normalized.overview && normalized.overview.shipment) {
                console.log('[ResultsPage] Using partial data despite warnings');
                setViewModel(normalized);
                setLoading(false);
                return;
              }
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

  // Auto-retry once if integrity is warning/invalid to avoid missing data
  useEffect(() => {
    if (!viewModel?.integrity) return;
    if (viewModel.integrity.status === 'ok') return;
    if (autoRetryAttempted) return;

    setAutoRetryAttempted(true);
    fetchResults(true, true);
  }, [viewModel?.integrity, autoRetryAttempted]);

  // ALL HOOKS MUST BE CALLED BEFORE ANY EARLY RETURNS
  // This ensures hooks are called in the same order on every render

  // Prepare data for components (safe with null checks)
  // Normalize risk level to Title Case
  const rawRiskLevel = viewModel?.overview?.riskScore?.level;
  const normalizeRiskLevel = (level: string | undefined): RiskLevel | undefined => {
    if (!level) return undefined;
    const upper = level.toUpperCase();
    if (upper === 'LOW') return 'Low';
    if (upper === 'MEDIUM') return 'Medium';
    if (upper === 'HIGH') return 'High';
    if (upper === 'CRITICAL') return 'Critical';
    // Already Title Case
    if (['Low', 'Medium', 'High', 'Critical', 'Unknown'].includes(level)) {
      return level as RiskLevel;
    }
    return 'Unknown';
  };
  const riskLevel: RiskLevel | undefined = normalizeRiskLevel(rawRiskLevel);
  const confidence = viewModel ? viewModel.overview.riskScore.confidence / 100 : 0;
  const riskScore = viewModel?.overview?.riskScore?.score ?? 0;

  // Build layers data with validation - use adapter-provided status/notes
  // Sprint 3: Include FAHP weight and TOPSIS score from algorithm data
  const layersData: LayerData[] = useMemo(() => {
    if (!viewModel?.breakdown?.layers || !Array.isArray(viewModel.breakdown.layers)) {
      console.log('[ResultsPage] No layers data available');
      return [];
    }
    console.log(`[ResultsPage] Processing ${viewModel.breakdown.layers.length} layers`);
    
    // Build FAHP weight map from algorithm data
    const fahpWeightMap = new Map<string, number>();
    if (viewModel.algorithm?.fahp?.weights) {
      viewModel.algorithm.fahp.weights.forEach(w => {
        fahpWeightMap.set(w.layerId, w.weight);
        fahpWeightMap.set(w.layerName, w.weight);
      });
    }
    
    return viewModel.breakdown.layers.map(l => {
      const layerAny = l as any;
      const layerId = layerAny.id || l.name.toLowerCase().replace(/\s+/g, '_');
      
      // Get FAHP weight: prefer layer data > FAHP map > weight/100
      const fahpWeight = layerAny.fahpWeight ?? 
                        fahpWeightMap.get(layerId) ?? 
                        fahpWeightMap.get(l.name) ?? 
                        (layerAny.weight ? layerAny.weight / 100 : undefined);
      
      // Get TOPSIS score: prefer layer data > algorithm data
      const topsisScore = layerAny.topsisScore ?? layerAny.topsis_score ?? undefined;
      
      return {
        id: layerId,
        name: l.name,
        score: l.score,
        contribution: l.contribution,
        weight: layerAny.weight || 0,
        category: l.category || 'UNKNOWN',
        color: layerAny.color || '#6B7280',
        enabled: l.enabled !== false,
        status: layerAny.status || (l.score >= 70 ? 'ALERT' : l.score >= 40 ? 'WARNING' : 'OK'),
        notes: layerAny.notes || `Contributing ${l.contribution.toFixed(1)}% to overall risk`,
        confidence: viewModel.overview.riskScore.confidence,
        // Sprint 3: FAHP weight and TOPSIS score from layer/algorithm data
        fahpWeight,
        topsisScore,
      } as LayerData & { fahpWeight?: number; topsisScore?: number };
    });
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
    const polValue: string = typeof viewModel.overview.shipment.pol === 'string' 
      ? viewModel.overview.shipment.pol 
      : (viewModel.overview.shipment.pol?.name || viewModel.overview.shipment.pol?.code || 'N/A');
    const podValue: string = typeof viewModel.overview.shipment.pod === 'string' 
      ? viewModel.overview.shipment.pod 
      : (viewModel.overview.shipment.pod?.name || viewModel.overview.shipment.pod?.code || 'N/A');
    const cargoValue: number = typeof viewModel.overview.shipment.cargoValue === 'number'
      ? viewModel.overview.shipment.cargoValue
      : (viewModel.overview.shipment.cargoValue?.amount || 0);
    
    return {
      shipmentId: viewModel?.overview?.shipment?.id || 'SHIP-001',
      route: { 
        pol: polValue, 
        pod: podValue
      },
      carrier: viewModel?.overview?.shipment?.carrier || 'Ocean Carrier',
      etd: viewModel?.overview?.shipment?.etd || 'N/A',
      eta: viewModel?.overview?.shipment?.eta || 'N/A',
      dataConfidence: confidence,
      cargoValue: cargoValue,
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

  // Sprint 1: Generate personalized narrative view model
  const narrativeViewModel = useMemo(() => {
    if (!viewModel) return undefined;
    try {
      return generateNarrativeViewModel(viewModel);
    } catch (error) {
      console.warn('[ResultsPage] Failed to generate personalized narrative:', error);
      return undefined;
    }
  }, [viewModel]);

  // Sprint 1: Debug logging (remove in production)
  useEffect(() => {
    if (viewModel) {
      console.log('[Sprint1 Debug] viewModel:', viewModel);
      console.log('[Sprint1 Debug] algorithm:', viewModel.algorithm);
      console.log('[Sprint1 Debug] cargoType:', viewModel.overview?.shipment?.cargoType);
      console.log('[Sprint1 Debug] containerType:', viewModel.overview?.shipment?.containerType);
      console.log('[Sprint1 Debug] dataFreshness:', viewModel.meta?.dataFreshness);
      console.log('[Sprint1 Debug] dataQuality:', viewModel.meta?.dataQuality);
    }
  }, [viewModel]);

  useEffect(() => {
    if (narrativeViewModel) {
      console.log('[Sprint1 Debug] narrativeViewModel:', narrativeViewModel);
      console.log('[Sprint1 Debug] personalizedSummary:', narrativeViewModel.personalizedSummary);
      console.log('[Sprint1 Debug] topRiskFactors:', narrativeViewModel.topRiskFactors);
    }
  }, [narrativeViewModel]);

  // Build narrative - use personalized narrative if available, otherwise fallback to engine explanation
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

  // Use personalized narrative if available, otherwise fallback to existing logic
  const narrativeData: AINarrative = useMemo(() => {
    if (narrativeViewModel) {
      // Use personalized narrative (Sprint 1 enhancement)
      return {
        executiveSummary: narrativeViewModel.personalizedSummary,
        keyInsights: narrativeViewModel.topRiskFactors.map(f => 
          `${f.factor}: ${f.contribution.toFixed(0)}% contribution`
        ),
        actionItems: narrativeViewModel.actionItems.map(a => a.action),
        riskDrivers: narrativeViewModel.topRiskFactors.map(f => f.factor),
        confidenceNotes: narrativeViewModel.sourceAttribution,
      };
    }
    
    // Fallback to existing logic (backward compatibility)
    return {
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
    };
  }, [narrativeViewModel, explanation, riskScore, riskLevel, driverInsights, layerInsights, viewModel, layersData, confidence]);

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

  // Build financial metrics - ONLY use real loss data (null if missing)
  const financialMetrics: FinancialMetrics | null = useMemo(() => {
    if (viewModel?.loss && viewModel.loss.expectedLoss !== null && viewModel.loss.expectedLoss > 0) {
      const lossCurve = viewModel.loss.lossCurve || [];
      console.log('[ResultsPage] Building financialMetrics:', {
        expectedLoss: viewModel.loss.expectedLoss,
        hasLossCurve: lossCurve.length > 0,
        lossCurveLength: lossCurve.length,
        lossCurveSample: lossCurve.slice(0, 3)
      });
      // Only return FinancialMetrics if we have all required fields
      // FinancialMetrics type requires all fields to be numbers (not null)
      if (viewModel.loss.p95 === null || viewModel.loss.p99 === null || 
          viewModel.loss.cvar95 === null || viewModel.loss.cvar99 === null) {
        console.log('[ResultsPage] Missing loss metrics - returning null');
        return null;
      }
      
      return {
        expectedLoss: viewModel.loss.expectedLoss,
        var95: viewModel.loss.p95,
        cvar95: viewModel.loss.cvar95,
        stdDev: (viewModel.loss.p99 - viewModel.loss.expectedLoss) / 2,
        histogram: [],
        lossCurve: lossCurve, // Use lossCurve from adapter if available
      };
    }
    console.log('[ResultsPage] No loss data in viewModel');
    return null;
  }, [viewModel]);

  // Get risk color helper (moved before early returns for consistency)
  const riskColor = useMemo(() => {
    if (riskScore >= 70) return 'from-red-500 to-orange-500';
    if (riskScore >= 40) return 'from-amber-500 to-yellow-500';
    return 'from-emerald-500 to-green-500';
  }, [riskScore]);

  // Loading State with Skeleton (P0 - #2)
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        {/* Animated Background */}
        <div className="fixed inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-blue-500/5 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute bottom-0 right-1/4 w-[600px] h-[600px] bg-purple-500/5 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
        </div>
        
        <div className="relative z-10 max-w-[1600px] mx-auto p-6 lg:p-8 space-y-8">
          {/* Skeleton Header */}
          <header className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                  <Activity className="w-6 h-6 text-white" />
                </div>
                <h1 className="text-3xl lg:text-4xl font-bold text-white tracking-tight">
                  RISKCAST<span className="text-blue-400">.</span>
                </h1>
              </div>
              <p className="text-white/50 mt-1 ml-15">Loading risk analysis...</p>
            </div>
            
            <div className="flex items-center gap-3">
              <div className="w-64 h-10 bg-white/5 rounded-xl animate-pulse" />
              <div className="w-24 h-10 bg-white/5 rounded-xl animate-pulse" />
            </div>
          </header>

          {/* Breadcrumb skeleton */}
          <div className="flex items-center gap-2">
            <div className="w-20 h-4 bg-white/5 rounded animate-pulse" />
            <div className="w-4 h-4 bg-white/5 rounded animate-pulse" />
            <div className="w-24 h-4 bg-white/5 rounded animate-pulse" />
            <div className="w-4 h-4 bg-white/5 rounded animate-pulse" />
            <div className="w-28 h-4 bg-white/5 rounded animate-pulse" />
          </div>

          {/* Skeleton content */}
          <SkeletonResultsPage />
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
            onClick={() => fetchResults(true, true)}
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
            href="/input_react"
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
     (!viewModel.loss || viewModel.loss.expectedLoss === null || viewModel.loss.expectedLoss === 0));

  if (isEmptyData && viewModel) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8 flex items-center justify-center">
        <GlassCard className="max-w-md text-center">
          <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-blue-500/10 flex items-center justify-center">
            <TrendingUp className="w-10 h-10 text-blue-400" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">Ready for Analysis</h2>
          <p className="text-white/60 mb-6">Submit shipment data to generate risk intelligence.</p>
          <a href="/input_react" className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-medium">
            Go to Input <ArrowRight className="w-5 h-5" />
          </a>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Skip Link for Accessibility */}
      <a 
        href="#main-content" 
        className="skip-link"
      >
        Skip to main content
      </a>

      {/* Animated Background */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-blue-500/5 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-0 right-1/4 w-[600px] h-[600px] bg-purple-500/5 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
        <div className="absolute top-1/2 left-1/2 w-[400px] h-[400px] bg-cyan-500/5 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }}></div>
      </div>

      <main 
        id="main-content" 
        className="relative z-10 max-w-[1600px] mx-auto p-4 sm:p-6 lg:p-8 space-y-6 safe-area-inset"
        role="main"
        aria-label="Risk analysis results"
      >
        {/* Header - All elements in one row */}
        <header className="mb-6">
          {/* Unified Header Row: Logo (left) | Tabs + Actions (right) */}
          <div 
            className="flex items-center justify-between gap-4 flex-wrap" 
            style={{ 
              display: 'flex',
              flexDirection: 'row',
              alignItems: 'center',
              width: '100%'
            } as React.CSSProperties}
          >
            {/* Left: Logo - Compact on mobile */}
            <div className="flex items-center gap-2" style={{ flexShrink: 0, minWidth: 'fit-content' }}>
              <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                <Activity className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
              </div>
              <div className="hidden lg:block" style={{ flexShrink: 0 }}>
                <h1 className="text-2xl lg:text-3xl font-bold text-white tracking-tight whitespace-nowrap leading-tight">
                  RISKCAST<span className="text-blue-400">.</span>
                </h1>
                <p className="text-white/50 text-xs whitespace-nowrap leading-tight">Enterprise Risk Intelligence Platform</p>
              </div>
              <div className="lg:hidden" style={{ flexShrink: 0 }}>
                <h1 className="text-lg sm:text-xl font-bold text-white tracking-tight whitespace-nowrap">
                  RISKCAST<span className="text-blue-400">.</span>
                </h1>
              </div>
            </div>

            {/* Right: Tabs + Action Buttons - Horizontal alignment */}
            <div className="flex items-center gap-3 sm:gap-4" style={{ flexShrink: 0, minWidth: 'fit-content' }}>
              {/* Tab Navigation */}
              <div className="flex items-center">
                <Tabs
                  tabs={[
                    { id: 'overview' as ResultsTab, label: t('overview') },
                    { id: 'analytics' as ResultsTab, label: t('analytics') },
                    { id: 'decisions' as ResultsTab, label: t('decisions') }
                  ]}
                  activeTab={activeTab}
                  onTabChange={setActiveTab}
                  size="md"
                  variant="default"
                  className="w-fit"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 sm:gap-3">
                {/* Export Menu */}
                <ExportMenu
                  onExportPDF={exportPDF}
                  onExportCSV={exportCSV}
                  onExportExcel={exportExcel}
                  onCopyLink={copyShareLink}
                  isExporting={isExporting}
                  disabled={!viewModel}
                />

                {/* Language Switcher - Hidden on mobile */}
                <div className="hidden sm:block">
                  <HeaderLangSwitcher />
                </div>

                {/* User Menu - Auth System */}
                <UserMenu />

                <button
                  onClick={() => fetchResults(true, true)}
                  disabled={loading}
                  className="px-3 sm:px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white rounded-xl font-medium transition-all flex items-center gap-2 shadow-lg shadow-blue-500/25 disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900 whitespace-nowrap"
                  aria-label="Refresh analysis data"
                >
                  <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                  <span className="hidden sm:inline">{t('refresh')}</span>
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* PR #6: Case Stepper (Navigation Progress) */}
        <div className="mb-4 pb-4 border-b border-white/10">
          <CaseStepper currentStep="results" completedSteps={['input', 'summary']} />
        </div>

        {/* Breadcrumb Navigation (P0 - #1) - UPDATED: Includes back to Summary */}
        <ResultsBreadcrumb 
          shipmentId={viewModel?.overview?.shipment?.id?.replace('SHIP-', '') || 'Unknown'}
          className="mb-2"
        />
        
        {/* PR #4: Display Run ID + Timestamp (traceability) */}
        {viewModel?.meta?.analysisId || viewModel?.meta?.timestamp ? (
          <div className="flex items-center gap-4 text-xs text-white/40 mb-4">
            {viewModel.meta.analysisId && (
              <span>Run #{viewModel.meta.analysisId.replace('AN-', '')}</span>
            )}
            {viewModel.meta.timestamp && (
              <span>• {new Date(viewModel.meta.timestamp).toLocaleString()}</span>
            )}
          </div>
        ) : null}

        {/* Shipment Header - Compact */}
        <ShipmentHeader data={shipmentData} />

        {/* Analysis Integrity Panel - Shows validation status and issues */}
        {viewModel?.integrity && viewModel.integrity.status !== 'ok' && (
          <div className="mb-4">
            <IntegrityPanel 
              integrity={viewModel.integrity}
              onRetry={() => fetchResults(true, true)}
              isLoading={loading}
            />
          </div>
        )}

        {/* Gating: If integrity check failed, show limited UI */}
        {viewModel?.integrity?.status === 'invalid' && !viewModel.integrity.gating.showOverview ? (
          <GlassCard className="p-8 text-center">
            <XCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-white mb-2">Analysis Data Invalid</h2>
            <p className="text-white/60 mb-4">
              The analysis results failed integrity validation and cannot be displayed.
              Please retry the analysis or check the input data.
            </p>
            <div className="flex justify-center gap-4">
              <button
                onClick={() => fetchResults(true, true)}
                className="px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-all"
              >
                Retry Analysis
              </button>
              <a
                href="/input_react"
                className="px-6 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg font-medium transition-all"
              >
                Edit Input
              </a>
            </div>
          </GlassCard>
        ) : (
          <>
        {/* ============================================================
            SECTION 1: OVERVIEW TAB - Executive Summary (Compact SaaS style)
            ============================================================ */}
        {activeTab === 'overview' && (
          <div className="space-y-4">
            {/* Hero Section - Compact 2-column layout */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
              {/* Left: Risk Score Card - Compact */}
              <GlassCard className="lg:col-span-4 p-4">
                <div className="flex items-center gap-4">
                  <RiskOrbPremium 
                    score={Math.round(riskScore)} 
                    riskLevel={riskLevel}
                    size="sm"
                    collapsible={false}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {riskLevel ? (
                        <BadgeRisk level={riskLevel} size="sm" />
                      ) : (
                        <span className="text-white/60 text-xs">Unknown</span>
                      )}
                      <span className="text-xs text-white/40">Confidence: {Math.round(confidence * 100)}%</span>
                    </div>
                    <p className="text-white/70 text-xs line-clamp-2">
                      {explanation || `${riskLevel || 'Unknown'} risk profile`}
                    </p>
                  </div>
                </div>
              </GlassCard>

              {/* Right: Key Metrics - Compact Grid */}
              <div className="lg:col-span-8 grid grid-cols-2 sm:grid-cols-4 gap-3">
                {/* Expected Loss - Gated by integrity */}
                {viewModel.integrity?.gating.showLossMetrics && viewModel.loss && viewModel.loss.expectedLoss !== null && viewModel.loss.expectedLoss > 0 ? (
                  <>
                    <GlassCard className="p-3 text-center">
                      <DollarSign className="w-4 h-4 text-emerald-400 mx-auto mb-1" />
                      <p className="text-lg font-bold text-white">${(viewModel.loss.expectedLoss / 1000).toFixed(1)}K</p>
                      <p className="text-[10px] text-white/50">Expected Loss</p>
                    </GlassCard>
                    {viewModel.loss.p95 !== null && (
                      <GlassCard className="p-3 text-center">
                        <AlertTriangle className="w-4 h-4 text-amber-400 mx-auto mb-1" />
                        <p className="text-lg font-bold text-white">${(viewModel.loss.p95 / 1000).toFixed(1)}K</p>
                        <p className="text-[10px] text-white/50">VaR 95%</p>
                      </GlassCard>
                    )}
                    {viewModel.loss.p99 !== null && (
                      <GlassCard className="p-3 text-center">
                        <Shield className="w-4 h-4 text-red-400 mx-auto mb-1" />
                        <p className="text-lg font-bold text-white">${(viewModel.loss.p99 / 1000).toFixed(1)}K</p>
                        <p className="text-[10px] text-white/50">CVaR 99%</p>
                      </GlassCard>
                    )}
                  </>
                ) : (
                  <GlassCard className="p-3 text-center col-span-3 bg-white/5 border-dashed">
                    <DollarSign className="w-4 h-4 text-white/30 mx-auto mb-1" />
                    <p className="text-sm text-white/40">No cargo value provided</p>
                    <p className="text-[10px] text-white/30">Add value in input to calculate loss</p>
                  </GlassCard>
                )}
                <GlassCard className="p-3 text-center">
                  <Layers className="w-4 h-4 text-purple-400 mx-auto mb-1" />
                  <p className="text-lg font-bold text-white">{layersData.length}</p>
                  <p className="text-[10px] text-white/50">Risk Layers</p>
                </GlassCard>
              </div>
            </div>

            {/* Key Takeaways - Compact */}
            <GlassCard className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Target className="w-4 h-4 text-blue-400" />
                <h2 className="text-sm font-semibold text-white">Key Findings</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                {keyTakeaways.map((takeaway, idx) => (
                  <div 
                    key={idx}
                    className="flex items-start gap-2 p-2 bg-white/5 rounded-lg border border-white/10 text-xs"
                  >
                    <div className={`flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center ${
                      idx === 0 ? 'bg-red-500/20' : idx === 1 ? 'bg-amber-500/20' : 'bg-blue-500/20'
                    }`}>
                      <Info className={`w-3 h-3 ${
                        idx === 0 ? 'text-red-400' : idx === 1 ? 'text-amber-400' : 'text-blue-400'
                      }`} />
                    </div>
                    <p className="text-white/80 leading-relaxed flex-1">{takeaway}</p>
                  </div>
                ))}
              </div>
            </GlassCard>

            {/* Shipment Details - Compact 2-column */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Route & Cargo */}
              <GlassCard className="p-4">
                <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-blue-400" />
                  Route & Cargo
                </h3>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2 bg-white/5 rounded">
                    <span className="text-white/50 block">Origin</span>
                    <span className="text-white font-medium">
                      {typeof viewModel.overview.shipment.pol === 'string' 
                        ? viewModel.overview.shipment.pol 
                        : viewModel.overview.shipment.pol?.code || 'N/A'}
                    </span>
                  </div>
                  <div className="p-2 bg-white/5 rounded">
                    <span className="text-white/50 block">Destination</span>
                    <span className="text-white font-medium">
                      {typeof viewModel.overview.shipment.pod === 'string' 
                        ? viewModel.overview.shipment.pod 
                        : viewModel.overview.shipment.pod?.code || 'N/A'}
                    </span>
                  </div>
                  <div className="p-2 bg-white/5 rounded">
                    <span className="text-white/50 block">Transit</span>
                    <span className="text-white font-medium">{viewModel.overview.shipment.transitTime || 0} days</span>
                  </div>
                  <div className="p-2 bg-white/5 rounded">
                    <span className="text-white/50 block">Cargo</span>
                    <span className="text-white font-medium truncate">
                      {viewModel.overview.shipment.cargoType || viewModel.overview.shipment.cargo || 'N/A'}
                    </span>
                  </div>
                  <div className="p-2 bg-white/5 rounded">
                    <span className="text-white/50 block">Container</span>
                    <span className="text-white font-medium">
                      {viewModel.overview.shipment.containerType || viewModel.overview.shipment.container || 'N/A'}
                    </span>
                  </div>
                  <div className="p-2 bg-white/5 rounded">
                    <span className="text-white/50 block">Value</span>
                    <span className="text-white font-medium">
                      {(() => {
                        const val = typeof viewModel.overview.shipment.cargoValue === 'number' 
                          ? viewModel.overview.shipment.cargoValue 
                          : viewModel.overview.shipment.cargoValue?.amount || 0;
                        return val > 0 ? `$${(val / 1000).toFixed(0)}K` : 'Not set';
                      })()}
                    </span>
                  </div>
                </div>
              </GlassCard>

              {/* Timeline & Carrier */}
              <GlassCard className="p-4">
                <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <Clock className="w-4 h-4 text-purple-400" />
                  Timeline
                </h3>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div className="p-2 bg-white/5 rounded">
                    <span className="text-white/50 block">ETD</span>
                    <span className="text-white font-medium">{viewModel.overview.shipment.etd || 'N/A'}</span>
                  </div>
                  <div className="p-2 bg-white/5 rounded">
                    <span className="text-white/50 block">ETA</span>
                    <span className="text-white font-medium">{viewModel.overview.shipment.eta || 'N/A'}</span>
                  </div>
                  <div className="p-2 bg-white/5 rounded">
                    <span className="text-white/50 block">Carrier</span>
                    <span className="text-white font-medium truncate">{viewModel.overview.shipment.carrier || 'N/A'}</span>
                  </div>
                </div>
              </GlassCard>
            </div>

            {/* Risk Visualization - Gated by integrity */}
            {viewModel.integrity?.gating.showLayers && layersData.length > 0 ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <Suspense fallback={<ChartLoader />}>
                  <RiskRadar layers={layersData} />
                </Suspense>
                <Suspense fallback={<ChartLoader />}>
                  <RiskContributionWaterfall layers={layersData} overallScore={riskScore} />
                </Suspense>
              </div>
            ) : viewModel.integrity?.gating.showLayers === false ? null : (
              <NoDataSection 
                title="No Risk Visualization Available"
                message="Analysis did not generate layer breakdown for visualization"
                icon={BarChart3}
              />
            )}

            {/* Data Integrity Warning */}
            {!layerValidation.isValid && layerValidation.warnings.length > 0 && (
              <GlassCard className="p-3 border-amber-500/30 bg-amber-500/5">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                  <p className="text-xs text-amber-300">{layerValidation.warnings[0]}</p>
                </div>
              </GlassCard>
            )}

            {/* Risk Drivers - Gated by integrity */}
            {viewModel.integrity?.gating.showDrivers && viewModel?.drivers && viewModel.drivers.length > 0 ? (
              <GlassCard className="p-4">
                <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <Zap className="w-4 h-4 text-amber-400" />
                  Top Risk Drivers
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {viewModel.drivers.slice(0, 4).map((driver, idx) => (
                    <div 
                      key={idx}
                      className={`p-2 rounded-lg border text-xs ${
                        driver.impact > 0 
                          ? 'bg-red-500/5 border-red-500/20' 
                          : 'bg-emerald-500/5 border-emerald-500/20'
                      }`}
                    >
                      <span className="text-white/80 block truncate">{driver.name}</span>
                      <span className={`text-lg font-bold ${driver.impact > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                        {driver.impact > 0 ? '+' : ''}{driver.impact.toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>
              </GlassCard>
            ) : viewModel.integrity?.gating.showDrivers === false ? null : (
              <NoDataSection 
                title="No Risk Drivers Available"
                message="Analysis did not identify specific risk drivers"
                icon={Zap}
              />
            )}

            {/* Executive Narrative - More compact */}
            <Suspense fallback={<ChartLoader />}>
              <ExecutiveNarrative narrative={narrativeData} />
            </Suspense>
          </div>
        )}

        {/* ============================================================
            SECTION 2: ANALYTICS TAB - Technical Deep Dive
            ============================================================ */}
        {activeTab === 'analytics' && (
          <div className="space-y-4">
            {/* Algorithm & Model Section - Gated by integrity */}
            {viewModel.integrity?.gating.showAlgorithm && viewModel.algorithm ? (
              <Suspense fallback={<ChartLoader />}>
                <AlgorithmExplainabilityPanel algorithmData={viewModel.algorithm} />
              </Suspense>
            ) : viewModel.integrity?.gating.showAlgorithm === false ? null : (
              <NoDataSection 
                title="Algorithm Data Not Available"
                message="Re-run analysis to generate algorithm details"
                icon={Brain}
              />
            )}

            {/* Financial Analysis Section - Gated by integrity */}
            {viewModel.integrity?.gating.showLossCharts && financialMetrics && viewModel.loss && viewModel.loss.expectedLoss !== null && viewModel.loss.expectedLoss > 0 ? (
              <>
                <Suspense fallback={<ChartLoader />}>
                  <FinancialModule financial={financialMetrics} />
                </Suspense>
                
                {/* Factor Contribution */}
                <Suspense fallback={<ChartLoader />}>
                  <FactorContributionWaterfall
                    baseScore={Math.max(0, riskScore - layersData.reduce((sum, l) => sum + (l.contribution || 0), 0))}
                    layers={layersData}
                    finalScore={riskScore}
                  />
                </Suspense>
              </>
            ) : (
              <GlassCard className="p-4 border-dashed border-white/20">
                <div className="flex items-center gap-3 text-white/50">
                  <DollarSign className="w-5 h-5" />
                  <div>
                    <p className="text-sm font-medium">Financial Analysis Not Available</p>
                    <p className="text-xs">Add cargo value in input to enable loss calculations</p>
                  </div>
                </div>
              </GlassCard>
            )}

            {/* Insurance Panel - Only if loss data available and gated */}
            {viewModel.integrity?.gating.showLossMetrics && viewModel.insurance && viewModel.loss && viewModel.loss.expectedLoss !== null && viewModel.loss.expectedLoss > 0 && (
              <Suspense fallback={<ChartLoader />}>
                <InsuranceUnderwritingPanel
                  insuranceData={viewModel.insurance}
                  cargoValue={typeof viewModel.overview.shipment.cargoValue === 'number'
                    ? viewModel.overview.shipment.cargoValue
                    : viewModel.overview.shipment.cargoValue?.amount || 0}
                  expectedLoss={viewModel.loss.expectedLoss}
                  p95={viewModel.loss.p95 ?? 0}
                  p99={viewModel.loss.p99 ?? 0}
                />
              </Suspense>
            )}

            {/* Logistics Panel */}
            {viewModel.logistics && (
              <Suspense fallback={<ChartLoader />}>
                <LogisticsRealismPanel
                  logisticsData={viewModel.logistics}
                  cargoType={viewModel.overview.shipment.cargoType || viewModel.overview.shipment.cargo || ''}
                  containerType={viewModel.overview.shipment.containerType || viewModel.overview.shipment.container || ''}
                  cargoValue={typeof viewModel.overview.shipment.cargoValue === 'number'
                    ? viewModel.overview.shipment.cargoValue
                    : viewModel.overview.shipment.cargoValue?.amount || 0}
                  transitDays={viewModel.overview.shipment.transitTime || 0}
                />
              </Suspense>
            )}

            {/* Risk Disclosure */}
            {viewModel.riskDisclosure && (
              <Suspense fallback={<ChartLoader />}>
                <RiskDisclosurePanel riskDisclosure={viewModel.riskDisclosure} />
              </Suspense>
            )}

            {/* Scenario Projections - Gated by integrity */}
            {viewModel.integrity?.gating.showTimeline && scenarioData.length > 0 ? (
              <Suspense fallback={<ChartLoader />}>
                <RiskScenarioFanChart 
                  data={scenarioData}
                  etd={viewModel.overview.shipment.etd || 'N/A'}
                  eta={viewModel.overview.shipment.eta || 'N/A'}
                />
              </Suspense>
            ) : viewModel.integrity?.gating.showTimeline === false ? null : (
              <NoDataSection 
                title="No Timeline Projections Available"
                message="Analysis did not generate scenario projections"
                icon={LineChart}
              />
            )}

            {/* Sensitivity Analysis - Gated by integrity */}
            {viewModel.integrity?.gating.showDrivers && sensitivityDrivers.length > 0 ? (
              <Suspense fallback={<ChartLoader />}>
                <RiskSensitivityTornado drivers={sensitivityDrivers} />
              </Suspense>
            ) : viewModel.integrity?.gating.showDrivers === false ? null : (
              <NoDataSection 
                title="No Sensitivity Analysis Available"
                message="Analysis did not generate sensitivity data"
                icon={BarChart3}
              />
            )}

            {/* Layers Table - Gated by integrity */}
            {viewModel.integrity?.gating.showLayers && layersData.length > 0 ? (
              <LayersTable layers={layersData} />
            ) : viewModel.integrity?.gating.showLayers === false ? null : (
              <NoDataSection 
                title="No Risk Layers Available"
                message="Analysis did not generate layer breakdown"
                icon={Layers}
              />
            )}
          </div>
        )}

        {/* ============================================================
            SECTION 3: DECISIONS TAB - Action Recommendations
            ============================================================ */}
        {activeTab === 'decisions' && (() => {
          const recommendedScenario = displayScenarios.find(s => s.isRecommended) || (displayScenarios.length > 0 ? displayScenarios[0] : null);
          const maxProtectionScenario = displayScenarios.length > 0 ? displayScenarios[displayScenarios.length - 1] : null;

          return (
            <div className="space-y-4">
              {/* Quick Decision Cards - Compact 3-column */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
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

              {/* Primary Scenarios - Gated by integrity */}
              {viewModel.integrity?.gating.showScenarios && displayScenarios.length > 0 && recommendedScenario ? (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
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
              ) : (
                <GlassCard className="p-4 border-dashed border-white/20">
                  <div className="flex items-center gap-3 text-white/50">
                    <Target className="w-5 h-5" />
                    <div>
                      <p className="text-sm font-medium">No Mitigation Scenarios Available</p>
                      <p className="text-xs">Analysis did not generate specific scenarios</p>
                    </div>
                  </div>
                </GlassCard>
              )}

              {/* Decision Matrix - Compact */}
              <GlassCard className="p-4">
                <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-blue-400" />
                  Decision Matrix
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-white/10">
                        <th className="text-left py-2 px-2 font-medium text-white/60">Category</th>
                        <th className="text-left py-2 px-2 font-medium text-white/60">Status</th>
                        <th className="text-left py-2 px-2 font-medium text-white/60">Action</th>
                        <th className="text-left py-2 px-2 font-medium text-white/60">Impact</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        { cat: 'Insurance', icon: '🛡️', ...viewModel.decisions.insurance,
                          impact: riskScore < 30 ? 'Minimal' : riskScore < 60 ? '-5 to -10 pts' : '-10 to -20 pts' },
                        { cat: 'Timing', icon: '⏱️', ...viewModel.decisions.timing,
                          impact: riskScore < 30 ? 'Minimal' : riskScore < 60 ? '-3 to -8 pts' : '-8 to -15 pts' },
                        { cat: 'Routing', icon: '🗺️', ...viewModel.decisions.routing,
                          impact: riskScore < 30 ? 'Minimal' : riskScore < 60 ? '-2 to -5 pts' : '-5 to -12 pts' },
                      ].map((row, idx) => (
                        <tr key={idx} className="border-b border-white/5 hover:bg-white/5">
                          <td className="py-2 px-2">
                            <span className="text-white">{row.icon} {row.cat}</span>
                          </td>
                          <td className="py-2 px-2">
                            <span className={`text-[10px] px-2 py-0.5 rounded-full ${
                              row.status === 'RECOMMENDED' ? 'bg-green-500/20 text-green-400' :
                              row.status === 'NOT_NEEDED' ? 'bg-blue-500/10 text-cyan-400' :
                              'bg-amber-500/20 text-amber-400'
                            }`}>
                              {row.status === 'NOT_NEEDED' ? 'Optional' : 
                               row.status === 'RECOMMENDED' ? 'Recommended' : 'Evaluate'}
                            </span>
                          </td>
                          <td className="py-2 px-2 text-white/80">{row.recommendation}</td>
                          <td className="py-2 px-2 text-amber-400">{row.impact}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="mt-3 pt-2 border-t border-white/10 flex items-center justify-between text-[10px] text-white/40">
                  <span>Overall Risk: {riskScore < 30 ? 'LOW' : riskScore < 60 ? 'MEDIUM' : 'HIGH'} ({Math.round(riskScore)}/100)</span>
                  <span>Confidence: {Math.round(confidence * 100)}%</span>
                </div>
              </GlassCard>

              {/* All Scenarios - Gated by integrity */}
              {viewModel.integrity?.gating.showScenarios && displayScenarios.length > 0 ? (
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
              ) : viewModel.integrity?.gating.showScenarios === false ? (
                <NoDataSection 
                  title="No Mitigation Scenarios Available"
                  message="Analysis did not generate scenarios"
                  icon={Target}
                />
              ) : null}
            </div>
          );
        })()}

          </>
        )}

        {/* Footer */}
        <footer className="text-center py-8 border-t border-white/10">
          <div className="flex items-center justify-center gap-2 text-white/30 text-sm mb-2">
            <Activity className="w-4 h-4" aria-hidden="true" />
            RISKCAST Enterprise Risk Intelligence
          </div>
          <p className="text-white/20 text-xs">
            Engine v2 • Last updated: {new Date().toLocaleString()} • Data Confidence: {Math.round(confidence * 100)}%
          </p>
        </footer>
      </main>

      {/* AI System Chat Panel */}
      <Suspense fallback={null}>
        <SystemChatPanel
          context={{
            page: 'results',
            shipmentId: viewModel?.overview?.shipment?.id,
            riskScore: viewModel?.overview?.riskScore?.score,
            expectedLoss: viewModel?.loss?.expectedLoss ?? undefined
          }}
        />
      </Suspense>

      {/* Change Indicator Toast (P1 - #9) */}
      <ChangeIndicator
        hasChanges={hasChanges}
        changes={changes}
        onDismiss={clearChanges}
        autoHideMs={8000}
        position="top"
      />

      {/* Keyboard Shortcuts Help (P1 - #8) */}
      <KeyboardShortcutsHelp
        isOpen={showShortcutsHelp}
        onClose={() => setShowShortcutsHelp(false)}
      />
    </div>
  );
}

export default function ResultsPage() {
  const needsProtection = shouldProtectRoute('/results');
  
  if (needsProtection) {
    return (
      <ProtectedRoute>
        <ResultsPageContent />
      </ProtectedRoute>
    );
  }
  
  return <ResultsPageContent />;
}

