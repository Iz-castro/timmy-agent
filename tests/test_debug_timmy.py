# core/llm.py
"""
Interface com LLM - Genérica e configurável
"""

import os
from typing import Dict, Any, List
from openai import OpenAI
import json
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()


class LLMClient:
    """Cliente genérico para LLM"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get("model", "gpt-4o-mini")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 500)
        
        # Inicializa cliente OpenAI
        api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError(
                "API Key da OpenAI não encontrada! "
                "Configure OPENAI_API_KEY no arquivo .env ou na config do tenant."
            )
        
        # Simples inicialização - SEM chamada para _test_connection
        self.client = OpenAI(api_key=api_key)
    
    def generate_response(
        self,
        user_message: str,
        context: Dict[str, Any],
        knowledge: Dict[str, Any],
        config: Dict[str, Any]
    ) -> str:
        """Gera resposta usando LLM"""
        
        # Constrói prompt do sistema
        system_prompt = self._build_system_prompt(knowledge, config, context)
        
        # Constrói mensagens para o modelo
        messages = self._build_messages(user_message, context, system_prompt)
        
        # Chama API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        return response.choices[0].message.content
    
    def _build_system_prompt(
        self, 
        knowledge: Dict[str, Any],
        config: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Constrói prompt do sistema baseado em configuração"""
        
        agent_name = config.get("agent_name", "Timmy")
        business_name = config.get("business_name", "")
        personality = config.get("personality", {})
        
        prompt = f"""Você é {agent_name}, assistente virtual da {business_name}.

PERSONALIDADE:
- Tom: {personality.get('tone', 'profissional e amigável')}
- Estilo: {personality.get('style', 'direto e claro')}

CONHECIMENTO:
{json.dumps(knowledge, indent=2, ensure_ascii=False)}

REGRAS DE RESPOSTA:
1. SEMPRE responda de forma completa e estruturada
2. Para listas ou opções, use formato numerado com detalhes
3. Inclua TODOS os detalhes relevantes
4. Seja específico com valores, condições e características
5. A formatação em múltiplas mensagens será feita depois

CONTEXTO DA CONVERSA:
- Fase: {context.get('analysis', {}).get('conversation_phase', 'ongoing')}
- Intent detectado: {context.get('analysis', {}).get('detected_intent', 'general')}
- Resposta estruturada necessária: {context.get('analysis', {}).get('requires_structured_response', False)}
"""
        
        # Adiciona instruções específicas do tenant
        if "system_instructions" in config:
            prompt += f"\nINSTRUÇÕES ESPECÍFICAS:\n{config['system_instructions']}"
        
        return prompt
    
    def _build_messages(
        self,
        user_message: str,
        context: Dict[str, Any],
        system_prompt: str
    ) -> List[Dict[str, str]]:
        """Constrói array de mensagens para o modelo"""
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Adiciona histórico relevante
        history = context.get("history", [])
        for msg in history[-10:]:  # Últimas 10 mensagens
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Adiciona mensagem atual
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages