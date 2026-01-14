"""
RISKCAST Case Study Generator
==============================
Generate realistic case studies for sales and marketing.

Supports:
- Multiple industry templates (forwarder, manufacturer, insurance)
- Synthetic or real (anonymized) data
- Customizable metrics and testimonials

Author: RISKCAST Team
Version: 2.0
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import random
import hashlib
import logging

logger = logging.getLogger(__name__)


@dataclass
class CaseStudyResult:
    """Generated case study result."""
    title: str
    company_profile: Dict
    executive_summary: str
    challenges: List[str]
    solution: str
    results: Dict
    quote: Dict
    timeline: str
    metadata: Dict
    
    def to_dict(self) -> Dict:
        return {
            'title': self.title,
            'company_profile': self.company_profile,
            'executive_summary': self.executive_summary,
            'challenges': self.challenges,
            'solution': self.solution,
            'results': self.results,
            'quote': self.quote,
            'timeline': self.timeline,
            'metadata': self.metadata
        }


class CaseStudyGenerator:
    """
    Generate realistic case studies for sales/marketing.
    Can use synthetic data or real anonymized data.
    """
    
    TEMPLATES = {
        'forwarder': {
            'title_template': "{company_name} Reduces Delay-Related Costs by {delay_reduction}% with RISKCAST",
            'summary_template': """
{company_name}, a {company_size} freight forwarder handling {annual_shipments:,} 
shipments annually across {primary_routes}, implemented RISKCAST to improve risk 
assessment accuracy and reduce costly delays. Within {timeframe}, they achieved 
remarkable results in operational efficiency and cost savings.

Key achievements:
• {delay_reduction}% reduction in shipment delays
• ${cost_savings:,} in annual cost savings  
• {time_savings}% faster risk assessment process
• {customer_satisfaction}% improvement in customer satisfaction scores
""",
            'challenges': [
                "Manual risk assessment process taking 4-6 hours per high-value shipment",
                "15-20% of shipments experiencing delays, impacting customer relationships",
                "High insurance premiums due to historical claim patterns",
                "Difficulty pricing risk accurately for complex multi-modal shipments",
                "Inconsistent assessment quality across different team members",
                "Limited visibility into route-specific risk factors"
            ],
            'solution_template': """
RISKCAST was integrated with their existing TMS platform (SAP TM), providing:

**Automated Risk Scoring**
• Instant risk assessment in under 30 seconds (vs. 4+ hours manual)
• Consistent, data-driven scoring across all team members
• Multi-modal risk analysis covering ocean, air, and ground segments

**Proactive Risk Management**
• Real-time route optimization recommendations
• Weather and congestion impact predictions
• Carrier reliability scoring based on historical data

**Insurance Optimization**
• Risk-based premium calculation
• Documentation for underwriter negotiations
• Claims reduction through proactive mitigation

**Executive Visibility**
• CFO dashboard for cargo risk exposure
• Portfolio-level risk monitoring
• ROI tracking and reporting
""",
            'results_ranges': {
                'delay_reduction': (25, 40),
                'cost_savings': (250000, 800000),
                'time_savings': (80, 95),
                'customer_satisfaction': (15, 30),
                'roi_percentage': (300, 900),
                'payback_months': (3, 8)
            },
            'company_names': [
                'Global Logistics Solutions', 'Pacific Freight Partners', 
                'TransOcean Forwarding', 'Alliance Cargo Services',
                'Continental Freight Group', 'Maritime Express Logistics'
            ],
            'routes': [
                'Asia-Pacific to North America', 'Europe to Asia', 
                'Trans-Atlantic', 'Intra-Asia', 'Latin America routes'
            ],
            'roles': ['VP of Operations', 'Chief Operating Officer', 'Director of Logistics', 'Head of Risk Management'],
            'quotes': [
                "RISKCAST transformed our risk assessment process. What used to take hours now takes seconds, and our accuracy has never been better.",
                "The ROI was immediate. We're catching high-risk shipments before they become problems, saving hundreds of thousands in potential losses.",
                "Our customers noticed the difference immediately. Fewer delays, better communication, and proactive problem-solving.",
                "RISKCAST paid for itself in the first quarter. The insurance savings alone justified the investment."
            ]
        },
        
        'manufacturer': {
            'title_template': "{company_name} Protects ${cargo_value_annual:,}+ in Annual Cargo Value with RISKCAST",
            'summary_template': """
{company_name}, a global {industry} manufacturer, ships high-value equipment 
and components worth over ${cargo_value_annual:,} annually across {trade_lanes} 
trade lanes. After implementing RISKCAST, they achieved significant improvements 
in supply chain resilience and cost management.

