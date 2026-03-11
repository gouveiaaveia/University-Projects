"""
Models para funcionalidades de IA.
"""
from dataclasses import dataclass, field
from typing import List, Literal
from datetime import datetime


@dataclass
class AIMessage:
    """Mensagem no chat de IA."""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ChatHistory:
    """Histórico de conversa com IA."""
    messages: List[AIMessage] = field(default_factory=list)
    
    def add_message(self, role: str, content: str):
        self.messages.append(AIMessage(role=role, content=content))
    
    def to_list(self) -> List[dict]:
        return [m.to_dict() for m in self.messages]
    
    def get_context_messages(self, limit: int = 10) -> List[dict]:
        """Retorna as últimas N mensagens para contexto."""
        recent = self.messages[-limit:] if len(self.messages) > limit else self.messages
        return [{'role': m.role, 'content': m.content} for m in recent]
