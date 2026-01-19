"""
AI System Advisor - Context Manager
Manages conversation history and context
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime, timedelta
from dataclasses import asdict

from app.ai_system_advisor.types import Message, Conversation


class ContextManager:
    """Manages conversation history and context"""
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize context manager
        
        Args:
            storage_path: Path to storage directory (default: data/conversations)
        """
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            # Default: data/conversations in project root
            root_dir = Path(__file__).resolve().parent.parent.parent
            self.storage_path = root_dir / "data" / "conversations"
        
        # Ensure directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache for active sessions
        self._cache: Dict[str, Conversation] = {}
        self._cache_ttl = timedelta(hours=1)
    
    def _get_file_path(self, session_id: str) -> Path:
        """Get file path for session"""
        # Sanitize session_id for filename
        safe_id = session_id.replace('/', '_').replace('\\', '_')
        return self.storage_path / f"{safe_id}.json"
    
    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for session
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return
            
        Returns:
            List of messages (formatted for LLM)
        """
        conversation = await self._load_conversation(session_id)
        
        if not conversation:
            return []
        
        # Get last N messages
        messages = conversation.messages[-limit:]
        
        # Format for LLM (Claude format)
        formatted = []
        for msg in messages:
            formatted.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return formatted
    
    async def save_message(
        self,
        session_id: str,
        role: Literal['user', 'assistant', 'system'],
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Save message to conversation history
        
        Args:
            session_id: Session identifier
            role: Message role
            content: Message content
            metadata: Optional metadata
        """
        conversation = await self._load_conversation(session_id)
        
        # Create new conversation if doesn't exist
        if not conversation:
            conversation = Conversation(
                session_id=session_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                messages=[],
                context={}
            )
        
        # Add message
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        conversation.messages.append(message)
        conversation.updated_at = datetime.utcnow()
        
        # Save to file
        await self._save_conversation(conversation)
        
        # Update cache
        self._cache[session_id] = conversation
    
    async def get_system_context(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Get system context for session
        
        Args:
            session_id: Session identifier
            
        Returns:
            System context dictionary
        """
        conversation = await self._load_conversation(session_id)
        
        if not conversation:
            return {}
        
        return conversation.context or {}
    
    async def update_system_context(
        self,
        session_id: str,
        context: Dict[str, Any]
    ):
        """
        Update system context for session
        
        Args:
            session_id: Session identifier
            context: Context dictionary
        """
        conversation = await self._load_conversation(session_id)
        
        if not conversation:
            conversation = Conversation(
                session_id=session_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                messages=[],
                context=context
            )
        else:
            # Merge with existing context
            existing = conversation.context or {}
            existing.update(context)
            conversation.context = existing
            conversation.updated_at = datetime.utcnow()
        
        await self._save_conversation(conversation)
        self._cache[session_id] = conversation
    
    async def summarize_context(
        self,
        session_id: str,
        max_messages: int = 50
    ) -> str:
        """
        Summarize conversation context for long conversations
        
        Args:
            session_id: Session identifier
            max_messages: Maximum messages before summarization
            
        Returns:
            Summary string
        """
        conversation = await self._load_conversation(session_id)
        
        if not conversation or len(conversation.messages) <= max_messages:
            return ""
        
        # Simple summarization: count messages, extract key topics
        total_messages = len(conversation.messages)
        user_messages = [m for m in conversation.messages if m.role == 'user']
        
        summary = f"Previous conversation had {total_messages} messages. "
        summary += f"User asked {len(user_messages)} questions. "
        
        # Extract key topics from recent messages
        recent = conversation.messages[-10:]
        topics = set()
        for msg in recent:
            if msg.role == 'user':
                # Simple keyword extraction
                content_lower = msg.content.lower()
                if 'risk' in content_lower:
                    topics.add('risk analysis')
                if 'export' in content_lower or 'pdf' in content_lower:
                    topics.add('export')
                if 'compare' in content_lower:
                    topics.add('comparison')
                if 'recommend' in content_lower:
                    topics.add('recommendations')
        
        if topics:
            summary += f"Recent topics: {', '.join(topics)}."
        
        return summary
    
    async def clear_conversation(self, session_id: str):
        """
        Clear conversation history for session
        
        Args:
            session_id: Session identifier
        """
        file_path = self._get_file_path(session_id)
        if file_path.exists():
            file_path.unlink()
        
        # Remove from cache
        if session_id in self._cache:
            del self._cache[session_id]
    
    async def _load_conversation(self, session_id: str) -> Optional[Conversation]:
        """Load conversation from storage"""
        # Check cache first
        if session_id in self._cache:
            return self._cache[session_id]
        
        # Load from file
        file_path = self._get_file_path(session_id)
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert to Conversation object
            messages = []
            for msg_data in data.get('messages', []):
                messages.append(Message(
                    role=msg_data['role'],
                    content=msg_data['content'],
                    timestamp=datetime.fromisoformat(msg_data['timestamp']),
                    metadata=msg_data.get('metadata')
                ))
            
            conversation = Conversation(
                session_id=data['session_id'],
                created_at=datetime.fromisoformat(data['created_at']),
                updated_at=datetime.fromisoformat(data['updated_at']),
                messages=messages,
                context=data.get('context')
            )
            
            # Cache it
            self._cache[session_id] = conversation
            
            return conversation
        except Exception as e:
            print(f"[ContextManager] Error loading conversation {session_id}: {e}")
            return None
    
    async def _save_conversation(self, conversation: Conversation):
        """Save conversation to storage"""
        file_path = self._get_file_path(conversation.session_id)
        
        # Convert to dict
        data = {
            'session_id': conversation.session_id,
            'created_at': conversation.created_at.isoformat(),
            'updated_at': conversation.updated_at.isoformat(),
            'messages': [
                {
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'metadata': msg.metadata
                }
                for msg in conversation.messages
            ],
            'context': conversation.context
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ContextManager] Error saving conversation {conversation.session_id}: {e}")
