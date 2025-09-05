# -*- coding: utf-8 -*-
"""
Core Utils - Utilitários e ferramentas do Timmy-IA
Responsável por: sessões, micro-respostas, carregamento de dados, LLM
"""

import os
import re
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Cliente OpenAI
_openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Armazenamento de sessões (memória local)
_SESSIONS: Dict[str, Dict[str, Any]] = {}

# Cache de conhecimento por tenant
_KNOWLEDGE_CACHE: Dict[str, Dict[str, Any]] = {}


# =============================================================================
# SESSION MANAGEMENT (Gerenciamento de Sessões)
# =============================================================================

def get_state(session_key: str) -> Dict[str, Any]:
    """Obtém estado da sessão"""
    return _SESSIONS.setdefault(str(session_key), {})


def set_state(session_key: str, **kwargs) -> None:
    """Define valores no estado da sessão"""
    state = _SESSIONS.setdefault(str(session_key), {})
    for key, value in kwargs.items():
        if value is not None:
            state[str(key)] = value


def mark_once(session_key: str, tag: str) -> bool:
    """
    Marca algo como já executado na sessão
    Retorna True se é a primeira vez, False se já foi executado
    """
    state = get_state(session_key)
    executed = state.get("_executed", set())
    
    if not isinstance(executed, set):
        executed = set()
    
    if str(tag) in executed:
        return False
    
    executed.add(str(tag))
    state["_executed"] = executed
    return True


def clear_session(session_key: str) -> None:
    """Limpa uma sessão específica"""
    _SESSIONS.pop(str(session_key), None)


def list_sessions() -> List[str]:
    """Lista todas as sessões ativas"""
    return list(_SESSIONS.keys())


# =============================================================================
# MICRO-RESPONSES (Quebra de Respostas)
# =============================================================================

def micro_responses(
    text: str, 
    min_chars: int = 80, 
    max_chars: int = 120,
    session_key: Optional[str] = None
) -> List[str]:
    """
    Quebra texto em micro-respostas respeitando limites de caracteres
    
    Args:
        text: Texto a ser quebrado
        min_chars: Mínimo de caracteres por resposta
        max_chars: Máximo de caracteres por resposta
        session_key: Chave da sessão (para fila de pendentes)
    
    Returns:
        Lista de micro-respostas
    """
    if not text or not text.strip():
        return [""]
    
    text = text.strip()
    
    # Se texto é pequeno, retorna direto
    if len(text) <= max_chars:
        return [text]
    
    # Quebra por sentenças
    sentences = re.split(r'(?<=[.!?])\s+', text)
    responses = []
    current = ""
    
    for sentence in sentences:
        # Se sentença única é muito grande, quebra por espaços
        if len(sentence) > max_chars:
            if current:
                responses.append(current.strip())
                current = ""
            
            # Quebra sentença longa em palavras
            words = sentence.split()
            for word in words:
                if len(current + " " + word) > max_chars:
                    if current:
                        responses.append(current.strip())
                    current = word
                else:
                    current = (current + " " + word).strip()
            continue
        
        # Tenta adicionar sentença ao bloco atual
        test_length = len(current + " " + sentence) if current else len(sentence)
        
        if test_length <= max_chars:
            current = (current + " " + sentence).strip() if current else sentence
            
            # Se chegou ao mínimo, pode finalizar bloco
            if len(current) >= min_chars:
                responses.append(current)
                current = ""
        else:
            # Finaliza bloco atual e inicia novo
            if current:
                responses.append(current)
            current = sentence
    
    # Adiciona último bloco
    if current:
        responses.append(current)
    
    return responses if responses else [text]


# =============================================================================
# KNOWLEDGE LOADING (Carregamento de Conhecimento)
# =============================================================================

