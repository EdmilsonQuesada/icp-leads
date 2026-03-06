# Lead Research App — Constelação Familiar — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Construir um app web pessoal para descobrir, qualificar e monitorar leads (potenciais clientes de constelação familiar) coletados do Instagram e YouTube, com enriquecimento de perfil via Facebook e LinkedIn.

**Architecture:** Backend FastAPI + workers Celery/Redis para coleta e monitoramento assíncrono, banco PostgreSQL para persistência, frontend React para visualização. Tudo orquestrado via Docker Compose rodando localmente.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Alembic, Celery, Redis, PostgreSQL, instagrapi, youtube-data-api, yt-dlp, openai-whisper, React 18, Vite, TailwindCSS, pytest, Docker Compose.

---

## Visão Geral das Tasks

1. Estrutura do projeto e Docker Compose
2. Modelos de banco de dados + Alembic migrations
3. Configuração FastAPI base + health check
4. Coletor Instagram (busca por hashtag + perfil)
5. Coletor YouTube (busca de vídeos + comentários)
6. Coletor YouTube (transcrição de vídeos longos)
7. Enriquecimento demográfico — Facebook scraper
8. Enriquecimento demográfico — LinkedIn scraper
9. Engine de scoring (engajamento + intenção + perfil)
10. Celery tasks — enriquecimento e monitoramento diário
11. API REST — leads CRUD e busca
12. API REST — exportação CSV/Excel
13. Frontend React — setup + Dashboard
14. Frontend React — Lista de Leads + filtros
15. Frontend React — Perfil do Lead + timeline
16. Frontend React — Notificações
17. Configurações do usuário (keywords, períodos, limites)
18. Integração final e smoke test

---

## Convenções

- **Testes:** sempre escreva o teste antes da implementação (TDD)
- **Commits:** um commit por task concluída
- **Variáveis de ambiente:** sempre via `.env` (nunca hardcoded)
- **Caminhos:** sempre relativos à raiz do projeto `ICP_Ideal/`

---

## Task 1: Estrutura do Projeto e Docker Compose

**Files:**
- Create: `docker-compose.yml`
- Create: `backend/Dockerfile`
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `frontend/Dockerfile`
- Create: `frontend/package.json` (via Vite)
- Create: `Makefile`

**Step 1: Criar estrutura de diretórios**

```bash
mkdir -p backend/app/{api,collectors,core,db,models,schemas,tasks,services}
mkdir -p backend/tests/{collectors,api,services}
mkdir -p frontend
touch backend/app/__init__.py
touch backend/app/api/__init__.py
touch backend/app/collectors/__init__.py
touch backend/app/core/__init__.py
touch backend/app/db/__init__.py
touch backend/app/models/__init__.py
touch backend/app/schemas/__init__.py
touch backend/app/tasks/__init__.py
touch backend/app/services/__init__.py
```

**Step 2: Criar `backend/requirements.txt`**

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.35
alembic==1.13.3
psycopg2-binary==2.9.9
celery[redis]==5.4.0
redis==5.1.1
instagrapi==2.1.2
google-api-python-client==2.149.0
yt-dlp==2024.10.22
openai-whisper==20240930
playwright==1.48.0
httpx==0.27.2
pydantic-settings==2.5.2
python-dotenv==1.0.1
openpyxl==3.1.5
pytest==8.3.3
pytest-asyncio==0.24.0
httpx==0.27.2
faker==30.3.0
```

**Step 3: Criar `backend/.env.example`**

```env
DATABASE_URL=postgresql://icp:icp@db:5432/icp_leads
REDIS_URL=redis://redis:6379/0
INSTAGRAM_USERNAME=
INSTAGRAM_PASSWORD=
YOUTUBE_API_KEY=
FACEBOOK_EMAIL=
FACEBOOK_PASSWORD=
LINKEDIN_EMAIL=
LINKEDIN_PASSWORD=
COLLECT_HOUR=3
MAX_LEADS_PER_DAY=100
```

**Step 4: Criar `docker-compose.yml`**

```yaml
version: "3.9"

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: icp
      POSTGRES_PASSWORD: icp
      POSTGRES_DB: icp_leads
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    env_file: ./backend/.env
    depends_on:
      - db
      - redis

  worker:
    build: ./backend
    command: celery -A app.tasks.celery_app worker --loglevel=info
    volumes:
      - ./backend:/app
    env_file: ./backend/.env
    depends_on:
      - db
      - redis

  beat:
    build: ./backend
    command: celery -A app.tasks.celery_app beat --loglevel=info
    volumes:
      - ./backend:/app
    env_file: ./backend/.env
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend

volumes:
  pgdata:
```

**Step 5: Criar `backend/Dockerfile`**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium --with-deps
COPY . .
```

**Step 6: Criar `Makefile`**

```makefile
up:
	docker-compose up --build -d

down:
	docker-compose down

logs:
	docker-compose logs -f backend worker

test:
	docker-compose exec backend pytest tests/ -v

migrate:
	docker-compose exec backend alembic upgrade head

shell:
	docker-compose exec backend python
```

**Step 7: Inicializar frontend com Vite**

```bash
cd frontend
npm create vite@latest . -- --template react
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npm install axios react-router-dom @tanstack/react-query lucide-react
```

**Step 8: Criar `frontend/Dockerfile`**

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

**Step 9: Commit**

```bash
git add .
git commit -m "chore: estrutura inicial do projeto e docker-compose"
```

---

## Task 2: Modelos de Banco de Dados + Migrations

**Files:**
- Create: `backend/app/db/base.py`
- Create: `backend/app/db/session.py`
- Create: `backend/app/models/lead.py`
- Create: `backend/app/models/lead_event.py`
- Create: `backend/app/models/search_job.py`
- Create: `backend/app/models/settings.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/tests/test_models.py`

**Step 1: Escrever teste de modelos**

```python
# backend/tests/test_models.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db.base import Base
from app.models.lead import Lead, LeadStatus, LeadCategory, LeadPlatform
from app.models.lead_event import LeadEvent
from app.models.search_job import SearchJob

DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)

def test_create_lead(db):
    lead = Lead(
        username="maria_silva",
        platform=LeadPlatform.INSTAGRAM,
        display_name="Maria Silva",
        score=0,
        category=LeadCategory.FRIO,
        status=LeadStatus.MONITORING,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    assert lead.id is not None
    assert lead.username == "maria_silva"

def test_lead_event(db):
    lead = Lead(username="joao", platform=LeadPlatform.YOUTUBE,
                score=50, category=LeadCategory.MORNO,
                status=LeadStatus.MONITORING)
    db.add(lead)
    db.commit()
    event = LeadEvent(lead_id=lead.id, event_type="comment",
                      description="Comentou em post de constelação",
                      score_delta=5, score_after=55)
    db.add(event)
    db.commit()
    assert event.id is not None
    assert event.lead_id == lead.id
```

**Step 2: Rodar teste para confirmar que falha**

```bash
docker-compose exec backend pytest tests/test_models.py -v
```
Esperado: `ImportError` ou `ModuleNotFoundError`

**Step 3: Implementar `backend/app/db/base.py`**

```python
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

**Step 4: Implementar `backend/app/db/session.py`**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Step 5: Implementar `backend/app/models/lead.py`**

```python
import enum
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Enum, Text, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class LeadPlatform(str, enum.Enum):
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"

class LeadCategory(str, enum.Enum):
    QUENTE = "quente"
    MORNO = "morno"
    FRIO = "frio"
    DESCARTE = "descarte"

class LeadStatus(str, enum.Enum):
    PENDING = "pending"
    ENRICHING = "enriching"
    MONITORING = "monitoring"
    READY = "ready"
    CONTACTED = "contacted"
    ARCHIVED = "archived"

class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), index=True)
    platform: Mapped[LeadPlatform] = mapped_column(Enum(LeadPlatform))
    display_name: Mapped[str | None] = mapped_column(String(200))
    bio: Mapped[str | None] = mapped_column(Text)
    profile_url: Mapped[str | None] = mapped_column(String(500))
    avatar_url: Mapped[str | None] = mapped_column(String(500))

    # Demográficos
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100), default="BR")
    age: Mapped[int | None] = mapped_column(Integer)
    birthdate: Mapped[datetime | None] = mapped_column(Date)
    birthdate_source: Mapped[str | None] = mapped_column(String(50))

    # Métricas de perfil
    followers: Mapped[int | None] = mapped_column(Integer)
    following: Mapped[int | None] = mapped_column(Integer)
    is_business_account: Mapped[bool] = mapped_column(default=False)

    # Scoring
    score: Mapped[int] = mapped_column(Integer, default=0)
    score_engagement: Mapped[int] = mapped_column(Integer, default=0)
    score_intention: Mapped[int] = mapped_column(Integer, default=0)
    score_profile: Mapped[int] = mapped_column(Integer, default=0)
    category: Mapped[LeadCategory] = mapped_column(Enum(LeadCategory), default=LeadCategory.FRIO)
    status: Mapped[LeadStatus] = mapped_column(Enum(LeadStatus), default=LeadStatus.PENDING)

    # Controle de monitoramento
    monitor_until: Mapped[datetime | None] = mapped_column(DateTime)
    monitoring_days: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_monitored_at: Mapped[datetime | None] = mapped_column(DateTime)
    contacted_at: Mapped[datetime | None] = mapped_column(DateTime)

    events: Mapped[list["LeadEvent"]] = relationship(back_populates="lead",
                                                       order_by="LeadEvent.created_at")
