"""
Coverage Recommendation Engine

Features:
1. Cargo-based coverage suggestions
2. Risk-adjusted recommendations
3. Historical pattern analysis
4. Personalized recommendations
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict
import json

from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler, LabelEncoder

from app.core.logging import get_logger


logger = get_logger(__name__)


class CoverageType(str, Enum):
    """Available coverage types."""
    ALL_RISKS = "ALL_RISKS"
    FPA = "FPA"  # Free of Particular Average
    WA = "WA"    # With Average
    NAMED_PERILS = "NAMED_PERILS"
    TOTAL_LOSS = "TOTAL_LOSS"


class CoverageExtension(str, Enum):
    """Coverage extensions/add-ons."""
    WAR_RISK = "WAR_RISK"
    STRIKES = "STRIKES"
    REJECTION = "REJECTION"
    REFRIGERATION = "REFRIGERATION"
    MOLD_MILDEW = "MOLD_MILDEW"
    INFESTATION = "INFESTATION"
    SHORTAGE = "SHORTAGE"
    HOOKS_DAMAGE = "HOOKS_DAMAGE"
    RUST_OXIDATION = "RUST_OXIDATION"
    THEFT = "THEFT"
    SURVEY_FEES = "SURVEY_FEES"


@dataclass
class CoverageRecommendation:
    """A coverage recommendation."""
    coverage_type: CoverageType
    recommended_extensions: List[CoverageExtension]
    confidence: float
    reasoning: List[str]
    estimated_premium_impact: float  # % increase from base
    risk_reduction: float  # Estimated risk reduction
    similar_shipments_count: int
    claim_rate_with_coverage: float
    claim_rate_without_coverage: float


@dataclass
class DeductibleRecommendation:
    """Deductible recommendation."""
    recommended_deductible_pct: float
    premium_savings_pct: float
    risk_retained_usd: float
    reasoning: str


class CoverageRecommender:
    """
    Recommends optimal coverage based on cargo, route, and historical data.
    """
    
    # Cargo type to recommended extensions mapping
    CARGO_EXTENSION_MATRIX = {
        "ELECTRONICS": [CoverageExtension.THEFT, CoverageExtension.REJECTION],
        "MACHINERY": [CoverageExtension.RUST_OXIDATION, CoverageExtension.HOOKS_DAMAGE],
        "FOOD_PERISHABLE": [CoverageExtension.REFRIGERATION, CoverageExtension.MOLD_MILDEW, CoverageExtension.INFESTATION],
        "TEXTILES": [CoverageExtension.MOLD_MILDEW, CoverageExtension.HOOKS_DAMAGE],
        "CHEMICALS": [CoverageExtension.REJECTION],
        "PHARMACEUTICALS": [CoverageExtension.REFRIGERATION, CoverageExtension.REJECTION],
        "AUTOMOTIVE": [CoverageExtension.RUST_OXIDATION, CoverageExtension.SHORTAGE],
        "RAW_MATERIALS": [CoverageExtension.SHORTAGE, CoverageExtension.SURVEY_FEES],
    }
    
    # High-risk regions requiring war risk
    WAR_RISK_REGIONS = {
        "MIDDLE_EAST", "WEST_AFRICA", "HORN_OF_AFRICA", "SOUTHEAST_ASIA_DISPUTED"
    }
    
    def __init__(self):
        self.model: Optional[NearestNeighbors] = None
        self.scaler: Optional[StandardScaler] = None
        self.historical_data: Optional[pd.DataFrame] = None
        self.label_encoders: Dict[str, LabelEncoder] = {}
    
    def train(self, historical_data: pd.DataFrame):
        """
        Train recommendation model on historical shipment data.
        
        Expected columns:
        - cargo_type, cargo_value_usd, origin_region, destination_region
        - coverage_type, extensions (list)
        - had_claim, claim_amount_usd
        """
        self.historical_data = historical_data.copy()
        
        # Encode categorical features
        categorical_cols = ['cargo_type', 'origin_region', 'destination_region', 'coverage_type']
        
        for col in categorical_cols:
            if col in historical_data.columns:
                self.label_encoders[col] = LabelEncoder()
                historical_data[f'{col}_encoded'] = self.label_encoders[col].fit_transform(
                    historical_data[col].fillna('UNKNOWN')
                )
        
        # Prepare features for similarity model
        feature_cols = [
            'cargo_value_usd',
            'cargo_type_encoded',
            'origin_region_encoded',
            'destination_region_encoded'
        ]
        
        available_features = [c for c in feature_cols if c in historical_data.columns]
        X = historical_data[available_features].fillna(0).values
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train nearest neighbors model
        self.model = NearestNeighbors(n_neighbors=50, metric='cosine')
        self.model.fit(X_scaled)
        
        logger.info(f"Coverage recommender trained on {len(historical_data)} shipments")
    
    def recommend(
        self,
        cargo_type: str,
        cargo_value_usd: float,
        origin_region: str,
        destination_region: str,
        transit_days: int = 21,
        customer_history: Optional[Dict] = None
    ) -> CoverageRecommendation:
        """
        Generate coverage recommendation for a shipment.
        """
        # Start with base recommendation
        base_coverage = self._determine_base_coverage(cargo_type, cargo_value_usd)
        
        # Get recommended extensions
        extensions = self._recommend_extensions(
            cargo_type, origin_region, destination_region
        )
        
        # Find similar shipments
        similar_stats = self._analyze_similar_shipments(
            cargo_type, cargo_value_usd, origin_region, destination_region
        )
        
        # Adjust based on customer history
        if customer_history:
            extensions = self._personalize_extensions(extensions, customer_history)
        
        # Calculate metrics
        premium_impact = self._calculate_premium_impact(extensions)
        risk_reduction = self._estimate_risk_reduction(base_coverage, extensions)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            base_coverage, extensions, cargo_type, origin_region, destination_region
        )
        
        return CoverageRecommendation(
            coverage_type=base_coverage,
            recommended_extensions=extensions,
            confidence=similar_stats.get('confidence', 0.7),
            reasoning=reasoning,
            estimated_premium_impact=premium_impact,
            risk_reduction=risk_reduction,
            similar_shipments_count=similar_stats.get('count', 0),
            claim_rate_with_coverage=similar_stats.get('claim_rate_with', 0.03),
            claim_rate_without_coverage=similar_stats.get('claim_rate_without', 0.08)
        )
    
    def _determine_base_coverage(self, cargo_type: str, cargo_value_usd: float) -> CoverageType:
        """Determine base coverage type."""
        # High-value cargo should get All Risks
        if cargo_value_usd > 500000:
            return CoverageType.ALL_RISKS
        
        # Sensitive cargo types
        sensitive_types = {'ELECTRONICS', 'PHARMACEUTICALS', 'FOOD_PERISHABLE', 'ARTWORK'}
        if cargo_type.upper() in sensitive_types:
            return CoverageType.ALL_RISKS
        
        # Bulk commodities can use FPA
        bulk_types = {'RAW_MATERIALS', 'MINERALS', 'GRAIN', 'COAL'}
        if cargo_type.upper() in bulk_types:
            return CoverageType.FPA
        
        # Default to With Average
        return CoverageType.WA
    
    def _recommend_extensions(
        self,
        cargo_type: str,
        origin_region: str,
        destination_region: str
    ) -> List[CoverageExtension]:
        """Recommend coverage extensions."""
        extensions = set()
        
        # Cargo-specific extensions
        cargo_upper = cargo_type.upper()
        if cargo_upper in self.CARGO_EXTENSION_MATRIX:
            extensions.update(self.CARGO_EXTENSION_MATRIX[cargo_upper])
        
        # Region-based extensions
        regions = {origin_region.upper(), destination_region.upper()}
        if regions & self.WAR_RISK_REGIONS:
            extensions.add(CoverageExtension.WAR_RISK)
            extensions.add(CoverageExtension.STRIKES)
        
        # Always recommend survey fees for high-value
        extensions.add(CoverageExtension.SURVEY_FEES)
        
        return list(extensions)
    
    def _analyze_similar_shipments(
        self,
        cargo_type: str,
        cargo_value_usd: float,
        origin_region: str,
        destination_region: str
    ) -> Dict:
        """Find and analyze similar historical shipments."""
        if self.model is None or self.historical_data is None:
            return {'count': 0, 'confidence': 0.5}
        
        # Encode query
        try:
            cargo_encoded = self.label_encoders['cargo_type'].transform([cargo_type])[0]
            origin_encoded = self.label_encoders['origin_region'].transform([origin_region])[0]
            dest_encoded = self.label_encoders['destination_region'].transform([destination_region])[0]
        except (KeyError, ValueError):
            return {'count': 0, 'confidence': 0.5}
        
        query = np.array([[cargo_value_usd, cargo_encoded, origin_encoded, dest_encoded]])
        query_scaled = self.scaler.transform(query)
        
        # Find neighbors
        distances, indices = self.model.kneighbors(query_scaled)
        
        similar = self.historical_data.iloc[indices[0]]
        
        # Calculate statistics
        with_good_coverage = similar[similar['coverage_type'] == 'ALL_RISKS']
        without_good_coverage = similar[similar['coverage_type'] != 'ALL_RISKS']
        
        claim_rate_with = with_good_coverage['had_claim'].mean() if len(with_good_coverage) > 0 else 0.03
        claim_rate_without = without_good_coverage['had_claim'].mean() if len(without_good_coverage) > 0 else 0.08
        
        # Confidence based on number of similar shipments and distance
        avg_distance = distances[0].mean()
        confidence = min(0.9, len(similar) / 100 * (1 - avg_distance))
        
        return {
            'count': len(similar),
            'confidence': confidence,
            'claim_rate_with': claim_rate_with,
            'claim_rate_without': claim_rate_without,
            'common_extensions': self._get_common_extensions(similar)
        }
    
    def _get_common_extensions(self, similar_shipments: pd.DataFrame) -> List[str]:
        """Get most common extensions from similar shipments."""
        if 'extensions' not in similar_shipments.columns:
            return []
        
        extension_counts = defaultdict(int)
        for extensions in similar_shipments['extensions'].dropna():
            if isinstance(extensions, str):
                extensions = json.loads(extensions)
            for ext in extensions:
                extension_counts[ext] += 1
        
        # Return extensions used by more than 30% of similar shipments
        threshold = len(similar_shipments) * 0.3
        common = [ext for ext, count in extension_counts.items() if count > threshold]
        
        return common
    
    def _personalize_extensions(
        self,
        extensions: List[CoverageExtension],
        customer_history: Dict
    ) -> List[CoverageExtension]:
        """Personalize extensions based on customer history."""
        # Add extensions the customer typically uses
        if 'preferred_extensions' in customer_history:
            for ext in customer_history['preferred_extensions']:
                try:
                    ext_enum = CoverageExtension(ext)
                    if ext_enum not in extensions:
                        extensions.append(ext_enum)
                except ValueError:
                    pass
        
        # If customer has had claims, recommend additional protection
        if customer_history.get('claim_count', 0) > 0:
            if CoverageExtension.SURVEY_FEES not in extensions:
                extensions.append(CoverageExtension.SURVEY_FEES)
        
        return extensions
    
    def _calculate_premium_impact(self, extensions: List[CoverageExtension]) -> float:
        """Calculate estimated premium impact of extensions."""
        extension_costs = {
            CoverageExtension.WAR_RISK: 0.15,
            CoverageExtension.STRIKES: 0.05,
            CoverageExtension.REJECTION: 0.08,
            CoverageExtension.REFRIGERATION: 0.12,
            CoverageExtension.MOLD_MILDEW: 0.05,
            CoverageExtension.INFESTATION: 0.04,
            CoverageExtension.SHORTAGE: 0.03,
            CoverageExtension.HOOKS_DAMAGE: 0.02,
            CoverageExtension.RUST_OXIDATION: 0.04,
            CoverageExtension.THEFT: 0.10,
            CoverageExtension.SURVEY_FEES: 0.02,
        }
        
        total_impact = sum(extension_costs.get(ext, 0.05) for ext in extensions)
        return min(total_impact, 0.50)  # Cap at 50% increase
    
    def _estimate_risk_reduction(
        self,
        coverage_type: CoverageType,
        extensions: List[CoverageExtension]
    ) -> float:
        """Estimate risk reduction from coverage."""
        base_reduction = {
            CoverageType.ALL_RISKS: 0.85,
            CoverageType.WA: 0.70,
            CoverageType.FPA: 0.50,
            CoverageType.NAMED_PERILS: 0.60,
            CoverageType.TOTAL_LOSS: 0.30
        }
        
        reduction = base_reduction.get(coverage_type, 0.50)
        
        # Extensions add incremental protection
        reduction += len(extensions) * 0.02
        
        return min(reduction, 0.95)
    
    def _generate_reasoning(
        self,
        coverage_type: CoverageType,
        extensions: List[CoverageExtension],
        cargo_type: str,
        origin_region: str,
        destination_region: str
    ) -> List[str]:
        """Generate human-readable reasoning."""
        reasons = []
        
        # Coverage type reasoning
        if coverage_type == CoverageType.ALL_RISKS:
            reasons.append("All Risks coverage recommended for comprehensive protection")
        elif coverage_type == CoverageType.FPA:
            reasons.append("FPA coverage suitable for bulk cargo with lower damage risk")
        
        # Extension reasoning
        if CoverageExtension.WAR_RISK in extensions:
            reasons.append(f"War risk recommended due to transit through high-risk region")
        
        if CoverageExtension.REFRIGERATION in extensions:
            reasons.append(f"Refrigeration breakdown coverage essential for {cargo_type}")
        
        if CoverageExtension.THEFT in extensions:
            reasons.append(f"Theft coverage recommended for high-value {cargo_type}")
        
        return reasons
    
    def recommend_deductible(
        self,
        cargo_value_usd: float,
        risk_score: float,
        customer_history: Optional[Dict] = None
    ) -> DeductibleRecommendation:
        """Recommend optimal deductible level."""
        # Higher risk = lower deductible recommended
        # Larger shipments can handle higher deductibles
        
        if cargo_value_usd > 1000000:
            # Large shipment - can afford higher deductible
            if risk_score < 0.3:
                deductible_pct = 0.02  # 2%
                savings = 0.15
            else:
                deductible_pct = 0.01  # 1%
                savings = 0.08
        elif cargo_value_usd > 100000:
            # Medium shipment
            if risk_score < 0.3:
                deductible_pct = 0.015
                savings = 0.12
            else:
                deductible_pct = 0.01
                savings = 0.06
        else:
            # Small shipment - keep deductible low
            deductible_pct = 0.01
            savings = 0.05
        
        # Adjust for customer history
        if customer_history:
            claim_ratio = customer_history.get('claim_ratio', 0)
            if claim_ratio > 0.1:
                # High claim history - recommend lower deductible
                deductible_pct = max(0.005, deductible_pct - 0.005)
                savings *= 0.7
        
        risk_retained = cargo_value_usd * deductible_pct
        
        reasoning = f"Based on cargo value (${cargo_value_usd:,.0f}) and risk profile ({risk_score:.0%})"
        
        return DeductibleRecommendation(
            recommended_deductible_pct=deductible_pct,
            premium_savings_pct=savings,
            risk_retained_usd=risk_retained,
            reasoning=reasoning
        )
