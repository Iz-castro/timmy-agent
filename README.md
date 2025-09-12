# 🤖 Timmy-IA - Assistente Conversacional Multi-Tenant

> Plataforma de assistentes virtuais inteligentes com memória conversacional completa e estrutura organizada por cliente/tenant.

## 🚀 **Visão Geral**

O Timmy-IA é uma plataforma robusta para criação de assistentes conversacionais personalizados, com foco em:

- **🧠 Memória Conversacional Perfeita**: Relê toda a conversa antes de cada resposta
- **🏢 Arquitetura Multi-Tenant**: Dados completamente isolados por cliente
- **📁 Organização Inteligente**: Um arquivo CSV por conversa para máxima performance
- **💬 Micro-Responses**: Quebra semântica que preserva o sentido das mensagens
- **🔧 Workflows Customizáveis**: Suporte a fluxos específicos por tenant (médico, vendas, etc.)

---

## 📋 **Funcionalidades Principais**

### **🧠 Sistema de Memória Avançado**
- **Releitura Completa**: Analisa todo o histórico antes de responder
- **Contexto Preservado**: Nunca repete saudações ou perde informações
- **Coleta Passiva**: Extrai nome, email, telefone automaticamente
- **Persistência Estruturada**: Dados organizados por tenant com CSV por conversa

### **🏢 Multi-Tenant Nativo**
- **Isolamento Total**: Cada cliente tem seus próprios dados e configurações
- **Personalização Completa**: Persona, conhecimento e regras por tenant
- **Escalabilidade**: Adicione novos clientes sem afetar os existentes

### **📱 Interfaces Disponíveis**
- **Streamlit**: Interface web completa com dashboard
- **API REST**: Endpoints para integração externa
- **WhatsApp**: Suporte via Meta Cloud API (em desenvolvimento)

---

## 🏗️ **Arquitetura do Projeto**

```
Timmy_IA/
├── core/
│   ├── agent.py
│   ├── formatter.py
│   ├── llm.py
│   ├── persistence.py
│   └── utils.py
├── data/
├── tenants/
│   └── timmy_vendas/
│       ├── config.json
│       ├── examples.jsonl
│       └── knowledge.json
├── test/
├── app.py
└── requirements.txt
```

---

## ⚡ **Instalação Rápida**

### **1. Preparação do Ambiente**
```bash
# Clone o repositório
git clone https://github.com/seu-usuario/timmy-ia
cd timmy-ia

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instale dependências
pip install -r requirements.txt
```

### **2. Configuração**
```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o .env e adicione sua chave OpenAI
# OPENAI_API_KEY=sk-proj-sua_chave_aqui
# TIMMY_MODEL=gpt-4o-mini  # Modelo econômico
```

### **3. Execução**
```bash
# Execute a aplicação
streamlit run app.py

# Acesse: http://localhost:8501
```

---

## 💼 **Exemplo: Tenant Vendas**

### **Estratégia Consultiva**
O Timmy inclui um sistema de vendas consultivas que:

1. **Descobre o Negócio**: "Que tipo de negócio você tem?"
2. **Entende as Dores**: "Quanto tempo gasta com perguntas repetitivas?"
3. **Posiciona a Solução**: Recomenda plano baseado no perfil
4. **Gera Proposta**: Personalizada conforme necessidades

### **Planos Configuráveis**
```json
{
  "essencial": {
    "price": "R$ 750/mês",
    "conversations": "300 inclusas",
    "ideal_for": "Clínicas e comércios locais"
  },
  "profissional": {
    "price": "R$ 1.400/mês", 
    "conversations": "1.000 inclusas",
    "recommended": true
  }
}
```

---

## 🔧 **Criando Novo Tenant**

### **Via Código**
```python
from core.utils import create_tenant_structure

# Cria estrutura completa
create_tenant_structure("minha_empresa")
```

