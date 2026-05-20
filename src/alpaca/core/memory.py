# src/alpaca/core/memory.py
"""Conversation memory management."""

from collections import deque

from alpaca.config import Config
from alpaca.models import Message


class ConversationMemory:
    """Manages conversation history with trimming."""
    
    def __init__(self, max_history: int | None = None):
        self.max_history = max_history or Config.max_history
        self._messages: deque[Message] = deque()
        self._system_message: Message | None = None
        
    def set_system(self, content: str) -> None:
        """Set the system message."""
        self._system_message = Message(role="system", content=content)
        
    def add(self, role: str, content: str, name: str | None = None) -> None:
        """Add a message to memory."""
        from alpaca.models import MessageRole
        
        msg = Message(
            role=MessageRole(role),
            content=content,
            name=name,
        )
        self._messages.append(msg)
        self._trim()
        
    def add_user(self, content: str) -> None:
        """Add user message."""
        self.add("user", content)
        
    def add_assistant(self, content: str) -> None:
        """Add assistant message."""
        self.add("assistant", content)
        
    def add_tool_result(self, name: str, content: str) -> None:
        """Add tool result message."""
        self.add("tool", content, name=name)
        
    def get_messages(self) -> list[Message]:
        """Get all messages including system message."""
        messages: list[Message] = []
        if self._system_message:
            messages.append(self._system_message)
        messages.extend(self._messages)
        return messages
        
    def clear(self) -> None:
        """Clear all messages except system."""
        self._messages.clear()
        
    def _trim(self) -> None:
        """Trim messages to max history while keeping system message."""
        while len(self._messages) > self.max_history:
            self._messages.popleft()
            
    def __len__(self) -> int:
        """Return number of non-system messages."""
        return len(self._messages)
