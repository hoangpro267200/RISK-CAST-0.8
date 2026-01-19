"""
RISKCAST Engine v2 - Fuzzy Analytic Hierarchy Process (FAHP)
Implements FAHP with triangular fuzzy numbers for risk factor weighting
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import math


@dataclass
class FuzzyTriangular:
    """Triangular fuzzy number (l, m, u)"""
    l: float  # Lower bound
    m: float  # Most likely
    u: float  # Upper bound
    
    def __post_init__(self):
        assert self.l <= self.m <= self.u, "Triangular fuzzy number must satisfy l <= m <= u"
    
    def defuzzify(self) -> float:
        """Convert fuzzy number to crisp value (centroid method)"""
        return (self.l + 2 * self.m + self.u) / 4.0
    
    def __add__(self, other):
        """Addition of two fuzzy triangular numbers"""
        if isinstance(other, FuzzyTriangular):
            return FuzzyTriangular(
                l=self.l + other.l,
                m=self.m + other.m,
                u=self.u + other.u
            )
        return NotImplemented
    
    def __mul__(self, other):
        """Multiplication by scalar or another fuzzy number"""
        if isinstance(other, (int, float)):
            return FuzzyTriangular(
                l=self.l * other,
                m=self.m * other,
                u=self.u * other
            )
        elif isinstance(other, FuzzyTriangular):
            return FuzzyTriangular(
                l=self.l * other.l,
                m=self.m * other.m,
                u=self.u * other.u
            )
        return NotImplemented


class FAHPSolver:
    """Fuzzy AHP solver for risk factor weighting"""
    
    # Linguistic scale for pairwise comparisons (Saaty scale 1-9, fuzzified)
    FUZZY_SCALE = {
        1: FuzzyTriangular(1, 1, 1),           # Equal importance
        2: FuzzyTriangular(1, 2, 3),           # Weak importance
        3: FuzzyTriangular(2, 3, 4),           # Moderate importance
        4: FuzzyTriangular(3, 4, 5),           # Moderate to strong
        5: FuzzyTriangular(4, 5, 6),           # Strong importance
        6: FuzzyTriangular(5, 6, 7),           # Strong to very strong
        7: FuzzyTriangular(6, 7, 8),           # Very strong importance
        8: FuzzyTriangular(7, 8, 9),           # Very strong to extreme
        9: FuzzyTriangular(8, 9, 9),           # Extreme importance
    }
    
    # Risk factors for FAHP analysis
    RISK_FACTORS = [
        "delay",
        "port",
        "climate",
        "carrier",
        "esg",
        "equipment"
    ]
    
    def __init__(self, comparison_matrix: Optional[np.ndarray] = None):
        """
        Initialize FAHP solver
        
        Args:
            comparison_matrix: Optional pre-computed comparison matrix (n×n)
        """
        self.comparison_matrix = comparison_matrix
        self.n = len(self.RISK_FACTORS)
        self.fuzzy_weights = None
        self.crisp_weights = None
        self.consistency_ratio = None
    
    def build_comparison_matrix(self, comparisons: Dict[str, Dict[str, int]]) -> np.ndarray:
        """
        Build pairwise comparison matrix from user inputs
        
        Args:
            comparisons: Dict like {"delay": {"port": 5, "climate": 3}, ...}
            
        Returns:
            Comparison matrix (n×n)
        """
        matrix = np.ones((self.n, self.n))
        
        factor_idx = {factor: i for i, factor in enumerate(self.RISK_FACTORS)}
        
        for factor1, comparisons_dict in comparisons.items():
            if factor1 not in factor_idx:
                continue
            
            i = factor_idx[factor1]
            for factor2, value in comparisons_dict.items():
                if factor2 not in factor_idx:
                    continue
                
                j = factor_idx[factor2]
                # Store the comparison value
                matrix[i, j] = value
                # Reciprocal for symmetric position
                if value > 0:
                    matrix[j, i] = 1.0 / value
        
        self.comparison_matrix = matrix
        return matrix
    
    def build_default_comparison_matrix(self, risk_context: Dict[str, float]) -> np.ndarray:
        """
        Build comparison matrix automatically based on risk context
        
        Args:
            risk_context: Dictionary with risk factor values
            
        Returns:
            Comparison matrix
        """
        matrix = np.ones((self.n, self.n))
        factor_idx = {factor: i for i, factor in enumerate(self.RISK_FACTORS)}
        
        # Get values for each factor (normalized to 1-9 scale)
        factor_values = {}
        for factor in self.RISK_FACTORS:
            if factor in risk_context:
                # Map risk value (0-1) to Saaty scale (1-9)
                value = risk_context[factor]
                factor_values[factor] = 1 + value * 8  # Scale to 1-9
            else:
                factor_values[factor] = 1.0
        
        # Build comparison matrix based on relative importance
        for i, factor1 in enumerate(self.RISK_FACTORS):
            for j, factor2 in enumerate(self.RISK_FACTORS):
                if i == j:
                    matrix[i, j] = 1.0
                else:
                    ratio = factor_values[factor1] / factor_values[factor2]
                    # Clamp to Saaty scale 1-9
                    ratio = max(1/9, min(9, ratio))
                    matrix[i, j] = ratio
                    if j > i:  # Set reciprocal
                        matrix[j, i] = 1.0 / ratio
        
        self.comparison_matrix = matrix
        return matrix
    
    def compute_fuzzy_weights(self) -> List[FuzzyTriangular]:
        """
        Compute fuzzy weights using geometric mean method
        
        Returns:
            List of fuzzy triangular weights
        """
        if self.comparison_matrix is None:
            raise ValueError("Comparison matrix not set")
        
        n = self.n
        fuzzy_weights = []
        
        # Step 1: Convert crisp comparison matrix to fuzzy
        fuzzy_matrix = []
        for i in range(n):
            row = []
            for j in range(n):
                crisp_value = self.comparison_matrix[i, j]
                # Find closest fuzzy scale
                fuzzy_num = self._crisp_to_fuzzy(crisp_value)
                row.append(fuzzy_num)
            fuzzy_matrix.append(row)
        
        # Step 2: Geometric mean for each row
        geometric_means = []
        for i in range(n):
            gm_l = 1.0
            gm_m = 1.0
            gm_u = 1.0
            
            for j in range(n):
                fuzzy_num = fuzzy_matrix[i][j]
                gm_l *= fuzzy_num.l
                gm_m *= fuzzy_num.m
                gm_u *= fuzzy_num.u
            
            # nth root
            gm_l = gm_l ** (1.0 / n)
            gm_m = gm_m ** (1.0 / n)
            gm_u = gm_u ** (1.0 / n)
            
            geometric_means.append(FuzzyTriangular(gm_l, gm_m, gm_u))
        
        # Step 3: Normalize weights
        sum_l = sum(gm.l for gm in geometric_means)
        sum_m = sum(gm.m for gm in geometric_means)
        sum_u = sum(gm.u for gm in geometric_means)
        
        for gm in geometric_means:
            normalized = FuzzyTriangular(
                l=gm.l / sum_u,  # Divide by max sum for lower bound
                m=gm.m / sum_m,  # Divide by mean sum for middle
                u=gm.u / sum_l   # Divide by min sum for upper bound
            )
            fuzzy_weights.append(normalized)
        
        self.fuzzy_weights = fuzzy_weights
        return fuzzy_weights
    
    def compute_crisp_weights(self) -> Dict[str, float]:
        """
        Compute crisp (defuzzified) weights
        
        Returns:
            Dictionary mapping factor names to weights (0-1, sum to 1)
        """
        if self.fuzzy_weights is None:
            self.compute_fuzzy_weights()
        
        crisp_weights_list = [fw.defuzzify() for fw in self.fuzzy_weights]
        
        # Normalize to sum to 1
        total = sum(crisp_weights_list)
        if total > 0:
            crisp_weights_list = [w / total for w in crisp_weights_list]
        
        crisp_weights = {
            self.RISK_FACTORS[i]: crisp_weights_list[i]
            for i in range(self.n)
        }
        
        self.crisp_weights = crisp_weights
        return crisp_weights
    
    def check_consistency(self) -> float:
        """
        Check consistency ratio (CR) - should be < 0.1
        
        Returns:
            Consistency ratio
        """
        if self.comparison_matrix is None:
            raise ValueError("Comparison matrix not set")
        
        n = self.n
        matrix = self.comparison_matrix
        
        # Compute eigenvalues
        eigenvalues, _ = np.linalg.eig(matrix)
        lambda_max = max(eigenvalues.real)
        
        # Consistency Index (CI)
        ci = (lambda_max - n) / (n - 1)
        
        # Random Index (RI) - from Saaty's table
        ri_table = {
            1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12,
            6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49
        }
        ri = ri_table.get(n, 1.49)
        
        # Consistency Ratio
        if ri > 0:
            cr = ci / ri
        else:
            cr = 0.0
        
        self.consistency_ratio = cr
        return cr
    
    def _crisp_to_fuzzy(self, crisp_value: float) -> FuzzyTriangular:
        """Convert crisp value to closest fuzzy triangular number"""
        # Find closest scale value
        min_diff = float('inf')
        closest_scale = 1
        
        for scale, fuzzy_num in self.FUZZY_SCALE.items():
            diff = abs(crisp_value - fuzzy_num.m)
            if diff < min_diff:
                min_diff = diff
                closest_scale = scale
        
        return self.FUZZY_SCALE[closest_scale]
    
    def solve(self, risk_context: Optional[Dict[str, float]] = None,
              comparisons: Optional[Dict[str, Dict[str, int]]] = None) -> Dict[str, float]:
        """
        Complete FAHP solving process
        
        Args:
            risk_context: Optional risk context for auto-comparison matrix
            comparisons: Optional manual comparisons
            
        Returns:
            Dictionary of factor weights
        """
        # Build comparison matrix
        if comparisons:
            self.build_comparison_matrix(comparisons)
        elif risk_context:
            self.build_default_comparison_matrix(risk_context)
        else:
            # Use equal weights as default
            self.comparison_matrix = np.ones((self.n, self.n))
        
        # Compute weights
        self.compute_fuzzy_weights()
        weights = self.compute_crisp_weights()
        
        # Check consistency
        cr = self.check_consistency()
        
        if cr > 0.1:
            # Warning: consistency ratio too high
            pass  # Could raise warning here
        
        return weights
















