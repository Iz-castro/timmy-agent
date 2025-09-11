# -*- coding: utf-8 -*-
"""
Core Extensions - Registry (CORRIGIDO)
Sistema de registro e gerenciamento de componentes do core
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class ComponentType(Enum):
    """Tipos de componentes registráveis"""
    STRATEGY = "strategy"
    FORMATTER = "formatter"
    WORKFLOW = "workflow"
    DATABASE = "database"
    PROCESSOR = "processor"


@dataclass
class ComponentInfo:
    """Informações sobre um componente registrado"""
    name: str
    component_type: ComponentType
    tenant_id: str
    priority: int
    description: str = ""
    version: str = "1.0.0"
    dependencies: List[str] = None
    component_class: Optional[type] = None  # NOVO: Referência para a classe
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class ComponentRegistry:
    """
    Registro centralizado de todos os componentes do sistema
    
    Permite registrar, descobrir e gerenciar componentes de forma centralizada
    """
    
    def __init__(self):
        self._components: Dict[str, ComponentInfo] = {}
        self._tenant_components: Dict[str, List[str]] = {}
        self._type_components: Dict[ComponentType, List[str]] = {
            component_type: [] for component_type in ComponentType
        }
        self._hooks: Dict[str, List[Callable]] = {}
        # Adiciona referência aos tipos para compatibilidade
        self.ComponentType = ComponentType
    
    def register_component(
        self, 
        component_info: ComponentInfo,
        override: bool = False
    ) -> bool:
        """
        Registra um componente no sistema
        
        Args:
            component_info: Informações do componente
            override: Se deve sobrescrever componente existente
            
        Returns:
            bool: True se registrou com sucesso
        """
        component_key = f"{component_info.tenant_id}_{component_info.component_type.value}_{component_info.name}"
        
        # Verifica se já existe
        if component_key in self._components and not override:
            print(f"[WARNING] Componente {component_key} já existe")
            return False
        
        try:
            # Registra o componente
            self._components[component_key] = component_info
            
            # Atualiza índices
            self._update_tenant_index(component_info.tenant_id, component_key)
            self._update_type_index(component_info.component_type, component_key)
            
            # Executa hooks de registro
            self._execute_hooks("component_registered", component_info)
            
            print(f"[REGISTRY] Componente registrado: {component_key}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Erro ao registrar componente {component_key}: {e}")
            return False
    
    def unregister_component(self, tenant_id: str, component_type: ComponentType, name: str) -> bool:
        """
        Remove um componente do registro
        
        Args:
            tenant_id: ID do tenant
            component_type: Tipo do componente
            name: Nome do componente
            
        Returns:
            bool: True se removeu com sucesso
        """
        component_key = f"{tenant_id}_{component_type.value}_{name}"
        
        if component_key not in self._components:
            return False
        
        try:
            component_info = self._components[component_key]
            
            # Remove dos índices
            self._remove_from_tenant_index(tenant_id, component_key)
            self._remove_from_type_index(component_type, component_key)
            
            # Remove do registro principal
            del self._components[component_key]
            
            # Executa hooks de remoção
            self._execute_hooks("component_unregistered", component_info)
            
            print(f"[REGISTRY] Componente removido: {component_key}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Erro ao remover componente {component_key}: {e}")
            return False
    
    def get_components_by_tenant(self, tenant_id: str) -> List[ComponentInfo]:
        """
        Retorna todos os componentes de um tenant
        
        Args:
            tenant_id: ID do tenant
            
        Returns:
            List[ComponentInfo]: Lista de componentes do tenant
        """
        if tenant_id not in self._tenant_components:
            return []
        
        components = []
        for component_key in self._tenant_components[tenant_id]:
            if component_key in self._components:
                components.append(self._components[component_key])
        
        # Ordena por prioridade
        components.sort(key=lambda c: c.priority)
        return components
    
    def get_components_by_type(self, component_type: ComponentType) -> List[ComponentInfo]:
        """
        Retorna todos os componentes de um tipo
        
        Args:
            component_type: Tipo de componente
            
        Returns:
            List[ComponentInfo]: Lista de componentes do tipo
        """
        if component_type not in self._type_components:
            return []
        
        components = []
        for component_key in self._type_components[component_type]:
            if component_key in self._components:
                components.append(self._components[component_key])
        
        # Ordena por prioridade
        components.sort(key=lambda c: c.priority)
        return components
    
    def get_component(self, tenant_id: str, component_type: ComponentType, name: str) -> Optional[ComponentInfo]:
        """
        Retorna um componente específico
        
        Args:
            tenant_id: ID do tenant
            component_type: Tipo do componente
            name: Nome do componente
            
        Returns:
            Optional[ComponentInfo]: Componente ou None se não encontrado
        """
        component_key = f"{tenant_id}_{component_type.value}_{name}"
        return self._components.get(component_key)
    
    def find_components(self, **filters) -> List[ComponentInfo]:
        """
        Busca componentes usando filtros
        
        Args:
            **filters: Filtros para busca (tenant_id, component_type, name, etc.)
            
        Returns:
            List[ComponentInfo]: Lista de componentes que atendem aos filtros
        """
        results = []
        
        for component in self._components.values():
            matches = True
            
            for key, value in filters.items():
                if hasattr(component, key):
                    component_value = getattr(component, key)
                    if component_value != value:
                        matches = False
                        break
            
            if matches:
                results.append(component)
        
        # Ordena por prioridade
        results.sort(key=lambda c: c.priority)
        return results
    
    def register_hook(self, event: str, callback: Callable) -> None:
        """
        Registra um hook para eventos do registry
        
        Args:
            event: Nome do evento (component_registered, component_unregistered)
            callback: Função a ser chamada
        """
        if event not in self._hooks:
            self._hooks[event] = []
        
        self._hooks[event].append(callback)
    
    def unregister_hook(self, event: str, callback: Callable) -> None:
        """
        Remove um hook de eventos
        
        Args:
            event: Nome do evento
            callback: Função a ser removida
        """
        if event in self._hooks and callback in self._hooks[event]:
            self._hooks[event].remove(callback)
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do registry
        
        Returns:
            Dict[str, Any]: Estatísticas do sistema
        """
        tenant_stats = {}
        for tenant_id, components in self._tenant_components.items():
            tenant_stats[tenant_id] = len(components)
        
        type_stats = {}
        for component_type, components in self._type_components.items():
            type_stats[component_type.value] = len(components)
        
        return {
            "total_components": len(self._components),
            "tenants": tenant_stats,
            "types": type_stats,
            "active_hooks": {event: len(callbacks) for event, callbacks in self._hooks.items()}
        }
    
    def validate_dependencies(self, component_info: ComponentInfo) -> List[str]:
        """
        Valida se as dependências de um componente estão disponíveis
        
        Args:
            component_info: Componente a validar
            
        Returns:
            List[str]: Lista de dependências não encontradas
        """
        missing_deps = []
        
        for dep in component_info.dependencies:
            # Busca dependência no mesmo tenant
            found = False
            for comp_key, comp_info in self._components.items():
                if (comp_info.tenant_id == component_info.tenant_id and 
                    comp_info.name == dep):
                    found = True
                    break
            
            if not found:
                missing_deps.append(dep)
        
        return missing_deps
    
    def clear_tenant_components(self, tenant_id: str) -> int:
        """
        Remove todos os componentes de um tenant
        
        Args:
            tenant_id: ID do tenant
            
        Returns:
            int: Número de componentes removidos
        """
        if tenant_id not in self._tenant_components:
            return 0
        
        component_keys = self._tenant_components[tenant_id].copy()
        removed_count = 0
        
        for component_key in component_keys:
            if component_key in self._components:
                component_info = self._components[component_key]
                
                # Remove dos índices
                self._remove_from_type_index(component_info.component_type, component_key)
                
                # Remove do registro principal
                del self._components[component_key]
                removed_count += 1
        
        # Limpa índice do tenant
        del self._tenant_components[tenant_id]
        
        print(f"[REGISTRY] Removidos {removed_count} componentes do tenant {tenant_id}")
        return removed_count
    
    def register_tenant_components_from_loader(self, tenant_id: str, extensions: Dict[str, Any]) -> int:
        """
        Registra componentes carregados pelo ExtensionLoader
        
        Args:
            tenant_id: ID do tenant
            extensions: Dicionário com extensões carregadas
            
        Returns:
            int: Número de componentes registrados
        """
        registered_count = 0
        
        # Registra estratégias
        for strategy in extensions.get("strategies", []):
            component_info = ComponentInfo(
                name=strategy.get_strategy_name(),
                component_type=ComponentType.STRATEGY,
                tenant_id=tenant_id,
                priority=strategy.get_priority(),
                description=f"Estratégia de conversação para {tenant_id}",
                component_class=strategy.__class__
            )
            if self.register_component(component_info):
                registered_count += 1
        
        # Registra formatadores
        for formatter in extensions.get("formatters", []):
            component_info = ComponentInfo(
                name=formatter.get_formatter_name(),
                component_type=ComponentType.FORMATTER,
                tenant_id=tenant_id,
                priority=formatter.get_priority(),
                description=f"Formatador de resposta para {tenant_id}",
                component_class=formatter.__class__
            )
            if self.register_component(component_info):
                registered_count += 1
        
        # Registra workflows
        for workflow in extensions.get("workflows", []):
            component_info = ComponentInfo(
                name=workflow.get_workflow_name(),
                component_type=ComponentType.WORKFLOW,
                tenant_id=tenant_id,
                priority=workflow.get_priority(),
                description=f"Workflow específico para {tenant_id}",
                component_class=workflow.__class__
            )
            if self.register_component(component_info):
                registered_count += 1
        
        # Registra database
        database = extensions.get("database")
        if database:
            component_info = ComponentInfo(
                name=database.__class__.__name__,
                component_type=ComponentType.DATABASE,
                tenant_id=tenant_id,
                priority=0,  # Database tem prioridade alta
                description=f"Banco de dados para {tenant_id}",
                component_class=database.__class__
            )
            if self.register_component(component_info):
                registered_count += 1
        
        print(f"[REGISTRY] Registrados {registered_count} componentes para tenant {tenant_id}")
        return registered_count
    
    def get_extensions(self, extension_type: str) -> Dict[str, type]:
        """
        Método de compatibilidade para buscar extensões por tipo (string)
        
        Args:
            extension_type: Tipo da extensão como string
            
        Returns:
            Dict[str, type]: Dicionário com nome -> classe
        """
        try:
            # Converte string para enum
            if extension_type.upper() in [ct.name for ct in ComponentType]:
                component_type = ComponentType[extension_type.upper()]
            else:
                print(f"[WARNING] Tipo de extensão desconhecido: {extension_type}")
                return {}
            
            components = self.get_components_by_type(component_type)
            return {
                comp.name: comp.component_class 
                for comp in components 
                if comp.component_class is not None
            }
            
        except Exception as e:
            print(f"[ERROR] Erro ao buscar extensões do tipo {extension_type}: {e}")
            return {}
    
    def _update_tenant_index(self, tenant_id: str, component_key: str) -> None:
        """Atualiza índice por tenant"""
        if tenant_id not in self._tenant_components:
            self._tenant_components[tenant_id] = []
        
        if component_key not in self._tenant_components[tenant_id]:
            self._tenant_components[tenant_id].append(component_key)
    
    def _update_type_index(self, component_type: ComponentType, component_key: str) -> None:
        """Atualiza índice por tipo"""
        if component_key not in self._type_components[component_type]:
            self._type_components[component_type].append(component_key)
    
    def _remove_from_tenant_index(self, tenant_id: str, component_key: str) -> None:
        """Remove do índice por tenant"""
        if tenant_id in self._tenant_components and component_key in self._tenant_components[tenant_id]:
            self._tenant_components[tenant_id].remove(component_key)
            
            # Remove tenant se ficou vazio
            if not self._tenant_components[tenant_id]:
                del self._tenant_components[tenant_id]
    
    def _remove_from_type_index(self, component_type: ComponentType, component_key: str) -> None:
        """Remove do índice por tipo"""
        if component_key in self._type_components[component_type]:
            self._type_components[component_type].remove(component_key)
    
    def _execute_hooks(self, event: str, component_info: ComponentInfo) -> None:
        """Executa hooks registrados para um evento"""
        if event in self._hooks:
            for callback in self._hooks[event]:
                try:
                    callback(component_info)
                except Exception as e:
                    print(f"[ERROR] Erro ao executar hook {event}: {e}")


# Instância global do registry
component_registry = ComponentRegistry()