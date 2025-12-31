"""
RiskCast V21 AI Risk Engine
===========================
Production-ready supply chain risk assessment engine with comprehensive
validation, multi-layer scoring, predictive analytics, and optimization.

Author: RiskCast AI Team
Version: 21.0
License: Proprietary
"""

import re
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


# ============================================================================
# ENUMERATIONS
# ============================================================================

class ValidationSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskCategory(Enum):
    TRANSPORT = "transport"
    CARGO = "cargo"
    COMMERCIAL = "commercial"
    COMPLIANCE = "compliance"
    EXTERNAL = "external"


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


@dataclass
class RiskLayer:
    name: str
    category: RiskCategory
    weight: float
    score: float
    severity: str
    impact_type: str
    description: str


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
                        'insurance_optimization']
        
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


# ============================================================================
# RISK SCORING ENGINE
# ============================================================================

class RiskScoringEngineV21:
    """
    Multi-layer risk scoring engine with 16 risk dimensions
    """
    
    RISK_LAYERS = {
        'mode_reliability': {
            'weight': 0.10,
            'category': RiskCategory.TRANSPORT,
            'description': 'Transport mode inherent reliability'
        },
        'carrier_performance': {
            'weight': 0.12,
            'category': RiskCategory.TRANSPORT,
            'description': 'Carrier on-time performance'
        },
        'route_complexity': {
            'weight': 0.08,
            'category': RiskCategory.TRANSPORT,
            'description': 'Route distance and complexity'
        },
        'transit_time_variance': {
            'weight': 0.05,
            'category': RiskCategory.TRANSPORT,
            'description': 'Schedule reliability'
        },
        'cargo_sensitivity': {
            'weight': 0.12,
            'category': RiskCategory.CARGO,
            'description': 'Cargo fragility and handling'
        },
        'packing_quality': {
            'weight': 0.08,
            'category': RiskCategory.CARGO,
            'description': 'Packaging adequacy'
        },
        'dg_compliance': {
            'weight': 0.05,
            'category': RiskCategory.CARGO,
            'description': 'Dangerous goods handling'
        },
        'incoterm_risk': {
            'weight': 0.08,
            'category': RiskCategory.COMMERCIAL,
            'description': 'Incoterm responsibility'
        },
        'seller_credibility': {
            'weight': 0.06,
            'category': RiskCategory.COMMERCIAL,
            'description': 'Seller reliability'
        },
        'buyer_credibility': {
            'weight': 0.04,
            'category': RiskCategory.COMMERCIAL,
            'description': 'Buyer reliability'
        },
        'insurance_adequacy': {
            'weight': 0.02,
            'category': RiskCategory.COMMERCIAL,
            'description': 'Insurance coverage'
        },
        'documentation_complexity': {
            'weight': 0.05,
            'category': RiskCategory.COMPLIANCE,
            'description': 'Customs requirements'
        },
        'trade_compliance': {
            'weight': 0.05,
            'category': RiskCategory.COMPLIANCE,
            'description': 'Trade restrictions'
        },
        'port_congestion': {
            'weight': 0.04,
            'category': RiskCategory.EXTERNAL,
            'description': 'Port efficiency'
        },
        'weather_climate': {
            'weight': 0.03,
            'category': RiskCategory.EXTERNAL,
            'description': 'Weather disruption'
        },
        'market_volatility': {
            'weight': 0.03,
            'category': RiskCategory.EXTERNAL,
            'description': 'Market fluctuations'
        }
    }
    
    MODE_RISK_SCORES = {
        'air_freight': 25,
        'sea_freight': 45,
        'rail': 40,
        'road': 50,
        'multimodal': 55
    }
    
    CARGO_SENSITIVITY_SCORES = {
        'standard': 20,
        'fragile': 55,
        'temperature': 65,
        'perishable': 70,
        'high_value': 60,
        'hazardous': 75
    }
    
    INCOTERM_RISK_SCORES = {
        'EXW': 85,
        'FCA': 70,
        'FAS': 65,
        'FOB': 60,
        'CFR': 45,
        'CIF': 40,
        'CPT': 45,
        'CIP': 40,
        'DAP': 30,
        'DPU': 25,
        'DDP': 20
    }
    
    PORT_RISK_DB = {
        'VNSGN': 55,
        'VNHPH': 50,
        'CNYTN': 60,
        'CNSHA': 50,
        'USLAX': 70,
        'USNYC': 55,
        'SGSIN': 25,
        'NLRTM': 30,
    }
    
    def calculate_comprehensive_risk(self, 
                                    validated_data: Dict,
                                    modules_enabled: Dict) -> Dict:
        """
        Main scoring orchestrator
        """
        
        transport = validated_data.get('transport', {})
        cargo = validated_data.get('cargo', {})
        seller = validated_data.get('seller', {})
        buyer = validated_data.get('buyer', {})
        
        layer_scores = {}
        
        mode = transport.get('mode', 'sea_freight')
        mode_base_score = self.MODE_RISK_SCORES.get(mode, 50)
        
        carrier_reliability = transport.get('reliability_score')
        if carrier_reliability:
            mode_score = mode_base_score * (1 - (carrier_reliability - 50) / 100 * 0.3)
        else:
            mode_score = mode_base_score
        
        layer_scores['mode_reliability'] = np.clip(mode_score, 0, 100)
        
        if carrier_reliability:
            carrier_score = 100 - carrier_reliability
        else:
            carrier_score = 50
        
        priority = transport.get('priority', 'balanced')
        if priority == 'fastest':
            carrier_score *= 0.85
        elif priority == 'cheapest':
            carrier_score *= 1.15
        
        layer_scores['carrier_performance'] = np.clip(carrier_score, 0, 100)
        
        transit_time = transport.get('transit_time', 0)
        
        if mode == 'air_freight':
            route_base = 20
        elif mode == 'sea_freight':
            route_base = 40
        elif mode == 'multimodal':
            route_base = 60
        else:
            route_base = 45
        
        if transit_time > 30:
            route_score = route_base * 1.3
        elif transit_time > 14:
            route_score = route_base * 1.1
        else:
            route_score = route_base * 0.9
        
        layer_scores['route_complexity'] = np.clip(route_score, 0, 100)
        
        schedule = transport.get('schedule_frequency', '').lower()
        if 'daily' in schedule:
            variance_score = 20
        elif 'weekly' in schedule:
            variance_score = 35
        elif 'biweekly' in schedule or 'fortnightly' in schedule:
            variance_score = 50
        else:
            variance_score = 45
        
        layer_scores['transit_time_variance'] = variance_score
        
        sensitivity = cargo.get('sensitivity', 'standard')
        cargo_base_score = self.CARGO_SENSITIVITY_SCORES.get(sensitivity, 40)
        
        insurance_coverage = cargo.get('insurance_coverage', '').lower()
        if insurance_coverage in ['icc_a', 'all_risks']:
            cargo_score = cargo_base_score * 0.85
        elif insurance_coverage in ['basic', 'icc_c']:
            cargo_score = cargo_base_score * 1.1
        else:
            cargo_score = cargo_base_score
        
        layer_scores['cargo_sensitivity'] = np.clip(cargo_score, 0, 100)
        
        packing_type = cargo.get('packing_type', '').lower()
        stackable = cargo.get('stackability', True)
        
        if packing_type in ['pallet', 'crate', 'container']:
            packing_score = 25
        elif packing_type in ['carton', 'box']:
            packing_score = 40
        elif packing_type in ['bag', 'bulk']:
            packing_score = 60
        else:
            packing_score = 50
        
        if not stackable:
            packing_score *= 1.2
        
        layer_scores['packing_quality'] = np.clip(packing_score, 0, 100)
        
        is_dg = cargo.get('dangerous_goods', False)
        if is_dg:
            dg_score = 70
            
            if cargo.get('special_instructions'):
                dg_score *= 0.85
            
            if mode == 'air_freight':
                dg_score *= 1.2
        else:
            dg_score = 10
        
        layer_scores['dg_compliance'] = np.clip(dg_score, 0, 100)
        
        incoterm = transport.get('incoterm', 'FOB').upper()
        incoterm_score = self.INCOTERM_RISK_SCORES.get(incoterm, 50)
        
        layer_scores['incoterm_risk'] = incoterm_score
        
        seller_score = self._assess_party_credibility(seller, 'seller')
        layer_scores['seller_credibility'] = seller_score
        
        buyer_score = self._assess_party_credibility(buyer, 'buyer')
        layer_scores['buyer_credibility'] = buyer_score
        
        insurance_value = cargo.get('insurance_value', 0)
        gross_weight = cargo.get('gross_weight', 1)
        
        value_per_kg = insurance_value / gross_weight if gross_weight > 0 else 0
        
        if value_per_kg < 5:
            insurance_score = 60
        elif value_per_kg < 50:
            insurance_score = 30
        elif value_per_kg < 200:
            insurance_score = 20
        else:
            insurance_score = 15
        
        if insurance_coverage in ['icc_a', 'all_risks']:
            insurance_score *= 0.8
        elif insurance_coverage in ['basic', 'icc_c']:
            insurance_score *= 1.3
        
        layer_scores['insurance_adequacy'] = np.clip(insurance_score, 0, 100)
        
        doc_score = self._calculate_documentation_complexity(transport, cargo)
        layer_scores['documentation_complexity'] = doc_score
        
        trade_score = self._calculate_trade_compliance_risk(
            seller.get('country', ''),
            buyer.get('country', ''),
            cargo
        )
        layer_scores['trade_compliance'] = trade_score
        
        if modules_enabled.get('port_congestion', False):
            port_score = self._calculate_port_risk(
                transport.get('pol', ''),
                transport.get('pod', '')
            )
        else:
            port_score = 40
        
        layer_scores['port_congestion'] = port_score
        
        if modules_enabled.get('weather_climate', False):
            weather_score = self._calculate_weather_risk(transport, cargo)
        else:
            weather_score = 35
        
        layer_scores['weather_climate'] = weather_score
        
        if modules_enabled.get('market_condition', False):
            market_score = self._calculate_market_risk(transport, cargo)
        else:
            market_score = 40
        
        layer_scores['market_volatility'] = market_score
        
        overall_score = 0
        for layer_name, layer_def in self.RISK_LAYERS.items():
            score = layer_scores.get(layer_name, 50)
            weight = layer_def['weight']
            overall_score += score * weight
        
        if overall_score < 30:
            risk_level = 'low'
        elif overall_score < 50:
            risk_level = 'medium'
        elif overall_score < 70:
            risk_level = 'high'
        else:
            risk_level = 'critical'
        
        category_scores = self._aggregate_by_category(layer_scores)
        
        recommendations = self._generate_recommendations(
            layer_scores, 
            category_scores,
            validated_data
        )
        
        mitigation_plan = self._generate_mitigation_plan(
            layer_scores,
            risk_level,
            validated_data
        )
        
        return {
            'overall_score': round(overall_score, 2),
            'risk_level': risk_level,
            'risk_grade': self._score_to_grade(overall_score),
            'layer_scores': {k: round(v, 2) for k, v in layer_scores.items()},
            'category_scores': category_scores,
            'recommendations': recommendations,
            'mitigation_plan': mitigation_plan,
            'financial_impact': self._estimate_financial_impact(
                overall_score, 
                cargo.get('insurance_value', 0)
            )
        }
    
    def _assess_party_credibility(self, party: Dict, role: str) -> float:
        """Assess seller/buyer credibility"""
        
        if not party:
            return 60
        
        score = 50
        
        if party.get('tax_id'):
            score -= 10
        
        business_type = party.get('business_type', '').lower()
        if 'manufacturer' in business_type or 'corporation' in business_type:
            score -= 5
        elif 'trading' in business_type or 'agent' in business_type:
            score += 5
        
        if party.get('email') and party.get('phone'):
            score -= 5
        
        if party.get('address') and party.get('city'):
            score -= 5
        
        return np.clip(score, 0, 100)
    
    def _calculate_documentation_complexity(self, 
                                           transport: Dict, 
                                           cargo: Dict) -> float:
        """Calculate documentation complexity"""
        
        complexity_score = 30
        
        if cargo.get('dangerous_goods'):
            complexity_score += 20
        
        if cargo.get('insurance_value', 0) > 100000:
            complexity_score += 10
        
        mode = transport.get('mode', '')
        if mode == 'air_freight':
            complexity_score += 5
        elif mode == 'multimodal':
            complexity_score += 15
        
        incoterm = transport.get('incoterm', '').upper()
        if incoterm in ['DDP', 'DAP', 'DPU']:
            complexity_score += 10
        
        return np.clip(complexity_score, 0, 100)
    
    def _calculate_trade_compliance_risk(self,
                                         seller_country: str,
                                         buyer_country: str,
                                         cargo: Dict) -> float:
        """Calculate trade compliance risk"""
        
        risk_score = 25
        
        high_risk_countries = ['kp', 'ir', 'sy', 'cu']
        medium_risk_countries = ['ve', 'by', 'mm']
        
        if seller_country.lower() in high_risk_countries:
            risk_score += 50
        elif seller_country.lower() in medium_risk_countries:
            risk_score += 25
        
        if buyer_country.lower() in high_risk_countries:
            risk_score += 50
        elif buyer_country.lower() in medium_risk_countries:
            risk_score += 25
        
        if cargo.get('dangerous_goods'):
            risk_score += 15
        
        if cargo.get('insurance_value', 0) > 50000:
            risk_score += 10
        
        return np.clip(risk_score, 0, 100)
    
    def _calculate_port_risk(self, pol: str, pod: str) -> float:
        """Calculate port congestion risk"""
        
        pol_risk = self.PORT_RISK_DB.get(pol.upper(), 45)
        pod_risk = self.PORT_RISK_DB.get(pod.upper(), 45)
        
        avg_risk = (pol_risk * 0.4 + pod_risk * 0.6)
        
        return avg_risk
    
    def _calculate_weather_risk(self, transport: Dict, cargo: Dict) -> float:
        """Calculate weather disruption risk"""
        
        risk_score = 30
        
        mode = transport.get('mode', '')
        if mode == 'sea_freight':
            risk_score += 15
        elif mode == 'air_freight':
            risk_score += 10
        elif mode == 'road':
            risk_score += 5
        
        sensitivity = cargo.get('sensitivity', '')
        if sensitivity in ['temperature', 'perishable']:
            risk_score += 20
        
        etd = transport.get('etd', '')
        if etd:
            try:
                etd_date = datetime.strptime(etd, '%d/%m/%Y')
                month = etd_date.month
                
                if 6 <= month <= 11:
                    risk_score += 10
            except:
                pass
        
        return np.clip(risk_score, 0, 100)
    
    def _calculate_market_risk(self, transport: Dict, cargo: Dict) -> float:
        """Calculate market volatility risk"""
        
        risk_score = 40
        
        mode = transport.get('mode', '')
        if mode == 'air_freight':
            risk_score += 10
        elif mode == 'sea_freight':
            risk_score += 5
        
        priority = transport.get('priority', '')
        if priority == 'fastest':
            risk_score += 10
        elif priority == 'cheapest':
            risk_score -= 5
        
        if cargo.get('insurance_value', 0) > 100000:
            risk_score += 5
        
        return np.clip(risk_score, 0, 100)
    
    def _aggregate_by_category(self, layer_scores: Dict) -> Dict:
        """Aggregate scores by category"""
        
        category_sums = {}
        category_weights = {}
        
        for layer_name, layer_def in self.RISK_LAYERS.items():
            category = layer_def['category'].value
            score = layer_scores.get(layer_name, 50)
            weight = layer_def['weight']
            
            if category not in category_sums:
                category_sums[category] = 0
                category_weights[category] = 0
            
            category_sums[category] += score * weight
            category_weights[category] += weight
        
        category_scores = {}
        for category, total in category_sums.items():
            weight = category_weights[category]
            category_scores[category] = round(total / weight, 2) if weight > 0 else 50
        
        return category_scores
    
    def _score_to_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score < 20:
            return 'A+'
        elif score < 30:
            return 'A'
        elif score < 40:
            return 'B+'
        elif score < 50:
            return 'B'
        elif score < 60:
            return 'C+'
        elif score < 70:
            return 'C'
        elif score < 80:
            return 'D'
        else:
            return 'F'
    
    def _generate_recommendations(self,
                                 layer_scores: Dict,
                                 category_scores: Dict,
                                 data: Dict) -> List[Dict]:
        """Generate prioritized recommendations"""
        
        recommendations = []
        
        sorted_layers = sorted(layer_scores.items(), 
                              key=lambda x: x[1], 
                              reverse=True)
        
        for layer_name, score in sorted_layers[:5]:
            if score > 60:
                layer_def = self.RISK_LAYERS.get(layer_name, {})
                
                rec = {
                    'layer': layer_name,
                    'risk_score': score,
                    'category': layer_def.get('category', RiskCategory.EXTERNAL).value,
                    'priority': 'HIGH' if score > 70 else 'MEDIUM',
                    'action': self._get_mitigation_action(layer_name, score, data)
                }
                recommendations.append(rec)
        
        return recommendations
    
    def _get_mitigation_action(self, 
                               layer_name: str, 
                               score: float,
                               data: Dict) -> str:
        """Get mitigation action for risk layer"""
        
        actions = {
            'mode_reliability': "Consider alternative transport mode",
            'carrier_performance': "Upgrade to premium carrier",
            'route_complexity': "Optimize routing to reduce transit time",
            'transit_time_variance': "Select guaranteed delivery services",
            'cargo_sensitivity': "Upgrade packaging protection",
            'packing_quality': "Use certified packing services",
            'dg_compliance': "Engage DG specialist for compliance",
            'incoterm_risk': "Review Incoterm allocation",
            'seller_credibility': "Conduct due diligence verification",
            'buyer_credibility': "Request payment guarantees",
            'insurance_adequacy': "Increase coverage to All Risks",
            'documentation_complexity': "Hire customs broker",
            'trade_compliance': "Conduct sanctions screening",
            'port_congestion': "Book priority berthing services",
            'weather_climate': "Monitor forecasts and arrange contingency",
            'market_volatility': "Lock in rates with contracts"
        }
        
        return actions.get(layer_name, "Implement mitigation measures")
    
    def _generate_mitigation_plan(self,
                                 layer_scores: Dict,
                                 risk_level: str,
                                 data: Dict) -> Dict:
        """Generate mitigation action plan"""
        
        plan = {
            'immediate_actions': [],
            'short_term_actions': [],
            'long_term_actions': [],
            'estimated_cost': 0,
            'expected_risk_reduction': 0
        }
        
        if risk_level in ['high', 'critical']:
            if layer_scores.get('carrier_performance', 0) > 60:
                plan['immediate_actions'].append({
                    'action': 'Upgrade carrier to premium tier',
                    'deadline': '48 hours',
                    'cost_usd': 2500,
                    'risk_reduction': 15
                })
            
            if layer_scores.get('insurance_adequacy', 0) > 60:
                plan['immediate_actions'].append({
                    'action': 'Increase insurance to All Risks',
                    'deadline': 'Before departure',
                    'cost_usd': 1200,
                    'risk_reduction': 10
                })
        
        if layer_scores.get('documentation_complexity', 0) > 50:
            plan['short_term_actions'].append({
                'action': 'Engage customs broker',
                'timeline': '1-2 weeks',
                'cost_usd': 800,
                'risk_reduction': 8
            })
        
        if layer_scores.get('packing_quality', 0) > 50:
            plan['short_term_actions'].append({
                'action': 'Upgrade packaging materials',
                'timeline': '1 week',
                'cost_usd': 500,
                'risk_reduction': 12
            })
        
        plan['long_term_actions'].append({
            'action': 'Establish preferred carrier partnerships',
            'timeline': '3-6 months',
            'benefit': 'Consistent quality and rates'
        })
        
        plan['estimated_cost'] = sum(
            a['cost_usd'] for a in plan['immediate_actions'] + plan['short_term_actions']
        )
        
        plan['expected_risk_reduction'] = sum(
            a['risk_reduction'] for a in plan['immediate_actions'] + plan['short_term_actions']
        )
        
        return plan
    
    def _estimate_financial_impact(self, 
                                   risk_score: float,
                                   cargo_value: float) -> Dict:
        """Estimate financial impact"""
        
        if risk_score < 30:
            loss_probability = 0.02
            avg_loss_pct = 0.05
        elif risk_score < 50:
            loss_probability = 0.08
            avg_loss_pct = 0.12
        elif risk_score < 70:
            loss_probability = 0.15
            avg_loss_pct = 0.25
        else:
            loss_probability = 0.30
            avg_loss_pct = 0.40
        
        expected_loss = cargo_value * loss_probability * avg_loss_pct
        
        return {
            'expected_loss_usd': round(expected_loss, 2),
            'loss_probability': round(loss_probability * 100, 2),
            'avg_loss_if_incident': round(cargo_value * avg_loss_pct, 2),
            'var_95_usd': round(cargo_value * 0.15, 2),
            'max_exposure_usd': cargo_value
        }


