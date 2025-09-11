# -*- coding: utf-8 -*-
"""
Core Interfaces - Workflow
Interface para workflows específicos que os tenants podem implementar
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from .strategy import Message, ConversationContext


class TenantWorkflow(ABC):
    """
    Interface base para workflows específicos de tenant
    
    Os tenants podem implementar esta interface para definir
    fluxos de trabalho específicos (médico, vendas, atendimento, etc.)
    """
    
    def __init__(self, tenant_id: str, config: Dict[str, Any] = None):
        self.tenant_id = tenant_id
        self.config = config or {}
        self.priority = self.config.get("priority", 50)  # Prioridade média
    
    @abstractmethod
    def should_activate(self, message: Message, context: ConversationContext) -> bool:
        """
        Determina se este workflow deve ser ativado
        
        Args:
            message: Mensagem do usuário
            context: Contexto da conversa
            
        Returns:
            bool: True se o workflow deve ser ativado
        """
        pass
    
    @abstractmethod
    def process_message(self, message: Message, context: ConversationContext) -> Optional[str]:
        """
        Processa a mensagem através do workflow específico
        
        Args:
            message: Mensagem do usuário
            context: Contexto da conversa
            
        Returns:
            Optional[str]: Resposta gerada ou None se não processou
        """
        pass
    
    def initialize_workflow(self, context: ConversationContext) -> None:
        """
        Inicializa o workflow para uma nova sessão (implementação opcional)
        
        Args:
            context: Contexto da conversa
        """
        pass
    
    def finalize_workflow(self, context: ConversationContext) -> None:
        """
        Finaliza o workflow para a sessão (implementação opcional)
        
        Args:
            context: Contexto da conversa
        """
        pass
    
    def get_workflow_state(self, context: ConversationContext) -> Dict[str, Any]:
        """
        Retorna o estado atual do workflow (implementação opcional)
        
        Args:
            context: Contexto da conversa
            
        Returns:
            Dict[str, Any]: Estado do workflow
        """
        return context.user_state.get(f"workflow_{self.get_workflow_name()}", {})
    
    def update_workflow_state(self, context: ConversationContext, state_updates: Dict[str, Any]) -> None:
        """
        Atualiza o estado do workflow (implementação opcional)
        
        Args:
            context: Contexto da conversa
            state_updates: Atualizações para o estado
        """
        workflow_key = f"workflow_{self.get_workflow_name()}"
        current_state = context.user_state.get(workflow_key, {})
        current_state.update(state_updates)
        context.user_state[workflow_key] = current_state
    
    def get_workflow_name(self) -> str:
        """Retorna o nome do workflow"""
        return self.__class__.__name__
    
    def get_priority(self) -> int:
        """Retorna a prioridade de execução do workflow"""
        return self.priority


class DatabaseWorkflow(TenantWorkflow):
    """
    Workflow base para tenants que utilizam banco de dados
    """
    
    def __init__(self, tenant_id: str, config: Dict[str, Any] = None):
        super().__init__(tenant_id, config)
        self.database_config = config.get("database", {}) if config else {}
    
    @abstractmethod
    def get_database_session(self):
        """
        Retorna sessão do banco de dados específico do tenant
        
        Returns:
            Database session object
        """
        pass
    
    def query_database(self, query_type: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Interface genérica para consultas ao banco (implementação opcional)
        
        Args:
            query_type: Tipo de consulta (find_doctors, get_plans, etc.)
            parameters: Parâmetros da consulta
            
        Returns:
            List[Dict[str, Any]]: Resultados da consulta
        """
        return []
    
    def format_database_results(self, results: List[Dict[str, Any]], query_type: str) -> str:
        """
        Formata resultados do banco para resposta (implementação opcional)
        
        Args:
            results: Resultados da consulta
            query_type: Tipo de consulta realizada
            
        Returns:
            str: Resposta formatada
        """
        return "Resultados encontrados no banco de dados."


class APIWorkflow(TenantWorkflow):
    """
    Workflow base para tenants que integram com APIs externas
    """
    
    def __init__(self, tenant_id: str, config: Dict[str, Any] = None):
        super().__init__(tenant_id, config)
        self.api_config = config.get("api", {}) if config else {}
    
    @abstractmethod
    def make_api_call(self, endpoint: str, method: str = "GET", data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Realiza chamada para API externa
        
        Args:
            endpoint: Endpoint da API
            method: Método HTTP
            data: Dados para enviar
            
        Returns:
            Dict[str, Any]: Resposta da API
        """
        pass
    
    def handle_api_error(self, error: Exception, endpoint: str) -> str:
        """
        Trata erros de API (implementação opcional)
        
        Args:
            error: Exceção ocorrida
            endpoint: Endpoint que causou o erro
            
        Returns:
            str: Mensagem de erro para o usuário
        """
        return "Ocorreu um problema ao consultar informações externas."
    
    def format_api_response(self, response: Dict[str, Any], endpoint: str) -> str:
        """
        Formata resposta da API para o usuário (implementação opcional)
        
        Args:
            response: Resposta da API
            endpoint: Endpoint consultado
            
        Returns:
            str: Resposta formatada para o usuário
        """
        return "Informações obtidas com sucesso."