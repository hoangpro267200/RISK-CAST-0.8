"""
RiskCast V22 - ESG Risk Engine (Full Version)
==============================================
Environmental, Social, and Governance risk assessment engine

Author: RiskCast AI Team
Version: 22.0
Module: #3 - ESG Risk Engine
License: Proprietary
"""

from typing import Dict, List, Tuple


class ESGEngineV22:
    """
    ESG Risk Engine that assesses Environmental, Social, and Governance
    factors for supply chain shipments.
    
    Scoring: 0-100 (higher = worse ESG risk)
    
    Categories:
    - Environmental (40% weight): CO2, energy, waste, sustainability
    - Social (30% weight): Labor, safety, human rights, fair wages
    - Governance (30% weight): Corruption, compliance, transparency
    
    This engine uses pure logic-based assessment without external APIs or ML.
    """
    
    # High-risk countries for social factors
    HIGH_RISK_SOCIAL_COUNTRIES = ['bd', 'mm', 'pk', 'ng', 'kh', 'la', 'af', 'iq']
    
    # High-risk countries for governance
    HIGH_RISK_GOVERNANCE_COUNTRIES = ['ve', 'by', 'ru', 'mm', 'cn', 'kp', 'ir', 'sy', 'cu']
    
    # EU countries (better environmental standards)
    EU_COUNTRIES = [
        'at', 'be', 'bg', 'hr', 'cy', 'cz', 'dk', 'ee', 'fi', 'fr', 'de', 'gr',
        'hu', 'ie', 'it', 'lv', 'lt', 'lu', 'mt', 'nl', 'pl', 'pt', 'ro', 'sk',
        'si', 'es', 'se'
    ]
    
    # Transport mode CO2 intensity (kg CO2 per ton-km)
    CO2_INTENSITY = {
        'sea_freight': 10,    # Low
        'rail': 20,           # Medium-low
        'road': 60,           # Medium-high
        'air_freight': 500,   # Very high
        'multimodal': 40      # Medium
    }
    
    def assess_esg(self, seller: Dict, buyer: Dict, cargo: Dict) -> Dict:
        """
        Main ESG assessment method
        
        Args:
            seller: Seller information (company, country, certifications, etc.)
            buyer: Buyer information
            cargo: Cargo details (type, weight, mode, DG status, etc.)
        
        Returns:
            Comprehensive ESG assessment dictionary
        """
        
        # Score each ESG pillar
        environmental_result = self._score_environmental(seller, buyer, cargo)
        social_result = self._score_social(seller, buyer, cargo)
        governance_result = self._score_governance(seller, buyer)
        
        # Calculate overall ESG score (weighted)
        overall_score = (
            environmental_result['score'] * 0.40 +
            social_result['score'] * 0.30 +
            governance_result['score'] * 0.30
        )
        
        # Determine ESG level
        esg_level = self._score_to_level(overall_score)
        
        # Generate summary and recommendations
        summary = self._generate_summary(
            overall_score, 
            esg_level,
            environmental_result,
            social_result,
            governance_result
        )
        
        recommendations = self._generate_recommendations(
            environmental_result,
            social_result,
            governance_result
        )
        
        return {
            'overall_esg_score': round(overall_score, 2),
            'esg_level': esg_level,
            'esg_grade': self._score_to_grade(overall_score),
            'environmental': environmental_result,
            'social': social_result,
            'governance': governance_result,
            'summary': summary,
            'recommendations': recommendations,
            'total_violations': (
                len(environmental_result['violations']) +
                len(social_result['violations']) +
                len(governance_result['violations'])
            )
        }
    
    def _score_environmental(self, seller: Dict, buyer: Dict, cargo: Dict) -> Dict:
        """
        Score environmental factors (8 indicators)
        
        Returns:
            {
                'score': float,
                'indicators': [{'name': str, 'score': float, 'description': str}],
                'violations': [str]
            }
        """
        
        indicators = []
        
        # 1. CO2 Intensity
        mode = cargo.get('mode', 'sea_freight').lower()
        weight_kg = cargo.get('gross_weight', 1000)
        
        co2_base = self.CO2_INTENSITY.get(mode, 50)
        # Normalize: air freight (500) = 100, sea freight (10) = 20
        co2_score = self._normalize(co2_base, 10, 500, 20, 100)
        
        indicators.append({
            'name': 'CO2 Intensity',
            'score': round(co2_score, 2),
            'description': f'{mode.replace("_", " ").title()} has {"high" if co2_score > 70 else "moderate" if co2_score > 40 else "low"} carbon footprint'
        })
        
        # 2. Packaging Sustainability
        packing_type = cargo.get('packing_type', '').lower()
        if packing_type in ['pallet', 'crate', 'container']:
            packaging_score = 30  # Reusable packaging
        elif packing_type in ['carton', 'box']:
            packaging_score = 50  # Recyclable
        elif packing_type in ['bag', 'bulk']:
            packaging_score = 40  # Variable
        else:
            packaging_score = 60  # Unknown/poor
        
        indicators.append({
            'name': 'Packaging Sustainability',
            'score': packaging_score,
            'description': f'{packing_type.title()} packaging is {"sustainable" if packaging_score < 40 else "moderately sustainable" if packaging_score < 60 else "not optimal"}'
        })
        
        # 3. Energy Efficiency (based on mode)
        if mode == 'air_freight':
            energy_score = 85  # High energy use
        elif mode == 'sea_freight':
            energy_score = 25  # Low energy use
        elif mode == 'rail':
            energy_score = 30  # Good efficiency
        elif mode == 'road':
            energy_score = 60  # Moderate
        else:
            energy_score = 50
        
        indicators.append({
            'name': 'Energy Efficiency',
            'score': energy_score,
            'description': f'{mode.replace("_", " ").title()} mode has {"poor" if energy_score > 70 else "moderate" if energy_score > 40 else "good"} energy efficiency'
        })
        
        # 4. Reefer Energy Use
        container_type = cargo.get('container_type', '').lower()
        if 'rf' in container_type or cargo.get('sensitivity') in ['temperature', 'perishable']:
            reefer_score = 70  # High energy penalty
            indicators.append({
                'name': 'Reefer Energy Use',
                'score': reefer_score,
                'description': 'Temperature-controlled transport requires significant additional energy'
            })
        else:
            reefer_score = 0  # Not applicable
            indicators.append({
                'name': 'Reefer Energy Use',
                'score': reefer_score,
                'description': 'Standard ambient temperature transport'
            })
        
        # 5. Waste Generation
        packages = cargo.get('packages', 1)
        if packages > 1000:
            waste_score = 65  # Many packages = more waste
        elif packages > 100:
            waste_score = 45
        else:
            waste_score = 30
        
        indicators.append({
            'name': 'Waste Generation',
            'score': waste_score,
            'description': f'{packages} packages generates {"high" if waste_score > 60 else "moderate" if waste_score > 40 else "low"} packaging waste'
        })
        
        # 6. Hazardous Materials
        is_dg = cargo.get('dangerous_goods', False)
        if is_dg:
            hazardous_score = 75  # High environmental risk
            indicators.append({
                'name': 'Hazardous Materials',
                'score': hazardous_score,
                'description': 'Dangerous goods present environmental contamination risk'
            })
        else:
            hazardous_score = 15
            indicators.append({
                'name': 'Hazardous Materials',
                'score': hazardous_score,
                'description': 'Non-hazardous cargo with minimal environmental risk'
            })
        
        # 7. Green Certification
        seller_certs = seller.get('certifications', [])
        buyer_certs = buyer.get('certifications', [])
        
        has_green_cert = any(
            'iso14001' in str(cert).lower() or 'green' in str(cert).lower()
            for cert in (seller_certs + buyer_certs)
        )
        
        if has_green_cert:
            cert_score = 20  # Good environmental practices
        else:
            cert_score = 55  # No certification
        
        indicators.append({
            'name': 'Green Certification',
            'score': cert_score,
            'description': 'Party has ISO14001 or equivalent certification' if has_green_cert else 'No environmental certifications reported'
        })
        
        # 8. Route Distance Impact
        transit_time = cargo.get('transit_time', 14)
        if mode == 'sea_freight' and transit_time > 30:
            distance_score = 60  # Long sea routes
        elif mode == 'air_freight' and transit_time > 2:
            distance_score = 70  # Long air routes = very high impact
        elif transit_time > 14:
            distance_score = 50
        else:
            distance_score = 35
        
        indicators.append({
            'name': 'Route Distance Impact',
            'score': distance_score,
            'description': f'{transit_time}-day transit has {"high" if distance_score > 60 else "moderate" if distance_score > 45 else "low"} distance-related environmental impact'
        })
        
        # Apply EU discount
        seller_country = seller.get('country', '').lower()
        buyer_country = buyer.get('country', '').lower()
        
        eu_discount = 0
        if seller_country in self.EU_COUNTRIES or buyer_country in self.EU_COUNTRIES:
            eu_discount = 10  # EU has better environmental standards
        
        # Calculate average environmental score
        env_score = sum(ind['score'] for ind in indicators) / len(indicators)
        env_score = max(0, env_score - eu_discount)
        
        # Identify violations (indicators > 70)
        violations = [
            f"{ind['name']}: {ind['description']}"
            for ind in indicators if ind['score'] > 70
        ]
        
        return {
            'score': round(env_score, 2),
            'indicators': indicators,
            'violations': violations,
            'eu_discount_applied': eu_discount > 0
        }
    
    def _score_social(self, seller: Dict, buyer: Dict, cargo: Dict) -> Dict:
        """
        Score social factors (8 indicators)
        
        Returns:
            {
                'score': float,
                'indicators': [{'name': str, 'score': float, 'description': str}],
                'violations': [str]
            }
        """
        
        indicators = []
        seller_country = seller.get('country', '').lower()
        buyer_country = buyer.get('country', '').lower()
        
        # 1. Labor Practices
        if seller_country in self.HIGH_RISK_SOCIAL_COUNTRIES:
            labor_score = 75
            labor_desc = 'Seller country has documented labor practice concerns'
        elif buyer_country in self.HIGH_RISK_SOCIAL_COUNTRIES:
            labor_score = 65
            labor_desc = 'Buyer country has some labor practice issues'
        else:
            labor_score = 35
            labor_desc = 'Labor practices appear within acceptable standards'
        
        indicators.append({
            'name': 'Labor Practices',
            'score': labor_score,
            'description': labor_desc
        })
        
        # 2. Worker Safety
        mode = cargo.get('mode', 'sea_freight').lower()
        is_dg = cargo.get('dangerous_goods', False)
        
        if is_dg:
            safety_score = 70  # DG handling = higher worker risk
        elif mode in ['road', 'multimodal']:
            safety_score = 55  # Multiple handling points
        else:
            safety_score = 40  # Standard safety
        
        indicators.append({
            'name': 'Worker Safety',
            'score': safety_score,
            'description': f'{"DG cargo presents elevated" if is_dg else "Standard"} worker safety risks'
        })
        
        # 3. Fair Wages Estimate
        # High-risk countries likely have wage issues
        if seller_country in self.HIGH_RISK_SOCIAL_COUNTRIES:
            wage_score = 80
            wage_desc = 'Country has documented fair wage concerns'
        elif seller_country in ['us', 'ca', 'au', 'nz', 'uk'] + self.EU_COUNTRIES:
            wage_score = 25
            wage_desc = 'Strong wage protections and enforcement'
        else:
            wage_score = 50
            wage_desc = 'Fair wage standards variable'
        
        indicators.append({
            'name': 'Fair Wages',
            'score': wage_score,
            'description': wage_desc
        })
        
        # 4. Overtime Risk
        priority = cargo.get('priority', '').lower()
        if priority == 'fastest':
            overtime_score = 65  # Rush orders = overtime
        elif priority == 'cheapest':
            overtime_score = 70  # Cost pressure = wage suppression
        else:
            overtime_score = 40
        
        indicators.append({
            'name': 'Overtime Risk',
            'score': overtime_score,
            'description': f'{"High" if overtime_score > 60 else "Moderate" if overtime_score > 40 else "Low"} risk of worker overtime pressure'
        })
        
        # 5. Supply Chain Transparency
        has_tax_id = bool(seller.get('tax_id'))
        has_address = bool(seller.get('address'))
        
        if has_tax_id and has_address:
            transparency_score = 30  # Good transparency
        elif has_tax_id or has_address:
            transparency_score = 50  # Partial
        else:
            transparency_score = 75  # Poor transparency
        
        indicators.append({
            'name': 'Supply Chain Transparency',
            'score': transparency_score,
            'description': f'{"Good" if transparency_score < 40 else "Limited" if transparency_score < 60 else "Poor"} supply chain visibility and documentation'
        })
        
        # 6. Human Rights Risk
        if seller_country in self.HIGH_RISK_SOCIAL_COUNTRIES:
            hr_score = 85
            hr_desc = 'Country has documented human rights concerns'
        elif buyer_country in self.HIGH_RISK_SOCIAL_COUNTRIES:
            hr_score = 70
            hr_desc = 'Destination has some human rights issues'
        else:
            hr_score = 30
            hr_desc = 'Human rights protections appear adequate'
        
        indicators.append({
            'name': 'Human Rights',
            'score': hr_score,
            'description': hr_desc
        })
        
        # 7. Community Impact
        cargo_value = cargo.get('insurance_value', 0)
        if cargo_value > 500000:
            community_score = 35  # High value = positive economic impact
        elif cargo_value > 100000:
            community_score = 45
        else:
            community_score = 55  # Low economic benefit
        
        indicators.append({
            'name': 'Community Impact',
            'score': community_score,
            'description': f'{"Positive" if community_score < 45 else "Neutral" if community_score < 60 else "Limited"} local economic contribution'
        })
        
        # 8. Shipping Worker Risk
        carrier_reliability = cargo.get('reliability_score', 50)
        if carrier_reliability < 50:
            shipping_worker_score = 70  # Unreliable carrier = poor conditions
        elif carrier_reliability < 70:
            shipping_worker_score = 50
        else:
            shipping_worker_score = 35  # Good carrier = better conditions
        
        indicators.append({
            'name': 'Shipping Worker Conditions',
            'score': shipping_worker_score,
            'description': f'Carrier reliability suggests {"poor" if shipping_worker_score > 60 else "adequate" if shipping_worker_score > 40 else "good"} worker conditions'
        })
        
        # Calculate average social score
        social_score = sum(ind['score'] for ind in indicators) / len(indicators)
        
        # Identify violations
        violations = [
            f"{ind['name']}: {ind['description']}"
            for ind in indicators if ind['score'] > 70
        ]
        
        return {
            'score': round(social_score, 2),
            'indicators': indicators,
            'violations': violations
        }
    
    def _score_governance(self, seller: Dict, buyer: Dict) -> Dict:
        """
        Score governance factors (8 indicators)
        
        Returns:
            {
                'score': float,
                'indicators': [{'name': str, 'score': float, 'description': str}],
                'violations': [str]
            }
        """
        
        indicators = []
        seller_country = seller.get('country', '').lower()
        buyer_country = buyer.get('country', '').lower()
        
        # 1. Corruption Risk
        if seller_country in self.HIGH_RISK_GOVERNANCE_COUNTRIES:
            corruption_score = 80
            corruption_desc = 'Seller country has elevated corruption risk'
        elif buyer_country in self.HIGH_RISK_GOVERNANCE_COUNTRIES:
            corruption_score = 70
            corruption_desc = 'Buyer country has some corruption concerns'
        else:
            corruption_score = 35
            corruption_desc = 'Corruption risk is within acceptable range'
        
        indicators.append({
            'name': 'Corruption Risk',
            'score': corruption_score,
            'description': corruption_desc
        })
        
        # 2. Document Accuracy
        seller_complete = all([
            seller.get('company_name'),
            seller.get('country'),
            seller.get('email'),
            seller.get('phone')
        ])
        buyer_complete = all([
            buyer.get('company_name'),
            buyer.get('country'),
            buyer.get('email'),
            buyer.get('phone')
        ])
        
        if seller_complete and buyer_complete:
            doc_score = 25  # Complete documentation
        elif seller_complete or buyer_complete:
            doc_score = 50  # Partial
        else:
            doc_score = 75  # Incomplete
        
        indicators.append({
            'name': 'Document Accuracy',
            'score': doc_score,
            'description': f'Documentation is {"complete" if doc_score < 40 else "partially complete" if doc_score < 60 else "incomplete"}'
        })
        
        # 3. Regulatory Compliance
        has_seller_tax = bool(seller.get('tax_id'))
        has_buyer_tax = bool(buyer.get('tax_id'))
        
        if has_seller_tax and has_buyer_tax:
            compliance_score = 30
        elif has_seller_tax or has_buyer_tax:
            compliance_score = 55
        else:
            compliance_score = 75
        
        indicators.append({
            'name': 'Regulatory Compliance',
            'score': compliance_score,
            'description': f'{"Strong" if compliance_score < 40 else "Moderate" if compliance_score < 60 else "Weak"} compliance indicators'
        })
        
        # 4. Sanctions Exposure
        sanctioned_countries = ['kp', 'ir', 'sy', 'cu', 've', 'by']
        
        if seller_country in sanctioned_countries or buyer_country in sanctioned_countries:
            sanctions_score = 90
            sanctions_desc = 'Critical sanctions exposure detected'
        elif seller_country in ['ru', 'cn'] or buyer_country in ['ru', 'cn']:
            sanctions_score = 60
            sanctions_desc = 'Moderate sanctions monitoring required'
        else:
            sanctions_score = 20
            sanctions_desc = 'No significant sanctions concerns'
        
        indicators.append({
            'name': 'Sanctions Exposure',
            'score': sanctions_score,
            'description': sanctions_desc
        })
        
        # 5. Audit Trail Strength
        seller_business_type = seller.get('business_type', '').lower()
        
        if 'manufacturer' in seller_business_type or 'corporation' in seller_business_type:
            audit_score = 30  # Established entities have better audit trails
        elif 'trading' in seller_business_type:
            audit_score = 55  # Traders have moderate trails
        else:
            audit_score = 65  # Unknown = weak
        
        indicators.append({
            'name': 'Audit Trail',
            'score': audit_score,
            'description': f'{"Strong" if audit_score < 40 else "Moderate" if audit_score < 60 else "Weak"} audit trail expected'
        })
        
        # 6. Contract Clarity
        has_incoterm = bool(seller.get('incoterm') or buyer.get('incoterm'))
        has_contact = bool(seller.get('contact_person') and buyer.get('contact_person'))
        
        if has_incoterm and has_contact:
            contract_score = 35
        elif has_incoterm or has_contact:
            contract_score = 55
        else:
            contract_score = 70
        
        indicators.append({
            'name': 'Contract Clarity',
            'score': contract_score,
            'description': f'Contract terms are {"clear" if contract_score < 45 else "partially defined" if contract_score < 60 else "unclear"}'
        })
        
        # 7. Tax Transparency
        if has_seller_tax and has_buyer_tax:
            tax_score = 25
            tax_desc = 'Both parties have tax identification'
        elif has_seller_tax:
            tax_score = 50
            tax_desc = 'Seller has tax ID, buyer information incomplete'
        else:
            tax_score = 75
            tax_desc = 'Tax transparency concerns exist'
        
        indicators.append({
            'name': 'Tax Transparency',
            'score': tax_score,
            'description': tax_desc
        })
        
        # 8. Anti-Fraud Controls
        seller_email_valid = '@' in seller.get('email', '')
        buyer_email_valid = '@' in buyer.get('email', '')
        
        fraud_indicators = sum([
            seller_email_valid,
            buyer_email_valid,
            has_seller_tax,
            has_buyer_tax,
            seller_complete,
            buyer_complete
        ])
        
        if fraud_indicators >= 5:
            fraud_score = 30  # Good controls
        elif fraud_indicators >= 3:
            fraud_score = 55  # Moderate
        else:
            fraud_score = 80  # High fraud risk
        
        indicators.append({
            'name': 'Anti-Fraud Controls',
            'score': fraud_score,
            'description': f'{"Strong" if fraud_score < 40 else "Moderate" if fraud_score < 60 else "Weak"} fraud prevention measures'
        })
        
        # Calculate average governance score
        governance_score = sum(ind['score'] for ind in indicators) / len(indicators)
        
        # Identify violations
        violations = [
            f"{ind['name']}: {ind['description']}"
            for ind in indicators if ind['score'] > 70
        ]
        
        return {
            'score': round(governance_score, 2),
            'indicators': indicators,
            'violations': violations
        }
    
    def _score_to_level(self, score: float) -> str:
        """Convert ESG score to risk level"""
        if score < 30:
            return 'low'
        elif score < 50:
            return 'medium'
        elif score < 70:
            return 'high'
        else:
            return 'critical'
    
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
    
    def _normalize(self, value: float, min_val: float, max_val: float, 
                   target_min: float = 0, target_max: float = 100) -> float:
        """Normalize a value to target range"""
        if max_val == min_val:
            return target_min
        
        normalized = ((value - min_val) / (max_val - min_val)) * (target_max - target_min) + target_min
        return max(target_min, min(target_max, normalized))
    
    def _generate_summary(self, overall_score: float, esg_level: str,
                         env_result: Dict, social_result: Dict, 
                         gov_result: Dict) -> str:
        """Generate ESG summary text"""
        
        if esg_level == 'low':
            return (
                f"ESG performance is strong with a score of {overall_score:.1f}/100. "
                f"Environmental, social, and governance factors are well-managed. "
                f"This shipment demonstrates responsible supply chain practices."
            )
        elif esg_level == 'medium':
            return (
                f"ESG performance is moderate with a score of {overall_score:.1f}/100. "
                f"While acceptable, there are opportunities to improve environmental, "
                f"social, or governance practices. Consider implementing recommendations."
            )
        elif esg_level == 'high':
            return (
                f"ESG risk is elevated at {overall_score:.1f}/100. "
                f"Significant concerns exist in environmental, social, or governance areas. "
                f"Action is recommended to address key ESG violations and improve practices."
            )
        else:  # critical
            return (
                f"ESG risk is critical at {overall_score:.1f}/100. "
                f"Severe environmental, social, or governance issues detected. "
                f"Immediate remediation required to meet responsible sourcing standards."
            )
    
    def _generate_recommendations(self, env_result: Dict, social_result: Dict,
                                 gov_result: Dict) -> List[str]:
        """Generate actionable ESG recommendations"""
        
        recommendations = []
        
        # Environmental recommendations
        if env_result['score'] > 60:
            recommendations.append("⚠️ Environmental: Consider alternative transport modes to reduce carbon footprint")
        if any('Hazardous' in v for v in env_result['violations']):
            recommendations.append("• Environmental: Implement enhanced hazardous material handling protocols")
        if any('Reefer' in v for v in env_result['violations']):
            recommendations.append("• Environmental: Optimize temperature control to reduce energy consumption")
        
        # Social recommendations
        if social_result['score'] > 60:
            recommendations.append("⚠️ Social: Conduct enhanced due diligence on labor practices")
        if any('Human Rights' in v for v in social_result['violations']):
            recommendations.append("• Social: Engage third-party auditor for human rights compliance verification")
        if any('Wages' in v for v in social_result['violations']):
            recommendations.append("• Social: Verify fair wage practices through supplier assessments")
        
        # Governance recommendations
        if gov_result['score'] > 60:
            recommendations.append("⚠️ Governance: Strengthen compliance and documentation processes")
        if any('Sanctions' in v for v in gov_result['violations']):
            recommendations.append("• Governance: Conduct comprehensive sanctions screening immediately")
        if any('Corruption' in v for v in gov_result['violations']):
            recommendations.append("• Governance: Implement anti-corruption due diligence procedures")
        if any('Tax' in v for v in gov_result['violations']):
            recommendations.append("• Governance: Obtain and verify tax identification for all parties")
        
        # Generic recommendations if no violations but scores are moderate
        if not recommendations:
            if env_result['score'] > 40:
                recommendations.append("• Consider green certifications (ISO14001) for environmental improvement")
            if social_result['score'] > 40:
                recommendations.append("• Implement supplier code of conduct for social responsibility")
            if gov_result['score'] > 40:
                recommendations.append("• Enhance governance through regular compliance audits")
        
        return recommendations[:5]  # Return top 5 recommendations




