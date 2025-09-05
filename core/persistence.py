# -*- coding: utf-8 -*-
"""
Core Persistence - Sistema de persistência em CSV
Responsável por: salvar dados de sessão, informações do usuário, histórico
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
SESSIONS_DIR = DATA_DIR / "sessions"
USERS_DIR = DATA_DIR / "users"
CONVERSATIONS_DIR = DATA_DIR / "conversations"

# Cria diretórios se não existirem
for directory in [DATA_DIR, SESSIONS_DIR, USERS_DIR, CONVERSATIONS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


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


class PersistenceManager:
    """Gerenciador de persistência de dados"""
    
    def __init__(self):
        self.users_file = USERS_DIR / "users.csv"
        self.sessions_file = SESSIONS_DIR / "sessions.csv"
        self.conversations_file = CONVERSATIONS_DIR / "conversations.csv"
        
        # Inicializa arquivos CSV se não existirem
        self._init_csv_files()
    
    def _init_csv_files(self):
        """Inicializa arquivos CSV com headers"""
        
        # Users CSV
        if not self.users_file.exists():
            with open(self.users_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'user_id', 'name', 'email', 'phone', 'company', 'job_title',
                    'location', 'age', 'interests', 'preferences', 'notes',
                    'created_at', 'updated_at'
                ])
                writer.writeheader()
        
        # Sessions CSV
        if not self.sessions_file.exists():
            with open(self.sessions_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'session_id', 'user_id', 'tenant_id', 'channel', 'phone_number',
                    'start_time', 'end_time', 'message_count', 'status', 'intent',
                    'satisfaction', 'converted', 'metadata'
                ])
                writer.writeheader()
        
        # Conversations CSV
        if not self.conversations_file.exists():
            with open(self.conversations_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'message_id', 'session_id', 'user_id', 'timestamp', 'role',
                    'content', 'intent', 'sentiment', 'extracted_info', 'response_time_ms'
                ])
                writer.writeheader()
    
    def save_user_info(self, user_info: UserInfo) -> bool:
        """Salva informações do usuário"""
        try:
            # Verifica se usuário já existe
            existing_user = self.get_user_by_id(user_info.user_id)
            
            if existing_user:
                # Atualiza usuário existente
                self._update_user_in_csv(user_info)
            else:
                # Adiciona novo usuário
                self._append_user_to_csv(user_info)
            
            return True
        except Exception as e:
            print(f"[ERROR] Erro ao salvar usuário: {e}")
            return False
    
    def save_session_info(self, session_info: SessionInfo) -> bool:
        """Salva informações da sessão"""
        try:
            # Verifica se sessão já existe
            existing_session = self.get_session_by_id(session_info.session_id)
            
            if existing_session:
                # Atualiza sessão existente
                self._update_session_in_csv(session_info)
            else:
                # Adiciona nova sessão
                self._append_session_to_csv(session_info)
            
            return True
        except Exception as e:
            print(f"[ERROR] Erro ao salvar sessão: {e}")
            return False
    
    def save_message(self, message: ConversationMessage) -> bool:
        """Salva mensagem da conversa"""
        try:
            with open(self.conversations_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'message_id', 'session_id', 'user_id', 'timestamp', 'role',
                    'content', 'intent', 'sentiment', 'extracted_info', 'response_time_ms'
                ])
                writer.writerow(asdict(message))
            return True
        except Exception as e:
            print(f"[ERROR] Erro ao salvar mensagem: {e}")
            return False
    
    def get_user_by_id(self, user_id: str) -> Optional[UserInfo]:
        """Busca usuário por ID"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['user_id'] == user_id:
                        return UserInfo(**row)
        except Exception as e:
            print(f"[ERROR] Erro ao buscar usuário: {e}")
        return None
    
    def get_user_by_phone(self, phone: str) -> Optional[UserInfo]:
        """Busca usuário por telefone"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['phone'] == phone:
                        return UserInfo(**row)
        except Exception as e:
            print(f"[ERROR] Erro ao buscar usuário por telefone: {e}")
        return None
    
    def get_session_by_id(self, session_id: str) -> Optional[SessionInfo]:
        """Busca sessão por ID"""
        try:
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
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
    
    def get_user_sessions(self, user_id: str) -> List[SessionInfo]:
        """Busca todas as sessões de um usuário"""
        sessions = []
        try:
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['user_id'] == user_id:
                        row['message_count'] = int(row['message_count'] or 0)
                        row['converted'] = row['converted'].lower() == 'true'
                        sessions.append(SessionInfo(**row))
        except Exception as e:
            print(f"[ERROR] Erro ao buscar sessões do usuário: {e}")
        return sessions
    
    def get_session_messages(self, session_id: str) -> List[ConversationMessage]:
        """Busca todas as mensagens de uma sessão"""
        messages = []
        try:
            with open(self.conversations_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['session_id'] == session_id:
                        # Converte campos específicos
                        if row['response_time_ms']:
                            row['response_time_ms'] = int(row['response_time_ms'])
                        messages.append(ConversationMessage(**row))
        except Exception as e:
            print(f"[ERROR] Erro ao buscar mensagens da sessão: {e}")
        return messages
    
    def _append_user_to_csv(self, user_info: UserInfo):
        """Adiciona usuário ao CSV"""
        with open(self.users_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'user_id', 'name', 'email', 'phone', 'company', 'job_title',
                'location', 'age', 'interests', 'preferences', 'notes',
                'created_at', 'updated_at'
            ])
            writer.writerow(asdict(user_info))
    
    def _append_session_to_csv(self, session_info: SessionInfo):
        """Adiciona sessão ao CSV"""
        with open(self.sessions_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'session_id', 'user_id', 'tenant_id', 'channel', 'phone_number',
                'start_time', 'end_time', 'message_count', 'status', 'intent',
                'satisfaction', 'converted', 'metadata'
            ])
            writer.writerow(asdict(session_info))
    
    def _update_user_in_csv(self, user_info: UserInfo):
        """Atualiza usuário no CSV"""
        self._update_csv_record(self.users_file, 'user_id', user_info.user_id, asdict(user_info))
    
    def _update_session_in_csv(self, session_info: SessionInfo):
        """Atualiza sessão no CSV"""
        self._update_csv_record(self.sessions_file, 'session_id', session_info.session_id, asdict(session_info))
    
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
    
    def update_session_message_count(self, session_id: str):
        """Incrementa contador de mensagens da sessão"""
        session = self.get_session_by_id(session_id)
        if session:
            session.message_count += 1
            self.save_session_info(session)
    
    def close_session(self, session_id: str, status: str = "completed"):
        """Fecha uma sessão"""
        session = self.get_session_by_id(session_id)
        if session:
            session.end_time = datetime.now().isoformat()
            session.status = status
            self.save_session_info(session)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas gerais"""
        try:
            # Conta usuários
            user_count = 0
            with open(self.users_file, 'r', encoding='utf-8') as f:
                user_count = sum(1 for line in f) - 1  # -1 para header
            
            # Conta sessões
            session_count = 0
            active_sessions = 0
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    session_count += 1
                    if row['status'] == 'active':
                        active_sessions += 1
            
            # Conta mensagens
            message_count = 0
            with open(self.conversations_file, 'r', encoding='utf-8') as f:
                message_count = sum(1 for line in f) - 1  # -1 para header
            
            return {
                "total_users": user_count,
                "total_sessions": session_count,
                "active_sessions": active_sessions,
                "total_messages": message_count,
                "data_directory": str(DATA_DIR.absolute())
            }
        
        except Exception as e:
            print(f"[ERROR] Erro ao obter estatísticas: {e}")
            return {}


# Instância global do gerenciador
persistence_manager = PersistenceManager()


# Funções de conveniência
def save_user_info(user_info: UserInfo) -> bool:
    """Função de conveniência para salvar usuário"""
    return persistence_manager.save_user_info(user_info)


def save_session_info(session_info: SessionInfo) -> bool:
    """Função de conveniência para salvar sessão"""
    return persistence_manager.save_session_info(session_info)


def save_message(message: ConversationMessage) -> bool:
    """Função de conveniência para salvar mensagem"""
    return persistence_manager.save_message(message)


def get_user_by_phone(phone: str) -> Optional[UserInfo]:
    """Função de conveniência para buscar usuário por telefone"""
    return persistence_manager.get_user_by_phone(phone)


def get_or_create_user_by_phone(phone: str, name: str = None) -> UserInfo:
    """Busca usuário por telefone ou cria novo se não existir"""
    user = persistence_manager.get_user_by_phone(phone)
    if not user:
        user = UserInfo(
            user_id=str(uuid.uuid4()),
            phone=phone,
            name=name
        )
        persistence_manager.save_user_info(user)
    return user