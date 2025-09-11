# -*- coding: utf-8 -*-
"""
Core Extensions - Loader (CORRIGIDO)
Sistema para carregar extensões específicas dos tenants
"""

import importlib.util
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Type

from core.interfaces.strategy import ConversationStrategy
from core.interfaces.formatter import ResponseFormatter
from core.interfaces.workflow import TenantWorkflow
from core.interfaces.database import TenantDatabase


class ExtensionLoader:
    """
    Sistema para carregar estratégias, formatadores, workflows e bancos de dados
    específicos dos tenants
    """
    
    def __init__(self):
        self._cache = {}
        self._loaded_modules = {}
    
    def load_tenant_strategies(self, tenant_id: str) -> List[ConversationStrategy]:
        """
        Carrega todas as estratégias de conversação do tenant
        
        Args:
            tenant_id: ID do tenant
            
        Returns:
            List[ConversationStrategy]: Lista de estratégias ordenadas por prioridade
        """
        cache_key = f"{tenant_id}_strategies"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        strategies = []
        tenant_path = Path(f"tenants/{tenant_id}")
        
        # Carrega configuração do tenant
        config = self._load_tenant_config(tenant_id)
        
        # Procura por estratégias em strategies/
        strategies_dir = tenant_path / "strategies"
        if strategies_dir.exists():
            for strategy_file in strategies_dir.glob("*.py"):
                if strategy_file.name.startswith("__"):
                    continue
                
                strategy_class = self._load_class_from_file(
                    strategy_file, 
                    ConversationStrategy
                )
                
                if strategy_class:
                    try:
                        strategy = strategy_class(tenant_id, config)
                        strategies.append(strategy)
                        print(f"[LOADER] Estratégia carregada: {strategy_class.__name__} para {tenant_id}")
                    except Exception as e:
                        print(f"[ERROR] Erro ao instanciar estratégia {strategy_file.name}: {e}")
        
        # Ordena por prioridade (menor número = maior prioridade)
        strategies.sort(key=lambda s: s.get_priority())
        
        self._cache[cache_key] = strategies
        return strategies
    
    def load_tenant_formatters(self, tenant_id: str) -> List[ResponseFormatter]:
        """
        Carrega todos os formatadores do tenant
        
        Args:
            tenant_id: ID do tenant
            
        Returns:
            List[ResponseFormatter]: Lista de formatadores ordenados por prioridade
        """
        cache_key = f"{tenant_id}_formatters"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        formatters = []
        tenant_path = Path(f"tenants/{tenant_id}")
        
        # Carrega configuração do tenant
        config = self._load_tenant_config(tenant_id)
        
        # Procura por formatadores em formatters/
        formatters_dir = tenant_path / "formatters"
        if formatters_dir.exists():
            for formatter_file in formatters_dir.glob("*.py"):
                if formatter_file.name.startswith("__"):
                    continue
                
                formatter_class = self._load_class_from_file(
                    formatter_file, 
                    ResponseFormatter
                )
                
                if formatter_class:
                    try:
                        formatter = formatter_class(tenant_id, config)
                        formatters.append(formatter)
                        print(f"[LOADER] Formatador carregado: {formatter_class.__name__} para {tenant_id}")
                    except Exception as e:
                        print(f"[ERROR] Erro ao instanciar formatador {formatter_file.name}: {e}")
        
        # Ordena por prioridade
        formatters.sort(key=lambda f: f.get_priority())
        
        self._cache[cache_key] = formatters
        return formatters
    
    def load_tenant_workflows(self, tenant_id: str) -> List[TenantWorkflow]:
        """
        Carrega todos os workflows do tenant
        
        Args:
            tenant_id: ID do tenant
            
        Returns:
            List[TenantWorkflow]: Lista de workflows ordenados por prioridade
        """
        cache_key = f"{tenant_id}_workflows"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        workflows = []
        tenant_path = Path(f"tenants/{tenant_id}")
        
        # Carrega configuração do tenant
        config = self._load_tenant_config(tenant_id)
        
        # Procura por workflows em workflows/
        workflows_dir = tenant_path / "workflows"
        if workflows_dir.exists():
            for workflow_file in workflows_dir.glob("*.py"):
                if workflow_file.name.startswith("__"):
                    continue
                
                workflow_class = self._load_class_from_file(
                    workflow_file, 
                    TenantWorkflow
                )
                
                if workflow_class:
                    try:
                        workflow = workflow_class(tenant_id, config)
                        workflows.append(workflow)
                        print(f"[LOADER] Workflow carregado: {workflow_class.__name__} para {tenant_id}")
                    except Exception as e:
                        print(f"[ERROR] Erro ao instanciar workflow {workflow_file.name}: {e}")
        
        # Ordena por prioridade
        workflows.sort(key=lambda w: w.get_priority())
        
        self._cache[cache_key] = workflows
        return workflows
    
    def load_tenant_database(self, tenant_id: str) -> Optional[TenantDatabase]:
        """
        Carrega o banco de dados específico do tenant
        
        Args:
            tenant_id: ID do tenant
            
        Returns:
            Optional[TenantDatabase]: Instância do banco ou None
        """
        cache_key = f"{tenant_id}_database"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        tenant_path = Path(f"tenants/{tenant_id}")
        config = self._load_tenant_config(tenant_id)
        
        # Procura por database.py no diretório do tenant
        database_file = tenant_path / "database.py"
        if database_file.exists():
            database_class = self._load_class_from_file(
                database_file, 
                TenantDatabase
            )
            
            if database_class:
                try:
                    database = database_class(tenant_id, config)
                    print(f"[LOADER] Database carregado: {database_class.__name__} para {tenant_id}")
                    self._cache[cache_key] = database
                    return database
                except Exception as e:
                    print(f"[ERROR] Erro ao instanciar database para {tenant_id}: {e}")
        
        # Se não encontrou database específico, retorna None
        print(f"[LOADER] Nenhum database específico encontrado para {tenant_id}")
        self._cache[cache_key] = None
        return None
    
    def load_all_tenant_extensions(self, tenant_id: str) -> Dict[str, Any]:
        """
        Carrega todas as extensões de um tenant de uma vez
        
        Args:
            tenant_id: ID do tenant
            
        Returns:
            Dict[str, Any]: Todas as extensões carregadas
        """
        return {
            "strategies": self.load_tenant_strategies(tenant_id),
            "formatters": self.load_tenant_formatters(tenant_id),
            "workflows": self.load_tenant_workflows(tenant_id),
            "database": self.load_tenant_database(tenant_id)
        }
    
    def _load_class_from_file(self, file_path: Path, base_class: Type) -> Optional[Type]:
        """
        Carrega uma classe de um arquivo específico
        
        Args:
            file_path: Caminho do arquivo Python
            base_class: Classe base que deve ser herdada
            
        Returns:
            Optional[Type]: Classe carregada ou None
        """
        try:
            # Verifica se já foi carregado
            module_key = str(file_path)
            if module_key in self._loaded_modules:
                module = self._loaded_modules[module_key]
            else:
                # Carrega o módulo
                spec = importlib.util.spec_from_file_location(
                    file_path.stem, 
                    file_path
                )
                
                if not spec or not spec.loader:
                    print(f"[WARNING] Não foi possível criar spec para {file_path}")
                    return None
                
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self._loaded_modules[module_key] = module
            
            # Procura por classes que herdam da base_class
            found_classes = []
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                
                if (isinstance(attr, type) and 
                    issubclass(attr, base_class) and 
                    attr != base_class):
                    found_classes.append(attr)
            
            if len(found_classes) == 1:
                return found_classes[0]
            elif len(found_classes) > 1:
                print(f"[WARNING] Múltiplas classes encontradas em {file_path}: {[c.__name__ for c in found_classes]}")
                return found_classes[0]  # Retorna a primeira
            else:
                print(f"[WARNING] Nenhuma classe válida encontrada em {file_path}")
                return None
            
        except Exception as e:
            print(f"[ERROR] Erro ao carregar classe de {file_path}: {e}")
            import traceback
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            return None
    
    def _load_tenant_config(self, tenant_id: str) -> Dict[str, Any]:
        """
        Carrega configuração do tenant
        
        Args:
            tenant_id: ID do tenant
            
        Returns:
            Dict[str, Any]: Configuração do tenant
        """
        config_cache_key = f"{tenant_id}_config"
        
        if config_cache_key in self._cache:
            return self._cache[config_cache_key]
        
        tenant_path = Path(f"tenants/{tenant_id}")
        config_file = tenant_path / "config.json"
        
        config = {}
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    print(f"[LOADER] Configuração carregada para {tenant_id}")
            except Exception as e:
                print(f"[ERROR] Erro ao carregar config.json para {tenant_id}: {e}")
        else:
            print(f"[WARNING] Arquivo config.json não encontrado para {tenant_id}")
        
        # Carrega também knowledge.json se existir
        knowledge_file = tenant_path / "knowledge.json"
        if knowledge_file.exists():
            try:
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    knowledge = json.load(f)
                    config["knowledge"] = knowledge
                    print(f"[LOADER] Base de conhecimento carregada para {tenant_id}")
            except Exception as e:
                print(f"[ERROR] Erro ao carregar knowledge.json para {tenant_id}: {e}")
        
        self._cache[config_cache_key] = config
        return config
    
    def clear_cache(self, tenant_id: Optional[str] = None) -> None:
        """
        Limpa cache de extensões
        
        Args:
            tenant_id: ID específico para limpar ou None para limpar tudo
        """
        if tenant_id:
            # Remove entradas específicas do tenant
            keys_to_remove = [
                key for key in self._cache.keys() 
                if key.startswith(f"{tenant_id}_")
            ]
            for key in keys_to_remove:
                del self._cache[key]
            print(f"[LOADER] Cache limpo para tenant {tenant_id}")
        else:
            # Limpa todo o cache
            self._cache.clear()
            self._loaded_modules.clear()
            print(f"[LOADER] Cache completo limpo")
    
    def reload_tenant_extensions(self, tenant_id: str) -> Dict[str, Any]:
        """
        Recarrega todas as extensões de um tenant (força atualização)
        
        Args:
            tenant_id: ID do tenant
            
        Returns:
            Dict[str, Any]: Extensões recarregadas
        """
        print(f"[LOADER] Recarregando extensões para tenant {tenant_id}")
        self.clear_cache(tenant_id)
        return self.load_all_tenant_extensions(tenant_id)
    
    def get_loaded_extensions_info(self, tenant_id: str) -> Dict[str, Any]:
        """
        Retorna informações sobre as extensões carregadas
        
        Args:
            tenant_id: ID do tenant
            
        Returns:
            Dict[str, Any]: Informações das extensões
        """
        strategies = self.load_tenant_strategies(tenant_id)
        formatters = self.load_tenant_formatters(tenant_id)
        workflows = self.load_tenant_workflows(tenant_id)
        database = self.load_tenant_database(tenant_id)
        
        return {
            "tenant_id": tenant_id,
            "strategies": [
                {
                    "name": s.get_strategy_name(),
                    "priority": s.get_priority(),
                    "class": s.__class__.__name__
                } for s in strategies
            ],
            "formatters": [
                {
                    "name": f.get_formatter_name(),
                    "priority": f.get_priority(),
                    "class": f.__class__.__name__
                } for f in formatters
            ],
            "workflows": [
                {
                    "name": w.get_workflow_name(),
                    "priority": w.get_priority(),
                    "class": w.__class__.__name__
                } for w in workflows
            ],
            "database": {
                "available": database is not None,
                "type": database.__class__.__name__ if database else None,
                "connected": getattr(database, 'connection', None) is not None if database else False
            },
            "totals": {
                "strategies": len(strategies),
                "formatters": len(formatters),
                "workflows": len(workflows),
                "database": 1 if database else 0
            }
        }
    
    def validate_tenant_structure(self, tenant_id: str) -> Dict[str, Any]:
        """
        Valida se a estrutura do tenant está correta
        
        Args:
            tenant_id: ID do tenant
            
        Returns:
            Dict[str, Any]: Resultado da validação
        """
        tenant_path = Path(f"tenants/{tenant_id}")
        
        validation = {
            "tenant_id": tenant_id,
            "base_directory_exists": tenant_path.exists(),
            "config_file_exists": (tenant_path / "config.json").exists(),
            "knowledge_file_exists": (tenant_path / "knowledge.json").exists(),
            "extensions_directories": {},
            "errors": [],
            "warnings": []
        }
        
        if not validation["base_directory_exists"]:
            validation["errors"].append(f"Diretório do tenant não existe: {tenant_path}")
            return validation
        
        # Verifica diretórios de extensões
        extension_dirs = ["strategies", "formatters", "workflows"]
        for ext_dir in extension_dirs:
            dir_path = tenant_path / ext_dir
            validation["extensions_directories"][ext_dir] = {
                "exists": dir_path.exists(),
                "files": list(dir_path.glob("*.py")) if dir_path.exists() else []
            }
        
        # Verifica se existem arquivos Python válidos
        total_extensions = sum(
            len(info["files"]) 
            for info in validation["extensions_directories"].values()
        )
        
        if total_extensions == 0:
            validation["warnings"].append("Nenhuma extensão Python encontrada")
        
        # Verifica arquivos de configuração
        if not validation["config_file_exists"]:
            validation["warnings"].append("Arquivo config.json não encontrado")
        
        if not validation["knowledge_file_exists"]:
            validation["warnings"].append("Arquivo knowledge.json não encontrado")
        
        return validation


# Instância global do loader
extension_loader = ExtensionLoader()