# ============================================================================
# ENHANCED ALGORITHMIC FEATURES
# ============================================================================

class EnhancedAlgorithmicFeaturesV21:
    """
    Advanced AI-like features for optimization and prediction
    """
    
    @staticmethod
    def dynamic_weight_adjustment(layer_scores: Dict, 
                                 priority: str,
                                 cargo_value: float) -> Dict:
        """
        Dynamically adjust layer weights based on context
        """
        
        adjusted_weights = {}
        for layer_name, layer_def in RiskScoringEngineV21.RISK_LAYERS.items():
            adjusted_weights[layer_name] = layer_def.copy()
        
        if cargo_value > 500000:
            adjusted_weights['insurance_adequacy']['weight'] *= 1.5
            adjusted_weights['cargo_sensitivity']['weight'] *= 1.3
        
        if priority == 'fastest':
            adjusted_weights['transit_time_variance']['weight'] *= 1.4
            adjusted_weights['carrier_performance']['weight'] *= 1.3
        elif priority == 'cheapest':
            adjusted_weights['market_volatility']['weight'] *= 1.2
        
        total_weight = sum(l['weight'] for l in adjusted_weights.values())
        for layer in adjusted_weights.values():
            layer['weight'] /= total_weight
        
        return adjusted_weights
    
    @staticmethod
    def predictive_delay_model(transport: Dict, 
                               layer_scores: Dict) -> Dict:
        """
        ML-style delay prediction model
        """
        
        base_transit = transport.get('transit_time', 14)
        
        delay_factors = {
            'carrier_performance': layer_scores.get('carrier_performance', 50) / 100 * 0.15,
            'port_congestion': layer_scores.get('port_congestion', 40) / 100 * 0.20,
            'weather_climate': layer_scores.get('weather_climate', 35) / 100 * 0.10,
            'documentation': layer_scores.get('documentation_complexity', 40) / 100 * 0.08
        }
        
        total_delay_factor = sum(delay_factors.values())
        
        expected_delay_days = base_transit * total_delay_factor
        
        delay_probability = min(0.95, total_delay_factor * 1.5)
        
        return {
            'expected_transit_days': round(base_transit + expected_delay_days, 1),
            'delay_probability': round(delay_probability * 100, 1),
            'p50_delay': round(expected_delay_days * 0.7, 1),
            'p95_delay': round(expected_delay_days * 2.0, 1),
            'delay_breakdown': {k: round(v * base_transit, 2) for k, v in delay_factors.items()}
        }
    
    @staticmethod
    def route_optimization_suggestions(transport: Dict,
                                      layer_scores: Dict) -> List[Dict]:
        """
        Suggest alternative routes/modes
        """
        
        suggestions = []
        current_mode = transport.get('mode', 'sea_freight')
        
        if current_mode == 'sea_freight':
            if layer_scores.get('transit_time_variance', 0) > 60:
                suggestions.append({
                    'alternative': 'air_freight',
                    'benefit': 'Reduce transit time by 70%',
                    'trade_off': 'Cost increase ~4-5x',
                    'risk_reduction': 25
                })
        
        if layer_scores.get('carrier_performance', 0) > 65:
            suggestions.append({
                'alternative': 'premium_carrier',
                'benefit': 'Improve on-time rate to 95%+',
                'trade_off': 'Cost increase ~15-20%',
                'risk_reduction': 15
            })
        
        if layer_scores.get('port_congestion', 0) > 65:
            suggestions.append({
                'alternative': 'alternative_port',
                'benefit': 'Avoid congested ports',
                'trade_off': 'Possible longer inland transport',
                'risk_reduction': 12
            })
        
        return suggestions
    
    @staticmethod
    def insurance_optimization(cargo: Dict, 
                              layer_scores: Dict,
                              overall_risk: float) -> Dict:
        """
        Intelligent insurance recommendations
        """
        
        cargo_value = cargo.get('insurance_value', 0)
        current_coverage = cargo.get('insurance_coverage', 'icc_c').lower()
        
        recommendations = {
            'current_coverage': current_coverage,
            'current_premium_estimate': cargo_value * 0.003,
            'recommendations': []
        }
        
        if overall_risk > 60:
            if current_coverage != 'icc_a':
                recommendations['recommendations'].append({
                    'upgrade_to': 'icc_a',
                    'reason': 'High risk warrants all-risks coverage',
                    'additional_premium': cargo_value * 0.002,
                    'benefit': 'Covers all losses except inherent vice'
                })
        
        if layer_scores.get('cargo_sensitivity', 0) > 60:
            recommendations['recommendations'].append({
                'add_on': 'damage_survey_clause',
                'reason': 'Sensitive cargo needs assessment',
                'additional_premium': 150,
                'benefit': 'Independent surveyor for claims'
            })
        
        if layer_scores.get('trade_compliance', 0) > 50:
            recommendations['recommendations'].append({
                'add_on': 'war_strikes_clause',
                'reason': 'Elevated geopolitical risk',
                'additional_premium': cargo_value * 0.001,
                'benefit': 'Protection against war/strikes'
            })
        
        return recommendations


