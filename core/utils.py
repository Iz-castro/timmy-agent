# -*- coding: utf-8 -*-
"""
Core Utils - Versão com micro-responses inteligentes
"""

import os
import re
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
_SESSIONS: Dict[str, Dict[str, Any]] = {}
_KNOWLEDGE_CACHE: Dict[str, Dict[str, Any]] = {}


# =============================================================================
# SESSION MANAGEMENT
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
    """Marca algo como executado uma vez"""
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
# MICRO-RESPONSES INTELIGENTES
# =============================================================================

def micro_responses(
    text: str, 
    min_chars: int = 80, 
    max_chars: int = 120,
    session_key: Optional[str] = None
) -> List[str]:
    """
    Quebra texto em micro-respostas INTELIGENTES
    
    Prioridades da quebra:
    1. Sentenças completas (ponto final, exclamação, interrogação)
    2. Pausas naturais (vírgulas, dois pontos)
    3. Conjunções (e, mas, porém, então)
    4. Espaços em branco
    5. Como último recurso: caracteres
    """
    if not text or not text.strip():
        return [""]
    
    text = text.strip()
    
    # Se texto é pequeno o suficiente, retorna direto
    if len(text) <= max_chars:
        return [text]
    
    print(f"[DEBUG] Quebrando texto de {len(text)} caracteres: '{text}'")
    
    # 1. PRIMEIRA TENTATIVA: Quebra por sentenças completas
    sentences = re.split(r'(?<=[.!?])\s+', text)
    print(f"[DEBUG] Sentenças encontradas: {sentences}")
    
    if len(sentences) > 1:
        responses = []
        current = ""
        
        for sentence in sentences:
            # Se sentença individual é muito grande, quebra ela internamente
            if len(sentence) > max_chars:
                # Finaliza bloco atual se existir
                if current:
                    responses.append(current.strip())
                    current = ""
                
                # Quebra a sentença grande usando quebra inteligente
                sub_responses = _intelligent_sentence_break(sentence, min_chars, max_chars)
                responses.extend(sub_responses)
                continue
            
            # Testa se pode adicionar a sentença ao bloco atual
            test_text = (current + " " + sentence).strip() if current else sentence
            
            if len(test_text) <= max_chars:
                current = test_text
                
                # Se chegou ao tamanho mínimo, pode finalizar
                if len(current) >= min_chars:
                    responses.append(current)
                    current = ""
            else:
                # Não cabe, finaliza bloco atual e inicia novo
                if current:
                    responses.append(current)
                current = sentence
        
        # Adiciona último bloco
        if current:
            responses.append(current)
        
        if responses:
            print(f"[DEBUG] Quebra por sentenças resultou em: {responses}")
            return responses
    
    # 2. SEGUNDA TENTATIVA: Quebra inteligente de texto único
    return _intelligent_sentence_break(text, min_chars, max_chars)


