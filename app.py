# -*- coding: utf-8 -*-
"""
Timmy-IA - Interface Streamlit
ATUALIZADO: Compatível com nova arquitetura core/
"""

import os
import uuid
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Imports da nova arquitetura
try:
    from core.agent import handle_turn, Message
    from core.utils import get_state, clear_session, list_sessions
    from core.persistence import persistence_manager
except ImportError as e:
    st.error(f"Erro ao importar módulos principais: {e}")
    st.stop()

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================

st.set_page_config(
    page_title="Timmy-IA - Assistente Conversacional",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def list_available_tenants():
    """Lista tenants disponíveis"""
    tenants_dir = Path("tenants")
    if not tenants_dir.exists():
        return ["default"]
    
    tenants = []
    for item in tenants_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('__'):
            tenants.append(item.name)
    
    return sorted(tenants) if tenants else ["default"]

def get_tenant_info(tenant_id):
    """Carrega informações básicas do tenant"""
    try:
        config_path = Path(f"tenants/{tenant_id}/config.json")
        if config_path.exists():
            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return {
                    "name": config.get("agent_name", tenant_id.title()),
                    "business": config.get("business_name", "Empresa"),
                    "description": config.get("description", "Assistente conversacional")
                }
    except Exception as e:
        print(f"Erro ao carregar config do tenant {tenant_id}: {e}")
    
    return {
        "name": tenant_id.title(),
        "business": "Empresa",
        "description": "Assistente conversacional"
    }

def get_data_stats(tenant_id):
    """Retorna estatísticas do tenant"""
    try:
        return persistence_manager.get_tenant_stats(tenant_id)
    except Exception as e:
        print(f"Erro ao obter stats do tenant {tenant_id}: {e}")
        return {
            "total_users": 0,
            "total_sessions": 0,
            "total_conversations": 0,
            "total_messages": 0,
            "active_sessions": 0
        }

def get_all_tenants_stats():
    """Retorna estatísticas de todos os tenants"""
    try:
        return persistence_manager.get_all_tenants_stats()
    except Exception as e:
        print(f"Erro ao obter stats globais: {e}")
        return {}

# =============================================================================
# SIDEBAR - CONFIGURAÇÕES
# =============================================================================

st.sidebar.header("⚙️ Configurações")

# Seleção de tenant
available_tenants = list_available_tenants()
tenant_id = st.sidebar.selectbox(
    "Selecionar Tenant:",
    available_tenants,
    help="Escolha qual versão do assistente usar"
)

# Informações do tenant selecionado
tenant_info = get_tenant_info(tenant_id)
st.sidebar.markdown(f"**🤖 {tenant_info['name']}**")
st.sidebar.markdown(f"*{tenant_info['business']}*")
st.sidebar.caption(tenant_info['description'])

# Controles de sessão
st.sidebar.markdown("---")
st.sidebar.subheader("🔄 Controles")

if st.sidebar.button("🗑️ Limpar Conversa", use_container_width=True):
    session_key = st.session_state.get('session_key', '')
    if session_key:
        clear_session(session_key)
        st.sidebar.success("Conversa limpa!")
        st.rerun()

# Estatísticas do tenant
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Estatísticas")

tenant_stats = get_data_stats(tenant_id)
st.sidebar.metric("Conversas", tenant_stats.get("total_conversations", 0))
st.sidebar.metric("Usuários", tenant_stats.get("total_users", 0))
st.sidebar.metric("Mensagens", tenant_stats.get("total_messages", 0))

# =============================================================================
# INTERFACE PRINCIPAL
# =============================================================================

# Título dinâmico
st.title(f"🤖 {tenant_info['name']}")
st.caption(f"Assistente de {tenant_info['business']} | Tenant: `{tenant_id}`")

# Inicializa session_state
if 'session_key' not in st.session_state:
    st.session_state.session_key = f"streamlit_{uuid.uuid4().hex[:12]}"

if 'messages' not in st.session_state:
    st.session_state.messages = []

# Container para o chat
chat_container = st.container()

# Área de entrada de mensagem
with st.form("message_form", clear_on_submit=True):
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input(
            "Digite sua mensagem:",
            placeholder=f"Converse com {tenant_info['name']}...",
            label_visibility="collapsed"
        )
    
    with col2:
        submit_button = st.form_submit_button("▶️ Enviar", use_container_width=True)

# Processamento da mensagem
if submit_button and user_input.strip():
    # Adiciona mensagem do usuário
    st.session_state.messages.append({
        "role": "user", 
        "content": user_input,
        "timestamp": "agora"
    })
    
    with st.spinner(f"{tenant_info['name']} está pensando..."):
        try:
            # Cria objeto Message
            message_obj = Message(
                text=user_input,
                session_key=st.session_state.session_key,
                tenant_id=tenant_id
            )
            
            # Chama handle_turn com a nova assinatura
            result = handle_turn(message_obj)
            
            # Processa resposta baseado no tipo
            if isinstance(result, dict):
                # Nova arquitetura retorna dict
                response_text = result.get('response', 'Desculpe, não consegui processar sua mensagem.')
                status = result.get('status', 'unknown')
                method = result.get('method', 'unknown')
                
                # Log para debug
                st.sidebar.caption(f"Status: {status} | Método: {method}")
                
            elif isinstance(result, list):
                # Sistema legado retorna lista
                response_text = ' '.join(result) if result else 'Desculpe, não consegui processar sua mensagem.'
                
            else:
                # Fallback
                response_text = str(result) if result else 'Desculpe, não consegui processar sua mensagem.'
            
            # Adiciona resposta do assistente
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_text,
                "timestamp": "agora"
            })
            
        except Exception as e:
            st.error(f"Erro ao processar mensagem: {e}")
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"Desculpe, ocorreu um erro: {str(e)}",
                "timestamp": "agora"
            })

