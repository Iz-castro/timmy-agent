# -*- coding: utf-8 -*-
"""
Core Interfaces - Package Init
Centraliza imports das interfaces principais
"""

from .strategy import ConversationStrategy, Message, ConversationContext
from .formatter import ResponseFormatter, StructuredResponseFormatter, MicroResponseFormatter
from .workflow import TenantWorkflow, DatabaseWorkflow, APIWorkflow
from .database import TenantDatabase, SQLiteDatabase

__all__ = [
    # Strategy interfaces
    'ConversationStrategy',
    'Message', 
    'ConversationContext',
    
    # Formatter interfaces
    'ResponseFormatter',
    'StructuredResponseFormatter',
    'MicroResponseFormatter',
    
    # Workflow interfaces
    'TenantWorkflow',
    'DatabaseWorkflow', 
    'APIWorkflow',
    
    # Database interfaces
    'TenantDatabase',
    'SQLiteDatabase'
]