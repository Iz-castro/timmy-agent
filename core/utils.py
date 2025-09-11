# -*- coding: utf-8 -*-
"""
Core Utils - REFATORADO: Mantém funções base + compatibilidade com nova arquitetura
Funções específicas migradas para processadores especializados
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
# SESSION MANAGEMENT (MANTIDO - FUNCÕES BASE)
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
# LLM INTEGRATION (MANTIDO - FUNÇÃO BASE)
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
# KNOWLEDGE LOADING (MANTIDO COM AVISO DE DEPRECIAÇÃO)
# =============================================================================

def load_knowledge_data(tenant_id: str = "default") -> Dict[str, Any]:
    """
    Carrega dados de conhecimento para um tenant
    
    DEPRECIAÇÃO: Esta função será movida para extension_loader.load_tenant_config()
    em versões futuras. Mantida por compatibilidade.
    """
    
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
    """
    Recarrega conhecimento forçando atualização
    
    DEPRECIAÇÃO: Use extension_loader.reload_tenant_extensions() na nova arquitetura
    """
    _KNOWLEDGE_CACHE.pop(tenant_id, None)
    return load_knowledge_data(tenant_id)


# =============================================================================
# LEGACY FUNCTIONS (MANTIDAS COM AVISOS DE DEPRECIAÇÃO)
# =============================================================================

def micro_responses(
    text: str, 
    min_chars: int = 120, 
    max_chars: int = 200,
    session_key: Optional[str] = None
) -> List[str]:
    """
    Quebra texto em micro-respostas INTELIGENTES
    
    DEPRECIAÇÃO: Esta função foi movida para ResponseProcessor._break_text_intelligently()
    Mantida por compatibilidade. Use a nova arquitetura para funcionalidades completas.
    """
    print(f"[DEPRECATION WARNING] micro_responses() será removida. Use ResponseProcessor.")
    
    if not text or not text.strip():
        return [""]
    
    text = text.strip()
    
    if len(text) <= max_chars:
        return [text]
    
    # Implementação simplificada para compatibilidade
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    if len(sentences) > 1:
        responses = []
        current = ""
        
        for sentence in sentences:
            if len(sentence) > max_chars:
                if current:
                    responses.append(current.strip())
                    current = ""
                
                # Quebra sentença longa por pausas
                responses.extend(_break_by_natural_pauses(sentence, max_chars))
                continue
            
            test_text = (current + " " + sentence).strip() if current else sentence
            
            if len(test_text) <= max_chars:
                current = test_text
            else:
                if current:
                    responses.append(current)
                current = sentence
        
        if current:
            responses.append(current)
        
        if responses:
            return responses
    
    return _break_by_natural_pauses(text, max_chars)


def format_structured_response(
    intro_text: str,
    items: List[Dict[str, str]], 
    outro_text: str,
    session_key: str = None
) -> List[str]:
    """
    Formata resposta estruturada em 3 fases
    
    DEPRECIAÇÃO: Esta função foi movida para ResponseProcessor._apply_structured_formatting()
    Mantida por compatibilidade.
    """
    print(f"[DEPRECATION WARNING] format_structured_response() será removida. Use ResponseProcessor.")
    
    responses = []
    
    # Introdução
    if intro_text and intro_text.strip():
        intro_parts = micro_responses(intro_text, min_chars=120, max_chars=200, session_key=session_key)
        responses.extend(intro_parts)
    
    # Cada item = 1 mensagem completa
    for i, item in enumerate(items, 1):
        if "number" in item and "title" in item:
            formatted_item = f"{item['number']}. **{item['title']}**: {item['details']}"
        elif "title" in item:
            formatted_item = f"**{item['title']}**: {item['details']}"
        else:
            formatted_item = item.get('details', str(item))
        
        responses.append(formatted_item)
    
    # Fechamento
    if outro_text and outro_text.strip():
        outro_parts = micro_responses(outro_text, min_chars=120, max_chars=200, session_key=session_key)
        responses.extend(outro_parts)
    
    return responses


def extract_info_from_text(text: str) -> Dict[str, str]:
    """
    Extrai informações do texto de forma avançada
    
    DEPRECIAÇÃO: Esta função foi movida para MessageProcessor.extract_entities()
    Mantida por compatibilidade com funcionalidade reduzida.
    """
    print(f"[DEPRECATION WARNING] extract_info_from_text() será removida. Use MessageProcessor.")
    
    info = {}
    text_lower = text.lower()
    
    # Nome (versão simplificada)
    name_patterns = [
        r"(?:meu nome é|me chamo|sou o|sou a|eu sou)\s+([A-Za-zÀ-ÿ\s]{2,30})",
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) >= 2:
                info['name'] = name
                break
    
    # Email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_match = re.search(email_pattern, text)
    if email_match:
        info['email'] = email_match.group()
    
    # Telefone
    phone_pattern = r'\(?(?:\+55\s?)?(?:\d{2})\)?\s?\d{4,5}-?\d{4}'
    phone_match = re.search(phone_pattern, text)
    if phone_match:
        info['phone'] = phone_match.group()
    
    return info


def _break_by_natural_pauses(text: str, max_chars: int) -> List[str]:
    """Quebra texto por pausas naturais (função auxiliar)"""
    if len(text) <= max_chars:
        return [text]
    
    # Procura pausas naturais
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
            result.extend(_break_by_natural_pauses(part1, max_chars))
            result.extend(_break_by_natural_pauses(part2, max_chars))
            return result
    
    # Quebra por palavras como último recurso
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


# =============================================================================
# UTILITY FUNCTIONS (MANTIDAS)
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
        
        # NOVO: Cria diretórios para nova arquitetura
        for ext_dir in ["strategies", "workflows", "formatters"]:
            (tenant_path / ext_dir).mkdir(exist_ok=True)
            
            # Cria arquivo __init__.py vazio
            with open(tenant_path / ext_dir / "__init__.py", 'w') as f:
                f.write("# Extensões do tenant\n")
        
        print(f"[SUCCESS] Tenant '{tenant_id}' criado em: {tenant_path}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Erro ao criar tenant '{tenant_id}': {e}")
        return False


def get_system_stats() -> Dict[str, Any]:
    """Retorna estatísticas do sistema"""
    stats = {
        "active_sessions": len(_SESSIONS),
        "cached_tenants": len(_KNOWLEDGE_CACHE),
        "session_keys": list(_SESSIONS.keys())
    }
    
    # Adiciona informações da nova arquitetura se disponível
    try:
        from core.extensions.loader import extension_loader
        stats["new_architecture"] = "available"
        stats["extension_loader"] = "loaded"
    except ImportError:
        stats["new_architecture"] = "unavailable"
    
    return stats


def load_tenant_workflow(tenant_id: str):
    """
    Carrega workflow customizado do tenant
    
    DEPRECIAÇÃO: Esta função foi substituída por extension_loader.load_tenant_workflows()
    Mantida por compatibilidade.
    """
    print(f"[DEPRECATION WARNING] load_tenant_workflow() será removida. Use extension_loader.")
    
    try:
        # Tenta usar nova arquitetura primeiro
        try:
            from core.extensions.loader import extension_loader
            workflows = extension_loader.load_tenant_workflows(tenant_id)
            return workflows[0] if workflows else None
        except ImportError:
            pass
        
        # Fallback para sistema legado
        import importlib.util
        import json
        
        config_path = Path(f"tenants/{tenant_id}/workflow_config.json")
        if not config_path.exists():
            return None
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        workflow_type = config.get("workflow_type")
        if not workflow_type:
            return None
        
        if workflow_type == "medical_base":
            from core.workflows.medical_base import MedicalWorkflow
            workflow = MedicalWorkflow(tenant_id, config)
            return workflow
        
        return None
    
    except Exception as e:
        print(f"[ERROR] Erro ao carregar workflow do tenant {tenant_id}: {e}")
        return None


# =============================================================================
# MIGRATION HELPERS (NOVAS FUNÇÕES)
# =============================================================================

def check_new_architecture_availability() -> Dict[str, Any]:
    """
    Verifica se a nova arquitetura está disponível
    """
    try:
        from core.processors.message import MessageProcessor
        from core.processors.context import ContextProcessor
        from core.processors.response import ResponseProcessor
        from core.extensions.loader import extension_loader
        from core.extensions.registry import component_registry
        
        return {
            "available": True,
            "processors": {
                "MessageProcessor": "loaded",
                "ContextProcessor": "loaded", 
                "ResponseProcessor": "loaded"
            },
            "extensions": {
                "extension_loader": "loaded",
                "component_registry": "loaded"
            }
        }
    except ImportError as e:
        return {
            "available": False,
            "error": str(e),
            "recommendation": "Execute: pip install -r requirements.txt e implemente os novos processadores"
        }


def migrate_conversation_strategy_to_tenant(source_file: str, target_tenant: str) -> bool:
    """
    Migra arquivo conversation_strategy.py para tenant específico
    """
    try:
        source_path = Path(source_file)
        if not source_path.exists():
            print(f"[ERROR] Arquivo fonte não encontrado: {source_file}")
            return False
        
        target_dir = Path(f"tenants/{target_tenant}/strategies")
        target_dir.mkdir(parents=True, exist_ok=True)
        
        target_file = target_dir / "consultative_strategy.py"
        
        # Lê arquivo original
        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Modifica imports para nova arquitetura
        content = content.replace(
            "from core.interfaces.strategy import",
            "from core.interfaces.strategy import"
        )
        
        # Adiciona implementação de interface se necessário
        if "class ConsultativeStrategy" in content and "ConversationStrategy" not in content:
            content = "from core.interfaces.strategy import ConversationStrategy\n\n" + content
            content = content.replace(
                "class ConsultativeStrategy:",
                "class ConsultativeStrategy(ConversationStrategy):"
            )
        
        # Salva no tenant
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[SUCCESS] Estratégia migrada para: {target_file}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Erro na migração: {e}")
        return False