# -*- coding: utf-8 -*-
"""
Core Processors - Context
Análise e gerenciamento de contexto conversacional
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from core.interfaces.strategy import ConversationContext


@dataclass
class ContextAnalysis:
    """Resultado da análise de contexto"""
    conversation_phase: str
    user_engagement_level: float
    topic_continuity: bool
    context_switches: List[str]
    emotional_tone: str
    information_completeness: float
    next_action_suggestions: List[str]
    context_metadata: Dict[str, Any]


class ContextProcessor:
    """
    Processador de contexto conversacional
    
    Analisa o contexto da conversa para determinar fase atual,
    engajamento do usuário, e sugerir próximas ações
    """
    
    def __init__(self):
        self.conversation_phases = {
            "initialization": {
                "indicators": ["primeira", "início", "começar", "iniciar"],
                "max_messages": 3
            },
            "discovery": {
                "indicators": ["descobrir", "entender", "saber", "contar"],
                "questions": ["o que", "como", "onde", "quando", "por que"]
            },
            "engagement": {
                "indicators": ["interessante", "gostaria", "preciso", "quero"],
                "min_exchanges": 3
            },
            "decision": {
                "indicators": ["decidir", "escolher", "quero", "vou", "fechado"],
                "action_words": ["comprar", "contratar", "agendar"]
            },
            "closure": {
                "indicators": ["obrigado", "tchau", "até", "finalizar"],
                "completion_signals": ["resolvido", "esclarecido", "suficiente"]
            }
        }
        
        self.emotional_indicators = {
            "positive": ["ótimo", "excelente", "perfeito", "gostei", "legal"],
            "neutral": ["ok", "entendi", "sim", "não", "talvez"],
            "negative": ["problema", "difícil", "complicado", "ruim"],
            "frustrated": ["não funciona", "não entendo", "confuso"],
            "excited": ["wow", "incrível", "fantástico", "demais"]
        }
    
    def analyze_context(
        self, 
        context: ConversationContext,
        current_message: str = None
    ) -> ContextAnalysis:
        """
        Analisa o contexto completo da conversa
        
        Args:
            context: Contexto da conversa
            current_message: Mensagem atual (opcional)
            
        Returns:
            ContextAnalysis: Análise completa do contexto
        """
        # Análise da fase da conversa
        phase = self._determine_conversation_phase(context, current_message)
        
        # Análise do engajamento
        engagement = self._calculate_engagement_level(context)
        
        # Análise de continuidade do tópico
        continuity = self._analyze_topic_continuity(context)
        
        # Detecção de mudanças de contexto
        switches = self._detect_context_switches(context)
        
        # Análise do tom emocional
        emotional_tone = self._analyze_emotional_tone(context, current_message)
        
        # Completude da informação
        completeness = self._calculate_information_completeness(context)
        
        # Sugestões de próximas ações
        suggestions = self._generate_action_suggestions(phase, engagement, context)
        
        # Metadados
        metadata = self._generate_context_metadata(context)
        
        return ContextAnalysis(
            conversation_phase=phase,
            user_engagement_level=engagement,
            topic_continuity=continuity,
            context_switches=switches,
            emotional_tone=emotional_tone,
            information_completeness=completeness,
            next_action_suggestions=suggestions,
            context_metadata=metadata
        )
    
    def _determine_conversation_phase(
        self, 
        context: ConversationContext, 
        current_message: str = None
    ) -> str:
        """
        Determina a fase atual da conversa
        
        Args:
            context: Contexto da conversa
            current_message: Mensagem atual
            
        Returns:
            str: Fase da conversa
        """
        message_count = len(context.conversation_history)
        
        # Análise por número de mensagens
        if message_count <= 3:
            return "initialization"
        
        # Análise por conteúdo das mensagens
        recent_messages = context.conversation_history[-5:]  # Últimas 5 mensagens
        if current_message:
            recent_content = " ".join([msg.get("content", "") for msg in recent_messages] + [current_message])
        else:
            recent_content = " ".join([msg.get("content", "") for msg in recent_messages])
        
        recent_content_lower = recent_content.lower()
        
        # Verifica indicadores de cada fase
        for phase, config in self.conversation_phases.items():
            if "indicators" in config:
                if any(indicator in recent_content_lower for indicator in config["indicators"]):
                    return phase
            
            if phase == "discovery" and "questions" in config:
                if any(question in recent_content_lower for question in config["questions"]):
                    return phase
            
            if phase == "engagement" and "min_exchanges" in config:
                user_messages = [msg for msg in recent_messages if msg.get("role") == "user"]
                if len(user_messages) >= config["min_exchanges"]:
                    return phase
        
        # Fase padrão baseada na quantidade de mensagens
        if message_count <= 10:
            return "discovery"
        elif message_count <= 20:
            return "engagement"
        else:
            return "decision"
    
    def _calculate_engagement_level(self, context: ConversationContext) -> float:
        """
        Calcula nível de engajamento do usuário
        
        Args:
            context: Contexto da conversa
            
        Returns:
            float: Nível de engajamento (0.0 a 1.0)
        """
        user_messages = [msg for msg in context.conversation_history if msg.get("role") == "user"]
        
        if not user_messages:
            return 0.0
        
        engagement_score = 0.0
        factors = 0
        
        # Fator 1: Comprimento médio das mensagens
        avg_length = sum(len(msg.get("content", "")) for msg in user_messages) / len(user_messages)
        if avg_length > 50:
            engagement_score += 0.3
        elif avg_length > 20:
            engagement_score += 0.2
        else:
            engagement_score += 0.1
        factors += 1
        
        # Fator 2: Frequência de perguntas
        question_count = sum(1 for msg in user_messages if "?" in msg.get("content", ""))
        question_ratio = question_count / len(user_messages)
        engagement_score += min(0.3, question_ratio * 0.6)
        factors += 1
        
        # Fator 3: Indicadores de interesse
        interest_indicators = ["interessante", "legal", "gostaria", "quero", "preciso"]
        recent_messages = user_messages[-3:]  # Últimas 3 mensagens do usuário
        recent_content = " ".join([msg.get("content", "") for msg in recent_messages]).lower()
        
        interest_score = sum(0.1 for indicator in interest_indicators if indicator in recent_content)
        engagement_score += min(0.4, interest_score)
        factors += 1
        
        return min(1.0, engagement_score / factors)
    
    def _analyze_topic_continuity(self, context: ConversationContext) -> bool:
        """
        Analisa se há continuidade no tópico da conversa
        
        Args:
            context: Contexto da conversa
            
        Returns:
            bool: True se há continuidade de tópico
        """
        if len(context.conversation_history) < 4:
            return True  # Poucas mensagens, assumir continuidade
        
        # Analisa palavras-chave nas últimas mensagens
        recent_messages = context.conversation_history[-6:]
        message_keywords = []
        
        for msg in recent_messages:
            content = msg.get("content", "").lower()
            # Extrai palavras relevantes (substantivos e verbos importantes)
            keywords = re.findall(r'\b[a-záêçõ]{4,}\b', content)
            message_keywords.append(set(keywords))
        
        # Calcula sobreposição entre mensagens adjacentes
        overlaps = []
        for i in range(1, len(message_keywords)):
            if message_keywords[i-1] and message_keywords[i]:
                overlap = len(message_keywords[i-1] & message_keywords[i])
                total = len(message_keywords[i-1] | message_keywords[i])
                overlaps.append(overlap / total if total > 0 else 0)
        
        # Se a maioria das transições tem sobreposição > 0.2, há continuidade
        if overlaps:
            avg_overlap = sum(overlaps) / len(overlaps)
            return avg_overlap > 0.2
        
        return True
    
    def _detect_context_switches(self, context: ConversationContext) -> List[str]:
        """
        Detecta mudanças abruptas de contexto
        
        Args:
            context: Contexto da conversa
            
        Returns:
            List[str]: Lista de mudanças detectadas
        """
        switches = []
        
        if len(context.conversation_history) < 3:
            return switches
        
        # Palavras que indicam mudança de tópico
        switch_indicators = [
            "aliás", "por falar nisso", "mudando de assunto",
            "outra coisa", "já agora", "aproveitando"
        ]
        
        user_messages = [msg for msg in context.conversation_history if msg.get("role") == "user"]
        
        for i, msg in enumerate(user_messages):
            content = msg.get("content", "").lower()
            
            for indicator in switch_indicators:
                if indicator in content:
                    switches.append(f"Mudança de tópico na mensagem {i+1}: {indicator}")
        
        return switches
    
    def _analyze_emotional_tone(
        self, 
        context: ConversationContext, 
        current_message: str = None
    ) -> str:
        """
        Analisa o tom emocional da conversa
        
        Args:
            context: Contexto da conversa
            current_message: Mensagem atual
            
        Returns:
            str: Tom emocional detectado
        """
        # Considera últimas mensagens do usuário + mensagem atual
        user_messages = [msg for msg in context.conversation_history[-5:] if msg.get("role") == "user"]
        
        if current_message:
            content_to_analyze = " ".join([msg.get("content", "") for msg in user_messages] + [current_message])
        else:
            content_to_analyze = " ".join([msg.get("content", "") for msg in user_messages])
        
        content_lower = content_to_analyze.lower()
        
        # Conta indicadores emocionais
        emotion_scores = {}
        for emotion, indicators in self.emotional_indicators.items():
            score = sum(1 for indicator in indicators if indicator in content_lower)
            emotion_scores[emotion] = score
        
        # Retorna emoção com maior score
        if emotion_scores:
            max_emotion = max(emotion_scores, key=emotion_scores.get)
            if emotion_scores[max_emotion] > 0:
                return max_emotion
        
        return "neutral"
    
    def _calculate_information_completeness(self, context: ConversationContext) -> float:
        """
        Calcula quão completa está a informação coletada
        
        Args:
            context: Contexto da conversa
            
        Returns:
            float: Completude da informação (0.0 a 1.0)
        """
        # Informações básicas que podem ser coletadas
        expected_info = [
            "name", "email", "phone", "company", "job_title",
            "business_type", "needs", "preferences"
        ]
        
        collected_count = 0
        for info_type in expected_info:
            if info_type in context.user_state and context.user_state[info_type]:
                collected_count += 1
        
        return collected_count / len(expected_info)
    
    def _generate_action_suggestions(
        self, 
        phase: str, 
        engagement: float, 
        context: ConversationContext
    ) -> List[str]:
        """
        Gera sugestões de próximas ações
        
        Args:
            phase: Fase atual da conversa
            engagement: Nível de engajamento
            context: Contexto da conversa
            
        Returns:
            List[str]: Sugestões de ações
        """
        suggestions = []
        
        # Sugestões baseadas na fase
        if phase == "initialization":
            suggestions.append("Apresentar-se se ainda não foi feito")
            suggestions.append("Fazer pergunta aberta para entender necessidades")
        
        elif phase == "discovery":
            if engagement > 0.7:
                suggestions.append("Fazer perguntas mais específicas")
                suggestions.append("Apresentar soluções relevantes")
            else:
                suggestions.append("Aumentar engajamento com exemplos")
                suggestions.append("Fazer perguntas mais simples")
        
        elif phase == "engagement":
            suggestions.append("Apresentar benefícios específicos")
            suggestions.append("Usar informações coletadas para personalizar")
        
        elif phase == "decision":
            suggestions.append("Facilitar tomada de decisão")
            suggestions.append("Oferecer próximos passos claros")
        
        elif phase == "closure":
            suggestions.append("Confirmar satisfação")
            suggestions.append("Oferecer suporte futuro")
        
        # Sugestões baseadas no engajamento
        if engagement < 0.3:
            suggestions.append("Reengajar usuário com pergunta interessante")
        elif engagement > 0.8:
            suggestions.append("Aproveitar alto engajamento para avançar")
        
        return suggestions
    
    def _generate_context_metadata(self, context: ConversationContext) -> Dict[str, Any]:
        """
        Gera metadados do contexto
        
        Args:
            context: Contexto da conversa
            
        Returns:
            Dict[str, Any]: Metadados do contexto
        """
        user_messages = [msg for msg in context.conversation_history if msg.get("role") == "user"]
        assistant_messages = [msg for msg in context.conversation_history if msg.get("role") == "assistant"]
        
        return {
            "total_messages": len(context.conversation_history),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "conversation_length_chars": sum(len(msg.get("content", "")) for msg in context.conversation_history),
            "avg_user_message_length": (
                sum(len(msg.get("content", "")) for msg in user_messages) / len(user_messages)
                if user_messages else 0
            ),
            "collected_info_count": len([k for k, v in context.user_state.items() if v]),
            "session_duration_minutes": None,  # Poderia ser calculado se houvesse timestamps
            "context_analysis_timestamp": datetime.now().isoformat()
        }