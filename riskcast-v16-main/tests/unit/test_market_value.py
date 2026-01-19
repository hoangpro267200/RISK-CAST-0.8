"""
Tests for Pipeline E: Market Value Proof & ROI Logic

Tests the ROI calculator, case study generator, and insurance premium calculator.

Author: RISKCAST Team
"""

import pytest
from unittest.mock import Mock, patch
import json

# Test imports
from app.services.roi_calculator import (
    ROICalculator,
    ROIScenario,
    CompanyProfile,
    CostAssumptions,
    BenefitAssumptions,
    calculate_roi,
    get_default_assumptions
)
from app.services.case_study_generator import (
    CaseStudyGenerator,
    generate_case_study,
    list_templates
)
from app.services.insurance_premium_calculator import (
    InsurancePremiumCalculator,
    RiskClass,
    calculate_premium,
    calculate_portfolio_premium,
    estimate_savings
)


# =============================================================================
# ROI Calculator Tests
# =============================================================================

class TestROICalculator:
    """Tests for ROI calculation functionality."""
    
    @pytest.fixture
    def sample_scenario(self):
        """Create sample ROI scenario."""
        return ROIScenario(
            company_profile=CompanyProfile(
                company_name="Test Company",
                annual_shipments=1000,
                avg_cargo_value_usd=100000,
                annual_revenue_usd=50000000,
                current_delay_rate=0.15,
                current_loss_rate=0.05
            ),
            cost_assumptions=CostAssumptions(
                annual_subscription_usd=12000,
                implementation_cost_usd=25000,
                training_cost_usd=5000,
                integration_cost_usd=15000,
                annual_support_usd=3000
            ),
            benefit_assumptions=BenefitAssumptions(
                delay_reduction_pct=0.30,
                loss_reduction_pct=0.25,
                insurance_rate_reduction_pct=0.15
            ),
            years=3
        )
    
    def test_roi_calculation_returns_positive_roi(self, sample_scenario):
        """Test that ROI calculation returns positive ROI for typical scenario."""
        result = ROICalculator.calculate_roi(sample_scenario)
        
        assert result.summary['roi_percentage'] > 0
        assert result.summary['net_benefit_3yr'] > 0
        assert result.summary['payback_period_years'] < 3
    
    def test_roi_calculation_has_required_fields(self, sample_scenario):
        """Test that ROI result contains all required fields."""
        result = ROICalculator.calculate_roi(sample_scenario)
        
        # Summary fields
        assert 'total_cost_3yr' in result.summary
        assert 'total_benefit_3yr' in result.summary
        assert 'net_benefit_3yr' in result.summary
        assert 'roi_percentage' in result.summary
        assert 'payback_period_months' in result.summary
        assert 'npv' in result.summary
        
        # Breakdown fields
        assert 'subscription' in result.cost_breakdown
        assert 'implementation' in result.cost_breakdown
        assert 'delay_cost_avoidance' in result.benefit_breakdown
        assert 'loss_cost_avoidance' in result.benefit_breakdown
        
        # Year-by-year
        assert len(result.year_by_year['costs']) == 3
        assert len(result.year_by_year['benefits']) == 3
    
    def test_roi_first_year_includes_implementation_costs(self, sample_scenario):
        """Test that first year costs include implementation."""
        result = ROICalculator.calculate_roi(sample_scenario)
        
        year1_cost = result.year_by_year['costs'][0]
        year2_cost = result.year_by_year['costs'][1]
        
        # Year 1 should be higher due to implementation costs
        assert year1_cost > year2_cost
    
    def test_roi_with_high_shipment_volume(self):
        """Test ROI improves with higher shipment volume."""
        low_volume = ROIScenario(
            company_profile=CompanyProfile(annual_shipments=500),
            cost_assumptions=CostAssumptions(),
            benefit_assumptions=BenefitAssumptions(),
            years=3
        )
        
        high_volume = ROIScenario(
            company_profile=CompanyProfile(annual_shipments=5000),
            cost_assumptions=CostAssumptions(),
            benefit_assumptions=BenefitAssumptions(),
            years=3
        )
        
        low_result = ROICalculator.calculate_roi(low_volume)
        high_result = ROICalculator.calculate_roi(high_volume)
        
        assert high_result.summary['roi_percentage'] > low_result.summary['roi_percentage']
    
    def test_payback_period_calculation(self, sample_scenario):
        """Test payback period is calculated correctly."""
        result = ROICalculator.calculate_roi(sample_scenario)
        
        payback_months = result.summary['payback_period_months']
        
        # Should be less than 12 months for typical scenario
        assert payback_months < 12
        assert payback_months > 0
    
    def test_npv_calculation(self, sample_scenario):
        """Test NPV is calculated correctly with discount rate."""
        result = ROICalculator.calculate_roi(sample_scenario)
        
        # NPV should be positive and less than undiscounted net benefit
        assert result.summary['npv'] > 0
        assert result.summary['npv'] < result.summary['net_benefit_3yr']
    
    def test_recommendation_generation(self, sample_scenario):
        """Test recommendation is generated based on ROI."""
        result = ROICalculator.calculate_roi(sample_scenario)
        
        assert result.recommendation is not None
        assert len(result.recommendation) > 0
        assert any(grade in result.recommendation for grade in ['STRONG BUY', 'RECOMMENDED', 'FAVORABLE', 'MARGINAL', 'NEEDS REVIEW'])
    
    def test_convenience_function_calculate_roi(self):
        """Test the convenience function works correctly."""
        profile = {
            'annual_shipments': 1000,
            'avg_cargo_value_usd': 100000
        }
        
        result = calculate_roi(profile)
        
        assert 'summary' in result
        assert 'recommendation' in result
    
    def test_get_default_assumptions(self):
        """Test default assumptions are returned correctly."""
        defaults = get_default_assumptions()
        
        assert 'company_profile' in defaults
        assert 'cost_assumptions' in defaults
        assert 'benefit_assumptions' in defaults


