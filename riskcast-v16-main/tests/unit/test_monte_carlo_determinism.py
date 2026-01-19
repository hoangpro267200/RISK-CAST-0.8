"""
Unit tests for Monte Carlo Engine Determinism (RC-D001)

CRITICAL: These tests verify that the risk engine produces deterministic
outputs - same input must always produce same output.
"""
import pytest
import numpy as np
from app.core.engine.monte_carlo_v22 import MonteCarloEngineV22


class TestMonteCarloDeterminism:
    """Test suite for Monte Carlo determinism"""
    
    def test_deterministic_with_explicit_seed(self):
        """
        Test that explicit seed produces identical results.
        
        Reproduces: RC-D001
        """
        transport = {'transit_time': 14}
        cargo = {'insurance_value': 100000}
        layer_scores = {
            'carrier_performance': 50,
            'port_congestion': 40,
            'weather_climate': 35,
            'documentation_complexity': 40,
            'market_volatility': 40,
            'cargo_sensitivity': 40
        }
        
        # Run simulation twice with same seed
        engine1 = MonteCarloEngineV22(n_runs=1000, random_seed=42)
        result1 = engine1.run_simulation(transport, cargo, layer_scores)
        
        engine2 = MonteCarloEngineV22(n_runs=1000, random_seed=42)
        result2 = engine2.run_simulation(transport, cargo, layer_scores)
        
        # Results must be identical
        assert result1['eta_stats']['mean'] == result2['eta_stats']['mean']
        assert result1['loss_stats']['expected_loss'] == result2['loss_stats']['expected_loss']
        assert result1['random_seed'] == result2['random_seed'] == 42
    
    def test_deterministic_without_seed(self):
        """
        Test that deterministic seed generation produces identical results.
        
        When no seed is provided, engine generates seed from input hash.
        Same input → same seed → same output.
        
        Reproduces: RC-D001
        """
        transport = {'transit_time': 20}
        cargo = {'insurance_value': 50000}
        layer_scores = {
            'carrier_performance': 60,
            'port_congestion': 50,
            'weather_climate': 45,
            'documentation_complexity': 30,
            'market_volatility': 35,
            'cargo_sensitivity': 55
        }
        
        # Run simulation twice without explicit seed
        engine1 = MonteCarloEngineV22(n_runs=1000)
        result1 = engine1.run_simulation(transport, cargo, layer_scores)
        
        engine2 = MonteCarloEngineV22(n_runs=1000)
        result2 = engine2.run_simulation(transport, cargo, layer_scores)
        
        # Results must be identical (deterministic seed from input)
        assert result1['eta_stats']['mean'] == result2['eta_stats']['mean']
        assert result1['loss_stats']['expected_loss'] == result2['loss_stats']['expected_loss']
        assert result1['random_seed'] == result2['random_seed']  # Same seed generated
        assert 'random_seed' in result1  # Seed must be saved
    
    def test_different_inputs_produce_different_results(self):
        """
        Test that different inputs produce different results.
        
        This ensures the engine is actually using the input data,
        not just returning constants.
        """
        base_transport = {'transit_time': 14}
        base_cargo = {'insurance_value': 100000}
        base_layers = {
            'carrier_performance': 50,
            'port_congestion': 40,
            'weather_climate': 35,
            'documentation_complexity': 40,
            'market_volatility': 40,
            'cargo_sensitivity': 40
        }
        
        # Base case
        engine1 = MonteCarloEngineV22(n_runs=1000)
        result1 = engine1.run_simulation(base_transport, base_cargo, base_layers)
        
        # Different transit time
        transport2 = {'transit_time': 30}
        engine2 = MonteCarloEngineV22(n_runs=1000)
        result2 = engine2.run_simulation(transport2, base_cargo, base_layers)
        
        # Results should differ
        assert result1['eta_stats']['mean'] != result2['eta_stats']['mean']
        assert result1['random_seed'] != result2['random_seed']  # Different seeds
    
    def test_seed_generation_consistency(self):
        """
        Test that seed generation is consistent for same input.
        """
        transport = {'transit_time': 14}
        cargo = {'insurance_value': 100000}
        layer_scores = {
            'carrier_performance': 50,
            'port_congestion': 40,
            'weather_climate': 35,
            'documentation_complexity': 40,
            'market_volatility': 40,
            'cargo_sensitivity': 40
        }
        
        input_data = {
            'transport': transport,
            'cargo': cargo,
            'layer_scores': layer_scores
        }
        
        # Generate seed multiple times
        seed1 = MonteCarloEngineV22._generate_deterministic_seed(input_data)
        seed2 = MonteCarloEngineV22._generate_deterministic_seed(input_data)
        seed3 = MonteCarloEngineV22._generate_deterministic_seed(input_data)
        
        # Seeds must be identical
        assert seed1 == seed2 == seed3
        assert isinstance(seed1, int)
        assert 0 <= seed1 < 2**31  # Valid numpy seed range