Key achievements:
• {loss_reduction}% reduction in cargo loss incidents
• ${insurance_savings:,} in annual insurance premium savings
• {claims_reduction}% reduction in insurance claims
• {visibility_improvement}% improvement in supply chain visibility
""",
            'challenges': [
                "High-value cargo requiring specialized risk assessment expertise",
                "Multiple transport modes (ocean, air, rail) with varying risk profiles",
                "Complex international routes with geopolitical and regulatory risks",
                "Difficulty justifying insurance costs to finance leadership",
                "Limited real-time visibility into in-transit cargo risks",
                "Reactive rather than proactive approach to supply chain disruptions"
            ],
            'solution_template': """
RISKCAST was deployed across their global supply chain operations:

**Multi-Modal Risk Intelligence**
• Unified risk scoring across ocean, air, rail, and ground transport
• Route-specific risk factors including geopolitical and regulatory risks
• Carrier performance analytics and reliability scoring

**Proactive Loss Prevention**
• Weather and climate risk forecasting
• Port congestion and delay predictions
• Automated alerts for high-risk conditions

**Financial Optimization**
• Data-driven insurance premium negotiations
• Risk-adjusted routing recommendations
• Cost-benefit analysis for risk mitigation options

**Executive Reporting**
• CFO-ready dashboards for cargo risk exposure
• Board-level risk reporting capabilities
• Audit-ready documentation and traceability
""",
            'results_ranges': {
                'loss_reduction': (30, 50),
                'insurance_savings': (150000, 400000),
                'claims_reduction': (40, 60),
                'visibility_improvement': (50, 75),
                'executive_time_saved': (70, 85),
                'cargo_value_annual': (50000000, 200000000)
            },
            'company_names': [
                'Advanced Manufacturing Corp', 'Precision Equipment Industries', 
                'Global Tech Manufacturing', 'Industrial Solutions Group',
                'TechParts International', 'Component Systems Inc'
            ],
            'industries': [
                'semiconductor', 'medical device', 'automotive', 
                'electronics', 'industrial equipment', 'aerospace'
            ],
            'roles': ['Chief Financial Officer', 'VP of Supply Chain', 'Director of Global Logistics', 'Chief Procurement Officer'],
            'quotes': [
                "RISKCAST gives our CFO the visibility she needs into cargo risk. It's become an essential part of our supply chain strategy.",
                "We've dramatically reduced our insurance costs while actually improving our risk management. RISKCAST paid for itself in the first quarter.",
                "The proactive alerts have saved us multiple times. We're catching problems before they impact production schedules.",
                "Our board now has confidence in our supply chain resilience. RISKCAST data is part of every quarterly risk review."
            ]
        },
        
        'insurance': {
            'title_template': "{company_name} Insurance Improves Underwriting Accuracy by {accuracy_improvement}%",
            'summary_template': """
{company_name}, a {company_type} specializing in marine cargo insurance, integrated 
RISKCAST into their underwriting workflow. The results transformed their competitive 
position in the market.

Key achievements:
• {accuracy_improvement}% improvement in risk pricing accuracy
• {underwriting_time_reduction}% reduction in underwriting time
• {combined_ratio_improvement} point improvement in combined ratio
• {portfolio_optimization}% improvement in portfolio risk distribution
""",
            'challenges': [
                "Manual underwriting process taking 2-3 days per complex policy",
                "Inconsistent risk assessment across different underwriters",
                "High loss ratio on certain trade lanes and cargo types",
                "Difficulty competing on pricing versus larger insurers",
                "Limited visibility into policyholder risk behaviors",
                "Reactive claims management rather than proactive risk prevention"
            ],
            'solution_template': """
RISKCAST was integrated into the underwriting and policy management workflow:

**Automated Underwriting Support**
• Instant preliminary risk scoring for quote requests
• Standardized underwriting criteria across all underwriters
• Historical loss data integration for pricing accuracy

