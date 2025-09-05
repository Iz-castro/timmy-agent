# -*- coding: utf-8 -*-
"""
Core Agent - Cérebro principal do Timmy-IA
Responsável por: conversação, coleta de dados, resposta contextual
"""

import json
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

from core.utils import (
    micro_responses, load_knowledge_data, get_state, set_state, 
    mark_once, chat_complete, extract_info_from_text
)

# Importa sistema de persistência
from core.persistence import (
    UserInfo, SessionInfo, ConversationMessage,
    persistence_manager, get_or_create_user_by_phone
)


@dataclass
class Message:
    """Estrutura de mensagem padronizada"""
    text: str
    session_key: str
    tenant_id: str = "default"
    meta: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.meta is None:
            self.meta = {}


class TimmyAgent:
    """
    Agente conversacional principal
    
    Funcionalidades:
    - Conversa natural
    - Coleta passiva de informações (nome, email, telefone, etc.)
    - Responde com base no conhecimento carregado
    - Mantém contexto por sessão
    - Persiste dados em CSV
    """
    
    def __init__(self, tenant_id: str = "default"):
        self.tenant_id = tenant_id
        self.knowledge = load_knowledge_data(tenant_id)
        
    def _greeting_line(self) -> str:
        """Gera saudação contextual baseada no horário"""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            greeting = "Bom dia"
        elif hour < 18:
            greeting = "Boa tarde"
        else:
            greeting = "Boa noite"
        
        agent_name = self.knowledge.get("agent_name", "Timmy")
        business_name = self.knowledge.get("business_name", "nossa empresa")
        
        return f"{greeting}! Eu sou {agent_name}, assistente de {business_name}."
    
    def _build_system_prompt(self) -> str:
        """Constrói prompt do sistema com conhecimento disponível"""
        
        # Prompt base
        base_prompt = """Você é um assistente virtual inteligente e prestativo.

INSTRUÇÕES BÁSICAS:
- Seja cordial, profissional e empático
- Responda de forma clara e objetiva  
- Ajude o usuário com suas dúvidas
- Colete informações quando necessário (nome, contato, etc.)
- Use apenas informações do conhecimento fornecido
- Não invente dados que não estão disponíveis

CONHECIMENTO DISPONÍVEL:
{knowledge}

REGRAS:
- Respostas entre 80-120 caracteres quando possível
- Se não souber algo, seja honesto
- Mantenha o contexto da conversa
- Pergunte quando precisar de esclarecimentos
"""
        
        # Adiciona conhecimento estruturado
        knowledge_text = ""
        if self.knowledge:
            knowledge_text = json.dumps(self.knowledge, indent=2, ensure_ascii=False)
        
        return base_prompt.format(knowledge=knowledge_text)
    
    def _analyze_intent(self, text: str, session_state: Dict) -> str:
        """Analisa intenção básica da mensagem"""
        text_lower = text.lower()
        
        # Intents básicos
        if any(word in text_lower for word in ["olá", "oi", "bom dia", "boa tarde", "boa noite"]):
            return "greeting"
        
        if any(word in text_lower for word in ["obrigado", "obrigada", "valeu", "tchau", "até logo"]):
            return "farewell"
        
        if any(word in text_lower for word in ["ajuda", "help", "como", "o que", "quem"]):
            return "help_request"
        
        if any(word in text_lower for word in ["preço", "valor", "quanto custa", "investimento"]):
            return "pricing"
        
        if any(word in text_lower for word in ["contato", "telefone", "email", "endereço"]):
            return "contact_info"
        
        return "general"
    
    def _handle_first_interaction(self, message: Message, session_state: Dict) -> List[str]:
        """Lida com primeira interação da sessão"""
        if not mark_once(message.session_key, "greeting_sent"):
            return []
        
        greeting = self._greeting_line()
        intent = self._analyze_intent(message.text, session_state)
        
        if intent == "greeting":
            response = f"{greeting} Como posso ajudar você hoje?"
        elif intent == "help_request":
            response = f"{greeting} Claro! Estou aqui para te ajudar. O que você gostaria de saber?"
        else:
            response = f"{greeting} Vi que você quer saber sobre algo específico. Vou te ajudar!"
        
        return micro_responses(response, session_key=message.session_key)
    
    def _collect_user_info(self, text: str, session_key: str) -> Dict[str, str]:
        """Coleta passivamente informações do usuário e persiste"""
        extracted = extract_info_from_text(text)
        collected = {}
        
        current_state = get_state(session_key)
        
        # Atualiza apenas se não existir
        for key, value in extracted.items():
            if value and not current_state.get(key):
                collected[key] = value
                set_state(session_key, **{key: value})
        
        # Se coletou informações significativas, persiste no CSV
        if collected:
            self._persist_user_data(session_key, current_state, collected)
        
        return collected
    
    def _persist_user_data(self, session_key: str, current_state: Dict, new_info: Dict):
        """Persiste dados do usuário no sistema CSV"""
        try:
            # Coleta todos os dados conhecidos sobre o usuário
            all_user_data = {**current_state, **new_info}
            
            # Busca ou cria usuário
            user_id = all_user_data.get("user_id")
            if not user_id:
                # Se tem telefone, tenta buscar usuário existente
                phone = all_user_data.get("phone")
                if phone:
                    existing_user = persistence_manager.get_user_by_phone(phone)
                    if existing_user:
                        user_id = existing_user.user_id
                        # Atualiza session state com user_id
                        set_state(session_key, user_id=user_id)
                    else:
                        # Cria novo usuário
                        user_id = str(uuid.uuid4())
                        set_state(session_key, user_id=user_id)
                else:
                    # Cria novo usuário sem telefone
                    user_id = str(uuid.uuid4())
                    set_state(session_key, user_id=user_id)
            
            # Cria/atualiza objeto UserInfo
            user_info = UserInfo(
                user_id=user_id,
                name=all_user_data.get("name"),
                email=all_user_data.get("email"),
                phone=all_user_data.get("phone"),
                company=all_user_data.get("company"),
                job_title=all_user_data.get("job_title"),
                location=all_user_data.get("location"),
                age=all_user_data.get("age"),
                interests=all_user_data.get("interests"),
                preferences=all_user_data.get("preferences"),
                notes=all_user_data.get("notes")
            )
            
            # Salva usuário
            persistence_manager.save_user_info(user_info)
            
            # Atualiza/cria sessão
            session_info = persistence_manager.get_session_by_id(session_key)
            if not session_info:
                session_info = SessionInfo(
                    session_id=session_key,
                    user_id=user_id,
                    tenant_id=self.tenant_id,
                    channel="streamlit"  # Padrão, pode ser alterado
                )
                if all_user_data.get("phone"):
                    session_info.phone_number = all_user_data["phone"]
            else:
                # Atualiza informações da sessão
                session_info.user_id = user_id
                if all_user_data.get("phone"):
                    session_info.phone_number = all_user_data["phone"]
            
            persistence_manager.save_session_info(session_info)
            
            print(f"[INFO] Dados persistidos - Usuário: {user_id}, Sessão: {session_key}")
            
        except Exception as e:
            print(f"[ERROR] Erro ao persistir dados do usuário: {e}")
    
    def _save_message(self, session_key: str, role: str, content: str, intent: str = None):
        """Salva mensagem no histórico CSV"""
        try:
            # Obtém user_id do estado da sessão
            current_state = get_state(session_key)
            user_id = current_state.get("user_id")
            
            # Cria objeto de mensagem
            message = ConversationMessage(
                message_id=str(uuid.uuid4()),
                session_id=session_key,
                user_id=user_id,
                timestamp=datetime.now().isoformat(),
                role=role,
                content=content,
                intent=intent
            )
            
            # Salva mensagem
            persistence_manager.save_message(message)
            
            # Atualiza contador de mensagens da sessão
            persistence_manager.update_session_message_count(session_key)
            
        except Exception as e:
            print(f"[ERROR] Erro ao salvar mensagem: {e}")
    
    def _generate_contextual_response(self, message: Message, session_state: Dict) -> str:
        """Gera resposta usando LLM com contexto"""
        
        # Prepara contexto da sessão
        context_info = []
        if session_state.get("name"):
            context_info.append(f"Nome do usuário: {session_state['name']}")
        if session_state.get("email"):
            context_info.append(f"Email: {session_state['email']}")
        if session_state.get("phone"):
            context_info.append(f"Telefone: {session_state['phone']}")
        if session_state.get("company"):
            context_info.append(f"Empresa: {session_state['company']}")
        if session_state.get("job_title"):
            context_info.append(f"Cargo: {session_state['job_title']}")
        if session_state.get("location"):
            context_info.append(f"Localização: {session_state['location']}")
        if session_state.get("interests"):
            context_info.append(f"Interesses: {session_state['interests']}")
        
        context_text = "\n".join(context_info) if context_info else "Primeira interação com o usuário."
        
        # Verifica se usuário já tem histórico (busca por telefone)
        user_history = ""
        if session_state.get("phone"):
            try:
                history = get_user_history(session_state["phone"])
                if "user_info" in history and history["total_sessions"] > 1:
                    user_history = f"\n\nEste usuário já conversou conosco {history['total_sessions']} vezes antes."
            except:
                pass
        
        # Mensagem para o LLM
        user_prompt = f"""CONTEXTO DA SESSÃO:
{context_text}{user_history}

MENSAGEM DO USUÁRIO:
{message.text}

Responda de forma útil, contextual e personalizada."""
        
        # Gera resposta
        system_prompt = self._build_system_prompt()
        response = chat_complete(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            max_tokens=200,
            temperature=0.7
        )
        
        return response.strip()


