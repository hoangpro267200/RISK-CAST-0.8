"""
RISKCAST Report - PDF Builder
Enterprise-grade PDF report generator with comprehensive risk analysis
"""

from io import BytesIO
from typing import Dict, List, Optional, Any
from datetime import datetime
from reportlab.lib.pagesizes import letter  # type: ignore
from reportlab.lib.units import inch  # type: ignore
from reportlab.lib import colors  # type: ignore
from reportlab.platypus import (  # type: ignore
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    Image as RLImage, KeepTogether, PageBreakIfNeeded
)
from reportlab.lib.styles import getSampleStyleSheet  # type: ignore
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY  # type: ignore

from .pdf_layouts import PDFLayouts
from .image_exporter import ImageExporter


class PDFReportBuilder:
    """Enterprise PDF report builder"""
    
    def __init__(self):
        """Initialize PDF builder"""
        self.layouts = PDFLayouts()
        self.image_exporter = ImageExporter()
        self.styles = self.layouts.styles
        self.margins = self.layouts.get_margins()
    
    def generate_report(self, data: Dict[str, Any]) -> BytesIO:
        """
        Generate complete PDF report
        
        Args:
            data: Report data dictionary containing:
                - risk_score, risk_level, confidence
                - profile, matrix, factors, drivers
                - recommendations, timeline, network
                - scenario_comparisons
                - charts (base64 strings)
                
        Returns:
            BytesIO buffer containing PDF
        """
        buffer = BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=self.margins['right'],
            leftMargin=self.margins['left'],
            topMargin=self.margins['top'],
            bottomMargin=self.margins['bottom']
        )
        
        # Build story (content)
        story = []
        
        # 1. Cover Page
        story.extend(self._build_cover_page(data))
        story.append(PageBreak())
        
        # 2. Executive Summary
        story.extend(self._build_executive_summary(data))
        story.append(PageBreak())
        
        # 3. Risk Matrix
        story.extend(self._build_risk_matrix(data))
        story.append(PageBreak())
        
        # 4. Radar Chart
        story.extend(self._build_radar_chart(data))
        
        # 5. Key Drivers
        story.extend(self._build_key_drivers(data))
        story.append(PageBreak())
        
        # 6. Risk Timeline
        story.extend(self._build_risk_timeline(data))
        
        # 7. Network Risk Map
        story.extend(self._build_network_map(data))
        story.append(PageBreak())
        
        # 8. Scenario Simulations
        if data.get('scenario_comparisons'):
            story.extend(self._build_scenario_section(data))
            story.append(PageBreak())
        
        # 9. Recommendations
        story.extend(self._build_recommendations(data))
        story.append(PageBreak())
        
        # 10. Appendix
        story.extend(self._build_appendix(data))
        
        # Build PDF
        doc.build(story, onFirstPage=self._add_footer, onLaterPages=self._add_footer)
        
        buffer.seek(0)
        return buffer
    
    def _build_cover_page(self, data: Dict[str, Any]) -> List:
        """Build cover page"""
        story = []
        
        # Title
        title = Paragraph(
            "RISKCAST ANALYSIS REPORT",
            self.styles['CoverTitle']
        )
        story.append(Spacer(1, 2*inch))
        story.append(title)
        
        # Subtitle
        route = data.get('route', 'Unknown Route')
        subtitle = Paragraph(
            f"Risk Assessment for {route}",
            self.styles['CoverSubtitle']
        )
        story.append(subtitle)
        story.append(Spacer(1, 1.5*inch))
        
        # Risk Score (large)
        risk_score = data.get('risk_score', 0)
        score_color = self.layouts.get_risk_color(risk_score)
        score_style = self.styles['RiskScore']
        score_style.textColor = score_color
        
        score_text = Paragraph(
            f"{risk_score:.1f}",
            score_style
        )
        story.append(score_text)
        
        # Risk Level
        risk_level = data.get('risk_level', 'Unknown')
        level_text = Paragraph(
            f"Risk Level: <b>{risk_level}</b>",
            self.styles['CoverSubtitle']
        )
        story.append(Spacer(1, 0.5*inch))
        story.append(level_text)
        
        # Date
        date_str = datetime.now().strftime("%B %d, %Y")
        date_text = Paragraph(
            f"Generated: {date_str}",
            self.styles['Footer']
        )
        story.append(Spacer(1, 2*inch))
        story.append(date_text)
        
        # Branding
        branding = Paragraph(
            "RISKCAST Enterprise AI - Powered by Advanced Risk Analytics",
            self.styles['Footer']
        )
        story.append(branding)
        
        return story
    
    def _build_executive_summary(self, data: Dict[str, Any]) -> List:
        """Build executive summary section"""
        story = []
        
        # Section header
        header = Paragraph(
            "Executive Summary",
            self.styles['SectionHeader']
        )
        story.append(header)
        story.append(Spacer(1, 0.3*inch))
        
        # Risk metrics table
        risk_score = data.get('risk_score', 0)
        risk_level = data.get('risk_level', 'Unknown')
        confidence = data.get('confidence', 0) * 100
        
        metrics_data = [
            ['Metric', 'Value'],
            ['Overall Risk Score', f"{risk_score:.1f} / 100"],
            ['Risk Level', risk_level],
            ['Confidence Score', f"{confidence:.1f}%"],
        ]
        
        metrics_table = Table(metrics_data, colWidths=[3*inch, 3*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#111827')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#00FFC8')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F7FA')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FAFAFA')]),
        ]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 0.4*inch))
        
        # AI Explanation
        explanation = data.get('profile', {}).get('explanation', [])
        if isinstance(explanation, list):
            explanation_text = ' '.join(explanation)
        else:
            explanation_text = str(explanation)
        
        if explanation_text:
            explanation_para = Paragraph(
                f"<b>Risk Assessment Overview:</b><br/>{explanation_text}",
                self.styles['BodyText']
            )
            story.append(explanation_para)
            story.append(Spacer(1, 0.3*inch))
        
        # Key insights
        insights = data.get('drivers', [])
        if insights:
            insights_title = Paragraph(
                "<b>Key Risk Drivers:</b>",
                self.styles['SubsectionHeader']
            )
            story.append(insights_title)
            
            for driver in insights[:5]:  # Top 5
                driver_text = Paragraph(
                    f"• {driver}",
                    self.styles['BodyText']
                )
                story.append(driver_text)
            
            story.append(Spacer(1, 0.2*inch))
        
        return story
    
    def _build_risk_matrix(self, data: Dict[str, Any]) -> List:
        """Build risk matrix section"""
        story = []
        
        header = Paragraph(
            "Risk Impact Matrix",
            self.styles['SectionHeader']
        )
        story.append(header)
        story.append(Spacer(1, 0.3*inch))
        
        # Matrix data
        matrix = data.get('matrix', {})
        probability = matrix.get('probability', 'medium')
        severity = matrix.get('severity', 'medium')
        quadrant = matrix.get('quadrant', 5)
        description = matrix.get('description', 'Medium risk')
        
        # Create 3x3 matrix visualization
        matrix_labels = [
            ['', 'Low Probability', 'Medium Probability', 'High Probability'],
            ['High Severity', '', '', ''],
            ['Medium Severity', '', '', ''],
            ['Low Severity', '', '', '']
        ]
        
        # Determine cell colors and highlight
        colors_map = {
            1: colors.HexColor('#E8F5E9'),  # Low-Low (Green)
            2: colors.HexColor('#FFF9C4'),  # Low-Medium (Yellow)
            3: colors.HexColor('#FFCC80'),  # Low-High (Orange)
            4: colors.HexColor('#FFF9C4'),  # Medium-Low
            5: colors.HexColor('#FFCC80'),  # Medium-Medium
            6: colors.HexColor('#FFAB91'),  # Medium-High
            7: colors.HexColor('#FFCC80'),  # High-Low
            8: colors.HexColor('#FFAB91'),  # High-Medium
            9: colors.HexColor('#EF5350'),  # High-High (Red)
        }
        
        # Fill matrix
        for row_idx in range(1, 4):
            for col_idx in range(1, 4):
                cell_quadrant = (row_idx - 1) * 3 + col_idx
                if cell_quadrant == quadrant:
                    matrix_labels[row_idx][col_idx] = f"★ {quadrant}"
                else:
                    matrix_labels[row_idx][col_idx] = f"{cell_quadrant}"
        
        matrix_table = Table(matrix_labels, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        
        # Style matrix
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#111827')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])
        
        # Highlight current quadrant
        row_idx = ((quadrant - 1) // 3) + 1
        col_idx = ((quadrant - 1) % 3) + 1
        style.add('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx), colors.HexColor('#00FFC8'))
        
        matrix_table.setStyle(style)
        story.append(matrix_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Matrix description
        desc_text = Paragraph(
            f"<b>Matrix Position:</b> Quadrant {quadrant}<br/>"
            f"<b>Probability:</b> {probability.capitalize()}<br/>"
            f"<b>Severity:</b> {severity.capitalize()}<br/>"
            f"<b>Interpretation:</b> {description}",
            self.styles['BodyText']
        )
        story.append(desc_text)
        
        return story
    
    def _build_radar_chart(self, data: Dict[str, Any]) -> List:
        """Build radar chart section"""
        story = []
        
        header = Paragraph(
            "Risk Factor Profile",
            self.styles['SectionHeader']
        )
        story.append(header)
        story.append(Spacer(1, 0.3*inch))
        
        # Add radar chart image if available
        charts = data.get('charts', {})
        radar_base64 = charts.get('radar')
        
        if radar_base64:
            try:
                chart_bytes = self.image_exporter.process_chart_image(radar_base64, max_width=600, max_height=400)
                if chart_bytes:
                    img_buffer = BytesIO(chart_bytes)
                    chart_img = RLImage(img_buffer, width=6*inch, height=4*inch)
                    story.append(chart_img)
                    story.append(Spacer(1, 0.2*inch))
                    
                    caption = Paragraph(
                        "Risk factors visualization showing relative contribution of each factor",
                        self.styles['Caption']
                    )
                    story.append(caption)
            except Exception as e:
                print(f"[PDF Builder] Error adding radar chart: {e}")
        
        return story
    
    def _build_key_drivers(self, data: Dict[str, Any]) -> List:
        """Build key drivers section"""
        story = []
        
        header = Paragraph(
            "Key Risk Drivers",
            self.styles['SectionHeader']
        )
        story.append(header)
        story.append(Spacer(1, 0.3*inch))
        
        # Drivers bar chart
        charts = data.get('charts', {})
        drivers_base64 = charts.get('drivers_bar')
        
        if drivers_base64:
            try:
                chart_bytes = self.image_exporter.process_chart_image(drivers_base64, max_width=600, max_height=300)
                if chart_bytes:
                    img_buffer = BytesIO(chart_bytes)
                    chart_img = RLImage(img_buffer, width=6*inch, height=3*inch)
                    story.append(chart_img)
                    story.append(Spacer(1, 0.3*inch))
            except Exception as e:
                print(f"[PDF Builder] Error adding drivers chart: {e}")
        
        # Drivers table
        factors = data.get('factors', {})
        if factors:
            drivers_data = [['Risk Factor', 'Score', 'Impact']]
            
            # Sort by score
            sorted_factors = sorted(factors.items(), key=lambda x: x[1], reverse=True)
            
            for factor_name, score in sorted_factors[:8]:  # Top 8
                friendly_name = factor_name.replace('_', ' ').title()
                impact = 'High' if score > 0.7 else 'Medium' if score > 0.4 else 'Low'
                drivers_data.append([friendly_name, f"{score:.2f}", impact])
            
            drivers_table = Table(drivers_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
            drivers_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#111827')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#00FFC8')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FAFAFA')]),
            ]))
            
            story.append(drivers_table)
        
        return story
    
    def _build_risk_timeline(self, data: Dict[str, Any]) -> List:
        """Build risk timeline section"""
        story = []
        
        header = Paragraph(
            "Risk Timeline Analysis",
            self.styles['SectionHeader']
        )
        story.append(header)
        story.append(Spacer(1, 0.3*inch))
        
        # Timeline chart if available
        charts = data.get('charts', {})
        timeline_base64 = charts.get('timeline')
        
        if timeline_base64:
            try:
                chart_bytes = self.image_exporter.process_chart_image(timeline_base64, max_width=600, max_height=300)
                if chart_bytes:
                    img_buffer = BytesIO(chart_bytes)
                    chart_img = RLImage(img_buffer, width=6*inch, height=3*inch)
                    story.append(chart_img)
                    story.append(Spacer(1, 0.2*inch))
            except Exception as e:
                print(f"[PDF Builder] Error adding timeline chart: {e}")
        
        # Timeline data
        timeline = data.get('timeline', [])
        if timeline:
            timeline_text = "<b>Key Timeline Events:</b><br/>"
            for event in timeline[:5]:  # Top 5 events
                if isinstance(event, dict):
                    timeline_text += f"• {event.get('description', str(event))}<br/>"
                else:
                    timeline_text += f"• {event}<br/>"
            
            timeline_para = Paragraph(timeline_text, self.styles['BodyText'])
            story.append(timeline_para)
        
        return story
    
    def _build_network_map(self, data: Dict[str, Any]) -> List:
        """Build network risk map section"""
        story = []
        
        header = Paragraph(
            "Network Risk Analysis",
            self.styles['SectionHeader']
        )
        story.append(header)
        story.append(Spacer(1, 0.3*inch))
        
        # Network chart if available
        charts = data.get('charts', {})
        network_base64 = charts.get('network')
        
        if network_base64:
            try:
                chart_bytes = self.image_exporter.process_chart_image(network_base64, max_width=600, max_height=400)
                if chart_bytes:
                    img_buffer = BytesIO(chart_bytes)
                    chart_img = RLImage(img_buffer, width=6*inch, height=4*inch)
                    story.append(chart_img)
                    story.append(Spacer(1, 0.2*inch))
            except Exception as e:
                print(f"[PDF Builder] Error adding network chart: {e}")
        
        # Network data
        network = data.get('network', {})
        if network:
            network_text = "<b>Network Risk Factors:</b><br/>"
            for key, value in list(network.items())[:5]:
                friendly_key = key.replace('_', ' ').title()
                network_text += f"• {friendly_key}: {value}<br/>"
            
            network_para = Paragraph(network_text, self.styles['BodyText'])
            story.append(network_para)
        
        return story
    
    def _build_scenario_section(self, data: Dict[str, Any]) -> List:
        """Build scenario simulation section"""
        story = []
        
        header = Paragraph(
            "Scenario Simulation Analysis",
            self.styles['SectionHeader']
        )
        story.append(header)
        story.append(Spacer(1, 0.3*inch))
        
        scenarios = data.get('scenario_comparisons', [])
        
        for idx, scenario in enumerate(scenarios[:3], 1):  # Top 3 scenarios
            scenario_name = scenario.get('name', f'Scenario {idx}')
            baseline_score = scenario.get('baseline_score', 0)
            simulation_score = scenario.get('simulation_score', 0)
            delta = scenario.get('delta_from_baseline', 0)
            
            scenario_header = Paragraph(
                f"<b>{scenario_name}</b>",
                self.styles['SubsectionHeader']
            )
            story.append(scenario_header)
            
            # Scenario comparison table
            comp_data = [
                ['Metric', 'Baseline', 'Scenario', 'Change'],
                ['Risk Score', f"{baseline_score:.1f}", f"{simulation_score:.1f}", f"{delta:+.1f}"],
            ]
            
            comp_table = Table(comp_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            comp_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#111827')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#00FFC8')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0')),
            ]))
            
            story.append(comp_table)
            story.append(Spacer(1, 0.2*inch))
            
            # Scenario explanation
            explanation = scenario.get('explanation', {})
            if explanation:
                exp_text = explanation.get('summary', '')
                if exp_text:
                    exp_para = Paragraph(f"<b>Analysis:</b> {exp_text}", self.styles['BodyText'])
                    story.append(exp_para)
            
            story.append(Spacer(1, 0.3*inch))
        
        return story
    
    def _build_recommendations(self, data: Dict[str, Any]) -> List:
        """Build recommendations section"""
        story = []
        
        header = Paragraph(
            "Risk Mitigation Recommendations",
            self.styles['SectionHeader']
        )
        story.append(header)
        story.append(Spacer(1, 0.3*inch))
        
        recommendations = data.get('recommendations', [])
        
        if not recommendations:
            recommendations = [
                "Maintain standard risk management procedures",
                "Monitor key risk factors regularly",
                "Ensure adequate insurance coverage"
            ]
        
        # Categorize recommendations
        operational = []
        tactical = []
        strategic = []
        
        for rec in recommendations:
            rec_lower = rec.lower()
            if any(word in rec_lower for word in ['immediate', 'urgent', 'now', 'today']):
                operational.append(rec)
            elif any(word in rec_lower for word in ['plan', 'strategy', 'long-term', 'future']):
                strategic.append(rec)
            else:
                tactical.append(rec)
        
        # Operational recommendations
        if operational:
            op_header = Paragraph("<b>Operational (Immediate Actions):</b>", self.styles['SubsectionHeader'])
            story.append(op_header)
            for rec in operational[:5]:
                rec_para = Paragraph(f"• {rec}", self.styles['BodyText'])
                story.append(rec_para)
            story.append(Spacer(1, 0.2*inch))
        
        # Tactical recommendations
        if tactical:
            tac_header = Paragraph("<b>Tactical (Short-term Actions):</b>", self.styles['SubsectionHeader'])
            story.append(tac_header)
            for rec in tactical[:5]:
                rec_para = Paragraph(f"• {rec}", self.styles['BodyText'])
                story.append(rec_para)
            story.append(Spacer(1, 0.2*inch))
        
        # Strategic recommendations
        if strategic:
            str_header = Paragraph("<b>Strategic (Long-term Actions):</b>", self.styles['SubsectionHeader'])
            story.append(str_header)
            for rec in strategic[:5]:
                rec_para = Paragraph(f"• {rec}", self.styles['BodyText'])
                story.append(rec_para)
            story.append(Spacer(1, 0.2*inch))
        
        return story
    
    def _build_appendix(self, data: Dict[str, Any]) -> List:
        """Build appendix section"""
        story = []
        
        header = Paragraph(
            "Appendix",
            self.styles['SectionHeader']
        )
        story.append(header)
        story.append(Spacer(1, 0.3*inch))
        
        # Metadata
        metadata_text = f"""
        <b>Report Metadata:</b><br/>
        Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br/>
        Report Version: RISKCAST v12.5<br/>
        Engine Version: v2<br/>
        """
        
        metadata_para = Paragraph(metadata_text, self.styles['BodyText'])
        story.append(metadata_para)
        story.append(Spacer(1, 0.3*inch))
        
        # Limitations
        limitations_text = """
        <b>Report Limitations:</b><br/>
        • Risk assessments are based on available data and assumptions<br/>
        • External factors (e.g., geopolitical events) may impact actual risk<br/>
        • Recommendations should be reviewed by qualified risk management professionals<br/>
        • This report does not constitute financial or legal advice<br/>
        """
        
        limitations_para = Paragraph(limitations_text, self.styles['BodyText'])
        story.append(limitations_para)
        
        return story
    
    def _add_footer(self, canvas, doc):
        """Add footer to each page"""
        canvas.saveState()
        
        # Footer text
        footer_text = f"RISKCAST Enterprise AI - Page {doc.page}"
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#999999'))
        
        # Draw footer
        canvas.drawCentredString(
            doc.pagesize[0] / 2,
            15,
            footer_text
        )
        
        # Draw line
        canvas.setStrokeColor(colors.HexColor('#E0E0E0'))
        canvas.line(
            self.margins['left'],
            25,
            doc.pagesize[0] - self.margins['right'],
            25
        )
        
        canvas.restoreState()




