### **Estrutura Criada**
```
tenants/minha_empresa/
├── config.json        # Configurações básicas
├── knowledge.json     # Base de conhecimento
└── examples.jsonl     # Exemplos de conversa

data/minha_empresa/     # Criado automaticamente
├── conversations/     # CSVs das conversas
├── sessions/         # Dados das sessões
└── users/           # Dados dos usuários
```

### **Personalização**
```json
// tenants/minha_empresa/config.json
{
  "agent_name": "Sofia",
  "business_name": "Minha Empresa",
  "personality": {
    "tone": "descontraído e amigável",
    "style": "direto e divertido"
  }
}
```

---

## 📊 **Monitoramento e Analytics**

### **Dashboard Streamlit**
- ✅ Métricas por tenant (usuários, sessões, conversas)
- ✅ Estatísticas globais de todos os tenants
- ✅ Sessões ativas em tempo real
- ✅ Debug detalhado do processo

### **Métricas Disponíveis**
```python
from core.agent import get_data_stats

# Estatísticas de um tenant
stats = get_data_stats("varizemed")
print(f"Usuários: {stats['total_users']}")
print(f"Conversas: {stats['total_conversations']}")
print(f"Mensagens: {stats['total_messages']}")
```

### **Relatórios CSV**
- `conversations/`: Histórico completo por conversa
- `sessions/`: Dados de sessão e performance
- `users/`: Informações coletadas dos usuários

---

## 🔒 **Privacidade e Compliance**

### **Isolamento por Tenant**
- ✅ **Dados Separados**: Cada cliente em diretório próprio
- ✅ **Zero Cross-Contamination**: Impossível vazar dados entre tenants
- ✅ **Backup Seletivo**: Por cliente específico

### **LGPD/GDPR Ready**
- ✅ **Consentimento**: Coleta passiva e transparente
- ✅ **Portabilidade**: Dados em CSV padrão
- ✅ **Esquecimento**: Deleção completa por tenant
- ✅ **Auditoria**: Logs completos de todas as interações

### **Proteção no Git**
```gitignore
# Dados sensíveis NUNCA commitados
data/*/conversations/
data/*/sessions/
data/*/users/
*.csv
!**/template.csv
```

---

## 🚀 **Uso Programático**

### **Integração Simples**
```python
from core.agent import process_message

# Conversa via código
responses = process_message(
    text="Olá, me chamo João",
    tenant_id="varizemed"
)
print(responses)  # ['Olá João! Como posso ajudá-lo hoje?']

# WhatsApp (futuro)
responses = process_message(
    text="Quero agendar consulta",
    phone_number="+5511999999999",
    tenant_id="varizemed"
)
```

### **API REST (Roadmap)**
```bash
# Enviar mensagem
curl -X POST http://localhost:8000/tenants/varizemed/message \
  -H "Content-Type: application/json" \
  -d '{"text": "Olá", "phone": "+5511999999999"}'

# Buscar histórico
curl http://localhost:8000/tenants/varizemed/users/+5511999999999/history
```

---

## 🧪 **Testes e Validação**

### **Teste Básico**
```python
# Teste da memória conversacional
from core.agent import process_message

# Primeira mensagem
resp1 = process_message("Oi, me chamo Maria", tenant_id="default")
print(resp1)  # ["Oi Maria! Como posso ajudá-la?"]

# Segunda mensagem - deve lembrar do nome
resp2 = process_message("Você lembra meu nome?", tenant_id="default") 
print(resp2)  # ["Claro, seu nome é Maria!"]
```

### **Teste Multi-Tenant**
```python
# Tenant A
process_message("Sou João", tenant_id="clinica_a")

# Tenant B (dados isolados)
process_message("Sou João", tenant_id="clinica_b")
# Não há vazamento entre tenants
```

### **Validação de Workflow**
```python
# Teste workflow médico
responses = process_message(
    text="Tenho varizes nas pernas",
    tenant_id="varizemed"
)
# Deve classificar como Angiologia e sugerir médicos
```

---

## 🛠️ **Configurações Avançadas**

