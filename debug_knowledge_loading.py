#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug específico do carregamento de knowledge para timmy_vendas
Identifica por que os preços corretos não estão sendo usados
"""

import json
import traceback
from pathlib import Path

def debug_knowledge_loading():
    """Debug detalhado do carregamento de knowledge"""
    print("🔍 DEBUG CARREGAMENTO DE KNOWLEDGE")
    print("=" * 60)
    
    # 1. Verifica se arquivos existem
    print("\n1️⃣ VERIFICANDO ARQUIVOS:")
    
    config_path = Path("tenants/timmy_vendas/config.json")
    knowledge_path = Path("tenants/timmy_vendas/knowledge.json")
    examples_path = Path("tenants/timmy_vendas/examples.jsonl")
    
    print(f"   config.json: {'✅' if config_path.exists() else '❌'}")
    print(f"   knowledge.json: {'✅' if knowledge_path.exists() else '❌'}")
    print(f"   examples.jsonl: {'✅' if examples_path.exists() else '❌'}")
    
    if not knowledge_path.exists():
        print("❌ ERRO CRÍTICO: knowledge.json não encontrado!")
        return
    
    # 2. Carrega e analisa knowledge.json
    print("\n2️⃣ ANALISANDO KNOWLEDGE.JSON:")
    
    try:
        with open(knowledge_path, 'r', encoding='utf-8') as f:
            knowledge_data = json.load(f)
        
        print(f"   ✅ Knowledge carregado com sucesso")
        print(f"   📊 Chaves principais: {list(knowledge_data.keys())}")
        
        # Verifica se tem planos
        if "plans" in knowledge_data:
            plans = knowledge_data["plans"]
            print(f"   💼 Planos encontrados: {list(plans.keys())}")
            
            for plan_name, plan_data in plans.items():
                price = plan_data.get("price", "N/A")
                print(f"      • {plan_name}: {price}")
        else:
            print("   ❌ Não encontrou 'plans' no knowledge!")
            print(f"   📋 Chaves disponíveis: {list(knowledge_data.keys())}")
            
            # Verifica se está em business_info ou outro lugar
            for key, value in knowledge_data.items():
                if isinstance(value, dict) and "plans" in value:
                    print(f"   🔍 Encontrou 'plans' dentro de '{key}'!")
                    plans = value["plans"]
                    print(f"      Planos: {list(plans.keys())}")
                    for plan_name, plan_data in plans.items():
                        price = plan_data.get("price", "N/A")
                        print(f"         • {plan_name}: {price}")
    
    except Exception as e:
        print(f"   ❌ ERRO ao carregar knowledge.json: {e}")
        return
    
    # 3. Testa load_knowledge_data
    print("\n3️⃣ TESTANDO LOAD_KNOWLEDGE_DATA:")
    
    try:
        from core.utils import load_knowledge_data
        
        loaded_knowledge = load_knowledge_data("timmy_vendas")
        print(f"   ✅ load_knowledge_data executado")
        print(f"   📊 Chaves retornadas: {list(loaded_knowledge.keys())}")
        
        # Verifica como os planos aparecem na estrutura carregada
        if "knowledge_base" in loaded_knowledge:
            kb = loaded_knowledge["knowledge_base"]
            print(f"   📚 knowledge_base tem: {list(kb.keys()) if isinstance(kb, dict) else type(kb)}")
            
            if isinstance(kb, dict) and "plans" in kb:
                plans = kb["plans"]
                print(f"   💼 Planos na knowledge_base: {list(plans.keys())}")
            else:
                print("   ❌ Não encontrou 'plans' em knowledge_base")
        
        # Verifica se tem planos direto no root
        if "plans" in loaded_knowledge:
            plans = loaded_knowledge["plans"]
            print(f"   💼 Planos no root: {list(plans.keys())}")
        
    except Exception as e:
        print(f"   ❌ ERRO em load_knowledge_data: {e}")
        print(f"   📍 Traceback: {traceback.format_exc()}")
    
    # 4. Testa construção do prompt
    print("\n4️⃣ TESTANDO CONSTRUÇÃO DO PROMPT:")
    
    try:
        from core.agent import TimmyAgent
        
        agent = TimmyAgent("timmy_vendas")
        print(f"   ✅ TimmyAgent criado")
        print(f"   📚 Knowledge carregado: {'✅' if agent.knowledge else '❌'}")
        
        if agent.knowledge:
            # Simula prompt com contexto simples
            fake_context = "Usuário perguntou sobre preços"
            prompt = agent._build_system_prompt_with_full_context(fake_context)
            
            print(f"   📝 Prompt construído: {len(prompt)} caracteres")
            
            # Verifica se prompt contém preços corretos
            correct_prices = ["750", "1.400", "2.000", "3.500"]
            wrong_prices = ["200", "1.000"]
            
            has_correct = any(price in prompt for price in correct_prices)
            has_wrong = any(price in prompt for price in wrong_prices)
            
            print(f"   💰 Contém preços corretos: {'✅' if has_correct else '❌'}")
            print(f"   ⚠️ Contém preços errados: {'❌' if not has_wrong else '✅'}")
            
            # Mostra trecho do prompt com preços (se houver)
            lines = prompt.split('\n')
            for i, line in enumerate(lines):
                if any(price in line for price in correct_prices + wrong_prices):
                    print(f"      Linha {i+1}: {line[:100]}...")
        
    except Exception as e:
        print(f"   ❌ ERRO na construção do prompt: {e}")
        print(f"   📍 Traceback: {traceback.format_exc()}")
    
    # 5. Testa estratégia consultiva
    print("\n5️⃣ TESTANDO ESTRATÉGIA CONSULTIVA:")
    
    try:
        # Tenta importar estratégia
        import sys
        sys.path.append("tenants/timmy_vendas")
        
        from strategies.consultative_strategy import ConsultativeStrategy
        
        print("   ✅ ConsultativeStrategy importada")
        
        # Cria instância e testa
        strategy = ConsultativeStrategy()
        
        # Simula context com pergunta sobre preços
        from core.utils import get_state
        from core.agent import Message
        
        fake_message = Message(
            text="Quanto custam seus planos?",
            session_key="debug_session",
            tenant_id="timmy_vendas"
        )
        
        # Simula context básico
        class FakeContext:
            def __init__(self):
                self.session_key = "debug_session"
                self.tenant_id = "timmy_vendas"
                self.user_state = {"business_type": "loja_roupas"}
                self.conversation_history = []
        
        fake_context = FakeContext()
        
        # Testa se deve ativar
        should_activate = strategy.should_activate(fake_message, fake_context)
        print(f"   🎯 Estratégia deve ativar: {'✅' if should_activate else '❌'}")
        
        if should_activate:
            response = strategy.process_turn(fake_message, fake_context)
            print(f"   💬 Resposta da estratégia: {response[:100] if response else 'None'}...")
            
            # Verifica se resposta tem preços corretos
            if response:
                has_correct = any(price in response for price in ["750", "1.400", "2.000", "3.500"])
                print(f"   💰 Resposta tem preços corretos: {'✅' if has_correct else '❌'}")
        
    except ImportError as e:
        print(f"   ❌ ERRO ao importar estratégia: {e}")
    except Exception as e:
        print(f"   ❌ ERRO na estratégia consultiva: {e}")
        print(f"   📍 Traceback: {traceback.format_exc()}")

def main():
    """Função principal"""
    debug_knowledge_loading()

if __name__ == "__main__":
    main()
