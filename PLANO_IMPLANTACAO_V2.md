# Plano de Implantação ICP Ideal - V2
**Data:** 07/03/2026 | **Status:** Em execução

---

## 📋 Visão Geral

Sistema de coleta e funil de leads para eventos presenciais (constelação familiar, sistêmica, terapia familiar).

**Arquitetura:**
- Backend: FastAPI + Celery + PostgreSQL
- Frontend: React + Vite + TailwindCSS
- Coleta: Instagram (instagrapi) + YouTube (yt-dlp)
- Enriquecimento: Análise de dados, scoring, detecção de gênero

---

## ✅ FASE 1: Core funcional (CONCLUÍDO)

- [x] Containers Docker (backend, worker, beat, frontend, db, redis)
- [x] Modelos: Lead, SearchJob, LeadEvent, AppSettings
- [x] Coleta YouTube (comentários em vídeos)
- [x] Coleta Instagram (posts em hashtags) - com session-based login
- [x] Enriquecimento de leads (scoring, categorização)
- [x] API REST completa (CRUD leads, jobs, exports)
- [x] Frontend responsivo (Dashboard, Lista, Perfil, Busca, Configurações)
- [x] Paginação (50 leads/página)
- [x] Histórico de jobs de busca

---

## 🔧 FASE 2: Melhorias imediatas (A FAZER)

### 2.1 - Aba LEADS: Campos adicionais
**Prioridade:** ALTA | **Ordem:** 1
**O que:**
- Campo de cidade: Dropdown dinâmico (apenas cidades com leads)
- Data da mensagem capturada (quando post/comentário foi feito)
- Identificação do criador/canal (quem fez o post, não o lead)
- Campo de gênero: Confiança ✅F/M/ND ou aproximado ⚠️?_F/?_M/?_ND
  - Lógica: Nome + foto + análise de comentários
  - Documentação: F=100%, ?_F=~70%, ND=sem dados

**Arquivos a modificar:**
- `backend/app/models/lead.py` → Adicionar `gender`, `gender_confidence`, `message_date`, `creator_profile`
- `backend/app/schemas/lead.py` → Atualizar LeadOut
- `backend/app/tasks/enrichment.py` → Implementar lógica de gênero
- `frontend/src/components/FilterBar.jsx` → Dropdown dinâmico de cidades, select de gênero
- `frontend/src/pages/LeadList.jsx` → Novos campos na tabela
- `frontend/src/pages/LeadProfile.jsx` → Mostrar todos os campos

**Dependências:** Nenhuma

**Tempo estimado:** 3-4 horas

---

### 2.2 - Mini-Dashboard na aba BUSCA
**Prioridade:** ALTA | **Ordem:** 2
**O que:**
- Exibição em tempo real do progresso de cada job (keyword × cidade)
- Barra de progresso: `leads_found / estimado_total`
- Status individual: ⏳ Rodando, 📋 Na fila, ✅ Concluído, ❌ Erro
- Resumo geral: X/9 rodando, Y/9 na fila, tempo estimado
- Quando termina: Vira "histórico condensado" + relatório detalhado

**Arquivos a modificar:**
- `backend/app/models/search_job.py` → Adicionar `progress_percent`, `estimated_completion`
- `backend/app/api/search.py` → GET /search retorna progresso
- `frontend/src/pages/SearchPage.jsx` → Novo componente `SearchProgressDashboard`
- `frontend/src/api/client.js` → Adaptar fetchSearchJobs para progresso

**Dependências:** Nenhuma

**Tempo estimado:** 2-3 horas

---

### 2.3 - Tratamento de erros + Retry inteligente
**Prioridade:** ALTA | **Ordem:** 3
**O que:**
- Job com erro → move para fim da fila + aguarda intervalo configurável (padrão 15 min)
- Relatório de erro: Mensagem + detalhes técnicos + stack trace
- Estados: ERRO_AGUARDANDO, ERRO_PAUSADO, AGUARDANDO_RETRY, ERRO_PERMANENTE
- Controles: Pausar, Reexecutar agora, Ver detalhes
- Máximo 2 tentativas (1ª automática, 2ª manual se falhar)
- Campo em Configurações: "Intervalo de retry (minutos)" - configurável

**Arquivos a modificar:**
- `backend/app/models/search_job.py` → Adicionar status, error_message, error_details, error_count, retry_after_timestamp
- `backend/app/tasks/search.py` → Implementar lógica de retry + rate limiting
- `backend/app/api/search.py` → Endpoints para pausar/reexecutar
- `backend/app/core/config.py` → Adicionar RETRY_INTERVAL_MINUTES
- `frontend/src/pages/SearchPage.jsx` → UI para pausar/reexecutar
- `frontend/src/components/JobStatusBadge.jsx` → Novo componente para status de erro

**Dependências:** 2.2 (precisa saber status do job)

**Tempo estimado:** 3 horas

---

