# debug_integration_test.py
"""
Debug ESPECÍFICO para testar a integração entre app.py e os módulos
Simula exatamente o que o Streamlit faz para identificar onde está o problema
"""

import json
import uuid
import traceback
from pathlib import Path

print("🔍 DEBUG DE INTEGRAÇÃO - APP.PY vs MÓDULOS")
print("=" * 60)

# =============================================================================
# TESTE 1: SIMULAR IMPORTS DO APP.PY
# =============================================================================

print("\n1️⃣ TESTANDO IMPORTS EXATOS DO APP.PY:")

def test_app_imports():
    """Testa os mesmos imports que o app.py faz"""
    
    imports_status = {}
    
    # Imports principais que o app.py faz
    try:
        from core.agent import handle_turn, Message, get_user_history, get_data_stats, get_all_tenants_stats
        imports_status['core.agent - principais'] = "✅ OK"
    except Exception as e:
        imports_status['core.agent - principais'] = f"❌ ERRO: {e}"
        traceback.print_exc()
    
    try:
        from core.utils import get_state, clear_session, get_system_stats, list_sessions
        imports_status['core.utils'] = "✅ OK"
    except Exception as e:
        imports_status['core.utils'] = f"❌ ERRO: {e}"
    
    try:
        from core.persistence import persistence_manager
        imports_status['core.persistence'] = "✅ OK"
    except Exception as e:
        imports_status['core.persistence'] = f"❌ ERRO: {e}"
    
    # Imports da nova arquitetura (opcionais no app.py)
    try:
        from core.agent import get_extension_info, reload_tenant_extensions
        imports_status['nova arquitetura'] = "✅ OK"
    except Exception as e:
        imports_status['nova arquitetura'] = f"❌ ERRO: {e}"
    
    # Imports do sistema de target (opcionais no app.py)
    try:
        from core.processors.target import target_manager, get_target_config
        from core.agent import get_target_completion_status, setup_target_system_for_tenant
        imports_status['sistema target'] = "✅ OK"
    except Exception as e:
        imports_status['sistema target'] = f"❌ ERRO: {e}"
    
    for module, status in imports_status.items():
        print(f"   {module}: {status}")
    
    return imports_status

app_imports = test_app_imports()

# =============================================================================
# TESTE 2: SIMULAR EXATAMENTE O QUE O APP.PY FAZ
# =============================================================================

print("\n2️⃣ SIMULANDO COMPORTAMENTO EXATO DO APP.PY:")

