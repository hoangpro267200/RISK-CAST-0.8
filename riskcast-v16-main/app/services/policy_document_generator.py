"""
Policy document generator.

Generates PDF policy documents with all terms, conditions, and disclosures.
"""

from typing import Tuple
from datetime import datetime
import hashlib
import io
import logging

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("reportlab not available, PDF generation will use fallback")

from app.modules.underwriting.models import Policy

logger = logging.getLogger(__name__)


class PolicyDocumentGenerator:
    """Generates policy documents in PDF format."""
    
    def generate(self, policy: Policy) -> Tuple[bytes, str]:
        """
        Generate policy document.
        
        Args:
            policy: Policy model with all terms
            
        Returns:
            Tuple of (document_bytes, document_hash)
        """
        if not REPORTLAB_AVAILABLE:
            # Fallback to simple text document
            return self._generate_text_document(policy)
        
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Build document content
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#1a1a1a')
        )
        
        # Title
        story.append(Paragraph("CARGO INSURANCE POLICY", title_style))
        story.append(Spacer(1, 12))
        
        # Policy details table
        policy_data = [
            ["Policy Number:", policy.policy_number],
            ["Status:", policy.status.value if hasattr(policy.status, 'value') else str(policy.status)],
            ["Effective From:", policy.effective_from.strftime("%Y-%m-%d %H:%M UTC") if policy.effective_from else "N/A"],
            ["Effective To:", policy.effective_to.strftime("%Y-%m-%d %H:%M UTC") if policy.effective_to else "N/A"],
            ["Issued:", policy.bound_at.strftime("%Y-%m-%d %H:%M UTC") if policy.bound_at else "N/A"]
        ]
        
        policy_table = Table(policy_data, colWidths=[2*inch, 4*inch])
        policy_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(policy_table)
        story.append(Spacer(1, 20))
        
        # Policyholder
        story.append(Paragraph("POLICYHOLDER", heading_style))
        policyholder = policy.policyholder_json or {}
        holder_text = f"""
        <b>Company:</b> {policyholder.get('company_name', 'N/A')}<br/>
        <b>Contact:</b> {policyholder.get('contact_email', 'N/A')}<br/>
        <b>Address:</b> {policyholder.get('address', 'N/A')}
        """
        story.append(Paragraph(holder_text, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Coverage Details
        story.append(Paragraph("COVERAGE DETAILS", heading_style))
        terms = policy.terms_json or {}
        
        insured_value_cents = terms.get('insured_value_cents', 0)
        deductible_cents = terms.get('deductible_cents', 0)
        premium_cents = terms.get('premium_cents', 0)
        currency = terms.get('currency', 'USD')
        
        coverage_data = [
            ["Coverage Type:", terms.get('coverage_type', 'ALL_RISK')],
            ["Insured Value:", f"${insured_value_cents / 100:,.2f} {currency}"],
            ["Deductible:", f"${deductible_cents / 100:,.2f} {currency}"],
            ["Premium:", f"${premium_cents / 100:,.2f} {currency}"]
        ]
        
        coverage_table = Table(coverage_data, colWidths=[2*inch, 4*inch])
        coverage_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(coverage_table)
        story.append(Spacer(1, 12))
        
        # Extensions
        extensions = terms.get('extensions', [])
        if extensions:
            story.append(Paragraph("COVERAGE EXTENSIONS", heading_style))
            for ext in extensions:
                story.append(Paragraph(f"• {ext}", styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Exclusions
        exclusions = terms.get('exclusions', [])
        if exclusions:
            story.append(Paragraph("EXCLUSIONS", heading_style))
            for exc in exclusions:
                story.append(Paragraph(f"• {exc}", styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Limits
        limits = terms.get('limits', {})
        if limits:
            story.append(Paragraph("COVERAGE LIMITS", heading_style))
            limits_text = ""
            for key, value in limits.items():
                if isinstance(value, (int, float)):
                    limits_text += f"<b>{key.replace('_', ' ').title()}:</b> ${value / 100:,.2f} {currency}<br/>"
                else:
                    limits_text += f"<b>{key.replace('_', ' ').title()}:</b> {value}<br/>"
            story.append(Paragraph(limits_text, styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Conditions
        conditions = terms.get('conditions', [])
        if conditions:
            story.append(Paragraph("CONDITIONS", heading_style))
            for i, cond in enumerate(conditions, 1):
                story.append(Paragraph(f"{i}. {cond}", styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Risk Assessment Summary
        story.append(Paragraph("RISK ASSESSMENT SUMMARY", heading_style))
        risk = policy.risk_snapshot_json or {}
        
        risk_score = risk.get('overall_risk_score', 0)
        var_95 = risk.get('var_95', 0)
        expected_loss_cents = risk.get('expected_loss_cents', 0)
        
        risk_text = f"""
        <b>Overall Risk Score:</b> {risk_score:.2%}<br/>
        <b>Value at Risk (95%):</b> {var_95:.2%}<br/>
        <b>Expected Loss:</b> ${expected_loss_cents / 100:,.2f} {currency}
        """
        
        risk_factors = risk.get('risk_factors', {})
        if risk_factors:
            risk_text += "<br/><br/><b>Risk Factors:</b><br/>"
            for factor, value in risk_factors.items():
                risk_text += f"• {factor.replace('_', ' ').title()}: {value:.2%}<br/>"
        
        story.append(Paragraph(risk_text, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Model and Audit Information
        story.append(Paragraph("AUDIT INFORMATION", heading_style))
        audit_text = f"""
        <b>Model Version ID:</b> {policy.model_version_id}<br/>
        <b>Risk Run ID:</b> {policy.risk_run_id}<br/>
        <b>Quote ID:</b> {policy.quote_id or 'N/A'}<br/>
        <b>Evidence Bundle ID:</b> {policy.evidence_bundle_id or 'N/A'}<br/>
        <b>Policy Hash:</b> {policy.policy_hash[:16]}...{policy.policy_hash[-8:]}
        """
        story.append(Paragraph(audit_text, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Disclosures
        story.append(Paragraph("DISCLOSURES", heading_style))
        disclosure_text = """
        This policy was underwritten using automated risk assessment models. 
        The risk score and premium are based on the information provided at the 
        time of application. Any material misrepresentation may void coverage.
        <br/><br/>
        <b>Important:</b> This policy is subject to the terms and conditions 
        stated herein. Coverage is effective only during the period specified 
        and is subject to all exclusions and limitations.
        <br/><br/>
        <b>For claims:</b> Please contact claims@example.com<br/>
        <b>For questions:</b> Please contact support@example.com
        """
        story.append(Paragraph(disclosure_text, styles['Normal']))
        
        # Footer
        story.append(Spacer(1, 30))
        footer_text = f"""
        <i>Document generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}</i><br/>
        <i>Policy Hash: {policy.policy_hash}</i>
        """
        story.append(Paragraph(footer_text, styles['Normal']))
        
        try:
            # Build PDF
            doc.build(story)
            
            # Get bytes and compute hash
            pdf_bytes = buffer.getvalue()
            pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()
            
            logger.info(f"Generated policy document for {policy.policy_number} (hash: {pdf_hash[:16]}...)")
            
            return pdf_bytes, pdf_hash
        except Exception as e:
            logger.error(f"Error generating PDF document: {e}, falling back to text")
            return self._generate_text_document(policy)
    
    def _generate_text_document(self, policy: Policy) -> Tuple[bytes, str]:
        """
        Fallback text document generator when reportlab is not available.
        
        Args:
            policy: Policy model
            
        Returns:
            Tuple of (document_bytes, document_hash)
        """
        terms = policy.terms_json or {}
        policyholder = policy.policyholder_json or {}
        risk = policy.risk_snapshot_json or {}
        
        document_text = f"""
CARGO INSURANCE POLICY
======================

Policy Number: {policy.policy_number}
Status: {policy.status.value if hasattr(policy.status, 'value') else str(policy.status)}
Effective From: {policy.effective_from.strftime("%Y-%m-%d %H:%M UTC") if policy.effective_from else "N/A"}
Effective To: {policy.effective_to.strftime("%Y-%m-%d %H:%M UTC") if policy.effective_to else "N/A"}
Issued: {policy.bound_at.strftime("%Y-%m-%d %H:%M UTC") if policy.bound_at else "N/A"}

POLICYHOLDER
------------
Company: {policyholder.get('company_name', 'N/A')}
Contact: {policyholder.get('contact_email', 'N/A')}
Address: {policyholder.get('address', 'N/A')}

COVERAGE DETAILS
----------------
Coverage Type: {terms.get('coverage_type', 'ALL_RISK')}
Insured Value: ${terms.get('insured_value_cents', 0) / 100:,.2f} {terms.get('currency', 'USD')}
Deductible: ${terms.get('deductible_cents', 0) / 100:,.2f} {terms.get('currency', 'USD')}
Premium: ${terms.get('premium_cents', 0) / 100:,.2f} {terms.get('currency', 'USD')}

COVERAGE EXTENSIONS
-------------------
{chr(10).join(f"• {ext}" for ext in terms.get('extensions', []))}

EXCLUSIONS
----------
{chr(10).join(f"• {exc}" for exc in terms.get('exclusions', []))}

CONDITIONS
----------
{chr(10).join(f"{i}. {cond}" for i, cond in enumerate(terms.get('conditions', []), 1))}

RISK ASSESSMENT SUMMARY
------------------------
Overall Risk Score: {risk.get('overall_risk_score', 0):.2%}
Value at Risk (95%): {risk.get('var_95', 0):.2%}
Expected Loss: ${risk.get('expected_loss_cents', 0) / 100:,.2f} {terms.get('currency', 'USD')}

AUDIT INFORMATION
------------------
Model Version ID: {policy.model_version_id}
Risk Run ID: {policy.risk_run_id}
Quote ID: {policy.quote_id or 'N/A'}
Evidence Bundle ID: {policy.evidence_bundle_id or 'N/A'}
Policy Hash: {policy.policy_hash}

DISCLOSURES
-----------
This policy was underwritten using automated risk assessment models.
The risk score and premium are based on the information provided at the
time of application. Any material misrepresentation may void coverage.

For claims: claims@example.com
For questions: support@example.com

Document generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
"""
        
        document_bytes = document_text.encode('utf-8')
        document_hash = hashlib.sha256(document_bytes).hexdigest()
        
        logger.warning(f"Generated text document (reportlab not available) for {policy.policy_number}")
        
        return document_bytes, document_hash
    
    def generate_certificate(self, policy: Policy) -> Tuple[bytes, str]:
        """
        Generate a shorter certificate of insurance.
        
        Args:
            policy: Policy model
            
        Returns:
            Tuple of (document_bytes, document_hash)
        """
        if not REPORTLAB_AVAILABLE:
            return self._generate_text_certificate(policy)
        
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1
        )
        
        # Title
        story.append(Paragraph("CERTIFICATE OF INSURANCE", title_style))
        story.append(Spacer(1, 12))
        
        # Policy details
        terms = policy.terms_json or {}
        policyholder = policy.policyholder_json or {}
        
        cert_data = [
            ["Policy Number:", policy.policy_number],
            ["Insured:", policyholder.get('company_name', 'N/A')],
            ["Coverage Type:", terms.get('coverage_type', 'ALL_RISK')],
            ["Insured Value:", f"${terms.get('insured_value_cents', 0) / 100:,.2f} {terms.get('currency', 'USD')}"],
            ["Effective From:", policy.effective_from.strftime("%Y-%m-%d") if policy.effective_from else "N/A"],
            ["Effective To:", policy.effective_to.strftime("%Y-%m-%d") if policy.effective_to else "N/A"]
        ]
        
        cert_table = Table(cert_data, colWidths=[2*inch, 4*inch])
        cert_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(cert_table)
        
        # Footer
        story.append(Spacer(1, 20))
        footer_text = f"""
        <i>This is a certificate of insurance only. Full terms and conditions 
        are contained in the policy document.</i><br/>
        <i>Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}</i>
        """
        story.append(Paragraph(footer_text, styles['Normal']))
        
        try:
            doc.build(story)
            
            pdf_bytes = buffer.getvalue()
            pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()
            
            return pdf_bytes, pdf_hash
        except Exception as e:
            logger.error(f"Error generating certificate PDF: {e}, falling back to text")
            return self._generate_text_certificate(policy)
    
    def _generate_text_certificate(self, policy: Policy) -> Tuple[bytes, str]:
        """Fallback text certificate generator."""
        terms = policy.terms_json or {}
        policyholder = policy.policyholder_json or {}
        
        cert_text = f"""
CERTIFICATE OF INSURANCE
========================

Policy Number: {policy.policy_number}
Insured: {policyholder.get('company_name', 'N/A')}
Coverage Type: {terms.get('coverage_type', 'ALL_RISK')}
Insured Value: ${terms.get('insured_value_cents', 0) / 100:,.2f} {terms.get('currency', 'USD')}
Effective From: {policy.effective_from.strftime("%Y-%m-%d") if policy.effective_from else "N/A"}
Effective To: {policy.effective_to.strftime("%Y-%m-%d") if policy.effective_to else "N/A"}

This is a certificate of insurance only. Full terms and conditions
are contained in the policy document.

Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
"""
        
        cert_bytes = cert_text.encode('utf-8')
        cert_hash = hashlib.sha256(cert_bytes).hexdigest()
        
        return cert_bytes, cert_hash
    
    def generate_endorsement(
        self,
        policy: Policy,
        endorsement_type: str,
        changes: dict
    ) -> Tuple[bytes, str]:
        """
        Generate an endorsement document for policy changes.
        
        Args:
            policy: Policy model
            endorsement_type: Type of endorsement
            changes: Dictionary of changes
            
        Returns:
            Tuple of (document_bytes, document_hash)
        """
        if not REPORTLAB_AVAILABLE:
            return self._generate_text_endorsement(policy, endorsement_type, changes)
        
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10
        )
        
        # Title
        story.append(Paragraph(f"POLICY ENDORSEMENT - {endorsement_type}", title_style))
        story.append(Spacer(1, 12))
        
        # Policy reference
        story.append(Paragraph("POLICY REFERENCE", heading_style))
        ref_data = [
            ["Policy Number:", policy.policy_number],
            ["Endorsement Type:", endorsement_type],
            ["Date:", datetime.utcnow().strftime("%Y-%m-%d")]
        ]
        
        ref_table = Table(ref_data, colWidths=[2*inch, 4*inch])
        ref_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(ref_table)
        story.append(Spacer(1, 12))
        
        # Changes
        story.append(Paragraph("CHANGES", heading_style))
        changes_text = ""
        for key, value in changes.items():
            changes_text += f"<b>{key.replace('_', ' ').title()}:</b> {value}<br/>"
        story.append(Paragraph(changes_text, styles['Normal']))
        
        # Footer
        story.append(Spacer(1, 20))
        footer_text = f"""
        <i>This endorsement forms part of Policy {policy.policy_number}</i><br/>
        <i>Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}</i>
        """
        story.append(Paragraph(footer_text, styles['Normal']))
        
        try:
            doc.build(story)
            
            pdf_bytes = buffer.getvalue()
            pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()
            
            return pdf_bytes, pdf_hash
        except Exception as e:
            logger.error(f"Error generating certificate PDF: {e}, falling back to text")
            return self._generate_text_certificate(policy)
    
    def _generate_text_endorsement(
        self,
        policy: Policy,
        endorsement_type: str,
        changes: dict
    ) -> Tuple[bytes, str]:
        """Fallback text endorsement generator."""
        endorsement_text = f"""
POLICY ENDORSEMENT - {endorsement_type}
=======================================

Policy Number: {policy.policy_number}
Endorsement Type: {endorsement_type}
Date: {datetime.utcnow().strftime("%Y-%m-%d")}

CHANGES
-------
{chr(10).join(f"{key.replace('_', ' ').title()}: {value}" for key, value in changes.items())}

This endorsement forms part of Policy {policy.policy_number}

Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
"""
        
        endorsement_bytes = endorsement_text.encode('utf-8')
        endorsement_hash = hashlib.sha256(endorsement_bytes).hexdigest()
        
        return endorsement_bytes, endorsement_hash
