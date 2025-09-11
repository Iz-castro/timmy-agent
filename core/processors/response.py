# -*- coding: utf-8 -*-
"""
Response Processor - Geração e formatação de respostas (CORRIGIDO)
Agnóstico a personas - toda configuração vem dos tenants
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import re

from core.interfaces.formatter import ResponseFormatter
from core.extensions.registry import component_registry


@dataclass
class ResponseConfig:
    """Configuração de resposta extraída do tenant"""
    min_chars: int = 80
    max_chars: int = 200
    use_emojis: bool = False
    tone: str = "profissional"
    style: str = "direto"
    formality: str = "moderada"
    structured_threshold: int = 150  # Tamanho mínimo para estruturação


@dataclass
class ResponseContext:
    """Contexto para geração de resposta"""
    user_message: str
    conversation_history: List[Dict[str, str]]
    extracted_info: Dict[str, Any]
    intent: str
    tenant_id: str
    session_key: str


@dataclass
class FormattedResponse:
    """Resposta formatada pronta para envio"""
    messages: List[str]
    total_parts: int
    formatting_applied: str  # "micro", "structured", "single"
    metadata: Dict[str, Any]


class ResponseProcessor:
    """
    Processador principal de respostas
    
    Responsabilidades:
    - Detectar tipo de conteúdo (estruturado vs simples)
    - Aplicar formatação adequada baseada na configuração do tenant
    - Garantir limites de caracteres configuráveis
    - Suportar formatadores customizados via extensões
    """
    
    def __init__(self):
        self.registry = component_registry
        self._formatters: Dict[str, ResponseFormatter] = {}
        self._load_formatters()
    
    def _load_formatters(self):
        """Carrega formatadores disponíveis do registry"""
        try:
            # Busca formatadores registrados no component_registry
            formatters = self.registry.get_components_by_type(
                self.registry.ComponentType.FORMATTER if hasattr(self.registry, 'ComponentType') else 'formatter'
            )
            
            for formatter_info in formatters:
                # Aqui você carregaria a classe real do formatador
                # Por enquanto, mantemos um dicionário vazio
                pass
                
        except Exception as e:
            print(f"[WARNING] Erro ao carregar formatadores do registry: {e}")
            # Continua com formatadores vazios
    
    def process_response(
        self, 
        raw_response: str,
        context: ResponseContext,
        config: ResponseConfig
    ) -> FormattedResponse:
        """
        Processa resposta bruta aplicando formatação apropriada
        
        Args:
            raw_response: Resposta gerada pelo LLM
            context: Contexto da conversa
            config: Configuração de formatação do tenant
            
        Returns:
            FormattedResponse com mensagens formatadas
        """
        if not raw_response.strip():
            return FormattedResponse(
                messages=[""],
                total_parts=0,
                formatting_applied="empty",
                metadata={}
            )
        
        # 1. Detecta tipo de conteúdo
        content_analysis = self._analyze_content_structure(raw_response)
        
        # 2. Escolhe estratégia de formatação
        formatting_strategy = self._choose_formatting_strategy(
            content_analysis, config, len(raw_response)
        )
        
        # 3. Aplica formatação
        if formatting_strategy == "structured":
            return self._apply_structured_formatting(raw_response, config, context)
        elif formatting_strategy == "micro":
            return self._apply_micro_formatting(raw_response, config, context)
        else:
            return self._apply_single_formatting(raw_response, config, context)
    
    def _analyze_content_structure(self, text: str) -> Dict[str, Any]:
        """
        Analisa estrutura do conteúdo para determinar formatação
        
        Returns:
            Dict com análise da estrutura:
            - has_numbered_list: bool
            - has_bullet_points: bool  
            - has_titles: bool
            - item_count: int
            - complexity_score: float
        """
        analysis = {
            "has_numbered_list": False,
            "has_bullet_points": False,
            "has_titles": False,
            "item_count": 0,
            "complexity_score": 0.0
        }
        
        # Detecta listas numeradas
        numbered_items = re.findall(r'^\d+\.\s+', text, re.MULTILINE)
        if numbered_items:
            analysis["has_numbered_list"] = True
            analysis["item_count"] = len(numbered_items)
        
        # Detecta bullet points
        bullet_items = re.findall(r'^[\-\*\•]\s+', text, re.MULTILINE)
        if bullet_items:
            analysis["has_bullet_points"] = True
            analysis["item_count"] = max(analysis["item_count"], len(bullet_items))
        
        # Detecta títulos com **
        title_items = re.findall(r'\*\*[^*]+\*\*:', text)
        if title_items:
            analysis["has_titles"] = True
            analysis["item_count"] = max(analysis["item_count"], len(title_items))
        
        # Calcula complexidade
        factors = []
        if analysis["item_count"] > 0:
            factors.append(analysis["item_count"] * 0.3)
        if analysis["has_titles"]:
            factors.append(0.4)
        if len(text.split('\n')) > 3:
            factors.append(0.3)
        
        analysis["complexity_score"] = sum(factors)
        
        return analysis
    
    def _choose_formatting_strategy(
        self, 
        content_analysis: Dict[str, Any], 
        config: ResponseConfig,
        text_length: int
    ) -> str:
        """
        Escolhe estratégia de formatação baseada na análise de conteúdo
        
        Returns:
            "structured", "micro", ou "single"
        """
        # Força estruturada se há múltiplos itens organizados
        if (content_analysis["item_count"] >= 3 or 
            content_analysis["complexity_score"] > 0.7):
            return "structured"
        
        # Usa micro-responses se texto é longo mas não estruturado
        if text_length > config.max_chars and content_analysis["complexity_score"] < 0.5:
            return "micro"
        
        # Mantém como mensagem única se é curto e simples
        if text_length <= config.max_chars:
            return "single"
        
        return "micro"
    
    def _apply_structured_formatting(
        self, 
        text: str, 
        config: ResponseConfig,
        context: ResponseContext
    ) -> FormattedResponse:
        """
        Aplica formatação estruturada (intro + itens + fechamento)
        """
        # Usa formatador específico se disponível
        formatter_name = f"structured_{context.tenant_id}"
        if formatter_name in self._formatters:
            try:
                return self._formatters[formatter_name].format(text, config, context)
            except Exception as e:
                print(f"[WARNING] Erro no formatador específico {formatter_name}: {e}")
        
        # Formatação estruturada genérica
        intro, items, outro = self._parse_structured_content(text)
        
        messages = []
        metadata = {
            "intro_length": len(intro) if intro else 0,
            "items_count": len(items),
            "outro_length": len(outro) if outro else 0
        }
        
        # Introdução (pode ser quebrada se muito longa)
        if intro:
            intro_parts = self._break_text_intelligently(intro, config)
            messages.extend(intro_parts)
        
        # Cada item = 1 mensagem completa (NUNCA quebrada)
        for item in items:
            formatted_item = self._format_single_item(item, config)
            messages.append(formatted_item)
        
        # Fechamento (pode ser quebrado se muito longo)
        if outro:
            outro_parts = self._break_text_intelligently(outro, config)
            messages.extend(outro_parts)
        
        return FormattedResponse(
            messages=messages,
            total_parts=len(messages),
            formatting_applied="structured",
            metadata=metadata
        )
    
    def _apply_micro_formatting(
        self, 
        text: str, 
        config: ResponseConfig,
        context: ResponseContext
    ) -> FormattedResponse:
        """
        Aplica micro-responses inteligentes
        """
        # Usa formatador específico se disponível
        formatter_name = f"micro_{context.tenant_id}"
        if formatter_name in self._formatters:
            try:
                return self._formatters[formatter_name].format(text, config, context)
            except Exception as e:
                print(f"[WARNING] Erro no formatador específico {formatter_name}: {e}")
        
        # Micro-formatting genérico
        messages = self._break_text_intelligently(text, config)
        
        return FormattedResponse(
            messages=messages,
            total_parts=len(messages),
            formatting_applied="micro",
            metadata={"original_length": len(text)}
        )
    
    def _apply_single_formatting(
        self, 
        text: str, 
        config: ResponseConfig,
        context: ResponseContext
    ) -> FormattedResponse:
        """
        Mantém como mensagem única
        """
        # Aplica apenas configurações básicas (emojis, etc)
        formatted_text = self._apply_basic_formatting(text, config)
        
        return FormattedResponse(
            messages=[formatted_text],
            total_parts=1,
            formatting_applied="single",
            metadata={"length": len(formatted_text)}
        )
    
    def _parse_structured_content(self, text: str) -> Tuple[str, List[Dict], str]:
        """
        Parseia conteúdo estruturado em introdução, itens e fechamento
        
        Returns:
            (intro_text, items_list, outro_text)
        """
        lines = text.strip().split('\n')
        intro_lines = []
        items = []
        outro_lines = []
        
        current_section = "intro"
        current_item = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detecta início de item
            numbered_match = re.match(r'^(\d+)\.\s*\*\*([^*]+)\*\*:\s*(.*)', line)
            simple_numbered_match = re.match(r'^(\d+)\.\s*([^:]+):\s*(.*)', line)
            title_match = re.match(r'^\*\*([^*]+)\*\*:\s*(.*)', line)
            bullet_match = re.match(r'^[\-\*\•]\s*\*\*([^*]+)\*\*:\s*(.*)', line)
            
            if numbered_match:
                if current_item:
                    items.append(current_item)
                current_section = "items"
                current_item = {
                    "number": numbered_match.group(1),
                    "title": numbered_match.group(2).strip(),
                    "details": numbered_match.group(3).strip(),
                    "type": "numbered_title"
                }
            elif simple_numbered_match:
                if current_item:
                    items.append(current_item)
                current_section = "items"
                current_item = {
                    "number": simple_numbered_match.group(1),
                    "title": simple_numbered_match.group(2).strip(),
                    "details": simple_numbered_match.group(3).strip(),
                    "type": "numbered_simple"
                }
            elif title_match:
                if current_item:
                    items.append(current_item)
                current_section = "items"
                current_item = {
                    "title": title_match.group(1).strip(),
                    "details": title_match.group(2).strip(),
                    "type": "title_only"
                }
            elif bullet_match:
                if current_item:
                    items.append(current_item)
                current_section = "items"
                current_item = {
                    "title": bullet_match.group(1).strip(),
                    "details": bullet_match.group(2).strip(),
                    "type": "bullet_title"
                }
            else:
                # Linha de continuação
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
        
        # Adiciona último item
        if current_item:
            items.append(current_item)
        
        intro_text = " ".join(intro_lines).strip()
        outro_text = " ".join(outro_lines).strip()
        
        return intro_text, items, outro_text
    
    def _format_single_item(self, item: Dict, config: ResponseConfig) -> str:
        """
        Formata um item individual baseado no seu tipo
        """
        item_type = item.get("type", "simple")
        
        if item_type == "numbered_title":
            return f"{item['number']}. **{item['title']}**: {item['details']}"
        elif item_type == "numbered_simple":
            return f"{item['number']}. {item['title']}: {item['details']}"
        elif item_type == "title_only":
            return f"**{item['title']}**: {item['details']}"
        elif item_type == "bullet_title":
            return f"• **{item['title']}**: {item['details']}"
        else:
            return item.get('details', str(item))
    
    def _break_text_intelligently(self, text: str, config: ResponseConfig) -> List[str]:
        """
        Quebra texto de forma inteligente respeitando limites configuráveis
        
        Prioridades de quebra:
        1. Sentenças completas
        2. Pausas naturais
        3. Conjunções
        4. Palavras completas
        """
        if len(text) <= config.max_chars:
            return [text]
        
        # Tenta quebrar por sentenças
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) > 1:
            return self._group_sentences(sentences, config)
        
        # Quebra por pausas naturais
        return self._break_by_natural_pauses(text, config)
    
    def _group_sentences(self, sentences: List[str], config: ResponseConfig) -> List[str]:
        """
        Agrupa sentenças respeitando limites de caracteres
        """
        groups = []
        current_group = ""
        
        for sentence in sentences:
            # Se sentença individual é muito grande, quebra ela
            if len(sentence) > config.max_chars:
                if current_group:
                    groups.append(current_group.strip())
                    current_group = ""
                
                sub_parts = self._break_by_natural_pauses(sentence, config)
                groups.extend(sub_parts)
                continue
            
            # Testa se pode adicionar ao grupo atual
            test_group = (current_group + " " + sentence).strip() if current_group else sentence
            
            if len(test_group) <= config.max_chars:
                current_group = test_group
            else:
                # Finaliza grupo atual e inicia novo
                if current_group:
                    groups.append(current_group.strip())
                current_group = sentence
        
        # Adiciona último grupo
        if current_group:
            groups.append(current_group.strip())
        
        return groups if groups else [text]
    
    def _break_by_natural_pauses(self, text: str, config: ResponseConfig) -> List[str]:
        """
        Quebra por pausas naturais (vírgulas, dois pontos, etc.)
        """
        if len(text) <= config.max_chars:
            return [text]
        
        # Procura pausas naturais
        pause_points = []
        for match in re.finditer(r'[,:;]\s+', text):
            pause_points.append(match.end())
        
        if pause_points:
            # Encontra melhor ponto de quebra
            best_break = None
            for point in pause_points:
                if config.min_chars <= point <= config.max_chars:
                    best_break = point
            
            if best_break:
                part1 = text[:best_break].strip()
                part2 = text[best_break:].strip()
                
                result = []
                result.extend(self._break_by_natural_pauses(part1, config))
                result.extend(self._break_by_natural_pauses(part2, config))
                return result
        
        # Quebra por palavras como último recurso
        return self._break_by_words(text, config)
    
    def _break_by_words(self, text: str, config: ResponseConfig) -> List[str]:
        """
        Quebra por palavras completas (último recurso)
        """
        words = text.split()
        if len(words) <= 1:
            return [text]  # Palavra única muito longa
        
        groups = []
        current_group = ""
        
        for word in words:
            test_group = (current_group + " " + word).strip() if current_group else word
            
            if len(test_group) <= config.max_chars:
                current_group = test_group
            else:
                if current_group:
                    groups.append(current_group.strip())
                    current_group = word
                else:
                    # Palavra individual muito longa
                    groups.append(word)
        
        if current_group:
            groups.append(current_group.strip())
        
        return groups if groups else [text]
    
    def _apply_basic_formatting(self, text: str, config: ResponseConfig) -> str:
        """
        Aplica formatação básica baseada na configuração
        """
        formatted = text
        
        # Remove emojis se configurado
        if not config.use_emojis:
            # Regex para remover emojis
            emoji_pattern = re.compile(
                "["
                "\U0001F600-\U0001F64F"  # emoticons
                "\U0001F300-\U0001F5FF"  # symbols & pictographs
                "\U0001F680-\U0001F6FF"  # transport & map symbols
                "\U0001F1E0-\U0001F1FF"  # flags (iOS)
                "\U00002700-\U000027BF"  # dingbats
                "\U0001f926-\U0001f937"
                "\U00010000-\U0010ffff"
                "\u2640-\u2642"
                "\u2600-\u2B55"
                "\u200d"
                "\u23cf"
                "\u23e9"
                "\u231a"
                "\ufe0f"
                "\u3030"
                "]+", 
                flags=re.UNICODE
            )
            formatted = emoji_pattern.sub('', formatted)
        
        return formatted.strip()
    
    def register_custom_formatter(self, name: str, formatter: ResponseFormatter):
        """
        Registra formatador customizado
        """
        self._formatters[name] = formatter
    
    def get_available_formatters(self) -> List[str]:
        """
        Retorna lista de formatadores disponíveis
        """
        return list(self._formatters.keys())