def simulate_app_behavior():
    """Simula exatamente o que o app.py faz quando processa uma mensagem"""
    
    print("\n   🎭 Simulando: Usuário seleciona 'timmy_vendas' no app.py")
    tenant_id = "timmy_vendas"
    
    print("\n   🎭 Simulando: Usuário envia mensagem no chat")
    user_message = "Tenho uma loja de roupas femininas"
    
    print("\n   🎭 Simulando: app.py cria sessão")
    session_key = f"streamlit_{uuid.uuid4().hex[:8]}"
    
    print(f"   📊 Parâmetros simulados:")
    print(f"      • tenant_id: {tenant_id}")
    print(f"      • session_key: {session_key}")
    print(f"      • message: {user_message}")
    
    # Simula exatamente o que o app.py faz
    try:
        print("\n   🔄 Executando: Message(text=prompt, session_key=..., tenant_id=tenant_id)")
        from core.agent import Message, handle_turn
        
        message_obj = Message(text=user_message, session_key=session_key, tenant_id=tenant_id)
        print(f"      ✅ Message criado: {message_obj}")
        
        print("\n   🔄 Executando: handle_turn(message_obj)")
        result = handle_turn(message_obj)
        
        print(f"      ✅ handle_turn executado")
        print(f"      📊 Tipo do resultado: {type(result)}")
        print(f"      🔑 Chaves do resultado: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
        
        response = result.get("response", "Nenhuma resposta")
        status = result.get("status", "unknown")
        method = result.get("method", "unknown")
        target_data = result.get("target_data", {})
        
        print(f"\n   📝 ANÁLISE DA RESPOSTA:")
        print(f"      • Status: {status}")
        print(f"      • Method: {method}")
        print(f"      • Response: '{response[:100]}{'...' if len(response) > 100 else ''}'")
        
        # Verifica se a resposta contém informações de vendas
        response_lower = response.lower()
        sales_keywords = ["plano", "automatizar", "atendimento", "whatsapp", "sistema", "timmy", "preço", "valor"]
        has_sales_content = any(keyword in response_lower for keyword in sales_keywords)
        
        print(f"      • Contém conteúdo de vendas: {'✅' if has_sales_content else '❌'}")
        
        # Verifica dados de target
        if target_data:
            print(f"      • Target data: {target_data}")
        else:
            print(f"      • Target data: ❌ Nenhum dado capturado")
        
        return {
            "success": True,
            "response": response,
            "has_sales_content": has_sales_content,
            "target_data": target_data
        }
        
    except Exception as e:
        print(f"      ❌ ERRO na simulação: {e}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}

simulation_result = simulate_app_behavior()

# =============================================================================
# TESTE 3: VERIFICAR CARREGAMENTO DE CONHECIMENTO
# =============================================================================

print("\n3️⃣ VERIFICANDO CARREGAMENTO DE CONHECIMENTO:")

def test_knowledge_loading():
    """Testa se o sistema está carregando o conhecimento do timmy_vendas"""
    
    try:
        from core.utils import load_knowledge_data
        
        print("   🔄 Executando: load_knowledge_data('timmy_vendas')")
        knowledge = load_knowledge_data("timmy_vendas")
        
        if knowledge:
            print(f"   ✅ Knowledge carregado com sucesso")
            print(f"   🔑 Chaves disponíveis: {list(knowledge.keys())}")
            
            # Verifica planos específicos
            plans = knowledge.get("plans", {})
            if plans:
                print(f"   💼 Planos encontrados: {list(plans.keys())}")
                
                # Mostra preços
                for plan_name, plan_info in plans.items():
                    price = plan_info.get("price", "N/A")
                    print(f"      • {plan_name}: {price}")
            else:
                print(f"   ❌ PROBLEMA: Nenhum plano encontrado no knowledge!")
            
            # Verifica informações do negócio
            business_info = knowledge.get("business_info", {})
            if business_info:
                print(f"   🏢 Business info: {business_info.get('name', 'N/A')}")
            else:
                print(f"   ❌ PROBLEMA: Nenhuma informação de negócio encontrada!")
        else:
            print(f"   ❌ PROBLEMA CRÍTICO: Knowledge retornou vazio!")
            
            # Verifica se arquivos existem
            knowledge_file = Path("tenants/timmy_vendas/knowledge.json")
            if knowledge_file.exists():
                print(f"   📁 Arquivo knowledge.json existe")
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    raw_knowledge = json.load(f)
                print(f"   📊 Conteúdo raw: {len(raw_knowledge)} chaves")
            else:
                print(f"   ❌ PROBLEMA: Arquivo knowledge.json não existe!")
        
        return knowledge
        
    except Exception as e:
        print(f"   ❌ ERRO no carregamento de knowledge: {e}")
        traceback.print_exc()
        return None

knowledge_result = test_knowledge_loading()

# =============================================================================
# TESTE 4: VERIFICAR ESTRATÉGIA CONSULTIVA
# =============================================================================

print("\n4️⃣ VERIFICANDO ESTRATÉGIA CONSULTIVA:")

def test_consultative_strategy():
    """Testa se a estratégia consultiva está sendo chamada"""
    
    try:
        from core.conversation_strategy import process_consultative_turn
        print("   ✅ Módulo de estratégia consultiva importado")
        
        test_session = f"consultive_test_{uuid.uuid4().hex[:8]}"
        test_message = "Tenho uma empresa de contabilidade"
        
        print(f"   🔄 Testando: process_consultative_turn('timmy_vendas', '{test_message}', '{test_session}')")
        
        result = process_consultative_turn("timmy_vendas", test_message, test_session)
        
        if result:
            print(f"   ✅ Estratégia consultiva FUNCIONANDO")
            print(f"   📝 Resposta: '{result[:100]}{'...' if len(result) > 100 else ''}'")
            
            # Verifica se menciona planos
            result_lower = result.lower()
            mentions_plans = any(plan in result_lower for plan in ["essencial", "profissional", "premium", "enterprise"])
            mentions_prices = any(price in result_lower for price in ["750", "1.400", "2.000", "3.500"])
            
            print(f"   💼 Menciona planos: {'✅' if mentions_plans else '❌'}")
            print(f"   💰 Menciona preços: {'✅' if mentions_prices else '❌'}")
            
            return True
        else:
            print(f"   ❌ PROBLEMA: Estratégia consultiva não gerou resposta")
            return False
            
    except ImportError as e:
        print(f"   ❌ PROBLEMA: Módulo de estratégia consultiva não encontrado: {e}")
        return False
    except Exception as e:
        print(f"   ❌ ERRO na estratégia consultiva: {e}")
        traceback.print_exc()
        return False

consultive_result = test_consultative_strategy()

# =============================================================================
# TESTE 5: VERIFICAR FLUXO COMPLETO DE PROCESSAMENTO
# =============================================================================

print("\n5️⃣ VERIFICANDO FLUXO COMPLETO DE PROCESSAMENTO:")

def test_complete_processing_flow():
    """Testa cada etapa do processamento para identificar onde está o problema"""
    
    session_key = f"flow_test_{uuid.uuid4().hex[:8]}"
    user_message = "Preciso automatizar meu negócio"
    tenant_id = "timmy_vendas"
    
    try:
        from core.agent import (
            process_target_capture, 
            analyze_enhanced_context,
            check_consultative_strategy,
            process_with_legacy_system,
            build_enhanced_prompt
        )
        
        print(f"   🔄 ETAPA 1: process_target_capture")
        target_data = process_target_capture(user_message, session_key, tenant_id)
        print(f"      Resultado: {target_data}")
        
        print(f"   🔄 ETAPA 2: load_knowledge_data")
        from core.utils import load_knowledge_data
        agent_data = load_knowledge_data(tenant_id)
        print(f"      Tem knowledge: {'✅' if agent_data else '❌'}")
        print(f"      Tem planos: {'✅' if agent_data and agent_data.get('plans') else '❌'}")
        
        print(f"   🔄 ETAPA 3: analyze_enhanced_context")
        context_analysis = analyze_enhanced_context(user_message, session_key, tenant_id, target_data)
        print(f"      Context keys: {list(context_analysis.keys()) if context_analysis else '❌'}")
        
        print(f"   🔄 ETAPA 4: check_consultative_strategy")
        consultive_response = check_consultative_strategy(user_message, session_key, tenant_id, context_analysis)
        print(f"      Consultive response: {'✅' if consultive_response else '❌'}")
        if consultive_response:
            print(f"      Preview: '{consultive_response[:80]}...'")
        
        if not consultive_response:
            print(f"   🔄 ETAPA 5: process_with_legacy_system (fallback)")
            legacy_result = process_with_legacy_system(user_message, session_key, tenant_id, agent_data, context_analysis)
            print(f"      Legacy result: {legacy_result.get('status', 'unknown')}")
            print(f"      Response: '{legacy_result.get('response', 'N/A')[:80]}...'")
        
        return {
            "target_data": bool(target_data),
            "agent_data": bool(agent_data),
            "consultive_response": bool(consultive_response)
        }
        
    except Exception as e:
        print(f"   ❌ ERRO no fluxo de processamento: {e}")
        traceback.print_exc()
        return None

flow_result = test_complete_processing_flow()

# =============================================================================
# TESTE 6: VERIFICAR PROMPT BUILDING
# =============================================================================

print("\n6️⃣ VERIFICANDO CONSTRUÇÃO DE PROMPTS:")

def test_prompt_building():
    """Verifica se os prompts estão sendo construídos com as informações corretas"""
    
    try:
        from core.agent import build_enhanced_prompt, analyze_enhanced_context
        from core.utils import load_knowledge_data
        
        session_key = f"prompt_test_{uuid.uuid4().hex[:8]}"
        user_message = "Quanto custam seus planos?"
        tenant_id = "timmy_vendas"
        
        # Carrega dados necessários
        agent_data = load_knowledge_data(tenant_id)
        context_analysis = analyze_enhanced_context(user_message, session_key, tenant_id, {})
        
        print(f"   🔄 Construindo prompt para: '{user_message}'")
        prompt = build_enhanced_prompt(user_message, agent_data, context_analysis, session_key, tenant_id)
        
        if prompt:
            print(f"   ✅ Prompt construído ({len(prompt)} caracteres)")
            
            # Verifica se contém informações de vendas
            prompt_lower = prompt.lower()
            
            checks = {
                "Contém planos": any(plan in prompt_lower for plan in ["essencial", "profissional", "premium", "enterprise"]),
                "Contém preços": any(price in prompt_lower for price in ["750", "1.400", "2.000", "3.500"]),
                "Contém 'timmy'": "timmy" in prompt_lower,
                "Contém conhecimento": "conhecimento disponível" in prompt_lower,
                "Contém instruções de vendas": "vendas" in prompt_lower or "consultiv" in prompt_lower
            }
            
            for check_name, result in checks.items():
                print(f"      • {check_name}: {'✅' if result else '❌'}")
            
            # Mostra uma amostra do prompt
            print(f"\n   📝 AMOSTRA DO PROMPT:")
            lines = prompt.split('\n')
            for i, line in enumerate(lines[:10]):  # Primeiras 10 linhas
                print(f"      {i+1:2d}: {line[:80]}{'...' if len(line) > 80 else ''}")
            
            if len(lines) > 10:
                print(f"      ... (+{len(lines)-10} linhas)")
        else:
            print(f"   ❌ PROBLEMA: Prompt não foi construído!")
        
        return bool(prompt)
        
    except Exception as e:
        print(f"   ❌ ERRO na construção de prompt: {e}")
        traceback.print_exc()
        return False

prompt_result = test_prompt_building()

# =============================================================================
# RESUMO FINAL E DIAGNÓSTICO
# =============================================================================

print("\n" + "=" * 60)
print("📊 DIAGNÓSTICO FINAL - INTEGRAÇÃO APP.PY")
print("=" * 60)

def generate_integration_diagnosis():
    """Gera diagnóstico final baseado nos testes"""
    
    print(f"\n🔍 **RESULTADOS DOS TESTES:**")
    
    # Status dos imports
    critical_imports = ['core.agent - principais', 'core.utils', 'core.persistence']
    imports_ok = all('✅' in app_imports.get(imp, '') for imp in critical_imports)
    print(f"   • Imports críticos: {'✅' if imports_ok else '❌'}")
    
    # Status da simulação
    simulation_ok = simulation_result.get("success", False)
    has_sales = simulation_result.get("has_sales_content", False)
    print(f"   • Simulação app.py: {'✅' if simulation_ok else '❌'}")
    print(f"   • Conteúdo de vendas: {'✅' if has_sales else '❌'}")
    
    # Status do knowledge
    knowledge_ok = knowledge_result is not None and bool(knowledge_result)
    print(f"   • Carregamento knowledge: {'✅' if knowledge_ok else '❌'}")
    
    # Status consultivo
    print(f"   • Estratégia consultiva: {'✅' if consultive_result else '❌'}")
    
    # Status do fluxo
    if flow_result:
        flow_ok = all(flow_result.values())
        print(f"   • Fluxo completo: {'✅' if flow_ok else '❌'}")
    
    # Status do prompt
    print(f"   • Construção de prompt: {'✅' if prompt_result else '❌'}")
    
    print(f"\n🎯 **DIAGNÓSTICO:**")
    
    if not imports_ok:
        print(f"   🚨 PROBLEMA CRÍTICO: Imports fundamentais falhando")
        print(f"      → Verifique se os arquivos core/agent.py e core/utils.py estão corretos")
    
    elif not knowledge_ok:
        print(f"   🚨 PROBLEMA CRÍTICO: Knowledge não está sendo carregado")
        print(f"      → Verifique tenants/timmy_vendas/knowledge.json")
        print(f"      → Verifique função load_knowledge_data() em core/utils.py")
    
    elif not consultive_result:
        print(f"   🚨 PROBLEMA: Estratégia consultiva não funciona")
        print(f"      → Verifique core/conversation_strategy.py")
        print(f"      → Verifique integração em check_consultative_strategy()")
    
    elif simulation_ok and not has_sales:
        print(f"   🚨 PROBLEMA: Sistema funciona mas não faz vendas")
        print(f"      → Knowledge carrega mas não chega ao LLM")
        print(f"      → Verifique build_enhanced_prompt()")
    
    else:
        print(f"   ✅ SISTEMA DEVERIA ESTAR FUNCIONANDO")
        print(f"      → Se app.py não funciona, pode ser problema de interface")
        print(f"      → Teste diretamente no terminal com o debug")
    
    print(f"\n🔧 **PRÓXIMOS PASSOS:**")
    print(f"   1. Corrija os problemas identificados acima")
    print(f"   2. Execute este debug novamente")
    print(f"   3. Só então teste no streamlit")

generate_integration_diagnosis()

print("\n" + "=" * 60)
print("🔍 DEBUG DE INTEGRAÇÃO CONCLUÍDO!")