"""
RiskCast V22 - API Response Generator
======================================
Complete risk assessment API with V22 modular architecture

Author: RiskCast AI Team
Version: 22.0
License: Proprietary
"""

from typing import Dict
from datetime import datetime

# V22 Modular imports
try:
    # When imported as module
    from .riskcast_validator import RiskCastV21Validator, ValidationSeverity
    from .risk_scoring_engine import RiskScoringEngineV21
    from .enhanced_features import EnhancedAlgorithmicFeaturesV21
    from .ai_explanation_engine import AIExplanationEngineV22
    from .risk_driver_tree_engine import RiskDriverTreeEngineV22
    from .esg_engine_v22 import ESGEngineV22
    from .monte_carlo_v22 import MonteCarloEngineV22
    from .global_freight_index_v22 import GlobalFreightIndexV22
    from .shock_scenario_engine_v22 import ShockScenarioEngineV22
    from .ai_explanation_ultra_v22 import AIExplanationUltraV22
except ImportError:
    # When run directly
    from riskcast_validator import RiskCastV21Validator, ValidationSeverity
    from risk_scoring_engine import RiskScoringEngineV21
    from enhanced_features import EnhancedAlgorithmicFeaturesV21
    from ai_explanation_engine import AIExplanationEngineV22
    from risk_driver_tree_engine import RiskDriverTreeEngineV22
    from esg_engine_v22 import ESGEngineV22
    from monte_carlo_v22 import MonteCarloEngineV22
    from global_freight_index_v22 import GlobalFreightIndexV22
    from shock_scenario_engine_v22 import ShockScenarioEngineV22
    from ai_explanation_ultra_v22 import AIExplanationUltraV22


