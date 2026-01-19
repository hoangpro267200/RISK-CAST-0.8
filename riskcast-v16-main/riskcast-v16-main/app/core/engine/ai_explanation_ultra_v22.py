"""
RiskCast V22 - AI Explanation Ultra Layer
==========================================
Comprehensive multi-perspective explanation engine that synthesizes
all V22 modules into actionable consultant-grade insights

Author: RiskCast AI Team
Version: 22.0
Phase: 2.7 - AI Explanation Ultra
License: Proprietary
"""

from typing import Dict, List, Optional


class AIExplanationUltraV22:
    """
    AI Explanation Ultra Layer that transforms all V22 analytics
    (risk scores, driver tree, ESG, GFI, Monte Carlo, shock scenarios)
    into comprehensive, multi-perspective explanations.
    
    Features:
    - Executive summary (C-level ready)
    - Key driver analysis with evidence
    - Root cause analysis
    - Scenario explanations (MC + Shock)
    - Persona-specific views (CFO, Logistics, Risk Officer)
    - What-if insights
    - Confidence scoring
    
    Uses pure rule-based logic without external LLMs.
    """
    
    def generate_explanation(self, bundle: Dict) -> Dict:
        """
        Main entrypoint: Generate comprehensive AI explanation
        
        Args:
            bundle: Complete V22 analytics bundle containing:
                - input_data: Original shipment data
                - core: Core risk assessment (overall_score, layer_scores, etc.)
                - driver_tree: Risk driver tree result
                - esg: ESG assessment
                - monte_carlo: Monte Carlo simulation (optional)
                - gfi: Global Freight Index
                - shock: Shock scenario results
        
        Returns:
            Comprehensive AI explanation dictionary
        """
        
        # Build internal context for analysis
        ctx = self._build_context(bundle)
        
        # Generate each explanation component
        executive_summary = self._build_executive_summary(ctx)
        key_drivers = self._extract_key_drivers(ctx)
        root_cause_analysis = self._build_root_cause(ctx)
        scenario_explanations = self._explain_scenarios(ctx)
        persona_views = self._build_persona_views(ctx)
        what_if_insights = self._build_what_if_insights(ctx)
        confidence_score = self._estimate_confidence(ctx, bundle.get('validation', {}))
        
        return {
            'executive_summary': executive_summary,
            'key_drivers': key_drivers,
            'root_cause_analysis': root_cause_analysis,
            'scenario_explanations': scenario_explanations,
            'persona_views': persona_views,
            'what_if_insights': what_if_insights,
            'confidence_score': confidence_score
        }
    
    def _build_context(self, bundle: Dict) -> Dict:
        """
        Build internal context from bundle for analysis
        """
        
        input_data = bundle.get('input_data', {})
        core = bundle.get('core', {})
        driver_tree = bundle.get('driver_tree', {})
        esg = bundle.get('esg', {})
        monte_carlo = bundle.get('monte_carlo', {})
        gfi = bundle.get('gfi', {})
        shock = bundle.get('shock', {})
        
        return {
            'overall_score': core.get('overall_score', 50),
            'risk_level': core.get('risk_level', 'medium'),
            'risk_grade': core.get('risk_grade', 'B'),
            'layer_scores': core.get('layer_scores', {}),
            'category_scores': core.get('category_scores', {}),
            'financial_impact': core.get('financial_impact', {}),
            'mitigation_plan': core.get('mitigation_plan', {}),
            
            'transport': input_data.get('transport', {}),
            'cargo': input_data.get('cargo', {}),
            'seller': input_data.get('seller', {}),
            'buyer': input_data.get('buyer', {}),
            
            'driver_tree': driver_tree,
            'esg': esg,
            'monte_carlo': monte_carlo,
            'gfi': gfi,
            'shock': shock
        }
    
    def _build_executive_summary(self, ctx: Dict) -> str:
        """
        Build executive summary (3-6 sentences, consultant-style)
        """
        
        overall_score = ctx['overall_score']
        risk_level = ctx['risk_level'].upper()
        risk_grade = ctx['risk_grade']
        
        # Sentence 1: Overall risk assessment
        summary = f"This shipment is assessed at {risk_level} RISK ({overall_score:.1f}/100, grade {risk_grade}). "
        
        # Sentence 2: Main exposure identification
        layer_scores = ctx['layer_scores']
        top_layers = sorted(layer_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        
        main_exposures = []
        for layer_name, score in top_layers:
            if score > 60:
                if 'cargo' in layer_name or 'packing' in layer_name:
                    main_exposures.append('cargo damage risk')
                elif 'port' in layer_name or 'congestion' in layer_name:
                    main_exposures.append('port congestion and delays')
                elif 'carrier' in layer_name:
                    main_exposures.append('carrier reliability issues')
                elif 'compliance' in layer_name or 'trade' in layer_name:
                    main_exposures.append('regulatory compliance concerns')
                elif 'weather' in layer_name or 'climate' in layer_name:
                    main_exposures.append('weather disruption risk')
        
        if main_exposures:
            summary += f"Primary exposures: {', '.join(main_exposures[:2])}. "
        
        # Sentence 3: Financial impact
        expected_loss = ctx['financial_impact'].get('expected_loss_usd', 0)
        cargo_value = ctx['cargo'].get('insurance_value', 100000)
        loss_pct = (expected_loss / cargo_value * 100) if cargo_value > 0 else 0
        
        summary += f"Expected loss: ${expected_loss:,.0f} ({loss_pct:.1f}% of cargo value). "
        
        # Sentence 4: Monte Carlo insight (if available)
        if ctx.get('monte_carlo') and 'eta_stats' in ctx['monte_carlo']:
            mc = ctx['monte_carlo']
            p95_eta = mc['eta_stats']['p95']
            base_transit = ctx['transport'].get('transit_time', 14)
            delay_buffer = p95_eta - base_transit
            
            if delay_buffer > base_transit * 0.3:
                summary += f"Simulation shows high delay risk: 95th percentile is {p95_eta:.0f} days (add {delay_buffer:.0f}-day buffer). "
        
        # Sentence 5: GFI market context (if available)
        if ctx.get('gfi') and 'pressure' in ctx['gfi']:
            gfi = ctx['gfi']
            pressure = gfi['pressure']['pressure_level']
            if pressure in ['high', 'extreme']:
                summary += f"Market pressure is {pressure.upper()} - secure capacity with contract coverage. "
        
        # Sentence 6: Recommended action
        mitigation_cost = ctx['mitigation_plan'].get('estimated_cost', 0)
        risk_reduction = ctx['mitigation_plan'].get('expected_risk_reduction', 0)
        
        if risk_reduction > 10:
            summary += f"Implementing recommended mitigation (${mitigation_cost:,.0f}) can reduce risk by ~{risk_reduction:.0f} points."
        elif risk_level in ['HIGH', 'CRITICAL']:
            summary += "Immediate action required to address critical risk factors."
        else:
            summary += "Standard mitigation measures should be sufficient for successful delivery."
        
        return summary
    
    def _extract_key_drivers(self, ctx: Dict) -> List[Dict]:
        """
        Extract top 3-5 key risk drivers with detailed analysis
        """
        
        layer_scores = ctx['layer_scores']
        driver_tree = ctx.get('driver_tree', {})
        
        # Get all layers and sort by score
        sorted_layers = sorted(layer_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Extract top drivers (score >= 60 or top 5, whichever is more restrictive)
        key_drivers = []
        
        for layer_name, score in sorted_layers[:5]:
            if score < 50 and len(key_drivers) >= 3:
                break  # Don't include too many low-impact drivers
            
            # Find category and weight
            category = self._layer_to_category(layer_name, driver_tree)
            weight = self._get_layer_weight(layer_name)
            
            # Determine impact direction
            impact_direction = "increase" if score > 50 else "neutral"
            
            # Generate short reason
            short_reason = self._generate_driver_reason(layer_name, score, ctx)
            
            # Suggest action
            suggested_action = self._suggest_driver_action(layer_name, score, ctx)
            
            key_drivers.append({
                'name': layer_name,
                'display_name': self._format_layer_name(layer_name),
                'score': round(score, 1),
                'weight': weight,
                'category': category,
                'impact_direction': impact_direction,
                'short_reason': short_reason,
                'suggested_action': suggested_action
            })
        
        return key_drivers[:5]  # Max 5 drivers
    
    def _build_root_cause(self, ctx: Dict) -> List[Dict]:
        """
        Build root cause analysis with evidence from multiple modules
        """
        
        root_causes = []
        layer_scores = ctx['layer_scores']
        driver_tree = ctx.get('driver_tree', {})
        gfi = ctx.get('gfi', {})
        
        # Analyze top 3 drivers
        top_drivers = sorted(layer_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        
        for layer_name, score in top_drivers:
            if score < 55:  # Only analyze significant drivers
                continue
            
            # Gather evidence from multiple sources
            evidence = []
            
            # Evidence from driver tree
            if driver_tree:
                for cat_key, cat_data in driver_tree.items():
                    for driver in cat_data.get('drivers', []):
                        if driver['layer'] == layer_name:
                            evidence.append(f"driver_tree.{cat_key}.{layer_name}.score = {driver['score']:.1f}")
                            if driver.get('root_causes'):
                                evidence.append(f"Root: {driver['root_causes'][0]}")
            
            # Evidence from GFI (if relevant)
            if layer_name in ['market_volatility', 'port_congestion'] and gfi:
                if 'pressure' in gfi:
                    evidence.append(f"gfi.pressure_level = {gfi['pressure']['pressure_level']}")
            
            # Build root cause explanation
            reason = self._explain_root_cause(layer_name, score, ctx)
            risk_consequence = self._explain_consequence(layer_name, score)
            mitigation_hint = self._suggest_driver_action(layer_name, score, ctx)
            
            root_causes.append({
                'driver': layer_name,
                'driver_display_name': self._format_layer_name(layer_name),
                'reason': reason,
                'evidence': evidence[:2],  # Top 2 pieces of evidence
                'risk_consequence': risk_consequence,
                'mitigation_hint': mitigation_hint
            })
        
        return root_causes
    
    def _explain_scenarios(self, ctx: Dict) -> Dict:
        """
        Explain Monte Carlo and Shock scenarios
        """
        
        explanations = {}
        
        # Monte Carlo explanation
        if ctx.get('monte_carlo') and 'eta_stats' in ctx['monte_carlo']:
            mc = ctx['monte_carlo']
            
            p50 = mc['eta_stats']['p50']
            p95 = mc['eta_stats']['p95']
            base_transit = ctx['transport'].get('transit_time', 14)
            
            # Classify delay risk
            if p95 > base_transit * 2:
                delay_risk_level = 'critical'
            elif p95 > base_transit * 1.5:
                delay_risk_level = 'high'
            elif p95 > base_transit * 1.2:
                delay_risk_level = 'medium'
            else:
                delay_risk_level = 'low'
            
            # Tail risk comment
            tail_ratio = p95 / p50 if p50 > 0 else 1
            if tail_ratio > 1.5:
                tail_comment = "Heavy-tailed distribution indicates extreme delay scenarios are possible"
            else:
                tail_comment = "Distribution is relatively symmetric with limited tail risk"
            
            explanations['monte_carlo'] = {
                'summary': f"10,000-scenario simulation projects median ETA of {p50:.1f} days with {delay_risk_level.upper()} delay risk",
                'delay_risk_level': delay_risk_level,
                'stats': {
                    'p50_delay_days': round(p50 - base_transit, 1),
                    'p95_delay_days': round(p95 - base_transit, 1),
                    'tail_risk_comment': tail_comment
                }
            }
        
        # Shock scenario explanations
        if ctx.get('shock') and 'scenarios' in ctx['shock']:
            shock_explanations = []
            
            for scenario in ctx['shock']['scenarios']:
                impact_score = scenario['impact']['delta_vs_base']
                impact_loss = scenario['impact']['delta_expected_loss_usd']
                
                if abs(impact_score) < 2:  # Skip minor impacts
                    continue
                
                base_score = ctx['overall_score']
                new_score = scenario['impact']['overall_score']
                base_level = ctx['risk_level']
                new_level = scenario['impact']['risk_level']
                
                # Build narrative
                if new_level != base_level:
                    narrative = (
                        f"If {scenario['name'].lower()} occurs, risk score jumps from "
                        f"{base_score:.0f} ({base_level.upper()}) → {new_score:.0f} ({new_level.upper()}) "
                        f"and expected loss increases by ${abs(impact_loss):,.0f}."
                    )
                else:
                    narrative = (
                        f"Under {scenario['name'].lower()}, risk increases by {impact_score:.1f} points "
                        f"(${abs(impact_loss):,.0f} additional expected loss) but remains in {new_level.upper()} category."
                    )
                
                shock_explanations.append({
                    'name': scenario['name'],
                    'impact_on_risk_score': round(impact_score, 1),
                    'impact_on_expected_loss_usd': round(abs(impact_loss), 2),
                    'narrative': narrative
                })
            
            explanations['shock_scenarios'] = shock_explanations[:3]  # Top 3
        
        return explanations
    
    def _build_persona_views(self, ctx: Dict) -> Dict:
        """
        Build persona-specific views (CFO, Logistics Manager, Risk Officer)
        """
        
        overall_score = ctx['overall_score']
        expected_loss = ctx['financial_impact'].get('expected_loss_usd', 0)
        mitigation_cost = ctx['mitigation_plan'].get('estimated_cost', 0)
        risk_reduction = ctx['mitigation_plan'].get('expected_risk_reduction', 0)
        cargo_value = ctx['cargo'].get('insurance_value', 100000)
        
        # CFO View - Financial focus
        loss_pct = (expected_loss / cargo_value * 100) if cargo_value > 0 else 0
        roi = (risk_reduction / mitigation_cost) if mitigation_cost > 0 else 0
        
        cfo_summary = (
            f"Expected loss is ${expected_loss:,.0f} ({loss_pct:.1f}% of cargo value). "
            f"Mitigation budget: ${mitigation_cost:,.0f}. "
        )
        
        if roi > 5:
            cfo_summary += f"ROI of mitigation is attractive (1:{roi:.0f} - reducing ${risk_reduction*1000:.0f} risk for ${mitigation_cost:,.0f} investment)."
        elif mitigation_cost > 0:
            cfo_summary += f"Mitigation reduces risk by {risk_reduction:.0f} points with moderate ROI."
        else:
            cfo_summary += "No immediate mitigation cost required; monitor standard risk factors."
        
        # Logistics Manager View - Operational focus
        delay_risk = "high" if ctx.get('monte_carlo') and ctx['monte_carlo'].get('eta_stats', {}).get('p95', 0) > ctx['transport'].get('transit_time', 14) * 1.5 else "moderate"
        
        carrier = ctx['transport'].get('carrier', 'current carrier')
        mode = ctx['transport'].get('mode', 'sea_freight')
        pol = ctx['transport'].get('pol', 'origin')
        pod = ctx['transport'].get('pod', 'destination')
        
        logistics_summary = f"Biggest operational risk is {delay_risk} delay probability via {pod}. "
        
        # Check if port congestion is high
        if ctx['layer_scores'].get('port_congestion', 0) > 60:
            logistics_summary += f"Port congestion at {pol}/{pod} is elevated. "
        
        # Check carrier performance
        if ctx['layer_scores'].get('carrier_performance', 0) > 60:
            logistics_summary += f"Switching to premium carrier can reduce delay risk by ~15-20%. "
        
        # Check cargo handling
        if ctx['layer_scores'].get('cargo_sensitivity', 0) > 60:
            logistics_summary += f"Cargo sensitivity requires upgraded handling and packaging protocols."
        else:
            logistics_summary += f"Current routing and carrier setup is adequate for this cargo type."
        
        # Risk Officer View - Compliance and ESG focus
        trade_risk = ctx['layer_scores'].get('trade_compliance', 0)
        dg_risk = ctx['layer_scores'].get('dg_compliance', 0)
        esg_score = ctx.get('esg', {}).get('overall_esg_score', 50)
        
        risk_officer_summary = ""
        
        if trade_risk > 60:
            risk_officer_summary += "Trade compliance risk is elevated - conduct enhanced sanctions screening. "
        elif trade_risk > 40:
            risk_officer_summary += "Trade compliance is moderate - standard screening applies. "
        else:
            risk_officer_summary += "Trade compliance risk is low. "
        
        if dg_risk > 60:
            risk_officer_summary += "Dangerous goods present significant compliance burden. "
        
        if esg_score > 60:
            risk_officer_summary += f"ESG score ({esg_score:.0f}/100) is below industry benchmark - review supplier practices. "
        elif esg_score > 40:
            risk_officer_summary += f"ESG performance ({esg_score:.0f}/100) is acceptable but has improvement opportunities. "
        else:
            risk_officer_summary += f"ESG performance ({esg_score:.0f}/100) is strong and meets responsible sourcing standards."
        
        return {
            'cfo': {
                'headline': 'Financial Risk & ROI Analysis',
                'focus': ['financial_impact', 'expected_loss', 'mitigation_cost'],
                'summary': cfo_summary
            },
            'logistics_manager': {
                'headline': 'Operational Risk & Delivery Confidence',
                'focus': ['delay_risk', 'route', 'carrier', 'packing'],
                'summary': logistics_summary
            },
            'risk_officer': {
                'headline': 'Compliance, ESG & Regulatory Risk',
                'focus': ['compliance', 'dg', 'esg', 'trade_restrictions'],
                'summary': risk_officer_summary
            }
        }
    
    def _build_what_if_insights(self, ctx: Dict) -> List[Dict]:
        """
        Build what-if insights (if X changes, then Y happens)
        """
        
        insights = []
        original_score = ctx['overall_score']
        layer_scores = ctx['layer_scores']
        
        # What-if #1: Upgrade packing (if cargo_sensitivity or packing_quality are high)
        if layer_scores.get('cargo_sensitivity', 0) > 50 or layer_scores.get('packing_quality', 0) > 50:
            # Estimate: Better packing reduces cargo_sensitivity by ~15 pts and packing_quality by ~20 pts
            weight_cargo = self._get_layer_weight('cargo_sensitivity')
            weight_packing = self._get_layer_weight('packing_quality')
            
            delta_score = -(15 * weight_cargo + 20 * weight_packing)
            new_score = max(0, original_score + delta_score)
            
            insights.append({
                'change': 'Upgrade packing from carton to crate with foam protection',
                'original_score': round(original_score, 1),
                'new_score': round(new_score, 1),
                'delta': round(delta_score, 1),
                'comment': 'Better packing reduces damage risk and slightly improves insurance conditions.'
            })
        
        # What-if #2: Switch mode (if currently sea_freight and transit_time is long)
        current_mode = ctx['transport'].get('mode', 'sea_freight')
        if current_mode == 'sea_freight' and ctx['transport'].get('transit_time', 0) > 14:
            # Air freight reduces transit_time_variance, weather_climate, route_complexity significantly
            weight_variance = self._get_layer_weight('transit_time_variance')
            weight_weather = self._get_layer_weight('weather_climate')
            weight_route = self._get_layer_weight('route_complexity')
            
            delta_score = -(30 * weight_variance + 25 * weight_weather + 20 * weight_route)
            new_score = max(0, original_score + delta_score)
            
            insights.append({
                'change': 'Switch mode from sea_freight to air_freight',
                'original_score': round(original_score, 1),
                'new_score': round(new_score, 1),
                'delta': round(delta_score, 1),
                'comment': 'Transit time drops significantly (3-5 days vs 22 days), reducing delay and weather risk. Trade-off: ~4-5× cost increase.'
            })
        
        # What-if #3: Upgrade carrier (if carrier_performance is high)
        if layer_scores.get('carrier_performance', 0) > 60:
            weight = self._get_layer_weight('carrier_performance')
            delta_score = -(25 * weight)
            new_score = max(0, original_score + delta_score)
            
            insights.append({
                'change': 'Upgrade to premium carrier tier',
                'original_score': round(original_score, 1),
                'new_score': round(new_score, 1),
                'delta': round(delta_score, 1),
                'comment': 'Premium carrier with 95%+ on-time performance reduces schedule risk. Cost increase: ~15-20%.'
            })
        
        # What-if #4: Alternative port (if port_congestion is high)
        if layer_scores.get('port_congestion', 0) > 65:
            weight = self._get_layer_weight('port_congestion')
            delta_score = -(30 * weight)
            new_score = max(0, original_score + delta_score)
            
            insights.append({
                'change': 'Route through alternative port to avoid congestion',
                'original_score': round(original_score, 1),
                'new_score': round(new_score, 1),
                'delta': round(delta_score, 1),
                'comment': 'Avoiding congested port reduces delay risk significantly. May add inland transport time.'
            })
        
        # What-if #5: Upgrade insurance (if insurance_adequacy is poor)
        if layer_scores.get('insurance_adequacy', 0) > 60:
            weight = self._get_layer_weight('insurance_adequacy')
            delta_score = -(35 * weight)
            new_score = max(0, original_score + delta_score)
            
            insights.append({
                'change': 'Upgrade insurance from ICC B to ICC A (All Risks)',
                'original_score': round(original_score, 1),
                'new_score': round(new_score, 1),
                'delta': round(delta_score, 1),
                'comment': 'Comprehensive coverage significantly reduces financial exposure. Premium increase: ~0.1-0.2% of cargo value.'
            })
        
        return insights[:4]  # Return top 4 what-if scenarios
    
    def _estimate_confidence(self, ctx: Dict, validation: Dict) -> float:
        """
        Estimate confidence in the risk assessment (0-1 scale)
        """
        
        base_confidence = 0.85
        
        # Deduct for validation warnings
        warnings = validation.get('warnings', [])
        if len(warnings) > 5:
            base_confidence -= 0.10
        elif len(warnings) > 2:
            base_confidence -= 0.05
        
        # Deduct for missing critical data
        transport = ctx.get('transport', {})
        cargo = ctx.get('cargo', {})
        seller = ctx.get('seller', {})
        buyer = ctx.get('buyer', {})
        
        # Check for missing data
        if not buyer.get('company_name'):
            base_confidence -= 0.05
        
        if not cargo.get('hs_code'):
            base_confidence -= 0.03
        
        if not cargo.get('insurance_coverage'):
            base_confidence -= 0.03
        
        if not transport.get('reliability_score'):
            base_confidence -= 0.04
        
        # Bonus for comprehensive data
        if ctx.get('monte_carlo'):
            base_confidence += 0.05
        
        if ctx.get('esg'):
            base_confidence += 0.02
        
        # Clamp to [0, 1]
        confidence = max(0.0, min(1.0, base_confidence))
        
        return round(confidence, 3)
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _layer_to_category(self, layer_name: str, driver_tree: Dict) -> str:
        """Find which category a layer belongs to"""
        if not driver_tree:
            return 'unknown'
        
        for cat_key, cat_data in driver_tree.items():
            for driver in cat_data.get('drivers', []):
                if driver['layer'] == layer_name:
                    return cat_key
        
        return 'unknown'
    
    def _get_layer_weight(self, layer_name: str) -> float:
        """Get layer weight from V21 config"""
        try:
            from .risk_scoring_engine import RiskScoringEngineV21
        except ImportError:
            from risk_scoring_engine import RiskScoringEngineV21
        
        return RiskScoringEngineV21.RISK_LAYERS.get(layer_name, {}).get('weight', 0.05)
    
    def _format_layer_name(self, layer_name: str) -> str:
        """Convert layer_name to human-readable"""
        return ' '.join(word.capitalize() for word in layer_name.split('_'))
    
    def _generate_driver_reason(self, layer_name: str, score: float, ctx: Dict) -> str:
        """Generate short reason for driver score"""
        
        reasons = {
            'cargo_sensitivity': f"Cargo type '{ctx['cargo'].get('sensitivity', 'standard')}' requires special handling precautions",
            'port_congestion': f"Destination port {ctx['transport'].get('pod', 'POD')} shows elevated congestion levels",
            'carrier_performance': f"Carrier reliability score {ctx['transport'].get('reliability_score', 50):.0f}/100 indicates performance variability",
            'weather_climate': "Seasonal weather patterns present disruption risk during transit period",
            'incoterm_risk': f"Incoterm {ctx['transport'].get('incoterm', 'FOB')} places significant responsibility on your side",
            'market_volatility': "Freight market shows elevated volatility and pricing uncertainty",
            'packing_quality': f"Packing type '{ctx['cargo'].get('packing_type', 'standard')}' may be insufficient for cargo sensitivity level",
            'route_complexity': f"Route transit time of {ctx['transport'].get('transit_time', 0)} days indicates moderate complexity",
            'documentation_complexity': "Documentation requirements for this trade lane are elevated",
            'trade_compliance': f"Trade route {ctx['seller'].get('country', 'N/A')} → {ctx['buyer'].get('country', 'N/A')} has compliance considerations"
        }
        
        return reasons.get(layer_name, f"Risk factor scores {score:.0f}/100 indicating elevated concern")
    
    def _suggest_driver_action(self, layer_name: str, score: float, ctx: Dict) -> str:
        """Suggest action for driver"""
        
        actions = {
            'cargo_sensitivity': 'Upgrade to crate with foam protection and shock sensors',
            'port_congestion': 'Book priority berthing or route through alternative port',
            'carrier_performance': 'Upgrade to premium carrier tier with 95%+ on-time rate',
            'weather_climate': 'Monitor forecasts and prepare weather routing contingencies',
            'incoterm_risk': 'Renegotiate Incoterm or clarify responsibility boundaries',
            'market_volatility': 'Lock rates with mid-term contracts (3-6 months)',
            'packing_quality': 'Use certified packing service with quality inspection',
            'route_complexity': 'Simplify route or add tracking checkpoints',
            'documentation_complexity': 'Engage experienced customs broker early',
            'trade_compliance': 'Conduct comprehensive sanctions and compliance screening',
            'insurance_adequacy': 'Upgrade insurance coverage to All Risks (ICC A)',
            'seller_credibility': 'Conduct enhanced due diligence and verification',
            'transit_time_variance': 'Select guaranteed delivery service with penalty clauses'
        }
        
        return actions.get(layer_name, 'Implement standard mitigation measures')
    
    def _explain_root_cause(self, layer_name: str, score: float, ctx: Dict) -> str:
        """Explain why this driver has its current score"""
        
        if layer_name == 'port_congestion':
            pod = ctx['transport'].get('pod', 'destination')
            return f"Port {pod} has documented congestion issues based on historical vessel wait times and berth availability"
        
        elif layer_name == 'cargo_sensitivity':
            sensitivity = ctx['cargo'].get('sensitivity', 'standard')
            packing = ctx['cargo'].get('packing_type', 'standard')
            return f"Cargo classified as '{sensitivity}' with '{packing}' packaging creates elevated handling risk"
        
        elif layer_name == 'carrier_performance':
            reliability = ctx['transport'].get('reliability_score', 50)
            return f"Carrier reliability score of {reliability}/100 is below industry benchmark (85+)"
        
        elif layer_name == 'weather_climate':
            return "Route and timing coincide with seasonal weather patterns that historically cause disruptions"
        
        elif layer_name == 'market_volatility':
            if ctx.get('gfi'):
                pressure = ctx['gfi']['pressure']['pressure_level']
                return f"Freight market pressure is {pressure.upper()} with elevated rate volatility"
            return "Market conditions show volatility above historical averages"
        
        else:
            return f"Multiple factors contribute to {self._format_layer_name(layer_name)} scoring {score:.0f}/100"
    
    def _explain_consequence(self, layer_name: str, score: float) -> str:
        """Explain the consequence of this risk driver"""
        
        consequences = {
            'cargo_sensitivity': 'Higher probability of cargo damage during handling and transit',
            'port_congestion': 'Increased vessel waiting time and unpredictable delivery schedule',
            'carrier_performance': 'Greater likelihood of delays and service disruptions',
            'weather_climate': 'Potential for weather-related delays and route diversions',
            'market_volatility': 'Freight rate instability and capacity availability concerns',
            'packing_quality': 'Elevated risk of damage from inadequate protection',
            'trade_compliance': 'Possible customs delays or regulatory holds',
            'insurance_adequacy': 'Insufficient financial protection against loss events'
        }
        
        return consequences.get(layer_name, 'Contributes to overall shipment risk level')