def _intelligent_sentence_break(text: str, min_chars: int, max_chars: int) -> List[str]:
    """
    Quebra inteligente de uma sentença longa
    
    Ordem de prioridade para quebra:
    1. Pausas naturais (, : ; )
    2. Conjunções (e, mas, porém, então, porque)
    3. Espaços entre palavras
    4. Caracteres (último recurso)
    """
    print(f"[DEBUG] Quebra inteligente para: '{text}' (len={len(text)})")
    
    if len(text) <= max_chars:
        return [text]
    
    # 1. Tenta quebrar por pausas naturais (vírgulas, dois pontos, etc.)
    pause_points = []
    for match in re.finditer(r'[,:;]\s+', text):
        pause_points.append(match.end())
    
    if pause_points:
        print(f"[DEBUG] Pontos de pausa encontrados: {pause_points}")
        best_break = _find_best_break_point(text, pause_points, min_chars, max_chars)
        if best_break:
            part1 = text[:best_break].strip()
            part2 = text[best_break:].strip()
            print(f"[DEBUG] Quebra por pausa: '{part1}' | '{part2}'")
            
            # Recursivamente quebra as partes se necessário
            result = []
            result.extend(_intelligent_sentence_break(part1, min_chars, max_chars))
            result.extend(_intelligent_sentence_break(part2, min_chars, max_chars))
            return result
    
    # 2. Tenta quebrar por conjunções
    conjunction_points = []
    conjunctions = ['\\se\\s', '\\smas\\s', '\\sporém\\s', '\\sentão\\s', '\\sque\\s', '\\sonde\\s', '\\scomo\\s']
    
    for conj in conjunctions:
        for match in re.finditer(conj, text, re.IGNORECASE):
            conjunction_points.append(match.start())
    
    if conjunction_points:
        print(f"[DEBUG] Pontos de conjunção encontrados: {conjunction_points}")
        best_break = _find_best_break_point(text, conjunction_points, min_chars, max_chars)
        if best_break:
            part1 = text[:best_break].strip()
            part2 = text[best_break:].strip()
            print(f"[DEBUG] Quebra por conjunção: '{part1}' | '{part2}'")
            
            result = []
            result.extend(_intelligent_sentence_break(part1, min_chars, max_chars))
            result.extend(_intelligent_sentence_break(part2, min_chars, max_chars))
            return result
    
    # 3. Quebra por espaços (palavras completas)
    words = text.split()
    if len(words) <= 1:
        # Texto é uma palavra única muito longa - quebra por caracteres
        return _break_by_characters(text, max_chars)
    
    print(f"[DEBUG] Quebrando por palavras ({len(words)} palavras)")
    
    responses = []
    current = ""
    
    for word in words:
        test_text = (current + " " + word).strip() if current else word
        
        if len(test_text) <= max_chars:
            current = test_text
        else:
            # Não cabe mais, finaliza bloco atual
            if current:
                responses.append(current)
                current = word
            else:
                # Palavra individual é muito grande
                if len(word) > max_chars:
                    responses.extend(_break_by_characters(word, max_chars))
                else:
                    current = word
    
    # Adiciona último bloco
    if current:
        responses.append(current)
    
    print(f"[DEBUG] Quebra por palavras resultou em: {responses}")
    return responses if responses else [text]


def _find_best_break_point(text: str, break_points: List[int], min_chars: int, max_chars: int) -> Optional[int]:
    """
    Encontra o melhor ponto de quebra dentro dos limites
    """
    valid_points = []
    
    for point in break_points:
        if min_chars <= point <= max_chars:
            valid_points.append(point)
    
    if not valid_points:
        return None
    
    # Prefere ponto mais próximo do ideal (meio do intervalo)
    ideal_point = (min_chars + max_chars) // 2
    best_point = min(valid_points, key=lambda x: abs(x - ideal_point))
    
    print(f"[DEBUG] Melhor ponto de quebra: {best_point} (ideal: {ideal_point})")
    return best_point


