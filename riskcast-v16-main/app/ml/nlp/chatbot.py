"""
AI Chatbot for Customer Support

Features:
1. Intent classification
2. Entity extraction
3. Context management
4. Response generation
5. Multi-turn conversation
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import re
import uuid

from app.core.logging import get_logger


logger = get_logger(__name__)


class Intent(str, Enum):
    """User intents."""
    GET_QUOTE = "get_quote"
    CHECK_POLICY = "check_policy"
    FILE_CLAIM = "file_claim"
    CLAIM_STATUS = "claim_status"
    COVERAGE_QUESTION = "coverage_question"
    PRICING_QUESTION = "pricing_question"
    GENERAL_QUESTION = "general_question"
    GREETING = "greeting"
    GOODBYE = "goodbye"
    HELP = "help"
    UNKNOWN = "unknown"


@dataclass
class ChatMessage:
    """Chat message."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    intent: Optional[Intent] = None
    entities: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0


@dataclass
class ConversationContext:
    """Conversation context for multi-turn dialogue."""
    session_id: str
    user_id: Optional[str] = None
    messages: List[ChatMessage] = field(default_factory=list)
    current_intent: Optional[Intent] = None
    collected_info: Dict[str, Any] = field(default_factory=dict)
    pending_action: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)


class InsuranceChatbot:
    """
    AI-powered chatbot for insurance customer support.
    
    Handles intent classification, entity extraction, and multi-turn conversations.
    """
    
    def __init__(self):
        """Initialize chatbot with patterns and responses."""
        # Intent classification patterns
        self.intent_patterns = {
            Intent.GET_QUOTE: [
                r"(?:get|request|need|want)\s+(?:a\s+)?quote",
                r"how much (?:would|does|will)\s+(?:it\s+)?cost",
                r"price for (?:shipping|cargo|insurance)",
                r"insure (?:my|a) shipment",
                r"quote (?:for|on)"
            ],
            Intent.CHECK_POLICY: [
                r"(?:check|view|see|find|show)\s+(?:my\s+)?policy",
                r"policy (?:status|details|information|info)",
                r"what (?:does|is) my policy",
                r"policy number",
                r"active policies"
            ],
            Intent.FILE_CLAIM: [
                r"(?:file|submit|make|report|create)\s+(?:a\s+)?claim",
                r"(?:damaged|lost|stolen|broken) (?:cargo|shipment|goods)",
                r"(?:need|want) to claim",
                r"report (?:loss|damage)",
                r"my cargo (?:is|was) damaged"
            ],
            Intent.CLAIM_STATUS: [
                r"(?:check|what is|where is|track)\s+(?:my\s+)?claim",
                r"claim (?:status|update|progress|number)",
                r"when will (?:my\s+)?claim",
                r"claim.*(?:processed|approved|paid)"
            ],
            Intent.COVERAGE_QUESTION: [
                r"what (?:does|is) (?:covered|coverage|included)",
                r"(?:am|is|are) .+ covered",
                r"exclusions?",
                r"(?:does|will) (?:it|policy|insurance) cover",
                r"what (?:kind|type) of (?:coverage|protection)"
            ],
            Intent.PRICING_QUESTION: [
                r"how (?:is|are) (?:rates?|premiums?|prices?) (?:calculated|determined|set)",
                r"why (?:is|are) (?:the\s+)?(?:rate|premium|price)",
                r"factors? (?:affecting|that affect|influencing)",
                r"why so (?:expensive|high|much)",
                r"discount"
            ],
            Intent.GREETING: [
                r"^(?:hi|hello|hey|good\s+(?:morning|afternoon|evening)|greetings)",
                r"^(?:how are you|what's up|sup)"
            ],
            Intent.GOODBYE: [
                r"(?:bye|goodbye|see you|thanks?|thank you)",
                r"(?:that's|that is) (?:all|it|everything)",
                r"(?:have a|good) (?:day|night)",
                r"no (?:more|further) (?:questions|help needed)"
            ],
            Intent.HELP: [
                r"(?:help|assist|support)",
                r"(?:what|how) can you (?:do|help)",
                r"what (?:can|do) you (?:offer|provide|do)",
                r"capabilities"
            ]
        }
        
        # Entity extraction patterns
        self.entity_patterns = {
            "cargo_value": r"(?:value|worth|valued at)[:\s]*\$?\s*([\d,]+)",
            "origin_port": r"(?:from|origin|departure|leaving)[:\s]*([A-Z]{5}|[A-Za-z\s]{3,30})",
            "destination_port": r"(?:to|destination|arrival|going to)[:\s]*([A-Z]{5}|[A-Za-z\s]{3,30})",
            "cargo_type": r"(?:shipping|transporting|cargo of|goods?|product)[:\s]*([A-Za-z\s]{2,30})",
            "policy_number": r"(?:policy|pol)[:\s#]*([A-Z0-9\-]{5,20})",
            "claim_number": r"(?:claim)[:\s#]*([A-Z0-9\-]{5,20})",
            "date": r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
            "weight": r"(\d+\.?\d*)\s*(?:kg|mt|tons?|lbs)",
            "container_count": r"(\d+)\s*(?:containers?|ctns?|boxes?)"
        }
        
        # Response templates
        self.responses = {
            Intent.GREETING: [
                "Hello! I'm the RISKCAST insurance assistant. How can I help you today?",
                "Hi there! I can help you with quotes, policies, claims, and coverage questions. What do you need?",
                "Welcome to RISKCAST! I'm here to assist you with your insurance needs."
            ],
            Intent.GET_QUOTE: {
                "initial": "I'd be happy to help you get a quote! I'll need some information:\n\n1. What type of cargo are you shipping?\n2. What's the approximate value?\n3. Where is it shipping from and to?\n\nYou can provide this information all at once or one by one.",
                "need_cargo": "What type of cargo will you be shipping? (e.g., electronics, machinery, food products)",
                "need_value": "What's the approximate value of the cargo in USD?",
                "need_route": "Where will the shipment be going from and to? (You can specify port codes or city names)",
                "complete": "Perfect! Based on the information you provided:\n\n• Cargo: {cargo_type}\n• Value: ${cargo_value:,}\n• Route: {origin} → {destination}\n\nLet me generate a quote for you. One moment please...",
                "partial": "Great! I have:\n{collected}\n\nI still need:\n{needed}"
            },
            Intent.FILE_CLAIM: {
                "initial": "I'm sorry to hear about your loss. I'll help you file a claim.\n\nPlease provide:\n1. Your policy number\n2. What happened to your cargo?\n3. When did the incident occur?\n4. Estimated loss amount",
                "need_policy": "What's your policy number? (You can find it on your insurance certificate)",
                "need_description": "Can you describe what happened to your cargo? (e.g., water damage during transit, container dropped)",
                "need_date": "When did the incident occur? Please provide the date.",
                "complete": "Thank you for providing the details. I've recorded your claim:\n\n• Policy: {policy_number}\n• Incident: {description}\n• Date: {date}\n• Claim Reference: {claim_ref}\n\nA claims specialist will contact you within 24 hours. Please prepare:\n- Photos of the damage\n- Bill of Lading\n- Commercial invoice\n- Survey report (if available)"
            },
            Intent.CLAIM_STATUS: {
                "found": "I found your claim!\n\n• Claim Number: {claim_number}\n• Status: {status}\n• Last Update: {update_date}\n\n{details}\n\nIs there anything else you'd like to know?",
                "not_found": "I couldn't find a claim with that number. Could you please double-check the claim number? It should be in the format CLM-YYYYMMDD-XXXX.",
                "need_number": "What's your claim number? You can find it in your claim confirmation email."
            },
            Intent.CHECK_POLICY: {
                "found": "I found your policy:\n\n• Policy Number: {policy_number}\n• Status: {status}\n• Coverage: {coverage}\n• Valid: {start_date} to {end_date}\n\nWould you like more details?",
                "not_found": "I couldn't find a policy with that number. Please check the policy number and try again.",
                "need_number": "What's your policy number? It's usually in the format POL-XXXXXXXX."
            },
            Intent.COVERAGE_QUESTION: {
                "general": "**RISKCAST cargo insurance typically covers:**\n\n✅ **Covered Perils:**\n• Physical loss or damage to cargo\n• General average contributions\n• Salvage and sue & labor charges\n• Transit by sea, air, road, or rail\n\n❌ **Common Exclusions:**\n• Inherent vice (natural deterioration)\n• Delay-related losses\n• War and strikes (unless added)\n• Improper packing by shipper\n\nWould you like details about a specific coverage type or scenario?",
                "specific": "Regarding **{topic}**:\n\n{explanation}\n\nDoes this answer your question, or would you like more information?",
                "war": "War coverage is available as an additional premium. It covers losses from:\n• War\n• Civil war\n• Revolution\n• Insurrection\n• Mines and torpedoes\n\nWould you like to add this to your policy?",
                "delay": "Unfortunately, losses caused by delay are not covered under standard cargo insurance. This includes:\n• Market price changes\n• Spoilage due to delays\n• Missed business opportunities\n\nHowever, physical damage that occurs during a delay would be covered."
            },
            Intent.PRICING_QUESTION: {
                "general": "**Our pricing is based on several factors:**\n\n1. **Cargo Details:**\n   • Type of goods (hazardous = higher rate)\n   • Value (higher value = higher premium)\n   • Packaging quality\n\n2. **Route Factors:**\n   • Origin and destination\n   • Known risk areas (piracy, weather)\n   • Mode of transport\n\n3. **Historical Factors:**\n   • Your claim history\n   • Carrier reliability\n   • Route loss history\n\n4. **Coverage Type:**\n   • Basic vs. comprehensive\n   • Additional coverages (war, strikes)\n\nTypical rates range from 0.3% to 2% of cargo value. Would you like a specific quote?",
                "high_rate": "If your rate seems high, it could be due to:\n• High-risk cargo type\n• Route through risk areas\n• Previous claims\n• Comprehensive coverage selected\n\nWe can review your quote to see if there are ways to optimize it."
            },
            Intent.HELP: [
                "I can help you with:\n\n📋 **Get a Quote** - Instant cargo insurance quotes\n📄 **Policy Information** - Check your policy details and coverage\n📝 **File a Claim** - Report loss or damage to your cargo\n🔍 **Claim Status** - Track your existing claims\n❓ **Coverage Questions** - Understand what's covered and excluded\n💰 **Pricing Questions** - Learn about rate factors\n\nJust tell me what you need, and I'll guide you through it!",
            ],
            Intent.GOODBYE: [
                "Thank you for using RISKCAST! Have a great day! 👋",
                "Goodbye! If you need help later, I'm always here. Safe shipping! 🚢",
                "Take care! Feel free to return anytime you need assistance. 👋"
            ],
            Intent.UNKNOWN: [
                "I'm not sure I understood that. Could you rephrase your question?",
                "I didn't quite catch that. You can ask me about:\n• Getting quotes\n• Policy information\n• Filing claims\n• Coverage details\n\nWhat would you like help with?",
                "Sorry, I'm not sure how to help with that. Try asking about quotes, policies, or claims."
            ]
        }
        
        # Conversation contexts (in-memory storage)
        self.contexts: Dict[str, ConversationContext] = {}
    
    def classify_intent(self, text: str) -> Tuple[Intent, float]:
        """
        Classify user intent from message.
        
        Args:
            text: User message
            
        Returns:
            Tuple of (Intent, confidence_score)
        """
        text_lower = text.lower().strip()
        
        best_intent = Intent.UNKNOWN
        best_score = 0
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text_lower)
                if match:
                    # Score based on pattern specificity (length)
                    score = len(pattern)
                    
                    # Boost if match is at start of message
                    if match.start() == 0:
                        score *= 1.2
                    
                    if score > best_score:
                        best_score = score
                        best_intent = intent
        
        # Convert score to confidence (0-1)
        confidence = min(best_score / 30, 1.0) if best_score > 0 else 0.1
        
        logger.info(f"Classified intent: {best_intent} (confidence: {confidence:.2f})")
        
        return best_intent, confidence
    
    def extract_entities(self, text: str) -> Dict[str, str]:
        """
        Extract entities from message.
        
        Args:
            text: User message
            
        Returns:
            Dictionary of extracted entities
        """
        entities = {}
        
        for entity_type, pattern in self.entity_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                
                # Clean up value
                if entity_type == "cargo_value":
                    value = value.replace(",", "")
                    try:
                        value = str(int(float(value)))
                    except:
                        pass
                
                entities[entity_type] = value
        
        if entities:
            logger.info(f"Extracted entities: {list(entities.keys())}")
        
        return entities
    
    def get_or_create_context(self, session_id: str, user_id: Optional[str] = None) -> ConversationContext:
        """
        Get existing context or create new one.
        
        Args:
            session_id: Session identifier
            user_id: Optional user identifier
            
        Returns:
            Conversation context
        """
        if session_id not in self.contexts:
            self.contexts[session_id] = ConversationContext(
                session_id=session_id,
                user_id=user_id
            )
            logger.info(f"Created new conversation context: {session_id}")
        
        # Update last activity
        self.contexts[session_id].last_activity = datetime.utcnow()
        
        return self.contexts[session_id]
    
    def chat(
        self,
        user_message: str,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Tuple[str, ConversationContext]:
        """
        Process user message and generate response.
        
        Args:
            user_message: User's message
            session_id: Session identifier
            user_id: Optional user identifier
            
        Returns:
            Tuple of (response, updated_context)
        """
        # Get or create context
        context = self.get_or_create_context(session_id, user_id)
        
        # Classify intent
        intent, confidence = self.classify_intent(user_message)
        
        # Extract entities
        entities = self.extract_entities(user_message)
        
        # Create user message
        user_msg = ChatMessage(
            role="user",
            content=user_message,
            intent=intent,
            entities=entities,
            confidence=confidence
        )
        context.messages.append(user_msg)
        
        # Update collected info
        context.collected_info.update(entities)
        
        # Generate response
        response = self._generate_response(intent, context)
        
        # Create assistant message
        assistant_msg = ChatMessage(
            role="assistant",
            content=response
        )
        context.messages.append(assistant_msg)
        
        # Update current intent (if not greeting/goodbye/unknown)
        if intent not in [Intent.GREETING, Intent.GOODBYE, Intent.UNKNOWN]:
            context.current_intent = intent
        
        logger.info(f"Generated response ({len(response)} chars)")
        
        return response, context
    
    def _generate_response(self, intent: Intent, context: ConversationContext) -> str:
        """
        Generate response for given intent.
        
        Args:
            intent: Classified intent
            context: Conversation context
            
        Returns:
            Response text
        """
        templates = self.responses.get(intent)
        
        if isinstance(templates, list):
            # Simple responses - pick first one
            import random
            return random.choice(templates)
        
        if isinstance(templates, dict):
            # Multi-turn conversation
            return self._handle_multi_turn(intent, templates, context)
        
        return self.responses[Intent.UNKNOWN][0]
    
    def _handle_multi_turn(
        self,
        intent: Intent,
        templates: Dict[str, str],
        context: ConversationContext
    ) -> str:
        """
        Handle multi-turn conversations.
        
        Args:
            intent: Current intent
            templates: Response templates
            context: Conversation context
            
        Returns:
            Response text
        """
        collected = context.collected_info
        
        if intent == Intent.GET_QUOTE:
            # Check what info we still need
            needed = []
            if "cargo_type" not in collected:
                needed.append("cargo type")
            if "cargo_value" not in collected:
                needed.append("cargo value")
            if "origin_port" not in collected:
                needed.append("origin port")
            if "destination_port" not in collected:
                needed.append("destination port")
            
            if not needed:
                # We have all info
                return templates["complete"].format(
                    cargo_type=collected.get("cargo_type", "General cargo"),
                    cargo_value=int(collected.get("cargo_value", "0")),
                    origin=collected.get("origin_port", "TBD"),
                    destination=collected.get("destination_port", "TBD")
                )
            
            # Show partial progress if we have some info
            if len(needed) < 4:
                collected_str = "\n".join([
                    f"✓ {k.replace('_', ' ').title()}: {v}"
                    for k, v in collected.items()
                    if k in ["cargo_type", "cargo_value", "origin_port", "destination_port"]
                ])
                needed_str = "\n".join([f"• {n.title()}" for n in needed])
                
                return templates["partial"].format(
                    collected=collected_str,
                    needed=needed_str
                )
            
            # Ask for first missing field
            if "cargo_type" not in collected:
                return templates["need_cargo"]
            if "cargo_value" not in collected:
                return templates["need_value"]
            if "origin_port" not in collected or "destination_port" not in collected:
                return templates["need_route"]
            
            return templates["initial"]
        
        elif intent == Intent.FILE_CLAIM:
            # Check required fields
            if "policy_number" not in collected:
                return templates["need_policy"]
            if "loss_description" not in collected and len(context.messages) > 2:
                # Only ask after initial exchange
                return templates["need_description"]
            
            # Generate claim reference
            claim_ref = f"CLM-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
            context.collected_info["claim_ref"] = claim_ref
            
            return templates["complete"].format(
                policy_number=collected.get("policy_number", "N/A"),
                description=collected.get("loss_description", "As described"),
                date=collected.get("date", "To be determined"),
                claim_ref=claim_ref
            )
        
        elif intent == Intent.CLAIM_STATUS:
            claim_number = collected.get("claim_number")
            if not claim_number:
                return templates["need_number"]
            
            # Mock claim lookup
            return templates["found"].format(
                claim_number=claim_number,
                status="IN REVIEW",
                update_date=datetime.now().strftime("%Y-%m-%d"),
                details="A claims adjuster is reviewing your documentation. We expect to complete the review within 3-5 business days."
            )
        
        elif intent == Intent.CHECK_POLICY:
            policy_number = collected.get("policy_number")
            if not policy_number:
                return templates["need_number"]
            
            # Mock policy lookup
            return templates["found"].format(
                policy_number=policy_number,
                status="ACTIVE",
                coverage="Comprehensive Marine Cargo",
                start_date="2026-01-01",
                end_date="2026-12-31"
            )
        
        elif intent == Intent.COVERAGE_QUESTION:
            # Check for specific topics
            last_message = context.messages[-1].content.lower()
            
            if "war" in last_message:
                return templates["war"]
            if "delay" in last_message:
                return templates["delay"]
            
            return templates["general"]
        
        elif intent == Intent.PRICING_QUESTION:
            last_message = context.messages[-1].content.lower()
            
            if any(word in last_message for word in ["high", "expensive", "much", "why"]):
                return templates["high_rate"]
            
            return templates["general"]
        
        return templates.get("initial", self.responses[Intent.UNKNOWN][0])
    
    def reset_context(self, session_id: str) -> bool:
        """
        Reset conversation context.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if context existed and was reset
        """
        if session_id in self.contexts:
            del self.contexts[session_id]
            logger.info(f"Reset context: {session_id}")
            return True
        return False
    
    def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """
        Get conversation context.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Context or None if not found
        """
        return self.contexts.get(session_id)
    
    def cleanup_old_contexts(self, max_age_hours: int = 24):
        """
        Clean up old conversation contexts.
        
        Args:
            max_age_hours: Maximum age in hours
        """
        now = datetime.utcnow()
        to_remove = []
        
        for session_id, context in self.contexts.items():
            age = (now - context.last_activity).total_seconds() / 3600
            if age > max_age_hours:
                to_remove.append(session_id)
        
        for session_id in to_remove:
            del self.contexts[session_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old contexts")


# Global instance
chatbot = InsuranceChatbot()