## 🎯 FASE 3: Busca por localização (A FAZER)

### 3.1 - Busca com múltiplas cidades (Lista Negativa)
**Prioridade:** ALTA | **Ordem:** 4
**O que:**
- Campo de cidades: Input com tags (flexível, qualquer cidade)
- Cidades obrigatórias para busca
- Para cada keyword × cidade → 1 SearchJob separado (9 jobs para 3×3)
- LISTA NEGATIVA: Antes de nova busca, verifica base existente
  - Ignora usernames já capturados
  - Campo em Configurações: "Intervalo de expurgo (dias)" - reset da lista
- Rate limiting: 2-3 jobs rodando simultâneos (Celery rate_limit)

**Arquivos a modificar:**
- `backend/app/models/search_job.py` → Adicionar `city`, `is_negative_list_used`
- `backend/app/schemas/lead.py` → SearchJobCreate recebe `cities: list[str]`
- `backend/app/api/search.py` → POST /search cria N jobs (1 por city)
- `backend/app/tasks/search.py` → Integrar lista negativa + ajustar keywords ("keyword city")
- `backend/app/core/config.py` → EXPURGE_INTERVAL_DAYS
- `frontend/src/pages/SearchPage.jsx` → Campo de cidades com tags
- `frontend/src/pages/Settings.jsx` → Intervalo de expurgo

**Dependências:** 2.2, 2.3

**Tempo estimado:** 4 horas

---

## 🔐 FASE 4: Ética + Segurança (A FAZER - POST MVP)

### 4.1 - Estratégia orgânica de contato
**Prioridade:** CRÍTICA | **Ordem:** 5 (depois que MVP rodar)
**O que:**
- Validação: Lead só é contatado se:
  a) Já segue perfil @edmilsoquesada_constelacao, OU
  b) Comentou em post do perfil oficial, OU
  c) Está em grupo/comunidade gerenciada
- Como saber se segue: Integração com Instagram API (profile_follows_list)
- App separado (Telegram/WhatsApp bot): Opt-in voluntário para funil
- Documentação: Política de privacidade + termo de contato

**Arquivos a criar:**
- `backend/app/tasks/contact_eligibility.py` → Lógica de validação
- `backend/app/integrations/telegram_bot.py` (futura) → Bot independente
- `docs/ETHICAL_STRATEGY.md` → Documentação

**Dependências:** MVP funcionando, decisão sobre infraestrutura de contato

**Tempo estimado:** 5-6 horas (incluindo setup do bot)

---

## 🤖 FASE 5: Funil de conversão (POST MVP)

### 5.1 - Jornada do lead
**Prioridade:** MÉDIA | **Ordem:** 6
**O que:**
- Estados: PENDING → CONTACTED → HOT/WARM/COLD → CUSTOMER → LOYAL
- Automações:
  - Reminder: 7 dias sem resposta → tentar novamente
  - 1 semana antes evento → enviar convite
  - Pós-evento → feedback + next event
- Integração: Email, WhatsApp (futura)
- Dashboard: Conversão por funil (% hot, % customer, etc)

**Arquivos:**
- `backend/app/models/lead.py` → status expansion, lifecycle tracking
- `backend/app/tasks/funnel.py` → Automações
- `frontend/src/pages/FunnelDashboard.jsx` → Visualização

**Dependências:** 4.1 (estratégia ética)

**Tempo estimado:** 6-8 horas

---

## 📊 Ordem de execução segura

```
SEMANA 1:
  └─ 2.1 (Campos LEADS) ✓ Independente, prepara dados
     └─ 2.2 (Mini-Dashboard) ✓ Depende de 2.1 (campos)
        └─ 2.3 (Retry inteligente) ✓ Depende de 2.2 (status)

SEMANA 2:
  └─ 3.1 (Busca + cidades) ✓ Depende de 2.3 (reliability)
     └─ Testes completos com lista negativa

SEMANA 3+:
  └─ 4.1 (Ética) ✓ Requer decisão + setup
     └─ 5.1 (Funil) ✓ Requer 4.1

TOTAL: ~28-36 horas de desenvolvimento
```

---

## ⚡ Quick wins para hoje

- [x] Corrigir bugs do Tailwind v4 ✓
- [x] Paginação 50/página ✓
- [x] Histórico de jobs ✓
- [x] Loading states ✓
- [x] Toast notifications ✓

---

## 🎬 Próximas ações (Modo Produção)

1. ✅ **Retomar login Instagram** (cooldown terminou ~16h)
2. ✅ **Testar coleta YouTube** com novos parâmetros
3. ➡️ **Iniciar FASE 2.1** (Campos LEADS)

---

## 📝 Notas

- Instagram scraper: Avaliar usar conta separada (não profissional) para reduzir risco
- Gênero: Começar conservador (só marcar ✅ se 100% confiante)
- Lista negativa: Implementar com cuidado no collector (performance)
- Ética: Nunca contatar sem validação orgânica (4.1)
