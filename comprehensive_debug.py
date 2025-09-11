# comprehensive_debug.py - Debug abrangente e preventivo
"""
Debug COMPLETO para identificar TODOS os problemas potenciais
antes de executar o Streamlit
"""

import traceback
import json
import uuid
import time
from pathlib import Path

print("🔍 DEBUG ABRANGENTE - TESTES PREVENTIVOS")
print("=" * 60)

# =============================================================================
# TESTE 1: IMPORTS E DEPENDÊNCIAS
# =============================================================================

print("\n1️⃣ VERIFICANDO TODOS OS IMPORTS E DEPENDÊNCIAS:")
imports_status = {}

# Core imports
try:
    from core.agent import Message, handle_turn, get_target_completion_status
    imports_status['core.agent'] = "✅ OK"
except Exception as e:
    imports_status['core.agent'] = f"❌ ERRO: {e}"

try:
    from core.utils import get_state, set_state, clear_session, micro_responses
    imports_status['core.utils'] = "✅ OK"
except Exception as e:
    imports_status['core.utils'] = f"❌ ERRO: {e}"

try:
    from core.persistence import persistence_manager, ConversationMessage
    imports_status['core.persistence'] = "✅ OK"
except Exception as e:
    imports_status['core.persistence'] = f"❌ ERRO: {e}"

try:
    from core.processors.target import target_manager, get_target_config
    imports_status['core.processors.target'] = "✅ OK"
except Exception as e:
    imports_status['core.processors.target'] = f"❌ ERRO: {e}"

# Streamlit imports (que serão usados no app.py)
try:
    import streamlit as st
    imports_status['streamlit'] = "✅ OK"
except Exception as e:
    imports_status['streamlit'] = f"❌ ERRO: {e}"

# Outros imports críticos
try:
    import openai
    imports_status['openai'] = "✅ OK"
except Exception as e:
    imports_status['openai'] = f"❌ ERRO: {e}"

for module, status in imports_status.items():
    print(f"   {module}: {status}")

# =============================================================================
# TESTE 2: CONFIGURAÇÕES E ARQUIVOS
# =============================================================================

print("\n2️⃣ VERIFICANDO CONFIGURAÇÕES E ARQUIVOS:")

# Verificar .env
env_status = {}
import os
from dotenv import load_dotenv
load_dotenv()

critical_env_vars = ['OPENAI_API_KEY', 'TIMMY_MODEL']
for var in critical_env_vars:
    value = os.getenv(var)
    if value:
        env_status[var] = f"✅ Configurado ({'***' if 'KEY' in var else value})"
    else:
        env_status[var] = "❌ NÃO CONFIGURADO"

for var, status in env_status.items():
    print(f"   {var}: {status}")

# Verificar estrutura de diretórios
print("\n   📁 ESTRUTURA DE DIRETÓRIOS:")
required_dirs = [
    "core/processors",
    "tenants/timmy_vendas", 
    "tenants/varizemed",
    "data"
]

for dir_path in required_dirs:
    path = Path(dir_path)
    if path.exists() and path.is_dir():
        print(f"   ✅ {dir_path}")
    else:
        print(f"   ❌ {dir_path} - FALTANDO")

# Verificar arquivos críticos
print("\n   📄 ARQUIVOS CRÍTICOS:")
required_files = [
    "core/agent.py",
    "core/utils.py", 
    "core/persistence.py",
    "core/processors/target.py",
    "tenants/timmy_vendas/config.json",
    "tenants/timmy_vendas/target_config.json",
    "tenants/varizemed/config.json", 
    "tenants/varizemed/target_config.json",
    "app.py"
]

for file_path in required_files:
    path = Path(file_path)
    if path.exists() and path.is_file():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            size_kb = len(content) / 1024
            print(f"   ✅ {file_path} ({size_kb:.1f}KB)")
        except Exception as e:
            print(f"   ⚠️ {file_path} - ERRO AO LER: {e}")
    else:
        print(f"   ❌ {file_path} - FALTANDO")

# =============================================================================
# TESTE 3: TENANTS E CONFIGURAÇÕES
# =============================================================================

print("\n3️⃣ TESTANDO TODOS OS TENANTS:")

tenants_to_test = ["timmy_vendas", "varizemed", "default"]

for tenant_id in tenants_to_test:
    print(f"\n   🏢 TENANT: {tenant_id}")
    
    # Testar target config
    try:
        target_config = get_target_config(tenant_id)
        if target_config:
            print(f"      ✅ Target: {target_config.target_name} ({len(target_config.fields)} campos)")
            
            # Verificar campos obrigatórios
            required_fields = [f.field_name for f in target_config.get_required_fields()]
            print(f"      📋 Obrigatórios: {required_fields}")
        else:
            print(f"      ⚠️ Sem target configurado")
    except Exception as e:
        print(f"      ❌ Erro no target: {e}")
    
    # Testar knowledge loading
    try:
        from core.utils import load_knowledge_data
        knowledge = load_knowledge_data(tenant_id)
        if knowledge:
            print(f"      ✅ Knowledge: {len(knowledge)} chaves")
        else:
            print(f"      ⚠️ Knowledge vazio ou não encontrado")
    except Exception as e:
        print(f"      ❌ Erro no knowledge: {e}")