# =============================================================================
# Case Study Generator Tests
# =============================================================================

class TestCaseStudyGenerator:
    """Tests for case study generation functionality."""
    
    def test_generate_forwarder_case_study(self):
        """Test generating forwarder case study."""
        result = CaseStudyGenerator.generate_case_study(
            template_type='forwarder',
            seed=42
        )
        
        assert result.title is not None
        assert 'forwarder' in result.metadata['template_type']
        assert result.company_profile is not None
        assert len(result.challenges) > 0
        assert result.results is not None
    
    def test_generate_manufacturer_case_study(self):
        """Test generating manufacturer case study."""
        result = CaseStudyGenerator.generate_case_study(
            template_type='manufacturer',
            seed=42
        )
        
        assert result.title is not None
        assert 'manufacturer' in result.metadata['template_type']
        assert result.quote is not None
    
    def test_generate_insurance_case_study(self):
        """Test generating insurance case study."""
        result = CaseStudyGenerator.generate_case_study(
            template_type='insurance',
            seed=42
        )
        
        assert result.title is not None
        assert 'insurance' in result.metadata['template_type']
    
    def test_invalid_template_type_raises_error(self):
        """Test that invalid template type raises error."""
        with pytest.raises(ValueError):
            CaseStudyGenerator.generate_case_study(template_type='invalid')
    
    def test_case_study_with_custom_data(self):
        """Test generating case study with custom company data."""
        custom_data = {
            'company_name': 'Acme Logistics',
            'company_size': 'enterprise',
            'annual_shipments': 5000,
            'timeframe': '9 months'
        }
        
        result = CaseStudyGenerator.generate_case_study(
            template_type='forwarder',
            company_data=custom_data,
            anonymize=False
        )
        
        assert result.company_profile['name'] == 'Acme Logistics'
    
    def test_anonymization(self):
        """Test that company name is anonymized."""
        custom_data = {
            'company_name': 'Secret Corp International'
        }
        
        result = CaseStudyGenerator.generate_case_study(
            template_type='forwarder',
            company_data=custom_data,
            anonymize=True
        )
        
        assert 'Secret Corp International' not in result.company_profile['name']
        assert '[' in result.company_profile['name']  # Anonymized format
    
    def test_reproducibility_with_seed(self):
        """Test that same seed produces same results."""
        result1 = CaseStudyGenerator.generate_case_study(
            template_type='forwarder',
            seed=12345
        )
        
        result2 = CaseStudyGenerator.generate_case_study(
            template_type='forwarder',
            seed=12345
        )
        
        assert result1.results == result2.results
    
    def test_list_templates(self):
        """Test listing available templates."""
        templates = CaseStudyGenerator.list_templates()
        
        assert len(templates) == 3
        types = [t['type'] for t in templates]
        assert 'forwarder' in types
        assert 'manufacturer' in types
        assert 'insurance' in types
    
    def test_generate_multiple_case_studies(self):
        """Test generating multiple case studies."""
        results = CaseStudyGenerator.generate_multiple(
            template_type='forwarder',
            count=3
        )
        
        assert len(results) == 3
        # Each should be unique
        ids = [r.metadata['case_study_id'] for r in results]
        assert len(set(ids)) == 3
    
    def test_to_dict_conversion(self):
        """Test case study converts to dictionary correctly."""
        result = CaseStudyGenerator.generate_case_study(
            template_type='forwarder',
            seed=42
        )
        
        as_dict = result.to_dict()
        
        assert isinstance(as_dict, dict)
        assert 'title' in as_dict
        assert 'company_profile' in as_dict
        assert 'results' in as_dict


