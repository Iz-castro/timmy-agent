# debug_test.py - Script para identificar problemas específicos
"""
Script de debug para identificar problemas no sistema de target
"""

import traceback
import json
from pathlib import Path

print("🔍 INICIANDO DEBUG DETALHADO")
print("=" * 50)

# 1. Verificar imports básicos
print("\n1️⃣ VERIFICANDO IMPORTS:")
try:
    from core.agent import Message, handle_turn
    print("✅ core.agent imports OK")
except Exception as e:
    print(f"❌ Erro no core.agent: {e}")
    traceback.print_exc()

try:
    from core.processors.target import target_manager
    print("✅ target_manager import OK")
except Exception as e:
    print(f"❌ Erro no target_manager: {e}")
    traceback.print_exc()

try:
    from core.persistence import ConversationMessage, persistence_manager
    print("✅ persistence imports OK")
except Exception as e:
    print(f"❌ Erro no persistence: {e}")
    traceback.print_exc()

# 2. Verificar estrutura de ConversationMessage
print("\n2️⃣ VERIFICANDO ConversationMessage:")
try:
    from core.persistence import ConversationMessage
    import inspect
    
    # Mostrar assinatura do __init__
    signature = inspect.signature(ConversationMessage.__init__)
    print(f"ConversationMessage.__init__ signature: {signature}")
    
    # Tentar criar uma instância
    test_msg = ConversationMessage(
        message_id="test",
        session_id="test_session",
        user_id=None,
        timestamp="2024-01-01T00:00:00",
        role="user",
        content="test message"
    )
    print("✅ ConversationMessage criado com sucesso")
    print(f"   Campos: {list(test_msg.__dict__.keys())}")
    
except Exception as e:
    print(f"❌ Erro no ConversationMessage: {e}")
    traceback.print_exc()

# 3. Verificar função chat_complete
print("\n3️⃣ VERIFICANDO FUNÇÃO chat_complete:")
try:
    from core.utils import chat_complete
    
    # Tentar chamar com prompt simples
    test_prompt = "Olá, como você está?"
    print(f"Testando prompt: '{test_prompt}'")
    
    result = chat_complete(test_prompt, "default")
    print(f"✅ chat_complete funcionou")
    print(f"   Tipo do resultado: {type(result)}")
    print(f"   Resultado (primeiros 100 chars): {str(result)[:100]}...")
    
except Exception as e:
    print(f"❌ Erro no chat_complete: {e}")
    traceback.print_exc()

# 4. Verificar micro_responses
print("\n4️⃣ VERIFICANDO FUNÇÃO micro_responses:")
try:
    from core.utils import micro_responses
    
    test_text = "Esta é uma mensagem de teste para verificar se a função micro_responses está funcionando corretamente."
    result = micro_responses(test_text, session_key="test_session")
    
    print(f"✅ micro_responses funcionou")
    print(f"   Tipo do resultado: {type(result)}")
    print(f"   Resultado: {result}")
    
except Exception as e:
    print(f"❌ Erro no micro_responses: {e}")
    traceback.print_exc()

# 5. Teste específico do target
print("\n5️⃣ TESTANDO SISTEMA DE TARGET:")
try:
    from core.processors.target import get_target_config, SmartTargetProcessor
    
    # Testar config do timmy_vendas
    config = get_target_config("timmy_vendas")
    if config:
        print(f"✅ Config encontrado para timmy_vendas: {config.target_name}")
        print(f"   Campos: {[f.field_name for f in config.fields]}")
        
        # Testar processador
        processor = SmartTargetProcessor()
        test_message = "Tenho uma empresa de contabilidade com 5 funcionários"
        extracted = processor.extract_from_message(test_message, config)
        
        print(f"✅ Extração testada")
        print(f"   Dados extraídos: {extracted}")
    else:
        print("❌ Config não encontrado para timmy_vendas")
        
except Exception as e:
    print(f"❌ Erro no sistema de target: {e}")
    traceback.print_exc()

# 6. Teste completo de handle_turn
print("\n6️⃣ TESTE COMPLETO handle_turn:")
try:
    from core.agent import Message, handle_turn
    
    test_message = Message(
        text="Olá, teste",
        session_key="debug_session",
        tenant_id="timmy_vendas"
    )
    
    print(f"Testando handle_turn com: {test_message}")
    result = handle_turn(test_message)
    
    print(f"✅ handle_turn completou")
    print(f"   Status: {result.get('status')}")
    print(f"   Response: {result.get('response', '')[:100]}...")
    print(f"   Erros: {result.get('error', 'Nenhum')}")
    
except Exception as e:
    print(f"❌ Erro no handle_turn: {e}")
    traceback.print_exc()

# 7. Verificar arquivos de configuração
print("\n7️⃣ VERIFICANDO ARQUIVOS DE CONFIG:")

configs_to_check = [
    "tenants/timmy_vendas/config.json",
    "tenants/timmy_vendas/target_config.json", 
    "tenants/varizemed/config.json",
    "tenants/varizemed/target_config.json"
]

for config_file in configs_to_check:
    path = Path(config_file)
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            print(f"✅ {config_file}: OK ({len(content)} chaves)")
        except Exception as e:
            print(f"❌ {config_file}: Erro JSON - {e}")
    else:
        print(f"⚠️ {config_file}: Arquivo não existe")

print("\n" + "=" * 50)
print("🔍 DEBUG COMPLETO!")
