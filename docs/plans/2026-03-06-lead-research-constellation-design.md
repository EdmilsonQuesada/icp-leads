# Design: App de Pesquisa e Qualificação de Leads — Constelação Familiar

**Data:** 2026-03-06
**Status:** Aprovado
**Autor:** Edmilson (uso pessoal)

---

## Objetivo

Ferramenta de uso pessoal para descobrir, qualificar e monitorar potenciais clientes (pessoas que consomem conteúdo de constelação familiar) no Instagram e YouTube, com enriquecimento de perfil via Facebook e LinkedIn. Pipeline completo: descoberta → monitoramento 7-15 dias → contato direto ou exportação.

---

## Arquitetura

**Stack:** Python (FastAPI) + Celery + Redis + PostgreSQL + React
**Infraestrutura:** Docker Compose (roda local)

```
┌─────────────────────────────────────────────────┐
│                  FRONTEND (React)                │
│  Dashboard · Lista de Leads · Perfil · Export    │
└────────────────────┬────────────────────────────┘
                     │ HTTP REST
┌────────────────────▼────────────────────────────┐
│               BACKEND (FastAPI)                  │
│  /leads · /search · /monitor · /export          │
└────┬──────────────────────────┬─────────────────┘
     │                          │
┌────▼────────┐        ┌────────▼────────┐
│   Celery    │        │   PostgreSQL     │
│  Workers   │        │  leads, events,  │
│  + Redis   │        │  scores, history │
└────┬────────┘        └─────────────────┘
     │
┌────▼──────────────────────────────┐
│         Coletores (Workers)        │
│  Instagram · YouTube · FB · LI    │
└───────────────────────────────────┘
```

---

## Fontes de Dados

### Instagram
| Fonte | Método | Dados coletados |
|-------|--------|-----------------|
| Perfis | `instagrapi` (scraping autenticado) | Bio, seguidores, localização, contato |
| Postagens & Reels | `instagrapi` | Legenda, hashtags, curtidas, comentários |
| Comentários | `instagrapi` | Texto, autor, data |
| Busca por hashtag | `instagrapi` | Posts de keywords de constelação |

**Anti-bloqueio:** delay aleatório 3-8s, conta autenticada, limite de requests por sessão.

### YouTube
| Fonte | Método | Dados coletados |
|-------|--------|-----------------|
| Busca de vídeos | YouTube Data API v3 | Título, canal, views, likes |
| Comentários | YouTube Data API v3 | Texto, autor, data, likes |
| Vídeos longos | `yt-dlp` + Whisper/legenda | Transcrição completa para análise |
| Perfil comentarista | YouTube Data API v3 | Canal, inscritos, histórico público |

### Enriquecimento Demográfico (Idade / Aniversário)
| Fonte | Método | Dados buscados |
|-------|--------|----------------|
| Instagram | Monitoramento de posts + bio | Menção de aniversário, faixa etária por linguagem |
| YouTube | Comentários + "sobre" do canal | Data de nascimento mencionada |
| Facebook | Scraping de perfil público | Data de nascimento, idade, cidade |
| LinkedIn | Scraping autenticado (conservador) | Data de nascimento, cidade, faixa etária |

**Estratégia:** busca pelo mesmo @usuario ou nome completo nas outras redes, confirmação por similaridade de foto de perfil.

> **Nota LinkedIn:** proteção agressiva contra scraping. Coleta limitada a perfis públicos com rate limiting conservador e sessão autenticada.

---

## Keywords de Busca (configuráveis)

- `constelação familiar`
- `constelação sistêmica`
- `Bert Hellinger`
- `ordem do amor`
- `alma família`
- `representante constelação`
- `campo mórfico`

---

## Qualificação e Score (0–100)

| Dimensão | Peso | Sinais |
|----------|------|--------|
| **Engajamento** | 40% | Frequência de curtidas/comentários em posts de constelação, recência, variedade de criadores |
| **Intenção** | 35% | Palavras-chave: "quero sessão", "como funciona", "preciso de ajuda", "onde encontro", perguntas diretas |
| **Perfil Demográfico** | 25% | Localização (BR preferencial), conta pessoal, bio com termos de espiritualidade/terapia |

