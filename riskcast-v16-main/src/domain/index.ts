/**
 * Domain Layer - Single Source of Truth for Case Data
 * 
 * Exports:
 * - DomainCase schema
 * - Mapper functions (Input → DomainCase → View Models)
 * - Validation utilities
 * - Port lookup utilities
 */

export * from './case.schema';
export * from './case.mapper';
export * from './case.validation';
export * from './port-lookup';
