"""
Weather Service - Unified interface for weather data.

Aggregates multiple weather sources with quality tracking.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from app.integrations.weather.tomorrow_io import (
    TomorrowIOClient,
    WeatherObservation,
    WeatherForecast,
    WeatherDataQuality,
    create_weather_client
)

logger = logging.getLogger(__name__)


class WeatherService:
    """
    Unified weather service with:
    - Multiple source fallback
    - Quality tracking at every level
    - Audit trail for all data access
    """
    
    def __init__(self, audit_ledger: Optional[Any] = None):
        self.audit = audit_ledger
        self.tomorrow_io = create_weather_client(audit_ledger)
        
        # Could add backup sources:
        # self.openweather = OpenWeatherClient(audit_ledger)
        # self.noaa = NOAAClient(audit_ledger)
    
    async def get_weather_for_port(
        self,
        port_code: str,
        port_lat: float,
        port_lng: float
    ) -> Dict[str, Any]:
        """
        Get comprehensive weather data for a port.
        
        Returns data with explicit quality indicators.
        """
        # Get current conditions
        current = await self.tomorrow_io.get_realtime_weather(
            lat=port_lat,
            lng=port_lng,
            location_name=port_code
        )
        
        # Get forecast
        forecast = await self.tomorrow_io.get_forecast(
            lat=port_lat,
            lng=port_lng
        )
        
        # Get alerts
        alerts = await self.tomorrow_io.check_severe_weather_alerts(
            lat=port_lat,
            lng=port_lng
        )
        
        # Compute weather risk score
        weather_risk = self._compute_weather_risk(current, forecast, alerts)
        
        return {
            "port_code": port_code,
            "current_conditions": current.to_dict(),
            "forecast": forecast.to_dict() if forecast else None,
            "alerts": alerts,
            "weather_risk_score": weather_risk["score"],
            "weather_risk_factors": weather_risk["factors"],
            "data_quality": {
                "current": current.data_quality.value,
                "forecast": forecast.data_quality.value if forecast else "UNAVAILABLE",
                "overall": self._compute_overall_quality(current, forecast)
            },
            "fetched_at": datetime.utcnow().isoformat()
        }
    
    async def get_route_weather_assessment(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        departure_time: datetime,
        waypoints: Optional[List[Dict[str, float]]] = None
    ) -> Dict[str, Any]:
        """
        Get weather assessment along a route for risk calculation.
        
        This replaces hardcoded weather risk with real data.
        """
        # Generate waypoints if not provided
        if not waypoints:
            waypoints = self._generate_route_waypoints(
                origin_lat, origin_lng,
                dest_lat, dest_lng,
                num_points=10
            )
        
        # Get weather along route
        route_forecasts = await self.tomorrow_io.get_weather_along_route(
            waypoints=waypoints,
            departure_time=departure_time
        )
        
        # Analyze route weather
        analysis = self._analyze_route_weather(route_forecasts)
        
        return {
            "route": {
                "origin": {"lat": origin_lat, "lng": origin_lng},
                "destination": {"lat": dest_lat, "lng": dest_lng},
                "waypoints": waypoints
            },
            "departure_time": departure_time.isoformat(),
            "weather_summary": analysis["summary"],
            "risk_score": analysis["risk_score"],
            "risk_factors": analysis["risk_factors"],
            "worst_conditions": analysis["worst_conditions"],
            "alerts_along_route": analysis["alerts"],
            "data_quality": analysis["data_quality"],
            "waypoint_forecasts": [f.to_dict() for f in route_forecasts]
        }
    
    def _compute_weather_risk(
        self,
        current: WeatherObservation,
        forecast: Optional[WeatherForecast],
        alerts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compute weather risk score from real data."""
        risk_score = 0.0
        factors = []
        
        # Wind risk
        if current.wind_speed_ms > 20:
            wind_risk = min((current.wind_speed_ms - 20) / 30, 1.0) * 0.3
            risk_score += wind_risk
            factors.append({
                "factor": "high_wind",
                "value": current.wind_speed_ms,
                "unit": "m/s",
                "contribution": wind_risk
            })
        
        # Precipitation risk
        if current.precipitation_mm > 10:
            precip_risk = min(current.precipitation_mm / 50, 1.0) * 0.25
            risk_score += precip_risk
            factors.append({
                "factor": "precipitation",
                "value": current.precipitation_mm,
                "unit": "mm",
                "contribution": precip_risk
            })
        
        # Visibility risk
        if current.visibility_km < 5:
            vis_risk = (5 - current.visibility_km) / 5 * 0.2
            risk_score += vis_risk
            factors.append({
                "factor": "low_visibility",
                "value": current.visibility_km,
                "unit": "km",
                "contribution": vis_risk
            })
        
        # Severe weather alerts
        for alert in alerts:
            severity = alert.get("severity", "").upper()
            if severity in ["EXTREME", "SEVERE"]:
                alert_risk = 0.4 if severity == "EXTREME" else 0.25
                risk_score += alert_risk
                factors.append({
                    "factor": "severe_weather_alert",
                    "type": alert.get("type"),
                    "severity": severity,
                    "contribution": alert_risk
                })
        
        # Cap at 1.0
        risk_score = min(risk_score, 1.0)
        
        # Apply quality discount if using fallback data
        quality_factor = 1.0
        if current.data_quality == WeatherDataQuality.FALLBACK:
            quality_factor = 0.5  # 50% confidence in fallback data
            factors.append({
                "factor": "data_quality_discount",
                "reason": "Using fallback weather data",
                "confidence": quality_factor
            })
        
        return {
            "score": risk_score,
            "confidence": quality_factor,
            "factors": factors
        }
    
    def _compute_overall_quality(
        self,
        current: WeatherObservation,
        forecast: Optional[WeatherForecast]
    ) -> str:
        """Compute overall data quality from current and forecast."""
        qualities = [current.data_quality]
        if forecast:
            qualities.append(forecast.data_quality)
        
        # Return worst quality
        quality_order = [
            WeatherDataQuality.REAL_TIME,
            WeatherDataQuality.CACHED,
            WeatherDataQuality.STALE,
            WeatherDataQuality.FALLBACK,
            WeatherDataQuality.UNAVAILABLE
        ]
        
        worst = qualities[0]
        for q in qualities:
            if quality_order.index(q) > quality_order.index(worst):
                worst = q
        
        return worst.value
    
    def _generate_route_waypoints(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        num_points: int = 10
    ) -> List[Dict[str, float]]:
        """Generate waypoints along a route (simple linear interpolation)."""
        waypoints = []
        
        for i in range(num_points + 1):
            t = i / num_points
            lat = origin_lat + (dest_lat - origin_lat) * t
            lng = origin_lng + (dest_lng - origin_lng) * t
            waypoints.append({"lat": lat, "lng": lng})
        
        return waypoints
    
    def _analyze_route_weather(
        self,
        route_forecasts: List[WeatherForecast]
    ) -> Dict[str, Any]:
        """Analyze weather along route to compute risk."""
        if not route_forecasts:
            return {
                "summary": "No weather data available",
                "risk_score": 0.5,
                "risk_factors": [],
                "worst_conditions": None,
                "alerts": [],
                "data_quality": "UNAVAILABLE"
            }
        
        # Aggregate risk factors
        all_factors = []
        worst_conditions = None
        worst_risk = 0.0
        all_alerts = []
        
        for forecast in route_forecasts:
            # Check hourly forecasts for worst conditions
            for hour in forecast.hourly[:24]:  # Next 24 hours
                wind = hour.get("wind_speed_ms", 0)
                precip = hour.get("precipitation_mm", 0)
                
                # Simple risk calculation
                hour_risk = 0.0
                if wind > 20:
                    hour_risk += min((wind - 20) / 30, 1.0) * 0.5
                if precip > 10:
                    hour_risk += min(precip / 50, 1.0) * 0.5
                
                if hour_risk > worst_risk:
                    worst_risk = hour_risk
                    worst_conditions = {
                        "time": hour.get("time"),
                        "wind_speed_ms": wind,
                        "precipitation_mm": precip,
                        "weather_code": hour.get("weather_code"),
                    }
            
            # Collect alerts
            all_alerts.extend(forecast.alerts)
        
        # Compute overall risk score
        risk_score = min(worst_risk, 1.0)
        
        # Quality assessment
        qualities = [f.data_quality for f in route_forecasts]
        if WeatherDataQuality.REAL_TIME in qualities:
            overall_quality = "REAL_TIME"
        elif WeatherDataQuality.CACHED in qualities:
            overall_quality = "CACHED"
        elif WeatherDataQuality.STALE in qualities:
            overall_quality = "STALE"
        elif WeatherDataQuality.FALLBACK in qualities:
            overall_quality = "FALLBACK"
        else:
            overall_quality = "UNAVAILABLE"
        
        return {
            "summary": f"Weather risk along route: {risk_score:.2f}",
            "risk_score": risk_score,
            "risk_factors": all_factors,
            "worst_conditions": worst_conditions,
            "alerts": all_alerts,
            "data_quality": overall_quality
        }
    
    async def close(self):
        """Close all weather clients."""
        await self.tomorrow_io.close()


# Export singleton
weather_service: Optional[WeatherService] = None


def get_weather_service(audit_ledger: Optional[Any] = None) -> WeatherService:
    """Get or create weather service singleton."""
    global weather_service
    if weather_service is None:
        weather_service = WeatherService(audit_ledger)
    return weather_service
