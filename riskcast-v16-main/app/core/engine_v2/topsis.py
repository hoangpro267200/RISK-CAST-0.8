"""
RISKCAST Engine v2 - TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)
Multi-criteria decision making for alternative ranking
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TOPSISResult:
    """TOPSIS analysis result"""
    closeness_coefficient: float  # 0-1, higher is better
    distance_to_ideal_positive: float
    distance_to_ideal_negative: float
    ranking: int
    normalized_scores: Dict[str, float]


class TOPSISSolver:
    """TOPSIS solver for multi-criteria decision analysis"""
    
    def __init__(self, alternatives: Optional[List[Dict[str, float]]] = None,
                 criteria_weights: Optional[Dict[str, float]] = None,
                 criteria_directions: Optional[Dict[str, str]] = None):
        """
        Initialize TOPSIS solver
        
        Args:
            alternatives: List of alternative solutions (each is a dict of criterion:value)
            criteria_weights: Weights for each criterion (from FAHP)
            criteria_directions: "maximize" or "minimize" for each criterion
        """
        self.alternatives = alternatives or []
        self.criteria_weights = criteria_weights or {}
        self.criteria_directions = criteria_directions or {}
        self.decision_matrix = None
        self.weighted_matrix = None
        self.ideal_positive = None
        self.ideal_negative = None
    
    def build_decision_matrix(self, alternatives: List[Dict[str, float]],
                             criteria: List[str]) -> np.ndarray:
        """
        Build decision matrix from alternatives
        
        Args:
            alternatives: List of alternative solutions
            criteria: List of criterion names
            
        Returns:
            Decision matrix (n alternatives × m criteria)
        """
        n = len(alternatives)
        m = len(criteria)
        
        matrix = np.zeros((n, m))
        
        for i, alt in enumerate(alternatives):
            for j, criterion in enumerate(criteria):
                matrix[i, j] = alt.get(criterion, 0.0)
        
        self.decision_matrix = matrix
        return matrix
    
    def normalize_matrix(self, method: str = "vector") -> np.ndarray:
        """
        Normalize decision matrix
        
        Args:
            method: Normalization method ("vector" or "min_max")
            
        Returns:
            Normalized matrix
        """
        if self.decision_matrix is None:
            raise ValueError("Decision matrix not built")
        
        matrix = self.decision_matrix
        n, m = matrix.shape
        
        if method == "vector":
            # Vector normalization (Euclidean norm)
            norms = np.sqrt(np.sum(matrix ** 2, axis=0, keepdims=True))
            norms[norms == 0] = 1  # Avoid division by zero
            normalized = matrix / norms
        elif method == "min_max":
            # Min-max normalization
            min_vals = np.min(matrix, axis=0, keepdims=True)
            max_vals = np.max(matrix, axis=0, keepdims=True)
            ranges = max_vals - min_vals
            ranges[ranges == 0] = 1  # Avoid division by zero
            normalized = (matrix - min_vals) / ranges
        else:
            raise ValueError(f"Unknown normalization method: {method}")
        
        return normalized
    
    def apply_weights(self, normalized_matrix: np.ndarray,
                     criteria: List[str], weights: Dict[str, float]) -> np.ndarray:
        """
        Apply criterion weights to normalized matrix
        
        Args:
            normalized_matrix: Normalized decision matrix
            criteria: List of criterion names
            weights: Weights for each criterion
            
        Returns:
            Weighted normalized matrix
        """
        weighted = normalized_matrix.copy()
        
        for j, criterion in enumerate(criteria):
            weight = weights.get(criterion, 1.0 / len(criteria))  # Equal weight if not specified
            weighted[:, j] *= weight
        
        self.weighted_matrix = weighted
        return weighted
    
    def find_ideal_solutions(self, weighted_matrix: np.ndarray,
                            criteria: List[str]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Find ideal positive and negative solutions
        
        Args:
            weighted_matrix: Weighted normalized matrix
            criteria: List of criterion names
            
        Returns:
            Tuple of (ideal_positive, ideal_negative) vectors
        """
        n, m = weighted_matrix.shape
        ideal_positive = np.zeros(m)
        ideal_negative = np.zeros(m)
        
        for j, criterion in enumerate(criteria):
            direction = self.criteria_directions.get(criterion, "maximize")
            
            if direction == "maximize":
                # For maximization: ideal positive = max, ideal negative = min
                ideal_positive[j] = np.max(weighted_matrix[:, j])
                ideal_negative[j] = np.min(weighted_matrix[:, j])
            else:  # minimize
                # For minimization: ideal positive = min, ideal negative = max
                ideal_positive[j] = np.min(weighted_matrix[:, j])
                ideal_negative[j] = np.max(weighted_matrix[:, j])
        
        self.ideal_positive = ideal_positive
        self.ideal_negative = ideal_negative
        
        return ideal_positive, ideal_negative
    
    def calculate_distances(self, weighted_matrix: np.ndarray,
                          ideal_positive: np.ndarray,
                          ideal_negative: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate distances to ideal solutions
        
        Args:
            weighted_matrix: Weighted normalized matrix
            ideal_positive: Ideal positive solution
            ideal_negative: Ideal negative solution
            
        Returns:
            Tuple of (distances_to_positive, distances_to_negative)
        """
        n = weighted_matrix.shape[0]
        dist_positive = np.zeros(n)
        dist_negative = np.zeros(n)
        
        for i in range(n):
            # Euclidean distance
            dist_positive[i] = np.sqrt(np.sum((weighted_matrix[i] - ideal_positive) ** 2))
            dist_negative[i] = np.sqrt(np.sum((weighted_matrix[i] - ideal_negative) ** 2))
        
        return dist_positive, dist_negative
    
    def calculate_closeness(self, dist_positive: np.ndarray,
                          dist_negative: np.ndarray) -> np.ndarray:
        """
        Calculate closeness coefficient (0-1, higher is better)
        
        Args:
            dist_positive: Distances to ideal positive
            dist_negative: Distances to ideal negative
            
        Returns:
            Closeness coefficient array
        """
        total = dist_positive + dist_negative
        total[total == 0] = 1e-10  # Avoid division by zero
        closeness = dist_negative / total
        return closeness
    
    def solve(self, alternatives: List[Dict[str, float]],
              criteria: List[str],
              weights: Dict[str, float],
              criteria_directions: Optional[Dict[str, str]] = None) -> TOPSISResult:
        """
        Complete TOPSIS solving process
        
        Args:
            alternatives: List of alternative solutions
            criteria: List of criterion names
            weights: Weights for each criterion
            criteria_directions: "maximize" or "minimize" for each criterion
            
        Returns:
            TOPSISResult object
        """
        if criteria_directions:
            self.criteria_directions = criteria_directions
        
        # Build decision matrix
        matrix = self.build_decision_matrix(alternatives, criteria)
        
        # Normalize
        normalized = self.normalize_matrix(method="vector")
        
        # Apply weights
        weighted = self.apply_weights(normalized, criteria, weights)
        
        # Find ideal solutions
        ideal_pos, ideal_neg = self.find_ideal_solutions(weighted, criteria)
        
        # Calculate distances
        dist_pos, dist_neg = self.calculate_distances(weighted, ideal_pos, ideal_neg)
        
        # Calculate closeness coefficient
        closeness = self.calculate_closeness(dist_pos, dist_neg)
        
        # For single alternative case, return the closeness coefficient
        if len(alternatives) == 1:
            score = float(closeness[0])
            result = TOPSISResult(
                closeness_coefficient=score,
                distance_to_ideal_positive=float(dist_pos[0]),
                distance_to_ideal_negative=float(dist_neg[0]),
                ranking=1,
                normalized_scores={criteria[i]: float(weighted[0, i]) for i in range(len(criteria))}
            )
        else:
            # Rank alternatives (higher closeness = better)
            rankings = np.argsort(closeness)[::-1]  # Descending order
            rank = int(np.where(rankings == 0)[0][0]) + 1
            
            result = TOPSISResult(
                closeness_coefficient=float(closeness[0]),
                distance_to_ideal_positive=float(dist_pos[0]),
                distance_to_ideal_negative=float(dist_neg[0]),
                ranking=rank,
                normalized_scores={criteria[i]: float(weighted[0, i]) for i in range(len(criteria))}
            )
        
        return result
















