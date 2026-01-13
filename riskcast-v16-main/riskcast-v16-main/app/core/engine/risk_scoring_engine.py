"""
RiskCast V22 - Risk Scoring Engine Module
==========================================
Multi-layer risk scoring engine with 16 risk dimensions

Author: RiskCast AI Team
Version: 22.0
License: Proprietary
"""

import numpy as np
from typing import Dict, List
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMERATIONS
# ============================================================================

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
# RISK SCORING ENGINE
# ============================================================================

class RiskScoringEngineV21:
    """
    Multi-layer risk scoring engine with 16 risk dimensions
    
    V22 Enhancement: Added sub_factor_scores tracking capability
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
    
    def __init__(self):
        """Initialize engine with sub-factor tracking"""
        self.sub_factor_scores = {}
    
    def calculate_comprehensive_risk(self, 
                                    validated_data: Dict,
                                    modules_enabled: Dict) -> Dict:
        """
        Main scoring orchestrator
        
        V22 Enhancement: Now tracks sub-factors for each risk layer
        """
        
        transport = validated_data.get('transport', {})
        cargo = validated_data.get('cargo', {})
        seller = validated_data.get('seller', {})
        buyer = validated_data.get('buyer', {})
        
        # Calculate sub-factors (V22 enhancement)
        self.sub_factor_scores = self.calculate_sub_factors(transport, cargo, seller, buyer)
        
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
            'sub_factor_scores': self.sub_factor_scores,  # V22 enhancement
            'recommendations': recommendations,
            'mitigation_plan': mitigation_plan,
            'financial_impact': self._estimate_financial_impact(
                overall_score, 
                cargo.get('insurance_value', 0)
            )
        }
    
    def calculate_sub_factors(self, transport: Dict, cargo: Dict, 
                             seller: Dict, buyer: Dict) -> Dict:
        """
        Calculate detailed sub-factors for each risk layer (V22 enhancement)
        
        TODO: Expand this in V22 with more granular sub-factors per layer
        """
        sub_factors = {
            'transport': {
                'mode_base_risk': self.MODE_RISK_SCORES.get(transport.get('mode', 'sea_freight'), 50),
                'carrier_reliability': transport.get('reliability_score', 50),
                'transit_days': transport.get('transit_time', 0)
            },
            'cargo': {
                'sensitivity_type': cargo.get('sensitivity', 'standard'),
                'is_dangerous': cargo.get('dangerous_goods', False),
                'value_per_kg': cargo.get('insurance_value', 0) / max(cargo.get('gross_weight', 1), 1)
            },
            'commercial': {
                'incoterm': transport.get('incoterm', 'FOB'),
                'seller_country': seller.get('country', ''),
                'buyer_country': buyer.get('country', '')
            }
        }
        
        return sub_factors
    
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