def generate_risk_assessment_v22(input_data: Dict) -> Dict:
    """
    V22 Complete API Response Generator
    
    This function orchestrates all V22 modules to produce comprehensive
    risk assessment with support for modular features.
    
    V22 Architecture:
    - Validator: Input validation (60+ rules)
    - Risk Scoring Engine: 16-layer risk calculation
    - Enhanced Features: Predictive analytics & optimization
    
    V22 Future Modules (placeholders below):
    - AI Explanation Engine
    - Risk Driver Tree
    - ESG Scoring
    - Monte Carlo Simulation
    - Stress Testing
    """
    
    # ========================================================================
    # STEP 1: VALIDATION
    # ========================================================================
    
    validator = RiskCastV21Validator()
    is_valid, validation_results = validator.validate_full_input(input_data)
    
    if not is_valid:
        return {
            'success': False,
            'version': 'RiskCast V22.0',
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
    
    # ========================================================================
    # STEP 2: CORE RISK SCORING
    # ========================================================================
    
    scorer = RiskScoringEngineV21()
    risk_assessment = scorer.calculate_comprehensive_risk(
        input_data,
        input_data.get('modules', {})
    )
    
    # ========================================================================
    # STEP 3: ENHANCED ALGORITHMIC FEATURES
    # ========================================================================
    
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
    
    # ========================================================================
    # STEP 4: AI EXPLANATION ENGINE (V22 Module #1 - ACTIVE)
    # ========================================================================
    
    # Generate human-readable explanations for risk scores
    explainer = AIExplanationEngineV22()
    ai_explanation = explainer.generate_explanation(
        risk_assessment['layer_scores'],
        risk_assessment['category_scores'],
        risk_assessment['overall_score'],
        risk_assessment['risk_level']
    )
    
    # ========================================================================
    # STEP 5: RISK DRIVER TREE ENGINE (V22 Module #2 - ACTIVE)
    # ========================================================================
    
    # Build hierarchical risk factor tree showing contribution analysis
    driver_engine = RiskDriverTreeEngineV22()
    risk_driver_tree = driver_engine.build_driver_tree(
        risk_assessment['layer_scores']
    )
    
    # Generate tree summary statistics
    tree_summary = driver_engine.get_tree_summary(risk_driver_tree)
    
    # ========================================================================
    # STEP 6: ESG RISK ENGINE (V22 Module #3 - ACTIVE)
    # ========================================================================
    
    # Assess Environmental, Social, and Governance factors
    esg_engine = ESGEngineV22()
    esg_assessment = esg_engine.assess_esg(
        input_data.get('seller', {}),
        input_data.get('buyer', {}),
        {
            **input_data.get('cargo', {}),
            **input_data.get('transport', {})  # Merge transport data for mode, priority, etc.
        }
    )
    
    # ========================================================================
    # STEP 7: GLOBAL FREIGHT INDEX (V22 Phase 2.5 - ACTIVE)
    # ========================================================================
    
    # Compute Global Freight Index for trade lane market intelligence
    gfi_engine = GlobalFreightIndexV22()
    gfi_result = gfi_engine.compute_index(
        input_data.get('transport', {}),
        risk_assessment['layer_scores'].get('market_volatility', 40)
    )
    
    # ========================================================================
    # V22 FUTURE MODULES - INTEGRATION HOOKS
    # ========================================================================
    
    modules = input_data.get('modules', {})
    
    # Monte Carlo Simulation (V22 Module #4 - ACTIVE when enabled)
    # Run 10,000-scenario probabilistic simulation
    monte_carlo_results = None
    if modules.get('monte_carlo'):
        mc_engine = MonteCarloEngineV22(n_runs=10000)
        monte_carlo_results = mc_engine.run_simulation(
            input_data.get('transport', {}),
            input_data.get('cargo', {}),
            risk_assessment['layer_scores']
        )
    
    # Shock Scenario Engine (V22 Phase 2.6 - ACTIVE)
    # Run macro and disruption stress tests
    shock_engine = ShockScenarioEngineV22()
    shock_scenarios = shock_engine.run_scenarios(
        input_data,
        risk_assessment,
        gfi_result=gfi_result,
        monte_carlo_result=monte_carlo_results
    )
    
    # ========================================================================
    # STEP 8: AI EXPLANATION ULTRA LAYER (V22 Phase 2.7 - ACTIVE)
    # ========================================================================
    
    # Generate comprehensive multi-perspective explanation
    ultra_engine = AIExplanationUltraV22()
    ai_explanation_ultra = ultra_engine.generate_explanation({
        'input_data': input_data,
        'core': risk_assessment,
        'driver_tree': risk_driver_tree,
        'esg': esg_assessment,
        'monte_carlo': monte_carlo_results,
        'gfi': gfi_result,
        'shock': shock_scenarios,
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
        }
    })
    
    # ========================================================================
    # STEP 9: BUILD COMPREHENSIVE RESPONSE
    # ========================================================================
    
    response = {
        'success': True,
        'version': 'RiskCast V22.0',
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
            'sub_factor_scores': risk_assessment.get('sub_factor_scores', {}),  # V22 enhancement
            
            # Market risk with GFI adjustment (V22 Phase 2.5)
            'market_risk': {
                'base_market_volatility_score': risk_assessment['layer_scores'].get('market_volatility', 40),
                'gfi_adjusted_market_volatility_score': gfi_result['pressure']['market_risk_gfi_adjusted'],
                'pressure_level': gfi_result['pressure']['pressure_level'],
                'adjustment_factor': round(
                    gfi_result['pressure']['market_risk_gfi_adjusted'] / 
                    max(risk_assessment['layer_scores'].get('market_volatility', 40), 1), 
                    3
                )
            },
            
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
    
    # ========================================================================
    # STEP 10: ADD V22 MODULES TO RESPONSE
    # ========================================================================
    
    # Add AI Explanation (V22 Module #1 - Active)
    response['ai_explanation'] = ai_explanation
    
    # Add Risk Driver Tree (V22 Module #2 - Active)
    response['risk_driver_tree'] = risk_driver_tree
    response['risk_tree_summary'] = tree_summary
    
    # Add ESG Assessment (V22 Module #3 - Active)
    response['esg_assessment'] = esg_assessment
    
    # Add Global Freight Index (V22 Phase 2.5 - Active)
    response['global_freight_index'] = gfi_result
    
    # Add Shock Scenarios (V22 Phase 2.6 - Active)
    response['shock_scenarios'] = shock_scenarios
    
    # Add AI Explanation Ultra (V22 Phase 2.7 - Active)
    response['ai_explanation_ultra'] = ai_explanation_ultra
    
    if monte_carlo_results:
        response['monte_carlo_simulation'] = monte_carlo_results
    
    return response


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
            "insurance_optimization": True,
            "monte_carlo": True,  # Enable Monte Carlo simulation
            "stress_test": False
        }
    }
    
    result = generate_risk_assessment_v22(sample_shipment)
    
    print("=" * 80)
    print("RISKCAST V22 - RISK ASSESSMENT RESULT")
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
        
        # V22 Module #1: AI Explanation Engine
        if 'ai_explanation' in result:
            print(f"\n{'='*80}")
            print("AI EXPLANATION (V22 Module #1)")
            print("=" * 80)
            explanation = result['ai_explanation']
            print(f"\nOverview:")
            print(f"  {explanation['overview']}")
            print(f"\nTop Risk Drivers:")
            for driver in explanation['drivers']:
                print(f"  • {driver['layer']} ({driver['score']}/100) - {driver['impact']}")
                print(f"    {driver['explanation']}")
            print(f"\nQuick Recommendations:")
            for rec in explanation['recommendations'][:3]:
                print(f"  {rec}")
        
        # V22 Module #2: Risk Driver Tree
        if 'risk_driver_tree' in result:
            print(f"\n{'='*80}")
            print("RISK DRIVER TREE (V22 Module #2)")
            print("=" * 80)
            tree = result['risk_driver_tree']
            summary = result.get('risk_tree_summary', {})
            
            print(f"\nTree Summary:")
            print(f"  Total Risk Drivers: {summary.get('total_drivers', 0)}")
            print(f"  High Risk Drivers: {summary.get('high_risk_drivers', 0)}")
            if summary.get('riskiest_category'):
                print(f"  Riskiest Category: {summary['riskiest_category']['name']} ({summary['riskiest_category']['score']:.1f})")
            
            print(f"\nCategory Breakdown:")
            for category_key, category_data in tree.items():
                print(f"\n  {category_data['category_display_name']} - Score: {category_data['score']:.1f} ({category_data['severity'].upper()})")
                print(f"    Top Drivers:")
                for driver in category_data['drivers'][:2]:  # Show top 2 per category
                    print(f"      • {driver['layer_display_name']} ({driver['score']:.1f})")
                    if driver['root_causes']:
                        print(f"        Root Cause: {driver['root_causes'][0]}")
        
        # V22 Module #3: ESG Assessment
        if 'esg_assessment' in result:
            print(f"\n{'='*80}")
            print("ESG ASSESSMENT (V22 Module #3)")
            print("=" * 80)
            esg = result['esg_assessment']
            
            print(f"\nOverall ESG Score: {esg['overall_esg_score']:.1f}/100 ({esg['esg_level'].upper()}) - Grade: {esg['esg_grade']}")
            print(f"Total Violations: {esg['total_violations']}")
            
            print(f"\nESG Breakdown:")
            print(f"  Environmental: {esg['environmental']['score']:.1f} ({len(esg['environmental']['violations'])} violations)")
            print(f"  Social: {esg['social']['score']:.1f} ({len(esg['social']['violations'])} violations)")
            print(f"  Governance: {esg['governance']['score']:.1f} ({len(esg['governance']['violations'])} violations)")
            
            if esg.get('recommendations'):
                print(f"\nESG Recommendations:")
                for rec in esg['recommendations'][:3]:
                    print(f"  {rec}")
        
        # V22 Phase 2.5: Global Freight Index
        if 'global_freight_index' in result:
            print(f"\n{'='*80}")
            print("GLOBAL FREIGHT INDEX (V22 Phase 2.5)")
            print("=" * 80)
            gfi = result['global_freight_index']
            
            print(f"\nLane: {gfi['meta']['trade_lane']}")
            print(f"Lane Key: {gfi['lane_key']}")
            
            print(f"\nIndex Status:")
            print(f"  Current: {gfi['index']['current_index']:.1f} {gfi['index']['currency']}")
            print(f"  Baseline: {gfi['index']['baseline_index']:.1f}")
            print(f"  Relative: {gfi['index']['relative_to_baseline']:.2f}x ({((gfi['index']['relative_to_baseline']-1)*100):.1f}% {'above' if gfi['index']['relative_to_baseline'] > 1 else 'below'} baseline)")
            
            print(f"\nMarket Pressure:")
            print(f"  Pressure Level: {gfi['pressure']['pressure_level'].upper()}")
            print(f"  Pressure Score: {gfi['pressure']['pressure_score']:.2f}")
            print(f"  Market Risk Adjusted: {gfi['pressure']['market_risk_base']:.1f} → {gfi['pressure']['market_risk_gfi_adjusted']:.1f}")
            
            print(f"\nMarket Statistics (52-week):")
            stats = gfi['history']['statistics']
            print(f"  12-week Average: {stats['avg_12w']:.1f}")
            print(f"  Volatility (12w): {stats['volatility_12w']:.1%}")
            print(f"  Trend (4w): {stats['trend_direction'].upper()} ({stats['trend_4w_slope_pct']:+.1%})")
            print(f"  Range (52w): {stats['min_52w']:.1f} - {stats['max_52w']:.1f}")
            
            print(f"\nStrategy Recommendation: {gfi['strategy']['recommendation_tier'].upper()}")
            print(f"  {gfi['strategy']['summary']}")
            if gfi['strategy'].get('actions'):
                print(f"\n  Key Actions:")
                for action in gfi['strategy']['actions'][:3]:
                    print(f"    • {action}")
        
        # V22 Module #4: Monte Carlo Simulation
        if result.get('monte_carlo_simulation'):
            print(f"\n{'='*80}")
            print("MONTE CARLO SIMULATION (V22 Module #4)")
            print("=" * 80)
            mc = result['monte_carlo_simulation']
            
            if isinstance(mc, dict) and 'runs' in mc:
                print(f"\nSimulation: {mc['runs']:,} scenarios completed")
                print(f"\nETA Statistics:")
                print(f"  P50 (Median): {mc['eta_stats']['p50']:.1f} days")
                print(f"  P90: {mc['eta_stats']['p90']:.1f} days")
                print(f"  P95: {mc['eta_stats']['p95']:.1f} days")
                print(f"  Range: {mc['eta_stats']['min']:.1f} - {mc['eta_stats']['max']:.1f} days")
                
                print(f"\nLoss Statistics:")
                print(f"  Expected Loss: ${mc['loss_stats']['expected_loss']:,.0f}")
                print(f"  P95 Loss (VaR): ${mc['loss_stats']['p95_loss']:,.0f}")
                print(f"  Max Loss: ${mc['loss_stats']['max_loss']:,.0f}")
                
                print(f"\nRisk Metrics:")
                print(f"  Significant Delay Risk: {mc['risk_metrics']['prob_significant_delay']:.1f}%")
                print(f"  Catastrophic Loss Risk: {mc['risk_metrics']['prob_catastrophic_loss']:.1f}%")
                
                if mc.get('recommendations'):
                    print(f"\nMonte Carlo Recommendations:")
                    for rec in mc['recommendations'][:3]:
                        print(f"  {rec}")
        
        # V22 Phase 2.6: Shock Scenarios
        if 'shock_scenarios' in result:
            print(f"\n{'='*80}")
            print("SHOCK SCENARIOS (V22 Phase 2.6)")
            print("=" * 80)
            shock = result['shock_scenarios']
            
            print(f"\nBase Case:")
            print(f"  Risk Score: {shock['base_case']['overall_score']:.1f} ({shock['base_case']['risk_level'].upper()})")
            print(f"  Expected Loss: ${shock['base_case']['expected_loss_usd']:,.0f}")
            
            print(f"\nStress Test Summary:")
            print(f"  Scenarios Tested: {shock['scenario_count']}")
            print(f"  Worst Case: {shock['summary']['worst_case_scenario_name']}")
            print(f"  Worst Case Score: {shock['summary']['worst_case_overall_score']:.1f}")
            print(f"  Max Delay (P95): {shock['summary']['max_delay_p95_days']:.1f} days")
            print(f"  Resilience Score: {shock['summary']['resilience_score']:.1f}/100")
            
            print(f"\nRisk Distribution Across Scenarios:")
            for level, count in shock['summary']['scenario_risk_distribution'].items():
                if count > 0:
                    print(f"  {level.upper()}: {count} scenario(s)")
            
            print(f"\nTop 3 Worst-Case Scenarios:")
            sorted_scenarios = sorted(shock['scenarios'], key=lambda s: s['impact']['overall_score'], reverse=True)
            for i, scenario in enumerate(sorted_scenarios[:3], 1):
                print(f"\n  {i}. {scenario['name']} ({scenario['type'].upper()})")
                print(f"     Risk: {scenario['impact']['overall_score']:.1f} ({scenario['impact']['risk_level'].upper()})")
                print(f"     Impact: +{scenario['impact']['delta_vs_base']:.1f} pts, +${scenario['impact']['delta_expected_loss_usd']:,.0f} loss")
                print(f"     Delays: P50={scenario['impact']['delay_days_p50']:.1f}d, P95={scenario['impact']['delay_days_p95']:.1f}d")
                if scenario['recommendation']:
                    print(f"     Action: {scenario['recommendation']['summary']}")
        
        # V22 Phase 2.7: AI Explanation Ultra
        if 'ai_explanation_ultra' in result:
            print(f"\n{'='*80}")
            print("AI EXPLANATION ULTRA (V22 Phase 2.7)")
            print("=" * 80)
            ultra = result['ai_explanation_ultra']
            
            print(f"\nExecutive Summary:")
            print(f"  {ultra['executive_summary']}")
            
            print(f"\nKey Drivers ({len(ultra['key_drivers'])}):")
            for driver in ultra['key_drivers'][:3]:
                print(f"  • {driver['display_name']} ({driver['score']}/100)")
                print(f"    Reason: {driver['short_reason']}")
                print(f"    Action: {driver['suggested_action']}")
            
            if ultra.get('persona_views'):
                print(f"\nPersona Views:")
                for persona, view in ultra['persona_views'].items():
                    print(f"\n  {persona.upper().replace('_', ' ')}: {view['headline']}")
                    print(f"    {view['summary']}")
            
            if ultra.get('what_if_insights') and len(ultra['what_if_insights']) > 0:
                print(f"\nWhat-If Insights ({len(ultra['what_if_insights'])}):")
                for insight in ultra['what_if_insights'][:2]:
                    print(f"  • {insight['change']}")
                    print(f"    Impact: {insight['original_score']:.1f} → {insight['new_score']:.1f} ({insight['delta']:+.1f} pts)")
                    print(f"    {insight['comment']}")
            
            print(f"\nConfidence Score: {ultra['confidence_score']:.1%}")
        
        # V22 Module Status (Future)
        if result.get('stress_test'):
            print(f"\n{'='*80}")
            print("V22 MODULES STATUS")
            print("=" * 80)
            if result.get('stress_test'):
                print(f"Stress Test: {result['stress_test']['status']}")
    
    else:
        print("\nVALIDATION ERRORS:")
        for error in result.get('validation_errors', []):
            print(f"\n{error['field']}: {error['message']}")
            if error['suggestion']:
                print(f"  Suggestion: {error['suggestion']}")

