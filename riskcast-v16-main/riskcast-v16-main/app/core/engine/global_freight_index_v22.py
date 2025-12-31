"""
RiskCast V22 - Global Freight Index Engine (GFI)
=================================================
Real-time freight market intelligence and dynamic risk adjustment

Author: RiskCast AI Team
Version: 22.0
Phase: 2.5 - Global Freight Index
License: Proprietary
"""

import numpy as np
from typing import Dict, List, Tuple


class GlobalFreightIndexV22:
    """
    Global Freight Index Engine that monitors freight market conditions
    across major trade lanes and provides dynamic market risk adjustment.
    
    Features:
    - 52-week historical index tracking
    - Market pressure classification
    - Volatility analysis
    - Trend detection
    - Dynamic market risk adjustment
    - Strategic recommendations
    
    Uses mock database for demonstration (production would use live APIs)
    """
    
    def __init__(self):
        """Initialize GFI engine with mock historical data"""
        
        # Mock historical index database (52 weeks of data per lane)
        self.LANE_INDEX_DB = {
            # Vietnam to US West Coast - Sea Freight 40HC
            "VNSGN-USLAX-SEA-40HC": {
                "baseline_index": 100.0,
                "currency": "USD",
                "unit": "per FEU",
                "weekly_index": [
                    120, 122, 125, 130, 135, 140, 150, 160,
                    165, 170, 180, 190, 200, 210, 205, 198,
                    190, 185, 180, 178, 176, 175, 174, 173,
                    172, 170, 168, 166, 165, 164, 163, 162,
                    160, 159, 158, 157, 156, 155, 154, 153,
                    152, 151, 150, 149, 148, 147, 146, 145,
                    144, 143, 142, 141
                ]
            },
            
            # Asia to Europe - Sea Freight 40HC
            "ASIA-EUR-SEA-40HC": {
                "baseline_index": 100.0,
                "currency": "USD",
                "unit": "per FEU",
                "weekly_index": [
                    110, 115, 118, 122, 128, 135, 145, 155,
                    165, 175, 185, 195, 205, 215, 220, 218,
                    210, 200, 195, 190, 185, 182, 180, 178,
                    176, 174, 172, 170, 168, 166, 164, 162,
                    160, 158, 156, 154, 152, 150, 148, 146,
                    145, 144, 143, 142, 141, 140, 139, 138,
                    137, 136, 135, 134
                ]
            },
            
            # Asia to US West Coast - Sea Freight 40HC (generic)
            "ASIA-USWC-SEA-40HC": {
                "baseline_index": 100.0,
                "currency": "USD",
                "unit": "per FEU",
                "weekly_index": [
                    115, 118, 120, 125, 130, 138, 148, 158,
                    168, 178, 188, 198, 208, 215, 210, 202,
                    195, 188, 182, 178, 174, 172, 170, 168,
                    166, 164, 162, 160, 158, 156, 154, 152,
                    150, 148, 146, 144, 142, 140, 138, 136,
                    135, 134, 133, 132, 131, 130, 129, 128,
                    127, 126, 125, 124
                ]
            },
            
            # China to US East Coast - Sea Freight 40HC
            "CNSHA-USNYC-SEA-40HC": {
                "baseline_index": 100.0,
                "currency": "USD",
                "unit": "per FEU",
                "weekly_index": [
                    105, 108, 112, 118, 125, 132, 142, 152,
                    162, 172, 182, 192, 202, 210, 205, 195,
                    185, 178, 172, 168, 165, 162, 160, 158,
                    156, 154, 152, 150, 148, 146, 145, 144,
                    143, 142, 141, 140, 139, 138, 137, 136,
                    135, 134, 133, 132, 131, 130, 129, 128,
                    127, 126, 125, 124
                ]
            },
            
            # Generic fallback - Asia to Global
            "ASIA-GLOBAL-SEA-40HC": {
                "baseline_index": 100.0,
                "currency": "USD",
                "unit": "per FEU",
                "weekly_index": [
                    112, 115, 118, 123, 128, 135, 145, 155,
                    165, 174, 183, 192, 200, 208, 202, 195,
                    188, 182, 177, 173, 170, 168, 166, 164,
                    162, 160, 158, 156, 154, 152, 150, 148,
                    146, 144, 142, 140, 138, 136, 134, 132,
                    131, 130, 129, 128, 127, 126, 125, 124,
                    123, 122, 121, 120
                ]
            }
        }
    
    def compute_index(self, transport: Dict, base_market_risk: float) -> Dict:
        """
        Compute Global Freight Index for the given trade lane
        
        Args:
            transport: Transport information dict with:
                - trade_lane: Human-readable lane description
                - mode: Transport mode
                - container_type: Container type
                - pol: Port of loading
                - pod: Port of discharge
                - priority: Shipment priority
            base_market_risk: Current market_volatility score (0-100)
        
        Returns:
            Comprehensive GFI analysis dictionary
        """
        
        # Step 1: Build lane key
        lane_key = self._build_lane_key(transport)
        
        # Step 2: Get lane data (with fallback)
        lane_data = self._get_lane_data(lane_key)
        
        # Step 3: Extract core data
        baseline_index = lane_data["baseline_index"]
        weekly_index = lane_data["weekly_index"]
        current_index = weekly_index[-1]  # Most recent week
        currency = lane_data["currency"]
        unit = lane_data["unit"]
        
        # Step 4: Calculate relative position
        relative_to_baseline = current_index / baseline_index
        
        # Step 5: Compute historical statistics
        history_stats = self._compute_history_stats(weekly_index)
        
        # Step 6: Classify pressure level
        pressure_level, pressure_score = self._classify_pressure_level(
            relative_to_baseline,
            history_stats["volatility_12w"]
        )
        
        # Step 7: Adjust market risk based on GFI
        adjusted_market_risk = self._adjust_market_risk(
            base_market_risk,
            pressure_score,
            history_stats["trend_direction"]
        )
        
        # Step 8: Build strategic recommendations
        strategy = self._build_strategy(
            pressure_level,
            history_stats["trend_direction"]
        )
        
        # Step 9: Build metadata
        meta = {
            "trade_lane": transport.get("trade_lane", "Unknown"),
            "mode": transport.get("mode", "sea_freight"),
            "container_type": transport.get("container_type", "40hc"),
            "pol": transport.get("pol", "N/A"),
            "pod": transport.get("pod", "N/A")
        }
        
        # Step 10: Construct full response
        return {
            "lane_key": lane_key,
            "meta": meta,
            "index": {
                "baseline_index": float(baseline_index),
                "current_index": float(current_index),
                "relative_to_baseline": float(relative_to_baseline),
                "currency": currency,
                "unit": unit
            },
            "history": {
                "lookback_weeks": 52,
                "weekly_points": weekly_index[-12:],  # Last 12 weeks for display
                "statistics": history_stats
            },
            "pressure": {
                "pressure_level": pressure_level,
                "pressure_score": float(pressure_score),
                "market_risk_base": float(base_market_risk),
                "market_risk_gfi_adjusted": float(adjusted_market_risk)
            },
            "strategy": strategy
        }
    
    def _build_lane_key(self, transport: Dict) -> str:
        """
        Build normalized lane key from transport data
        
        Format: '{POL}-{POD}-{MODE}-{CONTAINER}'
        Example: 'VNSGN-USLAX-SEA-40HC'
        
        Falls back to generic keys if data is missing
        """
        
        pol = transport.get("pol", "").upper()
        pod = transport.get("pod", "").upper()
        mode = transport.get("mode", "sea_freight").lower()
        container_type = transport.get("container_type", "40hc").lower()
        
        # Normalize mode
        mode_code = "SEA" if "sea" in mode else "AIR" if "air" in mode else "ROAD" if "road" in mode else "RAIL" if "rail" in mode else "SEA"
        
        # Normalize container
        container_code = container_type.replace("ft", "").replace("_", "").upper()
        
        # Build full key
        if pol and pod:
            lane_key = f"{pol}-{pod}-{mode_code}-{container_code}"
        else:
            # Fallback to generic
            # Try to infer region from POL/POD
            if pol and pol.startswith("CN"):
                region = "CHINA"
            elif pol and pol.startswith("VN"):
                region = "ASIA"
            else:
                region = "ASIA"
            
            if pod and pod.startswith("US"):
                destination = "USWC" if "LAX" in pod or "OAK" in pod or "SEA" in pod else "USEC"
            elif pod and (pod.startswith("NL") or pod.startswith("DE") or pod.startswith("GB")):
                destination = "EUR"
            else:
                destination = "GLOBAL"
            
            lane_key = f"{region}-{destination}-{mode_code}-{container_code}"
        
        return lane_key
    
    def _get_lane_data(self, lane_key: str) -> Dict:
        """
        Retrieve lane data from mock database with fallback logic
        """
        
        # Try exact match
        if lane_key in self.LANE_INDEX_DB:
            return self.LANE_INDEX_DB[lane_key]
        
        # Try generic fallback patterns
        fallback_patterns = [
            "ASIA-USWC-SEA-40HC",
            "ASIA-EUR-SEA-40HC",
            "ASIA-GLOBAL-SEA-40HC"
        ]
        
        for pattern in fallback_patterns:
            if pattern in self.LANE_INDEX_DB:
                return self.LANE_INDEX_DB[pattern]
        
        # Ultimate fallback
        return self.LANE_INDEX_DB["ASIA-GLOBAL-SEA-40HC"]
    
    def _compute_history_stats(self, weekly_index: List[float]) -> Dict:
        """
        Compute statistical metrics from historical index data
        
        Returns:
            - min_52w: Minimum over 52 weeks
            - max_52w: Maximum over 52 weeks
            - avg_12w: Average of last 12 weeks
            - volatility_12w: Coefficient of variation (std/mean) for last 12 weeks
            - trend_4w_slope_pct: Percentage change over last 4 weeks
            - trend_direction: 'up', 'flat', or 'down'
        """
        
        weekly_array = np.array(weekly_index)
        
        # 52-week stats
        min_52w = float(np.min(weekly_array))
        max_52w = float(np.max(weekly_array))
        
        # Last 12 weeks stats
        last_12 = weekly_array[-12:]
        avg_12w = float(np.mean(last_12))
        std_12w = float(np.std(last_12))
        volatility_12w = std_12w / avg_12w if avg_12w > 0 else 0.0
        
        # Last 4 weeks trend
        last_4 = weekly_array[-4:]
        trend_4w_slope_pct = float((last_4[-1] - last_4[0]) / last_4[0]) if last_4[0] > 0 else 0.0
        
        # Classify trend direction
        if abs(trend_4w_slope_pct) < 0.03:
            trend_direction = "flat"
        elif trend_4w_slope_pct > 0:
            trend_direction = "up"
        else:
            trend_direction = "down"
        
        return {
            "min_52w": float(min_52w),
            "max_52w": float(max_52w),
            "avg_12w": float(avg_12w),
            "volatility_12w": float(volatility_12w),
            "trend_4w_slope_pct": float(trend_4w_slope_pct),
            "trend_direction": trend_direction
        }
    
    def _classify_pressure_level(self, relative_to_baseline: float, 
                                 volatility_12w: float) -> Tuple[str, float]:
        """
        Classify market pressure level based on index position and volatility
        
        Returns:
            (pressure_level, pressure_score)
            - pressure_level: 'low', 'medium', 'high', or 'extreme'
            - pressure_score: 0.0-1.0 normalized score
        """
        
        base_score = 0.0
        
        # Index position relative to baseline
        if relative_to_baseline > 1.8:
            base_score += 0.4
        elif relative_to_baseline > 1.3:
            base_score += 0.25
        elif relative_to_baseline > 1.0:
            base_score += 0.15
        else:
            base_score += 0.05  # Below baseline
        
        # Volatility contribution
        if volatility_12w > 0.35:
            base_score += 0.35
        elif volatility_12w > 0.25:
            base_score += 0.25
        elif volatility_12w > 0.15:
            base_score += 0.15
        else:
            base_score += 0.05
        
        # Clamp score
        pressure_score = min(1.0, max(0.0, base_score))
        
        # Map to level
        if pressure_score < 0.25:
            pressure_level = "low"
        elif pressure_score < 0.5:
            pressure_level = "medium"
        elif pressure_score < 0.75:
            pressure_level = "high"
        else:
            pressure_level = "extreme"
        
        return pressure_level, pressure_score
    
    def _adjust_market_risk(self, base_market_risk: float, 
                           pressure_score: float, 
                           trend_direction: str) -> float:
        """
        Adjust market volatility risk score based on GFI pressure
        
        Args:
            base_market_risk: Current market_volatility score (0-100)
            pressure_score: GFI pressure score (0-1)
            trend_direction: 'up', 'flat', or 'down'
        
        Returns:
            Adjusted market risk score (0-100)
        """
        
        # Base multiplier from pressure
        multiplier = 1.0 + pressure_score * 0.4
        
        # Trend adjustment
        if trend_direction == "up":
            multiplier += 0.05  # Rising market = more risk
        elif trend_direction == "down":
            multiplier -= 0.05  # Falling market = less risk
        
        # Ensure minimum multiplier
        multiplier = max(0.8, multiplier)
        
        # Apply adjustment
        adjusted_risk = base_market_risk * multiplier
        
        # Clip to valid range
        adjusted_risk = min(100.0, max(0.0, adjusted_risk))
        
        return adjusted_risk
    
    def _build_strategy(self, pressure_level: str, trend_direction: str) -> Dict:
        """
        Build strategic recommendations based on market conditions
        
        Args:
            pressure_level: 'low', 'medium', 'high', or 'extreme'
            trend_direction: 'up', 'flat', or 'down'
        
        Returns:
            Strategy dictionary with tier, summary, and actions
        """
        
        # Define strategies based on conditions
        if pressure_level in ["low"] and trend_direction == "down":
            return {
                "recommendation_tier": "opportunistic",
                "summary": "Market is softening; good time to negotiate lower rates and explore alternatives.",
                "actions": [
                    "Shift more volume to spot market for rate advantage.",
                    "Renegotiate existing contracts with benchmark to current index.",
                    "Test new carriers on non-critical lanes for diversification.",
                    "Consider longer-term contracts to lock in favorable rates."
                ]
            }
        
        elif pressure_level == "low" and trend_direction in ["flat", "up"]:
            return {
                "recommendation_tier": "opportunistic",
                "summary": "Market conditions are favorable; proactive sourcing recommended.",
                "actions": [
                    "Balance 50-70% contract vs spot for flexibility.",
                    "Negotiate volume commitments for rate discounts.",
                    "Explore new carrier relationships while rates are stable.",
                    "Monitor early signals of market tightening."
                ]
            }
        
        elif pressure_level == "medium" and trend_direction == "down":
            return {
                "recommendation_tier": "balanced",
                "summary": "Market showing mixed signals; maintain balanced approach with flexibility.",
                "actions": [
                    "Maintain 60-70% contract coverage for core lanes.",
                    "Use spot market for 30-40% of volume for rate optimization.",
                    "Build contingency plans for potential market shifts.",
                    "Monitor weekly index movements closely."
                ]
            }
        
        elif pressure_level == "medium":
            return {
                "recommendation_tier": "balanced",
                "summary": "Market is stable but requires active management and monitoring.",
                "actions": [
                    "Secure 60-70% contract coverage for predictability.",
                    "Diversify across 3-4 carriers to reduce dependency risk.",
                    "Include quarterly rate review clauses in contracts.",
                    "Build buffer inventory for critical shipments."
                ]
            }
        
        elif pressure_level == "high":
            return {
                "recommendation_tier": "protective",
                "summary": "Market is tight and volatile; prioritize capacity protection over rate.",
                "actions": [
                    "Allocate 70-80% volume to mid-term contracts (3-6 months).",
                    "Use spot market only for excess or non-critical cargo.",
                    "Negotiate rate caps and index-linked clauses with core carriers.",
                    "Establish backup carriers with minimum volume commitments.",
                    "Consider alternative routings and modes for flexibility."
                ]
            }
        
        else:  # extreme
            return {
                "recommendation_tier": "protective",
                "summary": "Market conditions are extreme; immediate action required to secure capacity.",
                "actions": [
                    "Lock 80-90% of critical volume with long-term contracts (6-12 months).",
                    "Accept premium rates to guarantee space allocation.",
                    "Activate all carrier relationships including tier-2 and tier-3 providers.",
                    "Consider pre-positioning inventory to reduce freight dependency.",
                    "Implement demand planning to reduce peak shipping requirements.",
                    "Explore alternative supply chain configurations (nearshoring, etc.)."
                ]
            }