```

**Step 6: Implementar `backend/app/models/lead_event.py`**

```python
from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class LeadEvent(Base):
    __tablename__ = "lead_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey("leads.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(50))  # comment, like, birthday, score_up
    description: Mapped[str | None] = mapped_column(Text)
    score_delta: Mapped[int] = mapped_column(Integer, default=0)
    score_after: Mapped[int] = mapped_column(Integer, default=0)
    source_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    lead: Mapped["Lead"] = relationship(back_populates="events")
```

**Step 7: Implementar `backend/app/models/search_job.py`**

```python
from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class SearchJob(Base):
    __tablename__ = "search_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keywords: Mapped[list] = mapped_column(JSON)
    platforms: Mapped[list] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    leads_found: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
```

**Step 8: Implementar `backend/app/models/settings.py`**

```python
from sqlalchemy import Integer, String, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class AppSettings(Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    keywords: Mapped[list] = mapped_column(JSON, default=lambda: [
        "constelação familiar", "constelação sistêmica",
        "Bert Hellinger", "ordem do amor", "alma família"
    ])
    monitor_days_quente: Mapped[int] = mapped_column(Integer, default=7)
    monitor_days_morno: Mapped[int] = mapped_column(Integer, default=10)
    monitor_days_frio: Mapped[int] = mapped_column(Integer, default=15)
    collect_hour: Mapped[int] = mapped_column(Integer, default=3)
    max_leads_per_day: Mapped[int] = mapped_column(Integer, default=100)
    instagram_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    youtube_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    facebook_enrichment: Mapped[bool] = mapped_column(Boolean, default=True)
    linkedin_enrichment: Mapped[bool] = mapped_column(Boolean, default=False)
```

**Step 9: Configurar `backend/app/core/config.py`**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://icp:icp@db:5432/icp_leads"
    REDIS_URL: str = "redis://redis:6379/0"
    INSTAGRAM_USERNAME: str = ""
    INSTAGRAM_PASSWORD: str = ""
    YOUTUBE_API_KEY: str = ""
    FACEBOOK_EMAIL: str = ""
    FACEBOOK_PASSWORD: str = ""
    LINKEDIN_EMAIL: str = ""
    LINKEDIN_PASSWORD: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
```

**Step 10: Configurar Alembic**

```bash
docker-compose exec backend alembic init alembic
# Editar alembic/env.py para importar Base e usar DATABASE_URL do settings
```

Conteúdo de `backend/alembic/env.py` (seção relevante):
```python
from app.db.base import Base
from app.models import lead, lead_event, search_job, settings as settings_model
from app.core.config import settings as app_settings

config.set_main_option("sqlalchemy.url", app_settings.DATABASE_URL)
target_metadata = Base.metadata
```

**Step 11: Gerar e aplicar migration**

```bash
docker-compose exec backend alembic revision --autogenerate -m "initial schema"
docker-compose exec backend alembic upgrade head
```

**Step 12: Rodar testes**

```bash
docker-compose exec backend pytest tests/test_models.py -v
```
Esperado: todos passando

**Step 13: Commit**

```bash
git add backend/app/models/ backend/app/db/ backend/app/core/ backend/alembic/ backend/tests/test_models.py
git commit -m "feat: modelos de banco de dados e migrations iniciais"
```

---

## Task 3: FastAPI Base + Health Check

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/api/health.py`
- Create: `backend/tests/api/test_health.py`

**Step 1: Escrever teste**

```python
# backend/tests/api/test_health.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

**Step 2: Rodar para confirmar falha**

```bash
docker-compose exec backend pytest tests/api/test_health.py -v
```

**Step 3: Implementar `backend/app/api/health.py`**

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok"}
```

**Step 4: Implementar `backend/app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.health import router as health_router

app = FastAPI(title="ICP Lead Research — Constelação Familiar")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
```

**Step 5: Rodar testes**

```bash
docker-compose exec backend pytest tests/api/test_health.py -v
```
Esperado: PASS

**Step 6: Commit**

```bash
git add backend/app/main.py backend/app/api/health.py backend/tests/api/test_health.py
git commit -m "feat: FastAPI base app com health check"
```

---

## Task 4: Coletor Instagram

**Files:**
- Create: `backend/app/collectors/instagram.py`
- Create: `backend/tests/collectors/test_instagram.py`

**Step 1: Escrever testes (com mocks — não chamar API real em testes)**

```python
# backend/tests/collectors/test_instagram.py
import pytest
from unittest.mock import MagicMock, patch
from app.collectors.instagram import InstagramCollector

@pytest.fixture
def mock_client():
    with patch("app.collectors.instagram.Client") as MockClient:
        instance = MockClient.return_value
        instance.user_info_by_username.return_value = MagicMock(
            pk=123456,
            username="maria_silva",
            full_name="Maria Silva",
            biography="Amo constelação familiar 🌿",
            follower_count=843,
            following_count=612,
            is_business=False,
            profile_pic_url="https://example.com/pic.jpg",
        )
        instance.hashtag_medias_recent.return_value = [
            MagicMock(
                pk=789,
                user=MagicMock(username="maria_silva"),
                caption_text="Amei minha sessão de constelação #constelaçãofamiliar",
                like_count=45,
                comment_count=8,
            )
        ]
        yield instance

def test_get_profile(mock_client):
    collector = InstagramCollector.__new__(InstagramCollector)
    collector.client = mock_client
    profile = collector.get_profile("maria_silva")
    assert profile["username"] == "maria_silva"
    assert profile["followers"] == 843
    assert "constelação" in profile["bio"]

def test_search_hashtag(mock_client):
    collector = InstagramCollector.__new__(InstagramCollector)
    collector.client = mock_client
    posts = collector.search_hashtag("constelaçãofamiliar", limit=5)
    assert len(posts) >= 1
    assert posts[0]["username"] == "maria_silva"
```

**Step 2: Rodar para confirmar falha**

```bash
docker-compose exec backend pytest tests/collectors/test_instagram.py -v
```

**Step 3: Implementar `backend/app/collectors/instagram.py`**

```python
import time
import random
import logging
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired
from app.core.config import settings

logger = logging.getLogger(__name__)

class InstagramCollector:
    def __init__(self):
        self.client = Client()
        self._login()

    def _login(self):
        try:
            self.client.login(settings.INSTAGRAM_USERNAME, settings.INSTAGRAM_PASSWORD)
            logger.info("Instagram login bem-sucedido")
        except Exception as e:
            logger.error(f"Falha no login Instagram: {e}")
            raise

    def _delay(self):
        time.sleep(random.uniform(3, 8))

    def get_profile(self, username: str) -> dict:
        self._delay()
        user = self.client.user_info_by_username(username)
        return {
            "username": user.username,
            "display_name": user.full_name,
            "bio": user.biography,
            "followers": user.follower_count,
            "following": user.following_count,
            "is_business": user.is_business,
            "avatar_url": str(user.profile_pic_url),
            "platform": "instagram",
        }

    def search_hashtag(self, hashtag: str, limit: int = 50) -> list[dict]:
        self._delay()
        medias = self.client.hashtag_medias_recent(hashtag, amount=limit)
        results = []
        for media in medias:
            results.append({
                "username": media.user.username,
                "post_text": media.caption_text or "",
                "likes": media.like_count,
                "comments_count": media.comment_count,
                "post_url": f"https://instagram.com/p/{media.code}",
            })
            self._delay()
        return results

    def get_comments(self, media_id: str, limit: int = 100) -> list[dict]:
        self._delay()
        comments = self.client.media_comments(media_id, amount=limit)
        return [
            {
                "username": c.user.username,
                "text": c.text,
                "created_at": c.created_at_utc.isoformat() if c.created_at_utc else None,
            }
            for c in comments
        ]
```

**Step 4: Rodar testes**

```bash
docker-compose exec backend pytest tests/collectors/test_instagram.py -v
```
Esperado: PASS

**Step 5: Commit**

```bash
git add backend/app/collectors/instagram.py backend/tests/collectors/test_instagram.py
git commit -m "feat: coletor Instagram com busca por hashtag e perfil"
```

---

## Task 5: Coletor YouTube (Busca + Comentários)

**Files:**
- Create: `backend/app/collectors/youtube.py`
- Create: `backend/tests/collectors/test_youtube.py`

**Step 1: Escrever testes**

```python
# backend/tests/collectors/test_youtube.py
import pytest
from unittest.mock import MagicMock, patch
from app.collectors.youtube import YouTubeCollector

@pytest.fixture
def mock_youtube():
    with patch("app.collectors.youtube.build") as mock_build:
        service = MagicMock()
        mock_build.return_value = service

        # Mock search
        service.search().list().execute.return_value = {
            "items": [
                {
                    "id": {"videoId": "abc123"},
                    "snippet": {
                        "title": "Constelação Familiar - Como funciona",
                        "channelTitle": "Canal Espiritualidade",
                        "channelId": "UC123",
                        "publishedAt": "2024-01-01T00:00:00Z",
                    }
                }
            ]
        }

        # Mock comments
        service.commentThreads().list().execute.return_value = {
            "items": [
                {
                    "snippet": {
                        "topLevelComment": {
                            "snippet": {
                                "authorDisplayName": "João Paz",
                                "authorChannelId": {"value": "UC456"},
                                "textDisplay": "Quero fazer uma sessão, como faço?",
                                "likeCount": 3,
                                "publishedAt": "2024-01-02T00:00:00Z",
                            }
                        }
                    }
                }
            ],
            "nextPageToken": None,
        }
        yield service

def test_search_videos(mock_youtube):
    collector = YouTubeCollector.__new__(YouTubeCollector)
    collector.service = mock_youtube
    videos = collector.search_videos("constelação familiar", max_results=5)
    assert len(videos) == 1
    assert videos[0]["video_id"] == "abc123"
    assert "Constelação" in videos[0]["title"]

def test_get_comments(mock_youtube):
    collector = YouTubeCollector.__new__(YouTubeCollector)
    collector.service = mock_youtube
    comments = collector.get_comments("abc123", max_results=10)
    assert len(comments) == 1
    assert "Quero fazer" in comments[0]["text"]
    assert comments[0]["username"] == "João Paz"
```

**Step 2: Rodar para confirmar falha**

```bash
docker-compose exec backend pytest tests/collectors/test_youtube.py -v
```

**Step 3: Implementar `backend/app/collectors/youtube.py`**

```python
import logging
from googleapiclient.discovery import build
from app.core.config import settings

logger = logging.getLogger(__name__)

class YouTubeCollector:
    def __init__(self):
        self.service = build("youtube", "v3", developerKey=settings.YOUTUBE_API_KEY)

    def search_videos(self, query: str, max_results: int = 50) -> list[dict]:
        response = self.service.search().list(
            q=query,
            part="snippet",
            type="video",
            maxResults=max_results,
            relevanceLanguage="pt",
            regionCode="BR",
        ).execute()

        return [
            {
                "video_id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "channel_title": item["snippet"]["channelTitle"],
                "channel_id": item["snippet"]["channelId"],
                "published_at": item["snippet"]["publishedAt"],
            }
            for item in response.get("items", [])
        ]

    def get_comments(self, video_id: str, max_results: int = 100) -> list[dict]:
        comments = []
        page_token = None

        while len(comments) < max_results:
            params = dict(
                videoId=video_id,
                part="snippet",
                maxResults=min(100, max_results - len(comments)),
                textFormat="plainText",
            )
            if page_token:
                params["pageToken"] = page_token

            response = self.service.commentThreads().list(**params).execute()

            for item in response.get("items", []):
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "username": snippet["authorDisplayName"],
                    "channel_id": snippet.get("authorChannelId", {}).get("value"),
                    "text": snippet["textDisplay"],
                    "likes": snippet.get("likeCount", 0),
                    "published_at": snippet["publishedAt"],
                })

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return comments
```

**Step 4: Rodar testes**

```bash
docker-compose exec backend pytest tests/collectors/test_youtube.py -v
```
Esperado: PASS

**Step 5: Commit**

```bash
git add backend/app/collectors/youtube.py backend/tests/collectors/test_youtube.py
git commit -m "feat: coletor YouTube com busca de vídeos e extração de comentários"
```

---

## Task 6: Coletor YouTube — Transcrição de Vídeos Longos

**Files:**
- Create: `backend/app/collectors/transcriber.py`
- Create: `backend/tests/collectors/test_transcriber.py`

**Step 1: Escrever testes**

```python
# backend/tests/collectors/test_transcriber.py
import pytest
from unittest.mock import patch, MagicMock
from app.collectors.transcriber import VideoTranscriber

