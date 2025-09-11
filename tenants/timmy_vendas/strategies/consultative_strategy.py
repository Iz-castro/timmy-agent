# -*- coding: utf-8 -*-
"""
Estratégia Consultiva - CORRIGIDO: Bug de repetição após coleta de informação
"""

import re
from typing import Dict, List, Any, Optional

# Nova arquitetura
from core.interfaces.strategy import ConversationStrategy, Message, ConversationContext

# Compatibilidade com sistema legado
try:
    from core.utils import get_state, set_state
except ImportError:
    # Fallback se utils não estiver disponível
    _state = {}
    def get_state(key): return _state.get(key, {})
    def set_state(key, **kwargs): _state.setdefault(key, {}).update(kwargs)


class ConsultativeStrategy(ConversationStrategy):
    """
    Sistema consultivo que:
    1. Coleta informações de forma natural
    2. Constrói confiança antes de vender
    3. Direciona ao produto/serviço ideal gradualmente
    
    CORRIGIDO: Lógica de progressão após coleta de informações
    """
    
    def __init__(self, tenant_id: str, config: Dict[str, Any] = None):
        super().__init__(tenant_id, config)
        
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
    
    def should_activate(self, message: Message, context: ConversationContext) -> bool:
        """
        Determina se esta estratégia deve ser ativada
        
        Ativa para tenants de vendas quando há indicadores de negócio
        """
        # Só ativa para tenants de vendas
        if self.tenant_id != "timmy_vendas":
            return False
        
        text_lower = message.text.lower()
        
        # Indicadores de conversa de negócio
        business_indicators = [
            "negócio", "empresa", "clientes", "atendimento", "vendas",
            "automatizar", "whatsapp", "sistema", "ferramenta",
            "quanto custa", "preço", "valor", "planos"
        ]
        
        has_business_context = any(indicator in text_lower for indicator in business_indicators)
        
        # Verifica se já coletou informações de negócio
        collected_business_info = len([
            k for k in ["business_type", "volume_clients", "current_channels", "pain_points"]
            if context.user_state.get(k)
        ])
        
        # Ativa se há contexto de negócio ou se já está coletando informações
        return has_business_context or collected_business_info > 0
    
    def process_turn(self, message: Message, context: ConversationContext) -> Optional[str]:
        """
        Processa o turno da conversa usando estratégia consultiva
        CORRIGIDO: Verifica se informação já foi coletada antes de repetir pergunta
        """
        print(f"[CONSULTIVE] Processando mensagem: '{message.text}'")
        print(f"[CONSULTIVE] Estado atual: {context.user_state}")
        
        # 1. Extrai informações de negócio
        extracted_info = self.extract_business_info(message.text, context)
        
        # 2. Atualiza contexto com informações extraídas
        if extracted_info:
            print(f"[CONSULTIVE] Informações extraídas: {extracted_info}")
            self.update_context(context, extracted_info)
        
        # 3. NOVA LÓGICA: Se extraiu informações importantes, confirma e progride
        if extracted_info:
            response_parts = []
            
            # Reconhece a informação compartilhada
            business_type = extracted_info.get("business_type")
            volume = extracted_info.get("volume_clients")
            
            if business_type:
                if "loja_roupas" in business_type:
                    response_parts.append("Que legal, loja de roupas! O mercado de moda é bem dinâmico.")
                elif "restaurante" in business_type:
                    response_parts.append("Restaurante, excelente! Imagino que vocês têm bastante movimento.")
                elif "clinica" in business_type:
                    response_parts.append("Clínica médica, área muito importante! Vocês devem ter muito agendamento.")
                elif "escritorio" in business_type:
                    response_parts.append("Escritório, perfeito! Área que sempre tem demanda por organização.")
                elif "servicos" in business_type:
                    response_parts.append("Área de serviços, excelente! Sempre tem bastante contato com clientes.")
                else:
                    response_parts.append("Interessante! Cada tipo de negócio tem suas particularidades.")
            
            if volume:
                response_parts.append(f"Atender {volume} clientes dá trabalho mesmo!")
            
            # CORRIGIDO: Só faz pergunta se não tiver a informação ainda
            next_question = self.get_next_needed_question(context)
            if next_question:
                response_parts.append(next_question)
            elif self.should_present_solution(context):
                # Se tem informações suficientes, apresenta solução
                solution = self.get_personalized_solution(context)
                solution_text = f"Pelo que você me contou, o plano {solution['recommended_plan'].title()} seria {solution['plan_reason']}. "
                solution_text += "Quer que eu te explique como funcionaria na prática?"
                response_parts.append(solution_text)
            
            if response_parts:
                return " ".join(response_parts)
        
        # 4. CORRIGIDO: Verifica se usuário está perguntando sobre preços especificamente
        text_lower = message.text.lower()
        if any(word in text_lower for word in ["preço", "valor", "quanto custa", "planos"]):
            # Se já tem tipo de negócio, pode falar de preços
            if context.user_state.get("business_type"):
                return self.handle_pricing_question(context)
            else:
                # Se não tem tipo de negócio, explica por que precisa saber
                return "Para te dar a melhor recomendação de plano, preciso entender um pouco sobre seu negócio. Que tipo de empresa você tem?"
        
        # 5. Se já tem informações suficientes e cliente demonstra interesse, sugere solução
        if self.should_present_solution(context):
            solution = self.get_personalized_solution(context)
            
            response = f"Pelo que você me contou, acredito que posso ajudar você a {', '.join(solution['specific_benefits'][:2])}. "
            response += f"Para seu tipo de negócio, o plano {solution['recommended_plan'].title()} seria {solution['plan_reason']}. "
            response += "Quer que eu te explique como funcionaria na prática?"
            
            return response
        
        # 6. CORRIGIDO: Só faz pergunta consultiva se realmente precisar da informação
        consultative_question = self.get_next_needed_question(context)
        if consultative_question:
            return consultative_question
        
        # Se não se encaixa em estratégia consultiva, retorna None (fluxo normal)
        return None
    
    def get_next_needed_question(self, context: ConversationContext) -> Optional[str]:
        """
        NOVA FUNÇÃO: Retorna próxima pergunta necessária ou None se tem tudo
        """
        # Verifica quais informações ainda faltam
        missing_info = []
        
        if not context.user_state.get("business_type"):
            missing_info.append("business_type")
        
        if not context.user_state.get("volume_clients"):
            missing_info.append("volume_clients")
        
        if not context.user_state.get("current_channels"):
            missing_info.append("current_channels")
        
        # Evita perguntas já feitas
        asked_questions = context.user_state.get("asked_questions", [])
        
        # Prioriza por ordem de importância
        if "business_type" in missing_info:
            return "Que tipo de negócio você tem?"
        
        elif "volume_clients" in missing_info:
            return "Quantos clientes você costuma atender por mês?"
        
        elif "current_channels" in missing_info:
            return "Como seus clientes entram em contato com você hoje?"
        
        elif "automation_experience" not in asked_questions:
            asked_questions.append("automation_experience")
            context.user_state["asked_questions"] = asked_questions
            return "Você já tentou automatizar alguma parte do atendimento antes?"
        
        elif "time_spent" not in asked_questions:
            asked_questions.append("time_spent")
            context.user_state["asked_questions"] = asked_questions
            return "Quanto tempo você ou sua equipe gastam respondendo as mesmas perguntas todos os dias?"
        
        # Se chegou aqui, tem informações suficientes
        return None
    
    def handle_pricing_question(self, context: ConversationContext) -> str:
        """
        NOVA FUNÇÃO: Trata perguntas específicas sobre preços
        """
        business_type = context.user_state.get("business_type", "")
        volume = int(context.user_state.get("volume_clients", "0") or "0")
        
        # Personaliza resposta baseada no que já sabe
        if volume > 0:
            if volume <= 50:
                recommended_plan = "Essencial"
                price = "R$ 750/mês"
                reason = "ideal para começar com automação"
            elif volume <= 200:
                recommended_plan = "Profissional"
                price = "R$ 1.400/mês"
                reason = "perfeito para seu volume de clientes"
            else:
                recommended_plan = "Premium"
                price = "R$ 2.000/mês"
                reason = "necessário para atender seu volume com qualidade"
        else:
            # Não sabe o volume ainda
            recommended_plan = "Profissional"
            price = "R$ 1.400/mês"
            reason = "nosso plano mais popular"
        
        business_context = ""
        if "loja" in business_type:
            business_context = "Para lojas, o Timmy ajuda com dúvidas sobre produtos, disponibilidade e atendimento básico."
        elif "restaurante" in business_type:
            business_context = "Para restaurantes, o Timmy pode ajudar com cardápio, horários e pedidos básicos."
        elif "clinica" in business_type:
            business_context = "Para clínicas, o Timmy ajuda com agendamentos, informações sobre procedimentos e triagem inicial."
        
        response = f"Para seu tipo de negócio, recomendo o plano {recommended_plan} por {price} - {reason}. "
        if business_context:
            response += business_context + " "
        response += "Quer que eu detalhe o que está incluído?"
        
        return response
    
    def extract_business_info(self, text: str, context: ConversationContext) -> Dict[str, Any]:
        """
        Extração melhorada de informações de negócio
        CORRIGIDO: Detecta mais tipos de negócio
        """
        extracted = {}
        text_lower = text.lower()
        
        # Tipos de negócio expandidos
        business_patterns = {
            "loja_roupas": ["loja de roupas", "loja de roupa", "vendo roupas", "boutique", "confecção"],
            "restaurante": ["restaurante", "lanchonete", "padaria", "pizzaria", "delivery", "food"],
            "clinica": ["clínica", "consultório", "médico", "dentista", "fisioterapia"],
            "escritorio": ["escritório", "advocacia", "contabilidade", "consultoria", "conservadora"],
            "salao": ["salão", "barbearia", "estética", "beleza", "cabeleireiro"],
            "oficina": ["oficina", "mecânica", "auto center", "concessionária"],
            "escola": ["escola", "curso", "faculdade", "educação", "ensino"],
            "servicos": ["serviços", "manutenção", "limpeza", "segurança"]
        }
        
        # CORRIGIDO: Só extrai se ainda não tem essa informação
        if not context.user_state.get("business_type"):
            for business_type, patterns in business_patterns.items():
                for pattern in patterns:
                    if pattern in text_lower:
                        extracted["business_type"] = business_type
                        extracted["business_description"] = pattern
                        print(f"[CONSULTIVE] Detectado tipo de negócio: {business_type}")
                        break
                if "business_type" in extracted:
                    break
        
        # Volume de clientes - só se não tem ainda
        if not context.user_state.get("volume_clients"):
            volume_patterns = [
                (r"(\d+)\s*(?:clientes?|pessoas?)\s*(?:por|no)\s*(?:dia|mês)", "volume_clients"),
                (r"atendo\s*(?:cerca de|uns|aproximadamente)?\s*(\d+)", "volume_clients"),
                (r"(\d+)\s*(?:vendas?|pedidos?)\s*(?:por|no)\s*(?:dia|mês)", "volume_sales")
            ]
            
            for pattern, key in volume_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    extracted[key] = match.group(1)
                    print(f"[CONSULTIVE] Detectado volume: {match.group(1)}")
                    break
        
        # Canais de atendimento atuais - só se não tem ainda
        if not context.user_state.get("current_channels"):
            channel_patterns = {
                "whatsapp": ["whatsapp", "zap", "wpp"],
                "instagram": ["instagram", "insta", "dm"],
                "telefone": ["telefone", "ligação", "call"],
                "presencial": ["presencial", "loja física", "balcão"],
                "site": ["site", "website", "online"]
            }
            
            current_channels = context.user_state.get("current_channels", [])
            for channel, patterns in channel_patterns.items():
                for pattern in patterns:
                    if pattern in text_lower and channel not in current_channels:
                        current_channels.append(channel)
                        extracted["current_channels"] = current_channels
                        print(f"[CONSULTIVE] Detectado canal: {channel}")
                        break
        
        return extracted
    
    def get_conversation_phase(self, context: ConversationContext) -> str:
        """
        Determina em que fase da conversa consultiva estamos
        """
        # Conta quantas informações já temos
        business_info_score = 0
        if context.user_state.get("business_type"): business_info_score += 2
        if context.user_state.get("volume_clients"): business_info_score += 1
        if context.user_state.get("current_channels"): business_info_score += 1
        if context.user_state.get("pain_points"): business_info_score += 1
        
        # Determina fase baseado no que já sabemos
        if business_info_score < 2:
            return "discovery"
        elif business_info_score < 4:
            return "understanding"
        else:
            return "positioning"
    
    def should_present_solution(self, context: ConversationContext) -> bool:
        """
        Determina se já é hora de apresentar uma solução
        CORRIGIDO: Critérios mais flexíveis
        """
        # Precisa pelo menos do tipo de negócio
        if not context.user_state.get("business_type"):
            return False
        
        # Se tem tipo de negócio + qualquer outra informação, já pode sugerir
        other_info = [
            context.user_state.get("volume_clients"),
            context.user_state.get("current_channels"),
            context.user_state.get("pain_points")
        ]
        
        return any(other_info)
    
    def get_personalized_solution(self, context: ConversationContext) -> Dict[str, Any]:
        """
        Sugere solução personalizada baseada no perfil coletado
        """
        business_type = context.user_state.get("business_type", "")
        volume = int(context.user_state.get("volume_clients", "0") or "0")
        channels = context.user_state.get("current_channels", [])
        pains = context.user_state.get("pain_points", [])
        
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
        
        # Se não tem pain points específicos, usa genéricos baseados no tipo
        if not specific_benefits:
            if "loja" in business_type:
                specific_benefits = ["focar nas vendas", "atender melhor os clientes"]
            elif "clinica" in business_type:
                specific_benefits = ["organizar agendamentos", "ter mais tempo para pacientes"]
            else:
                specific_benefits = ["automatizar atendimento", "melhorar eficiência"]
        
        return {
            "recommended_plan": recommended_plan,
            "plan_reason": plan_reason,
            "specific_benefits": specific_benefits,
            "business_context": business_type
        }