def _break_by_characters(text: str, max_chars: int) -> List[str]:
    """
    Quebra por caracteres como último recurso
    """
    print(f"[DEBUG] Quebra por caracteres (último recurso) para: '{text}'")
    
    responses = []
    start = 0
    
    while start < len(text):
        end = start + max_chars
        if end >= len(text):
            responses.append(text[start:])
            break
        
        # Tenta não quebrar no meio de uma palavra
        if text[end] != ' ' and end < len(text) - 1:
            # Procura espaço anterior
            space_pos = text.rfind(' ', start, end)
            if space_pos > start + (max_chars // 2):  # Se espaço não está muito no início
                end = space_pos
        
        responses.append(text[start:end].strip())
        start = end
        
        # Pula espaços
        while start < len(text) and text[start] == ' ':
            start += 1
    
    print(f"[DEBUG] Quebra por caracteres resultou em: {responses}")
    return responses


# =============================================================================
# KNOWLEDGE LOADING (mantém como estava)
# =============================================================================

def load_knowledge_data(tenant_id: str = "default") -> Dict[str, Any]:
    """Carrega dados de conhecimento para um tenant"""
    
    if tenant_id in _KNOWLEDGE_CACHE:
        return _KNOWLEDGE_CACHE[tenant_id]
    
    knowledge = {}
    tenant_path = Path("tenants") / tenant_id
    
    # Config básico
    config_file = tenant_path / "config.json"
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                knowledge.update(config)
        except Exception as e:
            print(f"[WARNING] Erro ao carregar config.json: {e}")
    
    # Conhecimento específico
    knowledge_file = tenant_path / "knowledge.json"
    if knowledge_file.exists():
        try:
            with open(knowledge_file, 'r', encoding='utf-8') as f:
                kb_data = json.load(f)
                knowledge["knowledge_base"] = kb_data
        except Exception as e:
            print(f"[WARNING] Erro ao carregar knowledge.json: {e}")
    
    # Exemplos de conversa
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
    
    # Configuração padrão
    if not knowledge:
        knowledge = {
            "agent_name": "Timmy",
            "business_name": "nossa empresa",
            "language": "pt-BR",
            "knowledge_base": {},
            "examples": []
        }
    
    _KNOWLEDGE_CACHE[tenant_id] = knowledge
    return knowledge


def reload_knowledge(tenant_id: str = "default") -> Dict[str, Any]:
    """Recarrega conhecimento forçando atualização"""
    _KNOWLEDGE_CACHE.pop(tenant_id, None)
    return load_knowledge_data(tenant_id)


# =============================================================================
# INFORMATION EXTRACTION (mantém como estava)
# =============================================================================

def extract_info_from_text(text: str) -> Dict[str, str]:
    """Extrai informações do texto de forma avançada"""
    info = {}
    text_lower = text.lower()
    
    # Nome
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
    
    # Email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_match = re.search(email_pattern, text)
    if email_match:
        info['email'] = email_match.group()
    
    # Telefone
    phone_patterns = [
        r'\(?(?:\+55\s?)?(?:\d{2})\)?\s?\d{4,5}-?\d{4}',
        r'\(?(?:\d{2})\)?\s?\d{4,5}-?\d{4}',
        r'(?:\+55\s?)?(?:\d{2})\s?\d{4,5}\s?\d{4}'
    ]
    
    for pattern in phone_patterns:
        phone_match = re.search(pattern, text)
        if phone_match:
            phone = re.sub(r'[^\d+]', '', phone_match.group())
            if len(phone) >= 10:
                info['phone'] = phone_match.group()
                break
    
    # Empresa
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
    
    # Cargo
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
    
    return info


# =============================================================================
# LLM INTEGRATION
# =============================================================================

def chat_complete(
    system_prompt: str,
    messages: List[Dict[str, str]],
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 400
) -> str:
    """Chama API da OpenAI com modelo mais barato"""
    
    if model is None:
        model = os.getenv("TIMMY_MODEL", "gpt-4o-mini")
    
    try:
        api_messages = [{"role": "system", "content": system_prompt}] + messages
        
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
# UTILITY FUNCTIONS
# =============================================================================

def create_tenant_structure(tenant_id: str) -> bool:
    """Cria estrutura básica para novo tenant"""
    try:
        tenant_path = Path("tenants") / tenant_id
        tenant_path.mkdir(parents=True, exist_ok=True)
        
        config = {
            "agent_name": "Timmy",
            "business_name": f"Empresa {tenant_id.title()}",
            "language": "pt-BR",
            "created_at": str(Path.cwd() / "utils.py")
        }
        
        with open(tenant_path / "config.json", 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
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
    
# ADICIONAR ao final do core/utils.py

def load_tenant_workflow(tenant_id: str):
    """Carrega workflow customizado do tenant"""
    try:
        import importlib.util
        import json
        
        # Verifica se há configuração de workflow
        config_path = Path(f"tenants/{tenant_id}/workflow_config.json")
        if not config_path.exists():
            print(f"[DEBUG] Sem workflow config para tenant: {tenant_id}")
            return None
        
        # Carrega configuração
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        workflow_type = config.get("workflow_type")
        if not workflow_type:
            print(f"[DEBUG] Workflow type não definido para tenant: {tenant_id}")
            return None
        
        print(f"[DEBUG] Carregando workflow {workflow_type} para tenant: {tenant_id}")
        
        # Importa template correspondente
        if workflow_type == "medical_base":
            from core.workflows.medical_base import MedicalWorkflow
            workflow = MedicalWorkflow(tenant_id, config)
            print(f"[DEBUG] Workflow medical_base carregado com sucesso!")
            return workflow
        # elif workflow_type == "commerce_base":
        #     from core.workflows.commerce_base import CommerceWorkflow
        #     return CommerceWorkflow(tenant_id, config)
        
        print(f"[DEBUG] Tipo de workflow '{workflow_type}' não implementado")
        return None
    
    except Exception as e:
        print(f"[ERROR] Erro ao carregar workflow do tenant {tenant_id}: {e}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return None