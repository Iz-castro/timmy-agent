# -*- coding: utf-8 -*-
"""
Sistema de Conversação Consultiva - Abordagem universal para todas as personas
"""

import re
from typing import Dict, List, Any, Optional
from core.utils import get_state, set_state


class ConsultativeStrategy:
    """
    Sistema consultivo que:
    1. Coleta informações de forma natural
    2. Constrói confiança antes de vender
    3. Direciona ao produto/serviço ideal gradualmente
    """
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        
        # Fases da conversa consultiva
        self.conversation_phases = {
            "discovery": {
                "priority": 1,
                "questions": [
                    "Que tipo de negócio você tem?",
                    "Quantos clientes você atende por mês?",
                    "Como você faz o atendimento hoje?",
                    "Qual sua maior dificuldade no atendimento?"
                ]
            },
            "understanding": {
                "priority": 2,
                "questions": [
                    "Você já tentou automatizar alguma parte do atendimento?",
                    "Quanto tempo sua equipe gasta respondendo perguntas repetitivas?",
                    "Seus clientes preferem WhatsApp, site ou telefone?"
                ]
            },
            "positioning": {
                "priority": 3,
                "questions": [
                    "Você gostaria de ter mais tempo para focar no que realmente importa?",
                    "Como seria ideal para você automatizar sem perder o toque humano?"
                ]
            }
        }
    
    def extract_business_info(self, text: str, session_key: str) -> Dict[str, Any]:
        """
        Extração melhorada de informações de negócio
        """
        current_state = get_state(session_key)
        extracted = {}
        
        text_lower = text.lower()
        
        # Tipos de negócio expandidos
        business_patterns = {
            "loja_roupas": ["loja de roupas", "loja de roupa", "vendo roupas", "boutique", "confecção"],
            "restaurante": ["restaurante", "lanchonete", "padaria", "pizzaria", "delivery"],
            "clinica": ["clínica", "consultório", "médico", "dentista", "fisioterapia"],
            "escritorio": ["escritório", "advocacia", "contabilidade", "consultoria"],
            "salao": ["salão", "barbearia", "estética", "beleza", "cabeleireiro"],
            "oficina": ["oficina", "mecânica", "auto center", "concessionária"],
            "escola": ["escola", "curso", "faculdade", "educação", "ensino"],
            "servicos": ["serviços", "manutenção", "limpeza", "segurança"]
        }
        
        # Detecta tipo de negócio
        for business_type, patterns in business_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    extracted["business_type"] = business_type
                    extracted["business_description"] = pattern
                    break
            if "business_type" in extracted:
                break
        
        # Volume de clientes
        volume_patterns = [
            (r"(\d+)\s*(?:clientes?|pessoas?)\s*(?:por|no)\s*(?:dia|mês)", "volume_clients"),
            (r"atendo\s*(?:cerca de|uns|aproximadamente)?\s*(\d+)", "volume_clients"),
            (r"(\d+)\s*(?:vendas?|pedidos?)\s*(?:por|no)\s*(?:dia|mês)", "volume_sales")
        ]
        
        for pattern, key in volume_patterns:
            match = re.search(pattern, text_lower)
            if match:
                extracted[key] = match.group(1)
                break
        
        # Canais de atendimento atuais
        channel_patterns = {
            "whatsapp": ["whatsapp", "zap", "wpp"],
            "instagram": ["instagram", "insta", "dm"],
            "telefone": ["telefone", "ligação", "call"],
            "presencial": ["presencial", "loja física", "balcão"],
            "site": ["site", "website", "online"]
        }
        
        current_channels = current_state.get("current_channels", [])
        for channel, patterns in channel_patterns.items():
            for pattern in patterns:
                if pattern in text_lower and channel not in current_channels:
                    current_channels.append(channel)
                    extracted["current_channels"] = current_channels
                    break
        
        # Dores e problemas
        pain_patterns = {
            "tempo": ["muito tempo", "demora", "demorado", "perco tempo"],
            "repeticao": ["sempre a mesma coisa", "perguntas repetitivas", "sempre perguntam"],
            "organizacao": ["desorganizado", "bagunça", "perco informação"],
            "volume": ["muitos clientes", "não dou conta", "sobrecarregado"],
            "noturno": ["fora do horário", "à noite", "final de semana"]
        }
        
        current_pains = current_state.get("pain_points", [])
        for pain, patterns in pain_patterns.items():
            for pattern in patterns:
                if pattern in text_lower and pain not in current_pains:
                    current_pains.append(pain)
                    extracted["pain_points"] = current_pains
                    break
        
        # Salva informações extraídas
        if extracted:
            for key, value in extracted.items():
                set_state(session_key, **{key: value})
        
        return extracted
    
    def get_conversation_phase(self, session_key: str) -> str:
        """
        Determina em que fase da conversa consultiva estamos
        """
        state = get_state(session_key)
        
        # Conta quantas informações já temos
        business_info_score = 0
        if state.get("business_type"): business_info_score += 2
        if state.get("volume_clients"): business_info_score += 1
        if state.get("current_channels"): business_info_score += 1
        if state.get("pain_points"): business_info_score += 1
        
        # Determina fase baseado no que já sabemos
        if business_info_score < 2:
            return "discovery"
        elif business_info_score < 4:
            return "understanding"
        else:
            return "positioning"
    
    def generate_consultative_question(self, session_key: str, context: str) -> Optional[str]:
        """
        Gera pergunta consultiva baseada na fase atual
        """
        phase = self.get_conversation_phase(session_key)
        state = get_state(session_key)
        
        # Evita perguntas já feitas
        asked_questions = state.get("asked_questions", [])
        
        if phase == "discovery":
            if not state.get("business_type"):
                return "Que tipo de negócio você tem?"
            elif not state.get("volume_clients"):
                return "Quantos clientes você costuma atender?"
            elif not state.get("current_channels"):
                return "Como seus clientes entram em contato com você hoje?"
        
        elif phase == "understanding":
            if "automation_experience" not in asked_questions:
                set_state(session_key, asked_questions=asked_questions + ["automation_experience"])
                return "Você já tentou automatizar alguma parte do atendimento antes?"
            elif "time_spent" not in asked_questions:
                set_state(session_key, asked_questions=asked_questions + ["time_spent"])
                return "Quanto tempo você ou sua equipe gastam respondendo as mesmas perguntas todos os dias?"
        
        elif phase == "positioning":
            business_type = state.get("business_type", "")
            if "loja" in business_type:
                return "Imagina poder focar só nas vendas enquanto um assistente cuida das perguntas básicas?"
            elif "clinica" in business_type:
                return "E se você pudesse ter mais tempo para os pacientes, sem se preocupar com agendamentos repetitivos?"
            else:
                return "Como seria ideal para você: automatizar sem perder o toque pessoal com seus clientes?"
        
        return None
    
    def should_present_solution(self, session_key: str) -> bool:
        """
        Determina se já é hora de apresentar uma solução
        """
        phase = self.get_conversation_phase(session_key)
        state = get_state(session_key)
        
        # Só apresenta solução se:
        # 1. Está na fase de positioning
        # 2. Cliente demonstrou interesse/problema
        # 3. Já fizemos pelo menos 2 perguntas consultivas
        
        asked_questions = len(state.get("asked_questions", []))
        has_pain_points = len(state.get("pain_points", [])) > 0
        
        return (phase == "positioning" and 
                asked_questions >= 2 and 
                has_pain_points)
    
    def get_personalized_solution(self, session_key: str) -> Dict[str, Any]:
        """
        Sugere solução personalizada baseada no perfil coletado
        """
        state = get_state(session_key)
        
        business_type = state.get("business_type", "")
        volume = int(state.get("volume_clients", "0") or "0")
        channels = state.get("current_channels", [])
        pains = state.get("pain_points", [])
        
        # Lógica de recomendação personalizada
        if volume <= 50:
            recommended_plan = "essencial"
            plan_reason = "ideal para começar com automação"
        elif volume <= 200:
            recommended_plan = "profissional"
            plan_reason = "perfeito para seu volume de clientes"
        else:
            recommended_plan = "premium"
            plan_reason = "necessário para atender seu volume com qualidade"
        
        # Benefícios específicos para o negócio
        specific_benefits = []
        if "tempo" in pains:
            specific_benefits.append("recuperar horas do seu dia")
        if "repeticao" in pains:
            specific_benefits.append("eliminar perguntas repetitivas")
        if "noturno" in pains:
            specific_benefits.append("atender clientes 24/7")
        
        return {
            "recommended_plan": recommended_plan,
            "plan_reason": plan_reason,
            "specific_benefits": specific_benefits,
            "business_context": business_type
        }


