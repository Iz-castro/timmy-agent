# core/formatter.py
"""
Sistema de formatação de respostas em múltiplas mensagens curtas
✅ CORRIGIDO: WhatsApp nativo + proteção completa contra markdown
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class FormatterConfig:
    """Configuração de formatação por tenant"""
    max_chars: int = 200
    use_emojis: bool = True
    greeting_style: str = "friendly"  # formal, friendly, casual
    list_style: str = "numbered"  # numbered, bullets, plain
    separator_style: str = "natural"  # natural, structured
    whatsapp_formatting: bool = True  # ✅ Usa formatação WhatsApp
    clean_text_mode: bool = False     # ✅ Se True, remove toda formatação
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'FormatterConfig':
        return cls(**{k: v for k, v in config.items() if k in cls.__annotations__})


class MessageFormatter:
    """Formata respostas longas em múltiplas mensagens curtas"""
    
    def __init__(self, config: FormatterConfig = None):
        self.config = config or FormatterConfig()
    
    def format_response(self, response: str, context: Dict[str, Any] = None) -> List[str]:
        """
        Formata uma resposta longa em múltiplas mensagens curtas
        """
        # Proteção contra response vazio
        if not response or not response.strip():
            fallback = "Desculpe, não consegui gerar uma resposta. Pode reformular sua pergunta?"
            return [fallback]
        
        # ✅ CRÍTICO: Converte markdown para WhatsApp ANTES de tudo
        response = self._convert_markdown_to_whatsapp(response)
        
        # Detecta tipo de conteúdo
        content_type = self._detect_content_type(response)
        
        if content_type == "structured_list":
            return self._format_structured_list(response)
        elif content_type == "explanation":
            return self._format_explanation(response)
        elif content_type == "conversation":
            return self._format_conversation(response)
        else:
            return self._format_generic(response)
    
    def _convert_markdown_to_whatsapp(self, text: str) -> str:
        """✅ CRÍTICO: Converte/remove formatação para WhatsApp"""
        
        # Modo texto completamente limpo
        if self.config.clean_text_mode:
            # Remove TODOS os markdowns
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove **bold**
            text = re.sub(r'\*(.*?)\*', r'\1', text)      # Remove *italic*
            text = re.sub(r'`([^`]+)`', r'\1', text)      # Remove `code`
            text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)  # Remove headers
            text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)  # Remove bullets
            text = re.sub(r'^\s*\d+\.\s*', '', text, flags=re.MULTILINE)  # Remove numeração
            return text
        
        # Formatação WhatsApp nativa
        if self.config.whatsapp_formatting:
            # ✅ CORREÇÃO CRÍTICA: Converte **bold** para *bold* (WhatsApp)
            text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)
            
            # Remove headers markdown completamente
            text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
            
            # Converte listas markdown para formato simples
            text = re.sub(r'^\s*[-*+]\s+', '• ', text, flags=re.MULTILINE)
            
            # Remove código inline desnecessário
            text = re.sub(r'`([^`]+)`', r'\1', text)
            
            # ✅ NOVO: Remove formatação de tabelas
            text = re.sub(r'\|.*?\|', '', text, flags=re.MULTILINE)
            
            # ✅ NOVO: Limpa espaços extras após conversões
            text = re.sub(r'\n\n+', '\n\n', text)
            text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _detect_content_type(self, response: str) -> str:
        """Detecta o tipo de conteúdo da resposta"""
        # Padrões para listas numeradas (após conversão)
        if re.search(r'\d+\.\s+', response):
            return "structured_list"
        
        # Padrões para explicações
        if any(word in response.lower() for word in ["porque", "pois", "devido", "explicando"]):
            return "explanation"
        
        # Padrões para conversação
        if len(response) < 300 and "?" in response:
            return "conversation"
        
        return "generic"
    
    def _format_structured_list(self, response: str) -> List[str]:
        """
        Formata listas estruturadas (como planos, opções, etc)
        ✅ CORRIGIDO: Sem markdown, apenas WhatsApp nativo
        """
        messages = []
        
        # Extrai introdução se houver
        intro_match = re.match(r'^(.*?)(?=\d+\.)', response, re.DOTALL)
        if intro_match and intro_match.group(1).strip():
            intro = intro_match.group(1).strip()
            if self.config.use_emojis:
                intro = "✨ " + intro
            messages.append(self._truncate(intro))
        
        # Processa itens da lista
        items = re.findall(r'(\d+\..*?)(?=\d+\.|$)', response, re.DOTALL)
        
        for item in items:
            # Remove quebras de linha excessivas
            item = re.sub(r'\n+', ' ', item.strip())
            
            # Divide item longo se necessário
            if len(item) > self.config.max_chars:
                parts = self._split_long_item(item)
                messages.extend(parts)
            else:
                if self.config.use_emojis:
                    item = self._add_item_emoji(item)
                messages.append(item)
        
        # Adiciona mensagem de fechamento
        if messages and not any(p in messages[-1].lower() for p in ["avisar", "perguntar", "mais"]):
            closing = "Precisa de mais detalhes sobre alguma opção?"
            if self.config.use_emojis:
                closing = "💬 " + closing
            messages.append(closing)
        elif not messages:
            fallback = "Pode me contar mais sobre o que você precisa?"
            if self.config.use_emojis:
                fallback = "💬 " + fallback
            messages.append(fallback)
                    
        return messages
    
    def _format_explanation(self, response: str) -> List[str]:
        """Formata explicações em chunks naturais"""
        messages = []
        
        # Divide por frases
        sentences = re.split(r'(?<=[.!?])\s+', response)
        
        current_message = ""
        for sentence in sentences:
            # Se adicionar a frase exceder o limite, cria nova mensagem
            if len(current_message) + len(sentence) > self.config.max_chars:
                if current_message:
                    messages.append(current_message.strip())
                current_message = sentence
            else:
                current_message += " " + sentence if current_message else sentence
        
        # Adiciona última mensagem
        if current_message:
            messages.append(current_message.strip())
        
        return messages if messages else [response[:self.config.max_chars]]
    
    def _format_conversation(self, response: str) -> List[str]:
        """Formata respostas conversacionais curtas"""
        if len(response) <= self.config.max_chars:
            return [response]
        
        return self._format_generic(response)
    
    def _format_generic(self, response: str) -> List[str]:
        """Formatação genérica para qualquer conteúdo"""
        messages = []
        
        # Remove espaços e quebras excessivas
        response = re.sub(r'\n\n+', '\n', response.strip())
        
        # Divide em parágrafos
        paragraphs = response.split('\n')
        
        for para in paragraphs:
            if not para.strip():
                continue
            
            # Se o parágrafo é maior que o limite
            if len(para) > self.config.max_chars:
                parts = self._smart_split(para)
                messages.extend(parts)
            else:
                messages.append(para.strip())
        
        return messages if messages else [response[:self.config.max_chars]]
    
    def _smart_split(self, text: str) -> List[str]:
        """Divisão inteligente respeitando pontuação e contexto"""
        messages = []
        
        # Pontos de quebra preferenciais
        break_points = [
            (r'(?<=[.!?])\s+', True),   # Após pontuação forte
            (r'(?<=[,;:])\s+', True),   # Após pontuação fraca
            (r'(?<=\))\s+', True),      # Após parênteses
            (r'\s+(?=mas|porém|entretanto|todavia)', True),  # Antes de conjunções
            (r'\s+', False),            # Qualquer espaço
        ]
        
        remaining = text
        while remaining:
            if len(remaining) <= self.config.max_chars:
                messages.append(remaining.strip())
                break
            
            # Tenta cada ponto de quebra
            split_made = False
            for pattern, keep_delimiter in break_points:
                matches = list(re.finditer(pattern, remaining[:self.config.max_chars]))
                if matches:
                    last_match = matches[-1]
                    cut_point = last_match.end() if keep_delimiter else last_match.start()
                    
                    messages.append(remaining[:cut_point].strip())
                    remaining = remaining[cut_point:].strip()
                    split_made = True
                    break
            
            # Se não encontrou ponto de quebra, força no limite
            if not split_made:
                messages.append(remaining[:self.config.max_chars].strip())
                remaining = remaining[self.config.max_chars:].strip()
        
        return messages
    
    def _split_long_item(self, item: str) -> List[str]:
        """Divide um item longo de lista em múltiplas mensagens"""
        # Extrai número do item
        number_match = re.match(r'(\d+\.)', item)
        number = number_match.group(1) if number_match else ""
        content = item[len(number):].strip() if number else item
        
        # Divide o conteúdo
        parts = self._smart_split(content)
        
        # Adiciona número apenas na primeira parte
        if parts:
            parts[0] = f"{number} {parts[0]}" if number else parts[0]
        
        return parts
    
    def _add_item_emoji(self, item: str) -> str:
        """Adiciona emoji apropriado ao item"""
        emoji_map = {
            "essencial": "⭐",
            "profissional": "🚀", 
            "premium": "💎",
            "enterprise": "🏢",
            "básico": "📱",
            "avançado": "⚡",
            "completo": "🎯"
        }
        
        item_lower = item.lower()
        for keyword, emoji in emoji_map.items():
            if keyword in item_lower:
                # Adiciona emoji após o número
                return re.sub(r'^(\d+\.)', rf'\1 {emoji}', item)
        
        return item
    
    def _truncate(self, text: str) -> str:
        """Trunca texto no limite de caracteres"""
        if len(text) <= self.config.max_chars:
            return text
        
        # Tenta cortar em ponto de pontuação
        truncated = text[:self.config.max_chars]
        
        # Procura último ponto de pontuação
        for punct in ['. ', '! ', '? ', ', ', ' ']:
            last_punct = truncated.rfind(punct)
            if last_punct > self.config.max_chars * 0.7:  # Pelo menos 70% do limite
                return truncated[:last_punct + 1].strip()
        
        # Se não encontrou, corta no último espaço
        last_space = truncated.rfind(' ')
        if last_space > 0:
            return truncated[:last_space] + "..."
        
        return truncated + "..."


def create_formatter(tenant_config: Dict[str, Any]) -> MessageFormatter:
    """Factory para criar formatter com config do tenant"""
    formatter_config = FormatterConfig.from_dict(
        tenant_config.get("formatter", {})
    )
    return MessageFormatter(formatter_config)