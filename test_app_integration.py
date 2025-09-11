#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste Rápido de Integração App.py
Verifica se o app.py funcionará com a nova arquitetura
"""

import sys
import traceback
from pathlib import Path

print("🔍 TESTE RÁPIDO DE INTEGRAÇÃO APP.PY")
print("=" * 60)

def test_imports():
    """Testa imports principais do app.py"""
    print("\n1️⃣ TESTANDO IMPORTS:")
    
    try:
        from core.agent import handle_turn, Message
        print("   ✅ core.agent - principais: OK")
    except ImportError as e:
        print(f"   ❌ core.agent - ERRO: {e}")
        return False
    
    try:
        from core.utils import get_state, clear_session, list_sessions
        print("   ✅ core.utils - principais: OK")
    except ImportError as e:
        print(f"   ❌ core.utils - ERRO: {e}")
        return False
    
    try:
        from core.persistence import persistence_manager
        print("   ✅ core.persistence: OK")
    except ImportError as e:
        print(f"   ❌ core.persistence - ERRO: {e}")
        return False
    
    return True

def test_basic_functionality():
    """Testa funcionalidade básica"""
    print("\n2️⃣ TESTANDO FUNCIONALIDADE BÁSICA:")
    
    try:
        # Importa depois dos testes de import
        from core.agent import handle_turn, Message
        from core.utils import get_state
        from core.persistence import persistence_manager
        
        # Teste 1: Criar Message
        message = Message(
            text="Olá, sou um teste",
            session_key="test_session_123",
            tenant_id="timmy_vendas"
        )
        print(f"   ✅ Message criado: {message.text[:30]}...")
        
        # Teste 2: Chamar handle_turn
        result = handle_turn(message)
        print(f"   ✅ handle_turn executado - Tipo: {type(result)}")
        
        # Teste 3: Verificar resultado
        if isinstance(result, dict):
            response = result.get('response', 'No response')
            print(f"   ✅ Resposta: {response[:50]}...")
        elif isinstance(result, list):
            response = ' '.join(result) if result else 'No response'
            print(f"   ✅ Resposta (lista): {response[:50]}...")
        else:
            print(f"   ⚠️ Tipo de resposta inesperado: {type(result)}")
        
        # Teste 4: Verificar estado
        state = get_state("test_session_123")
        print(f"   ✅ Estado da sessão: {type(state)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
        print(f"   📍 Traceback: {traceback.format_exc()}")
        return False

def test_tenant_info():
    """Testa carregamento de informações do tenant"""
    print("\n3️⃣ TESTANDO INFORMAÇÕES DO TENANT:")
    
    try:
        import json
        
        # Testa tenants disponíveis
        tenants_dir = Path("tenants")
        if tenants_dir.exists():
            tenants = []
            for item in tenants_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('__'):
                    tenants.append(item.name)
            print(f"   ✅ Tenants encontrados: {tenants}")
            
            # Testa carregamento de config
            for tenant in tenants[:2]:  # Testa apenas os 2 primeiros
                config_path = Path(f"tenants/{tenant}/config.json")
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        agent_name = config.get("agent_name", tenant.title())
                        business = config.get("business_name", "Empresa")
                        print(f"   ✅ {tenant}: {agent_name} - {business}")
                else:
                    print(f"   ⚠️ {tenant}: Sem config.json")
        else:
            print("   ❌ Diretório tenants não encontrado")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
        return False

def test_stats():
    """Testa sistema de estatísticas"""
    print("\n4️⃣ TESTANDO SISTEMA DE ESTATÍSTICAS:")
    
    try:
        from core.persistence import persistence_manager
        
        # Testa stats do tenant
        stats = persistence_manager.get_tenant_stats("timmy_vendas")
        print(f"   ✅ Stats timmy_vendas: {stats}")
        
        # Testa stats globais
        global_stats = persistence_manager.get_all_tenants_stats()
        print(f"   ✅ Stats globais: {type(global_stats)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
        return False

def main():
    """Função principal"""
    print("Iniciando testes de integração...\n")
    
    # Lista de testes
    tests = [
        ("Imports", test_imports),
        ("Funcionalidade Básica", test_basic_functionality),
        ("Informações do Tenant", test_tenant_info),
        ("Sistema de Estatísticas", test_stats)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ ERRO CRÍTICO em {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES:")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 RESULTADO FINAL: {passed}/{len(tests)} testes passaram")
    
    if passed == len(tests):
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ O app.py deve funcionar perfeitamente")
        print("\n💡 PRÓXIMOS PASSOS:")
        print("   1. Execute: streamlit run app.py")
        print("   2. Teste a interface no navegador")
        print("   3. Se houver problemas, execute este script novamente")
    else:
        print("\n⚠️ ALGUNS TESTES FALHARAM!")
        print("❌ Corrija os problemas antes de executar o app.py")
        print("\n🔧 SUGESTÕES:")
        print("   1. Verifique se todos os módulos estão atualizados")
        print("   2. Confirme que não há erros de sintaxe")
        print("   3. Execute o debug_integration_test.py original")

if __name__ == "__main__":
    main()
