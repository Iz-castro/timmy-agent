# -*- coding: utf-8 -*-
"""
Core Agent - Com sistema de releitura completa da conversa + formatação estruturada automática
"""

import json
import uuid
import traceback
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

from core.utils import (
    micro_responses, load_knowledge_data, get_state, set_state, 
    mark_once, chat_complete, extract_info_from_text, 
    format_structured_response, load_tenant_workflow
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
            # Busca todas as mensagens da sessão no tenant específico
            messages = persistence_manager.get_session_messages(self.session_key, self.tenant_id)
            
            conversation_history = []
            for msg in messages:
                conversation_history.append({
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp
                })
            
            print(f"[DEBUG] Recuperadas {len(conversation_history)} mensagens da sessão")
            
            # Debug: mostra últimas 3 mensagens
            if conversation_history:
                print(f"[DEBUG] Últimas mensagens:")
                for i, msg in enumerate(conversation_history[-3:], 1):
                    print(f"[DEBUG]   {i}. {msg['role']}: {msg['content'][:50]}...")
            
            return conversation_history
            
        except Exception as e:
            print(f"[ERROR DEBUG] Erro ao recuperar histórico: {e}")
            print(f"[ERROR DEBUG] Traceback: {traceback.format_exc()}")
            return []
    
    def format_conversation_for_review(self, history: List[Dict[str, str]]) -> str:
        """Formata conversa para análise pelo LLM"""
        if not history:
            return "Esta é a primeira mensagem da conversa."
        
        formatted_lines = ["HISTÓRICO COMPLETO DA CONVERSA:"]
        
        for i, msg in enumerate(history, 1):
            role_display = "Usuário" if msg["role"] == "user" else "Assistente"
            formatted_lines.append(f"{i}. {role_display}: {msg['content']}")
        
        return "\n".join(formatted_lines)
    
    def generate_conversation_context(self) -> str:
        """Gera contexto rico baseado na conversa completa"""
        print(f"[DEBUG] Gerando contexto da conversa...")
        
        history = self.get_full_conversation_history()
        
        if not history:
            print(f"[DEBUG] Nenhum histórico encontrado - primeira mensagem")
            return ""
        
        # Formata para análise
        formatted_conversation = self.format_conversation_for_review(history)
        
        user_name = self._extract_user_name_from_history(history)
        shared_info = self._extract_shared_info_from_history(history)
        already_introduced = self._check_if_already_introduced(history)
        
        print(f"[DEBUG] Nome extraído: {user_name}")
        print(f"[DEBUG] Já se apresentou: {already_introduced}")
        print(f"[DEBUG] Info compartilhada: {shared_info}")
        
        # Adiciona análise contextual
        context_analysis = f"""
{formatted_conversation}

ANÁLISE PARA PRÓXIMA RESPOSTA:
- Total de mensagens na conversa: {len(history)}
- Primeira interação: {"Sim" if len(history) <= 2 else "Não"}
- Já me apresentei: {"Sim" if already_introduced else "Não"}
- Nome do usuário conhecido: {user_name}
- Informações já compartilhadas: {shared_info}
"""
        
        print(f"[DEBUG] Contexto gerado com {len(context_analysis)} caracteres")
        return context_analysis
    
    def _extract_user_name_from_history(self, history: List[Dict[str, str]]) -> str:
        """Extrai nome do usuário do histórico"""
        for msg in history:
            if msg["role"] == "user":
                content = msg["content"].lower()
                # Padrões para identificar nome
                patterns = ["me chamo", "meu nome é", "sou o", "sou a", "eu sou"]
                for pattern in patterns:
                    if pattern in content:
                        # Extração simples do nome
                        match = re.search(f"{pattern}\\s+([A-Za-zÀ-ÿ]+)", content, re.IGNORECASE)
                        if match:
                            return match.group(1)
        return "não informado"
    
    def _extract_shared_info_from_history(self, history: List[Dict[str, str]]) -> str:
        """Extrai informações já compartilhadas"""
        shared_info = []
        
        for msg in history:
            if msg["role"] == "user":
                content = msg["content"].lower()
                
                # Profissão/trabalho
                if any(word in content for word in ["trabalho", "sou", "desenvolvo", "programo", "faço"]):
                    shared_info.append("Profissão/atividade mencionada")
                
                # Projetos
                if any(word in content for word in ["projeto", "criando", "construindo", "desenvolvendo"]):
                    shared_info.append("Projeto atual mencionado")
                
                # Interesses
                if any(word in content for word in ["gosto", "interesse", "especialista"]):
                    shared_info.append("Interesses mencionados")
        
        return ", ".join(shared_info) if shared_info else "Nenhuma informação específica"
    
    def _check_if_already_introduced(self, history: List[Dict[str, str]]) -> bool:
        """Verifica se já se apresentou analisando mensagens do assistente"""
        for msg in history:
            if msg["role"] == "assistant":
                content = msg["content"].lower()
                if any(phrase in content for phrase in ["sou", "eu sou", "assistente"]):
                    return True
        return False


class TimmyAgent:
    """Agente conversacional com releitura completa"""
    
    def __init__(self, tenant_id: str = "default"):
        self.tenant_id = tenant_id
        self.knowledge = load_knowledge_data(tenant_id)
    
    def _detect_and_format_structured_content(self, response_text: str, session_key: str) -> List[str]:
        """
        Detecta se a resposta contém conteúdo estruturado e aplica formatação adequada
        """
        print(f"[DEBUG] Analisando resposta para formatação estruturada...")
        
        # Padrões que indicam conteúdo estruturado
        structured_patterns = [
            r'\d+\.\s*\*\*.*?\*\*:',  # "1. **Título**:"
            r'\d+\.\s*[A-Z][^:]*:',   # "1. Título:"
            r'\*\*[^*]+\*\*:',        # "**Título**:"
            r'(?:\d+\.\s*){2,}',      # Múltiplos itens numerados
        ]
        
        # Verifica se contém padrões estruturados
        has_structured_content = any(
            re.search(pattern, response_text, re.MULTILINE | re.IGNORECASE) 
            for pattern in structured_patterns
        )
        
        if not has_structured_content:
            print(f"[DEBUG] Conteúdo não estruturado - usando micro_responses")
            return micro_responses(response_text, session_key=session_key)
        
        print(f"[DEBUG] Conteúdo estruturado detectado - aplicando format_structured_response")
        
        # Extrai introdução, itens e fechamento
        lines = response_text.strip().split('\n')
        intro_lines = []
        items = []
        outro_lines = []
        current_section = "intro"
        current_item = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detecta início de item numerado ou com título
            item_match = re.match(r'^(\d+)\.\s*\*\*([^*]+)\*\*:\s*(.*)', line)
            simple_item_match = re.match(r'^(\d+)\.\s*([^:]+):\s*(.*)', line)
            title_match = re.match(r'^\*\*([^*]+)\*\*:\s*(.*)', line)
            
            if item_match:
                # Salva item anterior se existir
                if current_item:
                    items.append(current_item)
                
                current_section = "items"
                current_item = {
                    "number": item_match.group(1),
                    "title": item_match.group(2).strip(),
                    "details": item_match.group(3).strip()
                }
                
            elif simple_item_match:
                if current_item:
                    items.append(current_item)
                    
                current_section = "items"
                current_item = {
                    "number": simple_item_match.group(1),
                    "title": simple_item_match.group(2).strip(),
                    "details": simple_item_match.group(3).strip()
                }
                
            elif title_match:
                if current_item:
                    items.append(current_item)
                    
                current_section = "items"
                current_item = {
                    "title": title_match.group(1).strip(),
                    "details": title_match.group(2).strip()
                }
                
            else:
                # Linha de continuação ou outro conteúdo
                if current_section == "intro" and not items:
                    intro_lines.append(line)
                elif current_section == "items" and current_item:
                    # Adiciona à descrição do item atual
                    if current_item.get("details"):
                        current_item["details"] += " " + line
                    else:
                        current_item["details"] = line
                elif items:  # Já temos itens, então é fechamento
                    current_section = "outro"
                    outro_lines.append(line)
                else:
                    intro_lines.append(line)
        
        # Adiciona último item se existir
        if current_item:
            items.append(current_item)
        
        # Monta textos das seções
        intro_text = " ".join(intro_lines) if intro_lines else ""
        outro_text = " ".join(outro_lines) if outro_lines else ""
        
        # Aplica formatação padrão se não houver introdução/fechamento adequados
        if not intro_text and items:
            if any("plano" in str(item).lower() for item in items):
                intro_text = "Claro! Aqui estão os planos disponíveis:"
                outro_text = "Se precisar de mais detalhes sobre algum plano, é só avisar!"
            elif any("médico" in str(item).lower() or "doutor" in str(item).lower() for item in items):
                intro_text = "Nossa equipe médica tem excelentes profissionais:"
                outro_text = "Posso ajudar com agendamento ou mais informações sobre algum médico específico?"
            else:
                intro_text = "Aqui estão as informações:"
                outro_text = "Precisa de mais alguma coisa?"
        
        # Usa format_structured_response
        return format_structured_response(intro_text, items, outro_text, session_key)
        
    def _build_system_prompt_with_full_context(self, conversation_context: str) -> str:
        """Constrói prompt do sistema com contexto completo da conversa"""
        
        knowledge_text = ""
        if self.knowledge:
            knowledge_text = json.dumps(self.knowledge, indent=2, ensure_ascii=False)
        
        # Prompt com contexto completo
        base_prompt = f"""Você é um assistente virtual inteligente com acesso ao histórico completo da conversa.

PERSONALIDADE:
- Seja natural, cordial e consistente
- NUNCA se reapresente se já fez isso antes na conversa
- NUNCA repita saudações desnecessariamente
- Use informações já compartilhadas pelo usuário
- Demonstre que acompanha o fluxo da conversa
- Seja conversacional e menos robótico

INSTRUÇÕES CRÍTICAS:
- SEMPRE consulte o histórico completo antes de responder
- Se já se apresentou, não faça novamente
- Se já sabe o nome do usuário, use-o naturalmente
- Se já sabe informações sobre o usuário, referencie-as
- Mantenha consistência com mensagens anteriores
- Responda de forma clara e objetiva
- Não invente informações não mencionadas

CONTEXTO COMPLETO DA CONVERSA:
{conversation_context}

CONHECIMENTO DISPONÍVEL:
{knowledge_text}

REGRAS DE RESPOSTA:
- Respostas entre 80-120 caracteres quando possível
- Se não souber algo específico, seja honesto
- Mantenha naturalidade e fluidez
- JAMAIS ignore o contexto da conversa
- Demonstre que você acompanha e lembra da conversa
"""
        
        return base_prompt
    
    def _analyze_intent(self, text: str, conversation_history: List[Dict]) -> str:
        """Analisa intenção considerando o histórico completo"""
        text_lower = text.lower()
        
        # Verifica se é realmente a primeira mensagem
        user_messages = [msg for msg in conversation_history if msg["role"] == "user"]
        is_truly_first = len(user_messages) == 0
        
        if is_truly_first and any(word in text_lower for word in ["olá", "oi", "bom dia", "boa tarde", "boa noite"]):
            return "first_greeting"
        elif any(word in text_lower for word in ["obrigado", "obrigada", "valeu", "tchau", "até logo"]):
            return "farewell"
        elif any(word in text_lower for word in ["ajuda", "help", "como", "o que", "quem"]):
            return "help_request"
        elif any(word in text_lower for word in ["preço", "valor", "quanto custa", "investimento"]):
            return "pricing"
        elif any(word in text_lower for word in ["contato", "telefone", "email", "endereço"]):
            return "contact_info"
        else:
            return "general"
    
    def _should_send_greeting(self, conversation_history: List[Dict]) -> bool:
        """Determina se deve enviar saudação baseado no histórico completo"""
        
        print(f"[DEBUG] Verificando se deve enviar saudação...")
        print(f"[DEBUG] Histórico tem {len(conversation_history)} mensagens")
        
        # Se não há histórico, é primeira interação
        if not conversation_history:
            print(f"[DEBUG] Sem histórico - primeira interação!")
            return True
        
        # Verifica se já se apresentou
        already_introduced = self._check_if_already_introduced(conversation_history)
        print(f"[DEBUG] Já se apresentou: {already_introduced}")
        
        return not already_introduced
    
    def _check_if_already_introduced(self, conversation_history: List[Dict]) -> bool:
        """Verifica se já se apresentou"""
        for msg in conversation_history:
            if msg["role"] == "assistant":
                content = msg["content"].lower()
                if any(phrase in content for phrase in ["sou", "eu sou", "assistente"]):
                    return True
        return False
    
    def _handle_first_interaction(self, message: Message, conversation_history: List[Dict]) -> List[str]:
        """Lida com primeira interação baseado no histórico completo"""
        
        # Verifica se realmente deve fazer saudação
        if not self._should_send_greeting(conversation_history):
            return []  # Não faz saudação
        
        try:
            hour = datetime.now().hour
            if 5 <= hour < 12:
                greeting = "Bom dia"
            elif hour < 18:
                greeting = "Boa tarde"
            else:
                greeting = "Boa noite"
            
            agent_name = self.knowledge.get("agent_name", "Timmy")
            business_name = self.knowledge.get("business_name", "nossa empresa")
            
            intent = self._analyze_intent(message.text, conversation_history)
            
            if intent == "first_greeting":
                response = f"{greeting}! Eu sou {agent_name}, assistente de {business_name}. Como posso ajudar você hoje?"
            elif intent == "help_request":
                response = f"{greeting}! Eu sou {agent_name}, assistente de {business_name}. Claro! Estou aqui para te ajudar. O que você gostaria de saber?"
            else:
                response = f"{greeting}! Eu sou {agent_name}, assistente de {business_name}. Vi que você quer saber sobre algo específico. Vou te ajudar!"
            
            return micro_responses(response, session_key=message.session_key)
            
        except Exception as e:
            print(f"[ERROR] Erro em _handle_first_interaction: {e}")
            return ["Olá! Como posso ajudar você hoje?"]
    
    def _collect_user_info(self, text: str, session_key: str) -> Dict[str, str]:
        """Coleta informações do usuário"""
        try:
            extracted = extract_info_from_text(text)
            collected = {}
            
            current_state = get_state(session_key)
            
            for key, value in extracted.items():
                if value and not current_state.get(key):
                    collected[key] = value
                    set_state(session_key, **{key: value})
            
            if collected:
                self._persist_user_data(session_key, current_state, collected)
            
            return collected
            
        except Exception as e:
            print(f"[ERROR] Erro em _collect_user_info: {e}")
            return {}
    
    def _persist_user_data(self, session_key: str, current_state: Dict, new_info: Dict):
        """Persiste dados do usuário usando estrutura por tenant"""
        try:
            all_user_data = {**current_state, **new_info}
            
            user_id = all_user_data.get("user_id")
            if not user_id:
                phone = all_user_data.get("phone")
                if phone:
                    existing_user = persistence_manager.get_user_by_phone(phone, self.tenant_id)
                    if existing_user:
                        user_id = existing_user.user_id
                        set_state(session_key, user_id=user_id)
                    else:
                        user_id = str(uuid.uuid4())
                        set_state(session_key, user_id=user_id)
                else:
                    user_id = str(uuid.uuid4())
                    set_state(session_key, user_id=user_id)
            
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
                notes=all_user_data.get("notes"),
                tenant_id=self.tenant_id
            )
            
            persistence_manager.save_user_info(user_info)
            
            session_info = persistence_manager.get_session_by_id(session_key, self.tenant_id)
            if not session_info:
                session_info = SessionInfo(
                    session_id=session_key,
                    user_id=user_id,
                    tenant_id=self.tenant_id,
                    channel="streamlit"
                )
                if all_user_data.get("phone"):
                    session_info.phone_number = all_user_data["phone"]
            else:
                session_info.user_id = user_id
                if all_user_data.get("phone"):
                    session_info.phone_number = all_user_data["phone"]
            
            persistence_manager.save_session_info(session_info)
            
        except Exception as e:
            print(f"[ERROR] Erro em _persist_user_data: {e}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
    
    def _save_message(self, session_key: str, role: str, content: str, intent: str = None):
        """Salva mensagem no histórico usando estrutura por tenant"""
        try:
            current_state = get_state(session_key)
            user_id = current_state.get("user_id")
            
            message = ConversationMessage(
                message_id=str(uuid.uuid4()),
                session_id=session_key,
                user_id=user_id,
                timestamp=datetime.now().isoformat(),
                role=role,
                content=content,
                intent=intent
            )
            
            # Salva mensagem no arquivo específico da conversa
            save_message(message, self.tenant_id)
            persistence_manager.update_session_message_count(session_key, self.tenant_id)
            
            # Atualiza contador local
            message_count = current_state.get("message_count", 0) + 1
            set_state(session_key, message_count=message_count)
            
        except Exception as e:
            print(f"[ERROR] Erro em _save_message: {e}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
    
    def _generate_contextual_response(self, message: Message, conversation_context: str) -> List[str]:
        """Gera resposta com base no contexto completo da conversa"""
        
        try:
            # Prompt para o usuário incluindo contexto completo
            user_prompt = f"""Baseado no histórico completo da conversa acima, responda à seguinte mensagem do usuário:

NOVA MENSAGEM: {message.text}

Responda de forma natural, consistente com a conversa e demonstrando que você acompanha o contexto. Não se reapresente se já fez isso. Use informações já compartilhadas pelo usuário."""
            
            system_prompt = self._build_system_prompt_with_full_context(conversation_context)
            
            response_text = chat_complete(
                system_prompt=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                max_tokens=400,  # Aumentado para permitir listas mais longas
                temperature=0.7
            )
            
            # 🔥 NOVA LÓGICA: Detecta e formata conteúdo estruturado automaticamente
            formatted_responses = self._detect_and_format_structured_content(
                response_text.strip(), 
                message.session_key
            )
            
            return formatted_responses
            
        except Exception as e:
            print(f"[ERROR] Erro em _generate_contextual_response: {e}")
            return ["Desculpe, tive um problema técnico. Pode tentar novamente?"]


def handle_turn(tenant_id: str, message: Message) -> List[str]:
    """Processa turno com releitura completa da conversa + workflow customizado"""
    
    print(f"\n[DEBUG] ===== INICIANDO handle_turn =====")
    print(f"[DEBUG] tenant_id: {tenant_id}")
    print(f"[DEBUG] message.text: '{message.text}'")
    print(f"[DEBUG] message.session_key: {message.session_key}")
    
    try:
        agent = TimmyAgent(tenant_id)
        
        # Inicializa revisor de conversa com tenant_id
        conversation_reviewer = ConversationReviewer(message.session_key, tenant_id)
        
        # PASSO 1: Salva a mensagem do usuário PRIMEIRO
        print(f"[DEBUG] PASSO 1: Salvando mensagem do usuário...")
        intent = "general"  # Será determinado depois com contexto completo
        agent._save_message(message.session_key, "user", message.text, intent)
        
        # PASSO 2: Recupera TODA a conversa (incluindo a mensagem que acabou de salvar)
        print(f"[DEBUG] PASSO 2: Recuperando conversa completa...")
        conversation_history = conversation_reviewer.get_full_conversation_history()
        
        # PASSO 3: Gera contexto completo para análise
        print(f"[DEBUG] PASSO 3: Gerando contexto completo...")
        conversation_context = conversation_reviewer.generate_conversation_context()
        
        print(f"[DEBUG] Contexto gerado para {len(conversation_history)} mensagens")
        
        # PASSO 4: Determina intent com contexto completo
        print(f"[DEBUG] PASSO 4: Determinando intent...")
        intent = agent._analyze_intent(message.text, conversation_history)
        print(f"[DEBUG] Intent determinado: {intent}")
        
        # PASSO 5: Verifica se deve fazer primeira interação
        print(f"[DEBUG] PASSO 5: Verificando primeira interação...")
        first_interaction = agent._handle_first_interaction(message, conversation_history)
        if first_interaction:
            print(f"[DEBUG] Enviando primeira interação: {first_interaction}")
            for response in first_interaction:
                agent._save_message(message.session_key, "assistant", response, "greeting")
            return first_interaction
        
        # 🔥 PASSO 5.5: Verifica se há estratégia consultiva ANTES do workflow
        print(f"[DEBUG] PASSO 5.5: Verificando estratégia consultiva...")
        
        try:
            from core.conversation_strategy import process_consultative_turn
            consultative_response = process_consultative_turn(tenant_id, message.text, message.session_key)
            
            if consultative_response:
                print(f"[DEBUG] Estratégia consultiva ativa: '{consultative_response}'")
                responses = micro_responses(consultative_response, min_chars=120, max_chars=200, session_key=message.session_key)
                for response in responses:
                    agent._save_message(message.session_key, "assistant", response, "consultative")
                print(f"[DEBUG] ===== handle_turn CONCLUÍDO (CONSULTIVO) =====\n")
                return responses
        except Exception as e:
            print(f"[DEBUG] Erro na estratégia consultiva: {e}")
        
        # 🔥 PASSO 5.6: Verifica se há workflow customizado
        print(f"[DEBUG] PASSO 5.6: Verificando workflow customizado...")
        workflow = load_tenant_workflow(tenant_id)
        
        if workflow and hasattr(workflow, 'process_message'):
            print(f"[DEBUG] Workflow encontrado: {type(workflow).__name__}")
            try:
                workflow_response = workflow.process_message(message, conversation_context)
                if workflow_response:
                    print(f"[DEBUG] Workflow processou: '{workflow_response}'")
                    responses = micro_responses(workflow_response, session_key=message.session_key)
                    for response in responses:
                        agent._save_message(message.session_key, "assistant", response, intent)
                    print(f"[DEBUG] ===== handle_turn CONCLUÍDO (WORKFLOW) =====\n")
                    return responses
            except Exception as e:
                print(f"[DEBUG] Erro no workflow: {e}")
                import traceback
                print(f"[DEBUG] Traceback do workflow: {traceback.format_exc()}")
                # Continua com fluxo padrão
                
        # PASSO 6: Coleta informações do usuário (fluxo padrão)
        print(f"[DEBUG] PASSO 6: Coletando informações...")
        collected_info = agent._collect_user_info(message.text, message.session_key)
        
        if collected_info:
            print(f"[INFO] Coletado: {collected_info}")
            
        # PASSO 7: Gera resposta com contexto completo (fluxo padrão)
        print(f"[DEBUG] PASSO 7: Gerando resposta contextual...")
        responses = agent._generate_contextual_response(message, conversation_context)
        print(f"[DEBUG] Respostas geradas: {responses}")
        
        # PASSO 8: Salva respostas do assistente
        print(f"[DEBUG] PASSO 8: Salvando respostas...")
        for response in responses:
            agent._save_message(message.session_key, "assistant", response, intent)
            
        print(f"[DEBUG] ===== handle_turn CONCLUÍDO =====\n")
        return responses
    
    except Exception as e:
        print(f"[ERROR DEBUG] Erro em handle_turn: {e}")
        print(f"[ERROR DEBUG] Traceback completo:")
        print(traceback.format_exc())
        return [f"Erro interno: {str(e)}"]


def process_message(text: str, tenant_id: str = "default", phone_number: str = None, session_key: str = None) -> List[str]:
    """Função de conveniência para processar mensagem"""
    
    try:
        if not session_key:
            session_key = f"session_{uuid.uuid4().hex[:8]}"
        
        if phone_number:
            session_key = f"phone_{phone_number.replace('+', '').replace(' ', '')}"
            user = get_or_create_user_by_phone(phone_number, tenant_id=tenant_id)
            set_state(session_key, user_id=user.user_id, phone=phone_number)
            
            session_info = persistence_manager.get_session_by_id(session_key, tenant_id)
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
        
    except Exception as e:
        print(f"[ERROR] Erro em process_message: {e}")
        return [f"Erro em process_message: {str(e)}"]


def get_user_history(phone_number: str, tenant_id: str = "default") -> Dict[str, Any]:
    """Busca histórico de usuário no tenant específico"""
    try:
        user = persistence_manager.get_user_by_phone(phone_number, tenant_id)
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
    """Retorna estatísticas dos dados do tenant específico"""
    return persistence_manager.get_tenant_stats(tenant_id)


def get_all_tenants_stats() -> Dict[str, Any]:
    """Retorna estatísticas de todos os tenants"""
    return persistence_manager.get_all_tenants_stats()