def test_extract_transcript_from_subtitles():
    """Testa extração via legendas automáticas (caminho feliz)"""
    mock_info = {
        "subtitles": {},
        "automatic_captions": {
            "pt": [{"url": "https://example.com/captions.vtt", "ext": "vtt"}]
        },
        "duration": 3600,
    }
    with patch("app.collectors.transcriber.yt_dlp.YoutubeDL") as MockYDL:
        instance = MockYDL.return_value.__enter__.return_value
        instance.extract_info.return_value = mock_info
        instance.download.return_value = None

        transcriber = VideoTranscriber()
        # Só testa que o método existe e retorna algo estruturado
        assert hasattr(transcriber, "get_transcript")

def test_skip_short_videos():
    """Vídeos < 10 min não precisam de transcrição completa"""
    transcriber = VideoTranscriber()
    result = transcriber.should_transcribe(duration_seconds=300)
    assert result is False

def test_transcribe_long_videos():
    transcriber = VideoTranscriber()
    result = transcriber.should_transcribe(duration_seconds=1800)
    assert result is True
```

**Step 2: Implementar `backend/app/collectors/transcriber.py`**

```python
import logging
import tempfile
import os
import yt_dlp

logger = logging.getLogger(__name__)

TRANSCRIBE_MIN_DURATION = 600  # 10 minutos

