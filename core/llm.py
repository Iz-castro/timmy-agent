# core/llm.py
"""
Interface com LLM - Genérica e configurável
✅ MELHORADO: Abordagem consultiva + descoberta ativa + memória robusta
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
        
        # Inicializa cliente OpenAI com verificação da API key
        api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError(
                "API Key da OpenAI não encontrada! "
                "Configure OPENAI_API_KEY no arquivo .env ou na config do tenant."
            )
        
        try:
            self.client = OpenAI(api_key=api_key)
            self._test_connection()
        except Exception as e:
            raise ValueError(f"Erro ao conectar com a OpenAI: {e}")
    
    def _test_connection(self) -> None:
        """Testa conexão com a OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1,
                temperature=0
            )
        except Exception as e:
            raise ValueError(f"Falha no teste de conexão com OpenAI: {e}")
    
    def generate_response(
        self,
        user_message: str,
        context: Dict[str, Any],
        knowledge: Dict[str, Any],
        config: Dict[str, Any]
    ) -> str:
        """✅ MELHORADO: Gera resposta consultiva com descoberta ativa"""
        
        # Constrói prompt do sistema robusto
        system_prompt = self._build_consultive_system_prompt(knowledge, config, context)
        
        # Constrói mensagens para o modelo
        messages = self._build_messages_with_memory(user_message, context, system_prompt)
        
        # Chama API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        return response.choices[0].message.content
    
    def _build_consultive_system_prompt(
        self, 
        knowledge: Dict[str, Any],
        config: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """✅ NOVO: Prompt consultivo com descoberta ativa e memória robusta"""
        
        agent_name = config.get("agent_name", "Timmy")
        business_name = config.get("business_name", "")
        personality = config.get("personality", {})
        memory_data = context.get("memory_data", {})
        analysis = context.get("analysis", {})
        
        # ✅ NOVO: Análise do que ainda falta descobrir
        missing_info = self._analyze_missing_info(memory_data, context)
        discovery_priority = self._get_discovery_priority(missing_info, analysis)
        
        # ✅ MELHORADO: Seção de memória ativa e robusta
        memory_section = ""
        if memory_data:
            client_name = memory_data.get("client_name")
            business_area = memory_data.get("business_area")
            mentioned_facts = memory_data.get("mentioned_facts", [])
            
            memory_section = f"""
📋 MEMÓRIA COMPLETA DA CONVERSA:
- Nome do cliente: {client_name or "❌ NÃO INFORMADO - PERGUNTAR"}
- Área de negócio/empresa: {business_area or "❌ NÃO INFORMADO - PERGUNTAR"}
- Fatos importantes: {', '.join(mentioned_facts) if mentioned_facts else "❌ NENHUM - DESCOBRIR PROBLEMAS"}

🎯 REGRAS DE MEMÓRIA:
- SEMPRE se refira ao cliente pelo nome quando souber
- SEMPRE relembre detalhes específicos mencionados
- SE o cliente disser "esqueceu?" ou "já falei", revise a conversa completa
- NUNCA diga "não mencionou" se a informação está no histórico
"""

        # ✅ NOVO: Seção de descoberta ativa
        discovery_section = f"""
🔍 DESCOBERTA ATIVA (PRIORIDADE MÁXIMA):
{discovery_priority}

📝 PERGUNTAS DE DESCOBERTA OBRIGATÓRIAS:
1. Nome: "Qual seu nome?" ou "Como posso me dirigir a você?"
2. Negócio: "Que tipo de negócio você tem?" ou "Em que área você atua?"
3. Problemas: "Quais são seus maiores desafios com atendimento?" 
4. Volume: "Quantos atendimentos vocês fazem por mês?"
5. Dores: "O que mais consome tempo da sua equipe?"

⚠️ SÓ APRESENTE PLANOS DEPOIS DE ENTENDER O CLIENTE!
"""

        # ✅ NOVO: Seção de políticas (anti-alucinação)
        policies_section = ""
        if "policies" in knowledge:
            policies = knowledge["policies"]
            policies_section = f"""
🚫 POLÍTICAS OBRIGATÓRIAS (NUNCA INVENTE):
- Pagamento: {policies.get('payment', {}).get('methods', ['Consultar comercial'])}
- Cancelamento: {policies.get('cancellation', {}).get('contract_type', 'Consultar suporte')}
- Suporte: {policies.get('support', {}).get('channels', ['Consultar comercial'])}

🔒 REGRA CRÍTICA: Se não souber informação específica → "Entre em contato com nosso comercial"
"""

        # ✅ NOVO: Saudação personalizada
        greeting_section = ""
        if context.get("is_greeting", False):
            greeting_template = context.get("greeting_template", "")
            greeting_section = f"""
👋 PRIMEIRA INTERAÇÃO:
- Use saudação: "{greeting_template}"
- Seja caloroso e profissional
- IMEDIATAMENTE inicie descoberta: "Para te ajudar melhor, qual seu nome e que tipo de negócio você tem?"
"""

        # ✅ NOVO: Lógica consultiva vs informativa
        approach_section = f"""
🎯 ABORDAGEM CONSULTIVA:
{self._get_consultive_approach(missing_info, analysis)}
"""

        prompt = f"""Você é {agent_name}, consultor especialista em automação de atendimento da {business_name}.

PERSONALIDADE CONSULTIVA:
- Tom: {personality.get('tone', 'profissional e consultivo')}
- Estilo: {personality.get('style', 'descoberta ativa, entende primeiro')}
- Abordagem: SEMPRE consultiva - entenda PRIMEIRO, recomende DEPOIS

{memory_section}

{discovery_section}

{approach_section}

{policies_section}

{greeting_section}

CONHECIMENTO BASE:
{json.dumps(knowledge, indent=2, ensure_ascii=False)}

🎯 REGRAS DE RESPOSTA CONSULTIVA:
1. PRIORIDADE 1: Descobrir informações em falta (nome, negócio, problemas)
2. PRIORIDADE 2: Entender dores e necessidades específicas  
3. PRIORIDADE 3: Só então recomendar solução adequada
4. SEMPRE use informações APENAS do knowledge base
5. NUNCA invente preços, condições ou políticas
6. Use formatação WhatsApp nativa (*negrito*, não **markdown**)
7. Seja consultivo: faça perguntas, escute, entenda, DEPOIS venda

CONTEXTO ATUAL:
- Fase da conversa: {analysis.get('conversation_phase', 'ongoing')}
- Intent detectado: {analysis.get('detected_intent', 'discovery_needed')}
- Informações em falta: {', '.join(missing_info) if missing_info else 'Nenhuma'}
"""
        
        # Adiciona instruções específicas do tenant
        if "system_instructions" in config:
            prompt += f"\n\nINSTRUÇÕES ESPECÍFICAS DO TENANT:\n{config['system_instructions']}"
        
        return prompt
    
    def _analyze_missing_info(self, memory_data: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """✅ NOVO: Analisa que informações ainda faltam descobrir"""
        missing = []
        
        if not memory_data.get("client_name"):
            missing.append("nome_cliente")
        
        if not memory_data.get("business_area"):
            missing.append("tipo_negocio")
        
        if not memory_data.get("mentioned_facts"):
            missing.append("problemas_atuais")
        
        # Verifica se já perguntou sobre volume de atendimento
        history = context.get("history", [])
        volume_mentioned = any("atendimento" in msg.get("content", "").lower() 
                             for msg in history if msg.get("role") == "user")
        if not volume_mentioned:
            missing.append("volume_atendimento")
        
        return missing
    
    def _get_discovery_priority(self, missing_info: List[str], analysis: Dict[str, Any]) -> str:
        """✅ NOVO: Define prioridade de descoberta baseada no que falta"""
        if not missing_info:
            return "✅ Informações básicas coletadas. Focar em aprofundar necessidades."
        
        # Mapeamento de prioridades
        priority_map = {
            "nome_cliente": "🔥 URGENTE: Pergunte o nome do cliente",
            "tipo_negocio": "🔥 URGENTE: Descubra que tipo de negócio/empresa tem",
            "problemas_atuais": "⚡ IMPORTANTE: Entenda os problemas atuais com atendimento",
            "volume_atendimento": "📊 RELEVANTE: Pergunte quantos atendimentos fazem por mês"
        }
        
        priorities = []
        for info in missing_info:
            if info in priority_map:
                priorities.append(priority_map[info])
        
        return "\n".join(priorities)
    
    def _get_consultive_approach(self, missing_info: List[str], analysis: Dict[str, Any]) -> str:
        """✅ NOVO: Define abordagem baseada na fase da conversa"""
        
        if missing_info:
            return """
📋 FASE: DESCOBERTA ATIVA
- Faça perguntas diretas mas amigáveis
- Mostre interesse genuíno no negócio do cliente  
- NÃO mencione planos até entender as necessidades
- Use descoberta para criar conexão
"""
        
        detected_intent = analysis.get("detected_intent", "general")
        
        if detected_intent == "pricing":
            return """
💰 FASE: CONSULTA DE PREÇOS
- Cliente já quer saber preços
- Pode apresentar planos, MAS contextualizado às necessidades
- Destaque o plano mais adequado ao perfil descoberto
- Use descoberta prévia para personalizar recomendação
"""
        
        return """
🎯 FASE: CONSULTORIA
- Cliente informado, mas ainda descobrindo
- Aprofunde entendimento de dores específicas
- Apresente valor antes de preço
- Seja educativo sobre automação de atendimento
"""
    
    def _build_messages_with_memory(
        self,
        user_message: str,
        context: Dict[str, Any],
        system_prompt: str
    ) -> List[Dict[str, str]]:
        """✅ MELHORADO: Constrói array com TODA a conversa para memória ativa"""
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # ✅ NOVO: Adiciona TODA a conversa (memória completa)
        history = context.get("history", [])
        for msg in history:  # SEM LIMITE - toda a conversa
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