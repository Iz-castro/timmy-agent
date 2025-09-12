# app.py
"""
Timmy-IA - Interface Streamlit Simplificada
Compatível com a nova arquitetura de 5 arquivos
"""

import os
import uuid
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

# Carrega variáveis de ambiente (.env)
load_dotenv()

# Core
from core.agent import handle_turn, Message
from core.utils import (
    load_tenant_config,
    list_tenants,
    get_tenant_stats,
    create_tenant_structure,
)

# -----------------------------------------------------------------------------
# CONFIG DA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Timmy-IA - Assistente Multi-Tenant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS (opcional)
st.markdown(
    """
<style>
.stChat { background-color: #f5f5f5; border-radius: 10px; padding: 10px; }
.user-message { background-color: #007AFF; color: white; padding: 10px; border-radius: 15px; margin: 5px 0; text-align: right; }
.assistant-message { background-color: #E5E5EA; color: black; padding: 10px; border-radius: 15px; margin: 5px 0; }
.stats-card { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 10px 0; }
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# ESTADO
# -----------------------------------------------------------------------------
if "session_key" not in st.session_state:
    st.session_state.session_key = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_tenant" not in st.session_state:
    st.session_state.selected_tenant = "timmy_vendas"
if "show_debug" not in st.session_state:
    st.session_state.show_debug = False

# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configurações")

    # Tenants
    st.subheader("🏢 Tenant")
    available_tenants = list_tenants()
    if not available_tenants:
        st.warning("Nenhum tenant encontrado!")
        if st.button("➕ Criar Tenant Padrão"):
            create_tenant_structure("timmy_vendas")
            st.rerun()
    else:
        selected_tenant = st.selectbox(
            "Selecione o Tenant:",
            available_tenants,
            index=available_tenants.index(st.session_state.selected_tenant)
            if st.session_state.selected_tenant in available_tenants
            else 0,
            key="tenant_selector",
        )

        if selected_tenant != st.session_state.selected_tenant:
            st.session_state.selected_tenant = selected_tenant
            st.session_state.messages = []
            st.session_state.session_key = str(uuid.uuid4())
            st.rerun()

    # Info do tenant
    if st.session_state.selected_tenant:
        cfg = load_tenant_config(st.session_state.selected_tenant)
        st.info(
            f"**Agente:** {cfg.get('agent_name','Timmy')}  \n"
            f"**Empresa:** {cfg.get('business_name','N/A')}  \n"
            f"**Sessão:** {st.session_state.session_key[:8]}..."
        )

    st.divider()

    # Controles
    st.subheader("💬 Conversa")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Nova Conversa", use_container_width=True):
            st.session_state.messages = []
            st.session_state.session_key = str(uuid.uuid4())
            st.rerun()
    with col2:
        if st.button("🗑️ Limpar Tudo", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    st.session_state.show_debug = st.checkbox("🛠 Modo Debug", value=st.session_state.show_debug)

    st.divider()

    # Estatísticas
    st.subheader("📊 Estatísticas")
    if st.session_state.selected_tenant:
        stats = get_tenant_stats(st.session_state.selected_tenant)
        if stats["exists"]:
            st.metric("Total Conversas", stats["total_conversations"])
            st.metric("Total Mensagens", stats["total_messages"])
            st.metric("Sessões Ativas", stats["total_sessions"])
        else:
            st.info("Ainda sem dados para este tenant")

    # Criar novo tenant
    st.divider()
    st.subheader("➕ Novo Tenant")
    with st.expander("Criar Novo Tenant"):
        new_tenant_id = st.text_input("ID do Tenant:", placeholder="ex: minha_empresa", key="new_tenant_id")
        if st.button("Criar Tenant", disabled=not new_tenant_id):
            if new_tenant_id and new_tenant_id not in available_tenants:
                if create_tenant_structure(new_tenant_id):
                    st.success(f"Tenant '{new_tenant_id}' criado!")
                    st.session_state.selected_tenant = new_tenant_id
                    st.rerun()
                else:
                    st.error("Erro ao criar tenant")
            else:
                st.error("ID inválido ou já existe")

# -----------------------------------------------------------------------------
# ÁREA PRINCIPAL
# -----------------------------------------------------------------------------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.title("🤖 Timmy-IA")
    if st.session_state.selected_tenant:
        cfg = load_tenant_config(st.session_state.selected_tenant)
        st.caption(f"Conversando com **{cfg.get('agent_name','Timmy')}** — {cfg.get('business_name','')}")

chat_container = st.container()

# Histórico
with chat_container:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.write(m["content"])
            if st.session_state.show_debug and "metadata" in m:
                with st.expander("🔍 Debug Info"):
                    st.json(m["metadata"])

# Entrada do usuário
if prompt := st.chat_input("Digite sua mensagem..."):
    st.session_state.messages.append({"role": "user", "content": prompt, "timestamp": datetime.now().isoformat()})
    with st.chat_message("user"):
        st.write(prompt)

    # Resposta do agente
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                message = Message(
                    text=prompt,
                    session_key=st.session_state.session_key,
                    metadata={"tenant": st.session_state.selected_tenant, "timestamp": datetime.now().isoformat()},
                )

                # ✅ CORRIGIDO: handle_turn agora retorna List[str] diretamente
                response_pieces = handle_turn(tenant_id=st.session_state.selected_tenant, message=message)

                # Exibe cada chunk como uma mensagem separada
                import time
                for i, resp in enumerate(response_pieces):
                    st.write(resp)
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": resp,
                            "timestamp": datetime.now().isoformat(),
                            "metadata": {"chunk_index": i, "total_chunks": len(response_pieces)},
                        }
                    )
                    time.sleep(0.05)  # Pequena pausa para efeito visual

            except Exception as e:
                error_msg = f"⚠️ Erro: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": "Ops! Algo deu errado. Tenta de novo?",
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {"error": True, "error_detail": str(e)},
                    }
                )
                
                # ✅ NOVO: Modo debug mostra erro completo
                if st.session_state.show_debug:
                    import traceback
                    st.code(traceback.format_exc(), language="python")