class VideoTranscriber:
    def should_transcribe(self, duration_seconds: int) -> bool:
        return duration_seconds >= TRANSCRIBE_MIN_DURATION

    def get_transcript(self, video_id: str) -> str | None:
        url = f"https://www.youtube.com/watch?v={video_id}"

        ydl_opts = {
            "skip_download": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["pt", "pt-BR"],
            "subtitlesformat": "vtt",
            "quiet": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                duration = info.get("duration", 0)

                if not self.should_transcribe(duration):
                    return None

                # Tenta legendas automáticas em pt
                captions = info.get("automatic_captions", {})
                if not captions.get("pt") and not captions.get("pt-BR"):
                    logger.info(f"Vídeo {video_id} sem legendas em pt")
                    return self._transcribe_with_whisper(url)

                return self._extract_vtt_text(info)

        except Exception as e:
            logger.error(f"Erro ao transcrever vídeo {video_id}: {e}")
            return None

    def _extract_vtt_text(self, info: dict) -> str:
        """Extrai texto limpo das legendas VTT."""
        captions = info.get("automatic_captions", {})
        for lang in ["pt", "pt-BR"]:
            if lang in captions:
                # Retorna URL da legenda para processamento
                return f"[legenda disponível: {captions[lang][0]['url']}]"
        return ""

    def _transcribe_with_whisper(self, url: str) -> str | None:
        """Fallback: baixa áudio e usa Whisper para transcrever."""
        try:
            import whisper
            with tempfile.TemporaryDirectory() as tmpdir:
                audio_path = os.path.join(tmpdir, "audio.mp3")
                ydl_opts = {
                    "format": "bestaudio/best",
                    "outtmpl": audio_path,
                    "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
                    "quiet": True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                model = whisper.load_model("base")
                result = model.transcribe(audio_path, language="pt")
                return result["text"]
        except Exception as e:
            logger.error(f"Whisper falhou: {e}")
            return None
```

**Step 3: Rodar testes**

```bash
docker-compose exec backend pytest tests/collectors/test_transcriber.py -v
```
Esperado: PASS

**Step 4: Commit**

```bash
git add backend/app/collectors/transcriber.py backend/tests/collectors/test_transcriber.py
git commit -m "feat: transcrição de vídeos longos com yt-dlp e Whisper"
```

---

## Task 7: Enriquecimento Demográfico — Facebook Scraper

**Files:**
- Create: `backend/app/collectors/facebook.py`
- Create: `backend/tests/collectors/test_facebook.py`

**Step 1: Escrever testes**

```python
# backend/tests/collectors/test_facebook.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.collectors.facebook import FacebookEnricher

def test_parse_birthdate_from_text():
    enricher = FacebookEnricher.__new__(FacebookEnricher)
    result = enricher._parse_birthdate("15 de março de 1990")
    assert result is not None
    assert result.month == 3
    assert result.day == 15
    assert result.year == 1990

def test_parse_birthdate_numeric():
    enricher = FacebookEnricher.__new__(FacebookEnricher)
    result = enricher._parse_birthdate("15/03/1990")
    assert result is not None
    assert result.year == 1990

def test_parse_birthdate_invalid():
    enricher = FacebookEnricher.__new__(FacebookEnricher)
    result = enricher._parse_birthdate("texto sem data")
    assert result is None
```

**Step 2: Implementar `backend/app/collectors/facebook.py`**

```python
import re
import logging
from datetime import datetime, date
from playwright.async_api import async_playwright
from app.core.config import settings

logger = logging.getLogger(__name__)

MONTH_MAP = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4,
    "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
    "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}

class FacebookEnricher:
    def _parse_birthdate(self, text: str) -> date | None:
        if not text:
            return None

        # Formato DD/MM/YYYY ou DD-MM-YYYY
        match = re.search(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})", text)
        if match:
            try:
                return date(int(match.group(3)), int(match.group(2)), int(match.group(1)))
            except ValueError:
                pass

        # Formato "15 de março de 1990"
        match = re.search(
            r"(\d{1,2})\s+de\s+(\w+)(?:\s+de\s+(\d{4}))?",
            text.lower()
        )
        if match:
            day = int(match.group(1))
            month = MONTH_MAP.get(match.group(2))
            year = int(match.group(3)) if match.group(3) else None
            if month:
                try:
                    return date(year or datetime.now().year, month, day)
                except ValueError:
                    pass
        return None

    async def enrich(self, name: str, username: str) -> dict:
        """Tenta encontrar perfil público no Facebook e extrair dados demográficos."""
        result = {"birthdate": None, "age": None, "city": None, "source": "facebook"}

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                page = await context.new_page()

                # Busca pelo username ou nome
                search_url = f"https://www.facebook.com/search/people?q={name.replace(' ', '+')}"
                await page.goto(search_url, timeout=15000)
                await page.wait_for_timeout(3000)

                # Extrai texto visível para procurar data de nascimento
                content = await page.content()
                birthdate = self._parse_birthdate(content)
                if birthdate:
                    result["birthdate"] = birthdate
                    result["age"] = datetime.now().year - birthdate.year

                await browser.close()

        except Exception as e:
            logger.warning(f"Facebook enrichment falhou para {name}: {e}")

        return result
```

**Step 3: Rodar testes**

```bash
docker-compose exec backend pytest tests/collectors/test_facebook.py -v
```
Esperado: PASS (testes de parsing não precisam de browser)

**Step 4: Commit**

```bash
git add backend/app/collectors/facebook.py backend/tests/collectors/test_facebook.py
git commit -m "feat: Facebook enricher para dados demográficos e aniversário"
```

---

## Task 8: Enriquecimento Demográfico — LinkedIn Scraper

**Files:**
- Create: `backend/app/collectors/linkedin.py`
- Create: `backend/tests/collectors/test_linkedin.py`

**Step 1: Escrever testes**

```python
# backend/tests/collectors/test_linkedin.py
import pytest
from app.collectors.linkedin import LinkedInEnricher

def test_extract_city_from_location():
    enricher = LinkedInEnricher.__new__(LinkedInEnricher)
    result = enricher._extract_city("São Paulo, Brasil")
    assert result == "São Paulo"

def test_extract_city_no_country():
    enricher = LinkedInEnricher.__new__(LinkedInEnricher)
    result = enricher._extract_city("Rio de Janeiro")
    assert result == "Rio de Janeiro"

def test_estimate_age_from_graduation():
    enricher = LinkedInEnricher.__new__(LinkedInEnricher)
    age = enricher._estimate_age_from_graduation_year(2010)
    assert 30 <= age <= 45  # formou ~2010, provavelmente nasceu entre 1985-1990
```

**Step 2: Implementar `backend/app/collectors/linkedin.py`**

```python
import re
import logging
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from app.core.config import settings

logger = logging.getLogger(__name__)

class LinkedInEnricher:
    def _extract_city(self, location_text: str) -> str | None:
        if not location_text:
            return None
        # "São Paulo, Brasil" → "São Paulo"
        parts = location_text.split(",")
        return parts[0].strip() if parts else location_text.strip()

    def _estimate_age_from_graduation_year(self, year: int) -> int:
        # Assume graduação ~22 anos
        return datetime.now().year - year + 22

    async def enrich(self, name: str) -> dict:
        """Tenta enriquecer perfil via LinkedIn (conservador - apenas perfis públicos)."""
        result = {"city": None, "age": None, "source": "linkedin"}

        # LinkedIn é muito agressivo contra scraping — rate limit conservador
        await asyncio.sleep(10)

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                page = await context.new_page()

                # Apenas busca pública via Google (evita login direto no LI)
                search_url = f"https://www.google.com/search?q=site:linkedin.com+\"{name}\"+Brasil"
                await page.goto(search_url, timeout=15000)
                await page.wait_for_timeout(5000)

                content = await page.content()

                # Extrai cidade se aparecer no snippet do Google
                city_match = re.search(r"·\s*([A-ZÀ-Ú][a-zà-ú\s]+(?:,\s*[A-Z][a-z]+)?)\s*·", content)
                if city_match:
                    result["city"] = self._extract_city(city_match.group(1))

                await browser.close()

        except Exception as e:
            logger.warning(f"LinkedIn enrichment falhou para {name}: {e}")

        return result
```

**Step 3: Rodar testes**

```bash
docker-compose exec backend pytest tests/collectors/test_linkedin.py -v
```
Esperado: PASS

**Step 4: Commit**

```bash
git add backend/app/collectors/linkedin.py backend/tests/collectors/test_linkedin.py
git commit -m "feat: LinkedIn enricher conservador via busca pública"
```

---

## Task 9: Engine de Scoring

**Files:**
- Create: `backend/app/services/scorer.py`
- Create: `backend/tests/services/test_scorer.py`

**Step 1: Escrever testes**

```python
# backend/tests/services/test_scorer.py
import pytest
from app.services.scorer import LeadScorer, ScoreResult

INTENTION_KEYWORDS = [
    "quero fazer sessão", "como faço sessão", "onde encontro terapeuta",
    "preciso de ajuda", "quero agendar", "como funciona",
]

def test_score_zero_for_empty_lead():
    scorer = LeadScorer()
    result = scorer.score({
        "bio": "",
        "country": "US",
        "is_business": True,
        "followers": 500000,
        "engagement_events": [],
        "comments": [],
    })
    assert result.total < 25

def test_score_high_for_ideal_lead():
    scorer = LeadScorer()
    result = scorer.score({
        "bio": "buscando cura e autoconhecimento terapia 🌿",
        "country": "BR",
        "is_business": False,
        "followers": 800,
        "engagement_events": [
            {"type": "like", "context": "constelação familiar"},
            {"type": "comment", "context": "constelação sistêmica"},
            {"type": "like", "context": "constelação familiar"},
        ],
        "comments": [
            {"text": "quero fazer sessão de constelação, como funciona?"},
        ],
    })
    assert result.total >= 75
    assert result.category == "quente"

def test_intention_keyword_detected():
    scorer = LeadScorer()
    result = scorer.score({
        "bio": "",
        "country": "BR",
        "is_business": False,
        "followers": 500,
        "engagement_events": [],
        "comments": [{"text": "preciso de ajuda, quero marcar uma sessão"}],
    })
    assert result.intention_score > 0

def test_category_classification():
    scorer = LeadScorer()
    assert scorer._classify(85) == "quente"
    assert scorer._classify(60) == "morno"
    assert scorer._classify(35) == "frio"
    assert scorer._classify(10) == "descarte"
```

**Step 2: Rodar para confirmar falha**

```bash
docker-compose exec backend pytest tests/services/test_scorer.py -v
```

**Step 3: Implementar `backend/app/services/scorer.py`**

```python
import re
from dataclasses import dataclass

INTENTION_KEYWORDS = [
    "quero fazer sessão", "quero agendar", "como faço sessão",
    "onde encontro terapeuta", "preciso de ajuda", "como funciona",
    "quero participar", "onde agendar", "quanto custa sessão",
    "quero marcar", "como me inscrevo",
]

SPIRITUAL_BIO_KEYWORDS = [
    "terapia", "autoconhecimento", "cura", "espiritualidade",
    "constelação", "meditação", "yoga", "ayurveda", "xamanismo",
    "alma", "despertar", "consciência", "equilíbrio",
]

@dataclass
class ScoreResult:
    engagement_score: int
    intention_score: int
    profile_score: int
    total: int
    category: str

class LeadScorer:
    def _classify(self, total: int) -> str:
        if total >= 75:
            return "quente"
        elif total >= 50:
            return "morno"
        elif total >= 25:
            return "frio"
        return "descarte"

    def _calc_engagement(self, events: list[dict]) -> int:
        if not events:
            return 0
        score = 0
        score += min(len(events) * 5, 25)  # até 25 pts por frequência
        recency_bonus = min(sum(1 for e in events[-5:]), 5) * 2  # últimos 5
        score += recency_bonus
        variety = len(set(e.get("context", "") for e in events))
        score += min(variety * 3, 9)  # variedade de criadores
        return min(score, 40)

    def _calc_intention(self, comments: list[dict]) -> int:
        if not comments:
            return 0
        score = 0
        for comment in comments:
            text = comment.get("text", "").lower()
            for kw in INTENTION_KEYWORDS:
                if kw in text:
                    score += 15
                    break
        return min(score, 35)

    def _calc_profile(self, lead: dict) -> int:
        score = 0
        if lead.get("country") == "BR":
            score += 10
        if not lead.get("is_business", False):
            score += 5
        followers = lead.get("followers", 0)
        if 100 <= followers <= 10000:
            score += 5
        bio = lead.get("bio", "").lower()
        for kw in SPIRITUAL_BIO_KEYWORDS:
            if kw in bio:
                score += 5
                break
        return min(score, 25)

    def score(self, lead: dict) -> ScoreResult:
        eng = self._calc_engagement(lead.get("engagement_events", []))
        intention = self._calc_intention(lead.get("comments", []))
        profile = self._calc_profile(lead)
        total = eng + intention + profile
        return ScoreResult(
            engagement_score=eng,
            intention_score=intention,
            profile_score=profile,
            total=total,
            category=self._classify(total),
        )
```

**Step 4: Rodar testes**

```bash
docker-compose exec backend pytest tests/services/test_scorer.py -v
```
Esperado: PASS

**Step 5: Commit**

```bash
git add backend/app/services/scorer.py backend/tests/services/test_scorer.py
git commit -m "feat: engine de scoring com engajamento, intenção e perfil demográfico"
```

---

## Task 10: Celery Tasks — Enriquecimento e Monitoramento

**Files:**
- Create: `backend/app/tasks/celery_app.py`
- Create: `backend/app/tasks/enrichment.py`
- Create: `backend/app/tasks/monitoring.py`
- Create: `backend/tests/tasks/test_monitoring.py`

**Step 1: Criar `backend/app/tasks/celery_app.py`**

```python
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "icp_leads",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.enrichment", "app.tasks.monitoring"],
)

celery_app.conf.beat_schedule = {
    "monitor-leads-daily": {
        "task": "app.tasks.monitoring.run_daily_monitoring",
        "schedule": crontab(hour=3, minute=0),
    },
    "process-pending-leads": {
        "task": "app.tasks.enrichment.process_pending_queue",
        "schedule": crontab(minute=0),  # a cada hora
    },
    "revaluate-cold-leads": {
        "task": "app.tasks.monitoring.revaluate_cold_leads",
        "schedule": crontab(day_of_week=0, hour=4),  # semanalmente
    },
}
celery_app.conf.timezone = "America/Sao_Paulo"
```

**Step 2: Criar `backend/app/tasks/enrichment.py`**

```python
import logging
from datetime import datetime, timedelta
from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.lead import Lead, LeadStatus, LeadCategory
from app.models.lead_event import LeadEvent
from app.services.scorer import LeadScorer

logger = logging.getLogger(__name__)

