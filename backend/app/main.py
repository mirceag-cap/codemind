# FastAPI app entry point — creates the app and mounts all routers

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.health import router as health_router


# lifespan handles startup and shutdown logic cleanly
# anything before `yield` runs on startup, after yield runs on shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    print(f"🚀 {settings.app_name} starting up...")
    yield
    # shutdown
    print(f"👋 {settings.app_name} shutting down...")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Agentic codebase assistant",
    lifespan=lifespan,
)

# CORS lets the React frontend (running on a different port) call this API
# In production you'd lock this down to your actual domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default dev port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers — each router owns its own URL prefix
app.include_router(health_router, prefix="/api/v1", tags=["health"])
