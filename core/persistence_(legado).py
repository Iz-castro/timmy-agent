# -*- coding: utf-8 -*-
"""
Core Persistence - Sistema de persistência organizado por tenant
Estrutura: data/{tenant}/{conversations|sessions|users}/
"""

import csv
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import uuid

# Diretório base para dados
DATA_DIR = Path("data")

def get_tenant_data_structure(tenant_id: str) -> Dict[str, Path]:
    """Retorna estrutura de diretórios para um tenant específico"""
    tenant_dir = DATA_DIR / tenant_id
    
    return {
        "base": tenant_dir,
        "conversations": tenant_dir / "conversations",
        "sessions": tenant_dir / "sessions", 
        "users": tenant_dir / "users"
    }

def ensure_tenant_directories(tenant_id: str) -> None:
    """Garante que todos os diretórios do tenant existam"""
    structure = get_tenant_data_structure(tenant_id)
    
    for directory in structure.values():
        directory.mkdir(parents=True, exist_ok=True)
        
    print(f"[PERSISTENCE] Estrutura criada para tenant: {tenant_id}")


@dataclass
class UserInfo:
    """Estrutura para informações do usuário"""
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    location: Optional[str] = None
    age: Optional[str] = None
    interests: Optional[str] = None
    preferences: Optional[str] = None
    notes: Optional[str] = None
    tenant_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()


@dataclass
class SessionInfo:
    """Estrutura para informações da sessão"""
    session_id: str
    user_id: Optional[str] = None
    tenant_id: str = "default"
    channel: str = "streamlit"  # streamlit, whatsapp, telegram, etc.
    phone_number: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    message_count: int = 0
    status: str = "active"  # active, completed, abandoned
    intent: Optional[str] = None
    satisfaction: Optional[str] = None
    converted: bool = False
    metadata: Optional[str] = None
    
    def __post_init__(self):
        if not self.start_time:
            self.start_time = datetime.now().isoformat()


