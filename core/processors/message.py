# -*- coding: utf-8 -*-
"""
Core Processors - Message
Processamento genérico de mensagens
"""

import re
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from core.interfaces.strategy import Message


@dataclass
class ProcessedMessage:
    """Resultado do processamento de uma mensagem"""
    original_message: Message
    intent: str
    confidence: float
    extracted_entities: Dict[str, Any]
    language: str
    is_first_interaction: bool
    requires_greeting: bool
    processing_metadata: Dict[str, Any]
    
    def __post_init__(self):
        if not self.processing_metadata:
            self.processing_metadata = {}


class MessageProcessor:
    """
    Processador genérico de mensagens do sistema
    
    Responsável por análise básica de intenção, extração de entidades
    e preparação da mensagem para processamento posterior
    """
    
    def __init__(self):
        self.intent_patterns = self._initialize_intent_patterns()
        self.entity_patterns = self._initialize_entity_patterns()
    
    def process_message(
        self, 
        message: Message, 
        conversation_history: List[Dict[str, str]] = None
    ) -> ProcessedMessage:
        """
        Processa uma mensagem completa
        
        Args:
            message: Mensagem a ser processada
            conversation_history: Histórico da conversa
            
        Returns:
            ProcessedMessage: Resultado do processamento
        """
        if conversation_history is None:
            conversation_history = []
        
        # Análise de intenção
        intent, confidence = self.analyze_intent(message.text, conversation_history)
        
        # Extração de entidades
        entities = self.extract_entities(message.text)
        
        # Detecção de idioma (básica)
        language = self.detect_language(message.text)
        
        # Análise de primeira interação
        is_first_interaction = len(conversation_history) == 0
        requires_greeting = self.should_send_greeting(conversation_history)
        
        # Metadados do processamento
        metadata = {
            "processed_at": datetime.now().isoformat(),
            "message_length": len(message.text),
            "word_count": len(message.text.split()),
            "has_entities": len(entities) > 0
        }
        
        return ProcessedMessage(
            original_message=message,
            intent=intent,
            confidence=confidence,
            extracted_entities=entities,
            language=language,
            is_first_interaction=is_first_interaction,
            requires_greeting=requires_greeting,
            processing_metadata=metadata
        )
    
    def analyze_intent(self, text: str, conversation_history: List[Dict[str, str]]) -> tuple[str, float]:
        """
        Analisa a intenção da mensagem
        
        Args:
            text: Texto da mensagem
            conversation_history: Histórico da conversa
            
        Returns:
            tuple[str, float]: (intent, confidence)
        """
        text_lower = text.lower().strip()
        
        # Verifica se é realmente a primeira mensagem
        user_messages = [msg for msg in conversation_history if msg.get("role") == "user"]
        is_truly_first = len(user_messages) == 0
        
        # Análise de padrões de intenção
        for intent, patterns in self.intent_patterns.items():
            for pattern, confidence in patterns:
                if isinstance(pattern, str):
                    if pattern in text_lower:
                        # Ajusta confiança baseado no contexto
                        adjusted_confidence = self._adjust_confidence(
                            confidence, intent, is_truly_first, text_lower
                        )
                        return intent, adjusted_confidence
                else:  # regex pattern
                    if pattern.search(text_lower):
                        adjusted_confidence = self._adjust_confidence(
                            confidence, intent, is_truly_first, text_lower
                        )
                        return intent, adjusted_confidence
        
        # Intent padrão
        return "general", 0.5
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extrai entidades básicas do texto
        
        Args:
            text: Texto para análise
            
        Returns:
            Dict[str, Any]: Entidades extraídas
        """
        entities = {}
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(text)
                if matches:
                    if entity_type not in entities:
                        entities[entity_type] = []
                    entities[entity_type].extend(matches)
        
        # Remove duplicatas mantendo ordem
        for entity_type, values in entities.items():
            entities[entity_type] = list(dict.fromkeys(values))
        
        return entities
    
    def detect_language(self, text: str) -> str:
        """
        Detecção básica de idioma
        
        Args:
            text: Texto para análise
            
        Returns:
            str: Código do idioma detectado
        """
        # Detecção muito básica baseada em palavras comuns
        portuguese_indicators = [
            "olá", "oi", "bom dia", "boa tarde", "boa noite",
            "obrigado", "obrigada", "por favor", "com licença",
            "você", "voce", "como", "que", "não", "nao", "sim"
        ]
        
        english_indicators = [
            "hello", "hi", "good morning", "good afternoon", "good evening",
            "thank you", "thanks", "please", "excuse me",
            "you", "how", "what", "not", "yes", "no"
        ]
        
        text_lower = text.lower()
        
        pt_score = sum(1 for word in portuguese_indicators if word in text_lower)
        en_score = sum(1 for word in english_indicators if word in text_lower)
        
        if pt_score > en_score:
            return "pt-BR"
        elif en_score > pt_score:
            return "en-US"
        else:
            return "pt-BR"  # Default para português
    
    def should_send_greeting(self, conversation_history: List[Dict[str, str]]) -> bool:
        """
        Determina se deve enviar saudação
        
        Args:
            conversation_history: Histórico da conversa
            
        Returns:
            bool: True se deve enviar saudação
        """
        if not conversation_history:
            return True
        
        # Verifica se já se apresentou
        for msg in conversation_history:
            if msg.get("role") == "assistant":
                content = msg.get("content", "").lower()
                if any(phrase in content for phrase in ["sou", "eu sou", "assistente", "me chamo"]):
                    return False
        
        return True
    
    def _initialize_intent_patterns(self) -> Dict[str, List[tuple]]:
        """
        Inicializa padrões de intenção
        
        Returns:
            Dict[str, List[tuple]]: Padrões organizados por intenção
        """
        return {
            "greeting": [
                ("olá", 0.9),
                ("oi", 0.9),
                ("bom dia", 0.9),
                ("boa tarde", 0.9),
                ("boa noite", 0.9),
                ("hello", 0.8),
                ("hi", 0.8),
                (re.compile(r"\b(ola|oi)\b"), 0.8)
            ],
            "farewell": [
                ("tchau", 0.9),
                ("até logo", 0.9),
                ("obrigado", 0.7),
                ("obrigada", 0.7),
                ("valeu", 0.8),
                ("bye", 0.8),
                ("goodbye", 0.9)
            ],
            "help_request": [
                ("ajuda", 0.8),
                ("como", 0.6),
                ("o que", 0.6),
                ("quem", 0.6),
                ("pode me ajudar", 0.9),
                ("preciso de ajuda", 0.9),
                ("help", 0.8),
                ("how", 0.6)
            ],
            "pricing": [
                ("preço", 0.9),
                ("valor", 0.8),
                ("quanto custa", 0.9),
                ("investimento", 0.7),
                ("orçamento", 0.8),
                ("price", 0.9),
                ("cost", 0.8)
            ],
            "contact_info": [
                ("contato", 0.8),
                ("telefone", 0.8),
                ("email", 0.8),
                ("endereço", 0.8),
                ("localização", 0.7),
                ("onde", 0.6),
                ("contact", 0.8)
            ],
            "service_inquiry": [
                ("serviços", 0.8),
                ("produtos", 0.8),
                ("oferece", 0.7),
                ("faz", 0.6),
                ("trabalha", 0.6),
                ("services", 0.8),
                ("products", 0.8)
            ]
        }
    
    def _initialize_entity_patterns(self) -> Dict[str, List]:
        """
        Inicializa padrões de extração de entidades
        
        Returns:
            Dict[str, List]: Padrões organizados por tipo de entidade
        """
        return {
            "name": [
                re.compile(r"(?:me chamo|meu nome é|sou o|sou a|eu sou)\s+([A-Za-zÀ-ÿ\s]{2,30})", re.IGNORECASE),
                re.compile(r"(?:^|\s)([A-Z][a-zÀ-ÿ]+(?:\s+[A-Z][a-zÀ-ÿ]+)*),?\s*(?:aqui|falando|é meu nome)", re.IGNORECASE)
            ],
            "email": [
                re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
            ],
            "phone": [
                re.compile(r'\(?(?:\+55\s?)?(?:\d{2})\)?\s?\d{4,5}-?\d{4}'),
                re.compile(r'(?:\+55\s?)?(?:\d{2})\s?\d{4,5}\s?\d{4}')
            ],
            "company": [
                re.compile(r"(?:trabalho na|trabalho no|empresa|companhia)\s+([A-Za-zÀ-ÿ\s&]{2,30})", re.IGNORECASE),
                re.compile(r"(?:sou da|venho da)\s+([A-Za-zÀ-ÿ\s&]{2,30})", re.IGNORECASE)
            ],
            "job_title": [
                re.compile(r"(?:sou|trabalho como|atuo como|profissão|minha profissão é)\s+([A-Za-zÀ-ÿ\s]{2,30})", re.IGNORECASE)
            ],
            "number": [
                re.compile(r'\b\d+\b')
            ],
            "currency": [
                re.compile(r'R\$\s*[\d.,]+'),
                re.compile(r'reais?'),
                re.compile(r'\$\s*[\d.,]+')
            ]
        }
    
    def _adjust_confidence(
        self, 
        base_confidence: float, 
        intent: str, 
        is_first_interaction: bool, 
        text: str
    ) -> float:
        """
        Ajusta confiança baseado no contexto
        
        Args:
            base_confidence: Confiança base do padrão
            intent: Intenção detectada
            is_first_interaction: Se é primeira interação
            text: Texto da mensagem
            
        Returns:
            float: Confiança ajustada
        """
        confidence = base_confidence
        
        # Ajuste para primeira interação
        if intent == "greeting" and is_first_interaction:
            confidence = min(1.0, confidence + 0.1)
        elif intent == "greeting" and not is_first_interaction:
            confidence = max(0.1, confidence - 0.3)
        
        # Ajuste por comprimento da mensagem
        if len(text) < 5:  # Mensagens muito curtas
            confidence = max(0.1, confidence - 0.2)
        elif len(text) > 100:  # Mensagens longas
            confidence = max(0.1, confidence - 0.1)
        
        # Ajuste por contexto da mensagem
        if intent == "pricing" and any(word in text for word in ["quanto", "valor", "preço"]):
            confidence = min(1.0, confidence + 0.1)
        
        return confidence
    
    def get_message_statistics(self, text: str) -> Dict[str, Any]:
        """
        Calcula estatísticas da mensagem
        
        Args:
            text: Texto da mensagem
            
        Returns:
            Dict[str, Any]: Estatísticas da mensagem
        """
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        
        return {
            "character_count": len(text),
            "word_count": len(words),
            "sentence_count": len([s for s in sentences if s.strip()]),
            "avg_word_length": sum(len(word) for word in words) / len(words) if words else 0,
            "has_punctuation": any(char in text for char in ".!?,:;"),
            "has_numbers": any(char.isdigit() for char in text),
            "has_uppercase": any(char.isupper() for char in text),
            "language_indicators": {
                "portuguese_words": sum(1 for word in ["você", "não", "sim", "como", "que"] if word in text.lower()),
                "english_words": sum(1 for word in ["you", "not", "yes", "how", "what"] if word in text.lower())
            }
        }
                