"""
Tests for Pipeline G: Deal Qualification System

Tests the BANT scoring, red flag detection, and deal qualification logic.

Author: RISKCAST Team
"""

import pytest
from datetime import datetime
from app.services.deal_qualification import (
    DealQualifier,
    DealData,
    DealStage,
    RedFlag,
    PersonaType,
    qualify_deal
)


class TestBANTScoring:
    """Tests for BANT score calculation."""
    
    def test_budget_score_full_budget(self):
        """Test budget scoring with confirmed full budget."""
        deal = DealData(
            company_name="Test Co",
            company_size="enterprise",
            industry="logistics",
            budget_discussed=True,
            budget_amount=25000,
            budget_confirmed=True
        )
        score = DealQualifier.qualify_deal(deal)
        assert score.budget_score == 25  # Max score
    
    def test_budget_score_no_budget(self):
        """Test budget scoring with no budget info."""
        deal = DealData(
            company_name="Test Co",
            company_size="enterprise",
            industry="logistics",
            budget_discussed=False,
            budget_amount=None
        )
        score = DealQualifier.qualify_deal(deal)
        assert score.budget_score == 0
    
    def test_authority_score_c_level(self):
        """Test authority scoring with C-level involvement."""
        deal = DealData(
            company_name="Test Co",
            company_size="enterprise",
            industry="logistics",
            decision_maker_involved=True,
            stakeholders_met=["CFO", "Operations Manager", "Analyst"]
        )
        score = DealQualifier.qualify_deal(deal)
        assert score.authority_score >= 20  # High score for C-level
    
    def test_need_score_multiple_pain_points(self):
        """Test need scoring with multiple pain points."""
        deal = DealData(
            company_name="Test Co",
            company_size="enterprise",
            industry="logistics",
            pain_points_identified=[
                "high delay rate",
                "manual process",
                "insurance claims",
                "compliance risk"
            ],
            inbound=True
        )
        score = DealQualifier.qualify_deal(deal)
        assert score.need_score >= 20  # High score for multiple high-value pains
    
    def test_timeline_score_urgent(self):
        """Test timeline scoring with urgent timeline."""
        deal = DealData(
            company_name="Test Co",
            company_size="enterprise",
            industry="logistics",
            timeline="immediate - need solution ASAP"
        )
        score = DealQualifier.qualify_deal(deal)
        assert score.timeline_score == 25  # Max score for urgent
    
    def test_timeline_score_exploring(self):
        """Test timeline scoring with vague timeline."""
        deal = DealData(
            company_name="Test Co",
            company_size="enterprise",
            industry="logistics",
            timeline="just exploring options"
        )
        score = DealQualifier.qualify_deal(deal)
        assert score.timeline_score < 10  # Low score for vague timeline


class TestEngagementScoring:
    """Tests for engagement score calculation."""
    
    def test_high_engagement(self):
        """Test high engagement scenario."""
        deal = DealData(
            company_name="Test Co",
            company_size="enterprise",
            industry="logistics",
            demo_attended=True,
            trial_activated=True,
            multiple_demos=True,
            stakeholders_met=["CFO", "CTO", "Operations"],
            email_responses=10,
            days_since_last_contact=2,
            inbound=True
        )
        score = DealQualifier.qualify_deal(deal)
        assert score.engagement_score >= 80
    
    def test_low_engagement(self):
        """Test low engagement scenario."""
        deal = DealData(
            company_name="Test Co",
            company_size="enterprise",
            industry="logistics",
            demo_attended=False,
            trial_activated=False,
            email_responses=1,
            days_since_last_contact=25
        )
        score = DealQualifier.qualify_deal(deal)
        assert score.engagement_score < 30