def load_knowledge_data(tenant_id: str = "default") -> Dict[str, Any]:
    """
    Carrega dados de conhecimento para um tenant
    
    Args:
        tenant_id: ID do tenant
        
    Returns:
        Dicionário com dados de conhecimento
    """
    
    # Verifica cache
    if tenant_id in _KNOWLEDGE_CACHE:
        return _KNOWLEDGE_CACHE[tenant_id]
    
    knowledge = {}
    
    # Caminho base do tenant
    tenant_path = Path("tenants") / tenant_id
    
    # Carrega configuração básica
    config_file = tenant_path / "config.json"
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                knowledge.update(config)
        except Exception as e:
            print(f"[WARNING] Erro ao carregar config.json: {e}")
    
    # Carrega conhecimento específico
    knowledge_file = tenant_path / "knowledge.json"
    if knowledge_file.exists():
        try:
            with open(knowledge_file, 'r', encoding='utf-8') as f:
                kb_data = json.load(f)
                knowledge["knowledge_base"] = kb_data
        except Exception as e:
            print(f"[WARNING] Erro ao carregar knowledge.json: {e}")
    
    # Carrega exemplos de conversa
    examples_file = tenant_path / "examples.jsonl"
    if examples_file.exists():
        try:
            examples = []
            with open(examples_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        examples.append(json.loads(line))
            knowledge["examples"] = examples
        except Exception as e:
            print(f"[WARNING] Erro ao carregar examples.jsonl: {e}")
    
    # Configuração padrão se não existir nada
    if not knowledge:
        knowledge = {
            "agent_name": "Timmy",
            "business_name": "nossa empresa",
            "language": "pt-BR",
            "knowledge_base": {},
            "examples": []
        }
    
    # Salva no cache
    _KNOWLEDGE_CACHE[tenant_id] = knowledge
    
    return knowledge


def reload_knowledge(tenant_id: str = "default") -> Dict[str, Any]:
    """Recarrega conhecimento forçando atualização do cache"""
    _KNOWLEDGE_CACHE.pop(tenant_id, None)
    return load_knowledge_data(tenant_id)


# =============================================================================
# INFORMATION EXTRACTION (Extração de Informações)
# =============================================================================

def extract_info_from_text(text: str) -> Dict[str, str]:
    """
    Extrai informações avançadas do texto (nome, email, telefone, empresa, etc.)
    
    Args:
        text: Texto para análise
        
    Returns:
        Dicionário com informações extraídas
    """
    info = {}
    text_lower = text.lower()
    
    # Extração de nome
    name_patterns = [
        r"(?:meu nome é|me chamo|sou o|sou a|eu sou)\s+([A-Za-zÀ-ÿ\s]{2,30})",
        r"(?:^|\s)([A-Z][a-zÀ-ÿ]+(?:\s+[A-Z][a-zÀ-ÿ]+)*),?\s*(?:aqui|falando|é meu nome)"
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) >= 2 and not any(word in name.lower() for word in ['você', 'senhor', 'senhora']):
                info['name'] = name
                break
    
    # Extração de email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_match = re.search(email_pattern, text)
    if email_match:
        info['email'] = email_match.group()
    
    # Extração de telefone
    phone_patterns = [
        r'\(?(?:\+55\s?)?(?:\d{2})\)?\s?\d{4,5}-?\d{4}',  # Formato brasileiro
        r'\(?(?:\d{2})\)?\s?\d{4,5}-?\d{4}',              # Formato simples
        r'(?:\+55\s?)?(?:\d{2})\s?\d{4,5}\s?\d{4}'        # Sem separadores
    ]
    
    for pattern in phone_patterns:
        phone_match = re.search(pattern, text)
        if phone_match:
            phone = re.sub(r'[^\d+]', '', phone_match.group())
            if len(phone) >= 10:
                info['phone'] = phone_match.group()
                break
    
    # Extração de empresa
    company_patterns = [
        r"(?:trabalho na|trabalho no|empresa|companhia)\s+([A-Za-zÀ-ÿ\s&]{2,30})",
        r"(?:sou da|venho da)\s+([A-Za-zÀ-ÿ\s&]{2,30})",
        r"([A-Za-zÀ-ÿ\s&]{2,30})\s+(?:ltda|sa|s\.a\.|me|mei|eireli)"
    ]
    
    for pattern in company_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            if len(company) >= 2:
                info['company'] = company
                break
    
    # Extração de cargo/profissão
    job_patterns = [
        r"(?:sou|trabalho como|atuo como|profissão)\s+([A-Za-zÀ-ÿ\s]{2,30})",
        r"(?:cargo|função|posição)\s+(?:de|é)\s+([A-Za-zÀ-ÿ\s]{2,30})"
    ]
    
    for pattern in job_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            job = match.group(1).strip()
            if len(job) >= 2:
                info['job_title'] = job
                break
    
    # Extração de localização
    location_patterns = [
        r"(?:moro em|vivo em|de|localizado em)\s+([A-Za-zÀ-ÿ\s\-]{2,30})",
        r"(?:cidade|estado|região)\s+(?:de|é)\s+([A-Za-zÀ-ÿ\s\-]{2,30})"
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            if len(location) >= 2:
                info['location'] = location
                break
    
    # Extração de idade
    age_patterns = [
        r"(?:tenho|idade|anos)\s+(\d{1,2})\s*anos?",
        r"(\d{1,2})\s*anos\s+(?:de idade|old)"
    ]
    
    for pattern in age_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            age = match.group(1)
            if 15 <= int(age) <= 99:  # Validação básica de idade
                info['age'] = age
                break
    
    # Extração de interesses/preferências
    interest_patterns = [
        r"(?:gosto de|interessado em|prefiro|hobby)\s+([A-Za-zÀ-ÿ\s,]{5,50})",
        r"(?:interesse|paixão|área)\s+(?:é|por)\s+([A-Za-zÀ-ÿ\s,]{5,50})"
    ]
    
    for pattern in interest_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            interests = match.group(1).strip()
            if len(interests) >= 3:
                info['interests'] = interests
                break
    
    return info


# =============================================================================
# LLM INTEGRATION (Integração com LLM)
# =============================================================================

def chat_complete(
    system_prompt: str,
    messages: List[Dict[str, str]],
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 400
) -> str:
    """
    Chama API da OpenAI para completar conversa
    
    Args:
        system_prompt: Prompt do sistema
        messages: Lista de mensagens [{"role": "user/assistant", "content": "..."}]
        model: Modelo a usar (padrão: gpt-4o-mini)
        temperature: Criatividade (0-1)
        max_tokens: Máximo de tokens na resposta
        
    Returns:
        Resposta do modelo
    """
    
    if model is None:
        model = os.getenv("TIMMY_MODEL", "gpt-4o-mini")
    
    try:
        # Prepara mensagens
        api_messages = [{"role": "system", "content": system_prompt}] + messages
        
        # Chama API
        response = _openai_client.chat.completions.create(
            model=model,
            messages=api_messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content or ""
        
    except Exception as e:
        print(f"[ERROR] Erro na chamada LLM: {e}")
        return "Desculpe, tive um problema técnico. Pode tentar novamente?"


# =============================================================================
# UTILITY FUNCTIONS (Funções Auxiliares)
# =============================================================================

def create_tenant_structure(tenant_id: str) -> bool:
    """
    Cria estrutura básica de arquivos para um novo tenant
    
    Args:
        tenant_id: ID do novo tenant
        
    Returns:
        True se criado com sucesso
    """
    try:
        tenant_path = Path("tenants") / tenant_id
        tenant_path.mkdir(parents=True, exist_ok=True)
        
        # config.json básico
        config = {
            "agent_name": "Timmy",
            "business_name": f"Empresa {tenant_id.title()}",
            "language": "pt-BR",
            "created_at": str(Path.cwd() / "utils.py")
        }
        
        with open(tenant_path / "config.json", 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        # knowledge.json básico
        knowledge = {
            "business_info": {
                "name": f"Empresa {tenant_id.title()}",
                "description": "Empresa de exemplo"
            },
            "faq": [],
            "services": [],
            "contact": {}
        }
        
        with open(tenant_path / "knowledge.json", 'w', encoding='utf-8') as f:
            json.dump(knowledge, f, indent=2, ensure_ascii=False)
        
        # examples.jsonl básico
        examples = [
            {"role": "user", "content": "Olá!"},
            {"role": "assistant", "content": "Olá! Como posso ajudar você hoje?"}
        ]
        
        with open(tenant_path / "examples.jsonl", 'w', encoding='utf-8') as f:
            for example in examples:
                f.write(json.dumps(example, ensure_ascii=False) + '\n')
        
        print(f"[SUCCESS] Tenant '{tenant_id}' criado em: {tenant_path}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Erro ao criar tenant '{tenant_id}': {e}")
        return False


def get_system_stats() -> Dict[str, Any]:
    """Retorna estatísticas do sistema"""
    return {
        "active_sessions": len(_SESSIONS),
        "cached_tenants": len(_KNOWLEDGE_CACHE),
        "session_keys": list(_SESSIONS.keys())
    }