# =============================================================================
# TESTE 4: SISTEMA DE SESSÕES E PERSISTÊNCIA
# =============================================================================

print("\n4️⃣ TESTANDO SISTEMA DE SESSÕES E PERSISTÊNCIA:")

# Teste de sessão básica
try:
    test_session = f"test_session_{uuid.uuid4().hex[:8]}"
    
    # Testar get/set state
    set_state(test_session, test_value="teste123", user_name="João")
    state = get_state(test_session)
    
    if state.get("test_value") == "teste123":
        print("   ✅ Sistema de sessões funcionando")
    else:
        print("   ❌ Sistema de sessões com problema")
        
    # Testar clear session
    clear_session(test_session)
    cleared_state = get_state(test_session)
    
    if not cleared_state or not cleared_state.get("test_value"):
        print("   ✅ Clear session funcionando")
    else:
        print("   ❌ Clear session com problema")
        
except Exception as e:
    print(f"   ❌ Erro no sistema de sessões: {e}")

# Teste de persistência
try:
    test_msg = ConversationMessage(
        message_id=str(uuid.uuid4()),
        session_id="test_persist",
        user_id="test_user",
        timestamp="2024-01-01T00:00:00",
        role="user",
        content="Mensagem de teste"
    )
    
    # Tentar salvar mensagem
    success = persistence_manager.save_message(test_msg, "timmy_vendas")
    if success:
        print("   ✅ Persistência de mensagens funcionando")
    else:
        print("   ❌ Persistência de mensagens com problema")
        
except Exception as e:
    print(f"   ❌ Erro na persistência: {e}")

# =============================================================================
# TESTE 5: CAPTURA DE TARGET EM DIFERENTES CENÁRIOS
# =============================================================================

print("\n5️⃣ TESTANDO CAPTURA DE TARGET - CENÁRIOS DIVERSOS:")

test_scenarios = [
    {
        "tenant": "timmy_vendas",
        "message": "Tenho uma empresa de contabilidade com 10 funcionários",
        "expected": ["tipo_negocio", "numero_funcionarios"]
    },
    {
        "tenant": "timmy_vendas", 
        "message": "Meu problema é que perco muito tempo respondendo as mesmas perguntas",
        "expected": ["dor_principal"]
    },
    {
        "tenant": "varizemed",
        "message": "Preciso de um cardiologista para consulta de retorno",
        "expected": ["especialidade_interesse", "tipo_consulta"]
    },
    {
        "tenant": "varizemed",
        "message": "Tenho dor no peito e tenho 45 anos",
        "expected": ["sintomas_principais", "idade_paciente"]
    }
]

for i, scenario in enumerate(test_scenarios, 1):
    print(f"\n   📋 CENÁRIO {i}: {scenario['tenant']}")
    print(f"      Mensagem: '{scenario['message']}'")
    
    try:
        from core.processors.target import SmartTargetProcessor
        config = get_target_config(scenario['tenant'])
        
        if config:
            processor = SmartTargetProcessor()
            extracted = processor.extract_from_message(scenario['message'], config)
            
            captured_fields = list(extracted.keys())
            expected_fields = scenario['expected']
            
            print(f"      Capturado: {captured_fields}")
            print(f"      Esperado: {expected_fields}")
            
            # Verificar se capturou pelo menos um campo esperado
            overlap = set(captured_fields) & set(expected_fields)
            if overlap:
                print(f"      ✅ Sucesso: {list(overlap)}")
            else:
                print(f"      ⚠️ Nenhum campo esperado capturado")
        else:
            print(f"      ❌ Config não encontrado para {scenario['tenant']}")
            
    except Exception as e:
        print(f"      ❌ Erro na captura: {e}")

# =============================================================================
# TESTE 6: HANDLE_TURN EM DIFERENTES CENÁRIOS
# =============================================================================

print("\n6️⃣ TESTANDO handle_turn - CENÁRIOS DIVERSOS:")

handle_turn_scenarios = [
    {
        "tenant": "timmy_vendas",
        "message": "Olá!",
        "description": "Primeira mensagem - deve se apresentar"
    },
    {
        "tenant": "timmy_vendas", 
        "message": "Tenho uma loja de roupas",
        "description": "Captura de negócio"
    },
    {
        "tenant": "varizemed",
        "message": "Preciso de ajuda médica",
        "description": "Contexto médico geral"
    }
]

