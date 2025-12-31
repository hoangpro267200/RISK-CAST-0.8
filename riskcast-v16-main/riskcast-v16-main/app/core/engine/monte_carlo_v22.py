"""
RiskCast V22 - Monte Carlo Simulation Engine
=============================================
10,000-scenario probabilistic risk simulation engine

Author: RiskCast AI Team
Version: 22.0
Module: #4 - Monte Carlo Simulation Engine
License: Proprietary
"""

import numpy as np
from typing import Dict, List


class MonteCarloEngineV22:
    """
    Monte Carlo Simulation Engine that runs 10,000 probabilistic scenarios
    to model ETA variability and financial loss distributions.
    
    Uses numpy for all random number generation to ensure reproducibility
    and high-performance vectorized operations.
    
    Simulated Variables:
    - Carrier delays (Normal)
    - Port congestion (Normal)
    - Weather events (Bernoulli + Uniform)
    - Documentation delays (Bernoulli)
    - Market shocks (Cauchy - heavy tailed)
    - Cargo sensitivity (Uniform)
    - Base transit noise (Normal)
    - Catastrophic events (Bernoulli)
    """
    
    def __init__(self, n_runs: int = 10000, random_seed: int = None):
        """
        Initialize Monte Carlo engine
        
        Args:
            n_runs: Number of simulation runs (default: 10,000)
            random_seed: Random seed for reproducibility (default: None)
        """
        self.n_runs = n_runs
        if random_seed is not None:
            np.random.seed(random_seed)
    
    def run_simulation(self, transport: Dict, cargo: Dict, layer_scores: Dict) -> Dict:
        """
        Run Monte Carlo simulation for ETA and loss distributions
        
        Args:
            transport: Transport information (transit_time, mode, etc.)
            cargo: Cargo details (insurance_value, sensitivity, etc.)
            layer_scores: Risk layer scores from V21 engine
        
        Returns:
            Dictionary with simulation results, statistics, and distributions
        """
        
        # Extract base parameters
        base_transit = transport.get('transit_time', 14)
        cargo_value = cargo.get('insurance_value', 100000)
        
        # Extract relevant risk scores (0-100 range, convert to 0-1)
        carrier_risk = layer_scores.get('carrier_performance', 50) / 100.0
        port_risk = layer_scores.get('port_congestion', 40) / 100.0
        weather_risk = layer_scores.get('weather_climate', 35) / 100.0
        doc_risk = layer_scores.get('documentation_complexity', 40) / 100.0
        market_risk = layer_scores.get('market_volatility', 40) / 100.0
        sensitivity = layer_scores.get('cargo_sensitivity', 40) / 100.0
        
        # ====================================================================
        # SIMULATE RANDOM VARIABLES (10,000 scenarios)
        # ====================================================================
        
        # 1. Carrier Delay Factor (Normal distribution)
        # Higher carrier risk = more delay variance
        carrier_delay = np.random.normal(
            loc=carrier_risk,
            scale=0.15 * carrier_risk,
            size=self.n_runs
        )
        carrier_delay = np.clip(carrier_delay, 0, 1.5)  # Reasonable bounds
        
        # 2. Port Congestion Shock (Normal distribution)
        # Multiplier around 1.0, increases with port risk
        port_multiplier = np.random.normal(
            loc=1 + port_risk * 0.3,
            scale=0.05,
            size=self.n_runs
        )
        port_multiplier = np.clip(port_multiplier, 0.8, 1.8)
        
        # 3. Weather Delay (Bernoulli event + Uniform days)
        # Probability increases with weather risk
        weather_prob = 0.2 + 0.3 * weather_risk
        weather_event = np.random.binomial(n=1, p=weather_prob, size=self.n_runs)
        weather_delay_days = np.random.uniform(low=1, high=6, size=self.n_runs)
        weather_delay_days *= weather_event  # Only apply if event occurs
        
        # 4. Documentation Delay (Bernoulli event + fixed days)
        doc_prob = 0.1 + 0.2 * doc_risk
        doc_event = np.random.binomial(n=1, p=doc_prob, size=self.n_runs)
        doc_delay_days = np.random.uniform(low=1, high=4, size=self.n_runs)
        doc_delay_days *= doc_event  # Only apply if event occurs
        
        # 5. Market Shock (Cauchy distribution - heavy tailed)
        # Heavy-tailed distribution to model extreme market events
        market_shock = np.random.standard_cauchy(size=self.n_runs)
        market_shock = market_shock * (0.1 + 0.2 * market_risk) + 1.0
        market_shock = np.clip(market_shock, 0.7, 1.5)  # Reasonable bounds
        
        # 6. Cargo Sensitivity Penalty (Uniform distribution)
        # Additional delay factor based on cargo fragility
        sensitivity_factor = 1 + sensitivity * np.random.uniform(
            low=0.05, high=0.25, size=self.n_runs
        )
        
        # 7. Base Transit Noise (Normal around 1.0)
        # Small random variation in base transit time
        transit_noise = np.random.normal(loc=1.0, scale=0.05, size=self.n_runs)
        transit_noise = np.clip(transit_noise, 0.85, 1.15)
        
        # ====================================================================
        # CALCULATE ETA FOR EACH SCENARIO
        # ====================================================================
        
        # Start with base transit time
        eta_distribution = np.full(self.n_runs, base_transit, dtype=float)
        
        # Apply multiplicative factors
        eta_distribution *= transit_noise
        eta_distribution *= (1 + carrier_delay)
        eta_distribution *= port_multiplier
        eta_distribution *= market_shock
        eta_distribution *= sensitivity_factor
        
        # Add event-based delays (additive)
        eta_distribution += weather_delay_days
        eta_distribution += doc_delay_days
        
        # Ensure ETA is at least 1 day
        eta_distribution = np.clip(eta_distribution, 1, None)
        
        # ====================================================================
        # CALCULATE LOSS FOR EACH SCENARIO
        # ====================================================================
        
        # Base loss calculation
        loss_distribution = cargo_value * (0.01 + sensitivity * 0.1)
        
        # Apply market and port multipliers
        loss_distribution *= market_shock
        loss_distribution *= (port_multiplier - 1 + 1)  # Normalize around 1
        
        # Weather event penalty (15% increase)
        weather_loss_multiplier = np.where(weather_event == 1, 1.15, 1.0)
        loss_distribution *= weather_loss_multiplier
        
        # Documentation event penalty (10% increase)
        doc_loss_multiplier = np.where(doc_event == 1, 1.10, 1.0)
        loss_distribution *= doc_loss_multiplier
        
        # Catastrophic tail events (2% probability)
        catastrophic_prob = 0.02
        catastrophic_event = np.random.binomial(n=1, p=catastrophic_prob, size=self.n_runs)
        catastrophic_multiplier = np.random.uniform(low=2.0, high=4.0, size=self.n_runs)
        catastrophic_multiplier = np.where(catastrophic_event == 1, catastrophic_multiplier, 1.0)
        loss_distribution *= catastrophic_multiplier
        
        # Ensure non-negative losses
        loss_distribution = np.clip(loss_distribution, 0, None)
        
        # ====================================================================
        # CALCULATE STATISTICS
        # ====================================================================
        
        eta_stats = {
            'mean': float(np.mean(eta_distribution)),
            'p50': float(np.percentile(eta_distribution, 50)),
            'p90': float(np.percentile(eta_distribution, 90)),
            'p95': float(np.percentile(eta_distribution, 95)),
            'p99': float(np.percentile(eta_distribution, 99)),
            'min': float(np.min(eta_distribution)),
            'max': float(np.max(eta_distribution)),
            'std': float(np.std(eta_distribution))
        }
        
        loss_stats = {
            'expected_loss': float(np.mean(loss_distribution)),
            'p50_loss': float(np.percentile(loss_distribution, 50)),
            'p90_loss': float(np.percentile(loss_distribution, 90)),
            'p95_loss': float(np.percentile(loss_distribution, 95)),
            'p99_loss': float(np.percentile(loss_distribution, 99)),
            'max_loss': float(np.max(loss_distribution)),
            'var_95': float(np.percentile(loss_distribution, 95)),  # Value at Risk
            'cvar_95': float(np.mean(loss_distribution[loss_distribution >= np.percentile(loss_distribution, 95)])),  # Conditional VaR
            'probability_of_loss': float(np.sum(loss_distribution > cargo_value * 0.05) / self.n_runs)
        }
        
        # ====================================================================
        # CREATE HISTOGRAMS (30 bins)
        # ====================================================================
        
        # ETA histogram
        eta_hist_counts, eta_hist_edges = np.histogram(eta_distribution, bins=30)
        eta_histogram = {
            'counts': eta_hist_counts.tolist(),
            'bin_edges': eta_hist_edges.tolist(),
            'bin_centers': [(eta_hist_edges[i] + eta_hist_edges[i+1]) / 2 
                           for i in range(len(eta_hist_edges) - 1)]
        }
        
        # Loss histogram
        loss_hist_counts, loss_hist_edges = np.histogram(loss_distribution, bins=30)
        loss_histogram = {
            'counts': loss_hist_counts.tolist(),
            'bin_edges': loss_hist_edges.tolist(),
            'bin_centers': [(loss_hist_edges[i] + loss_hist_edges[i+1]) / 2 
                           for i in range(len(loss_hist_edges) - 1)]
        }
        
        # ====================================================================
        # RISK METRICS
        # ====================================================================
        
        # Probability of significant delay (> 150% of expected)
        expected_eta = base_transit
        prob_significant_delay = float(np.sum(eta_distribution > expected_eta * 1.5) / self.n_runs)
        
        # Probability of catastrophic loss (> 20% of cargo value)
        prob_catastrophic = float(np.sum(loss_distribution > cargo_value * 0.2) / self.n_runs)
        
        # Event frequencies
        weather_frequency = float(np.sum(weather_event) / self.n_runs)
        doc_frequency = float(np.sum(doc_event) / self.n_runs)
        cat_frequency = float(np.sum(catastrophic_event) / self.n_runs)
        
        # ====================================================================
        # GENERATE INSIGHTS
        # ====================================================================
        
        insights = self._generate_insights(
            eta_stats, loss_stats, base_transit, cargo_value,
            prob_significant_delay, prob_catastrophic
        )
        
        recommendations = self._generate_recommendations(
            eta_stats, loss_stats, base_transit, cargo_value,
            weather_frequency, doc_frequency
        )
        
        # ====================================================================
        # RETURN RESULTS
        # ====================================================================
        
        return {
            'runs': self.n_runs,
            'base_transit_time': base_transit,
            'cargo_value': cargo_value,
            
            # ETA Analysis
            'eta_distribution': eta_distribution.tolist()[:100],  # Sample 100 for display
            'eta_stats': eta_stats,
            
            # Loss Analysis
            'loss_distribution': loss_distribution.tolist()[:100],  # Sample 100 for display
            'loss_stats': loss_stats,
            
            # Distribution Shapes
            'distribution_shapes': {
                'eta_histogram': eta_histogram,
                'loss_histogram': loss_histogram
            },
            
            # Risk Metrics
            'risk_metrics': {
                'prob_significant_delay': round(prob_significant_delay * 100, 2),
                'prob_catastrophic_loss': round(prob_catastrophic * 100, 2),
                'weather_event_frequency': round(weather_frequency * 100, 2),
                'doc_delay_frequency': round(doc_frequency * 100, 2),
                'catastrophic_event_frequency': round(cat_frequency * 100, 2)
            },
            
            # Insights and Recommendations
            'insights': insights,
            'recommendations': recommendations,
            
            # Summary
            'summary': self._generate_summary(eta_stats, loss_stats, base_transit)
        }
    
    def _generate_insights(self, eta_stats: Dict, loss_stats: Dict, 
                          base_transit: float, cargo_value: float,
                          prob_delay: float, prob_catastrophic: float) -> List[str]:
        """Generate analytical insights from simulation results"""
        
        insights = []
        
        # ETA insights
        eta_variance = eta_stats['p95'] - eta_stats['p50']
        if eta_variance > base_transit * 0.3:
            insights.append(
                f"High ETA variability detected: P95 ({eta_stats['p95']:.1f} days) "
                f"is {(eta_variance/base_transit*100):.0f}% longer than P50 ({eta_stats['p50']:.1f} days)"
            )
        
        if prob_delay > 0.25:
            insights.append(
                f"Significant delay risk: {prob_delay*100:.1f}% probability of delays "
                f"exceeding 150% of expected transit time"
            )
        
        # Loss insights
        if loss_stats['expected_loss'] > cargo_value * 0.05:
            insights.append(
                f"Expected loss of ${loss_stats['expected_loss']:,.0f} represents "
                f"{(loss_stats['expected_loss']/cargo_value*100):.1f}% of cargo value"
            )
        
        if prob_catastrophic > 0.05:
            insights.append(
                f"Elevated catastrophic risk: {prob_catastrophic*100:.1f}% probability "
                f"of losses exceeding 20% of cargo value"
            )
        
        # Tail risk insights
        tail_ratio = loss_stats['p99_loss'] / loss_stats['expected_loss']
        if tail_ratio > 3:
            insights.append(
                f"Heavy-tailed loss distribution: P99 loss is {tail_ratio:.1f}x "
                f"higher than expected loss, indicating extreme event risk"
            )
        
        return insights
    
    def _generate_recommendations(self, eta_stats: Dict, loss_stats: Dict,
                                 base_transit: float, cargo_value: float,
                                 weather_freq: float, doc_freq: float) -> List[str]:
        """Generate actionable recommendations based on simulation"""
        
        recommendations = []
        
        # ETA recommendations
        if eta_stats['p95'] > base_transit * 1.4:
            recommendations.append(
                "⚠️ Consider buffer time: Add at least "
                f"{(eta_stats['p95'] - base_transit):.0f} days to planned schedule"
            )
        
        if weather_freq > 0.3:
            recommendations.append(
                f"• Weather risk is significant ({weather_freq*100:.0f}% of scenarios): "
                "Consider alternative timing or routing"
            )
        
        if doc_freq > 0.2:
            recommendations.append(
                f"• Documentation delays occur in {doc_freq*100:.0f}% of scenarios: "
                "Engage customs broker proactively"
            )
        
        # Loss recommendations
        if loss_stats['var_95'] > cargo_value * 0.15:
            recommendations.append(
                "⚠️ Upgrade insurance: VaR(95%) of "
                f"${loss_stats['var_95']:,.0f} suggests inadequate coverage"
            )
        
        if loss_stats['probability_of_loss'] > 0.5:
            recommendations.append(
                "• High probability of measurable loss: Implement enhanced "
                "monitoring and quality controls"
            )
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _generate_summary(self, eta_stats: Dict, loss_stats: Dict, 
                         base_transit: float) -> str:
        """Generate executive summary of simulation results"""
        
        eta_range = eta_stats['p95'] - eta_stats['p50']
        risk_level = 'HIGH' if eta_range > base_transit * 0.3 else 'MODERATE' if eta_range > base_transit * 0.15 else 'LOW'
        
        return (
            f"Monte Carlo simulation ({self.n_runs:,} scenarios) projects "
            f"median ETA of {eta_stats['p50']:.1f} days with {risk_level} variability. "
            f"Expected financial loss: ${loss_stats['expected_loss']:,.0f} "
            f"(P95: ${loss_stats['p95_loss']:,.0f}). "
            f"Recommend planning for {eta_stats['p90']:.1f}-day timeline to achieve 90% confidence."
        )






