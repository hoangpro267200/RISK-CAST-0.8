"""
RISKCAST Region Detector
Automatically detects region based on origin and destination
"""

from typing import Optional, Tuple
from .vn_model import VN_REGION_CONFIG
from .sea_model import SEA_REGION_CONFIG
from .china_model import CHINA_REGION_CONFIG
from .eu_model import EU_REGION_CONFIG
from .us_model import US_REGION_CONFIG
from .global_model import GLOBAL_REGION_CONFIG


class RegionDetector:
    """Region detection based on route origin and destination"""
    
    # Region mapping
    REGION_COUNTRY_CODES = {
        # Vietnam
        'VN': 'VN',
        'VNSGN': 'VN', 'VNHPH': 'VN', 'VNDAD': 'VN',
        'SGN': 'VN', 'HPH': 'VN', 'DAD': 'VN',
        
        # Southeast Asia
        'SG': 'SEA', 'SIN': 'SEA',  # Singapore
        'TH': 'SEA', 'BKK': 'SEA',  # Thailand
        'MY': 'SEA', 'KUL': 'SEA', 'PEN': 'SEA',  # Malaysia
        'ID': 'SEA', 'JKT': 'SEA', 'CGK': 'SEA',  # Indonesia
        'PH': 'SEA', 'MNL': 'SEA',  # Philippines
        'KH': 'SEA', 'PNH': 'SEA',  # Cambodia
        'MM': 'SEA', 'RGN': 'SEA',  # Myanmar
        'LA': 'SEA', 'VTE': 'SEA',  # Laos
        
        # China
        'CN': 'CN', 'CHN': 'CN',
        'SHA': 'CN', 'CNSHA': 'CN',  # Shanghai
        'NGB': 'CN', 'CNNGB': 'CN',  # Ningbo
        'SZX': 'CN', 'CNSZX': 'CN',  # Shenzhen
        'QIN': 'CN', 'CNQIN': 'CN',  # Qingdao
        'XMN': 'CN', 'CNXMN': 'CN',  # Xiamen
        'YAN': 'CN', 'CNYAN': 'CN',  # Yantai
        'PEK': 'CN', 'CNPEK': 'CN',  # Beijing
        'CAN': 'CN', 'CNCAN': 'CN',  # Guangzhou
        
        # European Union
        'EU': 'EU',
        'NL': 'EU', 'RTM': 'EU', 'AMS': 'EU',  # Netherlands
        'DE': 'EU', 'HAM': 'EU', 'FEL': 'EU',  # Germany
        'BE': 'EU', 'ANT': 'EU', 'BRV': 'EU',  # Belgium
        'GB': 'EU', 'UK': 'EU', 'LON': 'EU',  # United Kingdom
        'FR': 'EU', 'FEL': 'EU',  # France
        'IT': 'EU', 'GOA': 'EU',  # Italy
        'ES': 'EU', 'BCN': 'EU',  # Spain
        
        # United States
        'US': 'US',
        'LAX': 'US', 'USLAX': 'US',  # Los Angeles
        'LB': 'US', 'USLB': 'US',  # Long Beach
        'NYC': 'US', 'USNYC': 'US',  # New York
        'JFK': 'US', 'USJFK': 'US',  # JFK
        'SAV': 'US', 'USSAV': 'US',  # Savannah
        'HOU': 'US', 'USHOU': 'US',  # Houston
    }
    
    REGION_CONFIGS = {
        'VN': VN_REGION_CONFIG,
        'SEA': SEA_REGION_CONFIG,
        'CN': CHINA_REGION_CONFIG,
        'EU': EU_REGION_CONFIG,
        'US': US_REGION_CONFIG,
        'GLOBAL': GLOBAL_REGION_CONFIG,
    }
    
    def __init__(self):
        """Initialize region detector"""
        pass
    
    def extract_country_code(self, location: str) -> Optional[str]:
        """
        Extract country/region code from location string
        
        Args:
            location: Location string (e.g., "VN_SGN", "SGN", "VN")
            
        Returns:
            Country/region code or None
        """
        if not location:
            return None
        
        location_upper = location.upper().strip()
        
        # Check direct match
        if location_upper in self.REGION_COUNTRY_CODES:
            return self.REGION_COUNTRY_CODES[location_upper]
        
        # Check if starts with known code
        for code, region in self.REGION_COUNTRY_CODES.items():
            if location_upper.startswith(code):
                return region
        
        # Check if ends with known code
        for code, region in self.REGION_COUNTRY_CODES.items():
            if location_upper.endswith(code):
                return region
        
        # Try to extract from underscore-separated format
        if '_' in location_upper:
            parts = location_upper.split('_')
            for part in parts:
                if part in self.REGION_COUNTRY_CODES:
                    return self.REGION_COUNTRY_CODES[part]
        
        return None
    
    def detect_region(self, origin: str, destination: str) -> Tuple[str, dict]:
        """
        Detect region based on origin and destination
        
        Rules:
        - VN→CN / VN→SEA → region = "SEA"
        - VN→US → region = "US"
        - VN→EU → region = "EU"
        - CN→VN → region = "China"
        - Default → "Global"
        
        Args:
            origin: Origin location/route
            destination: Destination location/route
            
        Returns:
            Tuple of (region_code, region_config)
        """
        origin_code = self.extract_country_code(origin)
        dest_code = self.extract_country_code(destination)
        
        # Rule 1: VN→CN / VN→SEA → SEA
        if origin_code == 'VN' and dest_code in ('CN', 'SEA'):
            return 'SEA', SEA_REGION_CONFIG
        
        # Rule 2: VN→US → US
        if origin_code == 'VN' and dest_code == 'US':
            return 'US', US_REGION_CONFIG
        
        # Rule 3: VN→EU → EU
        if origin_code == 'VN' and dest_code == 'EU':
            return 'EU', EU_REGION_CONFIG
        
        # Rule 4: CN→VN → China
        if origin_code == 'CN' and dest_code == 'VN':
            return 'CN', CHINA_REGION_CONFIG
        
        # Rule 5: If destination is clearly identifiable, use destination region
        if dest_code in self.REGION_CONFIGS:
            if dest_code != 'VN':  # Don't override VN for SEA routes
                return dest_code, self.REGION_CONFIGS[dest_code]
        
        # Rule 6: If origin is identifiable, use origin region (for return trips)
        if origin_code in self.REGION_CONFIGS:
            if origin_code not in ('SEA',):  # Don't use SEA as fallback
                return origin_code, self.REGION_CONFIGS[origin_code]
        
        # Rule 7: Both in SEA region
        if origin_code == 'SEA' or dest_code == 'SEA':
            return 'SEA', SEA_REGION_CONFIG
        
        # Rule 8: Default to Global
        return 'GLOBAL', GLOBAL_REGION_CONFIG
    
    def get_region_config(self, region_code: str) -> dict:
        """
        Get region configuration by code
        
        Args:
            region_code: Region code (VN, SEA, CN, EU, US, GLOBAL)
            
        Returns:
            Region configuration dictionary
        """
        return self.REGION_CONFIGS.get(region_code.upper(), GLOBAL_REGION_CONFIG)


# Global detector instance
_detector = RegionDetector()

def detect_region(origin: str, destination: str) -> Tuple[str, dict]:
    """
    Global function to detect region
    
    Args:
        origin: Origin location
        destination: Destination location
        
    Returns:
        Tuple of (region_code, region_config)
    """
    return _detector.detect_region(origin, destination)




