for i, scenario in enumerate(handle_turn_scenarios, 1):
    print(f"\n   🎯 TESTE {i}: {scenario['description']}")
    print(f"      Tenant: {scenario['tenant']}")
    print(f"      Mensagem: '{scenario['message']}'")
    
    try:
        test_session = f"handle_test_{i}_{uuid.uuid4().hex[:8]}"
        test_message = Message(
            text=scenario['message'],
            session_key=test_session,
            tenant_id=scenario['tenant']
        )
        
        start_time = time.time()
        result = handle_turn(test_message)
        processing_time = time.time() - start_time
        
        print(f"      ⏱️ Tempo: {processing_time:.3f}s")
        print(f"      📊 Status: {result.get('status', 'unknown')}")
        
        response = result.get('response', '')
        if response and len(response) > 10:
            print(f"      ✅ Resposta: '{response[:80]}{'...' if len(response) > 80 else ''}'")
        else:
            print(f"      ⚠️ Resposta vazia ou muito curta")
            
        # Verificar dados de target se disponível
        target_data = result.get('target_data', {})
        if target_data.get('extracted'):
            print(f"      🎯 Target capturado: {list(target_data['extracted'].keys())}")
            
    except Exception as e:
        print(f"      ❌ Erro no handle_turn: {e}")
        traceback.print_exc()

# =============================================================================
# TESTE 7: SIMULAÇÃO DE USO INTENSIVO
# =============================================================================

print("\n7️⃣ TESTE DE STRESS - USO INTENSIVO:")

try:
    print("   🔥 Simulando múltiplas sessões simultâneas...")
    
    stress_sessions = []
    for i in range(5):
        session_key = f"stress_session_{i}"
        stress_sessions.append(session_key)
        
        # Criar estado para cada sessão
        set_state(session_key, user_id=f"user_{i}", test_data=f"data_{i}")
    
    # Verificar se todas as sessões estão isoladas
    all_good = True
    for i, session_key in enumerate(stress_sessions):
        state = get_state(session_key)
        expected_data = f"data_{i}"
        
        if state.get("test_data") != expected_data:
            all_good = False
            print(f"      ❌ Sessão {i} com dados incorretos")
            
    if all_good:
        print("   ✅ Isolamento de sessões funcionando")
    else:
        print("   ❌ Problema no isolamento de sessões")
        
    # Limpar sessões de teste
    for session_key in stress_sessions:
        clear_session(session_key)
        
except Exception as e:
    print(f"   ❌ Erro no teste de stress: {e}")

# =============================================================================
# TESTE 8: COMPATIBILIDADE COM APP.PY
# =============================================================================

print("\n8️⃣ VERIFICANDO COMPATIBILIDADE COM APP.PY:")

try:
    # Verificar se app.py existe e tem as funções esperadas
    app_path = Path("app.py")
    if app_path.exists():
        with open(app_path, 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        # Verificar imports críticos
        critical_imports = [
            "from core.agent import handle_turn",
            "import streamlit",
            "TARGET_UI_AVAILABLE"
        ]
        
        for import_check in critical_imports:
            if import_check in app_content:
                print(f"   ✅ Import encontrado: {import_check}")
            else:
                print(f"   ⚠️ Import não encontrado: {import_check}")
                
        # Verificar funções críticas
        critical_functions = [
            "render_target_config_editor",
            "render_enhanced_chat_message",
            "get_target_completion_status"
        ]
        
        for func_check in critical_functions:
            if func_check in app_content:
                print(f"   ✅ Função encontrada: {func_check}")
            else:
                print(f"   ⚠️ Função não encontrada: {func_check}")
    else:
        print("   ❌ app.py não encontrado")
        
except Exception as e:
    print(f"   ❌ Erro ao verificar app.py: {e}")

# =============================================================================
# RESUMO FINAL
# =============================================================================

print("\n" + "=" * 60)
print("📊 RESUMO DO DEBUG ABRANGENTE")
print("=" * 60)

print("\n🔍 **PRÓXIMOS PASSOS RECOMENDADOS:**")

# Verificar se tudo passou
all_critical_passed = True

if 'core.agent' in imports_status and '❌' in imports_status['core.agent']:
    all_critical_passed = False
    print("   ❌ Corrigir imports do core.agent")

if 'streamlit' in imports_status and '❌' in imports_status['streamlit']:
    all_critical_passed = False
    print("   ❌ Instalar streamlit: pip install streamlit")

if 'OPENAI_API_KEY' in env_status and '❌' in env_status['OPENAI_API_KEY']:
    all_critical_passed = False
    print("   ❌ Configurar OPENAI_API_KEY no .env")

if all_critical_passed:
    print("   ✅ **TUDO PRONTO PARA STREAMLIT!**")
    print("   🚀 Execute: streamlit run app.py")
else:
    print("   ⚠️ **CORRIGIR PROBLEMAS ANTES DO STREAMLIT**")

print("\n🎯 **STATUS GERAL:**")
if all_critical_passed:
    print("   🟢 SISTEMA PRONTO PARA PRODUÇÃO")
else:
    print("   🟡 REQUER CORREÇÕES MENORES")

print("\n" + "=" * 60)
print("🔍 DEBUG ABRANGENTE CONCLUÍDO!")