def handle_turn(tenant_id: str, message: Message) -> List[str]:
    """
    Função principal para processar um turno de conversa
    
    Args:
        tenant_id: ID do tenant/cliente
        message: Mensagem recebida
        
    Returns:
        Lista de respostas (micro-respostas)
    """
    
    # Inicializa agente
    agent = TimmyAgent(tenant_id)
    
    # Estado da sessão
    session_state = get_state(message.session_key)
    
    # 🔴 NOVO: Salva mensagem do usuário
    intent = agent._analyze_intent(message.text, session_state)
    agent._save_message(message.session_key, "user", message.text, intent)
    
    # 1. Primeira interação (saudação)
    first_interaction = agent._handle_first_interaction(message, session_state)
    if first_interaction:
        # Salva respostas da saudação
        for response in first_interaction:
            agent._save_message(message.session_key, "assistant", response, "greeting")
        return first_interaction
    
    # 2. Coleta passiva de informações
    collected_info = agent._collect_user_info(message.text, message.session_key)
    
    # 3. Log de informações coletadas (opcional)
    if collected_info:
        print(f"[INFO] Coletado da sessão {message.session_key}: {collected_info}")
    
    # 4. Gera resposta contextual
    response_text = agent._generate_contextual_response(message, session_state)
    
    # 5. Quebra em micro-respostas
    responses = micro_responses(response_text, session_key=message.session_key)
    
    # 🔴 NOVO: Salva respostas do assistente
    for response in responses:
        agent._save_message(message.session_key, "assistant", response, intent)
    
    return responses