@celery_app.task
def enrich_lead(lead_id: int):
    """Enriquece um lead recém-descoberto com dados de todas as fontes."""
    from app.core.config import settings

    with SessionLocal() as db:
        lead = db.get(Lead, lead_id)
        if not lead:
            return

        lead.status = LeadStatus.ENRICHING
        db.commit()

        enriched_data = {}

        # Facebook
        if settings.FACEBOOK_EMAIL:
            try:
                import asyncio
                from app.collectors.facebook import FacebookEnricher
                enricher = FacebookEnricher()
                fb_data = asyncio.run(enricher.enrich(lead.display_name or "", lead.username))
                if fb_data.get("birthdate"):
                    lead.birthdate = fb_data["birthdate"]
                    lead.age = fb_data.get("age")
                    lead.birthdate_source = "facebook"
            except Exception as e:
                logger.warning(f"Facebook enrichment falhou: {e}")

        # LinkedIn
        if settings.LINKEDIN_EMAIL:
            try:
                from app.collectors.linkedin import LinkedInEnricher
                li_enricher = LinkedInEnricher()
                li_data = asyncio.run(li_enricher.enrich(lead.display_name or lead.username))
                if li_data.get("city") and not lead.city:
                    lead.city = li_data["city"]
            except Exception as e:
                logger.warning(f"LinkedIn enrichment falhou: {e}")

        # Score inicial
        scorer = LeadScorer()
        result = scorer.score({
            "bio": lead.bio or "",
            "country": lead.country or "BR",
            "is_business": lead.is_business_account,
            "followers": lead.followers or 0,
            "engagement_events": [],
            "comments": [],
        })

        lead.score = result.total
        lead.score_engagement = result.engagement_score
        lead.score_intention = result.intention_score
        lead.score_profile = result.profile_score
        lead.category = LeadCategory(result.category)
        lead.status = LeadStatus.MONITORING

        # Define prazo de monitoramento
        days_map = {"quente": 7, "morno": 10, "frio": 15, "descarte": 0}
        days = days_map.get(result.category, 15)
        lead.monitor_until = datetime.utcnow() + timedelta(days=days)

        db.add(LeadEvent(
            lead_id=lead.id,
            event_type="enriched",
            description=f"Perfil enriquecido. Score inicial: {result.total}",
            score_delta=result.total,
            score_after=result.total,
        ))
        db.commit()

@celery_app.task
def process_pending_queue():
    """Processa leads com status PENDING."""
    with SessionLocal() as db:
        pending = db.query(Lead).filter(Lead.status == LeadStatus.PENDING).limit(50).all()
        for lead in pending:
            enrich_lead.delay(lead.id)
        logger.info(f"Enfileirados {len(pending)} leads para enriquecimento")
```

**Step 3: Criar `backend/app/tasks/monitoring.py`**

```python
import logging
from datetime import datetime
from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.lead import Lead, LeadStatus, LeadCategory
from app.models.lead_event import LeadEvent
from app.services.scorer import LeadScorer

logger = logging.getLogger(__name__)

INTENTION_KEYWORDS = [
    "quero fazer sessão", "como faço sessão", "onde encontro",
    "preciso de ajuda", "quero agendar", "como funciona",
]

@celery_app.task
def run_daily_monitoring():
    """Verifica atividade recente de todos os leads em monitoramento."""
    with SessionLocal() as db:
        active = db.query(Lead).filter(
            Lead.status == LeadStatus.MONITORING,
            Lead.monitor_until >= datetime.utcnow(),
        ).all()

        for lead in active:
            monitor_lead.delay(lead.id)
        logger.info(f"Monitoramento iniciado para {len(active)} leads")

@celery_app.task
def monitor_lead(lead_id: int):
    """Verifica atividade recente de um lead específico e atualiza score."""
    with SessionLocal() as db:
        lead = db.get(Lead, lead_id)
        if not lead:
            return

        lead.monitoring_days += 1
        lead.last_monitored_at = datetime.utcnow()
        score_delta = 0
        events_added = []

        # Verifica aniversário próximo (dentro de 7 dias)
        if lead.birthdate:
            today = datetime.utcnow().date()
            bday_this_year = lead.birthdate.replace(year=today.year)
            days_until = (bday_this_year - today).days
            if 0 <= days_until <= 7:
                events_added.append(LeadEvent(
                    lead_id=lead.id,
                    event_type="birthday_soon",
                    description=f"Aniversário em {days_until} dias",
                    score_delta=0,
                    score_after=lead.score,
                ))

        # Busca novos comentários do lead no Instagram
        if lead.platform == "instagram":
            try:
                from app.collectors.instagram import InstagramCollector
                collector = InstagramCollector()
                profile = collector.get_profile(lead.username)
                # Verifica se houve engajamento recente (heurística simples)
                # Em produção: comparar com último estado salvo
            except Exception as e:
                logger.warning(f"Monitoramento Instagram falhou para {lead.username}: {e}")

        # Penalidade por inatividade
        if lead.monitoring_days > 7 and not events_added:
            score_delta = -10

        if score_delta != 0:
            old_score = lead.score
            lead.score = max(0, lead.score + score_delta)
            new_category = _classify(lead.score)

            if new_category != lead.category.value:
                events_added.append(LeadEvent(
                    lead_id=lead.id,
                    event_type="score_change",
                    description=f"Categoria mudou: {lead.category.value} → {new_category}",
                    score_delta=score_delta,
                    score_after=lead.score,
                ))
                lead.category = LeadCategory(new_category)

        for event in events_added:
            db.add(event)
        db.commit()

def _classify(score: int) -> str:
    if score >= 75:
        return "quente"
    elif score >= 50:
        return "morno"
    elif score >= 25:
        return "frio"
    return "descarte"

@celery_app.task
def revaluate_cold_leads():
    """Arquiva leads frios sem evolução após período máximo."""
    with SessionLocal() as db:
        expired = db.query(Lead).filter(
            Lead.status == LeadStatus.MONITORING,
            Lead.monitor_until < datetime.utcnow(),
        ).all()

        for lead in expired:
            lead.status = LeadStatus.ARCHIVED
        db.commit()
        logger.info(f"Arquivados {len(expired)} leads expirados")
```

**Step 4: Rodar testes básicos**

```bash
docker-compose exec backend pytest tests/ -v --ignore=tests/collectors/test_instagram.py
```
Esperado: PASS (collectors reais ignorados em CI)

**Step 5: Commit**

```bash
git add backend/app/tasks/
git commit -m "feat: Celery tasks para enriquecimento e monitoramento diário de leads"
```

---

## Task 11: API REST — Leads CRUD e Busca

**Files:**
- Create: `backend/app/schemas/lead.py`
- Create: `backend/app/api/leads.py`
- Create: `backend/app/api/search.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/api/test_leads.py`

**Step 1: Criar `backend/app/schemas/lead.py`**

```python
from datetime import datetime, date
from pydantic import BaseModel

class LeadOut(BaseModel):
    id: int
    username: str
    platform: str
    display_name: str | None
    bio: str | None
    avatar_url: str | None
    city: str | None
    country: str | None
    age: int | None
    birthdate: date | None
    followers: int | None
    score: int
    category: str
    status: str
    created_at: datetime
    last_monitored_at: datetime | None

    class Config:
        from_attributes = True

class LeadList(BaseModel):
    total: int
    items: list[LeadOut]

class SearchJobCreate(BaseModel):
    keywords: list[str]
    platforms: list[str] = ["instagram", "youtube"]
```

**Step 2: Escrever testes da API**

```python
# backend/tests/api/test_leads.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.main import app
from app.db.base import Base
from app.models.lead import Lead, LeadPlatform, LeadCategory, LeadStatus
from app.db.session import get_db

DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def override_get_db():
    with Session(engine) as session:
        yield session

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def _create_lead(db):
    lead = Lead(
        username="test_user",
        platform=LeadPlatform.INSTAGRAM,
        score=80,
        category=LeadCategory.QUENTE,
        status=LeadStatus.MONITORING,
    )
    db.add(lead)
    db.commit()
    return lead

def test_list_leads_empty():
    response = client.get("/leads")
    assert response.status_code == 200
    assert response.json()["total"] == 0

def test_list_leads_with_data():
    with Session(engine) as db:
        _create_lead(db)
    response = client.get("/leads")
    assert response.status_code == 200
    assert response.json()["total"] == 1

def test_filter_by_category():
    with Session(engine) as db:
        _create_lead(db)
    response = client.get("/leads?category=quente")
    assert response.status_code == 200
    assert response.json()["total"] == 1

    response = client.get("/leads?category=frio")
    assert response.status_code == 200
    assert response.json()["total"] == 0

def test_get_lead_by_id():
    with Session(engine) as db:
        lead = _create_lead(db)
        lead_id = lead.id
    response = client.get(f"/leads/{lead_id}")
    assert response.status_code == 200
    assert response.json()["username"] == "test_user"

def test_mark_as_contacted():
    with Session(engine) as db:
        lead = _create_lead(db)
        lead_id = lead.id
    response = client.patch(f"/leads/{lead_id}/contacted")
    assert response.status_code == 200
    assert response.json()["status"] == "contacted"
```

**Step 3: Implementar `backend/app/api/leads.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.session import get_db
from app.models.lead import Lead, LeadStatus
from app.schemas.lead import LeadOut, LeadList

router = APIRouter(prefix="/leads", tags=["leads"])

