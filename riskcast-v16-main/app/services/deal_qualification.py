"""
RISKCAST Deal Qualification System
====================================
Score and qualify sales opportunities using BANT methodology.

Features:
- BANT scoring (Budget, Authority, Need, Timeline)
- Engagement signal analysis
- Red flag detection
- Win probability calculation
- Recommended next actions

Author: RISKCAST Team
Version: 2.0
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DealStage(Enum):
    """Sales pipeline stages."""
    LEAD = "lead"
    QUALIFIED = "qualified"
    DEMO = "demo"
    PILOT = "pilot"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class RedFlag(Enum):
    """Deal disqualification signals."""
    NO_BUDGET = "no_budget"
    NO_AUTHORITY = "no_authority"
    NO_NEED = "no_need"
    NO_TIMELINE = "no_timeline"
    GHOSTING = "ghosting"
    UNREALISTIC_EXPECTATIONS = "unrealistic_expectations"
    BAD_FIT = "bad_fit"
    COMPETITOR_PREFERENCE = "competitor_preference"
    INTERNAL_POLITICS = "internal_politics"
    
    @property
    def description(self) -> str:
        descriptions = {
            "no_budget": "No budget identified or discussed",
            "no_authority": "No decision maker involved",
            "no_need": "No clear pain points identified",
            "no_timeline": "No purchase timeline defined",
            "ghosting": "No response for 30+ days",
            "unrealistic_expectations": "Expects free/custom features",
            "bad_fit": "Company profile doesn't match ICP",
            "competitor_preference": "Strongly prefers competitor",
            "internal_politics": "Blocked by internal stakeholder"
        }
        return descriptions.get(self.value, "Unknown flag")
    
    @property
    def severity(self) -> str:
        """How serious is this red flag?"""
        critical = {RedFlag.NO_BUDGET, RedFlag.GHOSTING, RedFlag.BAD_FIT}
        high = {RedFlag.NO_AUTHORITY, RedFlag.COMPETITOR_PREFERENCE}
        
        if self in critical:
            return "critical"
        elif self in high:
            return "high"
        return "medium"


class PersonaType(Enum):
    """Buyer persona types."""
    ANALYST = "analyst"
    EXECUTIVE = "executive"
    PROCUREMENT = "procurement"
    UNDERWRITER = "underwriter"
    END_USER = "end_user"
    INVESTOR = "investor"
    ACADEMIC = "academic"


@dataclass
class StakeholderInfo:
    """Information about a stakeholder in the deal."""
    name: str
    title: str
    persona: PersonaType
    influence_level: int  # 1-10
    sentiment: str  # positive, neutral, negative, unknown
    last_contact: Optional[datetime] = None
    notes: str = ""


@dataclass
class DealScore:
    """Complete deal qualification score."""
    # BANT Scores (0-25 each, total 100)
    budget_score: float
    authority_score: float
    need_score: float
    timeline_score: float
    bant_total: float
    
    # Engagement metrics
    engagement_score: float  # 0-100
    
    # Red flags
    red_flags: List[RedFlag]
    red_flag_details: Dict[str, str]
    
    # Calculated metrics
    probability_to_close: float  # 0-1
    deal_quality: str  # A/B/C/D
    
    # Recommendations
    recommended_action: str
    next_steps: List[str]
    risks: List[str]
    
    # Metadata
    scored_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['red_flags'] = [f.value for f in self.red_flags]
        result['scored_at'] = self.scored_at.isoformat()
        return result


@dataclass
class DealData:
    """Input data for deal qualification."""
    # Company info
    company_name: str
    company_size: str  # startup, smb, mid_market, enterprise
    industry: str
    annual_shipments: Optional[int] = None
    
    # BANT indicators
    budget_discussed: bool = False
    budget_amount: Optional[float] = None
    budget_confirmed: bool = False
    decision_maker_involved: bool = False
    pain_points_identified: List[str] = field(default_factory=list)
    timeline: str = ""  # "immediate", "1 month", "3 months", "6 months", "year"
    
    # Engagement signals
    demo_attended: bool = False
    trial_activated: bool = False
    multiple_demos: bool = False
    stakeholders_met: List[str] = field(default_factory=list)
    email_responses: int = 0
    days_since_last_contact: int = 0
    inbound: bool = False  # Did they come to us?
    
    # Deal context
    current_stage: DealStage = DealStage.LEAD
    competitor_mentions: List[str] = field(default_factory=list)
    objections_raised: List[str] = field(default_factory=list)
    
    # Red flag indicators
    expects_free_forever: bool = False
    wants_custom_development: bool = False
    has_internal_solution: bool = False
    regulatory_constraints: bool = False


class DealQualifier:
    """
    Qualify sales opportunities using BANT + engagement signals.
    
    BANT = Budget, Authority, Need, Timeline
    """
    
    # Minimum scores for qualification
    QUALIFICATION_THRESHOLD = 50
    HIGH_QUALITY_THRESHOLD = 75
    
    # Company size weights
    SIZE_WEIGHTS = {
        'startup': 0.5,
        'smb': 0.7,
        'mid_market': 1.0,
        'enterprise': 1.2
    }
    
    # High-value pain points
    HIGH_VALUE_PAINS = [
        'high delay rate',
        'insurance claims',
        'manual process',
        'compliance risk',
        'customer complaints',
        'cargo loss',
        'premium costs'
    ]
    
    @staticmethod
    def qualify_deal(deal: DealData) -> DealScore:
        """
        Score and qualify a sales opportunity.
        
        Returns comprehensive DealScore with BANT analysis,
        engagement metrics, red flags, and recommendations.
        """
        # Calculate BANT scores
        budget_score = DealQualifier._score_budget(deal)
        authority_score = DealQualifier._score_authority(deal)
        need_score = DealQualifier._score_need(deal)
        timeline_score = DealQualifier._score_timeline(deal)
        bant_total = (budget_score + authority_score + need_score + timeline_score)
        
        # Calculate engagement score
        engagement_score = DealQualifier._score_engagement(deal)
        
        # Detect red flags
        red_flags = DealQualifier._detect_red_flags(deal)
        red_flag_details = {f.value: f.description for f in red_flags}
        
        # Calculate win probability
        probability = DealQualifier._calculate_probability(
            bant_total, engagement_score, red_flags, deal
        )
        
        # Determine deal quality grade
        deal_quality = DealQualifier._grade_deal(bant_total, engagement_score, red_flags)
        
        # Generate recommendations
        recommended_action = DealQualifier._recommend_action(
            bant_total, engagement_score, red_flags, deal
        )
        next_steps = DealQualifier._generate_next_steps(deal, red_flags)
        risks = DealQualifier._identify_risks(deal, red_flags)
        
        return DealScore(
            budget_score=budget_score,
            authority_score=authority_score,
            need_score=need_score,
            timeline_score=timeline_score,
            bant_total=bant_total,
            engagement_score=engagement_score,
            red_flags=red_flags,
            red_flag_details=red_flag_details,
            probability_to_close=probability,
            deal_quality=deal_quality,
            recommended_action=recommended_action,
            next_steps=next_steps,
            risks=risks
        )
    
    @staticmethod
    def _score_budget(deal: DealData) -> float:
        """Score budget qualification (0-25)."""
        score = 0.0
        
        # Budget discussed at all
        if deal.budget_discussed:
            score += 8
        
        # Budget amount known
        if deal.budget_amount:
            if deal.budget_amount >= 15000:  # Full subscription
                score += 12
            elif deal.budget_amount >= 10000:
                score += 10
            elif deal.budget_amount >= 5000:  # Entry tier
                score += 7
            else:
                score += 3
        
        # Budget confirmed/approved
        if deal.budget_confirmed:
            score += 5
        
        return min(score, 25)
    
    @staticmethod
    def _score_authority(deal: DealData) -> float:
        """Score decision authority (0-25)."""
        score = 0.0
        
        # Decision maker identified
        if deal.decision_maker_involved:
            score += 12
        
        # Stakeholder analysis
        stakeholders = ' '.join(deal.stakeholders_met).lower()
        
        if any(title in stakeholders for title in ['cfo', 'ceo', 'coo', 'president']):
            score += 10
        elif any(title in stakeholders for title in ['vp', 'vice president']):
            score += 8
        elif any(title in stakeholders for title in ['director', 'head of']):
            score += 6
        elif any(title in stakeholders for title in ['manager', 'lead']):
            score += 4
        elif deal.stakeholders_met:
            score += 2
        
        # Multiple stakeholders (buying committee)
        if len(deal.stakeholders_met) >= 3:
            score += 3
        elif len(deal.stakeholders_met) >= 2:
            score += 2
        
        return min(score, 25)
    
    @staticmethod
    def _score_need(deal: DealData) -> float:
        """Score need/pain points (0-25)."""
        score = 0.0
        
        pain_count = len(deal.pain_points_identified)
        
        # Number of pain points
        if pain_count >= 4:
            score += 12
        elif pain_count >= 3:
            score += 10
        elif pain_count >= 2:
            score += 7
        elif pain_count >= 1:
            score += 4
        
        # High-value pain points
        pains_lower = [p.lower() for p in deal.pain_points_identified]
        high_value_matches = sum(
            1 for hv in DealQualifier.HIGH_VALUE_PAINS
            if any(hv in p for p in pains_lower)
        )
        score += min(high_value_matches * 3, 9)
        
        # Inbound lead (they came to us = clear need)
        if deal.inbound:
            score += 4
        
        return min(score, 25)
    
    @staticmethod
    def _score_timeline(deal: DealData) -> float:
        """Score timeline urgency (0-25)."""
        score = 0.0
        timeline = deal.timeline.lower()
        
        if 'immediate' in timeline or 'asap' in timeline or 'urgent' in timeline:
            score += 25
        elif '1 month' in timeline or 'next month' in timeline:
            score += 22
        elif 'quarter' in timeline or '3 month' in timeline or '90 day' in timeline:
            score += 18
        elif '6 month' in timeline or 'half year' in timeline:
            score += 12
        elif 'year' in timeline or '12 month' in timeline:
            score += 8
        elif 'evaluating' in timeline or 'exploring' in timeline:
            score += 5
        else:
            score += 2  # No timeline = low urgency
        
        return score
    
    @staticmethod
    def _score_engagement(deal: DealData) -> float:
        """Score engagement level (0-100)."""
        score = 0.0
        
        # Demo engagement
        if deal.demo_attended:
            score += 20
        if deal.multiple_demos:
            score += 10
        
        # Trial activation (strong signal)
        if deal.trial_activated:
            score += 30
        
        # Email responsiveness
        score += min(deal.email_responses * 3, 15)
        
        # Recency of contact
        if deal.days_since_last_contact <= 3:
            score += 15
        elif deal.days_since_last_contact <= 7:
            score += 12
        elif deal.days_since_last_contact <= 14:
            score += 8
        elif deal.days_since_last_contact <= 30:
            score += 4
        
        # Stakeholder breadth
        score += min(len(deal.stakeholders_met) * 4, 12)
        
        # Inbound bonus
        if deal.inbound:
            score += 8
        
        return min(score, 100)
    
    @staticmethod
    def _detect_red_flags(deal: DealData) -> List[RedFlag]:
        """Detect deal red flags."""
        flags = []
        
        # No budget
        if not deal.budget_discussed and not deal.budget_amount:
            flags.append(RedFlag.NO_BUDGET)
        
        # No authority
        if not deal.decision_maker_involved:
            stakeholders = ' '.join(deal.stakeholders_met).lower()
            authority_titles = ['cfo', 'ceo', 'coo', 'vp', 'director', 'head']
            if not any(t in stakeholders for t in authority_titles):
                flags.append(RedFlag.NO_AUTHORITY)
        
        # No clear need
        if len(deal.pain_points_identified) == 0:
            flags.append(RedFlag.NO_NEED)
        
        # No timeline
        if not deal.timeline or deal.timeline.lower() in ['', 'unknown', 'none']:
            flags.append(RedFlag.NO_TIMELINE)
        
        # Ghosting
        if deal.days_since_last_contact > 30:
            flags.append(RedFlag.GHOSTING)
        
        # Unrealistic expectations
        if deal.expects_free_forever or deal.wants_custom_development:
            flags.append(RedFlag.UNREALISTIC_EXPECTATIONS)
        
        # Bad fit (small company, no shipments)
        if deal.company_size == 'startup' and (deal.annual_shipments or 0) < 100:
            flags.append(RedFlag.BAD_FIT)
        
        # Competitor preference
        if deal.competitor_mentions and any(
            'prefer' in o.lower() or 'better' in o.lower()
            for o in deal.objections_raised
        ):
            flags.append(RedFlag.COMPETITOR_PREFERENCE)
        
        return flags
    
    @staticmethod
    def _calculate_probability(
        bant_total: float,
        engagement_score: float,
        red_flags: List[RedFlag],
        deal: DealData
    ) -> float:
        """Calculate win probability (0-1)."""
        # Base probability from BANT (50% weight)
        bant_contrib = (bant_total / 100) * 0.50
        
        # Engagement contribution (30% weight)
        engagement_contrib = (engagement_score / 100) * 0.30
        
        # Stage bonus (10% weight)
        stage_weights = {
            DealStage.LEAD: 0.0,
            DealStage.QUALIFIED: 0.3,
            DealStage.DEMO: 0.5,
            DealStage.PILOT: 0.7,
            DealStage.NEGOTIATION: 0.85,
            DealStage.CLOSED_WON: 1.0,
            DealStage.CLOSED_LOST: 0.0
        }
        stage_contrib = stage_weights.get(deal.current_stage, 0.0) * 0.10
        
        # Company size multiplier (10% weight)
        size_mult = DealQualifier.SIZE_WEIGHTS.get(deal.company_size, 1.0) * 0.10
        
        base_probability = bant_contrib + engagement_contrib + stage_contrib + size_mult
        
        # Red flag penalties
        for flag in red_flags:
            if flag.severity == "critical":
                base_probability *= 0.5
            elif flag.severity == "high":
                base_probability *= 0.7
            else:
                base_probability *= 0.85
        
        return max(0.0, min(base_probability, 1.0))
    
    @staticmethod
    def _grade_deal(
        bant_total: float,
        engagement_score: float,
        red_flags: List[RedFlag]
    ) -> str:
        """Assign deal quality grade (A/B/C/D)."""
        combined_score = (bant_total * 0.6) + (engagement_score * 0.4)
        
        # Degrade for red flags
        critical_flags = sum(1 for f in red_flags if f.severity == "critical")
        high_flags = sum(1 for f in red_flags if f.severity == "high")
        
        if critical_flags >= 2:
            return "D"
        elif critical_flags >= 1:
            combined_score -= 20
        
        if high_flags >= 2:
            combined_score -= 15
        elif high_flags >= 1:
            combined_score -= 10
        
        if combined_score >= 80:
            return "A"
        elif combined_score >= 60:
            return "B"
        elif combined_score >= 40:
            return "C"
        else:
            return "D"
    
    @staticmethod
    def _recommend_action(
        bant_total: float,
        engagement_score: float,
        red_flags: List[RedFlag],
        deal: DealData
    ) -> str:
        """Recommend primary action for this deal."""
        
        # Critical red flags
        if RedFlag.GHOSTING in red_flags:
            return "DEPRIORITIZE: Send breakup email, move to nurture campaign"
        
        if RedFlag.BAD_FIT in red_flags:
            return "DISQUALIFY: Company profile doesn't match ICP"
        
        if RedFlag.NO_BUDGET in red_flags and RedFlag.NO_AUTHORITY in red_flags:
            return "DISQUALIFY: Not a real opportunity, politely disengage"
        
        # High-quality opportunities
        if bant_total >= 75 and engagement_score >= 60:
            if deal.current_stage == DealStage.NEGOTIATION:
                return "CLOSE: Push for contract signature this week"
            elif deal.current_stage == DealStage.PILOT:
                return "ACCELERATE: Convert pilot to paid, schedule close meeting"
            else:
                return "ACCELERATE: High-quality opportunity, fast-track to pilot"
        
        # Medium-quality with low engagement
        if bant_total >= 50 and engagement_score < 40:
            return "NURTURE: Good fit but low engagement, schedule follow-up demo"
        
        # Low BANT score
        if bant_total < 50:
            missing = []
            if not deal.budget_discussed:
                missing.append("budget")
            if not deal.decision_maker_involved:
                missing.append("decision maker")
            if len(deal.pain_points_identified) == 0:
                missing.append("pain points")
            if not deal.timeline:
                missing.append("timeline")
            
            return f"QUALIFY: Need more info on: {', '.join(missing)}"
        
        # Default
        return "MONITOR: Continue engagement, reassess in 2 weeks"
    
    @staticmethod
    def _generate_next_steps(deal: DealData, red_flags: List[RedFlag]) -> List[str]:
        """Generate specific next steps for this deal."""
        steps = []
        
        # Address red flags first
        if RedFlag.NO_AUTHORITY in red_flags:
            steps.append("Ask: 'Who else should be involved in this decision?'")
        
        if RedFlag.NO_BUDGET in red_flags:
            steps.append("Discuss budget range and approval process")
        
        if RedFlag.NO_TIMELINE in red_flags:
            steps.append("Ask: 'What's driving your timeline for this decision?'")
        
        if RedFlag.GHOSTING in red_flags:
            steps.append("Send 'breakup email' to prompt response")
        
        # Stage-specific actions
        if deal.current_stage == DealStage.LEAD:
            steps.append("Schedule discovery call to understand needs")
        elif deal.current_stage == DealStage.QUALIFIED:
            steps.append("Schedule product demo with key stakeholders")
        elif deal.current_stage == DealStage.DEMO:
            steps.append("Propose 30-day pilot program")
        elif deal.current_stage == DealStage.PILOT:
            steps.append("Schedule pilot review and success metrics discussion")
        elif deal.current_stage == DealStage.NEGOTIATION:
            steps.append("Send contract for review, schedule legal call")
        
        # Engagement actions
        if not deal.demo_attended:
            steps.append("Schedule live product demonstration")
        
        if deal.demo_attended and not deal.trial_activated:
            steps.append("Offer sandbox/trial access")
        
        if len(deal.stakeholders_met) < 2:
            steps.append("Expand to additional stakeholders (multi-thread)")
        
        return steps[:5]  # Limit to 5 most important
    
    @staticmethod
    def _identify_risks(deal: DealData, red_flags: List[RedFlag]) -> List[str]:
        """Identify risks to closing this deal."""
        risks = []
        
        for flag in red_flags:
            risks.append(f"🚩 {flag.description}")
        
        if deal.has_internal_solution:
            risks.append("⚠️ Has existing internal solution (status quo bias)")
        
        if deal.competitor_mentions:
            competitors = ', '.join(deal.competitor_mentions)
            risks.append(f"⚠️ Evaluating competitors: {competitors}")
        
        if deal.regulatory_constraints:
            risks.append("⚠️ Regulatory constraints may slow procurement")
        
        if deal.objections_raised:
            risks.append(f"⚠️ Objections to address: {len(deal.objections_raised)}")
        
        if deal.company_size == 'enterprise' and deal.days_since_last_contact > 14:
            risks.append("⚠️ Enterprise deals stall without regular touchpoints")
        
        return risks


# Convenience function
def qualify_deal(deal_data: Dict) -> Dict:
    """
    Qualify a deal from dictionary input.
    
    Example:
        result = qualify_deal({
            'company_name': 'Acme Logistics',
            'company_size': 'enterprise',
            'budget_discussed': True,
            'budget_amount': 25000,
            'decision_maker_involved': True,
            'pain_points_identified': ['manual process', 'delay costs'],
            'timeline': '3 months',
            'demo_attended': True,
            'stakeholders_met': ['CFO', 'Operations Manager'],
            'days_since_last_contact': 3
        })
    """
    # Convert dict to DealData
    deal = DealData(
        company_name=deal_data.get('company_name', 'Unknown'),
        company_size=deal_data.get('company_size', 'mid_market'),
        industry=deal_data.get('industry', 'logistics'),
        annual_shipments=deal_data.get('annual_shipments'),
        budget_discussed=deal_data.get('budget_discussed', False),
        budget_amount=deal_data.get('budget_amount'),
        budget_confirmed=deal_data.get('budget_confirmed', False),
        decision_maker_involved=deal_data.get('decision_maker_involved', False),
        pain_points_identified=deal_data.get('pain_points_identified', []),
        timeline=deal_data.get('timeline', ''),
        demo_attended=deal_data.get('demo_attended', False),
        trial_activated=deal_data.get('trial_activated', False),
        multiple_demos=deal_data.get('multiple_demos', False),
        stakeholders_met=deal_data.get('stakeholders_met', []),
        email_responses=deal_data.get('email_responses', 0),
        days_since_last_contact=deal_data.get('days_since_last_contact', 0),
        inbound=deal_data.get('inbound', False),
        current_stage=DealStage(deal_data.get('current_stage', 'lead')),
        competitor_mentions=deal_data.get('competitor_mentions', []),
        objections_raised=deal_data.get('objections_raised', []),
        expects_free_forever=deal_data.get('expects_free_forever', False),
        wants_custom_development=deal_data.get('wants_custom_development', False),
        has_internal_solution=deal_data.get('has_internal_solution', False),
        regulatory_constraints=deal_data.get('regulatory_constraints', False)
    )
    
    score = DealQualifier.qualify_deal(deal)
    return score.to_dict()
