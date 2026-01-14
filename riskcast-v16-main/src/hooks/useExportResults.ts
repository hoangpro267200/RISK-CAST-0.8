/**
 * useExportResults Hook
 * 
 * Enterprise export functionality for Results page.
 * - PDF export via print styles
 * - CSV/Excel export for data
 * - Copy shareable link
 * - Extensible for backend integration
 */

import { useCallback, useState } from 'react';
import type { ResultsViewModel } from '@/types/resultsViewModel';

export interface ExportOptions {
  /** Include charts in PDF export */
  includeCharts?: boolean;
  /** Include raw data tables */
  includeRawData?: boolean;
  /** Custom filename */
  filename?: string;
  /** Language */
  language?: 'en' | 'vi';
}

export interface UseExportResultsReturn {
  /** Export to PDF (print-friendly) */
  exportPDF: (options?: ExportOptions) => Promise<void>;
  /** Export to CSV */
  exportCSV: (options?: ExportOptions) => Promise<void>;
  /** Export to Excel (XLSX) */
  exportExcel: (options?: ExportOptions) => Promise<void>;
  /** Copy shareable link to clipboard */
  copyShareLink: () => Promise<boolean>;
  /** Loading state */
  isExporting: boolean;
  /** Last export type */
  lastExportType: 'pdf' | 'csv' | 'excel' | 'link' | null;
  /** Error message if export failed */
  exportError: string | null;
}

/**
 * Format number for export
 */
function formatNumber(value: number | undefined | null, decimals = 2): string {
  if (value === undefined || value === null || isNaN(value)) return 'N/A';
  return value.toFixed(decimals);
}

/**
 * Format currency for export
 */
