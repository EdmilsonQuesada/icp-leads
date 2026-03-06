from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.health import router as health_router
from app.api.leads import router as leads_router
from app.api.events import router as events_router
from app.api.search import router as search_router

app = FastAPI(title="ICP Lead Research — Constelação Familiar")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(leads_router)
app.include_router(events_router)
app.include_router(search_router)
