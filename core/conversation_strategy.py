# -*- coding: utf-8 -*-
"""
Sistema de Conversação Consultiva - Abordagem universal para todas as personas
VERSÃO CORRIGIDA - Evita repetição de perguntas
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
        
        # Tipos de negócio expandidos - MELHOR DETECÇÃO
        business_patterns = {
            "construcao": ["material de construção", "construção", "locadora", "locadora de material"],
            "loja_roupas": ["loja de roupas", "loja de roupa", "vendo roupas", "boutique", "confecção"],
            "restaurante": ["restaurante", "lanchonete", "padaria", "pizzaria", "delivery"],
            "clinica": ["clínica", "consultório", "médico", "dentista", "fisioterapia"],
            "escritorio": ["escritório", "advocacia", "contabilidade", "consultoria"],
            "salao": ["salão", "barbearia", "estética", "beleza", "cabeleireiro"],
            "oficina": ["oficina", "mecânica", "auto center", "concessionária"],
            "escola": ["escola", "curso", "faculdade", "educação", "ensino"],
            "servicos": ["serviços", "manutenção", "limpeza", "segurança"],
            "varejo": ["loja", "comércio", "venda", "mercado"],
            "tecnologia": ["software", "desenvolvimento", "TI", "tecnologia", "sistema"]
        }
        
        # 🔥 CORREÇÃO: Detecta tipo de negócio MELHOR
        for business_type, patterns in business_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    extracted["business_type"] = business_type
                    extracted["business_description"] = pattern
                    print(f"[DEBUG CONSULTIVO] Detectado negócio: {business_type} - {pattern}")
                    break
            if "business_type" in extracted:
                break
        
        # Volume de clientes
        volume_patterns = [
            (r"(\d+)\s*(?:clientes?|pessoas?)\s*(?:por|no)\s*(?:dia|mês)", "volume_clients"),
            (r"atendo\s*(?:cerca de|uns|aproximadamente)?\s*(\d+)", "volume_clients"),
            (r"(\d+)\s*(?:vendas?|pedidos?)\s*(?:por|no)\s*(?:dia|mês)", "volume_sales"),
            (r"(?:uns|cerca de|aproximadamente)\s*(\d+)", "volume_clients")
        ]
        
        for pattern, key in volume_patterns:
            match = re.search(pattern, text_lower)
            if match:
                extracted[key] = match.group(1)
                print(f"[DEBUG CONSULTIVO] Detectado volume: {key} = {match.group(1)}")
                break
        
        # Canais de atendimento atuais
        channel_patterns = {
            "whatsapp": ["whatsapp", "zap", "wpp"],
            "instagram": ["instagram", "insta", "dm"],
            "telefone": ["telefone", "ligação", "call", "telefônico"],
            "presencial": ["presencial", "loja física", "balcão", "pessoalmente"],
            "site": ["site", "website", "online", "internet"],
            "email": ["email", "e-mail", "correio eletrônico"]
        }
        
        current_channels = current_state.get("current_channels", [])
        for channel, patterns in channel_patterns.items():
            for pattern in patterns:
                if pattern in text_lower and channel not in current_channels:
                    current_channels.append(channel)
                    extracted["current_channels"] = current_channels
                    print(f"[DEBUG CONSULTIVO] Detectado canal: {channel}")
                    break
        
        # Dores e problemas
        pain_patterns = {
            "tempo": ["muito tempo", "demora", "demorado", "perco tempo", "sem tempo"],
            "repeticao": ["sempre a mesma coisa", "perguntas repetitivas", "sempre perguntam", "repetindo"],
            "organizacao": ["desorganizado", "bagunça", "perco informação", "sem controle"],
            "volume": ["muitos clientes", "não dou conta", "sobrecarregado", "muito movimento"],
            "noturno": ["fora do horário", "à noite", "final de semana", "depois do expediente"],
            "qualidade": ["atendimento ruim", "demora para responder", "clientes reclamam"]
        }
        
        current_pains = current_state.get("pain_points", [])
        for pain, patterns in pain_patterns.items():
            for pattern in patterns:
                if pattern in text_lower and pain not in current_pains:
                    current_pains.append(pain)
                    extracted["pain_points"] = current_pains
                    print(f"[DEBUG CONSULTIVO] Detectada dor: {pain}")
                    break
        
        # Salva informações extraídas
        if extracted:
            for key, value in extracted.items():
                set_state(session_key, **{key: value})
                print(f"[DEBUG CONSULTIVO] Salvando: {key} = {value}")
        
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
        
        print(f"[DEBUG CONSULTIVO] Business info score: {business_info_score}")
        
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
        
        print(f"[DEBUG CONSULTIVO] Fase atual: {phase}")
        print(f"[DEBUG CONSULTIVO] Estado atual: {state}")
        
        # Evita perguntas já feitas
        asked_questions = state.get("asked_questions", [])
        
        if phase == "discovery":
            if not state.get("business_type"):
                if "business_type_asked" not in asked_questions:
                    set_state(session_key, asked_questions=asked_questions + ["business_type_asked"])
                    return "Que tipo de negócio você tem?"
            elif not state.get("volume_clients"):
                if "volume_asked" not in asked_questions:
                    set_state(session_key, asked_questions=asked_questions + ["volume_asked"])
                    return "Quantos clientes você costuma atender por mês?"
            elif not state.get("current_channels"):
                if "channels_asked" not in asked_questions:
                    set_state(session_key, asked_questions=asked_questions + ["channels_asked"])
                    return "Como seus clientes entram em contato com você hoje?"
        
        elif phase == "understanding":
            if "automation_experience" not in asked_questions:
                set_state(session_key, asked_questions=asked_questions + ["automation_experience"])
                return "Você já tentou automatizar alguma parte do atendimento antes?"
            elif "time_spent" not in asked_questions:
                set_state(session_key, asked_questions=asked_questions + ["time_spent"])
                return "Quanto tempo você ou sua equipe gastam respondendo as mesmas perguntas todos os dias?"
            elif "main_challenge" not in asked_questions:
                set_state(session_key, asked_questions=asked_questions + ["main_challenge"])
                return "Qual é sua maior dificuldade no atendimento atualmente?"
        
        elif phase == "positioning":
            business_type = state.get("business_type", "")
            if "solution_interest" not in asked_questions:
                set_state(session_key, asked_questions=asked_questions + ["solution_interest"])
                
                if "construcao" in business_type:
                    return "Imagina poder ter mais tempo para focar nos orçamentos enquanto um assistente cuida das consultas básicas?"
                elif "loja" in business_type or "varejo" in business_type:
                    return "Imagina poder focar só nas vendas enquanto um assistente cuida das perguntas básicas?"
                elif "clinica" in business_type:
                    return "E se você pudesse ter mais tempo para os pacientes, sem se preocupar com agendamentos repetitivos?"
                elif "restaurante" in business_type:
                    return "Como seria poder automatizar pedidos e dúvidas básicas, deixando sua equipe livre para o atendimento?"
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
        has_business_info = bool(state.get("business_type"))
        
        print(f"[DEBUG CONSULTIVO] Should present solution? Phase: {phase}, Asked: {asked_questions}, Pain: {has_pain_points}, Business: {has_business_info}")
        
        return (phase == "positioning" and 
                asked_questions >= 2 and 
                (has_pain_points or has_business_info))
    
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
        if "volume" in pains:
            specific_benefits.append("lidar melhor com o volume de clientes")
        
        # Se não tem dores específicas, usa benefícios gerais
        if not specific_benefits:
            if "construcao" in business_type:
                specific_benefits = ["otimizar consultas de orçamentos", "qualificar leads automaticamente"]
            elif "clinica" in business_type:
                specific_benefits = ["agilizar agendamentos", "reduzir tempo com dúvidas básicas"]
            else:
                specific_benefits = ["melhorar a eficiência do atendimento", "focar no que realmente importa"]
        
        return {
            "recommended_plan": recommended_plan,
            "plan_reason": plan_reason,
            "specific_benefits": specific_benefits,
            "business_context": business_type
        }


def process_consultative_turn(tenant_id: str, text: str, session_key: str) -> Optional[str]:
        """
        CORREÇÃO: Processa turno consultivo com detecção de finalização
        """
        strategy = ConsultativeStrategy(tenant_id)
    
        text_lower = text.lower()
    
        # 🔥 NOVA LÓGICA: Detecta quando cliente já decidiu/finalizou
        finalization_signals = [
                "já escolhi", "já decidi", "escolhi o", "quero o", 
                "vou com o", "fechado", "ok", "beleza", "perfeito",
                "já me explicou", "já entendi", "obrigado", "obrigada"
        ]
    
        if any(signal in text_lower for signal in finalization_signals):
                print(f"[DEBUG CONSULTIVO] Sinal de finalização detectado: '{text}'")
            
                # Verifica se cliente mencionou plano específico
                plan_mentions = {
                        "essencial": ["essencial", "básico", "primeiro"],
                        "profissional": ["profissional", "segundo", "do meio"],
                        "premium": ["premium", "terceiro", "ilimitado"], 
                        "enterprise": ["enterprise", "quarto", "completo"]
                }
            
                chosen_plan = None
                for plan, keywords in plan_mentions.items():
                        if any(keyword in text_lower for keyword in keywords):
                                chosen_plan = plan
                                break
                    
                if chosen_plan:
                        # Cliente escolheu plano específico - finaliza consultivamente
                        return f"Perfeito! O plano {chosen_plan.title()} é uma excelente escolha para seu negócio. Vou conectar você com nossa equipe para finalizar. Preciso do seu nome e telefone para o contato."
            
                elif "obrigad" in text_lower or "tchau" in text_lower:
                        # Cliente agradecendo/se despedindo
                        return "Disponha! Se precisar de mais informações ou quiser uma proposta personalizada, estarei aqui. Boa sorte com seu projeto!"
            
                else:
                        # Cliente sinalizou decisão mas não especificou plano
                        return "Que bom que as informações foram úteis! Qual plano despertou mais seu interesse? Posso te conectar com nossa equipe para uma proposta personalizada."
            
        # 🔥 CORREÇÃO: Verifica se já apresentou solução recentemente
        state = get_state(session_key)
        recent_actions = state.get("recent_consultative_actions", [])
    
        # Se já ofereceu solução nas últimas 2 interações, para o loop
        if len(recent_actions) >= 2 and all("solution_offered" in action for action in recent_actions[-2:]):
                print(f"[DEBUG CONSULTIVO] Já ofereceu solução recentemente - parando loop consultivo")
                return None  # Deixa o fluxo normal lidar
    
        # Continua lógica consultiva normal...
        extracted_info = strategy.extract_business_info(text, session_key)
    
        if extracted_info:
                # [resto da lógica como antes...]
                business_type = extracted_info.get("business_type")
                response_parts = []
            
                if business_type == "construcao":
                        response_parts.append("Locadora de material de construção, excelente! Área com muito movimento e consultas.")
                # [outros tipos...]
                    
                consultative_question = strategy.generate_consultative_question(session_key, text)
                if consultative_question:
                        response_parts.append(consultative_question)
                    
                if response_parts:
                        return " ".join(response_parts)
            
        # Apresenta solução apenas se deve E ainda não ofereceu demais
        if strategy.should_present_solution(session_key):
                # Marca que ofereceu solução
                recent_actions.append("solution_offered")
                if len(recent_actions) > 5:  # Mantém apenas últimas 5 ações
                        recent_actions = recent_actions[-5:]
                set_state(session_key, recent_consultative_actions=recent_actions)
            
                solution = strategy.get_personalized_solution(session_key)
                response = f"Pelo que você me contou, acredito que posso ajudar você a {', '.join(solution['specific_benefits'][:2])}. "
                response += f"Para seu tipo de negócio, o plano {solution['recommended_plan'].title()} seria {solution['plan_reason']}. "
                response += "Quer que eu te explique como funcionaria na prática?"
            
                return response
    
        # Se não deve mais agir consultivamente, retorna None
        return None