# Display do chat
with chat_container:
    if not st.session_state.messages:
        st.info(f"👋 Olá! Sou o {tenant_info['name']}. Como posso ajudar você hoje?")
    else:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

# =============================================================================
# SIDEBAR EXPANDIDO - DEBUG E ADMIN
# =============================================================================

with st.sidebar.expander("🔧 Debug & Admin", expanded=False):
    st.subheader("🔍 Informações Técnicas")
    
    # Informações da sessão
    st.write("**Sessão Atual:**")
    st.code(st.session_state.session_key)
    
    # Estado da sessão
    session_data = get_state(st.session_state.session_key)
    if session_data:
        st.write("**Estado da Sessão:**")
        st.json(session_data, expanded=False)
    
    # Configurações de ambiente
    st.write("**Variáveis de Ambiente:**")
    env_vars = {
        "OPENAI_API_KEY": "✅ Configurada" if os.getenv("OPENAI_API_KEY") else "❌ Não configurada",
        "TIMMY_MODEL": os.getenv("TIMMY_MODEL", "Não definido"),
        "DEBUG": os.getenv("DEBUG", "false")
    }
    st.json(env_vars)
    
    # Sessões ativas
    st.write("**Sessões Ativas:**")
    active_sessions = list_sessions()
    if active_sessions:
        for session in active_sessions[:5]:  # Mostra apenas primeiras 5
            st.caption(f"🔑 {session}")
    else:
        st.caption("Nenhuma sessão ativa")
    
    # Estatísticas globais
    if st.button("📊 Ver Stats Globais"):
        global_stats = get_all_tenants_stats()
        st.json(global_stats, expanded=False)

# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")

# Métricas principais
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Sessões Ativas", len(list_sessions()))

with col2:
    api_status = "✅ Conectado" if os.getenv("OPENAI_API_KEY") else "❌ Sem API Key"
    st.metric("OpenAI API", api_status)

with col3:
    st.metric("Tenants", len(available_tenants))

with col4:
    st.metric("Mensagens", len(st.session_state.messages))

# Informações da versão
st.markdown(
    f"""
    <div style='text-align: center; color: #666; font-size: 0.8em; margin-top: 1rem;'>
        🤖 <strong>Timmy-IA v3.0</strong> | Nova Arquitetura Core<br>
        <em>Tenant: {tenant_id} | Sessão: {st.session_state.session_key[:8]}...</em>
    </div>
    """, 
    unsafe_allow_html=True
)