### **Modelos OpenAI**
```bash
# .env
TIMMY_MODEL=gpt-4o-mini     # Econômico (padrão)
TIMMY_MODEL=gpt-4o          # Mais avançado  
TIMMY_MODEL=gpt-3.5-turbo   # Mais rápido
```

### **Debug Mode**
```bash
# .env
DEBUG=true
```

### **Micro-Responses**
```python
# Personalização no core/utils.py
def micro_responses(text, min_chars=80, max_chars=120):
    # Quebra inteligente por:
    # 1. Sentenças completas
    # 2. Pausas naturais
    # 3. Conjunções
    # 4. Palavras (último recurso)
```

---

## 🎯 **Roadmap v3.0**

### **Próximas Funcionalidades**
- 🔗 **API REST Completa**: Endpoints para todas as operações
- 📱 **WhatsApp Nativo**: Integração direta com Meta Cloud API
- 📊 **Dashboard Avançado**: Analytics em tempo real
- 🌐 **Deploy Cloud**: Docker + Kubernetes ready
- 🔄 **Backup Automático**: Por tenant com agendamento
- 🎯 **A/B Testing**: Personas e estratégias por tenant

### **Melhorias de Performance**
- ⚡ **Cache Inteligente**: Conversas recentes em memória
- 🔄 **Streaming Responses**: Respostas em tempo real
- 🗜️ **Compressão**: Arquivos antigos otimizados
- 📊 **Métricas**: Latência e performance detalhadas

---

## ❓ **Troubleshooting**

### **Problemas Comuns**

**Erro: "Module not found"**
```bash
pip install -r requirements.txt
```

**Erro: "Invalid API Key"**
```bash
# Verifique no .env
OPENAI_API_KEY=sk-proj-sua_chave_real_aqui
```

**Conversas não aparecem**
1. Verifique se o tenant está selecionado corretamente
2. Confirme que as pastas `data/{tenant}/` foram criadas
3. Ative debug com `DEBUG=true`

**Performance lenta**
1. Use `gpt-4o-mini` para economia
2. Reduza `max_tokens` nas configurações
3. Implemente cache local se necessário

---

## 🤝 **Contribuindo**

### **Como Contribuir**
1. Fork o projeto
2. Crie feature branch: `git checkout -b feature/nova-funcionalidade`
3. Commit: `git commit -m 'feat: nova funcionalidade'`
4. Push: `git push origin feature/nova-funcionalidade`
5. Abra Pull Request

### **Padrões de Código**
- **Python**: PEP 8 + type hints
- **Commits**: Conventional Commits
- **Testes**: pytest para novas funcionalidades
- **Docs**: Markdown para documentação

---

## 📞 **Suporte**

### **Contato**
- **Desenvolvedor**: Izael Castro
- **Email**: izaeldecastro@egmail.com
- **LinkedIn**: [linkedin.com/in/izael-castro](https://linkedin.com/in/izael-castro)

---

## 📜 **Changelog**

### **v2.0.0 - Estrutura Multi-Tenant** *(Atual)*
- ✨ Sistema de dados organizado por tenant
- ✨ Arquivo separado por conversa (performance)
- ✨ Releitura completa da conversa (memória)
- ✨ Micro-responses inteligentes
- ✨ Workflows customizáveis por tipo de negócio
- ✨ Interface com estatísticas por tenant
- 💰 Migração para gpt-4o-mini (economia)

### **v1.0.0 - Base Funcional**
- 🎯 Conversação natural básica
- 📝 Coleta de informações
- 🧠 Base de conhecimento
- 📱 Interface Streamlit

---

## 📄 **Licença**

Este projeto está licenciado sob a [MIT License](LICENSE) - veja o arquivo LICENSE para detalhes.

---

<div align="center">

**🤖 Timmy-IA v2.0** - Sua plataforma completa para assistentes conversacionais multi-tenant!

*Criado com ❤️ por [Izael Castro](https://github.com/Iz-castro)*

</div>
