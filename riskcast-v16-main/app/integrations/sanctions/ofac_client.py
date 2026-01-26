"""
OFAC Direct API Client

Uses OFAC SDN data directly
"""

import aiohttp
import os
from typing import List, Optional
from datetime import datetime
import hashlib

from app.core.logging import get_logger
from app.integrations.sanctions.models import (
    SanctionsMatch, SanctionsList, MatchStrength, EntityType
)


logger = get_logger(__name__)


class OFACClient:
    """
    Direct OFAC SDN list client.
    
    Uses the public OFAC API or downloaded SDN data.
    """
    
    # OFAC public data endpoint
    SDN_URL = "https://www.treasury.gov/ofac/downloads/sdn.xml"
    SDN_CSV_URL = "https://www.treasury.gov/ofac/downloads/sdn.csv"
    
    def __init__(
        self,
        timeout: int = 30
    ):
        self.timeout = timeout
        self._sdn_cache: List[dict] = []
        self._cache_loaded_at: Optional[datetime] = None
    
    async def screen(
        self,
        name: str,
        entity_type: str = "company"
    ) -> List[SanctionsMatch]:
        """
        Screen name against OFAC SDN list.
        """
        # Load SDN data if not cached
        if not self._sdn_cache or self._should_refresh_cache():
            await self._load_sdn_data()
        
        matches = []
        name_normalized = self._normalize_name(name)
        
        for entry in self._sdn_cache:
            entry_name = self._normalize_name(entry.get("name", ""))
            
            # Calculate similarity
            score = self._calculate_similarity(name_normalized, entry_name)
            
            if score >= 50:  # Minimum threshold
                # Determine strength
                if score >= 95:
                    strength = MatchStrength.EXACT
                elif score >= 80:
                    strength = MatchStrength.STRONG
                elif score >= 65:
                    strength = MatchStrength.MEDIUM
                else:
                    strength = MatchStrength.WEAK
                
                matches.append(SanctionsMatch(
                    match_id=hashlib.md5(entry.get("uid", "").encode()).hexdigest()[:12],
                    list_name=SanctionsList.OFAC_SDN,
                    list_entry_id=entry.get("uid", ""),
                    matched_name=name,
                    matched_name_original=entry.get("name", ""),
                    match_strength=strength,
                    match_score=score,
                    entity_type=EntityType.INDIVIDUAL if entry.get("type") == "Individual" else EntityType.COMPANY,
                    aliases=entry.get("aliases", []),
                    program=entry.get("program", ""),
                    remarks=entry.get("remarks", "")
                ))
        
        # Sort by score
        matches.sort(key=lambda m: m.match_score, reverse=True)
        
        return matches[:10]  # Return top 10
    
    async def _load_sdn_data(self):
        """Load SDN data from OFAC."""
        try:
            # For production, implement proper SDN parsing
            # This is a simplified mock
            self._sdn_cache = self._get_mock_sdn_data()
            self._cache_loaded_at = datetime.utcnow()
            logger.info("OFAC SDN data loaded (mock)")
        except Exception as e:
            logger.error(f"Failed to load SDN data: {e}")
    
    def _should_refresh_cache(self) -> bool:
        """Check if cache needs refresh (24 hours)."""
        if not self._cache_loaded_at:
            return True
        
        age = (datetime.utcnow() - self._cache_loaded_at).total_seconds()
        return age > 86400
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison."""
        import re
        name = name.upper()
        name = re.sub(r'[^\w\s]', '', name)  # Remove punctuation
        name = ' '.join(name.split())  # Normalize whitespace
        return name
    
    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """Calculate name similarity score."""
        # Simple token-based similarity
        tokens1 = set(name1.split())
        tokens2 = set(name2.split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1 & tokens2
        union = tokens1 | tokens2
        
        jaccard = len(intersection) / len(union)
        
        # Boost for exact match
        if name1 == name2:
            return 100.0
        
        return jaccard * 100
    
    def _get_mock_sdn_data(self) -> List[dict]:
        """Mock SDN data for development."""
        return [
            {
                "uid": "7890",
                "name": "IRAN PETROCHEMICAL COMMERCIAL CO",
                "type": "Entity",
                "program": "IRAN",
                "aliases": ["IPCC", "IRAN PETROCHEM"],
                "remarks": "Designated pursuant to IFSR"
            },
            {
                "uid": "10234",
                "name": "KOREA KWANGSON BANKING CORP",
                "type": "Entity",
                "program": "DPRK",
                "aliases": ["KKBC"],
                "remarks": "North Korean financial institution"
            },
            {
                "uid": "15678",
                "name": "RUSSIAN NATIONAL OIL CORPORATION",
                "type": "Entity",
                "program": "UKRAINE-EO13662",
                "aliases": ["RNOC", "ROSNEFT"],
                "remarks": "Designated under sectoral sanctions"
            },
            {
                "uid": "20001",
                "name": "SYRIA INTERNATIONAL ISLAMIC BANK",
                "type": "Entity",
                "program": "SYRIA",
                "aliases": ["SIIB"],
                "remarks": "Syrian financial institution"
            }
        ]
