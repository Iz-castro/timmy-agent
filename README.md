# 🤖 Timmy-IA - Assistente Conversacional

Assistente virtual inteligente que conversa naturalmente, coleta informações e responde com base em conhecimento configurável.

## 🚀 Funcionalidades Principais

- **💬 Conversação Natural**: Dialoga de forma inteligente e contextual
- **📝 Coleta Automática**: Extrai informações como nome, email e telefone
- **🧠 Base de Conhecimento**: Responde com base em dados configurados
- **💾 Memória de Sessão**: Mantém contexto durante toda a conversa
- **🏢 Multi-tenant**: Suporte a múltiplos clientes/configurações
- **📱 Interface Web**: Interface Streamlit pronta para uso

## 📁 Estrutura do Projeto

```
timmy_IA/
├── app.py                    # Interface Streamlit
├── .env                      # Configurações (copie de .env.example)
├── requirements.txt          # Dependências Python
│
├── core/
│   ├── agent.py             # Cérebro principal do agente
│   └── utils.py             # Utilitários e ferramentas
│
└── tenants/
    └── default/             # Configuração padrão
        ├── config.json      # Configurações gerais
        ├── knowledge.json   # Base de conhecimento
        └── examples.jsonl   # Exemplos de conversa
```

## ⚡ Instalação Rápida

### 1. **Clone e configure o ambiente:**
```bash
# Clone o projeto
git clone <seu-repositorio>
cd timmy_IA

# Crie ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 2. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

### 3. **Configure as variáveis de ambiente:**
```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o .env e adicione sua chave da OpenAI
# OPENAI_API_KEY=sk-proj-sua_chave_aqui
```

### 4. **Execute a aplicação:**
```bash
streamlit run app.py
```

A aplicação estará disponível em: `http://localhost:8501`

## 🔧 Configuração Detalhada

### **Variáveis de Ambiente (.env)**

```bash
# OpenAI (OBRIGATÓRIO)
OPENAI_API_KEY=sk-proj-sua_chave_aqui

# Modelo (opcional, padrão: gpt-4o-mini)
TIMMY_MODEL=gpt-4o-mini

# Debug (opcional)
DEBUG=false
```

### **Estrutura de Tenant**

Cada tenant (cliente) tem sua própria configuração:

#### **config.json** - Configurações gerais
```json
{
  "agent_name": "Timmy",
  "business_name": "Sua Empresa",
  "language": "pt-BR",
  "personality": {
    "tone": "profissional e cordial",
    "style": "direto e empático"
  }
}
```

#### **knowledge.json** - Base de conhecimento
```json
{
  "business_info": {
    "name": "Sua Empresa",
    "description": "Descrição da empresa"
  },
  "services": [...],
  "faq": [...],
  "contact": {...}
}
```

#### **examples.jsonl** - Exemplos de conversa
```jsonl
{"role": "user", "content": "Olá!"}
{"role": "assistant", "content": "Olá! Como posso ajudar?"}
```

## 📖 Como Usar

### **Interface Streamlit**

1. **Acesse** `http://localhost:8501`
2. **Selecione** o tenant na sidebar
3. **Digite** sua mensagem no chat
4. **Converse** naturalmente com o Timmy

### **Programaticamente**

```python
from core.agent import process_message

# Mensagem simples
responses = process_message("Olá, meu nome é João")
print(responses)  # ['Olá João! Como posso ajudar você hoje?']

# Com sessão específica
responses = process_message(
    text="Quais serviços vocês oferecem?",
    session_key="minha_sessao_123",
    tenant_id="default"
)
```

## 🛠️ Personalização

### **Criar Novo Tenant**

```python
from core.utils import create_tenant_structure

# Cria estrutura para novo cliente
create_tenant_structure("meu_cliente")
```

### **Modificar Personalidade**

Edite `tenants/seu_tenant/config.json`:

```json
{
  "agent_name": "Maria",
  "business_name": "Clínica Exemplo",
  "personality": {
    "tone": "amigável e acolhedor",
    "style": "informal e carinhoso",
    "emoji_usage": true
  }
}
```

### **Adicionar Conhecimento**

Edite `tenants/seu_tenant/knowledge.json`:

```json
{
  "services": [
    {
      "name": "Novo Serviço",
      "description": "Descrição detalhada",
      "price": "R$ 100,00"
    }
  ]
}
```

## 🧪 Testando

### **Teste Básico**
```python
# Execute no terminal Python
from core.agent import process_message

# Teste simples
result = process_message("Olá!")
print(result)
```

### **Teste com Debug**
```bash
# Configure DEBUG=true no .env
DEBUG=true streamlit run app.py
```

## 📊 Monitoramento

### **Estatísticas em Tempo Real**

- **Sessões ativas**: Quantas conversas simultâneas
- **Estado das sessões**: Informações coletadas de cada usuário
- **Cache de tenants**: Configurações carregadas

### **Logs**

```python
from core.utils import get_system_stats

stats = get_system_stats()
print(stats)
# {
#   "active_sessions": 3,
#   "cached_tenants": 1,
#   "session_keys": ["session_abc123", ...]
# }
```

## 🚨 Troubleshooting

### **Erro: "Module not found"**
```bash
# Certifique-se de estar no diretório correto
cd timmy_IA

# Verifique se as dependências estão instaladas
pip install -r requirements.txt
```

### **Erro: "Invalid API Key"**
```bash
# Verifique se a chave OpenAI está correta no .env
OPENAI_API_KEY=sk-proj-sua_chave_aqui
```

### **Resposta estranha do agente**
- Verifique o arquivo `knowledge.json` do tenant
- Adicione exemplos específicos no `examples.jsonl`
- Ajuste a personalidade no `config.json`

## 🔮 Próximos Passos

Esta é a **versão básica funcional**. Para expandir:

1. **API REST** - Para integração com outros sistemas
2. **WhatsApp/Telegram** - Conectores para mensageria
3. **Banco de dados** - Persistência de conversas
4. **Analytics** - Métricas e relatórios
5. **Multi-modelo** - Suporte a outros LLMs

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique este README
2. Confira os logs de erro
3. Teste com `DEBUG=true`
4. Abra uma issue no repositório

---

**Timmy-IA v1.0** - Sua base sólida para assistentes conversacionais! 🚀