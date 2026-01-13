"""
===============================================================
RISKCAST v14.5 — README
Climate Intelligence Upgrade Documentation

Author: Kai × Hoàng | v14.5
===============================================================
"""

README_CONTENT = """
RISKCAST v14.5 — Climate Intelligence Upgrade
==============================================

OVERVIEW
--------
RISKCAST v14.5 adds comprehensive climate risk intelligence to the 
existing v14.0 supply chain risk analytics engine. This upgrade 
integrates climate variables, ESG metrics, and climate-adjusted 
risk modeling into the core engine.

KEY FEATURES
------------
1. Climate Variables Integration
   - ENSO (El Niño Southern Oscillation) index tracking
   - Seasonal typhoon frequency monitoring
   - Sea surface temperature anomaly analysis
   - Port climate stress scoring
   - Long-term climate volatility indexing

2. Climate-Adjusted Risk Layers
   - Weather exposure adjustments based on climate patterns
   - Port risk climate stress factors
   - Transport reliability climate impacts
   - Route complexity climate volatility

3. Climate-Enhanced Monte Carlo
   - Climate-driven tail shock generation
   - Climate correlation matrix adjustments
   - Climate-adjusted VaR/CVaR calculations

4. ESG & Climate Resilience
   - ESG score integration
   - Climate resilience scoring
   - Green packaging assessments

5. AI-Powered Climate Narratives
   - Climate vulnerability summaries
   - Tail risk analysis
   - ENSO seasonal outlooks
   - ESG recommendations

USAGE
-----
1. Import climate modules:
   ```python
   from app.core.legacy.riskcast_v14_5_climate_upgrade import (
       ClimateVariables,
       ClimateRiskLayerExtensions,
       ClimateMonteCarloExtension,
       ESGClimateResilience,
       ClimateAIAnalysis
   )
   ```

2. Create climate variables:
   ```python
   climate_vars = ClimateVariables(
       ENSO_index=1.5,
       seasonal_typhoon_frequency=0.65,
       sea_surface_temperature_anomaly=0.8,
       port_climate_stress_score=6.5,
       long_term_climate_volatility_index=6.0,
       climate_tail_event_probability=0.08,
       ESG_score=62.0,
       climate_resilience_score=6.5,
       green_packaging_score=7.0
   )
   ```

3. Calculate CHI (Climate Hazard Index):
   ```python
   chi = climate_vars.calculate_CHI()
   ```

4. Apply climate adjustments to risk layers:
   ```python
   adjusted_score = ClimateRiskLayerExtensions.adjust_weather_exposure(
       base_score=5.0,
       climate_vars=climate_vars,
       context={}
   )
   ```

INTEGRATION
-----------
The climate upgrade is fully integrated into:
- risk_engine_v14.py: Core engine with climate adjustments
- risk_service_v14.py: API service layer
- Frontend input.js: Climate field inputs
- Frontend results.js: Climate metrics display

CONFIGURATION
-------------
Climate influence can be configured via RiskConfig:
- CLIMATE_INFLUENCE_ALPHA: 0.6 (moderate influence)
- CLIMATE_TAIL_STRENGTH: 0.35 (tail shock strength)

See RiskConfig class in risk_engine_v14.py for details.
"""







