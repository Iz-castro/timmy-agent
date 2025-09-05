# -*- coding: utf-8 -*-
"""
Timmy-IA - Interface Streamlit
Aplicação web simples para testar o agente conversacional
"""

import os
import uuid
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Importa o agente principal
try:
    from core.agent import handle_turn, Message, get_user_history, get_data_stats
    from core.utils import get_state, clear_session, get_system_stats, list_sessions
    from core.persistence import persistence_manager
except ImportError as e:
    st.error(f"Erro ao importar módulos: {e}")
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
# SIDEBAR - CONFIGURAÇÕES
# =============================================================================

st.sidebar.header("⚙️ Configurações")

# Seleção de tenant
def list_available_tenants():
    """Lista tenants disponíveis"""
    tenants_dir = Path("tenants")
    if not tenants_dir.exists():
        return ["default"]
    
    tenants = []
    for item in tenants_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            tenants.append(item.name)
    
    return tenants if tenants else ["default"]

available_tenants = list_available_tenants()
tenant_id = st.sidebar.selectbox(
    "🏢 Tenant/Cliente",
    available_tenants,
    help="Selecione o cliente/configuração"
)

# Configurações do modelo
model_name = os.getenv("TIMMY_MODEL", "gpt-4o-mini")
st.sidebar.caption(f"🧠 Modelo: {model_name}")

# Informações da sessão
if "session_key" not in st.session_state:
    st.session_state.session_key = f"streamlit_{uuid.uuid4().hex[:8]}"

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Sessão Atual")
st.sidebar.caption(f"ID: {st.session_state.session_key}")

# Estado da sessão atual
current_state = get_state(st.session_state.session_key)
if current_state:
    st.sidebar.json(current_state, expanded=False)

# Botões de controle
col1, col2 = st.sidebar.columns(2)

with col1:
    if st.button("🔄 Nova Sessão", help="Inicia uma nova conversa"):
        clear_session(st.session_state.session_key)
        st.session_state.session_key = f"streamlit_{uuid.uuid4().hex[:8]}"
        st.session_state.clear()
        st.rerun()

with col2:
    if st.button("🗑️ Limpar Chat", help="Limpa apenas o histórico visual"):
        if "messages" in st.session_state:
            del st.session_state.messages
        st.rerun()

# Estatísticas do sistema
st.sidebar.markdown("---")
if st.sidebar.checkbox("📈 Estatísticas do Sistema"):
    stats = get_system_stats()
    st.sidebar.json(stats)

# =============================================================================
# ÁREA PRINCIPAL
# =============================================================================

st.title("🤖 Timmy-IA")
st.caption(f"Assistente conversacional inteligente • Tenant: **{tenant_id}**")

# Inicializa histórico de mensagens
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe histórico de conversa
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# =============================================================================
# ENTRADA DE MENSAGEM
# =============================================================================

# Campo de entrada
if prompt := st.chat_input("Digite sua mensagem..."):
    
    # Adiciona mensagem do usuário ao histórico
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Exibe mensagem do usuário
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Processa mensagem através do agente
    try:
        # Cria objeto Message
        message = Message(
            text=prompt,
            session_key=st.session_state.session_key,
            tenant_id=tenant_id
        )
        
        # Processa através do agente
        with st.spinner("Pensando..."):
            responses = handle_turn(tenant_id, message)
        
        # Exibe respostas do assistente
        for response in responses:
            if response.strip():  # Só exibe se não estiver vazio
                
                # Adiciona ao histórico
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response
                })
                
                # Exibe na interface
                with st.chat_message("assistant"):
                    st.markdown(response)
    
    except Exception as e:
        error_msg = f"❌ Erro ao processar mensagem: {str(e)}"
        st.error(error_msg)
        
        # Adiciona erro ao histórico para debug
        st.session_state.messages.append({
            "role": "assistant",
            "content": error_msg
        })

# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")

# Informações de ajuda
with st.expander("ℹ️ Como usar"):
    st.markdown("""
    **Timmy-IA** é um assistente conversacional que:
    
    - 💬 **Conversa naturalmente** com você
    - 📝 **Coleta informações** automaticamente (nome, contato, etc.)
    - 🧠 **Responde com base** no conhecimento configurado
    - 💾 **Mantém contexto** durante toda a conversa
    
    **Dicas:**
    - Mencione seu nome para que o Timmy te reconheça
    - Pergunte sobre produtos, serviços ou informações da empresa
    - Use a sidebar para trocar de tenant ou iniciar nova sessão
    """)

# Debug info (apenas em desenvolvimento)
if os.getenv("DEBUG", "false").lower() == "true":
    with st.expander("🔧 Debug Info"):
        st.write("**Estado da Sessão:**")
        st.json(get_state(st.session_state.session_key))
        
        st.write("**Estatísticas do Sistema:**")
        st.json(get_system_stats())
        
        st.write("**Variáveis de Ambiente:**")
        env_vars = {
            "OPENAI_API_KEY": "***" if os.getenv("OPENAI_API_KEY") else "❌ Não definida",
            "TIMMY_MODEL": os.getenv("TIMMY_MODEL", "Não definido"),
            "DEBUG": os.getenv("DEBUG", "false")
        }
        st.json(env_vars)
        
        st.write("**Sessões Ativas:**")
        active_sessions = list_sessions()
        if active_sessions:
            for session in active_sessions:
                with st.container():
                    st.write(f"🔑 **{session}**")
                    session_data = get_state(session)
                    if session_data:
                        st.json(session_data, expanded=False)
        else:
            st.write("Nenhuma sessão ativa")

# Footer com informações da versão e métricas expandidas
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Sessões Ativas", len(list_sessions()))

with col2:
    api_status = "✅ Conectado" if os.getenv("OPENAI_API_KEY") else "❌ Sem API Key"
    st.metric("OpenAI API", api_status)

with col3:
    tenant_count = len(list_available_tenants())
    st.metric("Tenants", tenant_count)

with col4:
    # 🔴 NOVO: Métrica de dados persistidos
    data_stats = get_data_stats()
    total_users = data_stats.get("total_users", 0)
    st.metric("Usuários", total_users)

# Footer com informações da versão
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.8em; margin-top: 2rem;'>
        🤖 <strong>Timmy-IA v1.0</strong> | Assistente Conversacional Inteligente<br>
        <em>Criado com Streamlit + OpenAI + Python</em>
    </div>
    """, 
    unsafe_allow_html=True
)