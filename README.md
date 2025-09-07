# 🤖 Timmy-IA v2.0 - Assistente Conversacional Multi-Tenant

Assistente virtual inteligente com memória conversacional perfeita, organizado por tenant com arquivos separados por conversa.

## 🚀 Funcionalidades Principais

- **🧠 Memória Conversacional Completa**: Relê toda a conversa antes de cada resposta
- **🏢 Multi-Tenant**: Suporte completo a múltiplos clientes com dados isolados
- **📁 Arquivo por Conversa**: Cada sessão gera um CSV separado para melhor performance
- **💬 Micro-responses Inteligentes**: Quebra semântica que preserva o sentido
- **📝 Coleta Automática**: Extrai informações como nome, email e telefone
- **🧠 Base de Conhecimento**: Responde com base em dados configuráveis por tenant
- **📱 Interface Web**: Interface Streamlit com estatísticas por tenant

## 📁 Nova Estrutura Organizada

```
timmy_IA/
├── app.py                      # Interface Streamlit atualizada
├── .env                        # Configurações (copie de .env.example)
├── requirements.txt            # Dependências Python
│
├── core/
│   ├── agent.py               # Sistema de releitura completa + multi-tenant
│   ├── utils.py               # Micro-responses inteligentes
│   └── persistence.py         # Estrutura de dados por tenant
│
├── data/                      # 🔒 Dados organizados por tenant
│   ├── default/              # Tenant padrão
│   │   ├── conversations/    # Um CSV por conversa
│   │   │   ├── conversation_streamlit_abc123.csv
│   │   │   └── conversation_phone_5511999999.csv
│   │   ├── sessions/         # Sessões do tenant
│   │   │   └── sessions.csv
│   │   └── users/           # Usuários do tenant
│   │       └── users.csv
│   ├── varizemed/           # Exemplo: tenant clínica médica
│   └── comercio_exemplo/    # Exemplo: tenant comércio
│
└── tenants/                  # Configurações por cliente
    ├── default/
    │   ├── config.json      # Configurações gerais
    │   ├── knowledge.json   # Base de conhecimento
    │   └── examples.jsonl   # Exemplos de conversa
    ├── varizemed/           # Configuração da clínica
    └── comercio_exemplo/    # Configuração do comércio
```

## ⚡ Instalação Rápida

### 1. **Clone e configure o ambiente:**
```bash
# Clone o projeto
git clone https://github.com/Iz-castro/timmy-agent
cd timmy-agent

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
# TIMMY_MODEL=gpt-4o-mini  # Modelo econômico (padrão)
```

### 4. **Execute a aplicação:**
```bash
streamlit run app.py
```

A aplicação estará disponível em: `http://localhost:8501`

## 🏢 Sistema Multi-Tenant

### **Criando um Novo Tenant**

```python
from core.utils import create_tenant_structure

# Cria estrutura completa para novo cliente
create_tenant_structure("minha_clinica")
```

Isso criará:
- `tenants/minha_clinica/` - Configurações
- `data/minha_clinica/` - Dados (criado automaticamente no primeiro uso)

### **Configuração do Tenant**

#### **`tenants/minha_clinica/config.json`**
```json
{
  "agent_name": "Dr. Assistant",
  "business_name": "Clínica Exemplo",
  "language": "pt-BR",
  "timezone": "America/Sao_Paulo",
  "personality": {
    "tone": "profissional e acolhedor",
    "style": "empático e cuidadoso",
    "emoji_usage": false
  }
}
```

#### **`tenants/minha_clinica/knowledge.json`**
```json
{
  "business_info": {
    "name": "Clínica Exemplo",
    "specialty": "Medicina Geral",
    "location": "São Paulo, SP"
  },
  "services": [
    {
      "name": "Consulta Geral",
      "description": "Consulta médica completa",
      "price": "R$ 150,00"
    }
  ],
  "faq": [
    {
      "question": "Como agendar consulta?",
      "answer": "Ligue para (11) 9999-9999 ou use nosso sistema online."
    }
  ]
}
```

## 🧠 Sistema de Memória Conversacional

### **Como Funciona:**
1. **Salva mensagem** do usuário
2. **Lê TODA a conversa** desde o início
3. **Analisa contexto** completo
4. **Responde** com base no histórico
5. **Salva resposta** no arquivo da conversa

### **Benefícios:**
- ✅ **Zero repetições** de saudações
- ✅ **Lembra de tudo** que foi dito
- ✅ **Conecta informações** entre mensagens
- ✅ **Personalidade consistente**

## 📊 Monitoramento e Analytics

### **Interface Streamlit:**
- **Métricas por tenant** - usuários, sessões, conversas
- **Estatísticas globais** - todos os tenants
- **Sessões ativas** - monitoramento em tempo real
- **Debug detalhado** - logs completos do processo

### **Via Código:**
```python
from core.agent import get_data_stats, get_all_tenants_stats

# Estatísticas de um tenant específico
stats = get_data_stats("minha_clinica")
print(f"Usuários: {stats['total_users']}")
print(f"Conversas: {stats['total_conversations']}")

# Estatísticas de todos os tenants
all_stats = get_all_tenants_stats()
print(f"Total de tenants: {all_stats['total_tenants']}")
```