# ============================================================================
# API RESPONSE GENERATOR
# ============================================================================

def generate_risk_assessment_v21(input_data: Dict) -> Dict:
    """
    V21 Complete API Response Generator
    """
    
    validator = RiskCastV21Validator()
    is_valid, validation_results = validator.validate_full_input(input_data)
    
    if not is_valid:
        return {
            'success': False,
            'version': 'RiskCast V21.0',
            'timestamp': datetime.now().isoformat(),
            'validation_errors': [
                {
                    'field': r.field,
                    'severity': r.severity.value,
                    'message': r.message,
                    'suggestion': r.suggestion
                }
                for r in validation_results if r.severity == ValidationSeverity.ERROR
            ],
            'validation_warnings': [
                {
                    'field': r.field,
                    'message': r.message,
                    'suggestion': r.suggestion
                }
                for r in validation_results if r.severity == ValidationSeverity.WARNING
            ]
        }
    
    scorer = RiskScoringEngineV21()
    risk_assessment = scorer.calculate_comprehensive_risk(
        input_data,
        input_data.get('modules', {})
    )
    
    enhancer = EnhancedAlgorithmicFeaturesV21()
    
    delay_prediction = enhancer.predictive_delay_model(
        input_data.get('transport', {}),
        risk_assessment['layer_scores']
    )
    
    route_alternatives = enhancer.route_optimization_suggestions(
        input_data.get('transport', {}),
        risk_assessment['layer_scores']
    )
    
    insurance_rec = enhancer.insurance_optimization(
        input_data.get('cargo', {}),
        risk_assessment['layer_scores'],
        risk_assessment['overall_score']
    )
    
    return {
        'success': True,
        'version': 'RiskCast V21.0',
        'timestamp': datetime.now().isoformat(),
        
        'validation': {
            'is_valid': is_valid,
            'warnings': [
                {
                    'field': r.field,
                    'message': r.message,
                    'suggestion': r.suggestion
                }
                for r in validation_results if r.severity == ValidationSeverity.WARNING
            ]
        },
        
        'risk_assessment': {
            'overall_score': risk_assessment['overall_score'],
            'risk_level': risk_assessment['risk_level'],
            'risk_grade': risk_assessment['risk_grade'],
            
            'layer_scores': risk_assessment['layer_scores'],
            'category_scores': risk_assessment['category_scores'],
            
            'financial_impact': risk_assessment['financial_impact'],
            
            'summary': f"Risk Score: {risk_assessment['overall_score']:.1f}/100 ({risk_assessment['risk_grade']}) - "
                      f"{risk_assessment['risk_level'].upper()} risk level. "
                      f"Expected loss: ${risk_assessment['financial_impact']['expected_loss_usd']:,.0f}."
        },
        
        'operational_intelligence': {
            'delay_prediction': delay_prediction,
            'route_alternatives': route_alternatives,
            'insurance_optimization': insurance_rec
        },
        
        'recommendations': {
            'priority_actions': risk_assessment['recommendations'][:3],
            'all_recommendations': risk_assessment['recommendations'],
            'mitigation_plan': risk_assessment['mitigation_plan']
        },
        
        'executive_summary': {
            'risk_verdict': risk_assessment['risk_level'].upper(),
            'key_concerns': [
                f"{rec['layer'].replace('_', ' ').title()}: {rec['risk_score']:.0f}/100"
                for rec in risk_assessment['recommendations'][:3]
            ],
            'estimated_total_cost': risk_assessment['mitigation_plan']['estimated_cost'],
            'action_required': 'IMMEDIATE' if risk_assessment['risk_level'] in ['high', 'critical'] else 'STANDARD'
        }
    }


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    
    sample_shipment = {
        "transport": {
            "trade_lane": "Vietnam to USA",
            "mode": "sea_freight",
            "shipment_type": "fcl",
            "priority": "balanced",
            "service_route": "VNSGN-USLAX Direct",
            "carrier": "Maersk Line",
            "incoterm": "FOB",
            "incoterm_location": "Ho Chi Minh Port",
            "pol": "VNSGN",
            "pod": "USLAX",
            "container_type": "40hc",
            "etd": "15/01/2026",
            "schedule_frequency": "weekly",
            "transit_time": 22,
            "reliability_score": 88
        },
        "cargo": {
            "cargo_type": "electronics",
            "hs_code": "847130",
            "packing_type": "carton",
            "packages": 500,
            "gross_weight": 12000.0,
            "net_weight": 11500.0,
            "volume_m3": 60.0,
            "stackability": True,
            "insurance_value": 250000.0,
            "insurance_coverage": "icc_b",
            "sensitivity": "fragile",
            "dangerous_goods": False,
            "special_instructions": "Handle with care, fragile electronics",
            "cargo_description": "Laptop computers and accessories"
        },
        "seller": {
            "company_name": "VN Electronics Co Ltd",
            "business_type": "Manufacturer",
            "country": "Vietnam",
            "city": "Ho Chi Minh City",
            "address": "123 Nguyen Hue Street",
            "contact_person": "Nguyen Van A",
            "contact_role": "Export Manager",
            "email": "export@vnelectronics.com",
            "phone": "+84901234567",
            "tax_id": "0123456789"
        },
        "buyer": {
            "company_name": "USA Tech Imports Inc",
            "business_type": "Importer",
            "country": "USA",
            "city": "Los Angeles",
            "address": "456 Main Street",
            "contact_person": "John Smith",
            "contact_role": "Procurement Manager",
            "email": "john@usatechimports.com",
            "phone": "+13105551234",
            "tax_id": "987654321"
        },
        "modules": {
            "esg": True,
            "weather_climate": True,
            "port_congestion": True,
            "carrier_performance": True,
            "market_condition": True,
            "insurance_optimization": True
        }
    }
    
    result = generate_risk_assessment_v21(sample_shipment)
    
    print("=" * 80)
    print("RISKCAST V21 - RISK ASSESSMENT RESULT")
    print("=" * 80)
    print(f"\nSuccess: {result['success']}")
    print(f"Version: {result['version']}")
    print(f"Timestamp: {result['timestamp']}")
    
    if result['success']:
        print(f"\n{'='*80}")
        print("RISK ASSESSMENT")
        print("=" * 80)
        print(f"Overall Score: {result['risk_assessment']['overall_score']}")
        print(f"Risk Level: {result['risk_assessment']['risk_level']}")
        print(f"Risk Grade: {result['risk_assessment']['risk_grade']}")
        
        print(f"\n{'='*80}")
        print("CATEGORY SCORES")
        print("=" * 80)
        for category, score in result['risk_assessment']['category_scores'].items():
            print(f"{category}: {score}")
        
        print(f"\n{'='*80}")
        print("FINANCIAL IMPACT")
        print("=" * 80)
        fin = result['risk_assessment']['financial_impact']
        print(f"Expected Loss: ${fin['expected_loss_usd']:,.2f}")
        print(f"Loss Probability: {fin['loss_probability']:.2f}%")
        print(f"VaR 95%: ${fin['var_95_usd']:,.2f}")
        
        print(f"\n{'='*80}")
        print("DELAY PREDICTION")
        print("=" * 80)
        delay = result['operational_intelligence']['delay_prediction']
        print(f"Expected Transit: {delay['expected_transit_days']} days")
        print(f"Delay Probability: {delay['delay_probability']}%")
        print(f"P95 Delay: {delay['p95_delay']} days")
        
        print(f"\n{'='*80}")
        print("TOP RECOMMENDATIONS")
        print("=" * 80)
        for rec in result['recommendations']['priority_actions']:
            print(f"\n{rec['layer']} ({rec['priority']})")
            print(f"  Score: {rec['risk_score']}")
            print(f"  Action: {rec['action']}")
        
        print(f"\n{'='*80}")
        print("EXECUTIVE SUMMARY")
        print("=" * 80)
        print(f"Verdict: {result['executive_summary']['risk_verdict']}")
        print(f"Action Required: {result['executive_summary']['action_required']}")
        print(f"Mitigation Cost: ${result['executive_summary']['estimated_total_cost']:,.0f}")
    else:
        print("\nVALIDATION ERRORS:")
        for error in result.get('validation_errors', []):
            print(f"\n{error['field']}: {error['message']}")
            if error['suggestion']:
                print(f"  Suggestion: {error['suggestion']}")