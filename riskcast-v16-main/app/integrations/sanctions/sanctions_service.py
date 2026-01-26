"""
Sanctions Screening Service

Provides:
1. Entity screening against multiple lists
2. Vessel sanctions check
3. Country sanctions check
4. PEP screening
5. Adverse media screening
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json

from app.core.logging import get_logger
from app.integrations.sanctions.models import (
    SanctionsMatch, ScreeningResult, VesselScreeningResult,
    SanctionsList, EntityType, MatchStrength, RiskLevel
)
from app.integrations.sanctions.ofac_client import OFACClient
from app.integrations.sanctions.comply_advantage_client import ComplyAdvantageClient

# Optional Redis import
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False


logger = get_logger(__name__)


class SanctionsService:
    """
    Unified sanctions screening service.
    """
    
    # Sanctioned countries (high risk)
    SANCTIONED_COUNTRIES = {
        "KP": "North Korea",
        "IR": "Iran",
        "SY": "Syria",
        "CU": "Cuba",
        "RU": "Russia",  # Partial sanctions
        "BY": "Belarus",
        "VE": "Venezuela",  # Partial sanctions
        "MM": "Myanmar",
    }
    
    # High-risk flag states
    HIGH_RISK_FLAGS = {
        "KP", "IR", "SY", "KM", "TG", "TZ", "MD", "BO"
    }
    
    # Cache TTL
    CACHE_TTL_SECONDS = 86400  # 24 hours for sanctions data
    
    def __init__(
        self,
        ofac_client: Optional[OFACClient] = None,
        comply_advantage_client: Optional[ComplyAdvantageClient] = None,
        redis_client: Optional[object] = None
    ):
        self.ofac = ofac_client
        self.comply_advantage = comply_advantage_client
        self.redis = redis_client if REDIS_AVAILABLE and redis_client else None
    
    async def screen_entity(
        self,
        name: str,
        entity_type: EntityType = EntityType.COMPANY,
        country: Optional[str] = None,
        additional_info: Optional[Dict] = None,
        lists_to_check: Optional[List[SanctionsList]] = None
    ) -> ScreeningResult:
        """
        Screen an entity against sanctions lists.
        
        Args:
            name: Entity name to screen
            entity_type: Type of entity
            country: Country code (for additional context)
            additional_info: Additional identifying information
            lists_to_check: Specific lists to check (default: all)
        
        Returns:
            ScreeningResult with matches and risk assessment
        """
        screening_id = self._generate_screening_id(name, entity_type)
        
        # Check cache
        cached_result = await self._get_cached_result(screening_id)
        if cached_result:
            cached_result.cached = True
            return cached_result
        
        # Determine lists to check
        if lists_to_check is None:
            lists_to_check = [
                SanctionsList.OFAC_SDN,
                SanctionsList.OFAC_CONS,
                SanctionsList.EU_SANCTIONS,
                SanctionsList.UN_SANCTIONS,
                SanctionsList.UK_SANCTIONS
            ]
        
        all_matches = []
        
        # Screen with ComplyAdvantage (comprehensive)
        if self.comply_advantage:
            try:
                matches = await self.comply_advantage.screen(
                    name=name,
                    entity_type=entity_type.value,
                    country=country
                )
                all_matches.extend(matches)
            except Exception as e:
                logger.error(f"ComplyAdvantage screening failed: {e}")
        
        # Screen with OFAC direct
        if self.ofac and not all_matches:  # Fallback if ComplyAdvantage failed
            try:
                matches = await self.ofac.screen(
                    name=name,
                    entity_type=entity_type.value
                )
                all_matches.extend(matches)
            except Exception as e:
                logger.error(f"OFAC screening failed: {e}")
        
        # If no API available, use mock
        if not self.comply_advantage and not self.ofac:
            all_matches = self._mock_screen(name, entity_type)
        
        # Deduplicate matches
        all_matches = self._deduplicate_matches(all_matches)
        
        # Assess risk
        risk_level, risk_score, risk_factors = self._assess_risk(
            all_matches, entity_type, country
        )
        
        # Generate recommendation
        recommendation = self._generate_recommendation(risk_level, all_matches)
        
        result = ScreeningResult(
            screening_id=screening_id,
            query=name,
            entity_type=entity_type,
            total_matches=len(all_matches),
            high_risk_matches=len([m for m in all_matches if m.match_strength in [MatchStrength.EXACT, MatchStrength.STRONG]]),
            matches=all_matches,
            risk_level=risk_level,
            risk_score=risk_score,
            risk_factors=risk_factors,
            lists_checked=lists_to_check,
            screened_at=datetime.utcnow(),
            recommendation=recommendation
        )
        
        # Cache result
        await self._cache_result(screening_id, result)
        
        logger.info(
            f"Sanctions screening completed: {name}",
            extra={
                "screening_id": screening_id,
                "matches": len(all_matches),
                "risk_level": risk_level.value
            }
        )
        
        return result
    
    async def screen_vessel(
        self,
        vessel_name: str,
        imo: Optional[str] = None,
        mmsi: Optional[str] = None,
        flag_country: Optional[str] = None,
        owner_name: Optional[str] = None,
        operator_name: Optional[str] = None
    ) -> VesselScreeningResult:
        """
        Comprehensive vessel sanctions screening.
        """
        screening_id = self._generate_screening_id(
            f"VESSEL:{imo or mmsi or vessel_name}",
            EntityType.VESSEL
        )
        
        risk_factors = []
        
        # Screen vessel
        vessel_result = await self.screen_entity(
            name=vessel_name,
            entity_type=EntityType.VESSEL,
            additional_info={"imo": imo, "mmsi": mmsi}
        )
        vessel_sanctioned = vessel_result.risk_level in [RiskLevel.HIGH, RiskLevel.MEDIUM]
        
        # Screen owner if provided
        owner_matches = []
        owner_sanctioned = False
        if owner_name:
            owner_result = await self.screen_entity(
                name=owner_name,
                entity_type=EntityType.COMPANY
            )
            owner_matches = owner_result.matches
            owner_sanctioned = owner_result.risk_level in [RiskLevel.HIGH, RiskLevel.MEDIUM]
            if owner_sanctioned:
                risk_factors.append(f"Owner {owner_name} has sanctions matches")
        
        # Screen operator if provided
        operator_matches = []
        operator_sanctioned = False
        if operator_name and operator_name != owner_name:
            operator_result = await self.screen_entity(
                name=operator_name,
                entity_type=EntityType.COMPANY
            )
            operator_matches = operator_result.matches
            operator_sanctioned = operator_result.risk_level in [RiskLevel.HIGH, RiskLevel.MEDIUM]
            if operator_sanctioned:
                risk_factors.append(f"Operator {operator_name} has sanctions matches")
        
        # Check flag country
        flag_sanctioned = False
        flag_risk = RiskLevel.LOW
        if flag_country:
            if flag_country.upper() in self.SANCTIONED_COUNTRIES:
                flag_sanctioned = True
                flag_risk = RiskLevel.HIGH
                risk_factors.append(f"Flag country {flag_country} is sanctioned")
            elif flag_country.upper() in self.HIGH_RISK_FLAGS:
                flag_risk = RiskLevel.MEDIUM
                risk_factors.append(f"Flag country {flag_country} is high-risk")
        
        # Overall risk assessment
        if vessel_sanctioned or owner_sanctioned or operator_sanctioned or flag_sanctioned:
            overall_risk = RiskLevel.HIGH
        elif flag_risk == RiskLevel.MEDIUM or vessel_result.matches:
            overall_risk = RiskLevel.MEDIUM
        else:
            overall_risk = RiskLevel.CLEAR
        
        # Recommendation
        if overall_risk == RiskLevel.HIGH:
            recommendation = "REJECT - Do not proceed with this vessel"
        elif overall_risk == RiskLevel.MEDIUM:
            recommendation = "REVIEW - Manual review required before proceeding"
        else:
            recommendation = "CLEAR - No sanctions concerns identified"
        
        return VesselScreeningResult(
            screening_id=screening_id,
            imo=imo,
            mmsi=mmsi,
            vessel_name=vessel_name,
            flag_country=flag_country or "Unknown",
            vessel_sanctioned=vessel_sanctioned,
            vessel_matches=vessel_result.matches,
            owner_name=owner_name,
            owner_sanctioned=owner_sanctioned,
            owner_matches=owner_matches,
            operator_name=operator_name,
            operator_sanctioned=operator_sanctioned,
            operator_matches=operator_matches,
            flag_country_sanctioned=flag_sanctioned,
            flag_country_risk=flag_risk,
            overall_risk=overall_risk,
            risk_factors=risk_factors,
            recommendation=recommendation,
            screened_at=datetime.utcnow()
        )
    
    async def check_country(
        self,
        country_code: str
    ) -> Dict:
        """
        Check if a country is under sanctions.
        """
        country_upper = country_code.upper()
        
        is_sanctioned = country_upper in self.SANCTIONED_COUNTRIES
        is_high_risk = country_upper in self.HIGH_RISK_FLAGS
        
        risk_level = RiskLevel.HIGH if is_sanctioned else (
            RiskLevel.MEDIUM if is_high_risk else RiskLevel.LOW
        )
        
        return {
            "country_code": country_upper,
            "country_name": self.SANCTIONED_COUNTRIES.get(country_upper, ""),
            "is_sanctioned": is_sanctioned,
            "is_high_risk": is_high_risk,
            "risk_level": risk_level.value,
            "sanctions_programs": self._get_country_programs(country_upper),
            "recommendation": "REJECT" if is_sanctioned else (
                "REVIEW" if is_high_risk else "CLEAR"
            )
        }
    
    def _generate_screening_id(self, name: str, entity_type: EntityType) -> str:
        """Generate unique screening ID."""
        content = f"{name}:{entity_type.value}:{datetime.utcnow().date()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def _get_cached_result(
        self,
        screening_id: str
    ) -> Optional[ScreeningResult]:
        """Get cached screening result."""
        if not self.redis:
            return None
        
        try:
            cached = await self.redis.get(f"sanctions:{screening_id}")
            if cached:
                data = json.loads(cached)
                return self._dict_to_result(data)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        
        return None
    
    async def _cache_result(self, screening_id: str, result: ScreeningResult):
        """Cache screening result."""
        if not self.redis:
            return
        
        try:
            data = self._result_to_dict(result)
            await self.redis.setex(
                f"sanctions:{screening_id}",
                self.CACHE_TTL_SECONDS,
                json.dumps(data)
            )
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
    
    def _deduplicate_matches(
        self,
        matches: List[SanctionsMatch]
    ) -> List[SanctionsMatch]:
        """Remove duplicate matches."""
        seen = set()
        unique = []
        
        for match in matches:
            key = f"{match.list_name}:{match.list_entry_id}"
            if key not in seen:
                seen.add(key)
                unique.append(match)
        
        return unique
    
    def _assess_risk(
        self,
        matches: List[SanctionsMatch],
        entity_type: EntityType,
        country: Optional[str]
    ) -> Tuple[RiskLevel, float, List[str]]:
        """Assess overall risk from matches."""
        risk_factors = []
        
        if not matches:
            # Check country even without matches
            if country and country.upper() in self.SANCTIONED_COUNTRIES:
                risk_factors.append(f"Entity associated with sanctioned country: {country}")
                return RiskLevel.MEDIUM, 50.0, risk_factors
            return RiskLevel.CLEAR, 0.0, []
        
        # Count by strength
        exact = len([m for m in matches if m.match_strength == MatchStrength.EXACT])
        strong = len([m for m in matches if m.match_strength == MatchStrength.STRONG])
        medium = len([m for m in matches if m.match_strength == MatchStrength.MEDIUM])
        
        # Risk score
        risk_score = (exact * 40) + (strong * 25) + (medium * 10)
        risk_score = min(risk_score, 100.0)
        
        # Risk factors
        if exact > 0:
            risk_factors.append(f"{exact} exact match(es) on sanctions lists")
        if strong > 0:
            risk_factors.append(f"{strong} strong match(es) on sanctions lists")
        
        # Key programs
        programs = set(m.program for m in matches if m.program)
        if programs:
            risk_factors.append(f"Sanctions programs: {', '.join(programs)}")
        
        # Risk level
        if exact > 0 or risk_score >= 70:
            return RiskLevel.HIGH, risk_score, risk_factors
        elif strong > 0 or risk_score >= 40:
            return RiskLevel.MEDIUM, risk_score, risk_factors
        elif medium > 0:
            return RiskLevel.LOW, risk_score, risk_factors
        
        return RiskLevel.CLEAR, risk_score, risk_factors
    
    def _generate_recommendation(
        self,
        risk_level: RiskLevel,
        matches: List[SanctionsMatch]
    ) -> str:
        """Generate action recommendation."""
        if risk_level == RiskLevel.HIGH:
            return "REJECT - Entity matches sanctions lists. Do not proceed."
        elif risk_level == RiskLevel.MEDIUM:
            return "REVIEW - Potential matches require manual review."
        elif risk_level == RiskLevel.LOW:
            return "REVIEW - Minor matches detected. Quick review recommended."
        else:
            return "CLEAR - No sanctions concerns identified."
    
    def _get_country_programs(self, country_code: str) -> List[str]:
        """Get sanctions programs for a country."""
        programs = {
            "KP": ["North Korea Sanctions Program"],
            "IR": ["Iran Sanctions Program", "JCPOA"],
            "SY": ["Syria Sanctions Program"],
            "CU": ["Cuba Sanctions Program"],
            "RU": ["Russia/Ukraine Sanctions", "Sectoral Sanctions"],
            "BY": ["Belarus Sanctions Program"],
            "VE": ["Venezuela Sanctions Program"],
            "MM": ["Burma Sanctions Program"],
        }
        return programs.get(country_code, [])
    
    def _mock_screen(
        self,
        name: str,
        entity_type: EntityType
    ) -> List[SanctionsMatch]:
        """Mock screening for development."""
        # Simulate some matches for testing
        test_entities = {
            "PETRO IRAN": SanctionsList.OFAC_SDN,
            "NORTH KOREA SHIPPING": SanctionsList.OFAC_SDN,
            "RUSSIAN OIL": SanctionsList.EU_SANCTIONS,
            "SYRIAN TRADING": SanctionsList.UN_SANCTIONS,
        }
        
        matches = []
        name_upper = name.upper()
        
        for test_name, list_name in test_entities.items():
            if test_name in name_upper or any(word in name_upper for word in test_name.split()):
                matches.append(SanctionsMatch(
                    match_id=f"MOCK-{hashlib.md5(test_name.encode()).hexdigest()[:8]}",
                    list_name=list_name,
                    list_entry_id=f"MOCK-{test_name[:8]}",
                    matched_name=name,
                    matched_name_original=test_name,
                    match_strength=MatchStrength.STRONG if test_name in name_upper else MatchStrength.MEDIUM,
                    match_score=85.0 if test_name in name_upper else 65.0,
                    entity_type=entity_type,
                    program=test_name.split()[0]
                ))
        
        return matches
    
    def _result_to_dict(self, result: ScreeningResult) -> Dict:
        """Convert result to dict for caching."""
        return {
            "screening_id": result.screening_id,
            "query": result.query,
            "entity_type": result.entity_type.value,
            "total_matches": result.total_matches,
            "high_risk_matches": result.high_risk_matches,
            "matches": [
                {
                    "match_id": m.match_id,
                    "list_name": m.list_name.value,
                    "list_entry_id": m.list_entry_id,
                    "matched_name": m.matched_name,
                    "matched_name_original": m.matched_name_original,
                    "match_strength": m.match_strength.value,
                    "match_score": m.match_score,
                    "entity_type": m.entity_type.value,
                    "program": m.program
                }
                for m in result.matches
            ],
            "risk_level": result.risk_level.value,
            "risk_score": result.risk_score,
            "risk_factors": result.risk_factors,
            "lists_checked": [l.value for l in result.lists_checked],
            "screened_at": result.screened_at.isoformat(),
            "recommendation": result.recommendation
        }
    
    def _dict_to_result(self, data: Dict) -> ScreeningResult:
        """Convert dict back to result."""
        return ScreeningResult(
            screening_id=data["screening_id"],
            query=data["query"],
            entity_type=EntityType(data["entity_type"]),
            total_matches=data["total_matches"],
            high_risk_matches=data["high_risk_matches"],
            matches=[
                SanctionsMatch(
                    match_id=m["match_id"],
                    list_name=SanctionsList(m["list_name"]),
                    list_entry_id=m["list_entry_id"],
                    matched_name=m["matched_name"],
                    matched_name_original=m["matched_name_original"],
                    match_strength=MatchStrength(m["match_strength"]),
                    match_score=m["match_score"],
                    entity_type=EntityType(m["entity_type"]),
                    program=m.get("program")
                )
                for m in data["matches"]
            ],
            risk_level=RiskLevel(data["risk_level"]),
            risk_score=data["risk_score"],
            risk_factors=data["risk_factors"],
            lists_checked=[SanctionsList(l) for l in data["lists_checked"]],
            screened_at=datetime.fromisoformat(data["screened_at"]),
            recommendation=data["recommendation"]
        )
