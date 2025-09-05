# Estrutura Simplificada - Timmy/Val

## 📁 Nova Estrutura Proposta (Simples e Funcional)

```
timmy_IA/
├── app.py                    # 🎯 Streamlit runner (mantém como está)
├── .env                      # 🔑 Configurações
├── requirements.txt          # 📦 Dependências
│
├── core/
│  ├── agent.py              # 🧠 TUDO: lógica principal, captura, contexto, LLM
│  └── utils.py              # 🛠️ Micro-respostas, session store, loaders
│
├── apps/
│  ├── api.py                # 🔗 FastAPI completa (todos endpoints)
│  └── webhook.py            # 📞 Twilio/WhatsApp/outros canais
│
└── tenants/
   └── varizemed/            # 🏥 Configuração do cliente (mantém como está)
      ├── config.json        # ⚙️ Configurações gerais
      ├── knowledge.json     # 📚 Catálogo + KB unificado
      └── examples.jsonl     # 💬 Few-shots
```

## 🎯 **Filosofia da Simplificação**

### **3 Arquivos Principais:**
1. **`core/agent.py`** - Todo o cérebro em um lugar
2. **`core/utils.py`** - Todas as utilidades em um lugar  
3. **`apps/api.py`** - Toda a API em um lugar

### **Vantagens:**
- ✅ **Menos arquivos** = Menos confusão
- ✅ **Lógica concentrada** = Mais fácil de debuggar
- ✅ **Imports simples** = Menos problemas de dependência
- ✅ **Manutenção fácil** = Tudo relacionado está junto

## 📋 **Detalhamento dos Arquivos**

### **1. core/agent.py** (O Cérebro - ~300 linhas)
```python
# CONTÉM TUDO:
# - Classe Message
# - Função handle_turn (lógica principal)
# - Captura passiva (extract_name, normalize_*)
# - Análise contextual (perguntas específicas)
# - Prompt building
# - Chamadas LLM
# - Lógica de fluxo completa
```

### **2. core/utils.py** (Utilitários - ~200 linhas)
```python
# CONTÉM:
# - Session store (get, set_state, mark_once)
# - Micro-respostas (quebra natural de texto)
# - Loaders (load_tenant_*)
# - Cliente OpenAI
# - Funções auxiliares
```

### **3. apps/api.py** (API Completa - ~150 linhas)
```python
# CONTÉM:
# - FastAPI app
# - Todos os endpoints (/health, /webhooks/*, /tenants/*)
# - Tratamento de erros
# - Documentação automática
```

### **4. apps/webhook.py** (Canais - ~100 linhas)
```python
# CONTÉM:
# - Twilio WhatsApp
# - Meta WhatsApp (futuro)
# - Telegram (futuro)
# - Outros canais
```

## 🔄 **Migração da Estrutura Atual**

### **Consolidação:**
```
core/orchestrator/agent.py + 
core/orchestrator/collector.py + 
core/orchestrator/contextual_analyzer.py
→ core/agent.py

core/llm/* + core/rag/loaders.py + core/state/*
→ core/utils.py

apps/api/main.py + apps/api/twilio_webhook.py
→ apps/api.py + apps/webhook.py
```

## 📊 **Comparação: Antes vs Depois**

### **ANTES (Atual):**
- 📁 **20+ arquivos** espalhados
- 🔗 **10+ imports** cruzados
- 🐛 **Complexo** de debuggar
- ⚠️ **Difícil** de manter

### **DEPOIS (Proposto):**
- 📁 **4 arquivos** principais
- 🔗 **3 imports** simples
- ✅ **Fácil** de debuggar
- 🛠️ **Simples** de manter

## 🎯 **Lógica de Funcionamento Simplificada**

### **Fluxo Principal:**
```python
# app.py (Streamlit)
from core.agent import handle_turn, Message

# core/agent.py
from core.utils import micro_responses, load_tenant_knowledge, get_state

# Tudo funciona com 2 imports apenas!
```

### **Responsabilidades Claras:**
- **`core/agent.py`** = "O que fazer" (lógica de negócio)
- **`core/utils.py`** = "Como fazer" (ferramentas)
- **`apps/*.py`** = "Onde expor" (interfaces)

## 🚀 **Próximos Passos**

1. **Consolidar arquivos** existentes nos 4 novos
2. **Testar funcionalidade** completa
3. **Limpar estrutura** antiga
4. **Documentar** o novo fluxo

## 💡 **Benefícios Imediatos**

- 🔍 **Debug simples**: problema no agent? Arquivo único
- 📝 **Manutenção fácil**: mudança na lógica? Um lugar só
- 🚀 **Deploy simplificado**: menos arquivos = menos problemas
- 👥 **Onboarding rápido**: nova pessoa entende em minutos

---

**Essa estrutura elimina a complexidade desnecessária e mantém toda a funcionalidade que construímos, mas de forma muito mais simples e manutenível.**