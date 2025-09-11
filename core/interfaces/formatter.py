# -*- coding: utf-8 -*-
"""
Core Interfaces - Formatter (CORRIGIDO)
Interface para formatadores de resposta que os tenants podem implementar
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class ResponseFormatter(ABC):
    """
    Interface base para formatadores de resposta
    
    Os tenants podem implementar esta interface para definir
    como as respostas devem ser formatadas (estruturada, simples, etc.)
    """
    
    def __init__(self, tenant_id: str, config: Dict[str, Any] = None):
        self.tenant_id = tenant_id
        self.config = config or {}
        self.priority = self.config.get("priority", 100)
    
    @abstractmethod
    def should_format(self, response_text: str, session_key: str) -> bool:
        """
        Determina se este formatador deve ser aplicado à resposta
        
        Args:
            response_text: Texto da resposta gerada
            session_key: Chave da sessão
            
        Returns:
            bool: True se o formatador deve ser aplicado
        """
        pass
    
    @abstractmethod
    def format_response(self, response_text: str, session_key: str) -> List[str]:
        """
        Formata a resposta em múltiplas mensagens
        
        Args:
            response_text: Texto da resposta original
            session_key: Chave da sessão
            
        Returns:
            List[str]: Lista de mensagens formatadas
        """
        pass
    
    @abstractmethod
    def format(self, text: str, config: Any, context: Any) -> Any:
        """
        Método de formatação principal usado pelos processadores
        
        Args:
            text: Texto a ser formatado
            config: Configuração de formatação
            context: Contexto da conversa
            
        Returns:
            Any: Resultado formatado
        """
        pass
    
    def get_formatter_name(self) -> str:
        """Retorna o nome do formatador"""
        return self.__class__.__name__
    
    def get_priority(self) -> int:
        """Retorna a prioridade de execução do formatador"""
        return self.priority


class StructuredResponseFormatter(ResponseFormatter):
    """
    Formatador base para respostas estruturadas (listas, planos, etc.)
    """
    
    def extract_structured_items(self, response_text: str) -> Dict[str, Any]:
        """
        Extrai itens estruturados do texto de resposta
        
        Args:
            response_text: Texto da resposta
            
        Returns:
            Dict contendo intro_text, items, outro_text
        """
        import re
        
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
                
            # Detecta item numerado estruturado
            item_match = re.match(r'^(\d+)\.\s*\*\*([^*]+)\*\*[:\-]\s*(.*)', line)
            
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
                
            else:
                # Linha de continuação ou outro conteúdo
                if current_section == "intro" and not items:
                    intro_lines.append(line)
                elif current_section == "items" and current_item:
                    if line and not re.match(r'^\d+\.', line):
                        if current_item.get("details"):
                            current_item["details"] += " " + line
                        else:
                            current_item["details"] = line
                elif items:
                    current_section = "outro"
                    outro_lines.append(line)
                else:
                    intro_lines.append(line)
        
        # Adiciona último item se existir
        if current_item:
            items.append(current_item)
        
        return {
            "intro_text": " ".join(intro_lines) if intro_lines else "",
            "items": items,
            "outro_text": " ".join(outro_lines) if outro_lines else ""
        }


class MicroResponseFormatter(ResponseFormatter):
    """
    Formatador base para micro-respostas (quebra inteligente de texto)
    """
    
    def break_text_intelligently(
        self, 
        text: str, 
        min_chars: int = 120, 
        max_chars: int = 200
    ) -> List[str]:
        """
        Quebra texto em micro-respostas inteligentes
        
        Args:
            text: Texto para quebrar
            min_chars: Mínimo de caracteres por mensagem
            max_chars: Máximo de caracteres por mensagem
            
        Returns:
            List[str]: Lista de mensagens quebradas
        """
        import re
        
        if not text or not text.strip():
            return [""]
        
        text = text.strip()
        
        if len(text) <= max_chars:
            return [text]
        
        # Quebra por sentenças completas
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        if len(sentences) > 1:
            responses = []
            current = ""
            
            for sentence in sentences:
                if len(sentence) > max_chars:
                    if current:
                        responses.append(current.strip())
                        current = ""
                    
                    sub_responses = self._break_by_natural_pauses(sentence, max_chars)
                    responses.extend(sub_responses)
                    continue
                
                test_text = (current + " " + sentence).strip() if current else sentence
                
                if len(test_text) <= max_chars:
                    current = test_text
                    
                    if len(current) >= min_chars:
                        responses.append(current)
                        current = ""
                else:
                    if current:
                        responses.append(current)
                    current = sentence
            
            if current:
                responses.append(current)
            
            if responses:
                return responses
        
        return self._break_by_natural_pauses(text, max_chars)
    
    def _break_by_natural_pauses(self, text: str, max_chars: int) -> List[str]:
        """Quebra texto por pausas naturais"""
        import re
        
        if len(text) <= max_chars:
            return [text]
        
        # Tenta quebrar por pausas naturais
        pause_points = []
        for match in re.finditer(r'[,:;]\s+', text):
            pause_points.append(match.end())
        
        if pause_points:
            best_break = None
            for point in pause_points:
                if point <= max_chars:
                    best_break = point
            
            if best_break:
                part1 = text[:best_break].strip()
                part2 = text[best_break:].strip()
                
                result = []
                result.extend(self._break_by_natural_pauses(part1, max_chars))
                result.extend(self._break_by_natural_pauses(part2, max_chars))
                return result
        
        # Quebra por palavras como último recurso
        return self._break_by_words(text, max_chars)
    
    def _break_by_words(self, text: str, max_chars: int) -> List[str]:
        """Quebra por palavras completas (último recurso)"""
        words = text.split()
        if len(words) <= 1:
            return [text]
        
        responses = []
        current = ""
        
        for word in words:
            test_text = (current + " " + word).strip() if current else word
            
            if len(test_text) <= max_chars:
                current = test_text
            else:
                if current:
                    responses.append(current.strip())
                    current = word
                else:
                    responses.append(word)
        
        if current:
            responses.append(current.strip())
        
        return responses if responses else [text]