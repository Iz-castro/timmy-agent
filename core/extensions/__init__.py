# -*- coding: utf-8 -*-
"""
Core Extensions - Package Init
Centraliza sistema de registro e carregamento de extensões
"""

from .registry import ComponentRegistry, ComponentType, ComponentInfo, component_registry
from .loader import ExtensionLoader, extension_loader

__all__ = [
    # Registry system
    'ComponentRegistry',
    'ComponentType',
    'ComponentInfo',
    'component_registry',  # Instância global
    
    # Loader system
    'ExtensionLoader',
    'extension_loader'  # Instância global
]