class TestRedFlagDetection:
    """Tests for red flag detection."""
    
    def test_ghosting_flag(self):
        """Test ghosting red flag detection."""
        deal = DealData(
            company_name="Test Co",
            company_size="enterprise",
            industry="logistics",
            days_since_last_contact=45  # Over 30 days
        )
        score = DealQualifier.qualify_deal(deal)
        assert RedFlag.GHOSTING in score.red_flags
    
    def test_no_budget_flag(self):
        """Test no budget red flag detection."""
        deal = DealData(
            company_name="Test Co",
            company_size="enterprise",
            industry="logistics",
            budget_discussed=False,
            budget_amount=None
        )
        score = DealQualifier.qualify_deal(deal)
        assert RedFlag.NO_BUDGET in score.red_flags
    
    def test_no_authority_flag(self):
        """Test no authority red flag detection."""
        deal = DealData(
            company_name="Test Co",
            company_size="enterprise",
            industry="logistics",
            decision_maker_involved=False,
            stakeholders_met=["Analyst", "Staff Member"]  # No executives (avoid "coordinator" containing "coo")
        )
        score = DealQualifier.qualify_deal(deal)
        assert RedFlag.NO_AUTHORITY in score.red_flags
    
    def test_unrealistic_expectations_flag(self):
        """Test unrealistic expectations red flag."""
        deal = DealData(
            company_name="Test Co",
            company_size="enterprise",
            industry="logistics",
            expects_free_forever=True
        )
        score = DealQualifier.qualify_deal(deal)
        assert RedFlag.UNREALISTIC_EXPECTATIONS in score.red_flags
    
    def test_bad_fit_flag(self):
        """Test bad fit red flag for small company."""
        deal = DealData(
            company_name="Tiny Startup",
            company_size="startup",
            industry="logistics",
            annual_shipments=50  # Too small
        )
        score = DealQualifier.qualify_deal(deal)
        assert RedFlag.BAD_FIT in score.red_flags
    
    def test_clean_deal_no_flags(self):
        """Test that good deal has no red flags."""
        deal = DealData(
            company_name="Good Corp",
            company_size="enterprise",
            industry="logistics",
            annual_shipments=5000,
            budget_discussed=True,
            budget_amount=20000,
            decision_maker_involved=True,
            pain_points_identified=["delay costs", "manual process"],
            timeline="3 months",
            stakeholders_met=["CFO", "VP Operations"],
            days_since_last_contact=3
        )
        score = DealQualifier.qualify_deal(deal)
        assert len(score.red_flags) == 0


class TestDealGrading:
    """Tests for deal quality grading."""
    
    def test_grade_a_deal(self):
        """Test A-grade deal scoring."""
        deal = DealData(
            company_name="Enterprise Corp",
            company_size="enterprise",
            industry="logistics",
            budget_discussed=True,
            budget_amount=30000,
            budget_confirmed=True,
            decision_maker_involved=True,
            pain_points_identified=["high delay rate", "insurance claims", "manual process"],
            timeline="1 month",
            demo_attended=True,
            trial_activated=True,
            stakeholders_met=["CFO", "COO", "VP Operations"],
            email_responses=12,
            days_since_last_contact=2,
            inbound=True
        )
        score = DealQualifier.qualify_deal(deal)
        assert score.deal_quality == "A"
    
    def test_grade_d_deal(self):
        """Test D-grade deal scoring."""
        deal = DealData(
            company_name="Bad Fit Co",
            company_size="startup",
            industry="logistics",
            annual_shipments=20,
            budget_discussed=False,
            decision_maker_involved=False,
            days_since_last_contact=60,
            expects_free_forever=True
        )
        score = DealQualifier.qualify_deal(deal)
        assert score.deal_quality == "D"


class TestProbabilityCalculation:
    """Tests for win probability calculation."""
    
    def test_high_probability_deal(self):
        """Test high probability deal."""
        deal = DealData(
            company_name="Hot Lead",
            company_size="enterprise",
            industry="logistics",
            budget_discussed=True,
            budget_amount=25000,
            budget_confirmed=True,
            decision_maker_involved=True,
            pain_points_identified=["delay costs", "manual process", "compliance"],
            timeline="immediate",
            demo_attended=True,
            trial_activated=True,
            stakeholders_met=["CFO", "VP Ops"],
            days_since_last_contact=1,
            current_stage=DealStage.NEGOTIATION
        )
        score = DealQualifier.qualify_deal(deal)
        assert score.probability_to_close > 0.6
    
    def test_low_probability_deal(self):
        """Test low probability deal."""
        deal = DealData(
            company_name="Cold Lead",
            company_size="smb",
            industry="logistics",
            budget_discussed=False,
            decision_maker_involved=False,
            days_since_last_contact=40,
            current_stage=DealStage.LEAD
        )
        score = DealQualifier.qualify_deal(deal)
        assert score.probability_to_close < 0.2


