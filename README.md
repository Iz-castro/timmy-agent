# 🤖 Timmy IA - Agente Conversacional Multi-Tenant

**Plataforma de agentes de IA para atendimento ao cliente com memória ativa e abordagem consultiva**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-green.svg)](https://openai.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ **Principais Características**

### 🧠 **Memória Ativa Robusta**
- **Context Window Completo**: Toda conversa enviada para LLM sempre
- **Extração Automática**: Nome, negócio, problemas e volume de atendimento
- **Persistência Temporal**: Dados salvos com timestamps para auditoria
- **Reconhecimento Inteligente**: Padrões aprimorados para capturar informações

### 🔍 **Descoberta Consultiva**
- **Abordagem Estruturada**: Nome → Negócio → Problemas → Volume
- **Priorização Automática**: Identifica informações faltantes e foca no essencial
- **Perguntas Contextuais**: Sistema sugere a pergunta certa no momento certo
- **Flexibilidade Inteligente**: Atende demandas diretas mas retoma consultoria

### 🚫 **Anti-Alucinação**
- **Políticas Obrigatórias**: Nunca inventa informações sobre pagamento ou condições
- **Fallbacks Seguros**: "Consulte nosso comercial" quando não souber
- **Knowledge Base**: Dados estruturados e validados por tenant
- **Validação Contínua**: Verifica informações antes de responder

### 📱 **Formatação WhatsApp Nativa**
- **Conversão Automática**: `**bold**` → `*bold*` (formato WhatsApp)
- **Configuração Flexível**: Formatado, texto limpo ou personalizado
- **Micro-mensagens**: Respostas divididas em chunks de 200 caracteres
- **Emojis Contextuais**: Uso inteligente baseado no conteúdo

---

## 🏗️ **Arquitetura**

### **Separação Core vs Tenants**

```
Timmy_IA/
├── core/                    # 🔧 Funcionalidades genéricas
│   ├── agent.py            # Orquestrador principal
│   ├── llm.py              # Interface com OpenAI
│   ├── formatter.py        # Sistema de formatação
│   ├── persistence.py      # Persistência multi-tenant
│   └── utils.py            # Utilitários compartilhados
├── tenants/                 # 🎯 Configurações específicas
│   └── timmy_vendas/
│       ├── config.json     # Personalidade e comportamento
│       ├── knowledge.json  # Base de conhecimento
│       └── examples.jsonl  # Exemplos de treinamento
├── data/                    # 📁 Dados por tenant
│   └── tenants/<tenant_id>/
│       ├── conversations/  # Histórico de conversas
│       ├── sessions/       # Estados de sessão
│       └── users/          # Perfis de usuários
└── app.py                  # 🖥️ Interface Streamlit
```

### **Responsabilidades**

**Core (Agnóstico):**
- ✅ Processamento de mensagens
- ✅ Memória ativa e persistência
- ✅ Formatação configurável
- ✅ Interface com LLM

**Tenants (Específico):**
- 🎯 Personalidade e tom
- 🎯 Base de conhecimento
- 🎯 Regras de negócio
- 🎯 Políticas e procedimentos

---

## 🚀 **Instalação e Configuração**

### **1. Clone o Repositório**
```bash
git clone https://github.com/Iz-castro/timmy-agent.git
cd timmy-agent
```

### **2. Instale Dependências**
```bash
pip install -r requirements.txt
```

### **3. Configure Variáveis de Ambiente**
```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Configure sua API key da OpenAI
OPENAI_API_KEY=sk-your-api-key-here
TIMMY_MODEL=gpt-4o-mini
DEBUG=True
```

### **4. Execute a Aplicação**
```bash
streamlit run app.py
```

---

## 🎯 **Como Usar**

### **Interface Streamlit**
1. Acesse `http://localhost:8501`
2. Selecione o tenant (ex: `timmy_vendas`)
3. Digite uma mensagem no chat
4. Observe a memória ativa e descoberta consultiva em ação

### **API Programática**
```python
from core.agent import handle_turn

# Processamento simples
responses = handle_turn(
    tenant_id="timmy_vendas",
    session_key="user_123",
    user_text="Olá, sou João e tenho uma loja de roupas"
)

print(responses)
# ['Bom dia, João! Prazer em conhecê-lo...']
```

---

## 📊 **Funcionalidades da Memória**

### **Dados Extraídos Automaticamente:**
- **Nome do Cliente**: Padrões como "me chamo", "sou o", "nome é"
- **Área de Negócio**: "trabalho com", "tenho uma", "minha empresa"
- **Problemas Identificados**: "problema com", "dificuldade em", "demora muito"
- **Volume de Atendimento**: "X conversas por mês", "cerca de X clientes"
- **Preferências**: Canal, estilo de comunicação, urgência
- **Fatos Importantes**: "não tenho", "meu amigo", "preciso de"

### **Análise Consultiva:**
```json
{
  "conversation_phase": "discovery_basic",
  "missing_basic_info": ["nome", "tipo_negocio"],
  "discovery_priority": "🔥 URGENTE: Pergunte o nome do cliente",
  "detected_intent": "discovery_needed"
}
```

---

## ⚙️ **Configuração de Tenant**

### **config.json**
```json
{
  "agent_name": "Timmy",
  "business_name": "Timmy IA",
  "personality": {
    "tone": "consultivo e genuinamente interessado",
    "style": "descoberta ativa, escuta primeiro",
    "approach": "consultoria especializada"
  },
  "formatter": {
    "whatsapp_formatting": true,
    "max_chars": 200,
    "use_emojis": true
  },
  "system_instructions": "ESTRATÉGIA CONSULTIVA OBRIGATÓRIA: Sempre priorize descobrir nome, negócio e problemas ANTES de apresentar soluções..."
}
```

### **knowledge.json**
```json
{
  "business_info": {
    "name": "Timmy IA",
    "value_proposition": "Automatize 80% do atendimento"
  },
  "plans": {
    "essencial": {
      "name": "Essencial",
      "price": "R$ 750/mês",
      "features": ["WhatsApp", "CRM próprio"]
    }
  },
  "policies": {
    "payment": {
      "methods": ["Consulte nosso comercial"],
      "billing_cycle": "Mensal"
    }
  }
}
```

---

## 🧪 **Testes e Exemplos**

### **Teste de Memória Ativa**
```
👤 Usuário: "Oi, sou João, trabalho com açaí"
🤖 Timmy: "Prazer, João! Que legal que trabalha com açaí..."

👤 Usuário: "Esqueceu meu nome?"
🤖 Timmy: "Claro que não, João! Você trabalha com açaí..."
```

### **Teste de Descoberta Consultiva**
```
👤 Usuário: "Quero saber os preços"
🤖 Timmy: "Claro! Mas antes, qual seu nome e tipo de negócio?"
🤖 Timmy: [Após descoberta] "Perfeito, João! Para seu negócio de açaí, recomendo..."
```

### **Teste de Anti-Alucinação**
```
👤 Usuário: "Como posso pagar?"
🤖 Timmy: "Para informações sobre formas de pagamento, entre em contato com nosso comercial."
```

---

## 📈 **Métricas e Analytics**

### **Dados Coletados por Tenant:**
- **Total de Conversas**: Número de sessões únicas
- **Total de Mensagens**: Volume de interações
- **Taxa de Descoberta**: % de conversas com nome/negócio identificados
- **Tempo Médio de Sessão**: Duração das conversas
- **Fases de Conversa**: Distribuição por descoberta/consultoria/venda

### **Arquivos de Dados:**
```
data/tenants/timmy_vendas/
├── conversations/
│   ├── joão__session_123.csv      # Nome amigável
│   └── maria__session_456.csv
├── sessions/
│   ├── session_123.json           # Estado da sessão
│   └── session_456.json
└── users/
    ├── joão.json                  # Perfil do usuário
    └── maria.json
```

---

## 🔧 **Desenvolvimento**

### **Adicionando Novo Tenant**
```python
from core.utils import create_tenant_structure

# Cria estrutura completa
create_tenant_structure("novo_cliente")

# Customiza config.json e knowledge.json
# Testa com app.py
```

### **Executando Testes**
```bash
pytest test/ -v
```

### **Estrutura de Commits**
```bash
git commit -m "feat: nova funcionalidade"
git commit -m "fix: correção de bug"
git commit -m "docs: atualização de documentação"
```

---

## 🛣️ **Roadmap**

### **v1.1 - Atual ✅**
- [x] Memória ativa robusta
- [x] Descoberta consultiva
- [x] Anti-alucinação
- [x] Formatação WhatsApp

### **v1.2 - Próximo**
- [ ] Integração WhatsApp Business API
- [ ] Dashboard de analytics
- [ ] API REST completa
- [ ] Webhook para notificações

### **v1.3 - Futuro**
- [ ] Suporte a múltiplos idiomas
- [ ] Integração com CRMs externos
- [ ] IA de sentimento
- [ ] Relatórios automatizados

---

## 🤝 **Contribuição**

### **Como Contribuir:**
1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'feat: adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

### **Diretrizes:**
- Mantenha o core agnóstico
- Funcionalidades específicas vão em tenants/
- Adicione testes para novas funcionalidades
- Documente mudanças no README

---

## 📝 **Licença**

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 👥 **Contato**

**Desenvolvedor**: Izael Castro  
**Email**: [izaeldecastrol@gmail.com]  
**GitHub**: [@Iz-castro](https://github.com/Iz-castro)  
**Projeto**: [timmy-agent](https://github.com/Iz-castro/timmy-agent)

---

## 🙏 **Agradecimentos**

- **Comunidade Python** pelas ferramentas excelentes

---

*⚡ Criado com ❤️ para revolucionar o atendimento ao cliente com IA*
