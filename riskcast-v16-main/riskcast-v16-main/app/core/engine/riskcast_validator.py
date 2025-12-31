"""
RiskCast V22 - Validator Module
================================
Comprehensive input validation with 60+ business rules

Author: RiskCast AI Team
Version: 22.0
License: Proprietary
"""

import re
from typing import Dict, List, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import Optional


# ============================================================================
# ENUMERATIONS
# ============================================================================

class ValidationSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ValidationResult:
    is_valid: bool
    severity: ValidationSeverity
    field: str
    message: str
    suggestion: Optional[str] = None


# ============================================================================
# VALIDATOR
# ============================================================================

class RiskCastV21Validator:
    """
    Comprehensive input validation with 60+ business rules
    """
    
    VALID_MODES = ['sea_freight', 'air_freight', 'road', 'rail', 'multimodal']
    
    VALID_SHIPMENT_TYPES = {
        'sea_freight': ['fcl', 'lcl', 'break_bulk', 'roro'],
        'air_freight': ['general', 'express', 'consolidated'],
        'road': ['ftl', 'ltl', 'express'],
        'rail': ['container', 'bulk']
    }
    
    VALID_PRIORITIES = ['fastest', 'cheapest', 'balanced', 'most_reliable']
    
    VALID_INCOTERMS = ['EXW', 'FCA', 'FAS', 'FOB', 'CFR', 'CIF', 'CPT', 'CIP', 'DAP', 'DPU', 'DDP']
    
    VALID_CONTAINER_TYPES = ['20ft', '40ft', '40hc', '45hc', '20rf', '40rf', '20ot', '40ot', 'flatbed', 'tank']
    
    VALID_CARGO_SENSITIVITY = ['standard', 'fragile', 'temperature', 'high_value', 'perishable', 'hazardous']
    
    VALID_INSURANCE_COVERAGE = ['icc_a', 'icc_b', 'icc_c', 'all_risks', 'basic', 'war_risks']
    
    INCOTERM_MODE_COMPATIBILITY = {
        'FAS': ['sea_freight'],
        'FOB': ['sea_freight'],
        'CFR': ['sea_freight'],
        'CIF': ['sea_freight']
    }
    
    DG_MODE_RESTRICTIONS = {
        'air_freight': ['class_1', 'class_7'],
        'road': ['class_7'],
        'rail': ['class_1']
    }
    
    def validate_full_input(self, data: Dict) -> Tuple[bool, List[ValidationResult]]:
        """
        Main validation orchestrator
        Returns: (is_valid, validation_results)
        """
        results = []
        
        results.extend(self._validate_transport(data.get('transport', {})))
        results.extend(self._validate_cargo(data.get('cargo', {})))
        results.extend(self._validate_party(data.get('seller', {}), 'seller'))
        
        if 'buyer' in data and data['buyer']:
            results.extend(self._validate_party(data.get('buyer', {}), 'buyer'))
        
        results.extend(self._validate_cross_field_rules(data))
        results.extend(self._validate_modules(data.get('modules', {})))
        
        has_errors = any(r.severity == ValidationSeverity.ERROR for r in results)
        is_valid = not has_errors
        
        return is_valid, results
    
    def _validate_transport(self, transport: Dict) -> List[ValidationResult]:
        """Validate transport section"""
        results = []
        
        required_fields = ['trade_lane', 'mode', 'shipment_type', 'carrier', 'priority', 
                          'incoterm', 'pol', 'pod', 'etd', 'transit_time']
        
        for field in required_fields:
            if not transport.get(field):
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    field=f"transport.{field}",
                    message=f"Required field '{field}' is missing",
                    suggestion=f"Provide valid {field} value"
                ))
        
        mode = transport.get('mode', '').lower()
        if mode and mode not in self.VALID_MODES:
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                field="transport.mode",
                message=f"Invalid mode: {mode}",
                suggestion=f"Valid modes: {', '.join(self.VALID_MODES)}"
            ))
        
        shipment_type = transport.get('shipment_type', '').lower()
        if mode and shipment_type:
            valid_types = self.VALID_SHIPMENT_TYPES.get(mode, [])
            if shipment_type not in valid_types:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    field="transport.shipment_type",
                    message=f"Shipment type '{shipment_type}' incompatible with mode '{mode}'",
                    suggestion=f"Valid types for {mode}: {', '.join(valid_types)}"
                ))
        
        priority = transport.get('priority', '').lower()
        if priority and priority not in self.VALID_PRIORITIES:
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.WARNING,
                field="transport.priority",
                message=f"Invalid priority: {priority}",
                suggestion=f"Valid priorities: {', '.join(self.VALID_PRIORITIES)}"
            ))
        
        incoterm = transport.get('incoterm', '').upper()
        if incoterm and incoterm not in self.VALID_INCOTERMS:
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                field="transport.incoterm",
                message=f"Invalid Incoterm: {incoterm}",
                suggestion=f"Valid Incoterms: {', '.join(self.VALID_INCOTERMS)}"
            ))
        
        if incoterm in self.INCOTERM_MODE_COMPATIBILITY:
            required_modes = self.INCOTERM_MODE_COMPATIBILITY[incoterm]
            if mode not in required_modes:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    field="transport.incoterm",
                    message=f"Incoterm {incoterm} typically used with {', '.join(required_modes)}",
                    suggestion="Consider FCA, CPT, or CIP for other transport modes"
                ))
        
        if incoterm in ['FCA', 'DAP', 'DPU', 'DDP']:
            if not transport.get('incoterm_location'):
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    field="transport.incoterm_location",
                    message=f"Incoterm {incoterm} requires specific location",
                    suggestion="Specify named place"
                ))
        
        if mode == 'sea_freight':
            container_type = transport.get('container_type', '').lower()
            if container_type and container_type not in self.VALID_CONTAINER_TYPES:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    field="transport.container_type",
                    message=f"Invalid container type: {container_type}",
                    suggestion=f"Valid types: {', '.join(self.VALID_CONTAINER_TYPES)}"
                ))
        
        etd = transport.get('etd')
        if etd:
            try:
                etd_date = datetime.strptime(etd, '%d/%m/%Y')
                if etd_date < datetime.now():
                    results.append(ValidationResult(
                        is_valid=False,
                        severity=ValidationSeverity.WARNING,
                        field="transport.etd",
                        message="ETD is in the past",
                        suggestion="Verify departure date"
                    ))
            except ValueError:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    field="transport.etd",
                    message="Invalid ETD format",
                    suggestion="Use format: dd/mm/yyyy"
                ))
        
        transit_time = transport.get('transit_time', 0)
        if transit_time:
            if mode == 'air_freight' and transit_time > 7:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    field="transport.transit_time",
                    message=f"Air freight transit time {transit_time} days seems high",
                    suggestion="Typical air freight: 1-5 days"
                ))
            elif mode == 'sea_freight' and transit_time < 5:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    field="transport.transit_time",
                    message=f"Sea freight transit time {transit_time} days seems low",
                    suggestion="Typical sea freight: 7-45 days"
                ))
        
        reliability = transport.get('reliability_score')
        if reliability is not None:
            if not (0 <= reliability <= 100):
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    field="transport.reliability_score",
                    message=f"Reliability score {reliability} out of range",
                    suggestion="Score must be between 0-100"
                ))
        
        return results
    
    def _validate_cargo(self, cargo: Dict) -> List[ValidationResult]:
        """Validate cargo section"""
        results = []
        
        required_fields = ['cargo_type', 'packing_type', 'packages', 
                          'gross_weight', 'volume_m3', 'insurance_value']
        
        for field in required_fields:
            if cargo.get(field) is None:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    field=f"cargo.{field}",
                    message=f"Required field '{field}' is missing",
                    suggestion=f"Provide valid {field} value"
                ))
        
        hs_code = cargo.get('hs_code', '')
        if hs_code:
            if not re.match(r'^\d{4,10}$', hs_code):
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    field="cargo.hs_code",
                    message="Invalid HS Code format",
                    suggestion="HS Code should be 4-10 digits"
                ))
        
        gross_weight = cargo.get('gross_weight', 0)
        net_weight = cargo.get('net_weight', 0)
        
        if gross_weight and net_weight:
            if net_weight > gross_weight:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    field="cargo.net_weight",
                    message="Net weight cannot exceed gross weight",
                    suggestion="Verify weight measurements"
                ))
            
            tare_weight = gross_weight - net_weight
            if tare_weight / gross_weight > 0.3:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    field="cargo.gross_weight",
                    message=f"High tare weight ratio: {tare_weight/gross_weight*100:.1f}%",
                    suggestion="Verify packaging weight"
                ))
        
        volume = cargo.get('volume_m3', 0)
        if volume and gross_weight:
            density = gross_weight / volume
            
            if density > 1000:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.INFO,
                    field="cargo.volume_m3",
                    message=f"High density cargo: {density:.0f} kg/m³",
                    suggestion="Consider weight-based freight charges"
                ))
            elif density < 100:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.INFO,
                    field="cargo.volume_m3",
                    message=f"Low density cargo: {density:.0f} kg/m³",
                    suggestion="Consider volumetric weight charges"
                ))
        
        sensitivity = cargo.get('sensitivity', '').lower()
        if sensitivity and sensitivity not in self.VALID_CARGO_SENSITIVITY:
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.WARNING,
                field="cargo.sensitivity",
                message=f"Invalid sensitivity: {sensitivity}",
                suggestion=f"Valid types: {', '.join(self.VALID_CARGO_SENSITIVITY)}"
            ))
        
        is_dg = cargo.get('dangerous_goods', False)
        if is_dg:
            if not cargo.get('hs_code'):
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    field="cargo.hs_code",
                    message="HS Code required for dangerous goods",
                    suggestion="Provide UN number or HS Code"
                ))
            
            if not cargo.get('special_instructions'):
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    field="cargo.special_instructions",
                    message="DG special instructions recommended",
                    suggestion="Include UN class, packing group"
                ))
        
        insurance_value = cargo.get('insurance_value', 0)
        if insurance_value and gross_weight:
            value_per_kg = insurance_value / gross_weight
            if value_per_kg < 1:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    field="cargo.insurance_value",
                    message=f"Low insurance value: ${value_per_kg:.2f}/kg",
                    suggestion="Verify cargo value"
                ))
        
        insurance_coverage = cargo.get('insurance_coverage', '').lower()
        if insurance_coverage and insurance_coverage not in self.VALID_INSURANCE_COVERAGE:
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.WARNING,
                field="cargo.insurance_coverage",
                message=f"Invalid insurance coverage: {insurance_coverage}",
                suggestion=f"Valid types: {', '.join(self.VALID_INSURANCE_COVERAGE)}"
            ))
        
        return results
    
    def _validate_party(self, party: Dict, role: str) -> List[ValidationResult]:
        """Validate seller/buyer information"""
        results = []
        
        required_fields = ['company_name', 'country', 'email', 'phone']
        
        for field in required_fields:
            if not party.get(field):
                severity = ValidationSeverity.ERROR if role == 'seller' else ValidationSeverity.WARNING
                results.append(ValidationResult(
                    is_valid=False,
                    severity=severity,
                    field=f"{role}.{field}",
                    message=f"{role.title()} {field} is missing",
                    suggestion=f"Provide {role} {field}"
                ))
        
        email = party.get('email', '')
        if email:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    field=f"{role}.email",
                    message=f"Invalid email format: {email}",
                    suggestion="Use valid email format"
                ))
        
        phone = party.get('phone', '')
        if phone:
            phone_clean = re.sub(r'[^\d+]', '', phone)
            if len(phone_clean) < 8:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.INFO,
                    field=f"{role}.phone",
                    message="Phone should include country code",
                    suggestion="Use international format"
                ))
        
        tax_id = party.get('tax_id', '')
        if tax_id and len(tax_id) < 5:
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.WARNING,
                field=f"{role}.tax_id",
                message="Tax ID seems too short",
                suggestion="Verify Tax ID format"
            ))
        
        return results
    
    def _validate_cross_field_rules(self, data: Dict) -> List[ValidationResult]:
        """Validate business rules across sections"""
        results = []
        
        transport = data.get('transport', {})
        cargo = data.get('cargo', {})
        
        if cargo.get('dangerous_goods'):
            mode = transport.get('mode', '').lower()
            if mode in self.DG_MODE_RESTRICTIONS:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    field="cargo.dangerous_goods",
                    message=f"DG may have restrictions for {mode}",
                    suggestion="Verify DG class compatibility"
                ))
        
        if cargo.get('sensitivity') in ['temperature', 'perishable']:
            container_type = transport.get('container_type', '').lower()
            if mode := transport.get('mode', '').lower():
                if mode == 'sea_freight' and 'rf' not in container_type:
                    results.append(ValidationResult(
                        is_valid=False,
                        severity=ValidationSeverity.ERROR,
                        field="transport.container_type",
                        message="Temperature cargo requires reefer",
                        suggestion="Select reefer container (20RF/40RF)"
                    ))
            
            transit_time = transport.get('transit_time', 0)
            if transit_time > 30:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    field="transport.transit_time",
                    message=f"Long transit ({transit_time}d) for perishable",
                    suggestion="Consider faster routing"
                ))
        
        insurance_value = cargo.get('insurance_value', 0)
        if insurance_value > 500000:
            coverage = cargo.get('insurance_coverage', '').lower()
            if coverage not in ['icc_a', 'all_risks']:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    field="cargo.insurance_coverage",
                    message="High-value cargo needs comprehensive coverage",
                    suggestion="Use ICC A or All Risks"
                ))
        
        priority = transport.get('priority', '').lower()
        mode = transport.get('mode', '').lower()
        if priority == 'fastest' and mode == 'sea_freight':
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.INFO,
                field="transport.priority",
                message="'Fastest' with sea freight may not meet expectations",
                suggestion="Consider air freight for urgent shipments"
            ))
        
        return results
    
    def _validate_modules(self, modules: Dict) -> List[ValidationResult]:
        """Validate module configuration"""
        results = []
        
        valid_modules = ['esg', 'weather_climate', 'port_congestion', 
                        'carrier_performance', 'market_condition', 
                        'insurance_optimization', 'monte_carlo', 'stress_test']
        
        for module in modules.keys():
            if module not in valid_modules:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    field=f"modules.{module}",
                    message=f"Unknown module: {module}",
                    suggestion=f"Valid modules: {', '.join(valid_modules)}"
                ))
        
        return results






