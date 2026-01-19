/**
 * useChangeDetection Hook
 * 
 * Detects changes in data between refreshes.
 * Shows what metrics changed and by how much.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import type { ResultsViewModel } from '@/types/resultsViewModel';

export interface DataChange {
  field: string;
  label: string;
  previousValue: number | string;
  newValue: number | string;
  changeType: 'increase' | 'decrease' | 'unchanged' | 'new';
  changeAmount?: number;
  changePercent?: number;
}

export interface ChangeDetectionResult {
  /** Whether changes were detected */
  hasChanges: boolean;
  /** List of detected changes */
  changes: DataChange[];
  /** Timestamp of last change detection */
  lastDetectedAt: Date | null;
  /** Clear changes (e.g., after user dismisses) */
  clearChanges: () => void;
  /** Mark data as seen (update previous ref without triggering change detection) */
  markAsSeen: () => void;
}

/**
 * Compare two values and return change info
 */
function compareValues(
  field: string,
  label: string,
  prev: number | undefined | null,
  curr: number | undefined | null
): DataChange | null {
  const prevVal = prev ?? 0;
  const currVal = curr ?? 0;

  if (prevVal === currVal) return null;

  const changeAmount = currVal - prevVal;
  const changePercent = prevVal !== 0 ? (changeAmount / prevVal) * 100 : 0;

  return {
    field,
    label,
    previousValue: prevVal,
    newValue: currVal,
    changeType: changeAmount > 0 ? 'increase' : changeAmount < 0 ? 'decrease' : 'unchanged',
    changeAmount,
    changePercent
  };
}

/**
 * Extract key metrics from view model for comparison
 */
function extractKeyMetrics(viewModel: ResultsViewModel | null) {
  if (!viewModel) return null;

  return {
    riskScore: viewModel.overview.riskScore.score,
    confidence: viewModel.overview.riskScore.confidence,
    expectedLoss: viewModel.loss?.expectedLoss ?? 0,
    var95: viewModel.loss?.p95 ?? 0,
    cvar99: viewModel.loss?.p99 ?? 0,
    layersCount: viewModel.breakdown.layers.length,
    driversCount: viewModel.drivers.length,
    scenariosCount: viewModel.scenarios.length
  };
}

/**
 * Hook to detect changes in results data
 */
export function useChangeDetection(
  viewModel: ResultsViewModel | null
): ChangeDetectionResult {
  const previousMetricsRef = useRef<ReturnType<typeof extractKeyMetrics>>(null);
  const [changes, setChanges] = useState<DataChange[]>([]);
  const [lastDetectedAt, setLastDetectedAt] = useState<Date | null>(null);
  const isFirstLoad = useRef(true);

  // Detect changes when viewModel updates
  useEffect(() => {
    if (!viewModel) return;

    const currentMetrics = extractKeyMetrics(viewModel);
    if (!currentMetrics) return;

    // Skip change detection on first load
    if (isFirstLoad.current) {
      previousMetricsRef.current = currentMetrics;
      isFirstLoad.current = false;
      return;
    }

    const prevMetrics = previousMetricsRef.current;
    if (!prevMetrics) {
      previousMetricsRef.current = currentMetrics;
      return;
    }

    // Compare key metrics
    const detectedChanges: DataChange[] = [];

    const comparisons: Array<{ field: string; label: string; prev: number; curr: number }> = [
      { field: 'riskScore', label: 'Risk Score', prev: prevMetrics.riskScore, curr: currentMetrics.riskScore },
      { field: 'confidence', label: 'Confidence', prev: prevMetrics.confidence, curr: currentMetrics.confidence },
      { field: 'expectedLoss', label: 'Expected Loss', prev: prevMetrics.expectedLoss, curr: currentMetrics.expectedLoss },
      { field: 'var95', label: 'VaR 95%', prev: prevMetrics.var95, curr: currentMetrics.var95 },
      { field: 'cvar99', label: 'CVaR 99%', prev: prevMetrics.cvar99, curr: currentMetrics.cvar99 }
    ];

    for (const comp of comparisons) {
      const change = compareValues(comp.field, comp.label, comp.prev, comp.curr);
      if (change && Math.abs(change.changeAmount || 0) > 0.1) {
        detectedChanges.push(change);
      }
    }

    // Update previous metrics
    previousMetricsRef.current = currentMetrics;

    // Only update state if there are actual changes
    if (detectedChanges.length > 0) {
      setChanges(detectedChanges);
      setLastDetectedAt(new Date());
    }
  }, [viewModel]);

  const clearChanges = useCallback(() => {
    setChanges([]);
    setLastDetectedAt(null);
  }, []);

  const markAsSeen = useCallback(() => {
    if (viewModel) {
      previousMetricsRef.current = extractKeyMetrics(viewModel);
    }
    setChanges([]);
    setLastDetectedAt(null);
  }, [viewModel]);

  return {
    hasChanges: changes.length > 0,
    changes,
    lastDetectedAt,
    clearChanges,
    markAsSeen
  };
}

export default useChangeDetection;
