"""
RISKCAST Regions Module
Region-based risk model calibrations for global deployment
"""

from .vn_model import VN_REGION_CONFIG
from .sea_model import SEA_REGION_CONFIG
from .china_model import CHINA_REGION_CONFIG
from .eu_model import EU_REGION_CONFIG
from .us_model import US_REGION_CONFIG
from .global_model import GLOBAL_REGION_CONFIG
from .detector import RegionDetector

__all__ = [
    "VN_REGION_CONFIG",
    "SEA_REGION_CONFIG",
    "CHINA_REGION_CONFIG",
    "EU_REGION_CONFIG",
    "US_REGION_CONFIG",
    "GLOBAL_REGION_CONFIG",
    "RegionDetector",
]




