def process_consultative_turn(tenant_id: str, text: str, session_key: str) -> Optional[str]:
    """
    Processa turno usando estratégia consultiva
    Retorna resposta consultiva ou None se deve seguir fluxo normal
    """
    strategy = ConsultativeStrategy(tenant_id)
    
    # 1. Extrai informações de negócio
    extracted_info = strategy.extract_business_info(text, session_key)
    
    # 2. Se extraiu informações importantes, reconhece e faz pergunta consultiva
    if extracted_info:
        business_type = extracted_info.get("business_type")
        volume = extracted_info.get("volume_clients")
        
        response_parts = []
        
        # Reconhece a informação compartilhada
        if business_type:
            if "loja_roupas" in business_type:
                response_parts.append("Que legal, loja de roupas! O mercado de moda é bem dinâmico.")
            elif "restaurante" in business_type:
                response_parts.append("Restaurante, excelente! Imagino que vocês têm bastante movimento.")
            elif "clinica" in business_type:
                response_parts.append("Clínica médica, área muito importante! Vocês devem ter muito agendamento.")
        
        if volume:
            response_parts.append(f"Atender {volume} clientes dá trabalho mesmo!")
        
        # Faz pergunta consultiva
        consultative_question = strategy.generate_consultative_question(session_key, text)
        if consultative_question:
            response_parts.append(consultative_question)
        
        if response_parts:
            return " ".join(response_parts)
    
    # 3. Se já tem informações suficientes e cliente demonstra interesse, sugere solução
    if strategy.should_present_solution(session_key):
        solution = strategy.get_personalized_solution(session_key)
        
        response = f"Pelo que você me contou, acredito que posso ajudar você a {', '.join(solution['specific_benefits'][:2])}. "
        response += f"Para seu tipo de negócio, o plano {solution['recommended_plan'].title()} seria {solution['plan_reason']}. "
        response += "Quer que eu te explique como funcionaria na prática?"
        
        return response
    
    # 4. Se está em conversa consultiva mas ainda coletando, faz mais perguntas
    consultative_question = strategy.generate_consultative_question(session_key, text)
    if consultative_question:
        return consultative_question
    
    # Se não se encaixa em estratégia consultiva, retorna None (fluxo normal)
    return None