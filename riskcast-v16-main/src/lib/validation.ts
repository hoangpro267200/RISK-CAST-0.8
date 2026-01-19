import type { ShipmentData } from '../components/summary/types';

export interface ValidationIssue {
  id: string;
  severity: 'critical' | 'warning' | 'suggestion';
  message: string;
  detail: string;
  affectedFields: string[];
  action?: string;
}

export function getValidationIssues(data: ShipmentData): ValidationIssue[] {
  const issues: ValidationIssue[] = [];

  // 1. MODE_PORT_MISMATCH_SEA
  if (data.trade.mode === 'SEA' && (data.trade.polName?.toLowerCase().includes('airport') || data.trade.podName?.toLowerCase().includes('airport'))) {
    issues.push({
      id: 'MODE_PORT_MISMATCH_SEA',
      severity: 'critical',
      message: 'Mode is SEA but ports are airports',
      detail: 'POL/POD should be seaports, not airports',
      affectedFields: ['trade.mode', 'trade.pol', 'trade.pod'],
      action: 'Fix Now',
    });
  }

  // 2. MODE_PORT_MISMATCH_AIR
  if (data.trade.mode === 'AIR' && (data.trade.polName?.toLowerCase().includes('seaport') || data.trade.podName?.toLowerCase().includes('seaport'))) {
    issues.push({
      id: 'MODE_PORT_MISMATCH_AIR',
      severity: 'critical',
      message: 'Mode is AIR but ports are seaports',
      detail: 'POL/POD should be airports, not seaports',
      affectedFields: ['trade.mode', 'trade.pol', 'trade.pod'],
      action: 'Fix Now',
    });
  }

  // 3. ETD_IN_PAST
  const etdDate = new Date(data.trade.etd);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  if (etdDate < today) {
    issues.push({
      id: 'ETD_IN_PAST',
      severity: 'critical',
      message: 'Departure date is in the past',
      detail: 'ETD must be today or future date',
      affectedFields: ['trade.etd'],
      action: 'Fix Now',
    });
  }

  // 4. ETA_BEFORE_ETD
  const etaDate = new Date(data.trade.eta);
  if (etaDate <= etdDate) {
    issues.push({
      id: 'ETA_BEFORE_ETD',
      severity: 'critical',
      message: 'Arrival before departure',
      detail: 'ETA must be after ETD',
      affectedFields: ['trade.eta', 'trade.etd'],
      action: 'Fix Now',
    });
  }

  // 5. HS_CODE_REQUIRED
  if (!data.cargo.hs_code && (data.cargo.gross_weight_kg > 0 || data.cargo.volume_cbm > 0)) {
    issues.push({
      id: 'HS_CODE_REQUIRED',
      severity: 'critical',
      message: 'HS Code is required',
      detail: 'Mandatory when weight/volume specified',
      affectedFields: ['cargo.hs_code'],
      action: 'Fix Now',
    });
  }

  // 6. HS_DG_ENFORCED
  const hsChapter = data.cargo.hs_code ? parseInt(data.cargo.hs_code.split('.')[0]) : 0;
  if ((hsChapter === 28 || hsChapter === 29) && !data.cargo.is_dg) {
    issues.push({
      id: 'HS_DG_ENFORCED',
      severity: 'critical',
      message: 'Dangerous goods flag required',
      detail: 'HS Chapter 28/29 typically contains DG',
      affectedFields: ['cargo.hs_code', 'cargo.is_dg'],
      action: 'Fix Now',
    });
  }

  // 7. WEIGHT_GREATER_THAN_NET
  if (data.cargo.net_weight_kg && data.cargo.gross_weight_kg && data.cargo.net_weight_kg > data.cargo.gross_weight_kg) {
    issues.push({
      id: 'WEIGHT_GREATER_THAN_NET',
      severity: 'critical',
      message: 'Net weight exceeds gross weight',
      detail: 'Net weight must be ≤ Gross weight',
      affectedFields: ['cargo.gross_weight_kg', 'cargo.net_weight_kg'],
      action: 'Fix Now',
    });
  }

  // 8. SELLER_CONTACT_REQUIRED
  if (!data.seller.email || !data.seller.phone) {
    issues.push({
      id: 'SELLER_CONTACT_REQUIRED',
      severity: 'critical',
      message: 'Seller contact information incomplete',
      detail: 'Email and phone are required',
      affectedFields: ['seller.email', 'seller.phone'],
      action: 'Fix Now',
    });
  }

  // 9. BUYER_CONTACT_REQUIRED
  if (!data.buyer.email || !data.buyer.phone) {
    issues.push({
      id: 'BUYER_CONTACT_REQUIRED',
      severity: 'critical',
      message: 'Buyer contact information incomplete',
      detail: 'Email and phone are required',
      affectedFields: ['buyer.email', 'buyer.phone'],
      action: 'Fix Now',
    });
  }

  // 10. TRANSIT_DAYS_MISSING
  if (!data.trade.transit_time_days || data.trade.transit_time_days === 0) {
    issues.push({
      id: 'TRANSIT_DAYS_MISSING',
      severity: 'warning',
      message: 'Transit time not specified',
      detail: 'Please estimate transit duration',
      affectedFields: ['trade.transit_time_days'],
      action: 'Review',
    });
  }

  // 11. TRANSIT_DAYS_OUTLIER
  if (data.trade.transit_time_days > 0) {
    if (data.trade.mode === 'SEA' && (data.trade.transit_time_days < 3 || data.trade.transit_time_days > 90)) {
      issues.push({
        id: 'TRANSIT_DAYS_OUTLIER',
        severity: 'warning',
        message: 'Transit time seems unusual',
        detail: 'SEA: 3-90 days expected',
        affectedFields: ['trade.transit_time_days', 'trade.mode'],
        action: 'Review',
      });
    } else if (data.trade.mode === 'AIR' && data.trade.transit_time_days >= 15) {
      issues.push({
        id: 'TRANSIT_DAYS_OUTLIER',
        severity: 'warning',
        message: 'Transit time seems unusual',
        detail: 'AIR: <15 days expected',
        affectedFields: ['trade.transit_time_days', 'trade.mode'],
        action: 'Review',
      });
    }
  }

  // 12. INCOTERM_LOCATION_REQUIRED
  const incotermsNeedingLocation = ['FOB', 'CIF', 'CFR', 'DAP', 'DPU', 'DDP'];
  if (incotermsNeedingLocation.includes(data.trade.incoterm) && !data.trade.incoterm_location) {
    issues.push({
      id: 'INCOTERM_LOCATION_REQUIRED',
      severity: 'warning',
      message: 'Incoterm location missing',
      detail: `${data.trade.incoterm} requires location`,
      affectedFields: ['trade.incoterm', 'trade.incoterm_location'],
      action: 'Review',
    });
  }

  // 13. HS_REEFER_ENFORCED
  const perishableChapters = [2, 3, 7, 8];
  if (perishableChapters.includes(hsChapter) && !data.cargo.temp_control_required) {
    issues.push({
      id: 'HS_REEFER_ENFORCED',
      severity: 'warning',
      message: 'Perishable cargo needs reefer',
      detail: 'Container should be temperature controlled',
      affectedFields: ['cargo.hs_code', 'cargo.temp_control_required'],
      action: 'Review',
    });
  }

  // 14. STACKABILITY_CHECK
  if (data.cargo.cargo_type?.toLowerCase().includes('fragile') && data.cargo.stackability) {
    issues.push({
      id: 'STACKABILITY_CHECK',
      severity: 'warning',
      message: 'Fragile items marked as stackable',
      detail: 'Fragile cargo typically non-stackable',
      affectedFields: ['cargo.cargo_type', 'cargo.stackability'],
      action: 'Review',
    });
  }

  // 15. WEIGHT_VOLUME_INCONSISTENT
  if (data.cargo.gross_weight_kg && data.cargo.volume_cbm) {
    const ratio = data.cargo.gross_weight_kg / data.cargo.volume_cbm;
    if (ratio < 50 || ratio > 1500) {
      issues.push({
        id: 'WEIGHT_VOLUME_INCONSISTENT',
        severity: 'warning',
        message: 'Weight/volume ratio unusual',
        detail: `Expected 50-1500 kg/CBM, got ${ratio.toFixed(0)}`,
        affectedFields: ['cargo.gross_weight_kg', 'cargo.volume_cbm'],
        action: 'Review',
      });
    }
  }

  // 16. PACKAGES_REQUIRED
  if (!data.cargo.packages || data.cargo.packages === 0) {
    issues.push({
      id: 'PACKAGES_REQUIRED',
      severity: 'warning',
      message: 'Package count missing',
      detail: 'Specify number of packages/pallets',
      affectedFields: ['cargo.packages'],
      action: 'Review',
    });
  }

  // 24. RISK_MODULES_OFF_FOR_LONG_ROUTE
  if (data.trade.transit_time_days > 30) {
    issues.push({
      id: 'RISK_MODULES_OFF_FOR_LONG_ROUTE',
      severity: 'suggestion',
      message: 'Long route, consider enabling modules',
      detail: 'Route >30 days benefits from risk tracking',
      affectedFields: ['trade.transit_time_days'],
      action: 'Enable',
    });
  }

  // 25. INSURANCE_ADVICE_HIGH_RISK
  if (data.value > 100000 || data.cargo.is_dg) {
    issues.push({
      id: 'INSURANCE_ADVICE_HIGH_RISK',
      severity: 'suggestion',
      message: 'Consider enabling insurance module',
      detail: 'Multiple risk factors detected',
      affectedFields: ['value', 'cargo.is_dg'],
      action: 'Enable',
    });
  }

  return issues;
}