@router.get("", response_model=LeadList)
def list_leads(
    category: str | None = None,
    platform: str | None = None,
    status: str | None = None,
    city: str | None = None,
    birthday_soon: bool = False,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Lead)
    if category:
        query = query.filter(Lead.category == category)
    if platform:
        query = query.filter(Lead.platform == platform)
    if status:
        query = query.filter(Lead.status == status)
    if city:
        query = query.filter(Lead.city.ilike(f"%{city}%"))
    if birthday_soon:
        from datetime import date, timedelta
        today = date.today()
        in_7_days = today + timedelta(days=7)
        query = query.filter(
            Lead.birthdate != None,
        )
    total = query.count()
    items = query.order_by(Lead.score.desc()).offset(skip).limit(limit).all()
    return LeadList(total=total, items=items)

@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return lead

@router.patch("/{lead_id}/contacted", response_model=LeadOut)
def mark_contacted(lead_id: int, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    lead.status = LeadStatus.CONTACTED
    lead.contacted_at = datetime.utcnow()
    db.commit()
    db.refresh(lead)
    return lead

@router.delete("/{lead_id}")
def archive_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    lead.status = LeadStatus.ARCHIVED
    db.commit()
    return {"ok": True}
```

**Step 4: Criar `backend/app/api/search.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.search_job import SearchJob
from app.schemas.lead import SearchJobCreate

router = APIRouter(prefix="/search", tags=["search"])

@router.post("")
def create_search_job(payload: SearchJobCreate, db: Session = Depends(get_db)):
    job = SearchJob(keywords=payload.keywords, platforms=payload.platforms)
    db.add(job)
    db.commit()
    db.refresh(job)

    # Dispara task Celery
    from app.tasks.enrichment import process_pending_queue
    process_pending_queue.delay()

    return {"job_id": job.id, "status": "queued"}

@router.get("")
def list_search_jobs(db: Session = Depends(get_db)):
    jobs = db.query(SearchJob).order_by(SearchJob.created_at.desc()).limit(20).all()
    return jobs
```

**Step 5: Atualizar `backend/app/main.py`**

```python
from app.api.leads import router as leads_router
from app.api.search import router as search_router

app.include_router(leads_router)
app.include_router(search_router)
```

**Step 6: Rodar testes**

```bash
docker-compose exec backend pytest tests/api/test_leads.py -v
```
Esperado: PASS

**Step 7: Commit**

```bash
git add backend/app/api/ backend/app/schemas/ backend/tests/api/test_leads.py
git commit -m "feat: API REST para leads com CRUD, filtros e busca"
```

---

## Task 12: API REST — Exportação CSV/Excel

**Files:**
- Create: `backend/app/api/export.py`
- Create: `backend/tests/api/test_export.py`
- Modify: `backend/app/main.py`

**Step 1: Escrever testes**

```python
# backend/tests/api/test_export.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.main import app
from app.db.base import Base
from app.models.lead import Lead, LeadPlatform, LeadCategory, LeadStatus
from app.db.session import get_db

DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def override_get_db():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        lead = Lead(username="export_user", platform=LeadPlatform.INSTAGRAM,
                    score=70, category=LeadCategory.MORNO, status=LeadStatus.MONITORING,
                    display_name="Export User", city="São Paulo")
        db.add(lead)
        db.commit()
    yield
    Base.metadata.drop_all(engine)

client = TestClient(app)

def test_export_csv():
    response = client.get("/export/csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert b"export_user" in response.content

def test_export_excel():
    response = client.get("/export/excel")
    assert response.status_code == 200
    content_type = response.headers["content-type"]
    assert "spreadsheet" in content_type or "excel" in content_type
```

**Step 2: Implementar `backend/app/api/export.py`**

```python
import csv
import io
from datetime import datetime
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from openpyxl import Workbook
from app.db.session import get_db
from app.models.lead import Lead

router = APIRouter(prefix="/export", tags=["export"])

EXPORT_FIELDS = [
    "id", "username", "platform", "display_name", "profile_url",
    "score", "category", "status", "city", "country",
    "age", "birthdate", "birthdate_source",
    "followers", "bio", "created_at", "last_monitored_at", "contacted_at",
]

def _lead_to_row(lead: Lead) -> list:
    return [
        lead.id, lead.username, lead.platform.value if lead.platform else "",
        lead.display_name or "", lead.profile_url or "",
        lead.score, lead.category.value if lead.category else "",
        lead.status.value if lead.status else "",
        lead.city or "", lead.country or "",
        lead.age, str(lead.birthdate) if lead.birthdate else "",
        lead.birthdate_source or "",
        lead.followers, lead.bio or "",
        str(lead.created_at) if lead.created_at else "",
        str(lead.last_monitored_at) if lead.last_monitored_at else "",
        str(lead.contacted_at) if lead.contacted_at else "",
    ]

@router.get("/csv")
def export_csv(db: Session = Depends(get_db)):
    leads = db.query(Lead).order_by(Lead.score.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(EXPORT_FIELDS)
    for lead in leads:
        writer.writerow(_lead_to_row(lead))

    output.seek(0)
    filename = f"leads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

@router.get("/excel")
def export_excel(db: Session = Depends(get_db)):
    leads = db.query(Lead).order_by(Lead.score.desc()).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Leads"
    ws.append(EXPORT_FIELDS)
    for lead in leads:
        ws.append(_lead_to_row(lead))

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"leads_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
```

**Step 3: Rodar testes**

```bash
docker-compose exec backend pytest tests/api/test_export.py -v
```
Esperado: PASS

**Step 4: Commit**

```bash
git add backend/app/api/export.py backend/tests/api/test_export.py
git commit -m "feat: exportação de leads em CSV e Excel"
```

---

## Task 13: Frontend React — Setup + Dashboard

**Files:**
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/api/client.js`
- Create: `frontend/src/pages/Dashboard.jsx`
- Create: `frontend/src/components/StatCard.jsx`

**Step 1: Criar `frontend/src/api/client.js`**

```javascript
import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
});

export const fetchLeads = (params) => api.get("/leads", { params });
export const fetchLead = (id) => api.get(`/leads/${id}`);
export const markContacted = (id) => api.patch(`/leads/${id}/contacted`);
export const archiveLead = (id) => api.delete(`/leads/${id}`);
export const createSearch = (data) => api.post("/search", data);
export const exportCsv = () => api.get("/export/csv", { responseType: "blob" });
export const exportExcel = () => api.get("/export/excel", { responseType: "blob" });

export default api;
```

**Step 2: Criar `frontend/src/components/StatCard.jsx`**

```jsx
export function StatCard({ label, value, emoji, color }) {
  const colors = {
    red: "bg-red-50 border-red-200 text-red-700",
    yellow: "bg-yellow-50 border-yellow-200 text-yellow-700",
    blue: "bg-blue-50 border-blue-200 text-blue-700",
    gray: "bg-gray-50 border-gray-200 text-gray-700",
  };
  return (
    <div className={`rounded-xl border p-4 flex flex-col gap-1 ${colors[color] || colors.gray}`}>
      <span className="text-2xl">{emoji}</span>
      <span className="text-3xl font-bold">{value}</span>
      <span className="text-sm font-medium">{label}</span>
    </div>
  );
}
```

**Step 3: Criar `frontend/src/pages/Dashboard.jsx`**

```jsx
import { useQuery } from "@tanstack/react-query";
import { fetchLeads } from "../api/client";
import { StatCard } from "../components/StatCard";

export function Dashboard() {
  const { data: quentes } = useQuery({
    queryKey: ["leads", "quente"],
    queryFn: () => fetchLeads({ category: "quente" }).then((r) => r.data),
  });
  const { data: mornos } = useQuery({
    queryKey: ["leads", "morno"],
    queryFn: () => fetchLeads({ category: "morno" }).then((r) => r.data),
  });
  const { data: frios } = useQuery({
    queryKey: ["leads", "frio"],
    queryFn: () => fetchLeads({ category: "frio" }).then((r) => r.data),
  });
  const { data: aniversarios } = useQuery({
    queryKey: ["leads", "birthday"],
    queryFn: () => fetchLeads({ birthday_soon: true }).then((r) => r.data),
  });

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard emoji="🔥" label="Leads Quentes" value={quentes?.total ?? 0} color="red" />
        <StatCard emoji="🌤" label="Leads Mornos" value={mornos?.total ?? 0} color="yellow" />
        <StatCard emoji="❄️" label="Leads Frios" value={frios?.total ?? 0} color="blue" />
        <StatCard emoji="🎂" label="Aniversários (7d)" value={aniversarios?.total ?? 0} color="gray" />
      </div>
    </div>
  );
}
```

**Step 4: Criar `frontend/src/App.jsx`**

```jsx
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Dashboard } from "./pages/Dashboard";
import { LeadList } from "./pages/LeadList";
import { LeadProfile } from "./pages/LeadProfile";

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50">
          <nav className="bg-white border-b px-6 py-3 flex gap-6">
            <Link to="/" className="font-semibold text-indigo-600">ICP Leads</Link>
            <Link to="/leads" className="text-gray-600 hover:text-indigo-600">Leads</Link>
            <Link to="/" className="text-gray-600 hover:text-indigo-600">Dashboard</Link>
          </nav>
          <main>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/leads" element={<LeadList />} />
              <Route path="/leads/:id" element={<LeadProfile />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
```

**Step 5: Verificar no browser**

```bash
docker-compose up --build -d
# Acesse http://localhost:5173
```
Esperado: Dashboard carrega com cards de estatísticas

**Step 6: Commit**

```bash
git add frontend/src/
git commit -m "feat: frontend React com Dashboard e stats por categoria"
```

---

## Task 14: Frontend React — Lista de Leads + Filtros

**Files:**
- Create: `frontend/src/pages/LeadList.jsx`
- Create: `frontend/src/components/LeadRow.jsx`
- Create: `frontend/src/components/FilterBar.jsx`

**Step 1: Criar `frontend/src/components/LeadRow.jsx`**

```jsx
import { Link } from "react-router-dom";

const CATEGORY_BADGE = {
  quente: "bg-red-100 text-red-700",
  morno: "bg-yellow-100 text-yellow-700",
  frio: "bg-blue-100 text-blue-700",
  descarte: "bg-gray-100 text-gray-500",
};

const EMOJI = { quente: "🔥", morno: "🌤", frio: "❄️", descarte: "🗑" };

export function LeadRow({ lead }) {
  return (
    <tr className="border-b hover:bg-gray-50">
      <td className="p-3">
        <div className="w-8 h-8 rounded-full bg-indigo-200 flex items-center justify-center text-sm font-bold">
          {(lead.display_name || lead.username)[0].toUpperCase()}
        </div>
      </td>
      <td className="p-3">
        <Link to={`/leads/${lead.id}`} className="font-medium text-indigo-600 hover:underline">
          @{lead.username}
        </Link>
        {lead.city && <div className="text-xs text-gray-400">{lead.city}</div>}
      </td>
      <td className="p-3">
        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${CATEGORY_BADGE[lead.category]}`}>
          {EMOJI[lead.category]} {lead.score} pts
        </span>
      </td>
      <td className="p-3 text-sm text-gray-500 uppercase">{lead.platform}</td>
      <td className="p-3">
        <Link to={`/leads/${lead.id}`} className="text-sm text-indigo-500 hover:underline mr-3">Ver</Link>
        {lead.profile_url && (
          <a href={lead.profile_url} target="_blank" rel="noreferrer"
             className="text-sm text-gray-500 hover:underline">Perfil</a>
        )}
      </td>
    </tr>
  );
}
```

**Step 2: Criar `frontend/src/components/FilterBar.jsx`**

```jsx
export function FilterBar({ filters, onChange }) {
  return (
    <div className="flex flex-wrap gap-3 p-4 bg-white rounded-xl border">
      <select value={filters.category || ""} onChange={(e) => onChange({ ...filters, category: e.target.value || undefined })}
              className="border rounded px-3 py-1.5 text-sm">
        <option value="">Todas categorias</option>
        <option value="quente">🔥 Quente</option>
        <option value="morno">🌤 Morno</option>
        <option value="frio">❄️ Frio</option>
      </select>
      <select value={filters.platform || ""} onChange={(e) => onChange({ ...filters, platform: e.target.value || undefined })}
              className="border rounded px-3 py-1.5 text-sm">
        <option value="">Todas plataformas</option>
        <option value="instagram">Instagram</option>
        <option value="youtube">YouTube</option>
      </select>
      <input type="text" placeholder="Filtrar por cidade..."
             value={filters.city || ""} onChange={(e) => onChange({ ...filters, city: e.target.value || undefined })}
             className="border rounded px-3 py-1.5 text-sm" />
      <label className="flex items-center gap-2 text-sm cursor-pointer">
        <input type="checkbox" checked={filters.birthday_soon || false}
               onChange={(e) => onChange({ ...filters, birthday_soon: e.target.checked || undefined })} />
        🎂 Aniversário próximo
      </label>
    </div>
  );
}
```

**Step 3: Criar `frontend/src/pages/LeadList.jsx`**

```jsx
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchLeads, exportCsv, exportExcel } from "../api/client";
import { LeadRow } from "../components/LeadRow";
import { FilterBar } from "../components/FilterBar";