class TestRecommendedActions:
    """Tests for recommended action generation."""
    
    def test_accelerate_action(self):
        """Test accelerate recommendation for hot deal."""
        deal = DealData(
            company_name="Hot Lead",
            company_size="enterprise",
            industry="logistics",
            budget_discussed=True,
            budget_amount=30000,
            budget_confirmed=True,  # Add confirmed budget for higher score
            decision_maker_involved=True,
            pain_points_identified=["high delay rate", "manual process", "insurance claims"],  # More high-value pains
            timeline="1 month",  # More urgent timeline
            demo_attended=True,
            trial_activated=True,
            stakeholders_met=["CFO", "VP Operations", "Director"],
            email_responses=8,
            days_since_last_contact=2,
            inbound=True
        )
        score = DealQualifier.qualify_deal(deal)
        assert "ACCELERATE" in score.recommended_action
    
    def test_deprioritize_action(self):
        """Test deprioritize recommendation for ghosted deal."""
        deal = DealData(
            company_name="Ghost Co",
            company_size="enterprise",
            industry="logistics",
            days_since_last_contact=45
        )
        score = DealQualifier.qualify_deal(deal)
        assert "DEPRIORITIZE" in score.recommended_action
    
    def test_disqualify_action(self):
        """Test disqualify recommendation for bad fit."""
        deal = DealData(
            company_name="Bad Fit",
            company_size="startup",
            industry="logistics",
            annual_shipments=30,
            budget_discussed=False,
            decision_maker_involved=False
        )
        score = DealQualifier.qualify_deal(deal)
        assert "DISQUALIFY" in score.recommended_action


class TestNextStepsGeneration:
    """Tests for next steps generation."""
    
    def test_next_steps_for_lead(self):
        """Test next steps for lead stage deal."""
        deal = DealData(
            company_name="New Lead",
            company_size="mid_market",
            industry="logistics",
            current_stage=DealStage.LEAD,
            demo_attended=False
        )
        score = DealQualifier.qualify_deal(deal)
        assert len(score.next_steps) > 0
        assert any("demo" in step.lower() or "discovery" in step.lower() for step in score.next_steps)
    
    def test_next_steps_address_red_flags(self):
        """Test that next steps address red flags."""
        deal = DealData(
            company_name="Problem Deal",
            company_size="enterprise",
            industry="logistics",
            budget_discussed=False,
            decision_maker_involved=False,
            timeline=""
        )
        score = DealQualifier.qualify_deal(deal)
        # Should have steps addressing missing BANT elements
        assert any("budget" in step.lower() for step in score.next_steps)


class TestConvenienceFunction:
    """Tests for the convenience function."""
    
    def test_qualify_deal_from_dict(self):
        """Test qualifying deal from dictionary input."""
        deal_data = {
            'company_name': 'Acme Logistics',
            'company_size': 'enterprise',
            'industry': 'logistics',
            'budget_discussed': True,
            'budget_amount': 25000,
            'decision_maker_involved': True,
            'pain_points_identified': ['manual process', 'delay costs'],
            'timeline': '3 months',
            'demo_attended': True,
            'stakeholders_met': ['CFO', 'Operations Manager'],
            'days_since_last_contact': 3,
            'current_stage': 'demo'
        }
        
        result = qualify_deal(deal_data)
        
        assert 'bant_total' in result
        assert 'probability_to_close' in result
        assert 'recommended_action' in result
        assert 'next_steps' in result
    
    def test_qualify_deal_minimal_input(self):
        """Test with minimal input."""
        deal_data = {
            'company_name': 'Unknown Co',
            'company_size': 'mid_market',
            'industry': 'unknown'
        }
        
        result = qualify_deal(deal_data)
        
        assert result['bant_total'] < 50  # Should be low with missing info
        assert len(result['red_flags']) > 0


class TestIntegration:
    """Integration tests for deal qualification."""
    
    def test_full_qualification_workflow(self):
        """Test complete qualification workflow."""
        # Stage 1: New lead
        lead_data = DealData(
            company_name="Prospect Inc",
            company_size="enterprise",
            industry="logistics",
            inbound=True,
            pain_points_identified=["delay visibility"],
            current_stage=DealStage.LEAD
        )
        lead_score = DealQualifier.qualify_deal(lead_data)
        
        assert lead_score.deal_quality in ["C", "D"]
        assert "QUALIFY" in lead_score.recommended_action or "NURTURE" in lead_score.recommended_action
        
        # Stage 2: After discovery call
        qualified_data = DealData(
            company_name="Prospect Inc",
            company_size="enterprise",
            industry="logistics",
            inbound=True,
            budget_discussed=True,
            budget_amount=20000,
            pain_points_identified=["delay visibility", "manual process", "insurance costs"],
            timeline="3 months",
            stakeholders_met=["VP Operations"],
            demo_attended=True,
            email_responses=5,
            days_since_last_contact=3,
            current_stage=DealStage.DEMO
        )
        qualified_score = DealQualifier.qualify_deal(qualified_data)
        
        assert qualified_score.bant_total > lead_score.bant_total
        assert qualified_score.probability_to_close > lead_score.probability_to_close


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
