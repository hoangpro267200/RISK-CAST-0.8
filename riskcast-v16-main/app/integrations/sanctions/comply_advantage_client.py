"""
ComplyAdvantage API Client

API Documentation: https://docs.complyadvantage.com/
"""

import aiohttp
import os
from typing import List, Optional

from app.core.logging import get_logger
from app.integrations.sanctions.models import (
    SanctionsMatch, SanctionsList, MatchStrength, EntityType
)


logger = get_logger(__name__)


class ComplyAdvantageClient:
    """
    ComplyAdvantage API client for KYC/AML screening.
    """
    
    BASE_URL = "https://api.complyadvantage.com"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        self.api_key = api_key or os.getenv("COMPLY_ADVANTAGE_API_KEY")
        self.timeout = timeout
        
        if not self.api_key:
            logger.warning("ComplyAdvantage API key not configured")
    
    async def screen(
        self,
        name: str,
        entity_type: str = "company",
        country: Optional[str] = None
    ) -> List[SanctionsMatch]:
        """
        Screen entity against ComplyAdvantage database.
        """
        if not self.api_key:
            return []
        
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "search_term": name,
            "fuzziness": 0.6,
            "filters": {
                "types": ["sanction", "warning", "fitness-probity"]
            }
        }
        
        if entity_type.lower() == "individual":
            payload["filters"]["entity_type"] = "person"
        else:
            payload["filters"]["entity_type"] = "company"
        
        if country:
            payload["filters"]["countries"] = [country]
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.BASE_URL}/searches",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status != 200:
                        logger.error(f"ComplyAdvantage error: {response.status}")
                        return []
                    
                    data = await response.json()
                    return self._parse_results(data, name, entity_type)
                    
        except Exception as e:
            logger.error(f"ComplyAdvantage request failed: {e}")
            return []
    
    def _parse_results(
        self,
        data: dict,
        query_name: str,
        entity_type: str
    ) -> List[SanctionsMatch]:
        """Parse ComplyAdvantage response."""
        matches = []
        
        hits = data.get("content", {}).get("data", {}).get("hits", [])
        
        for hit in hits:
            doc = hit.get("doc", {})
            
            # Determine list
            sources = doc.get("sources", [])
            list_name = SanctionsList.WATCHLIST
            for source in sources:
                source_name = source.lower()
                if "ofac" in source_name:
                    list_name = SanctionsList.OFAC_SDN
                    break
                elif "eu" in source_name:
                    list_name = SanctionsList.EU_SANCTIONS
                    break
                elif "un" in source_name:
                    list_name = SanctionsList.UN_SANCTIONS
                    break
            
            # Match strength from score
            score = hit.get("score", 0)
            if score >= 90:
                strength = MatchStrength.EXACT
            elif score >= 70:
                strength = MatchStrength.STRONG
            elif score >= 50:
                strength = MatchStrength.MEDIUM
            else:
                strength = MatchStrength.WEAK
            
            matches.append(SanctionsMatch(
                match_id=doc.get("id", ""),
                list_name=list_name,
                list_entry_id=doc.get("entity_type", "") + "-" + str(doc.get("id", "")),
                matched_name=query_name,
                matched_name_original=doc.get("name", ""),
                match_strength=strength,
                match_score=score,
                entity_type=EntityType.INDIVIDUAL if entity_type == "individual" else EntityType.COMPANY,
                aliases=doc.get("aka", []),
                program=", ".join(sources[:3]) if sources else None,
                remarks=doc.get("fields", {}).get("notes", [{}])[0].get("value") if doc.get("fields", {}).get("notes") else None
            ))
        
        return matches
