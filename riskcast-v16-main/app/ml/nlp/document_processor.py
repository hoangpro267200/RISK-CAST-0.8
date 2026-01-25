"""
NLP Document Processing

Features:
1. Document classification
2. Key information extraction
3. Sentiment analysis
4. Summarization
5. Issue detection
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

try:
    import spacy
    from spacy.matcher import Matcher
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    spacy = None

try:
    from transformers import pipeline
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from app.core.logging import get_logger


logger = get_logger(__name__)


class DocumentType(str, Enum):
    """Document types for classification."""
    BILL_OF_LADING = "bill_of_lading"
    COMMERCIAL_INVOICE = "commercial_invoice"
    PACKING_LIST = "packing_list"
    INSURANCE_CERTIFICATE = "insurance_certificate"
    CLAIM_REPORT = "claim_report"
    SURVEY_REPORT = "survey_report"
    CUSTOMS_DECLARATION = "customs_declaration"
    UNKNOWN = "unknown"


@dataclass
class ExtractedEntity:
    """Extracted entity from document."""
    entity_type: str
    value: str
    confidence: float
    start_pos: int
    end_pos: int
    context: str = ""


@dataclass
class DocumentAnalysis:
    """Complete document analysis result."""
    document_type: DocumentType
    type_confidence: float
    entities: List[ExtractedEntity] = field(default_factory=list)
    key_values: Dict[str, str] = field(default_factory=dict)
    summary: Optional[str] = None
    sentiment: Optional[Dict[str, Any]] = None
    flags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DocumentProcessor:
    """
    NLP-based document processor for insurance documents.
    
    Uses spaCy for NER and custom patterns for domain-specific extraction.
    """
    
    def __init__(self):
        """Initialize document processor."""
        self.nlp = None
        self.matcher = None
        self.sentiment_analyzer = None
        
        # Load models if available
        if SPACY_AVAILABLE:
            self._load_spacy_model()
        else:
            logger.warning("spaCy not available. Install with: pip install spacy && python -m spacy download en_core_web_sm")
        
        if TRANSFORMERS_AVAILABLE:
            self._load_sentiment_model()
        else:
            logger.warning("Transformers not available. Install with: pip install transformers torch")
        
        # Document classification patterns
        self.doc_type_patterns = {
            DocumentType.BILL_OF_LADING: [
                r"bill of lading", r"\bb/?l\b", r"shipper", r"consignee",
                r"vessel", r"port of loading", r"port of discharge",
                r"notify party", r"freight collect", r"laden on board"
            ],
            DocumentType.COMMERCIAL_INVOICE: [
                r"commercial invoice", r"invoice no", r"unit price",
                r"total amount", r"terms of sale", r"incoterms",
                r"exporter", r"importer", r"payment terms"
            ],
            DocumentType.PACKING_LIST: [
                r"packing list", r"gross weight", r"net weight",
                r"package no", r"dimensions", r"marks and numbers",
                r"carton", r"pallet"
            ],
            DocumentType.INSURANCE_CERTIFICATE: [
                r"insurance certificate", r"policy number", r"insured value",
                r"sum insured", r"coverage", r"underwriters"
            ],
            DocumentType.CLAIM_REPORT: [
                r"claim", r"loss", r"damage", r"incident",
                r"survey", r"assessment", r"casualty",
                r"date of loss", r"cause of loss"
            ],
            DocumentType.SURVEY_REPORT: [
                r"survey report", r"surveyor", r"inspection",
                r"findings", r"recommendations", r"condition",
                r"observed damage", r"extent of loss"
            ],
            DocumentType.CUSTOMS_DECLARATION: [
                r"customs declaration", r"entry number", r"tariff",
                r"duty", r"hs code", r"declared value"
            ]
        }
        
        # Key field extraction patterns
        self.field_patterns = {
            "policy_number": r"(?:policy\s*(?:no|number|#)?[:\s]*)([A-Z0-9\-]{5,20})",
            "claim_number": r"(?:claim\s*(?:no|number|#)?[:\s]*)([A-Z0-9\-]{5,20})",
            "invoice_number": r"(?:invoice\s*(?:no|number|#)?[:\s]*)([A-Z0-9\-]{5,20})",
            "bl_number": r"(?:b/?l\s*(?:no|number|#)?[:\s]*)([A-Z0-9\-]{5,20})",
            "container_number": r"\b([A-Z]{4}\d{7})\b",
            "vessel_name": r"(?:vessel|ship|m/?v)[:\s]*([A-Z][A-Za-z\s]{2,30})",
            "port_code": r"\b([A-Z]{2}[A-Z]{3})\b",  # UN/LOCODE format
            "amount": r"(?:USD|EUR|GBP|total)?\s*[$€£]?\s*([\d,]+\.?\d*)\s*(?:USD|EUR|GBP)?",
            "date": r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})",
            "weight": r"(\d+\.?\d*)\s*(?:kg|kgs|mt|mts|tons?|lbs)",
            "email": r"\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b",
            "phone": r"\+?\d[\d\s\-\(\)]{8,20}",
        }
    
    def _load_spacy_model(self):
        """Load spaCy model for NER."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            self._add_custom_patterns()
            logger.info("spaCy model loaded successfully")
        except OSError:
            logger.warning("spaCy model not found. Attempting to download...")
            try:
                import subprocess
                subprocess.run(
                    ["python", "-m", "spacy", "download", "en_core_web_sm"],
                    check=True
                )
                self.nlp = spacy.load("en_core_web_sm")
                self._add_custom_patterns()
                logger.info("spaCy model downloaded and loaded")
            except Exception as e:
                logger.error(f"Failed to load spaCy model: {e}")
                self.nlp = None
    
    def _add_custom_patterns(self):
        """Add custom entity patterns to spaCy."""
        if not self.nlp:
            return
        
        self.matcher = Matcher(self.nlp.vocab)
        
        # Container number pattern: 4 letters + 7 digits
        container_pattern = [{"TEXT": {"REGEX": r"^[A-Z]{4}\d{7}$"}}]
        self.matcher.add("CONTAINER_NUMBER", [container_pattern])
        
        # Port code pattern: 5 uppercase letters (UN/LOCODE)
        port_pattern = [{"TEXT": {"REGEX": r"^[A-Z]{5}$"}}]
        self.matcher.add("PORT_CODE", [port_pattern])
        
        # Amount pattern
        amount_pattern = [
            {"TEXT": {"IN": ["USD", "EUR", "GBP", "$", "€", "£"]}, "OP": "?"},
            {"LIKE_NUM": True},
            {"TEXT": {"IN": ["USD", "EUR", "GBP"]}, "OP": "?"}
        ]
        self.matcher.add("AMOUNT", [amount_pattern])
    
    def _load_sentiment_model(self):
        """Load sentiment analysis model."""
        try:
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=-1  # CPU
            )
            logger.info("Sentiment analysis model loaded")
        except Exception as e:
            logger.warning(f"Could not load sentiment model: {e}")
            self.sentiment_analyzer = None
    
    def classify_document(self, text: str) -> Tuple[DocumentType, float]:
        """
        Classify document type based on content.
        
        Args:
            text: Document text
            
        Returns:
            Tuple of (DocumentType, confidence_score)
        """
        text_lower = text.lower()
        scores = {}
        
        for doc_type, patterns in self.doc_type_patterns.items():
            # Count pattern matches
            matches = sum(
                1 for pattern in patterns
                if re.search(pattern, text_lower)
            )
            # Calculate score as percentage of patterns matched
            scores[doc_type] = matches / len(patterns)
        
        if not scores or max(scores.values()) == 0:
            return DocumentType.UNKNOWN, 0.0
        
        best_type = max(scores, key=scores.get)
        confidence = scores[best_type]
        
        # Boost confidence if multiple patterns matched
        if confidence > 0.3:
            confidence = min(confidence * 1.5, 1.0)
        
        logger.info(f"Document classified as {best_type} with confidence {confidence:.2f}")
        
        return best_type, confidence
    
    def extract_entities(self, text: str) -> List[ExtractedEntity]:
        """
        Extract named entities from document.
        
        Uses spaCy NER + custom patterns for domain-specific entities.
        
        Args:
            text: Document text
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        # Use spaCy NER if available
        if self.nlp:
            doc = self.nlp(text)
            
            for ent in doc.ents:
                # Get context (surrounding text)
                start = max(0, ent.start_char - 20)
                end = min(len(text), ent.end_char + 20)
                context = text[start:end]
                
                entities.append(ExtractedEntity(
                    entity_type=ent.label_,
                    value=ent.text,
                    confidence=0.8,  # spaCy doesn't provide confidence
                    start_pos=ent.start_char,
                    end_pos=ent.end_char,
                    context=context
                ))
            
            # Use custom matcher
            if self.matcher:
                matches = self.matcher(doc)
                for match_id, start, end in matches:
                    span = doc[start:end]
                    match_name = self.nlp.vocab.strings[match_id]
                    
                    entities.append(ExtractedEntity(
                        entity_type=match_name,
                        value=span.text,
                        confidence=0.9,
                        start_pos=span.start_char,
                        end_pos=span.end_char,
                        context=text[max(0, span.start_char-20):min(len(text), span.end_char+20)]
                    ))
        
        # Use regex patterns for specific fields
        for field_name, pattern in self.field_patterns.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                value = match.group(1) if match.lastindex and match.lastindex >= 1 else match.group(0)
                
                # Get context
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                context = text[start:end]
                
                entities.append(ExtractedEntity(
                    entity_type=field_name.upper(),
                    value=value.strip(),
                    confidence=0.85,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    context=context
                ))
        
        # Deduplicate entities
        seen = set()
        unique_entities = []
        for ent in entities:
            # Create unique key from type and normalized value
            key = (ent.entity_type, ent.value.lower().strip())
            if key not in seen:
                seen.add(key)
                unique_entities.append(ent)
        
        logger.info(f"Extracted {len(unique_entities)} unique entities")
        
        return unique_entities
    
    def extract_key_values(self, text: str, document_type: DocumentType) -> Dict[str, str]:
        """
        Extract key-value pairs based on document type.
        
        Args:
            text: Document text
            document_type: Type of document
            
        Returns:
            Dictionary of key-value pairs
        """
        key_values = {}
        
        # Common extractions for all document types
        for field, pattern in self.field_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1) if match.lastindex and match.lastindex >= 1 else match.group(0)
                key_values[field] = value.strip()
        
        # Document-specific extractions
        if document_type == DocumentType.BILL_OF_LADING:
            # Extract shipper
            shipper_match = re.search(
                r"shipper[:\s]+([^\n]+(?:\n(?!\s*consignee)[^\n]+)*)",
                text, re.IGNORECASE
            )
            if shipper_match:
                key_values["shipper"] = shipper_match.group(1).strip()[:200]
            
            # Extract consignee
            consignee_match = re.search(
                r"consignee[:\s]+([^\n]+(?:\n(?!\s*notify)[^\n]+)*)",
                text, re.IGNORECASE
            )
            if consignee_match:
                key_values["consignee"] = consignee_match.group(1).strip()[:200]
            
            # Extract commodity
            commodity_match = re.search(
                r"(?:commodity|description of goods)[:\s]+([^\n]+)",
                text, re.IGNORECASE
            )
            if commodity_match:
                key_values["commodity"] = commodity_match.group(1).strip()[:200]
        
        elif document_type == DocumentType.CLAIM_REPORT:
            # Extract loss date
            loss_date_match = re.search(
                r"(?:date of loss|loss date|incident date)[:\s]+([^\n]+)",
                text, re.IGNORECASE
            )
            if loss_date_match:
                key_values["loss_date"] = loss_date_match.group(1).strip()
            
            # Extract loss description
            desc_match = re.search(
                r"(?:description of loss|loss description|details of incident)[:\s]+([^\n]+(?:\n[^\n]+){0,5})",
                text, re.IGNORECASE
            )
            if desc_match:
                key_values["loss_description"] = desc_match.group(1).strip()[:500]
            
            # Extract cause
            cause_match = re.search(
                r"(?:cause of loss|cause|reason)[:\s]+([^\n]+)",
                text, re.IGNORECASE
            )
            if cause_match:
                key_values["cause"] = cause_match.group(1).strip()
        
        elif document_type == DocumentType.COMMERCIAL_INVOICE:
            # Extract seller
            seller_match = re.search(
                r"(?:seller|exporter|from)[:\s]+([^\n]+)",
                text, re.IGNORECASE
            )
            if seller_match:
                key_values["seller"] = seller_match.group(1).strip()[:200]
            
            # Extract buyer
            buyer_match = re.search(
                r"(?:buyer|importer|to)[:\s]+([^\n]+)",
                text, re.IGNORECASE
            )
            if buyer_match:
                key_values["buyer"] = buyer_match.group(1).strip()[:200]
            
            # Extract payment terms
            payment_match = re.search(
                r"(?:payment terms|terms of payment)[:\s]+([^\n]+)",
                text, re.IGNORECASE
            )
            if payment_match:
                key_values["payment_terms"] = payment_match.group(1).strip()
        
        logger.info(f"Extracted {len(key_values)} key-value pairs")
        
        return key_values
    
    def analyze_sentiment(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Analyze sentiment of text (useful for claim descriptions).
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment analysis results or None if unavailable
        """
        if not self.sentiment_analyzer:
            return None
        
        try:
            # Truncate long text (model limit is usually 512 tokens)
            text = text[:512]
            
            if not text.strip():
                return None
            
            result = self.sentiment_analyzer(text)[0]
            
            sentiment_data = {
                "label": result["label"],
                "score": float(result["score"]),
                "positive": float(result["score"]) if result["label"] == "POSITIVE" else 1 - float(result["score"]),
                "negative": float(result["score"]) if result["label"] == "NEGATIVE" else 1 - float(result["score"])
            }
            
            logger.info(f"Sentiment: {sentiment_data['label']} ({sentiment_data['score']:.2f})")
            
            return sentiment_data
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return None
    
    def generate_summary(self, text: str, max_length: int = 150) -> str:
        """
        Generate a summary of the document.
        
        Uses extractive summarization based on sentence importance.
        
        Args:
            text: Document text
            max_length: Maximum summary length
            
        Returns:
            Summary text
        """
        if len(text) <= max_length:
            return text
        
        if self.nlp:
            # Use spaCy for sentence segmentation
            doc = self.nlp(text)
            sentences = list(doc.sents)
        else:
            # Fallback to simple sentence splitting
            sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
            sentences = sentences[:20]  # Limit for performance
        
        if len(sentences) <= 3:
            return text[:max_length]
        
        # Score sentences based on:
        # 1. Position (first sentences are often important)
        # 2. Entity density (if using spaCy)
        # 3. Keyword presence
        
        keywords = {
            "claim", "loss", "damage", "amount", "policy", "shipment", 
            "cargo", "vessel", "invoice", "payment", "insurance",
            "coverage", "incident", "date"
        }
        
        sentence_scores = []
        
        for i, sent in enumerate(sentences):
            score = 0
            
            # Position score (first sentences more important)
            if i < 3:
                score += 3 - i
            
            # Entity density (if spaCy available)
            if self.nlp and hasattr(sent, 'start'):
                entities_in_sent = len([
                    ent for ent in doc.ents 
                    if ent.start >= sent.start and ent.end <= sent.end
                ])
                score += entities_in_sent * 0.5
            
            # Keyword score
            sent_text = str(sent).lower()
            keyword_count = sum(1 for kw in keywords if kw in sent_text)
            score += keyword_count * 0.3
            
            # Length penalty (avoid very short sentences)
            if len(str(sent).split()) < 5:
                score *= 0.5
            
            sentence_scores.append((i, sent, score))
        
        # Select top sentences
        sorted_sentences = sorted(sentence_scores, key=lambda x: x[2], reverse=True)
        top_n = min(3, len(sorted_sentences))
        selected = sorted(sorted_sentences[:top_n], key=lambda x: x[0])  # Keep original order
        
        summary = " ".join([str(s[1]) for s in selected])
        
        # Truncate if needed
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        
        logger.info(f"Generated summary ({len(summary)} chars from {len(text)} chars)")
        
        return summary
    
    def detect_issues(
        self, 
        text: str, 
        document_type: DocumentType, 
        key_values: Dict[str, str]
    ) -> List[str]:
        """
        Detect potential issues or flags in the document.
        
        Args:
            text: Document text
            document_type: Type of document
            key_values: Extracted key-value pairs
            
        Returns:
            List of issue descriptions
        """
        flags = []
        
        # Check for missing required fields
        required_fields = {
            DocumentType.BILL_OF_LADING: ["bl_number", "vessel_name"],
            DocumentType.CLAIM_REPORT: ["claim_number", "amount"],
            DocumentType.COMMERCIAL_INVOICE: ["invoice_number", "amount"],
            DocumentType.INSURANCE_CERTIFICATE: ["policy_number"]
        }
        
        if document_type in required_fields:
            missing = [f for f in required_fields[document_type] if f not in key_values]
            if missing:
                flags.append(f"⚠️ Missing critical fields: {', '.join(missing)}")
        
        # Check for suspicious patterns in claims
        if document_type == DocumentType.CLAIM_REPORT:
            text_lower = text.lower()
            
            if "total loss" in text_lower:
                flags.append("🚨 Total loss claim - requires special handling and investigation")
            
            if any(word in text_lower for word in ["theft", "stolen", "pilferage"]):
                flags.append("🚨 Theft reported - police report and documentation required")
            
            if any(word in text_lower for word in ["fire", "explosion", "sinking"]):
                flags.append("🚨 Major casualty - immediate investigation required")
            
            # Check for vague language
            vague_phrases = ["approximately", "around", "possibly", "maybe", "unclear"]
            if any(phrase in text_lower for phrase in vague_phrases):
                flags.append("⚠️ Contains vague language - request clarification and specifics")
            
            # Check for missing documentation references
            if "attach" not in text_lower and "photo" not in text_lower:
                flags.append("⚠️ No mention of supporting documentation - request photos/evidence")
        
        # Check document length
        if len(text) < 100:
            flags.append("⚠️ Document appears incomplete (very short)")
        
        # Check for PII that might need redaction
        if re.search(r'\b\d{3}-\d{2}-\d{4}\b', text):  # SSN pattern
            flags.append("🔒 Contains potential SSN - ensure PII compliance")
        
        # Check for multiple currencies (potential confusion)
        currencies = re.findall(r'\b(USD|EUR|GBP|JPY|CNY)\b', text, re.IGNORECASE)
        if len(set(c.upper() for c in currencies)) > 1:
            flags.append("⚠️ Multiple currencies mentioned - verify exchange rates")
        
        logger.info(f"Detected {len(flags)} potential issues")
        
        return flags
    
    def analyze(self, text: str) -> DocumentAnalysis:
        """
        Perform complete document analysis.
        
        Args:
            text: Document text
            
        Returns:
            Complete analysis results
        """
        logger.info(f"Analyzing document ({len(text)} chars)")
        
        # Classify document
        doc_type, type_confidence = self.classify_document(text)
        
        # Extract entities
        entities = self.extract_entities(text)
        
        # Extract key-value pairs
        key_values = self.extract_key_values(text, doc_type)
        
        # Generate summary
        summary = self.generate_summary(text) if len(text) > 200 else None
        
        # Analyze sentiment (mainly for claim descriptions)
        sentiment = None
        if doc_type == DocumentType.CLAIM_REPORT:
            sentiment = self.analyze_sentiment(text)
        
        # Detect issues
        flags = self.detect_issues(text, doc_type, key_values)
        
        # Metadata
        metadata = {
            "text_length": len(text),
            "num_entities": len(entities),
            "num_key_values": len(key_values),
            "num_flags": len(flags),
            "spacy_available": SPACY_AVAILABLE,
            "transformers_available": TRANSFORMERS_AVAILABLE
        }
        
        logger.info(f"Analysis complete: {doc_type} ({type_confidence:.2f} confidence)")
        
        return DocumentAnalysis(
            document_type=doc_type,
            type_confidence=type_confidence,
            entities=entities,
            key_values=key_values,
            summary=summary,
            sentiment=sentiment,
            flags=flags,
            metadata=metadata
        )


# Global instance
document_processor = DocumentProcessor()