### Classificação

| Score | Categoria | Ação sugerida |
|-------|-----------|---------------|
| 75–100 | 🔥 Lead Quente | Contato direto em até 48h |
| 50–74 | 🌤 Lead Morno | Monitorar + contato após 7 dias |
| 25–49 | ❄️ Lead Frio | Monitorar 15 dias, reavaliar |
| 0–24 | 🗑 Descarte | Remove da fila |

### Reavaliação durante monitoramento
- Novo comentário em post de constelação → +5 pts
- Comentário com palavra de intenção → +15 pts
- Inatividade por 7 dias → -10 pts
- Score sobe de categoria → notificação no painel

---

## Ciclo de Vida do Lead

```
[Descoberto]
     ↓
[Enriquecimento inicial]
  · Coleta perfil completo (IG, YT, FB, LI)
  · Score inicial calculado
  · Categoria definida
     ↓
[Monitoramento ativo] ← Celery Beat (1x por dia)
  · Verifica novos comentários/curtidas
  · Detecta post de aniversário
  · Atualiza score e timeline
     ↓
[Condição de saída]
  · Score ≥ 75 → notifica "pronto para contato"
  · 15 dias sem evolução → arquiva
  · Marcado como Contatado → sai da fila
```

---

## Agendamento (Celery Beat)

| Frequência | Tarefa |
|------------|--------|
| A cada 1h | Processa fila de novos leads pendentes |
| A cada 24h | Roda monitoramento de todos os leads ativos |
| A cada 7d | Reavalia leads frios (arquivar ou manter) |

---

## Interface Web (React)

### Dashboard
- Contadores por categoria (Quente / Morno / Frio)
- Leads prontos para contato hoje
- Monitoramentos ativos

### Lista de Leads
- Foto, @usuario, score, fonte, ação (Ver / DM)
- Filtros: Fonte · Categoria · Data · Localização · Aniversário próximo

### Perfil do Lead
- Dados: @usuario, score, cidade, bio, seguidores
- Timeline de eventos dos últimos N dias
- Botões: Enviar DM · Marcar como Contatado · Exportar

### Notificações
| Gatilho | Mensagem |
|---------|----------|
| Lead vira Quente | 🔥 "@usuario agora é lead quente (87 pts)" |
| Comentário com intenção | 💬 "@usuario perguntou: 'como faço sessão?'" |
| Aniversário detectado/próximo | 🎂 "@usuario faz aniversário em 3 dias" |
| Leads inativos | ⚠️ "N leads sem atividade — revisar" |

---

## Exportação

**Formatos:** CSV, Excel
**Campos:** nome, @usuario, link perfil, score, categoria, fonte, cidade, idade, data de nascimento, primeiro evento, último evento, comentários capturados

---

## Configurações do Usuário

- Período de monitoramento por categoria (padrão: Quente=7d, Morno=10d, Frio=15d)
- Keywords customizáveis
- Horário preferido para coletas (ex: 3h da manhã)
- Limite diário de novos leads coletados

---

## Modelo de Dados (simplificado)

```
leads
  id, username, platform, display_name, bio
  city, country, followers, account_type
  age, birthdate, birthdate_source
  score, category, status
  created_at, last_monitored_at, contacted_at

lead_events
  id, lead_id, event_type, description
  score_delta, score_after, created_at

search_jobs
  id, keywords, platforms, status
  leads_found, created_at, finished_at
```

---

## Restrições e Riscos

| Risco | Mitigação |
|-------|-----------|
| Bloqueio por rate limit (IG/LI) | Delays aleatórios, sessões autenticadas, limites configuráveis |
| Violação de ToS das plataformas | Uso pessoal, volume baixo, sem revenda de dados |
| Dados demográficos incompletos | Campo vazio é válido; enriquecimento é melhor-esforço |
| LinkedIn scraping frágil | Módulo isolado com fallback gracioso (sem dados = sem erro) |
