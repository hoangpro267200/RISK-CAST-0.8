"""
Conversation persistence model.

RISKCAST v17 - AI Conversation Storage

Stores AI advisor conversations for:
- Conversation history retrieval
- Context management
- Analytics
- Export functionality
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

# Try to import Base from database
try:
    from app.database import Base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()


class Conversation(Base):
    """
    AI advisor conversation container.
    
    Stores metadata about a conversation session.
    Individual messages are stored in ConversationMessage.
    """
    
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Unique conversation identifier (UUID)
    conversation_id = Column(
        String(36),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )
    
    # Ownership
    user_id = Column(String(255), index=True, nullable=True)
    organization_id = Column(String(255), index=True, nullable=True)
    
    # Metadata
    title = Column(String(255), nullable=True)  # Auto-generated from first message
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Associated data
    shipment_id = Column(String(255), nullable=True)
    risk_assessment_id = Column(String(255), nullable=True)
    
    # Settings
    language = Column(String(10), default='en')
    model_version = Column(String(50), default='claude-sonnet-4')
    
    # Usage tracking
    total_tokens = Column(Integer, default=0)
    message_count = Column(Integer, default=0)
    
    # Context (JSON for flexible storage)
    context = Column(JSON, nullable=True)  # Store risk data, preferences, etc.
    
    # Relationships
    messages = relationship(
        "ConversationMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    def __repr__(self):
        return f"<Conversation {self.conversation_id[:8]}... ({self.message_count} messages)>"
    
    def add_message(
        self,
        role: str,
        content: str,
        token_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'ConversationMessage':
        """
        Add a message to the conversation.
        
        Args:
            role: 'user' or 'assistant'
            content: Message content
            token_count: Number of tokens used
            metadata: Optional metadata dict
        
        Returns:
            Created ConversationMessage
        """
        message = ConversationMessage(
            conversation_id=self.conversation_id,
            role=role,
            content=content,
            token_count=token_count,
            metadata=metadata
        )
        
        # Update conversation stats
        self.message_count += 1
        self.total_tokens += token_count
        self.updated_at = datetime.utcnow()
        
        # Auto-generate title from first user message
        if not self.title and role == 'user':
            self.title = content[:50] + "..." if len(content) > 50 else content
        
        return message
    
    def get_messages(self, limit: int = 50) -> List['ConversationMessage']:
        """Get messages in chronological order."""
        return self.messages.order_by(
            ConversationMessage.timestamp.asc()
        ).limit(limit).all()
    
    def get_context_for_ai(self, max_messages: int = 10) -> List[Dict[str, str]]:
        """
        Get conversation history formatted for AI API.
        
        Returns:
            List of {'role': 'user'|'assistant', 'content': '...'}
        """
        messages = self.messages.order_by(
            ConversationMessage.timestamp.desc()
        ).limit(max_messages).all()
        
        # Reverse to chronological order
        messages = list(reversed(messages))
        
        return [
            {'role': msg.role, 'content': msg.content}
            for msg in messages
        ]
    
    def set_context(self, key: str, value: Any):
        """Set a context value."""
        if self.context is None:
            self.context = {}
        self.context[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a context value."""
        if self.context is None:
            return default
        return self.context.get(key, default)
    
    def to_dict(self, include_messages: bool = False) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        result = {
            'conversation_id': self.conversation_id,
            'title': self.title,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'language': self.language,
            'message_count': self.message_count,
            'total_tokens': self.total_tokens,
            'shipment_id': self.shipment_id,
            'risk_assessment_id': self.risk_assessment_id
        }
        
        if include_messages:
            result['messages'] = [
                msg.to_dict() for msg in self.get_messages()
            ]
        
        return result
    
    @classmethod
    def create(
        cls,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        language: str = 'en',
        shipment_id: Optional[str] = None,
        risk_assessment_id: Optional[str] = None
    ) -> 'Conversation':
        """
        Create a new conversation.
        
        Args:
            user_id: Owner user ID
            organization_id: Owner organization ID
            language: Conversation language
            shipment_id: Associated shipment
            risk_assessment_id: Associated risk assessment
        
        Returns:
            New Conversation instance
        """
        return cls(
            conversation_id=str(uuid.uuid4()),
            user_id=user_id,
            organization_id=organization_id,
            language=language,
            shipment_id=shipment_id,
            risk_assessment_id=risk_assessment_id
        )


class ConversationMessage(Base):
    """
    Individual message in a conversation.
    
    Stores both user messages and AI responses.
    """
    
    __tablename__ = "conversation_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Link to conversation
    conversation_id = Column(
        String(36),
        ForeignKey('conversations.conversation_id', ondelete='CASCADE'),
        index=True,
        nullable=False
    )
    
    # Message data
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Token tracking
    token_count = Column(Integer, default=0)
    
    # Extra data (JSON for flexible storage)
    # Can store: function_calls, tool_use, model_info, etc.
    # Note: "metadata" is reserved in SQLAlchemy, so we use "extra_data"
    extra_data = Column(JSON, nullable=True)
    
    # Processing info
    processing_time_ms = Column(Integer, nullable=True)
    model_used = Column(String(50), nullable=True)
    
    # Relationship
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        content_preview = self.content[:30] + "..." if len(self.content) > 30 else self.content
        return f"<Message {self.role}: {content_preview}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'token_count': self.token_count,
            'extra_data': self.extra_data
        }
    
    @property
    def is_user(self) -> bool:
        """Check if message is from user."""
        return self.role == 'user'
    
    @property
    def is_assistant(self) -> bool:
        """Check if message is from assistant."""
        return self.role == 'assistant'
    
    def has_function_call(self) -> bool:
        """Check if message contains function calls."""
        if not self.extra_data:
            return False
        return 'function_calls' in self.extra_data


# ============================================================
# CONVERSATION SUMMARY (for long conversations)
# ============================================================

class ConversationSummary(Base):
    """
    Summary of a long conversation.
    
    Used to maintain context in very long conversations
    without sending all messages to the AI.
    """
    
    __tablename__ = "conversation_summaries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    conversation_id = Column(
        String(36),
        ForeignKey('conversations.conversation_id', ondelete='CASCADE'),
        index=True,
        nullable=False
    )
    
    # Summary text
    summary = Column(Text, nullable=False)
    
    # Range of messages summarized
    start_message_id = Column(Integer)
    end_message_id = Column(Integer)
    messages_summarized = Column(Integer)
    
    # When summary was created
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Token count of summary
    token_count = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<Summary conv={self.conversation_id[:8]}... ({self.messages_summarized} messages)>"
