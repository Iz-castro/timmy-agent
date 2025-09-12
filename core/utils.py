# core/utils.py
"""
Utilitários e funções auxiliares
CORRIGIDO: Import circular removido + encoding + estrutura consistente
"""

import json
import csv
from pathlib import Path
from typing import Dict, Any, List


def load_tenant_config(tenant_id: str) -> Dict[str, Any]:
    """Carrega configuração do tenant"""
    config_path = Path("tenants") / tenant_id / "config.json"

    if not config_path.exists():
        # Config padrão segura para rodar
        return {
            "agent_name": "Timmy",
            "business_name": "Iz-Solutions",
            "language": "pt-BR",
            "personality": {"tone": "profissional e amigável", "style": "direto e claro"},
            "formatter": {"max_chars": 200, "use_emojis": True, "greeting_style": "friendly", "list_style": "numbered"},
            "llm": {"model": "gpt-4o-mini", "temperature": 0.7, "max_tokens": 500},
            "structured_keywords": ["planos", "preços", "valores", "opções", "serviços", "produtos", "pacotes"],
            "intent_patterns": {},
            "analysis_rules": [],
        }

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"⚠️ Erro ao carregar config do tenant {tenant_id}: {e}")
        # Retorna config padrão em caso de erro
        return load_tenant_config("default") if tenant_id != "default" else {}


def load_tenant_knowledge(tenant_id: str) -> Dict[str, Any]:
    """Carrega base de conhecimento do tenant"""
    knowledge_path = Path("tenants") / tenant_id / "knowledge.json"

    if not knowledge_path.exists():
        return {"business_info": {}, "services": [], "faq": []}

    try:
        with open(knowledge_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"⚠️ Erro ao carregar knowledge do tenant {tenant_id}: {e}")
        return {"business_info": {}, "services": [], "faq": []}


def load_tenant_examples(tenant_id: str) -> List[Dict[str, str]]:
    """Carrega exemplos JSONL do tenant (opcional)"""
    examples_path = Path("tenants") / tenant_id / "examples.jsonl"
    if not examples_path.exists():
        return []
    
    examples: List[Dict[str, str]] = []
    try:
        with open(examples_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    examples.append(json.loads(line))
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"⚠️ Erro ao carregar examples do tenant {tenant_id}: {e}")
    
    return examples


def create_tenant_structure(tenant_id: str) -> bool:
    """
    Cria estrutura completa para novo tenant.
    ✅ CORRIGIDO: Removido import circular, usa estrutura consistente
    """
    try:
        tenant_path = Path("tenants") / tenant_id
        tenant_path.mkdir(parents=True, exist_ok=True)

        # Config mínima
        config = {
            "agent_name": "Timmy",
            "business_name": f"Empresa {tenant_id.title()}",
            "language": "pt-BR",
            "personality": {"tone": "profissional e amigável", "style": "direto e claro"},
            "formatter": {"max_chars": 200, "use_emojis": True, "greeting_style": "friendly", "list_style": "numbered"},
            "llm": {"model": "gpt-4o-mini", "temperature": 0.7, "max_tokens": 500},
            "structured_keywords": ["planos", "preços", "valores", "opções", "serviços", "produtos", "pacotes"],
            "intent_patterns": {},
            "analysis_rules": [],
        }
        (tenant_path / "config.json").write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")

        knowledge = {
            "business_info": {
                "name": f"Empresa {tenant_id.title()}",
                "description": "Descrição da empresa",
                "contact": {"phone": "", "email": "", "website": ""},
            },
            "services": [],
            "products": [],
            "faq": [],
            "policies": {},
        }
        (tenant_path / "knowledge.json").write_text(json.dumps(knowledge, indent=2, ensure_ascii=False), encoding="utf-8")

        # Exemplos básicos
        examples = [
            {"role": "user", "content": "Olá!"},
            {"role": "assistant", "content": "Olá! Como posso ajudar você hoje?"},
            {"role": "user", "content": "Quais são seus planos?"},
            {"role": "assistant", "content": "Claro! Vou te mostrar nossos planos disponíveis."},
        ]
        with open(tenant_path / "examples.jsonl", "w", encoding="utf-8") as f:
            for ex in examples:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")

        # ✅ CORRIGIDO: Cria estrutura de dados sem import circular
        data_path = Path("data") / "tenants" / tenant_id
        for subdir in ["conversations", "sessions", "users"]:
            (data_path / subdir).mkdir(parents=True, exist_ok=True)
            # Cria .gitkeep para manter estrutura no git
            (data_path / subdir / ".gitkeep").touch()

        return True
    except Exception as e:
        print(f"❌ Erro ao criar tenant {tenant_id}: {e}")
        return False


# ==============================
# Helpers usados pelo app.py
# ==============================

def list_tenants() -> List[str]:
    """Lista diretórios em tenants/"""
    tenants_root = Path("tenants")
    if not tenants_root.exists():
        tenants_root.mkdir(parents=True, exist_ok=True)
        return []
    
    # ✅ CORRIGIDO: Só lista tenants que têm config.json válido
    valid_tenants = []
    for p in tenants_root.iterdir():
        if p.is_dir() and (p / "config.json").exists():
            try:
                # Testa se o config é válido
                load_tenant_config(p.name)
                valid_tenants.append(p.name)
            except Exception:
                print(f"⚠️ Tenant {p.name} tem config.json inválido, ignorando...")
    
    return sorted(valid_tenants)


def get_tenant_stats(tenant_id: str) -> Dict[str, Any]:
    """Retorna totais para o painel lateral do app."""
    # ✅ CORRIGIDO: Usar estrutura data/tenants/<tenant_id>/
    data_path = Path("data") / "tenants" / tenant_id
    conversations = data_path / "conversations"
    sessions = data_path / "sessions"

    if not data_path.exists():
        return {"exists": False, "total_conversations": 0, "total_messages": 0, "total_sessions": 0}

    total_conversations = 0
    total_messages = 0
    if conversations.exists():
        for f in conversations.glob("*.csv"):
            total_conversations += 1
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    total_messages += max(0, sum(1 for _ in csv.reader(fh)) - 1)  # - header
            except Exception:
                pass

    total_sessions = len(list(sessions.glob("*.json"))) if sessions.exists() else 0
    return {
        "exists": True,
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "total_sessions": total_sessions,
    }