# Função de conveniência para uso direto
def process_message(text: str, session_key: str = None, tenant_id: str = "default", phone_number: str = None) -> List[str]:
    """
    Função simplificada para processar uma mensagem
    
    Args:
        text: Texto da mensagem
        session_key: Chave da sessão (gerada automaticamente se não fornecida)
        tenant_id: ID do tenant
        phone_number: Telefone do usuário (para webhook WhatsApp)
        
    Returns:
        Lista de respostas
    """
    if not session_key:
        session_key = f"session_{uuid.uuid4().hex[:8]}"
    
    # 🔴 NOVO: Se tem telefone, usa ele como session_key e busca/cria usuário
    if phone_number:
        # Usa telefone como base para session_key
        session_key = f"phone_{phone_number.replace('+', '').replace(' ', '')}"
        
        # Busca ou cria usuário por telefone
        user = get_or_create_user_by_phone(phone_number)
        
        # Atualiza estado da sessão com dados do usuário
        set_state(session_key, user_id=user.user_id, phone=phone_number)
        
        # Atualiza/cria sessão com canal WhatsApp
        session_info = persistence_manager.get_session_by_id(session_key)
        if not session_info:
            session_info = SessionInfo(
                session_id=session_key,
                user_id=user.user_id,
                tenant_id=tenant_id,
                channel="whatsapp",
                phone_number=phone_number
            )
            persistence_manager.save_session_info(session_info)
    
    message = Message(
        text=text,
        session_key=session_key,
        tenant_id=tenant_id
    )
    
    return handle_turn(tenant_id, message)


def get_user_history(phone_number: str) -> Dict[str, Any]:
    """
    Busca histórico completo de um usuário pelo telefone
    
    Args:
        phone_number: Número de telefone
        
    Returns:
        Dicionário com dados do usuário e histórico
    """
    try:
        # Busca usuário
        user = persistence_manager.get_user_by_phone(phone_number)
        if not user:
            return {"error": "Usuário não encontrado"}
        
        # Busca sessões do usuário
        sessions = persistence_manager.get_user_sessions(user.user_id)
        
        # Busca mensagens de cada sessão
        sessions_with_messages = []
        for session in sessions:
            messages = persistence_manager.get_session_messages(session.session_id)
            sessions_with_messages.append({
                "session_info": session,
                "messages": messages
            })
        
        return {
            "user_info": user,
            "total_sessions": len(sessions),
            "sessions": sessions_with_messages
        }
        
    except Exception as e:
        return {"error": f"Erro ao buscar histórico: {e}"}


def get_data_stats() -> Dict[str, Any]:
    """Retorna estatísticas dos dados persistidos"""
    return persistence_manager.get_stats()