@dataclass
class ConversationMessage:
    """Estrutura para mensagens da conversa"""
    message_id: str
    session_id: str
    user_id: Optional[str]
    timestamp: str
    role: str  # user, assistant, system
    content: str
    intent: Optional[str] = None
    sentiment: Optional[str] = None
    extracted_info: Optional[str] = None
    response_time_ms: Optional[int] = None
    
    def __post_init__(self):
        if not self.message_id:
            self.message_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class EnhancedPersistenceManager:
    """Gerenciador de persistência organizado por tenant"""
    
    def __init__(self):
        # Garantir que o diretório base existe
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    def _get_users_file(self, tenant_id: str) -> Path:
        """Retorna caminho do arquivo de usuários do tenant"""
        ensure_tenant_directories(tenant_id)
        return get_tenant_data_structure(tenant_id)["users"] / "users.csv"
    
    def _get_sessions_file(self, tenant_id: str) -> Path:
        """Retorna caminho do arquivo de sessões do tenant"""
        ensure_tenant_directories(tenant_id)
        return get_tenant_data_structure(tenant_id)["sessions"] / "sessions.csv"
    
    def _get_conversation_file(self, tenant_id: str, session_id: str) -> Path:
        """Retorna caminho do arquivo de conversa específica"""
        ensure_tenant_directories(tenant_id)
        conversations_dir = get_tenant_data_structure(tenant_id)["conversations"]
        return conversations_dir / f"conversation_{session_id}.csv"
    
    def _init_users_csv(self, file_path: Path) -> None:
        """Inicializa arquivo CSV de usuários"""
        if not file_path.exists():
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'user_id', 'name', 'email', 'phone', 'company', 'job_title',
                    'location', 'age', 'interests', 'preferences', 'notes', 
                    'tenant_id', 'created_at', 'updated_at'
                ])
                writer.writeheader()
    
    def _init_sessions_csv(self, file_path: Path) -> None:
        """Inicializa arquivo CSV de sessões"""
        if not file_path.exists():
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'session_id', 'user_id', 'tenant_id', 'channel', 'phone_number',
                    'start_time', 'end_time', 'message_count', 'status', 'intent',
                    'satisfaction', 'converted', 'metadata'
                ])
                writer.writeheader()
    
    def _init_conversation_csv(self, file_path: Path) -> None:
        """Inicializa arquivo CSV de conversa"""
        if not file_path.exists():
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'message_id', 'session_id', 'user_id', 'timestamp', 'role',
                    'content', 'intent', 'sentiment', 'extracted_info', 'response_time_ms'
                ])
                writer.writeheader()
    
    def save_user_info(self, user_info: UserInfo) -> bool:
        """Salva informações do usuário no tenant específico"""
        try:
            tenant_id = user_info.tenant_id or "default"
            users_file = self._get_users_file(tenant_id)
            self._init_users_csv(users_file)
            
            # Verifica se usuário já existe
            existing_user = self.get_user_by_id(user_info.user_id, tenant_id)
            
            if existing_user:
                # Atualiza usuário existente
                self._update_user_in_csv(users_file, user_info)
            else:
                # Adiciona novo usuário
                self._append_user_to_csv(users_file, user_info)
            
            print(f"[PERSISTENCE] Usuário salvo: {user_info.user_id} no tenant {tenant_id}")
            return True
        except Exception as e:
            print(f"[ERROR] Erro ao salvar usuário: {e}")
            return False
    
    def save_session_info(self, session_info: SessionInfo) -> bool:
        """Salva informações da sessão no tenant específico"""
        try:
            tenant_id = session_info.tenant_id
            sessions_file = self._get_sessions_file(tenant_id)
            self._init_sessions_csv(sessions_file)
            
            # Verifica se sessão já existe
            existing_session = self.get_session_by_id(session_info.session_id, tenant_id)
            
            if existing_session:
                # Atualiza sessão existente
                self._update_session_in_csv(sessions_file, session_info)
            else:
                # Adiciona nova sessão
                self._append_session_to_csv(sessions_file, session_info)
            
            print(f"[PERSISTENCE] Sessão salva: {session_info.session_id} no tenant {tenant_id}")
            return True
        except Exception as e:
            print(f"[ERROR] Erro ao salvar sessão: {e}")
            return False
    
    def save_message(self, message: ConversationMessage, tenant_id: str) -> bool:
        """Salva mensagem na conversa específica do tenant"""
        try:
            conversation_file = self._get_conversation_file(tenant_id, message.session_id)
            self._init_conversation_csv(conversation_file)
            
            with open(conversation_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'message_id', 'session_id', 'user_id', 'timestamp', 'role',
                    'content', 'intent', 'sentiment', 'extracted_info', 'response_time_ms'
                ])
                writer.writerow(asdict(message))
            
            print(f"[PERSISTENCE] Mensagem salva: {message.session_id} no tenant {tenant_id}")
            return True
        except Exception as e:
            print(f"[ERROR] Erro ao salvar mensagem: {e}")
            return False
    
    def get_user_by_id(self, user_id: str, tenant_id: str = "default") -> Optional[UserInfo]:
        """Busca usuário por ID no tenant específico"""
        try:
            users_file = self._get_users_file(tenant_id)
            if not users_file.exists():
                return None
                
            with open(users_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['user_id'] == user_id:
                        return UserInfo(**row)
        except Exception as e:
            print(f"[ERROR] Erro ao buscar usuário: {e}")
        return None
    
    def get_user_by_phone(self, phone: str, tenant_id: str = "default") -> Optional[UserInfo]:
        """Busca usuário por telefone no tenant específico"""
        try:
            users_file = self._get_users_file(tenant_id)
            if not users_file.exists():
                return None
                
            with open(users_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['phone'] == phone:
                        return UserInfo(**row)
        except Exception as e:
            print(f"[ERROR] Erro ao buscar usuário por telefone: {e}")
        return None
    
    def get_session_by_id(self, session_id: str, tenant_id: str = "default") -> Optional[SessionInfo]:
        """Busca sessão por ID no tenant específico"""
        try:
            sessions_file = self._get_sessions_file(tenant_id)
            if not sessions_file.exists():
                return None
                
            with open(sessions_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['session_id'] == session_id:
                        # Converte campos específicos
                        row['message_count'] = int(row['message_count'] or 0)
                        row['converted'] = row['converted'].lower() == 'true'
                        return SessionInfo(**row)
        except Exception as e:
            print(f"[ERROR] Erro ao buscar sessão: {e}")
        return None
    
    def get_session_messages(self, session_id: str, tenant_id: str = "default") -> List[ConversationMessage]:
        """Busca todas as mensagens de uma sessão específica"""
        messages = []
        try:
            conversation_file = self._get_conversation_file(tenant_id, session_id)
            if not conversation_file.exists():
                return messages
                
            with open(conversation_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Converte campos específicos
                    if row['response_time_ms']:
                        row['response_time_ms'] = int(row['response_time_ms'])
                    messages.append(ConversationMessage(**row))
        except Exception as e:
            print(f"[ERROR] Erro ao buscar mensagens da sessão: {e}")
        return messages
    
    def get_user_sessions(self, user_id: str, tenant_id: str = "default") -> List[SessionInfo]:
        """Busca todas as sessões de um usuário no tenant específico"""
        sessions = []
        try:
            sessions_file = self._get_sessions_file(tenant_id)
            if not sessions_file.exists():
                return sessions
                
            with open(sessions_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['user_id'] == user_id:
                        row['message_count'] = int(row['message_count'] or 0)
                        row['converted'] = row['converted'].lower() == 'true'
                        sessions.append(SessionInfo(**row))
        except Exception as e:
            print(f"[ERROR] Erro ao buscar sessões do usuário: {e}")
        return sessions
    
    def _append_user_to_csv(self, file_path: Path, user_info: UserInfo):
        """Adiciona usuário ao CSV"""
        with open(file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'user_id', 'name', 'email', 'phone', 'company', 'job_title',
                'location', 'age', 'interests', 'preferences', 'notes',
                'tenant_id', 'created_at', 'updated_at'
            ])
            writer.writerow(asdict(user_info))
    
    def _append_session_to_csv(self, file_path: Path, session_info: SessionInfo):
        """Adiciona sessão ao CSV"""
        with open(file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'session_id', 'user_id', 'tenant_id', 'channel', 'phone_number',
                'start_time', 'end_time', 'message_count', 'status', 'intent',
                'satisfaction', 'converted', 'metadata'
            ])
            writer.writerow(asdict(session_info))
    
    def _update_user_in_csv(self, file_path: Path, user_info: UserInfo):
        """Atualiza usuário no CSV"""
        self._update_csv_record(file_path, 'user_id', user_info.user_id, asdict(user_info))
    
    def _update_session_in_csv(self, file_path: Path, session_info: SessionInfo):
        """Atualiza sessão no CSV"""
        self._update_csv_record(file_path, 'session_id', session_info.session_id, asdict(session_info))
    
    def _update_csv_record(self, file_path: Path, key_field: str, key_value: str, new_data: Dict):
        """Atualiza um registro específico no CSV"""
        try:
            # Lê todos os dados
            rows = []
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                for row in reader:
                    if row[key_field] == key_value:
                        # Atualiza o registro
                        rows.append(new_data)
                    else:
                        rows.append(row)
            
            # Reescreve o arquivo
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        
        except Exception as e:
            print(f"[ERROR] Erro ao atualizar CSV: {e}")
    
    def update_session_message_count(self, session_id: str, tenant_id: str = "default"):
        """Incrementa contador de mensagens da sessão"""
        session = self.get_session_by_id(session_id, tenant_id)
        if session:
            session.message_count += 1
            self.save_session_info(session)
    
    def close_session(self, session_id: str, tenant_id: str = "default", status: str = "completed"):
        """Fecha uma sessão"""
        session = self.get_session_by_id(session_id, tenant_id)
        if session:
            session.end_time = datetime.now().isoformat()
            session.status = status
            self.save_session_info(session)
    
    def get_tenant_stats(self, tenant_id: str = "default") -> Dict[str, Any]:
        """Retorna estatísticas de um tenant específico"""
        try:
            structure = get_tenant_data_structure(tenant_id)
            
            # Conta usuários
            user_count = 0
            users_file = structure["users"] / "users.csv"
            if users_file.exists():
                with open(users_file, 'r', encoding='utf-8') as f:
                    user_count = sum(1 for line in f) - 1  # -1 para header
            
            # Conta sessões
            session_count = 0
            active_sessions = 0
            sessions_file = structure["sessions"] / "sessions.csv"
            if sessions_file.exists():
                with open(sessions_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        session_count += 1
                        if row['status'] == 'active':
                            active_sessions += 1
            
            # Conta conversas (arquivos CSV)
            conversation_count = 0
            conversations_dir = structure["conversations"]
            if conversations_dir.exists():
                conversation_count = len(list(conversations_dir.glob("conversation_*.csv")))
            
            # Conta mensagens totais
            total_messages = 0
            if conversations_dir.exists():
                for conv_file in conversations_dir.glob("conversation_*.csv"):
                    with open(conv_file, 'r', encoding='utf-8') as f:
                        total_messages += sum(1 for line in f) - 1  # -1 para header
            
            return {
                "tenant_id": tenant_id,
                "total_users": user_count,
                "total_sessions": session_count,
                "active_sessions": active_sessions,
                "total_conversations": conversation_count,
                "total_messages": total_messages,
                "data_directory": str(structure["base"].absolute())
            }
        
        except Exception as e:
            print(f"[ERROR] Erro ao obter estatísticas do tenant {tenant_id}: {e}")
            return {"error": str(e)}
    
    def get_all_tenants_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de todos os tenants"""
        try:
            all_stats = {}
            
            if not DATA_DIR.exists():
                return {"tenants": {}, "total_tenants": 0}
            
            # Lista todos os diretórios de tenant
            for tenant_dir in DATA_DIR.iterdir():
                if tenant_dir.is_dir() and not tenant_dir.name.startswith('.'):
                    tenant_id = tenant_dir.name
                    all_stats[tenant_id] = self.get_tenant_stats(tenant_id)
            
            return {
                "tenants": all_stats,
                "total_tenants": len(all_stats)
            }
        
        except Exception as e:
            print(f"[ERROR] Erro ao obter estatísticas gerais: {e}")
            return {"error": str(e)}


# Instância global do gerenciador aprimorado
persistence_manager = EnhancedPersistenceManager()


# Funções de conveniência atualizadas
def save_user_info(user_info: UserInfo, tenant_id: str = "default") -> bool:
    """Função de conveniência para salvar usuário"""
    if not user_info.tenant_id:
        user_info.tenant_id = tenant_id
    return persistence_manager.save_user_info(user_info)


def save_session_info(session_info: SessionInfo) -> bool:
    """Função de conveniência para salvar sessão"""
    return persistence_manager.save_session_info(session_info)


def save_message(message: ConversationMessage, tenant_id: str = "default") -> bool:
    """Função de conveniência para salvar mensagem"""
    return persistence_manager.save_message(message, tenant_id)


def get_user_by_phone(phone: str, tenant_id: str = "default") -> Optional[UserInfo]:
    """Função de conveniência para buscar usuário por telefone"""
    return persistence_manager.get_user_by_phone(phone, tenant_id)


def get_or_create_user_by_phone(phone: str, name: str = None, tenant_id: str = "default") -> UserInfo:
    """Busca usuário por telefone ou cria novo se não existir"""
    user = persistence_manager.get_user_by_phone(phone, tenant_id)
    if not user:
        user = UserInfo(
            user_id=str(uuid.uuid4()),
            phone=phone,
            name=name,
            tenant_id=tenant_id
        )
        persistence_manager.save_user_info(user)
    return user