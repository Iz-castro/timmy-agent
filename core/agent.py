# core/agent.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import re
from datetime import datetime

from core.formatter import create_formatter
from core.llm import LLMClient
from core.persistence import PersistenceManager
from core.utils import load_tenant_config, load_tenant_knowledge


# ----------------------------- Tipos simples ---------------------------------
@dataclass
class Message:
    """Envelope mínimo de mensagem de entrada."""
    text: str
    session_key: str
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        self.text = (self.text or "").strip()
        self.metadata = self.metadata or {}


# ------------------------------- Agente --------------------------------------
class Agent:
    """
    Orquestrador principal do atendimento:
    ✅ MELHORADO: Descoberta ativa + memória robusta + abordagem consultiva
    - Identifica informações em falta
    - Prioriza descoberta antes de venda
    - Memória ativa completa e confiável
    - Abordagem consultiva inteligente
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.config = load_tenant_config(tenant_id)
        self.knowledge = load_tenant_knowledge(tenant_id)

        self.persistence = PersistenceManager(tenant_id=tenant_id)
        self.formatter = create_formatter(self.config)
        self.llm = LLMClient(self.config.get("llm", {}))

    # ----------------------------- Público -----------------------------------
    def process(self, message: Message) -> List[str]:
        """
        Processa um turno de conversa com descoberta ativa e memória robusta
        """
        try:
            # 1) Persistir mensagem do usuário
            self.persistence.save_message(
                message.session_key, role="user", content=message.text, metadata=message.metadata
            )

            # 2) ✅ MELHORADO: Extrair e persistir memória de forma mais robusta
            session_state = self.persistence.get_session_state(message.session_key)
            self._extract_and_persist_memory_enhanced(message, session_state)

            # 3) Registrar identidade para arquivo amigável
            self._maybe_register_identity(message, session_state)

            # 4) ✅ NOVO: Construir contexto completo com análise de descoberta
            context = self._build_discovery_context(message)

            # 5) ✅ NOVO: Verificar se é primeira mensagem para saudação consultiva
            is_first_message = len(context["history"]) <= 1
            if is_first_message:
                context["is_greeting"] = True
                context["greeting_template"] = self._get_consultive_greeting_template()

            # 6) Geração com LLM (agora com contexto consultivo)
            response = self.llm.generate_response(
                user_message=message.text,
                context=context,
                knowledge=self.knowledge,
                config=self.config,
            )

            # 7) Formatar em micro-mensagens
            chunks = self.formatter.format_response(response=response, context={"session_key": message.session_key})

            # 8) Persistir mensagens do assistente
            for c in chunks:
                self.persistence.save_message(
                    message.session_key, role="assistant", content=c, metadata={"formatted": True}
                )

            return chunks

        except Exception as e:
            fallback = "Ops! Algo deu errado. Pode tentar novamente?"
            self.persistence.save_message(
                message.session_key, role="assistant", content=fallback, metadata={"error": True, "detail": str(e)}
            )
            return [fallback]

    # --------------------------- Internos ------------------------------------
    def _build_discovery_context(self, message: Message) -> Dict[str, Any]:
        """
        ✅ NOVO: Monta contexto com foco em descoberta ativa e memória robusta
        """
        # Recupera TODA a conversa (sem limite)
        history = self.persistence.get_conversation_history(message.session_key, limit=None)
        session_state = self.persistence.get_session_state(message.session_key)

        # ✅ MELHORADO: Extrai dados da memória de forma mais inteligente
        memory_data = self._extract_comprehensive_memory(history, session_state)
        
        # ✅ NOVO: Análise consultiva (o que falta descobrir)
        analysis = self._analyze_consultive_needs(message.text, history, session_state, memory_data)

        # Contexto final que vai para o LLM
        return {
            "history": history,  # ✅ TODA a conversa para memória completa
            "session_state": session_state,
            "memory_data": memory_data,  # ✅ MELHORADO: Dados mais abrangentes
            "analysis": analysis,  # ✅ NOVO: Análise consultiva
            "tenant_info": {
                "name": self.config.get("agent_name", "Timmy"),
                "business": self.config.get("business_name", ""),
                "personality": self.config.get("personality", {}),
            },
        }

    def _extract_comprehensive_memory(self, history: List[Dict[str, Any]], session_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        ✅ MELHORADO: Extração de memória mais abrangente e inteligente
        """
        memory = {
            "client_name": session_state.get("client_name"),
            "business_area": session_state.get("business_area"),
            "company_name": session_state.get("company_name"),
            "interests": session_state.get("interests", []),
            "preferences": session_state.get("preferences", {}),
            "mentioned_facts": session_state.get("mentioned_facts", []),
            "problems_identified": session_state.get("problems_identified", []),
            "volume_info": session_state.get("volume_info", {}),
        }

        # ✅ NOVO: Análise mais sofisticada das mensagens do usuário
        user_messages = [msg["content"] for msg in history if msg["role"] == "user"]
        
        for msg_content in user_messages:
            msg_lower = msg_content.lower()
            
            # ✅ MELHORADO: Detecta área de negócio com mais padrões
            business_patterns = {
                "alimentação": ["restaurante", "comida", "lanche", "delivery", "picolé", "jabuticaba", "açaí", "padaria", "pizzaria"],
                "saúde": ["clínica", "consultório", "médico", "dentista", "fisio", "psicólogo", "veterinário"],
                "varejo": ["loja", "venda", "produto", "cliente", "estoque", "boutique", "farmácia"],
                "serviços": ["consultor", "advogado", "contador", "designer", "arquiteto", "corretor"],
                "educação": ["escola", "curso", "professor", "aluno", "ensino", "faculdade"],
                "tecnologia": ["software", "app", "sistema", "desenvolvedor", "programador", "ti"],
                "beleza": ["salão", "cabeleireiro", "estética", "manicure", "barbeiro"],
                "fitness": ["academia", "personal", "treino", "exercício", "pilates", "yoga"]
            }
            
            for area, keywords in business_patterns.items():
                if any(keyword in msg_lower for keyword in keywords):
                    if "business_areas" not in memory:
                        memory["business_areas"] = []
                    if area not in memory["business_areas"]:
                        memory["business_areas"].append(area)

            # ✅ NOVO: Detecta problemas e dores específicas
            problem_patterns = [
                r"problema com (.*?)(?:\.|,|$)",
                r"dificuldade (?:em|com) (.*?)(?:\.|,|$)",
                r"demora muito (.*?)(?:\.|,|$)",
                r"perco tempo com (.*?)(?:\.|,|$)",
                r"não consigo (.*?)(?:\.|,|$)"
            ]
            
            for pattern in problem_patterns:
                matches = re.findall(pattern, msg_content, re.IGNORECASE)
                for match in matches:
                    problem = match.strip()
                    if problem and len(problem) < 50:
                        if "problems_identified" not in memory:
                            memory["problems_identified"] = []
                        if problem not in memory["problems_identified"]:
                            memory["problems_identified"].append(problem)

            # ✅ NOVO: Detecta informações de volume
            volume_patterns = [
                r"(\d+)\s*(?:atendimentos?|conversas?|clientes?)",
                r"(?:cerca de|mais ou menos|aproximadamente)\s*(\d+)",
                r"por (?:dia|semana|mês).*?(\d+)"
            ]
            
            for pattern in volume_patterns:
                matches = re.findall(pattern, msg_content, re.IGNORECASE)
                for match in matches:
                    volume = match.strip()
                    if volume and volume.isdigit():
                        if "volume_info" not in memory:
                            memory["volume_info"] = {}
                        memory["volume_info"]["mentioned_volume"] = int(volume)

            # ✅ MELHORADO: Fatos importantes com mais padrões
            fact_patterns = [
                r"não tenho (.*?)(?:\.|,|$)",
                r"meu amigo (.*?)(?:\.|,|$)", 
                r"trabalho com (.*?)(?:\.|,|$)",
                r"vendo (.*?)(?:\.|,|$)",
                r"tenho uma? (.*?)(?:\.|,|$)",
                r"minha (.*?)(?:\.|,|$)",
                r"uso (.*?)(?:\.|,|$)"
            ]
            
            for pattern in fact_patterns:
                matches = re.findall(pattern, msg_content, re.IGNORECASE)
                for match in matches:
                    fact = match.strip()
                    if fact and len(fact) < 50:
                        if "mentioned_facts" not in memory:
                            memory["mentioned_facts"] = []
                        if fact not in memory["mentioned_facts"]:
                            memory["mentioned_facts"].append(fact)

        return memory

    def _analyze_consultive_needs(
        self, 
        text: str, 
        history: List[Dict[str, Any]], 
        session_state: Dict[str, Any],
        memory_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """✅ NOVO: Análise consultiva - o que ainda precisa descobrir"""
        t = text.lower()
        
        # Informações básicas em falta
        missing_basic_info = []
        if not memory_data.get("client_name"):
            missing_basic_info.append("nome")
        if not memory_data.get("business_area") and not memory_data.get("business_areas"):
            missing_basic_info.append("tipo_negocio")
        
        # Problemas e necessidades em falta
        missing_needs_info = []
        if not memory_data.get("problems_identified"):
            missing_needs_info.append("problemas_atuais")
        if not memory_data.get("volume_info"):
            missing_needs_info.append("volume_atendimento")
        
        # Intent detection melhorado
        intent_patterns = self.config.get("intent_patterns", {})
        detected_intent = "discovery_needed"
        
        for intent, keywords in intent_patterns.items():
            if any(kw in t for kw in keywords):
                detected_intent = intent
                break
        
        # Se tem informações básicas mas pede preços, pode mostrar
        if detected_intent == "pricing" and not missing_basic_info:
            conversation_phase = "pricing_ready"
        elif missing_basic_info:
            conversation_phase = "discovery_basic"
        elif missing_needs_info:
            conversation_phase = "discovery_needs"
        else:
            conversation_phase = "consultation"

        return {
            "message_count": len(history),
            "is_new_conversation": len(history) <= 2,
            "detected_intent": detected_intent,
            "conversation_phase": conversation_phase,
            "missing_basic_info": missing_basic_info,
            "missing_needs_info": missing_needs_info,
            "discovery_priority": "basic" if missing_basic_info else "needs" if missing_needs_info else "none",
            "requires_structured_response": detected_intent == "pricing" and conversation_phase == "pricing_ready",
        }

    def _get_consultive_greeting_template(self) -> str:
        """
        ✅ MELHORADO: Template de saudação consultiva com descoberta ativa
        """
        now = datetime.now()
        hour = now.hour
        
        # Determina turno do dia
        if 5 <= hour < 12:
            greeting = "Bom dia"
        elif 12 <= hour < 18:
            greeting = "Boa tarde"
        else:
            greeting = "Boa noite"
        
        agent_name = self.config.get("agent_name", "Timmy")
        business_name = self.config.get("business_name", "nossa empresa")
        
        # Template consultivo sempre com descoberta
        return f"{greeting}! Sou {agent_name}, consultor em automação de atendimento da {business_name}. Para te ajudar da melhor forma, qual seu nome e que tipo de negócio você tem?"

    # ✅ MELHORADO: Extração de memória mais robusta
    def _extract_and_persist_memory_enhanced(self, message: Message, session_state: Dict[str, Any]) -> None:
        """
        ✅ MELHORADO: Extração de memória mais robusta e inteligente
        """
        txt = message.text.strip()
        t = txt.lower()

        updates: Dict[str, Any] = {}

        # ✅ MELHORADO: Padrões de nome mais abrangentes
        name_patterns = [
            r"(?:me chamo|meu nome (?:é|e)|sou o?|sou a?|eu sou o?|eu sou a?) ([A-Za-zÀ-ÿ\s]+?)(?:\.|,|$|!|\?)",
            r"(?:eu sou|nome:|chamo) ([A-Za-zÀ-ÿ\s]+?)(?:\.|,|$|!|\?)",
            r"^([A-Za-zÀ-ÿ\s]{2,30})(?:,|\.|\s+aqui|\s+falando)$"  # Nome no início da frase
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, txt, re.IGNORECASE)
            if match:
                name = match.group(1).strip().title()
                # Validação melhorada
                if 2 <= len(name) <= 30 and not any(word in name.lower() for word in ["não", "sim", "ok", "oi", "olá"]):
                    updates["client_name"] = name
                    break

        # ✅ MELHORADO: Padrões de negócio mais abrangentes
        business_patterns = [
            r"(?:trabalho (?:na|no|com|como)|sou (?:da|do)|vendo|tenho uma?|minha empresa|meu negócio) ([^,.!?]{3,50})",
            r"(?:atuo (?:na|no|com)|área de|ramo de|setor de) ([^,.!?]{3,50})",
            r"(?:dono de|proprietário de|gerente de) ([^,.!?]{3,50})",
            r"([^,.!?]{3,50})(?:\s+é\s+meu\s+negócio|\s+é\s+minha\s+empresa)"
        ]
        
        for pattern in business_patterns:
            match = re.search(pattern, t, re.IGNORECASE)
            if match:
                business = match.group(1).strip()
                if business and len(business) <= 50:
                    updates["business_area"] = business
                    break

        # ✅ NOVO: Detecta problemas e dores específicas
        problems = session_state.get("problems_identified", [])
        problem_indicators = [
            r"problema com ([^,.!?]{3,40})",
            r"dificuldade (?:em|com|para) ([^,.!?]{3,40})",
            r"demora muito para ([^,.!?]{3,40})",
            r"perco tempo com ([^,.!?]{3,40})",
            r"não consigo ([^,.!?]{3,40})",
            r"muito trabalho para ([^,.!?]{3,40})"
        ]
        
        for pattern in problem_indicators:
            matches = re.findall(pattern, t, re.IGNORECASE)
            for match in matches:
                problem = match.strip()
                if problem and problem not in problems:
                    problems.append(problem)
        
        if problems:
            updates["problems_identified"] = problems

        # ✅ NOVO: Detecta informações de volume
        volume_info = session_state.get("volume_info", {})
        volume_patterns = [
            r"(\d+)\s*(?:atendimentos?|conversas?|clientes?|pessoas?)",
            r"(?:cerca de|mais ou menos|aproximadamente|uns?)\s*(\d+)",
            r"(\d+)\s*por\s*(?:dia|semana|mês)"
        ]
        
        for pattern in volume_patterns:
            matches = re.findall(pattern, t, re.IGNORECASE)
            for match in matches:
                if match.isdigit():
                    volume_info["mentioned_volume"] = int(match)
                    volume_info["context"] = txt  # Guarda contexto completo
                    break
        
        if volume_info:
            updates["volume_info"] = volume_info

        # ✅ MELHORADO: Preferências expandidas
        prefs = session_state.get("preferences", {})
        
        # Canal preferido
        if any(word in t for word in ["whatsapp", "zap", "telegram"]) and not prefs.get("channel"):
            prefs["channel"] = "WhatsApp"
        elif any(word in t for word in ["email", "e-mail"]) and not prefs.get("channel"):
            prefs["channel"] = "Email"
            
        # Estilo de comunicação
        if any(word in t for word in ["curtas", "curto", "objetiva", "direto", "rápido"]):
            prefs["communication_style"] = "direto"
        elif any(word in t for word in ["detalhado", "completo", "explicação", "tudo"]):
            prefs["communication_style"] = "detalhado"
        
        # Urgência
        if any(word in t for word in ["urgente", "rápido", "logo", "já"]):
            prefs["urgency"] = "alta"
            
        # Fatos importantes melhorados
        mentioned_facts = session_state.get("mentioned_facts", [])
        
        # ✅ MELHORADO: Detecta mais tipos de fatos importantes
        important_facts = [
            r"não tenho ([^,.!?]{3,30})",
            r"(?:meu|minha) ([^,.!?]{3,30})",
            r"preciso de ([^,.!?]{3,30})",
            r"uso ([^,.!?]{3,30})",
            r"comprei ([^,.!?]{3,30})",
            r"tenho ([^,.!?]{3,30})"
        ]
        
        for pattern in important_facts:
            matches = re.findall(pattern, t, re.IGNORECASE)
            for match in matches:
                fact = match.strip()
                if fact and fact not in mentioned_facts and len(fact) > 2:
                    mentioned_facts.append(fact)

        if prefs:
            updates["preferences"] = prefs
        if mentioned_facts:
            updates["mentioned_facts"] = mentioned_facts

        # ✅ NOVO: Timestamp da última atualização
        updates["last_updated"] = datetime.now().isoformat()

        # Salva as atualizações
        if updates:
            self.persistence.update_session_state(message.session_key, updates=updates)

            # Também cria/atualiza perfil do usuário
            user_id = (updates.get("client_name") or "anonymous").lower().replace(" ", "_")
            self.persistence.upsert_user_profile(user_id=user_id, updates={
                "name": updates.get("client_name", "Desconhecido"),
                "business_area": updates.get("business_area", ""),
                "problems_identified": problems,
                "volume_info": volume_info,
                "preferences": prefs,
                "mentioned_facts": mentioned_facts,
                "last_interaction": datetime.now().isoformat()
            })

    def _maybe_register_identity(self, message: Message, session_state: Dict[str, Any]) -> None:
        """
        Se o PersistenceManager tiver `register_identity`, registra nome/telefone
        para gerar o arquivo de conversa amigável (<slug>__<session>.csv).
        """
        if not hasattr(self.persistence, "register_identity"):
            return

        name = session_state.get("client_name")
        phone = None
        # Quando o webhook estiver ativo, preencha aqui o telefone:
        # phone = message.metadata.get("from")  # <- exemplo (comentado)

        # evita chamadas redundantes
        try:
            self.persistence.register_identity(
                session_key=message.session_key,
                name=name,
                phone=phone,
            )
        except Exception:
            # não deixar isso derrubar a conversa
            pass


# ---------------------------- Facade p/ apps ---------------------------------
def handle_turn(
    tenant_id: str,
    session_key: Optional[str] = None,
    user_id: Optional[str] = None,
    user_text: Optional[str] = None,
    message: Optional[Any] = None,
    **kwargs,
) -> List[str]:
    """
    Aceita:
      - handle_turn(tenant_id, session_key, user_id, user_text)
      - handle_turn(tenant_id, message={ 'text': ..., 'session_key': ..., 'metadata': ... })
      - handle_turn(tenant_id, message='texto', session_key='...', user_id='...')
    Retorna: List[str] - Lista das mensagens formatadas
    """
    # Normaliza entrada
    meta: Dict[str, Any] = {}
    if message is not None and user_text is None:
        if isinstance(message, str):
            user_text = message
        elif isinstance(message, dict):
            user_text = message.get("text")
            session_key = session_key or message.get("session_key")
            meta = message.get("metadata") or {}
        elif isinstance(message, Message):
            user_text = message.text
            session_key = session_key or message.session_key
            meta = message.metadata or {}

    user_text = user_text or ""
    session_key = session_key or "session_default"

    agent = Agent(tenant_id=tenant_id)
    pieces = agent.process(Message(text=user_text, session_key=session_key, metadata=meta))
    return pieces