**Portfolio Risk Management**
• Real-time portfolio risk monitoring and concentration alerts
• Trade lane and cargo type risk analysis
• Reinsurance optimization recommendations

**Policyholder Services**
• Risk alerts and recommendations for policyholders
• Claims prevention through proactive risk management
• Premium discount programs for risk-reducing behaviors

**Regulatory Compliance**
• Audit-ready risk assessment documentation
• Solvency II compliant risk modeling
• Complete calculation traceability
""",
            'results_ranges': {
                'accuracy_improvement': (35, 55),
                'underwriting_time_reduction': (60, 80),
                'combined_ratio_improvement': (3, 8),
                'portfolio_optimization': (20, 35),
                'claims_reduction': (15, 30),
                'premium_volume_increase': (10, 25)
            },
            'company_names': [
                'Marine Risk Underwriters', 'Cargo Insurance Partners', 
                'International Marine Insurance', 'Pacific Cargo Mutual',
                'TransOcean Insurance Group', 'Continental Cargo Insurance'
            ],
            'company_types': [
                'regional marine cargo insurer', 'specialty cargo underwriter',
                'global marine insurance provider', 'mutual insurance company'
            ],
            'roles': ['Chief Underwriting Officer', 'VP of Marine Insurance', 'Head of Risk Assessment', 'Director of Actuarial Services'],
            'quotes': [
                "RISKCAST has standardized our underwriting process and improved our loss ratio. It's become a competitive advantage.",
                "Our underwriters can now handle 3x more policies with better accuracy. The efficiency gains alone justify the investment.",
                "The portfolio risk visibility has transformed how we manage concentration risk. We're making smarter reinsurance decisions.",
                "RISKCAST data has become central to our actuarial analysis. The accuracy improvements are measurable and significant."
            ]
        }
    }
    
    @staticmethod
    def generate_case_study(
        template_type: str,
        company_data: Dict = None,
        anonymize: bool = True,
        seed: int = None
    ) -> CaseStudyResult:
        """
        Generate a case study from template.
        
        Args:
            template_type: Type of template ('forwarder', 'manufacturer', 'insurance')
            company_data: Optional real company data (anonymized if flag set)
            anonymize: Whether to anonymize company name
            seed: Random seed for reproducible generation
            
        Returns:
            CaseStudyResult with complete case study
        """
        if seed is not None:
            random.seed(seed)
        
        template = CaseStudyGenerator.TEMPLATES.get(template_type)
        
        if not template:
            raise ValueError(f"Unknown template type: {template_type}. Available: {list(CaseStudyGenerator.TEMPLATES.keys())}")
        
        # Generate or use company data
        if company_data:
            # Start with synthetic data, then overlay custom data
            data = CaseStudyGenerator._generate_synthetic_company(template_type, template)
            data.update(company_data)
            if anonymize and 'company_name' in company_data:
                data['company_name'] = CaseStudyGenerator._anonymize_name(company_data['company_name'])
        else:
            data = CaseStudyGenerator._generate_synthetic_company(template_type, template)
        
        # Generate results within template ranges
        results = {}
        for metric, (min_val, max_val) in template['results_ranges'].items():
            if isinstance(min_val, int) and isinstance(max_val, int):
                results[metric] = random.randint(min_val, max_val)
            else:
                results[metric] = round(random.uniform(min_val, max_val), 1)
        
        # Merge data and results for formatting
        format_data = {**data, **results}
        
        # Generate case study components
        title = template['title_template'].format(**format_data)
        summary = template['summary_template'].format(**format_data).strip()
        solution = template['solution_template'].strip()
        
        # Select subset of challenges (3-4)
        challenges = random.sample(template['challenges'], min(4, len(template['challenges'])))
        
        # Generate quote
        quote = CaseStudyGenerator._generate_quote(data, results, template)
        
        # Generate timeline
        timelines = ['6 months', '9 months', '12 months', '18 months']
        timeline = data.get('timeframe', random.choice(timelines))
        
        # Metadata
        metadata = {
            'template_type': template_type,
            'generated_date': datetime.utcnow().isoformat(),
            'anonymized': anonymize,
            'case_study_id': CaseStudyGenerator._generate_case_study_id(data, template_type)
        }
        
        return CaseStudyResult(
            title=title,
            company_profile={
                'name': data['company_name'],
                'industry': data.get('industry', template_type),
                'size': data.get('company_size', 'mid-market'),
                'geography': data.get('geography', 'Global'),
                'annual_shipments': data.get('annual_shipments', 'N/A')
            },
            executive_summary=summary,
            challenges=challenges,
            solution=solution,
            results=results,
            quote=quote,
            timeline=timeline,
            metadata=metadata
        )
    
    @staticmethod
    def _generate_synthetic_company(template_type: str, template: Dict) -> Dict:
        """Generate realistic synthetic company data."""
        sizes = ['mid-market', 'enterprise', 'large enterprise']
        geographies = ['North America', 'Europe', 'Asia-Pacific', 'Global']
        
        data = {
            'company_name': random.choice(template.get('company_names', ['Anonymous Company'])),
            'company_size': random.choice(sizes),
            'geography': random.choice(geographies),
            'annual_shipments': random.randint(1000, 10000),
            'timeframe': random.choice(['6 months', '9 months', '12 months']),
        }
        
        # Template-specific fields
        if template_type == 'forwarder':
            data['primary_routes'] = random.choice(template.get('routes', ['Global']))
        elif template_type == 'manufacturer':
            data['industry'] = random.choice(template.get('industries', ['manufacturing']))
            data['cargo_value_annual'] = random.randint(50000000, 200000000)
            data['trade_lanes'] = random.randint(5, 15)
        elif template_type == 'insurance':
            data['company_type'] = random.choice(template.get('company_types', ['marine cargo insurer']))
        
        return data
    
    @staticmethod
    def _anonymize_name(name: str) -> str:
        """Anonymize company name while maintaining recognizability."""
        words = name.split()
        if len(words) > 1:
            return f"[{words[0][0]}*** {words[-1]}]"
        return f"[{name[0]}*** Company]"
    
    @staticmethod
    def _generate_quote(data: Dict, results: Dict, template: Dict) -> Dict:
        """Generate realistic testimonial quote."""
        quotes = template.get('quotes', ["RISKCAST delivered exceptional ROI."])
        roles = template.get('roles', ['Executive'])
        
        return {
            'text': random.choice(quotes),
            'author': "[Name Withheld]",
            'title': random.choice(roles),
            'company': data['company_name']
        }
    
    @staticmethod
    def _generate_case_study_id(data: Dict, template_type: str) -> str:
        """Generate unique case study identifier."""
        import uuid
        unique_id = uuid.uuid4().hex[:8]
        content = f"{data.get('company_name', 'anon')}_{template_type}_{unique_id}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    @staticmethod
    def list_templates() -> List[Dict]:
        """List available case study templates."""
        return [
            {
                'type': 'forwarder',
                'description': 'Freight forwarder focused on delay reduction and operational efficiency',
                'key_metrics': ['delay_reduction', 'cost_savings', 'time_savings', 'customer_satisfaction']
            },
            {
                'type': 'manufacturer',
                'description': 'Manufacturer focused on cargo protection and insurance optimization',
                'key_metrics': ['loss_reduction', 'insurance_savings', 'claims_reduction', 'visibility_improvement']
            },
            {
                'type': 'insurance',
                'description': 'Insurance underwriter focused on pricing accuracy and portfolio management',
                'key_metrics': ['accuracy_improvement', 'underwriting_time_reduction', 'combined_ratio_improvement']
            }
        ]
    
    @staticmethod
    def generate_multiple(
        template_type: str,
        count: int = 3,
        anonymize: bool = True
    ) -> List[CaseStudyResult]:
        """Generate multiple case studies of the same type."""
        case_studies = []
        
        for i in range(count):
            cs = CaseStudyGenerator.generate_case_study(
                template_type=template_type,
                anonymize=anonymize,
                seed=None  # Different each time
            )
            case_studies.append(cs)
        
        return case_studies


# Convenience functions
def generate_case_study(
    template_type: str,
    company_data: Dict = None,
    anonymize: bool = True
) -> Dict:
    """Generate a case study and return as dictionary."""
    result = CaseStudyGenerator.generate_case_study(
        template_type=template_type,
        company_data=company_data,
        anonymize=anonymize
    )
    return result.to_dict()


def list_templates() -> List[Dict]:
    """List available templates."""
    return CaseStudyGenerator.list_templates()
