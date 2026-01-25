"""
NLP Module for Document Processing and Chatbot

Exports:
- Document processing: DocumentProcessor, DocumentType, DocumentAnalysis
- Chatbot: InsuranceChatbot, Intent, ConversationContext
"""

from .document_processor import (
    DocumentProcessor,
    DocumentType,
    ExtractedEntity,
    DocumentAnalysis,
    document_processor
)

from .chatbot import (
    InsuranceChatbot,
    Intent,
    ChatMessage,
    ConversationContext,
    chatbot
)

__all__ = [
    # Document Processing
    "DocumentProcessor",
    "DocumentType",
    "ExtractedEntity",
    "DocumentAnalysis",
    "document_processor",
    
    # Chatbot
    "InsuranceChatbot",
    "Intent",
    "ChatMessage",
    "ConversationContext",
    "chatbot",
]
