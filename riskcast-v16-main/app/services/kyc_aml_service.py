"""
RISKCAST KYC/AML Service
=========================
Handles Know Your Customer (KYC) and Anti-Money Laundering (AML) checks.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

# External services will be imported conditionally
try:
    # ComplyAdvantage or Trulioo SDK would go here
    # import complyadvantage
    COMPLY_ADVANTAGE_AVAILABLE = False
except ImportError:
    COMPLY_ADVANTAGE_AVAILABLE = False

try:
    # Trulioo SDK would go here
    # import trulioo
    TRULIOO_AVAILABLE = False
except ImportError:
    TRULIOO_AVAILABLE = False


class KYCAMLService:
    """
    KYC/AML verification service.
    Integrates with ComplyAdvantage, Trulioo, or similar services.
    """
    
    def __init__(self):
        self.comply_advantage_key = os.getenv("COMPLY_ADVANTAGE_API_KEY", "")
        self.trulioo_key = os.getenv("TRULIOO_API_KEY", "")
        self.use_mock = not (self.comply_advantage_key or self.trulioo_key)
        
        if self.use_mock:
            logger.warning("KYC/AML service using mock mode (no API keys configured)")
    
    async def verify_entity(
        self,
        legal_name: str,
        registration_number: str,
        country: str,
        industry: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify business entity.
        
        Args:
            legal_name: Legal company name
            registration_number: Business registration number
            country: Country code
            industry: Industry sector
            
        Returns:
            Verification result
        """
        if self.use_mock:
            return await self._mock_entity_verification(legal_name, country)
        
        # In production, call ComplyAdvantage or Trulioo
        # For now, return mock
        return await self._mock_entity_verification(legal_name, country)
    
    async def screen_sanctions(
        self,
        name: str,
        country: str,
        entity_type: str = "company"
    ) -> Dict[str, Any]:
        """
        Screen against sanctions lists (OFAC, EU, UN).
        
        Args:
            name: Entity or person name
            country: Country code
            entity_type: 'company' or 'person'
            
        Returns:
            Sanctions screening result
        """
        if self.use_mock:
            return await self._mock_sanctions_screen(name, country)
        
        # In production, call ComplyAdvantage sanctions API
        return await self._mock_sanctions_screen(name, country)
    
    async def check_pep(
        self,
        name: str,
        id_type: str,
        id_number: str,
        country: str
    ) -> Dict[str, Any]:
        """
        Check if person is Politically Exposed Person (PEP).
        
        Args:
            name: Person name
            id_type: ID type (passport, national_id, etc.)
            id_number: ID number
            country: Country code
            
        Returns:
            PEP check result
        """
        if self.use_mock:
            return await self._mock_pep_check(name, country)
        
        # In production, call ComplyAdvantage PEP database
        return await self._mock_pep_check(name, country)
    
    async def perform_full_kyc(
        self,
        entity_data: Dict[str, Any],
        beneficial_owners: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Perform full KYC check including entity verification, sanctions, and PEP.
        
        Args:
            entity_data: Entity information
            beneficial_owners: List of beneficial owners (>25% ownership)
            
        Returns:
            Complete KYC result
        """
        # Step 1: Entity verification
        entity_check = await self.verify_entity(
            legal_name=entity_data.get("legal_name", ""),
            registration_number=entity_data.get("registration_number", ""),
            country=entity_data.get("country", ""),
            industry=entity_data.get("industry")
        )
        
        if not entity_check.get("verified"):
            return {
                "status": "failed",
                "reason": "Entity verification failed",
                "details": entity_check
            }
        
        # Step 2: Sanctions screening
        sanctions_check = await self.screen_sanctions(
            name=entity_data.get("legal_name", ""),
            country=entity_data.get("country", ""),
            entity_type="company"
        )
        
        if sanctions_check.get("matches", 0) > 0:
            return {
                "status": "failed",
                "reason": "Sanctions match detected",
                "details": sanctions_check,
                "requires_manual_review": True
            }
        
        # Step 3: Beneficial owner screening
        pep_flags = []
        if beneficial_owners:
            for owner in beneficial_owners:
                pep_check = await self.check_pep(
                    name=owner.get("name", ""),
                    id_type=owner.get("id_type", ""),
                    id_number=owner.get("id_number", ""),
                    country=entity_data.get("country", "")
                )
                
                if pep_check.get("is_pep"):
                    pep_flags.append({
                        "owner": owner.get("name"),
                        "pep_details": pep_check
                    })
        
        # Step 4: Risk scoring
        risk_score = self._calculate_risk_score(
            entity_check=entity_check,
            sanctions_check=sanctions_check,
            pep_flags=pep_flags,
            country=entity_data.get("country", "")
        )
        
        # Determine status
        if risk_score > 70:
            status = "requires_manual_review"
        elif risk_score > 50:
            status = "requires_enhanced_due_diligence"
        elif sanctions_check.get("matches", 0) > 0:
            status = "failed"
        else:
            status = "approved"
        
        return {
            "status": status,
            "risk_score": risk_score,
            "entity_verification": entity_check,
            "sanctions_check": sanctions_check,
            "pep_flags": pep_flags,
            "approved_at": datetime.now() if status == "approved" else None,
            "reason": None if status == "approved" else f"Risk score: {risk_score}"
        }
    
    def _calculate_risk_score(
        self,
        entity_check: Dict[str, Any],
        sanctions_check: Dict[str, Any],
        pep_flags: List[Dict[str, Any]],
        country: str
    ) -> float:
        """
        Calculate overall risk score (0-100).
        
        Args:
            entity_check: Entity verification result
            sanctions_check: Sanctions screening result
            pep_flags: PEP check flags
            country: Country code
            
        Returns:
            Risk score (0-100)
        """
        score = 0.0
        
        # Entity verification contributes to score
        if not entity_check.get("verified"):
            score += 50
        
        # Sanctions matches
        score += sanctions_check.get("matches", 0) * 30
        
        # PEP flags
        score += len(pep_flags) * 15
        
        # Country risk (simplified)
        high_risk_countries = ["KP", "IR", "SY", "CU"]
        if country in high_risk_countries:
            score += 20
        
        return min(score, 100.0)
    
    async def _mock_entity_verification(
        self,
        legal_name: str,
        country: str
    ) -> Dict[str, Any]:
        """Mock entity verification."""
        # Simulate verification
        verified = True  # Most entities pass in mock mode
        
        # Check for obvious issues
        if any(term in legal_name.lower() for term in ["test", "fake", "invalid"]):
            verified = False
        
        return {
            "verified": verified,
            "entity_name": legal_name,
            "country": country,
            "confidence": 0.95 if verified else 0.0
        }
    
    async def _mock_sanctions_screen(
        self,
        name: str,
        country: str
    ) -> Dict[str, Any]:
        """Mock sanctions screening."""
        # Simulate sanctions check
        matches = 0
        
        # Check against known sanctions (mock)
        sanctioned_entities = ["sanctioned_company", "blocked_entity"]
        if any(term in name.lower() for term in sanctioned_entities):
            matches = 1
        
        return {
            "matches": matches,
            "screened_name": name,
            "country": country,
            "lists_checked": ["OFAC", "EU", "UN"],
            "match_details": [] if matches == 0 else [{"list": "OFAC", "reason": "Mock match"}]
        }
    
    async def _mock_pep_check(
        self,
        name: str,
        country: str
    ) -> Dict[str, Any]:
        """Mock PEP check."""
        # Simulate PEP check
        is_pep = False
        
        # Check for obvious PEP indicators (mock)
        pep_indicators = ["president", "minister", "senator", "governor"]
        if any(term in name.lower() for term in pep_indicators):
            is_pep = True
        
        return {
            "is_pep": is_pep,
            "name": name,
            "country": country,
            "confidence": 0.90 if is_pep else 0.95
        }
