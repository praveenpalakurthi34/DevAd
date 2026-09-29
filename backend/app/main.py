from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from contextlib import asynccontextmanager
from .config import settings
from .db import init_db
from .api import campaigns, generation, memory, outcomes, dashboard, system, assets


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


MEDIA_DIR = Path(__file__).resolve().parents[1] / "generated"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="DevAd API",
    description="AI-powered advertising agent that remembers what worked",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(campaigns.router, prefix="/api", tags=["campaigns"])
app.include_router(generation.router, prefix="/api", tags=["generation"])
app.include_router(memory.router, prefix="/api", tags=["memory"])
app.include_router(outcomes.router, prefix="/api", tags=["outcomes"])
app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])
app.include_router(system.router, prefix="/api", tags=["system"])
app.include_router(assets.router, prefix="/api", tags=["assets"])
app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "DevAd API",
        "version": "1.0.0",
    }