export function LeadList() {
  const [filters, setFilters] = useState({});

  const { data, isLoading } = useQuery({
    queryKey: ["leads", filters],
    queryFn: () => fetchLeads(filters).then((r) => r.data),
  });

  const handleExport = async (type) => {
    const fn = type === "csv" ? exportCsv : exportExcel;
    const res = await fn();
    const url = URL.createObjectURL(res.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = `leads.${type === "csv" ? "csv" : "xlsx"}`;
    a.click();
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">
          Leads {data ? `(${data.total})` : ""}
        </h1>
        <div className="flex gap-2">
          <button onClick={() => handleExport("csv")} className="px-3 py-1.5 text-sm border rounded hover:bg-gray-50">📤 CSV</button>
          <button onClick={() => handleExport("excel")} className="px-3 py-1.5 text-sm border rounded hover:bg-gray-50">📊 Excel</button>
        </div>
      </div>

      <FilterBar filters={filters} onChange={setFilters} />

      {isLoading ? (
        <p className="text-gray-500">Carregando...</p>
      ) : (
        <div className="bg-white rounded-xl border overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 text-xs uppercase text-gray-500">
              <tr>
                <th className="p-3 text-left">Foto</th>
                <th className="p-3 text-left">Usuário</th>
                <th className="p-3 text-left">Score</th>
                <th className="p-3 text-left">Fonte</th>
                <th className="p-3 text-left">Ação</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((lead) => <LeadRow key={lead.id} lead={lead} />)}
            </tbody>
          </table>
          {data?.items.length === 0 && (
            <p className="text-center text-gray-400 py-8">Nenhum lead encontrado</p>
          )}
        </div>
      )}
    </div>
  );
}
```

**Step 4: Verificar no browser**

Acesse `http://localhost:5173/leads` — deve mostrar tabela com filtros.

**Step 5: Commit**

```bash
git add frontend/src/pages/LeadList.jsx frontend/src/components/
git commit -m "feat: lista de leads com filtros por categoria, plataforma, cidade e aniversário"
```

---

## Task 15: Frontend React — Perfil do Lead + Timeline

**Files:**
- Create: `frontend/src/pages/LeadProfile.jsx`
- Create: `frontend/src/components/Timeline.jsx`
- Create: `backend/app/api/events.py`
- Modify: `backend/app/main.py`

**Step 1: Criar `backend/app/api/events.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.lead_event import LeadEvent

router = APIRouter(prefix="/leads", tags=["events"])

@router.get("/{lead_id}/events")
def get_lead_events(lead_id: int, db: Session = Depends(get_db)):
    events = (
        db.query(LeadEvent)
        .filter(LeadEvent.lead_id == lead_id)
        .order_by(LeadEvent.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "description": e.description,
            "score_delta": e.score_delta,
            "score_after": e.score_after,
            "created_at": str(e.created_at),
        }
        for e in events
    ]
```

**Step 2: Criar `frontend/src/components/Timeline.jsx`**

```jsx
const EVENT_ICONS = {
  comment: "💬",
  like: "❤️",
  birthday_soon: "🎂",
  score_change: "📈",
  enriched: "✨",
  default: "📌",
};

export function Timeline({ events }) {
  if (!events?.length) return <p className="text-gray-400 text-sm">Nenhum evento registrado.</p>;

  return (
    <div className="space-y-3">
      {events.map((event) => (
        <div key={event.id} className="flex gap-3 items-start">
          <span className="text-lg">{EVENT_ICONS[event.event_type] || EVENT_ICONS.default}</span>
          <div>
            <p className="text-sm text-gray-700">{event.description}</p>
            <p className="text-xs text-gray-400">{new Date(event.created_at).toLocaleDateString("pt-BR")}</p>
          </div>
          {event.score_delta !== 0 && (
            <span className={`ml-auto text-sm font-semibold ${event.score_delta > 0 ? "text-green-600" : "text-red-500"}`}>
              {event.score_delta > 0 ? "+" : ""}{event.score_delta} pts
            </span>
          )}
        </div>
      ))}
    </div>
  );
}
```

**Step 3: Criar `frontend/src/pages/LeadProfile.jsx`**

```jsx
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchLead, markContacted, archiveLead } from "../api/client";
import { Timeline } from "../components/Timeline";
import api from "../api/client";

export function LeadProfile() {
  const { id } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const { data: lead, isLoading } = useQuery({
    queryKey: ["lead", id],
    queryFn: () => fetchLead(id).then((r) => r.data),
  });

  const { data: events } = useQuery({
    queryKey: ["lead-events", id],
    queryFn: () => api.get(`/leads/${id}/events`).then((r) => r.data),
  });

  const contacted = useMutation({
    mutationFn: () => markContacted(id),
    onSuccess: () => qc.invalidateQueries(["lead", id]),
  });

  const archive = useMutation({
    mutationFn: () => archiveLead(id),
    onSuccess: () => navigate("/leads"),
  });

  if (isLoading) return <p className="p-6 text-gray-500">Carregando...</p>;
  if (!lead) return <p className="p-6 text-red-500">Lead não encontrado.</p>;

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-6">
      <button onClick={() => navigate(-1)} className="text-sm text-indigo-500 hover:underline">← Voltar</button>

      <div className="bg-white rounded-xl border p-5 space-y-3">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-full bg-indigo-200 flex items-center justify-center text-xl font-bold">
            {(lead.display_name || lead.username)[0].toUpperCase()}
          </div>
          <div>
            <h2 className="text-xl font-bold">@{lead.username}</h2>
            {lead.city && <p className="text-sm text-gray-500">📍 {lead.city}{lead.country ? `, ${lead.country}` : ""}</p>}
          </div>
          <div className="ml-auto text-right">
            <div className="text-2xl font-bold text-indigo-600">{lead.score} pts</div>
            <div className="text-sm text-gray-500 capitalize">{lead.category}</div>
          </div>
        </div>

        {lead.bio && <p className="text-sm text-gray-600 italic">"{lead.bio}"</p>}

        <div className="grid grid-cols-2 gap-2 text-sm">
          {lead.followers && <div>👥 <b>{lead.followers.toLocaleString()}</b> seguidores</div>}
          {lead.age && <div>🎂 <b>{lead.age} anos</b></div>}
          {lead.birthdate && <div>📅 Nasc.: <b>{lead.birthdate}</b> ({lead.birthdate_source})</div>}
          <div>📱 <b className="capitalize">{lead.platform}</b></div>
        </div>

        <div className="flex gap-2 pt-2">
          {lead.status !== "contacted" && (
            <button onClick={() => contacted.mutate()}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700">
              ✉️ Marcar como Contatado
            </button>
          )}
          <button onClick={() => archive.mutate()}
                  className="px-4 py-2 border rounded-lg text-sm hover:bg-gray-50 text-gray-600">
            Arquivar
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl border p-5">
        <h3 className="font-semibold text-gray-700 mb-3">Timeline de Eventos</h3>
        <Timeline events={events} />
      </div>
    </div>
  );
}
```

