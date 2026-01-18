/**
 * Case Validation - Validation utilities for DomainCase
 */

import type { DomainCase } from './case.schema';
import type { ValidationIssue } from '@/lib/validation';

/**
 * Validate DomainCase and return validation issues
 */
export function validateDomainCase(caseData: Partial<DomainCase>): {
  valid: boolean;
  issues: ValidationIssue[];
} {
  const issues: ValidationIssue[] = [];
  
  // Required fields
  if (!caseData.pol || caseData.pol.trim() === '') {
    issues.push({
      id: 'POL_REQUIRED',
      severity: 'critical',
      message: 'POL (Port of Loading) is required',
      detail: 'Please specify the origin port',
      affectedFields: ['pol'],
    });
  }
  
  if (!caseData.pod || caseData.pod.trim() === '') {
    issues.push({
      id: 'POD_REQUIRED',
      severity: 'critical',
      message: 'POD (Port of Discharge) is required',
      detail: 'Please specify the destination port',
      affectedFields: ['pod'],
    });
  }
  
  if (!caseData.transportMode) {
    issues.push({
      id: 'TRANSPORT_MODE_REQUIRED',
      severity: 'critical',
      message: 'Transport mode is required',
      detail: 'Please select AIR, SEA, ROAD, RAIL, or MULTIMODAL',
      affectedFields: ['transportMode'],
    });
  }
  
  if (!caseData.containerType || caseData.containerType.trim() === '') {
    issues.push({
      id: 'CONTAINER_TYPE_REQUIRED',
      severity: 'critical',
      message: 'Container type is required',
      detail: 'Please specify container type',
      affectedFields: ['containerType'],
    });
  }
  
  if (!caseData.etd) {
    issues.push({
      id: 'ETD_REQUIRED',
      severity: 'critical',
      message: 'ETD (Estimated Time of Departure) is required',
      detail: 'Please specify departure date',
      affectedFields: ['etd'],
    });
  }
  
  // Date validation
  if (caseData.etd) {
    try {
      const etdDate = new Date(caseData.etd);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      if (isNaN(etdDate.getTime())) {
        issues.push({
          id: 'ETD_INVALID',
          severity: 'critical',
          message: 'Invalid ETD date format',
          detail: 'ETD must be a valid date (YYYY-MM-DD)',
          affectedFields: ['etd'],
        });
      } else if (etdDate < today) {
        issues.push({
          id: 'ETD_IN_PAST',
          severity: 'critical',
          message: 'Departure date is in the past',
          detail: 'ETD must be today or future date',
          affectedFields: ['etd'],
        });
      }
      
      // ETA validation
      if (caseData.eta) {
        const etaDate = new Date(caseData.eta);
        if (!isNaN(etaDate.getTime()) && etaDate <= etdDate) {
          issues.push({
            id: 'ETA_BEFORE_ETD',
            severity: 'critical',
            message: 'Arrival before departure',
            detail: 'ETA must be after ETD',
            affectedFields: ['eta', 'etd'],
          });
        }
      }
    } catch (e) {
      // Invalid date format
      issues.push({
        id: 'ETD_INVALID',
        severity: 'critical',
        message: 'Invalid ETD date format',
        detail: 'ETD must be a valid date (YYYY-MM-DD)',
        affectedFields: ['etd'],
      });
    }
  }
  
  // Cargo validation
  if (!caseData.cargoType || caseData.cargoType.trim() === '') {
    issues.push({
      id: 'CARGO_TYPE_REQUIRED',
      severity: 'critical',
      message: 'Cargo type is required',
      detail: 'Please specify cargo type',
      affectedFields: ['cargoType'],
    });
  }
  
  if (!caseData.packages || caseData.packages < 1) {
    issues.push({
      id: 'PACKAGES_REQUIRED',
      severity: 'critical',
      message: 'Package count must be at least 1',
      detail: 'Please specify number of packages',
      affectedFields: ['packages'],
    });
  }
  
  if (caseData.cargoValue === undefined || caseData.cargoValue < 0) {
    issues.push({
      id: 'CARGO_VALUE_INVALID',
      severity: 'critical',
      message: 'Cargo value must be >= 0',
      detail: 'Please specify cargo value',
      affectedFields: ['cargoValue'],
    });
  }
  
  // Weight validation
  if (caseData.netWeightKg !== undefined && caseData.grossWeightKg !== undefined) {
    if (caseData.netWeightKg > caseData.grossWeightKg) {
      issues.push({
        id: 'NET_WEIGHT_EXCEEDS_GROSS',
        severity: 'critical',
        message: 'Net weight exceeds gross weight',
        detail: 'Net weight must be ≤ Gross weight',
        affectedFields: ['grossWeightKg', 'netWeightKg'],
      });
    }
  }
  
  // Party validation
  if (!caseData.seller?.company || caseData.seller.company.trim() === '') {
    issues.push({
      id: 'SELLER_COMPANY_REQUIRED',
      severity: 'critical',
      message: 'Seller company name is required',
      detail: 'Please specify seller company',
      affectedFields: ['seller.company'],
    });
  }
  
  if (!caseData.seller?.email || caseData.seller.email.trim() === '') {
    issues.push({
      id: 'SELLER_EMAIL_REQUIRED',
      severity: 'critical',
      message: 'Seller email is required',
      detail: 'Please specify seller email',
      affectedFields: ['seller.email'],
    });
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(caseData.seller.email)) {
    issues.push({
      id: 'SELLER_EMAIL_INVALID',
      severity: 'critical',
      message: 'Invalid seller email format',
      detail: 'Email must be valid format (e.g., name@example.com)',
      affectedFields: ['seller.email'],
    });
  }
  
  if (!caseData.buyer?.company || caseData.buyer.company.trim() === '') {
    issues.push({
      id: 'BUYER_COMPANY_REQUIRED',
      severity: 'critical',
      message: 'Buyer company name is required',
      detail: 'Please specify buyer company',
      affectedFields: ['buyer.company'],
    });
  }
  
  if (!caseData.buyer?.email || caseData.buyer.email.trim() === '') {
    issues.push({
      id: 'BUYER_EMAIL_REQUIRED',
      severity: 'critical',
      message: 'Buyer email is required',
      detail: 'Please specify buyer email',
      affectedFields: ['buyer.email'],
    });
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(caseData.buyer.email)) {
    issues.push({
      id: 'BUYER_EMAIL_INVALID',
      severity: 'critical',
      message: 'Invalid buyer email format',
      detail: 'Email must be valid format (e.g., name@example.com)',
      affectedFields: ['buyer.email'],
    });
  }
  
  // Transit time validation (warnings)
  if (caseData.transitTimeDays !== undefined && caseData.transitTimeDays > 0) {
    if (caseData.transportMode === 'SEA' && (caseData.transitTimeDays < 3 || caseData.transitTimeDays > 90)) {
      issues.push({
        id: 'TRANSIT_TIME_OUTLIER_SEA',
        severity: 'warning',
        message: 'Transit time seems unusual for SEA',
        detail: 'SEA typically 3-90 days',
        affectedFields: ['transitTimeDays'],
      });
    } else if (caseData.transportMode === 'AIR' && caseData.transitTimeDays >= 15) {
      issues.push({
        id: 'TRANSIT_TIME_OUTLIER_AIR',
        severity: 'warning',
        message: 'Transit time seems unusual for AIR',
        detail: 'AIR typically < 15 days',
        affectedFields: ['transitTimeDays'],
      });
    }
  }
  
  const valid = issues.filter(i => i.severity === 'critical').length === 0;
  return { valid, issues };
}

/**
 * Calculate completeness score (0-100) based on required fields
 */
export function getCompletenessScore(caseData: Partial<DomainCase>): number {
  const requiredFields: Array<keyof DomainCase> = [
    'pol', 'pod', 'transportMode', 'containerType', 'etd',
    'cargoType', 'packages', 'cargoValue',
    'seller', 'buyer',
  ];
  
  let filledCount = 0;
  
  for (const field of requiredFields) {
    const value = caseData[field];
    
    if (field === 'seller' || field === 'buyer') {
      const party = value as DomainCase['seller'];
      if (party?.company && party?.email && party?.phone && party?.country) {
        filledCount++;
      }
    } else if (value !== undefined && value !== null && value !== '') {
      filledCount++;
    }
  }
  
  return Math.round((filledCount / requiredFields.length) * 100);
}