## 💬 Como Usar

### **Interface Web:**
1. Acesse `http://localhost:8501`
2. Selecione o tenant na sidebar
3. Digite sua mensagem no chat
4. Converse naturalmente - o Timmy lembra de tudo!

### **Programaticamente:**
```python
from core.agent import process_message

# Mensagem simples
responses = process_message(
    text="Olá, me chamo João",
    tenant_id="minha_clinica"
)

# Com telefone (WhatsApp)
responses = process_message(
    text="Quero agendar consulta",
    phone_number="+5511999999999",
    tenant_id="minha_clinica"
)
```

## 🔒 Privacidade e Segurança

### **Isolamento por Tenant:**
- Dados completamente separados por cliente
- Estrutura de diretórios isolada
- Arquivos específicos por conversa

### **Proteção no Git:**
```gitignore
# Dados sensíveis nunca são commitados
data/*/conversations/
data/*/sessions/
data/*/users/
*.csv
```

### **Compliance:**
- **GDPR/LGPD Ready** - dados por cliente
- **Backup seletivo** - por tenant
- **Auditoria completa** - histórico preservado

## 🔧 Configurações Avançadas

### **Modelo OpenAI:**
```bash
# .env
TIMMY_MODEL=gpt-4o-mini     # Econômico (padrão)
TIMMY_MODEL=gpt-4o          # Mais avançado
TIMMY_MODEL=gpt-3.5-turbo   # Mais rápido
```

### **Debug Mode:**
```bash
# .env
DEBUG=true
```

### **Micro-responses:**
```python
# core/utils.py - Personalizar quebra de mensagens
def micro_responses(text, min_chars=80, max_chars=120):
    # Quebra inteligente por:
    # 1. Sentenças completas
    # 2. Pausas naturais 
    # 3. Conjunções
    # 4. Palavras
```

## 🧪 Testando

### **Teste Básico:**
```python
from core.agent import process_message

# Teste da memória conversacional
responses = process_message("Oi, me chamo Maria", tenant_id="default")
responses = process_message("Você lembra meu nome?", tenant_id="default")
# Resultado: "Sim, seu nome é Maria!"
```

### **Teste Multi-Tenant:**
```python
# Tenant 1
process_message("Sou João", tenant_id="clinica_a")

# Tenant 2 (dados isolados)
process_message("Sou João", tenant_id="clinica_b")
```

## 🚨 Troubleshooting

### **Erro: "Module not found"**
```bash
pip install -r requirements.txt
```

### **Erro: "Invalid API Key"**
```bash
# Verifique o .env
OPENAI_API_KEY=sk-proj-sua_chave_real_aqui
```

### **Erro: "Permission denied" em data/**
```bash
# Verifique permissões
chmod -R 755 data/
```

### **Conversas não aparecem:**
- Verifique se o tenant está selecionado corretamente
- Confirme que as pastas `data/{tenant}/` foram criadas
- Veja logs com `DEBUG=true`

## 🔮 Roadmap v3.0

### **Próximas Funcionalidades:**
- 🔗 **API REST** completa
- 📱 **WhatsApp/Telegram** nativos
- 🗄️ **Banco de dados** opcional
- 📊 **Dashboard analytics** avançado
- 🌐 **Deploy cloud** facilitado
- 🔄 **Backup automático** por tenant
- 🎯 **A/B testing** por tenant

### **Melhorias de Performance:**
- ⚡ **Cache inteligente** de conversas
- 🔄 **Streaming responses**
- 📊 **Métricas de performance**
- 🗜️ **Compressão** de dados antigos

## 📞 Suporte

### **Problemas?**
1. Confira este README
2. Verifique logs com `DEBUG=true`
3. Teste com tenant "default"
4. Abra issue no GitHub: [timmy-agent/issues](https://github.com/Iz-castro/timmy-agent/issues)

### **Contribuindo:**
1. Fork o projeto
2. Crie feature branch: `git checkout -b feature/nova-funcionalidade`
3. Commit: `git commit -m 'feat: nova funcionalidade'`
4. Push: `git push origin feature/nova-funcionalidade`
5. Abra Pull Request

## 📜 Changelog

### **v2.0.0 - Estrutura Multi-Tenant**
- ✨ Sistema de dados organizado por tenant
- ✨ Arquivo separado por conversa
- ✨ Releitura completa da conversa
- ✨ Micro-responses inteligentes
- ✨ Interface com estatísticas por tenant
- 💰 Migração para gpt-4o-mini (99% mais barato)

### **v1.0.0 - Base Funcional**
- 🎯 Conversação natural básica
- 📝 Coleta de informações
- 🧠 Base de conhecimento
- 📱 Interface Streamlit

---

**🤖 Timmy-IA v2.0** - Sua plataforma completa para assistentes conversacionais multi-tenant! 

*Criado com ❤️ por [Izael Castro](https://github.com/Iz-castro)*