function formatCurrency(value: number | undefined | null): string {
  if (value === undefined || value === null || isNaN(value)) return 'N/A';
  return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/**
 * Generate CSV content from view model
 */
function generateCSV(viewModel: ResultsViewModel): string {
  const lines: string[] = [];
  
  // Header section
  lines.push('RISKCAST Enterprise Risk Intelligence Report');
  lines.push(`Generated: ${new Date().toISOString()}`);
  lines.push('');
  
  // Shipment Info
  lines.push('=== SHIPMENT INFORMATION ===');
  lines.push(`Shipment ID,${viewModel.overview.shipment.id}`);
  lines.push(`Route,${viewModel.overview.shipment.route}`);
  lines.push(`Origin (POL),${viewModel.overview.shipment.pol}`);
  lines.push(`Destination (POD),${viewModel.overview.shipment.pod}`);
  lines.push(`Carrier,${viewModel.overview.shipment.carrier}`);
  lines.push(`ETD,${viewModel.overview.shipment.etd || 'N/A'}`);
  lines.push(`ETA,${viewModel.overview.shipment.eta || 'N/A'}`);
  lines.push(`Transit Time (days),${viewModel.overview.shipment.transitTime}`);
  lines.push(`Cargo Value (USD),${formatCurrency(viewModel.overview.shipment.cargoValue)}`);
  lines.push('');
  
  // Risk Score Summary
  lines.push('=== RISK ASSESSMENT ===');
  lines.push(`Overall Risk Score,${formatNumber(viewModel.overview.riskScore.score, 0)}/100`);
  lines.push(`Risk Level,${viewModel.overview.riskScore.level}`);
  lines.push(`Confidence,${formatNumber(viewModel.overview.riskScore.confidence, 0)}%`);
  lines.push('');
  
  // Financial Impact
  if (viewModel.loss) {
    lines.push('=== FINANCIAL IMPACT ===');
    lines.push(`Expected Loss,${formatCurrency(viewModel.loss.expectedLoss)}`);
    lines.push(`VaR 95%,${formatCurrency(viewModel.loss.p95)}`);
    lines.push(`CVaR 99%,${formatCurrency(viewModel.loss.p99)}`);
    lines.push(`Tail Contribution,${formatNumber(viewModel.loss.tailContribution, 1)}%`);
    lines.push('');
  }
  
  // Risk Layers
  if (viewModel.breakdown.layers.length > 0) {
    lines.push('=== RISK LAYERS ===');
    lines.push('Layer Name,Score,Contribution (%),Category');
    viewModel.breakdown.layers.forEach(layer => {
      lines.push(`${layer.name},${formatNumber(layer.score, 1)},${formatNumber(layer.contribution, 1)},${layer.category || 'N/A'}`);
    });
    lines.push('');
  }
  
  // Risk Drivers
  if (viewModel.drivers.length > 0) {
    lines.push('=== RISK DRIVERS ===');
    lines.push('Driver,Impact (%),Description');
    viewModel.drivers.forEach(driver => {
      lines.push(`${driver.name},${driver.impact > 0 ? '+' : ''}${formatNumber(driver.impact, 1)},${driver.description.replace(/,/g, ';')}`);
    });
    lines.push('');
  }
  
  // Mitigation Scenarios
  if (viewModel.scenarios.length > 0) {
    lines.push('=== MITIGATION SCENARIOS ===');
    lines.push('Scenario,Risk Reduction (pts),Cost Impact (USD),Recommended');
    viewModel.scenarios.forEach(scenario => {
      lines.push(`${scenario.title.replace(/,/g, ';')},${formatNumber(scenario.riskReduction, 0)},${formatCurrency(scenario.costImpact)},${scenario.isRecommended ? 'Yes' : 'No'}`);
    });
    lines.push('');
  }
  
  // Decisions
  lines.push('=== DECISION RECOMMENDATIONS ===');
  lines.push(`Insurance,${viewModel.decisions.insurance.status},${viewModel.decisions.insurance.recommendation}`);
  lines.push(`Timing,${viewModel.decisions.timing.status},${viewModel.decisions.timing.recommendation}`);
  lines.push(`Routing,${viewModel.decisions.routing.status},${viewModel.decisions.routing.recommendation}`);
  
  return lines.join('\n');
}

/**
 * Hook for export functionality
 */
export function useExportResults(viewModel: ResultsViewModel | null): UseExportResultsReturn {
  const [isExporting, setIsExporting] = useState(false);
  const [lastExportType, setLastExportType] = useState<'pdf' | 'csv' | 'excel' | 'link' | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  /**
   * Export to PDF using browser print
   */
  const exportPDF = useCallback(async (_options?: ExportOptions) => {
    if (!viewModel) {
      setExportError('No data to export');
      return;
    }

    try {
      setIsExporting(true);
      setExportError(null);
      setLastExportType('pdf');

      // Add print-friendly class to body
      document.body.classList.add('print-mode');
      
      // Wait for styles to apply
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Trigger print dialog
      window.print();
      
      // Remove print class after print dialog closes
      await new Promise(resolve => setTimeout(resolve, 500));
      document.body.classList.remove('print-mode');
      
    } catch (err) {
      console.error('[useExportResults] PDF export failed:', err);
      setExportError('Failed to export PDF');
    } finally {
      setIsExporting(false);
    }
  }, [viewModel]);

  /**
   * Export to CSV
   */
  const exportCSV = useCallback(async (options?: ExportOptions) => {
    if (!viewModel) {
      setExportError('No data to export');
      return;
    }

    try {
      setIsExporting(true);
      setExportError(null);
      setLastExportType('csv');

      const csvContent = generateCSV(viewModel);
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      
      const filename = options?.filename || `riskcast-${viewModel.overview.shipment.id}-${Date.now()}.csv`;
      
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      URL.revokeObjectURL(url);
      
    } catch (err) {
      console.error('[useExportResults] CSV export failed:', err);
      setExportError('Failed to export CSV');
    } finally {
      setIsExporting(false);
    }
  }, [viewModel]);

  /**
   * Export to Excel (using CSV for now, can be upgraded to XLSX with library)
   */
  const exportExcel = useCallback(async (options?: ExportOptions) => {
    if (!viewModel) {
      setExportError('No data to export');
      return;
    }

    try {
      setIsExporting(true);
      setExportError(null);
      setLastExportType('excel');

      // For now, use CSV format with .xlsx extension
      // Can be upgraded to use xlsx library for true Excel format
      const csvContent = generateCSV(viewModel);
      const blob = new Blob([csvContent], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const url = URL.createObjectURL(blob);
      
      const filename = options?.filename || `riskcast-${viewModel.overview.shipment.id}-${Date.now()}.xlsx`;
      
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      URL.revokeObjectURL(url);
      
    } catch (err) {
      console.error('[useExportResults] Excel export failed:', err);
      setExportError('Failed to export Excel');
    } finally {
      setIsExporting(false);
    }
  }, [viewModel]);

  /**
   * Copy shareable link to clipboard
   */
  const copyShareLink = useCallback(async (): Promise<boolean> => {
    try {
      setIsExporting(true);
      setExportError(null);
      setLastExportType('link');

      const url = window.location.href;
      
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(url);
      } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = url;
        textArea.style.position = 'fixed';
        textArea.style.left = '-9999px';
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
      }
      
      return true;
    } catch (err) {
      console.error('[useExportResults] Copy link failed:', err);
      setExportError('Failed to copy link');
      return false;
    } finally {
      setIsExporting(false);
    }
  }, []);

  return {
    exportPDF,
    exportCSV,
    exportExcel,
    copyShareLink,
    isExporting,
    lastExportType,
    exportError
  };
}

export default useExportResults;
