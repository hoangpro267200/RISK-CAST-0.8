"""
RISKCAST Report - PDF Layouts
Enterprise-style PDF layout definitions with consistent styling
"""

from reportlab.lib import colors  # type: ignore
from reportlab.lib.pagesizes import letter, A4  # type: ignore
from reportlab.lib.units import inch, mm  # type: ignore
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # type: ignore
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY  # type: ignore
from reportlab.platypus import Paragraph, Spacer, PageBreak, Image as RLImage  # type: ignore
from typing import Dict, Tuple

# Color theme
PRIMARY_COLOR = '#00FFC8'  # Neon cyan
SECONDARY_COLOR = '#111827'  # Dark gray
LIGHT_BG = '#F5F7FA'  # Light gray background
ACCENT_COLOR = '#00D4FF'  # Bright blue
DANGER_COLOR = '#FF4444'  # Red for high risk
SUCCESS_COLOR = '#44FF44'  # Green for low risk

# Page setup
PAGE_SIZE = letter
LEFT_MARGIN = 30
RIGHT_MARGIN = 30
TOP_MARGIN = 40
BOTTOM_MARGIN = 30

# Fonts
FONT_PRIMARY = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'
FONT_ITALIC = 'Helvetica-Oblique'


class PDFLayouts:
    """PDF layout and style definitions"""
    
    def __init__(self):
        """Initialize layout system"""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        
        # Title style (Cover page)
        self.styles.add(ParagraphStyle(
            name='CoverTitle',
            parent=self.styles['Heading1'],
            fontSize=36,
            textColor=colors.HexColor(SECONDARY_COLOR),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName=FONT_BOLD,
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CoverSubtitle',
            parent=self.styles['Normal'],
            fontSize=18,
            textColor=colors.HexColor('#666666'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName=FONT_PRIMARY,
        ))
        
        # Section header
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor(SECONDARY_COLOR),
            spaceAfter=12,
            spaceBefore=24,
            fontName=FONT_BOLD,
            borderWidth=0,
            borderColor=colors.HexColor(PRIMARY_COLOR),
            borderPadding=5,
            leftIndent=0,
        ))
        
        # Subsection header
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor(SECONDARY_COLOR),
            spaceAfter=10,
            spaceBefore=16,
            fontName=FONT_BOLD,
        ))
        
        # Risk score style (large, highlighted)
        self.styles.add(ParagraphStyle(
            name='RiskScore',
            parent=self.styles['Normal'],
            fontSize=72,
            textColor=colors.HexColor(PRIMARY_COLOR),
            alignment=TA_CENTER,
            fontName=FONT_BOLD,
        ))
        
        # Body text
        self.styles.add(ParagraphStyle(
            name='BodyText',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor(SECONDARY_COLOR),
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            fontName=FONT_PRIMARY,
            leading=14,
        ))
        
        # Highlight text (neon accent)
        self.styles.add(ParagraphStyle(
            name='HighlightText',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor(PRIMARY_COLOR),
            fontName=FONT_BOLD,
        ))
        
        # Caption style
        self.styles.add(ParagraphStyle(
            name='Caption',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER,
            fontName=FONT_ITALIC,
            spaceAfter=12,
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#999999'),
            alignment=TA_CENTER,
            fontName=FONT_PRIMARY,
        ))
    
    def get_primary_color(self) -> colors.HexColor:
        """Get primary color"""
        return colors.HexColor(PRIMARY_COLOR)
    
    def get_secondary_color(self) -> colors.HexColor:
        """Get secondary color"""
        return colors.HexColor(SECONDARY_COLOR)
    
    def get_light_bg_color(self) -> colors.HexColor:
        """Get light background color"""
        return colors.HexColor(LIGHT_BG)
    
    def get_risk_color(self, score: float) -> colors.HexColor:
        """
        Get color based on risk score
        
        Args:
            score: Risk score (0-100)
            
        Returns:
            Color for the risk level
        """
        if score >= 85:
            return colors.HexColor(DANGER_COLOR)  # Critical/High
        elif score >= 70:
            return colors.HexColor('#FF8800')  # Medium-High
        elif score >= 50:
            return colors.HexColor('#FFAA00')  # Medium
        elif score >= 30:
            return colors.HexColor(ACCENT_COLOR)  # Low-Medium
        else:
            return colors.HexColor(SUCCESS_COLOR)  # Low
    
    def get_page_size(self) -> Tuple[float, float]:
        """Get page size"""
        return PAGE_SIZE
    
    def get_margins(self) -> Dict[str, float]:
        """Get page margins in points"""
        return {
            'left': LEFT_MARGIN,
            'right': RIGHT_MARGIN,
            'top': TOP_MARGIN,
            'bottom': BOTTOM_MARGIN,
        }
    
    def create_page_break(self) -> PageBreak:
        """Create page break element"""
        return PageBreak()
    
    def create_spacer(self, height: float = 12) -> Spacer:
        """
        Create spacer element
        
        Args:
            height: Height in points
            
        Returns:
            Spacer element
        """
        return Spacer(1, height)




