# =============================================================================
# Insurance Premium Calculator Tests
# =============================================================================

class TestInsurancePremiumCalculator:
    """Tests for insurance premium calculation functionality."""
    
    def test_calculate_premium_basic(self):
        """Test basic premium calculation."""
        result = InsurancePremiumCalculator.calculate_premium(
            cargo_value=100000,
            transport_mode='ocean',
            risk_score=50
        )
        
        assert result.premium_usd > 0
        assert result.risk_class == 'class_c'  # Risk score 50 = Class C
        assert result.recommended_deductible_usd > 0
    
    def test_risk_class_determination(self):
        """Test risk class is determined correctly."""
        # Class A: 0-30
        result_a = InsurancePremiumCalculator.calculate_premium(100000, 'ocean', 25)
        assert result_a.risk_class == 'class_a'
        
        # Class B: 30-50
        result_b = InsurancePremiumCalculator.calculate_premium(100000, 'ocean', 40)
        assert result_b.risk_class == 'class_b'
        
        # Class C: 50-70
        result_c = InsurancePremiumCalculator.calculate_premium(100000, 'ocean', 60)
        assert result_c.risk_class == 'class_c'
        
        # Class D: 70-85
        result_d = InsurancePremiumCalculator.calculate_premium(100000, 'ocean', 75)
        assert result_d.risk_class == 'class_d'
        
        # Class E: 85+
        result_e = InsurancePremiumCalculator.calculate_premium(100000, 'ocean', 90)
        assert result_e.risk_class == 'class_e'
    
    def test_premium_increases_with_risk_score(self):
        """Test that premium increases with higher risk score."""
        low_risk = InsurancePremiumCalculator.calculate_premium(100000, 'ocean', 20)
        high_risk = InsurancePremiumCalculator.calculate_premium(100000, 'ocean', 80)
        
        assert high_risk.premium_usd > low_risk.premium_usd
    
    def test_transport_mode_affects_base_rate(self):
        """Test different transport modes have different base rates."""
        ocean = InsurancePremiumCalculator.calculate_premium(100000, 'ocean', 50)
        air = InsurancePremiumCalculator.calculate_premium(100000, 'air', 50)
        
        # Ocean should have higher base rate than air
        assert ocean.base_rate > air.base_rate
    
    def test_hazmat_surcharge(self):
        """Test hazmat cargo has surcharge applied."""
        normal = InsurancePremiumCalculator.calculate_premium(
            100000, 'ocean', 50
        )
        
        hazmat = InsurancePremiumCalculator.calculate_premium(
            100000, 'ocean', 50,
            additional_factors={'hazmat': True}
        )
        
        assert hazmat.premium_usd > normal.premium_usd
    
    def test_cargo_type_adjustment(self):
        """Test cargo type affects premium."""
        general = InsurancePremiumCalculator.calculate_premium(
            100000, 'ocean', 50, cargo_type='general'
        )
        
        electronics = InsurancePremiumCalculator.calculate_premium(
            100000, 'ocean', 50, cargo_type='electronics'
        )
        
        assert electronics.premium_usd > general.premium_usd
    
    def test_deductible_recommendations(self):
        """Test deductible recommendations vary with risk."""
        low_risk = InsurancePremiumCalculator.calculate_premium(100000, 'ocean', 20)
        high_risk = InsurancePremiumCalculator.calculate_premium(100000, 'ocean', 80)
        
        # Low risk should have higher recommended deductible
        assert low_risk.recommended_deductible_usd > high_risk.recommended_deductible_usd
    
    def test_recommendations_generated(self):
        """Test that recommendations are generated."""
        result = InsurancePremiumCalculator.calculate_premium(100000, 'ocean', 50)
        
        assert isinstance(result.recommendations, list)
        assert len(result.recommendations) > 0
    
    def test_comparison_to_baseline(self):
        """Test comparison to baseline is calculated."""
        result = InsurancePremiumCalculator.calculate_premium(100000, 'ocean', 80)
        
        assert 'baseline_premium' in result.comparison_to_baseline
        assert 'adjustment_amount' in result.comparison_to_baseline
        assert 'adjustment_pct' in result.comparison_to_baseline


