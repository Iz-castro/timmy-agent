# -*- coding: utf-8 -*-
"""
Core Agent - Com sistema de releitura completa + sistema de target + estratégia consultiva
VERSÃO FINAL: Integração limpa e funcional
"""

import json
import uuid
import traceback
import re
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

# Imports da nova arquitetura
try:
    from core.processors.message import MessageProcessor, ProcessedMessage
    from core.processors.context import ContextProcessor, ContextAnalysis
    from core.processors.response import ResponseProcessor, ResponseConfig, ResponseContext
    from core.extensions.loader import extension_loader
    from core.interfaces.strategy import Message as IMessage, ConversationContext
    NEW_ARCHITECTURE_AVAILABLE = True
except ImportError as e:
    print(f"[INFO] Nova arquitetura não disponível, usando sistema legado: {e}")
    NEW_ARCHITECTURE_AVAILABLE = False

# Imports do sistema de target
try:
    from core.processors.target import (
        target_manager, SmartTargetProcessor, 
        get_target_config, TargetCapture
    )
    TARGET_SYSTEM_AVAILABLE = True
except ImportError:
    print(f"[INFO] Sistema de Target não disponível")
    TARGET_SYSTEM_AVAILABLE = False

# Imports do sistema atual (mantidos para compatibilidade)
from core.utils import (
    micro_responses, load_knowledge_data, get_state, set_state, 
    mark_once, chat_complete, extract_info_from_text, 
    format_structured_response
)

