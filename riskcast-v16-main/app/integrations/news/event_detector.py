"""
Risk Event Detection using NLP

Uses spaCy and custom rules for entity extraction
"""

from typing import Dict, List, Tuple
import re

from app.core.logging import get_logger


logger = get_logger(__name__)


class RiskEventDetector:
    """
    NLP-based risk event detector.
    """
    
    def __init__(self):
        self._nlp = None
        self._load_nlp()
    
    def _load_nlp(self):
        """Load spaCy model."""
        try:
            import spacy
            self._nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded for event detection")
        except Exception as e:
            logger.warning(f"Could not load spaCy: {e}")
            self._nlp = None
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities from text.
        """
        entities = {
            "locations": [],
            "organizations": [],
            "vessels": [],
            "dates": [],
            "monetary": []
        }
        
        if not self._nlp:
            return entities
        
        doc = self._nlp(text)
        
        for ent in doc.ents:
            if ent.label_ in ["GPE", "LOC"]:
                entities["locations"].append(ent.text)
            elif ent.label_ == "ORG":
                entities["organizations"].append(ent.text)
            elif ent.label_ == "DATE":
                entities["dates"].append(ent.text)
            elif ent.label_ == "MONEY":
                entities["monetary"].append(ent.text)
        
        # Custom vessel name detection
        vessel_pattern = r'\b(?:M/?V|SS|MT|MV)\s+[A-Z][A-Za-z\s]+\b'
        vessels = re.findall(vessel_pattern, text)
        entities["vessels"].extend(vessels)
        
        # IMO number detection
        imo_pattern = r'\bIMO\s*[:-]?\s*(\d{7})\b'
        imo_matches = re.findall(imo_pattern, text, re.IGNORECASE)
        for imo in imo_matches:
            entities["vessels"].append(f"IMO {imo}")
        
        return entities
    
    def calculate_sentiment(self, text: str) -> Tuple[str, float]:
        """
        Calculate text sentiment.
        
        Returns: (label, score) where label is POSITIVE/NEGATIVE/NEUTRAL
        """
        if not self._nlp:
            return "NEUTRAL", 0.0
        
        # Simple keyword-based sentiment
        negative_words = [
            "attack", "collision", "damage", "disaster", "fire", "sinking",
            "piracy", "strike", "closure", "delay", "sanction", "crash",
            "explosion", "casualty", "loss", "theft", "storm", "typhoon"
        ]
        positive_words = [
            "recovery", "resolved", "reopened", "safe", "successful",
            "improvement", "growth", "record"
        ]
        
        text_lower = text.lower()
        
        neg_count = sum(1 for w in negative_words if w in text_lower)
        pos_count = sum(1 for w in positive_words if w in text_lower)
        
        if neg_count > pos_count + 2:
            return "NEGATIVE", -0.5 - min(neg_count * 0.1, 0.4)
        elif pos_count > neg_count + 2:
            return "POSITIVE", 0.5 + min(pos_count * 0.1, 0.4)
        else:
            return "NEUTRAL", 0.0