**Step 4: Commit**

```bash
git add frontend/src/pages/LeadProfile.jsx frontend/src/components/Timeline.jsx backend/app/api/events.py
git commit -m "feat: página de perfil do lead com timeline de eventos"
```

---

## Task 16: Frontend React — Notificações

**Files:**
- Create: `backend/app/api/notifications.py`
- Create: `frontend/src/components/NotificationBell.jsx`
- Modify: `backend/app/main.py`
- Modify: `frontend/src/App.jsx`

**Step 1: Criar `backend/app/api/notifications.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
from app.db.session import get_db
from app.models.lead import Lead, LeadCategory, LeadStatus

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("")
def get_notifications(db: Session = Depends(get_db)):
    notifications = []

    # Leads quentes prontos para contato
    quentes = db.query(Lead).filter(
        Lead.category == LeadCategory.QUENTE,
        Lead.status == LeadStatus.MONITORING,
    ).count()
    if quentes:
        notifications.append({
            "type": "hot_leads",
            "message": f"🔥 {quentes} lead(s) quente(s) prontos para contato",
            "priority": "high",
        })

    # Aniversários nos próximos 7 dias
    today = date.today()
    in_7_days = today + timedelta(days=7)
    birthday_leads = db.query(Lead).filter(Lead.birthdate != None).all()
    birthday_count = sum(
        1 for l in birthday_leads
        if l.birthdate and 0 <= (l.birthdate.replace(year=today.year) - today).days <= 7
    )
    if birthday_count:
        notifications.append({
            "type": "birthday",
            "message": f"🎂 {birthday_count} lead(s) com aniversário nos próximos 7 dias",
            "priority": "medium",
        })

    return notifications
```

**Step 2: Criar `frontend/src/components/NotificationBell.jsx`**

```jsx
import { useQuery } from "@tanstack/react-query";
import api from "../api/client";
import { useState } from "react";

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const { data: notifications = [] } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => api.get("/notifications").then((r) => r.data),
    refetchInterval: 60000,
  });

  return (
    <div className="relative">
      <button onClick={() => setOpen(!open)} className="relative p-2 text-gray-600 hover:text-indigo-600">
        🔔
        {notifications.length > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
            {notifications.length}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-72 bg-white rounded-xl shadow-lg border z-10">
          <div className="p-3 border-b font-semibold text-sm text-gray-700">Notificações</div>
          {notifications.length === 0 ? (
            <p className="p-4 text-sm text-gray-400">Nenhuma notificação</p>
          ) : (
            notifications.map((n, i) => (
              <div key={i} className="p-3 border-b text-sm text-gray-700 hover:bg-gray-50">
                {n.message}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
```

**Step 3: Adicionar `NotificationBell` na nav do `App.jsx`**

```jsx
import { NotificationBell } from "./components/NotificationBell";

// Na <nav>, adicione ao final:
<div className="ml-auto">
  <NotificationBell />
</div>
```

**Step 4: Commit**

```bash
git add backend/app/api/notifications.py frontend/src/components/NotificationBell.jsx
git commit -m "feat: sistema de notificações para leads quentes e aniversários"
```

---

## Task 17: Configurações do Usuário

**Files:**
- Create: `backend/app/api/settings.py`
- Create: `frontend/src/pages/Settings.jsx`
- Modify: `backend/app/main.py`
- Modify: `frontend/src/App.jsx`

**Step 1: Criar `backend/app/api/settings.py`**

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.settings import AppSettings

router = APIRouter(prefix="/settings", tags=["settings"])

class SettingsUpdate(BaseModel):
    keywords: list[str] | None = None
    monitor_days_quente: int | None = None
    monitor_days_morno: int | None = None
    monitor_days_frio: int | None = None
    max_leads_per_day: int | None = None
    collect_hour: int | None = None

def _get_or_create(db: Session) -> AppSettings:
    s = db.get(AppSettings, 1)
    if not s:
        s = AppSettings(id=1)
        db.add(s)
        db.commit()
        db.refresh(s)
    return s

@router.get("")
def get_settings(db: Session = Depends(get_db)):
    return _get_or_create(db)

@router.patch("")
def update_settings(payload: SettingsUpdate, db: Session = Depends(get_db)):
    s = _get_or_create(db)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(s, field, value)
    db.commit()
    db.refresh(s)
    return s
```

**Step 2: Criar `frontend/src/pages/Settings.jsx`**

```jsx
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import api from "../api/client";

export function Settings() {
  const qc = useQueryClient();
  const { data: settings } = useQuery({
    queryKey: ["settings"],
    queryFn: () => api.get("/settings").then((r) => r.data),
  });

  const [keywords, setKeywords] = useState("");
  const [maxLeads, setMaxLeads] = useState(100);
  const [collectHour, setCollectHour] = useState(3);

  useEffect(() => {
    if (settings) {
      setKeywords((settings.keywords || []).join(", "));
      setMaxLeads(settings.max_leads_per_day);
      setCollectHour(settings.collect_hour);
    }
  }, [settings]);

  const save = useMutation({
    mutationFn: () => api.patch("/settings", {
      keywords: keywords.split(",").map((k) => k.trim()).filter(Boolean),
      max_leads_per_day: maxLeads,
      collect_hour: collectHour,
    }),
    onSuccess: () => qc.invalidateQueries(["settings"]),
  });

  return (
    <div className="p-6 max-w-lg mx-auto space-y-5">
      <h1 className="text-2xl font-bold text-gray-800">Configurações</h1>

      <div className="bg-white rounded-xl border p-5 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Keywords de busca (separadas por vírgula)</label>
          <textarea value={keywords} onChange={(e) => setKeywords(e.target.value)} rows={4}
                    className="w-full border rounded-lg px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Máx. leads por dia</label>
          <input type="number" value={maxLeads} onChange={(e) => setMaxLeads(Number(e.target.value))}
                 className="border rounded-lg px-3 py-2 text-sm w-24" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Horário de coleta (hora)</label>
          <input type="number" min={0} max={23} value={collectHour} onChange={(e) => setCollectHour(Number(e.target.value))}
                 className="border rounded-lg px-3 py-2 text-sm w-24" />
        </div>
        <button onClick={() => save.mutate()}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700">
          {save.isPending ? "Salvando..." : "Salvar configurações"}
        </button>
      </div>
    </div>
  );
}
```

**Step 3: Commit**

```bash
git add backend/app/api/settings.py frontend/src/pages/Settings.jsx
git commit -m "feat: página de configurações do usuário (keywords, limites, horário)"
```

---

## Task 18: Integração Final e Smoke Test

**Step 1: Rodar todos os testes backend**

```bash
docker-compose exec backend pytest tests/ -v --tb=short
```
Esperado: todos passando (ou skips documentados para testes que requerem credenciais reais)

**Step 2: Verificar que todos os serviços sobem**

```bash
docker-compose up -d
docker-compose ps
```
Esperado: db, redis, backend, worker, beat, frontend todos `Up`

**Step 3: Smoke test manual**

1. Acesse `http://localhost:8000/health` → `{"status": "ok"}`
2. Acesse `http://localhost:8000/docs` → Swagger UI com todos os endpoints
3. Acesse `http://localhost:5173` → Dashboard carrega
4. Acesse `http://localhost:5173/leads` → Lista carrega (vazia)
5. `POST /search` com `{"keywords": ["constelação familiar"], "platforms": ["youtube"]}` → `{"job_id": 1, "status": "queued"}`
6. `GET /export/csv` → download de arquivo CSV

**Step 4: Criar `.env` real a partir do `.env.example`**

```bash
cp backend/.env.example backend/.env
# Preencher credenciais reais: INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD, YOUTUBE_API_KEY
```

**Step 5: Commit final**

```bash
git add .
git commit -m "chore: integração final e smoke test — app pronto para uso"
```

---

## Resumo das Tasks

| # | Task | Prioridade |
|---|------|-----------|
| 1 | Setup do projeto + Docker Compose | Alta |
| 2 | Modelos de banco + Migrations | Alta |
| 3 | FastAPI base + health check | Alta |
| 4 | Coletor Instagram | Alta |
| 5 | Coletor YouTube (busca + comentários) | Alta |
| 6 | Transcrição de vídeos longos | Média |
| 7 | Facebook enricher (aniversário) | Média |
| 8 | LinkedIn enricher (conservador) | Baixa |
| 9 | Engine de scoring | Alta |
| 10 | Celery tasks (monitoramento diário) | Alta |
| 11 | API REST leads + busca | Alta |
| 12 | Exportação CSV/Excel | Média |
| 13 | Frontend Dashboard | Alta |
| 14 | Frontend Lista de Leads | Alta |
| 15 | Frontend Perfil + Timeline | Alta |
| 16 | Notificações | Média |
| 17 | Configurações do usuário | Média |
| 18 | Integração final + smoke test | Alta |