from core.persistence import (
    UserInfo, SessionInfo, ConversationMessage,
    persistence_manager, get_or_create_user_by_phone, save_message
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


class ConversationReviewer:
    """Sistema de releitura completa da conversa"""
    
    def __init__(self, session_key: str, tenant_id: str = "default"):
        self.session_key = session_key
        self.tenant_id = tenant_id
    
    def get_full_conversation_history(self) -> List[Dict[str, str]]:
        """Recupera todo o histórico da conversa da sessão atual"""
        print(f"[DEBUG] Buscando histórico completo para sessão: {self.session_key}")
        
        try:
            messages = persistence_manager.get_session_messages(self.session_key, self.tenant_id)
            
            conversation_history = []
            for msg in messages:
                conversation_history.append({
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp
                })
            
            print(f"[DEBUG] Recuperadas {len(conversation_history)} mensagens da sessão")
            return conversation_history
            
        except Exception as e:
            print(f"[ERROR DEBUG] Erro ao recuperar histórico: {e}")
            return []
    
    def format_conversation_for_review(self, history: List[Dict[str, str]]) -> str:
        """Formata conversa para análise pelo LLM"""
        if not history:
            return "Esta é a primeira mensagem da conversa."
        
        formatted_parts = []
        for msg in history:
            role = "USUÁRIO" if msg["role"] == "user" else "ASSISTENTE"
            formatted_parts.append(f"{role}: {msg['content']}")
        
        return "\n".join(formatted_parts)
    
    def generate_conversation_context(self) -> str:
        """Gera contexto da conversa para o LLM"""
        history = self.get_full_conversation_history()
        return self.format_conversation_for_review(history)


def handle_turn(message: Message) -> Dict[str, Any]:
    """
    Handle principal - Processa uma mensagem completa
    """
    start_time = time.time()
    session_key = message.session_key
    tenant_id = message.tenant_id
    user_message = message.text.strip()
    
    print(f"\n[AGENT] Processando mensagem para tenant: {tenant_id}")
    print(f"[AGENT] Sessão: {session_key}")
    print(f"[AGENT] Mensagem: {user_message[:100]}...")
    
    try:
        # 1. CAPTURA DE TARGET - Executa antes de tudo
        target_data = {}
        if TARGET_SYSTEM_AVAILABLE:
            target_data = process_target_capture(user_message, session_key, tenant_id)
            print(f"[TARGET] Dados capturados: {target_data}")
        
        # 2. CARREGAMENTO DE CONHECIMENTO
        agent_data = load_knowledge_data(tenant_id)
        if not agent_data:
            return {"response": "⚠️ Configuração do tenant não encontrada", "status": "error"}
        
        # 3. ANÁLISE DE CONTEXTO
        context_analysis = analyze_enhanced_context(user_message, session_key, tenant_id, target_data)
        
        # 4. PROCESSAMENTO DA MENSAGEM
        if NEW_ARCHITECTURE_AVAILABLE:
            response_result = process_with_new_architecture(
                user_message, session_key, tenant_id, agent_data, context_analysis
            )
        else:
            response_result = process_with_legacy_system(
                user_message, session_key, tenant_id, agent_data, context_analysis
            )
        
        # 5. PERSISTÊNCIA
        save_enhanced_interaction(user_message, response_result, session_key, tenant_id, target_data)
        
        # 6. RESPOSTA FINAL
        processing_time = time.time() - start_time
        response_result.update({
            "processing_time": round(processing_time, 3),
            "target_data": target_data,
            "target_completion": get_target_completion_status(session_key, tenant_id) if TARGET_SYSTEM_AVAILABLE else None
        })
        
        print(f"[AGENT] Resposta processada em {processing_time:.3f}s")
        return response_result
        
    except Exception as e:
        print(f"[ERROR] Erro no handle_turn: {e}")
        traceback.print_exc()
        return {
            "response": "❌ Desculpe, houve um erro interno. Tente novamente.",
            "status": "error",
            "error": str(e)
        }


def process_target_capture(user_message: str, session_key: str, tenant_id: str) -> Dict[str, Any]:
    """
    Processa captura de informações de target
    """
    if not TARGET_SYSTEM_AVAILABLE:
        return {}
    
    try:
        target_config = get_target_config(tenant_id)
        if not target_config:
            print(f"[TARGET] Nenhuma configuração encontrada para {tenant_id}")
            return {}
        
        processor = SmartTargetProcessor()
        extracted_data = processor.extract_from_message(user_message, target_config)
        
        if extracted_data:
            current_state = get_state(session_key) or {}
            target_session_data = current_state.get("target_data", {})
            
            target_session_data.update(extracted_data)
            current_state["target_data"] = target_session_data
            set_state(session_key, current_state)
            
            print(f"[TARGET] Dados extraídos e salvos: {extracted_data}")
            
            completion_status = target_config.is_complete(target_session_data)
            if completion_status:
                print(f"[TARGET] Target completo para {tenant_id}!")
                current_state["target_completed"] = True
                current_state["target_completed_at"] = datetime.now().isoformat()
                set_state(session_key, current_state)
            
            return {
                "extracted": extracted_data,
                "session_total": target_session_data,
                "is_complete": completion_status,
                "config": {
                    "target_name": target_config.target_name,
                    "total_fields": len(target_config.fields),
                    "required_fields": len(target_config.get_required_fields())
                }
            }
        
        return {}
        
    except Exception as e:
        print(f"[ERROR TARGET] Erro no processamento de target: {e}")
        return {"error": str(e)}


def analyze_enhanced_context(user_message: str, session_key: str, tenant_id: str, target_data: Dict) -> Dict[str, Any]:
    """
    Análise de contexto incluindo dados de target
    """
    conversation_reviewer = ConversationReviewer(session_key, tenant_id)
    conversation_history = conversation_reviewer.get_full_conversation_history()
    
    original_context = {
        "message_count": len(conversation_history),
        "is_first_message": len(conversation_history) == 0,
        "conversation_context": conversation_reviewer.generate_conversation_context(),
        "session_state": get_state(session_key) or {}
    }
    
    target_context = {}
    if TARGET_SYSTEM_AVAILABLE and target_data:
        target_config = get_target_config(tenant_id)
        if target_config:
            session_state = get_state(session_key) or {}
            session_target_data = session_state.get("target_data", {})
            
            target_context = {
                "has_target_data": bool(session_target_data),
                "target_completion": target_config.is_complete(session_target_data),
                "missing_required_fields": [
                    f.field_name for f in target_config.get_required_fields()
                    if f.field_name not in session_target_data
                ],
                "captured_fields": list(session_target_data.keys()),
                "next_suggested_capture": get_next_capture_suggestion(target_config, session_target_data)
            }
    
    enhanced_context = {
        **original_context,
        "target": target_context,
        "should_focus_on_capture": should_prioritize_capture(target_context, original_context)
    }
    
    return enhanced_context


def get_next_capture_suggestion(target_config: TargetCapture, current_data: Dict) -> Optional[str]:
    """Sugere próximo campo a ser capturado baseado na prioridade"""
    required_missing = [
        f for f in target_config.get_required_fields()
        if f.field_name not in current_data
    ]
    if required_missing:
        return required_missing[0].field_name
    
    optional_missing = [
        f for f in target_config.fields
        if f.field_name not in current_data and not f.required
    ]
    if optional_missing:
        return optional_missing[0].field_name
    
    return None


def should_prioritize_capture(target_context: Dict, conversation_context: Dict) -> bool:
    """Decide se deve priorizar captura de dados ou resposta normal"""
    if not target_context.get("has_target_data"):
        return True
    
    if target_context.get("missing_required_fields"):
        return True
    
    if conversation_context.get("message_count", 0) < 3:
        return True
    
    return False


def check_consultative_strategy(user_message: str, session_key: str, tenant_id: str, context_analysis: Dict) -> Optional[str]:
    """
    Verifica se deve ativar estratégia consultiva (apenas para timmy_vendas)
    """
    if tenant_id != "timmy_vendas":
        return None
    
    try:
        from core.conversation_strategy import process_consultative_turn
        
        text_lower = user_message.lower()
        business_indicators = [
            "negócio", "empresa", "clientes", "atendimento", "vendas",
            "automatizar", "whatsapp", "sistema", "ferramenta",
            "quanto custa", "preço", "valor", "planos", "loja", 
            "restaurante", "clínica", "consultório", "comércio"
        ]
        
        has_business_context = any(indicator in text_lower for indicator in business_indicators)
        
        session_state = get_state(session_key) or {}
        in_consultive_flow = session_state.get("consultive_active", False)
        
        if has_business_context or in_consultive_flow:
            print(f"[CONSULTIVE] Ativando estratégia consultiva para: {user_message[:50]}...")
            
            response = process_consultative_turn(tenant_id, user_message, session_key)
            
            if response:
                set_state(session_key, consultive_active=True)
                print(f"[CONSULTIVE] Resposta gerada: {response[:100]}...")
                return response
            else:
                set_state(session_key, consultive_active=False)
                
        return None
    
    except ImportError:
        print(f"[INFO] Estratégia consultiva não disponível para {tenant_id}")
        return None
    except Exception as e:
        print(f"[ERROR] Erro na estratégia consultiva: {e}")
        return None


def process_with_legacy_system(user_message: str, session_key: str, tenant_id: str, agent_data: Dict, context_analysis: Dict) -> Dict[str, Any]:
    """
    Processamento usando sistema legado com estratégia consultiva integrada
    """
    try:
        # 1. PRIMEIRO: Verifica estratégia consultiva (apenas timmy_vendas)
        consultive_response = check_consultative_strategy(user_message, session_key, tenant_id, context_analysis)
        
        if consultive_response:
            print(f"[AGENT] Usando estratégia consultiva")
            formatted_responses = micro_responses(consultive_response, session_key=session_key)
            final_response = " ".join(formatted_responses) if isinstance(formatted_responses, list) else formatted_responses
            
            return {
                "response": final_response,
                "status": "success",
                "method": "consultive"
            }
        
        # 2. FALLBACK: Processamento normal com target
        print(f"[AGENT] Usando processamento padrão com target")
        
        system_prompt = build_enhanced_prompt(user_message, agent_data, context_analysis, session_key, tenant_id)
        messages = [{"role": "user", "content": user_message}]
        
        response = chat_complete(
            system_prompt=system_prompt,
            messages=messages,
            model=None,
            temperature=0.7,
            max_tokens=400
        )
        
        if isinstance(response, list):
            response = " ".join(str(r) for r in response)
            
        formatted_responses = micro_responses(response, session_key=session_key)
        final_response = " ".join(formatted_responses) if isinstance(formatted_responses, list) else formatted_responses
        
        return {
            "response": final_response,
            "status": "success",
            "method": "legacy"
        }
    
    except Exception as e:
        print(f"[ERROR] Erro no processamento legado: {e}")
        traceback.print_exc()
        return {
            "response": "❌ Erro no processamento da mensagem.",
            "status": "error",
            "error": str(e)
        }


def process_with_new_architecture(user_message: str, session_key: str, tenant_id: str, agent_data: Dict, context_analysis: Dict) -> Dict[str, Any]:
    """
    Processamento usando nova arquitetura (fallback para legado por enquanto)
    """
    try:
        return process_with_legacy_system(user_message, session_key, tenant_id, agent_data, context_analysis)
    except Exception as e:
        print(f"[ERROR] Erro na nova arquitetura: {e}")
        return process_with_legacy_system(user_message, session_key, tenant_id, agent_data, context_analysis)


def build_enhanced_prompt(user_message: str, agent_data: Dict, context_analysis: Dict, session_key: str, tenant_id: str) -> str:
    """
    Constrói prompt genérico baseado APENAS nos dados do tenant
    """
    agent_name = agent_data.get("agent_name", "Assistente")
    business_name = agent_data.get("business_name", "Nossa Empresa")
    personality = agent_data.get("personality", {})
    knowledge = agent_data.get("knowledge_base", {})  # CORRIGIDO: chave certa
    
    conversation_context = context_analysis.get("conversation_context", "")
    target_summary = get_target_summary_for_prompt(session_key, tenant_id)
    
    # CONFIGURAÇÃO DE RESPOSTA VEM DO TENANT
    response_settings = agent_data.get("response_settings", {})
    min_chars = response_settings.get("min_chars", 120)  # CORRIGIDO: seus valores
    max_chars = response_settings.get("max_chars", 200)  # CORRIGIDO: seus valores
    
    prompt = f"""Você é {agent_name}, assistente de {business_name}.

PERSONALIDADE:
- Seja natural, cordial e consistente
- NUNCA se reapresente se já fez isso antes na conversa
- Use informações já compartilhadas pelo usuário
- Demonstre que acompanha o fluxo da conversa

CONTEXTO COMPLETO DA CONVERSA:
{conversation_context}

CONHECIMENTO DISPONÍVEL:
{json.dumps(knowledge, indent=2, ensure_ascii=False)}

{target_summary}

INSTRUÇÕES DE RESPOSTA:
- Respostas entre {min_chars}-{max_chars} caracteres quando possível
- Seja conversacional e natural
- Mantenha consistência com mensagens anteriores
- JAMAIS ignore o contexto da conversa
- Use EXATAMENTE as informações do conhecimento fornecido

MENSAGEM ATUAL DO USUÁRIO: {user_message}

Responda de forma natural e útil."""
    
    return prompt

def get_target_summary_for_prompt(session_key: str, tenant_id: str) -> str:
    """
    Gera resumo de target para incluir no prompt do LLM
    """
    if not TARGET_SYSTEM_AVAILABLE:
        return ""
    
    try:
        target_config = get_target_config(tenant_id)
        if not target_config:
            return ""
        
        session_state = get_state(session_key) or {}
        target_data = session_state.get("target_data", {})
        
        if not target_data:
            return f"""
## 🎯 CONFIGURAÇÃO DE CAPTURA ({target_config.target_name})
- Você deve capturar informações específicas durante a conversa
- Campos obrigatórios: {[f.display_name for f in target_config.get_required_fields()]}
- Campos opcionais: {[f.display_name for f in target_config.fields if not f.required]}
- Seja natural na captura, não faça interrogatório
"""
        
        captured_summary = []
        missing_required = []
        
        for field in target_config.fields:
            if field.field_name in target_data:
                captured_summary.append(f"✅ {field.display_name}: {target_data[field.field_name]}")
            elif field.required:
                missing_required.append(field.display_name)
        
        summary = f"""
## 🎯 DADOS DO {target_config.target_name.upper()} CAPTURADOS:
{chr(10).join(captured_summary)}

"""
        
        if missing_required:
            summary += f"""
⚠️ **CAMPOS OBRIGATÓRIOS FALTANDO**: {', '.join(missing_required)}
- Tente capturar naturalmente durante a conversa
"""
        else:
            summary += "✅ **Todos os campos obrigatórios capturados!**"
        
        return summary
        
    except Exception as e:
        print(f"[ERROR] Erro ao gerar resumo de target: {e}")
        return ""


def save_enhanced_interaction(user_message: str, response_result: Dict, session_key: str, tenant_id: str, target_data: Dict):
    """
    Salva interação incluindo dados de target
    """
    try:
        user_msg = ConversationMessage(
            message_id=str(uuid.uuid4()),
            session_id=session_key,
            user_id=None,
            timestamp=datetime.now().isoformat(),
            role="user",
            content=user_message,
            intent="general",
            extracted_info=json.dumps(target_data.get("extracted", {}))
        )
        persistence_manager.save_message(user_msg, tenant_id)
        
        agent_msg = ConversationMessage(
            message_id=str(uuid.uuid4()),
            session_id=session_key,
            user_id=None,
            timestamp=datetime.now().isoformat(),
            role="assistant", 
            content=response_result.get("response", ""),
            intent="response",
            extracted_info=json.dumps({
                "processing_time": response_result.get("processing_time"),
                "target_completion": response_result.get("target_completion"),
                "total_target_data": target_data.get("session_total", {})
            })
        )
        persistence_manager.save_message(agent_msg, tenant_id)
        
        if target_data.get("is_complete"):
            update_user_with_target_data(session_key, tenant_id, target_data.get("session_total", {}))
            
    except Exception as e:
        print(f"[ERROR] Erro ao salvar interação: {e}")


def update_user_with_target_data(session_key: str, tenant_id: str, target_data: Dict):
    """
    Atualiza dados do usuário com informações de target capturadas
    """
    try:
        session_state = get_state(session_key)
        if not session_state:
            return
        
        user_info = session_state.get("user_info")
        if not user_info:
            return
        
        target_config = get_target_config(tenant_id)
        if not target_config:
            return
        
        user_updates = {}
        
        field_mapping = {
            "tipo_negocio": "company",
            "dor_principal": "notes",
            "especialidade_interesse": "interests",
            "sintomas_principais": "notes"
        }
        
        for target_field, user_field in field_mapping.items():
            if target_field in target_data:
                user_updates[user_field] = target_data[target_field]
        
        if target_data:
            current_preferences = user_info.get("preferences", "")
            target_summary = f"Target {target_config.target_name}: {json.dumps(target_data, ensure_ascii=False)}"
            
            if current_preferences:
                user_updates["preferences"] = f"{current_preferences} | {target_summary}"
            else:
                user_updates["preferences"] = target_summary
        
        if user_updates:
            for field, value in user_updates.items():
                setattr(user_info, field, value)
            
            persistence_manager.save_user_info(user_info)
            print(f"[TARGET] Usuário atualizado com dados de target: {list(user_updates.keys())}")
        
    except Exception as e:
        print(f"[ERROR] Erro ao atualizar usuário com target: {e}")


def get_target_completion_status(session_key: str, tenant_id: str) -> Optional[Dict]:
    """
    Retorna status de completude do target
    """
    if not TARGET_SYSTEM_AVAILABLE:
        return None
    
    try:
        target_config = get_target_config(tenant_id)
        if not target_config:
            return None
        
        session_state = get_state(session_key) or {}
        target_data = session_state.get("target_data", {})
        
        required_fields = target_config.get_required_fields()
        optional_fields = [f for f in target_config.fields if not f.required]
        
        required_complete = all(f.field_name in target_data for f in required_fields)
        optional_complete = sum(1 for f in optional_fields if f.field_name in target_data)
        
        return {
            "target_name": target_config.target_name,
            "is_complete": target_config.is_complete(target_data),
            "required_complete": required_complete,
            "required_total": len(required_fields),
            "optional_complete": optional_complete,
            "optional_total": len(optional_fields),
            "completion_percentage": round(
                (len(target_data) / len(target_config.fields)) * 100, 1
            ) if target_config.fields else 0,
            "captured_fields": list(target_data.keys()),
            "missing_required": [
                f.field_name for f in required_fields 
                if f.field_name not in target_data
            ]
        }
        
    except Exception as e:
        print(f"[ERROR] Erro ao obter status de target: {e}")
        return {"error": str(e)}


# FUNÇÕES MANTIDAS PARA COMPATIBILIDADE
def get_user_history(phone: str, tenant_id: str = "default") -> Dict[str, Any]:
    """Retorna histórico do usuário (MANTIDA)"""
    try:
        user = persistence_manager.get_user_by_phone(phone, tenant_id)
        if not user:
            return {"error": "Usuário não encontrado"}
        
        sessions = persistence_manager.get_user_sessions(user.user_id, tenant_id)
        sessions_with_messages = []
        
        for session in sessions:
            messages = persistence_manager.get_session_messages(session.session_id, tenant_id)
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


def get_data_stats(tenant_id: str = "default") -> Dict[str, Any]:
    """Retorna estatísticas dos dados do tenant específico (MANTIDA)"""
    return persistence_manager.get_tenant_stats(tenant_id)


def get_all_tenants_stats() -> Dict[str, Any]:
    """Retorna estatísticas de todos os tenants (MANTIDA)"""
    return persistence_manager.get_all_tenants_stats()


def get_extension_info(tenant_id: str = "default") -> Dict[str, Any]:
    """Retorna informações sobre extensões carregadas"""
    if NEW_ARCHITECTURE_AVAILABLE:
        try:
            return extension_loader.get_loaded_extensions_info(tenant_id)
        except Exception as e:
            return {"error": f"Erro ao carregar informações de extensões: {e}"}
    else:
        return {"message": "Nova arquitetura não disponível"}


def reload_tenant_extensions(tenant_id: str = "default") -> Dict[str, Any]:
    """Recarrega extensões de um tenant específico"""
    if NEW_ARCHITECTURE_AVAILABLE:
        try:
            extensions = extension_loader.reload_tenant_extensions(tenant_id)
            return {
                "status": "success",
                "tenant_id": tenant_id,
                "extensions_loaded": {
                    "strategies": len(extensions.get("strategies", [])),
                    "workflows": len(extensions.get("workflows", [])),
                    "formatters": len(extensions.get("formatters", [])),
                    "database": "loaded" if extensions.get("database") else "none"
                }
            }
        except Exception as e:
            return {"error": f"Erro ao recarregar extensões: {e}"}
    else:
        return {"message": "Nova arquitetura não disponível"}


def setup_target_system_for_tenant(tenant_id: str, target_type: str = "generic"):
    """Configura sistema de target para um tenant"""
    if not TARGET_SYSTEM_AVAILABLE:
        print(f"[ERROR] Sistema de target não disponível")
        return False


def process_message(text: str, tenant_id: str = "default", phone_number: str = None, session_key: str = None) -> List[str]:
    """Função de conveniência para processar mensagem (MANTIDA)"""
    
    try:
        if not session_key:
            session_key = f"session_{uuid.uuid4().hex[:8]}"
        
        if phone_number:
            session_key = f"phone_{phone_number.replace('+', '').replace(' ', '')}"
            user = get_or_create_user_by_phone(phone_number, tenant_id=tenant_id)
            set_state(session_key, user_id=user.user_id, phone=phone_number)
        
        message = Message(text=text, session_key=session_key, tenant_id=tenant_id)
        result = handle_turn(message)
        
        response = result.get("response", "Erro no processamento")
        return [response] if isinstance(response, str) else response
        
    except Exception as e:
        print(f"[ERROR] Erro no process_message: {e}")
        return [f"Erro interno: {str(e)}"]
    
    try:
        from core.processors.target import create_target_config
        
        config = create_target_config(tenant_id, target_type)
        
        print(f"[SUCCESS] Sistema de target configurado para {tenant_id}")
        print(f"[INFO] Tipo: {target_type}")
        print(f"[INFO] Campos configurados: {len(config.fields)}")
        print(f"[INFO] Campos obrigatórios: {len(config.get_required_fields())}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Erro ao configurar sistema de target: {e}")
        return