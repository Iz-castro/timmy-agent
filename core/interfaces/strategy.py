# -*- coding: utf-8 -*-
"""
Core Interfaces - Strategy
Interface para estratégias de conversação que os tenants podem implementar
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Message:
    """Estrutura padronizada de mensagem"""
    text: str
    session_key: str
    tenant_id: str = "default"
    meta: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.meta is None:
            self.meta = {}


@dataclass
class ConversationContext:
    """Contexto da conversa"""
    session_key: str
    tenant_id: str
    conversation_history: list
    user_state: Dict[str, Any]
    message_count: int = 0
    
    def __post_init__(self):
        if not self.user_state:
            self.user_state = {}


class ConversationStrategy(ABC):
    """
    Interface base para estratégias de conversação
    
    Os tenants podem implementar esta interface para definir
    estratégias específicas de conversação (consultiva, médica, etc.)
    """
    
    def __init__(self, tenant_id: str, config: Dict[str, Any] = None):
        self.tenant_id = tenant_id
        self.config = config or {}
        self.priority = self.config.get("priority", 100)  # Prioridade de execução
    
    @abstractmethod
    def should_activate(self, message: Message, context: ConversationContext) -> bool:
        """
        Determina se esta estratégia deve ser ativada para esta mensagem
        
        Args:
            message: Mensagem do usuário
            context: Contexto da conversa
            
        Returns:
            bool: True se a estratégia deve ser ativada
        """
        pass
    
    @abstractmethod
    def process_turn(self, message: Message, context: ConversationContext) -> Optional[str]:
        """
        Processa o turno da conversa usando esta estratégia
        
        Args:
            message: Mensagem do usuário
            context: Contexto da conversa
            
        Returns:
            Optional[str]: Resposta gerada ou None se não processou
        """
        pass
    
    def extract_information(self, message: Message, context: ConversationContext) -> Dict[str, Any]:
        """
        Extrai informações relevantes da mensagem (implementação opcional)
        
        Args:
            message: Mensagem do usuário
            context: Contexto da conversa
            
        Returns:
            Dict[str, Any]: Informações extraídas
        """
        return {}
    
    def update_context(self, context: ConversationContext, extracted_info: Dict[str, Any]) -> None:
        """
        Atualiza o contexto com informações extraídas (implementação opcional)
        
        Args:
            context: Contexto da conversa
            extracted_info: Informações para adicionar ao contexto
        """
        context.user_state.update(extracted_info)
    
    def get_strategy_name(self) -> str:
        """Retorna o nome da estratégia"""
        return self.__class__.__name__
    
    def get_priority(self) -> int:
        """Retorna a prioridade de execução da estratégia"""
        return self.priority