class TestPortfolioPremium:
    """Tests for portfolio premium calculation."""
    
    @pytest.fixture
    def sample_portfolio(self):
        """Create sample portfolio of shipments."""
        return [
            {'cargo_value': 100000, 'transport_mode': 'ocean', 'risk_score': 30},
            {'cargo_value': 150000, 'transport_mode': 'air', 'risk_score': 45},
            {'cargo_value': 200000, 'transport_mode': 'ocean', 'risk_score': 60},
            {'cargo_value': 75000, 'transport_mode': 'road', 'risk_score': 55},
            {'cargo_value': 125000, 'transport_mode': 'rail', 'risk_score': 40},
        ]
    
    def test_portfolio_premium_calculation(self, sample_portfolio):
        """Test portfolio premium is calculated."""
        result = InsurancePremiumCalculator.calculate_portfolio_premium(sample_portfolio)
        
        assert result.total_premium_before_discount > 0
        assert result.shipment_count == 5
        assert result.average_premium_per_shipment > 0
    
    def test_portfolio_volume_discount(self):
        """Test volume discount is applied for large portfolios."""
        # Small portfolio: no discount
        small = [{'cargo_value': 100000, 'transport_mode': 'ocean', 'risk_score': 50}] * 5
        
        # Large portfolio: should have discount
        large = [{'cargo_value': 100000, 'transport_mode': 'ocean', 'risk_score': 50}] * 50
        
        small_result = InsurancePremiumCalculator.calculate_portfolio_premium(small)
        large_result = InsurancePremiumCalculator.calculate_portfolio_premium(large)
        
        # Large portfolio should have higher discount percentage
        assert large_result.portfolio_discount_pct > small_result.portfolio_discount_pct
    
    def test_risk_distribution_analysis(self, sample_portfolio):
        """Test risk distribution is analyzed."""
        result = InsurancePremiumCalculator.calculate_portfolio_premium(sample_portfolio)
        
        assert 'risk_distribution' in result.to_dict()
        assert len(result.risk_distribution) > 0
    
    def test_portfolio_recommendations(self, sample_portfolio):
        """Test portfolio-level recommendations are generated."""
        result = InsurancePremiumCalculator.calculate_portfolio_premium(sample_portfolio)
        
        assert isinstance(result.recommendations, list)
    
    def test_empty_portfolio_raises_error(self):
        """Test empty portfolio raises error."""
        with pytest.raises(ValueError):
            InsurancePremiumCalculator.calculate_portfolio_premium([])


class TestSavingsEstimation:
    """Tests for savings estimation functionality."""
    
    def test_savings_estimate(self):
        """Test savings estimate calculation."""
        result = InsurancePremiumCalculator.estimate_savings_with_riskcast(
            current_premium=0,
            current_risk_score=70,
            projected_risk_score=40,
            cargo_value=100000,
            transport_mode='ocean'
        )
        
        assert result['estimated_savings'] > 0
        assert result['current_premium'] > result['projected_premium']
        assert result['savings_percentage'] > 0
    
    def test_risk_class_improvement(self):
        """Test risk class improvement is reflected."""
        result = InsurancePremiumCalculator.estimate_savings_with_riskcast(
            current_premium=0,
            current_risk_score=85,  # Class E
            projected_risk_score=25,  # Class A
            cargo_value=100000,
            transport_mode='ocean'
        )
        
        assert result['current_risk_class'] == 'class_e'
        assert result['projected_risk_class'] == 'class_a'
    
    def test_convenience_functions(self):
        """Test convenience functions work correctly."""
        premium = calculate_premium(100000, 'ocean', 50)
        assert 'premium_usd' in premium
        
        savings = estimate_savings(70, 40, 100000, 'ocean')
        assert 'estimated_savings' in savings


# =============================================================================
# Integration Tests
# =============================================================================

class TestMarketValueIntegration:
    """Integration tests for market value components."""
    
    def test_roi_drives_case_study_metrics(self):
        """Test that ROI calculations align with case study ranges."""
        # Get ROI result
        roi_result = calculate_roi({
            'annual_shipments': 1000,
            'avg_cargo_value_usd': 100000,
            'current_delay_rate': 0.15
        })
        
        # ROI should be within case study ranges
        roi_pct = roi_result['summary']['roi_percentage']
        
        # ROI should be positive and significant
        assert roi_pct > 100  # At minimum 100% ROI (pays for itself)
        # High ROI is expected given the value proposition
        assert roi_pct < 10000  # Sanity check upper bound
    
    def test_premium_savings_drives_roi(self):
        """Test insurance savings contribute to ROI."""
        # Calculate potential premium savings
        savings = estimate_savings(60, 30, 100000, 'ocean')
        
        # Savings should be meaningful
        assert savings['savings_percentage'] > 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
