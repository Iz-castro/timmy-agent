# -*- coding: utf-8 -*-
"""
Timmy-IA - Interface Streamlit
Aplicação web com estrutura organizada por tenant
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
    from core.agent import handle_turn, Message, get_user_history, get_data_stats, get_all_tenants_stats
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
    system_stats = get_system_stats()
    st.sidebar.json(system_stats)

# Estatísticas do tenant atual
if st.sidebar.checkbox("📊 Estatísticas do Tenant"):
    tenant_stats = get_data_stats(tenant_id)
    st.sidebar.json(tenant_stats, expanded=True)

# Estatísticas de todos os tenants
if st.sidebar.checkbox("🌐 Todos os Tenants"):
    all_stats = get_all_tenants_stats()
    st.sidebar.json(all_stats, expanded=False)

# =============================================================================
# ÁREA PRINCIPAL
# =============================================================================

st.title("🤖 Timmy-IA")
st.caption(f"Assistente conversacional inteligente • Tenant: **{tenant_id}**")

# Informações da nova estrutura
if st.checkbox("ℹ️ Mostrar estrutura de dados"):
    st.info(f"""
    **Nova estrutura organizada por tenant:**
    ```
    data/
    └── {tenant_id}/
        ├── conversations/    # Um CSV por conversa
        ├── sessions/        # Sessões do tenant
        └── users/          # Usuários do tenant
    ```
    """)

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
    - 🏢 **Organizado por tenant** para múltiplos clientes
    - 📁 **Arquivo separado** para cada conversa
    
    **Dicas:**
    - Mencione seu nome para que o Timmy te reconheça
    - Pergunte sobre produtos, serviços ou informações da empresa
    - Use a sidebar para trocar de tenant ou ver estatísticas
    """)

# Debug info (apenas em desenvolvimento)
if os.getenv("DEBUG", "false").lower() == "true":
    with st.expander("🔧 Debug Info"):
        st.write("**Estado da Sessão:**")
        st.json(get_state(st.session_state.session_key))
        
        st.write("**Estatísticas do Sistema:**")
        st.json(get_system_stats())
        
        st.write("**Estatísticas do Tenant Atual:**")
        st.json(get_data_stats(tenant_id))
        
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

# Footer com métricas expandidas
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

# Estatísticas do tenant atual
tenant_stats = get_data_stats(tenant_id)

with col1:
    st.metric("Sessões Ativas", len(list_sessions()))

with col2:
    api_status = "✅ Conectado" if os.getenv("OPENAI_API_KEY") else "❌ Sem API Key"
    st.metric("OpenAI API", api_status)

with col3:
    st.metric("Tenants", len(list_available_tenants()))

with col4:
    total_conversations = tenant_stats.get("total_conversations", 0)
    st.metric("Conversas", total_conversations)

# Segunda linha de métricas específicas do tenant
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_users = tenant_stats.get("total_users", 0)
    st.metric("Usuários", total_users)

with col2:
    total_sessions = tenant_stats.get("total_sessions", 0)
    st.metric("Sessões", total_sessions)

with col3:
    total_messages = tenant_stats.get("total_messages", 0)
    st.metric("Mensagens", total_messages)

with col4:
    active_sessions_count = tenant_stats.get("active_sessions", 0)
    st.metric("Ativas", active_sessions_count)

# Footer com informações da versão
st.markdown(
    f"""
    <div style='text-align: center; color: #666; font-size: 0.8em; margin-top: 2rem;'>
        🤖 <strong>Timmy-IA v2.0</strong> | Assistente Conversacional com Estrutura por Tenant<br>
        <em>Criado com Streamlit + OpenAI + Python | Tenant: {tenant_id}</em>
    </div>
    """, 
    unsafe_allow_html=True
)