# -*- coding: utf-8 -*-
"""
Core Interfaces - Database
Interface para sistemas de banco de dados que os tenants podem implementar
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from pathlib import Path


class TenantDatabase(ABC):
    """
    Interface base para bancos de dados específicos de tenant
    
    Os tenants podem implementar esta interface para definir
    seu próprio sistema de banco de dados (SQLite, PostgreSQL, etc.)
    """
    
    def __init__(self, tenant_id: str, config: Dict[str, Any] = None):
        self.tenant_id = tenant_id
        self.config = config or {}
        self.connection = None
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Estabelece conexão com o banco de dados
        
        Returns:
            bool: True se conectou com sucesso
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """
        Fecha conexão com o banco de dados
        """
        pass
    
    @abstractmethod
    def create_tables(self) -> bool:
        """
        Cria tabelas necessárias para o tenant
        
        Returns:
            bool: True se criou com sucesso
        """
        pass
    
    @abstractmethod
    def query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Executa query no banco de dados
        
        Args:
            query: Query SQL ou equivalente
            parameters: Parâmetros da query
            
        Returns:
            List[Dict[str, Any]]: Resultados da query
        """
        pass
    
    @abstractmethod
    def insert(self, table: str, data: Dict[str, Any]) -> bool:
        """
        Insere dados na tabela
        
        Args:
            table: Nome da tabela
            data: Dados para inserir
            
        Returns:
            bool: True se inseriu com sucesso
        """
        pass
    
    @abstractmethod
    def update(self, table: str, data: Dict[str, Any], conditions: Dict[str, Any]) -> bool:
        """
        Atualiza dados na tabela
        
        Args:
            table: Nome da tabela
            data: Dados para atualizar
            conditions: Condições para o update
            
        Returns:
            bool: True se atualizou com sucesso
        """
        pass
    
    @abstractmethod
    def delete(self, table: str, conditions: Dict[str, Any]) -> bool:
        """
        Remove dados da tabela
        
        Args:
            table: Nome da tabela
            conditions: Condições para remoção
            
        Returns:
            bool: True se removeu com sucesso
        """
        pass
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o banco (implementação opcional)
        
        Returns:
            Dict[str, Any]: Informações do banco
        """
        return {
            "tenant_id": self.tenant_id,
            "database_type": self.__class__.__name__,
            "connected": self.connection is not None
        }


class SQLiteDatabase(TenantDatabase):
    """
    Implementação base para bancos SQLite específicos de tenant
    """
    
    def __init__(self, tenant_id: str, config: Dict[str, Any] = None):
        super().__init__(tenant_id, config)
        self.database_path = self._get_database_path()
    
    def _get_database_path(self) -> Path:
        """
        Retorna caminho do arquivo do banco SQLite
        
        Returns:
            Path: Caminho do arquivo do banco
        """
        tenant_dir = Path(f"tenants/{self.tenant_id}")
        tenant_dir.mkdir(parents=True, exist_ok=True)
        return tenant_dir / "database.db"
    
    def connect(self) -> bool:
        """
        Conecta ao banco SQLite
        
        Returns:
            bool: True se conectou com sucesso
        """
        try:
            import sqlite3
            self.connection = sqlite3.connect(str(self.database_path))
            self.connection.row_factory = sqlite3.Row  # Para retornar dicts
            return True
        except Exception as e:
            print(f"[ERROR] Erro ao conectar SQLite para {self.tenant_id}: {e}")
            return False
    
    def disconnect(self) -> None:
        """
        Desconecta do banco SQLite
        """
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def create_tables(self) -> bool:
        """
        Cria tabelas básicas (implementação padrão)
        
        Returns:
            bool: True se criou com sucesso
        """
        if not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # Tabela de configurações genérica
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tenant_config (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.connection.commit()
            return True
            
        except Exception as e:
            print(f"[ERROR] Erro ao criar tabelas para {self.tenant_id}: {e}")
            return False
    
    def query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Executa query no SQLite
        
        Args:
            query: Query SQL
            parameters: Parâmetros da query
            
        Returns:
            List[Dict[str, Any]]: Resultados da query
        """
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)
            
            # Converte Row objects para dicts
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            print(f"[ERROR] Erro na query para {self.tenant_id}: {e}")
            return []
    
    def insert(self, table: str, data: Dict[str, Any]) -> bool:
        """
        Insere dados na tabela SQLite
        
        Args:
            table: Nome da tabela
            data: Dados para inserir
            
        Returns:
            bool: True se inseriu com sucesso
        """
        if not self.connection or not data:
            return False
        
        try:
            cursor = self.connection.cursor()
            
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            
            cursor.execute(query, list(data.values()))
            self.connection.commit()
            return True
            
        except Exception as e:
            print(f"[ERROR] Erro ao inserir em {table} para {self.tenant_id}: {e}")
            return False
    
    def update(self, table: str, data: Dict[str, Any], conditions: Dict[str, Any]) -> bool:
        """
        Atualiza dados na tabela SQLite
        
        Args:
            table: Nome da tabela
            data: Dados para atualizar
            conditions: Condições para o update
            
        Returns:
            bool: True se atualizou com sucesso
        """
        if not self.connection or not data or not conditions:
            return False
        
        try:
            cursor = self.connection.cursor()
            
            set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
            where_clause = ' AND '.join([f"{key} = ?" for key in conditions.keys()])
            query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
            
            parameters = list(data.values()) + list(conditions.values())
            cursor.execute(query, parameters)
            self.connection.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"[ERROR] Erro ao atualizar {table} para {self.tenant_id}: {e}")
            return False
    
    def delete(self, table: str, conditions: Dict[str, Any]) -> bool:
        """
        Remove dados da tabela SQLite
        
        Args:
            table: Nome da tabela
            conditions: Condições para remoção
            
        Returns:
            bool: True se removeu com sucesso
        """
        if not self.connection or not conditions:
            return False
        
        try:
            cursor = self.connection.cursor()
            
            where_clause = ' AND '.join([f"{key} = ?" for key in conditions.keys()])
            query = f"DELETE FROM {table} WHERE {where_clause}"
            
            cursor.execute(query, list(conditions.values()))
            self.connection.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"[ERROR] Erro ao deletar de {table} para {self.tenant_id}: {e}")
            return False