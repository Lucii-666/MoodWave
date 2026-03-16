"""
hmas.api.main
─────────────
FastAPI application — the "Bridge" layer of MoodWave.

Endpoints:
  POST /recommend     → Mood-to-artist semantic search (FAISS)
  POST /agent/run     → TinyFish SSE proxy for live event discovery
  GET  /health        → Health check
"""

from __future__ import annotations

import json
from contextlib import asynccontextmanager

import httpx

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
from pydantic import BaseModel, Field

from hmas.agents.tinyfish_client import run_agent_async
from hmas.core.config import settings
from hmas.core.recommender import MoodRecommender


# ── Lifespan: preload models on startup ───────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the FAISS index + embedding model once at startup."""
    print("🎵 MoodWave starting up …")
    try:
        MoodRecommender.get()  # triggers lazy load
        print("✅ Recommender ready")
    except FileNotFoundError as e:
        print(f"⚠️  {e}")
        print("   Run: python scripts/build_embeddings.py")
    yield
    print("🎵 MoodWave shutting down")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="MoodWave API",
    description=(
        "AI-powered music curation & live event discovery engine. "
        "Maps human moods to artists via 1M-song semantic embeddings, "
        "then uses TinyFish Web Agent to find real-time tickets on live websites."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ─────────────────────────────────────────────────

class MoodRequest(BaseModel):
    mood: str = Field(..., min_length=1, max_length=500, description="Natural-language mood description")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of artists to return")


class ArtistResult(BaseModel):
    artist: str
    genre: str
    primary_emotion: str
    song_count: int
    score: float


class RecommendResponse(BaseModel):
    mood: str
    artists: list[ArtistResult]


class AgentRequest(BaseModel):
    artist: str = Field(..., min_length=1, max_length=200, description="Artist name to search for events")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Health check."""
    recommender_ready = MoodRecommender._instance is not None and MoodRecommender._instance._loaded
    return {
        "status": "ok",
        "service": "MoodWave",
        "recommender_loaded": recommender_ready,
        "tinyfish_configured": settings.tinyfish_api_key is not None,
    }


@app.post("/recommend", response_model=RecommendResponse)
async def recommend(req: MoodRequest):
    """
    Mood-to-Artist recommendation.

    Encodes the mood string into the same embedding space as 1M song profiles,
    then returns the top-K closest artists by cosine similarity.
    Typical latency: < 200ms.
    """
    try:
        recommender = MoodRecommender.get()
        artists = recommender.recommend(req.mood, req.top_k)
        return RecommendResponse(mood=req.mood, artists=artists)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {e}")


@app.post("/agent/run")
async def agent_run(req: AgentRequest):
    """
    TinyFish Web Agent SSE proxy.

    Launches the TinyFish agent to navigate live ticketing websites
    (Ticketmaster → Songkick → Bandsintown) and find real-time event
    data for the given artist.

    Returns a Server-Sent Events stream so the frontend can display
    each agent step in real-time (the "demo money shot").
    """
    if not settings.tinyfish_api_key:
        raise HTTPException(
            status_code=503,
            detail="TinyFish API key not configured. Set HMAS_TINYFISH_API_KEY in .env",
        )

    async def event_stream():
        try:
            async for event in run_agent_async(req.artist):
                yield f"data: {json.dumps(event)}\n\n"
            yield "data: [DONE]\n\n"
        except httpx.HTTPStatusError as e:
            error = {"type": "error", "content": f"TinyFish API error: {e.response.status_code}"}
            yield f"data: {json.dumps(error)}\n\n"
        except Exception as e:
            error = {"type": "error", "content": str(e)}
            yield f"data: {json.dumps(error)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Serve Frontend ──────────────────────────────────────────────────────────────

frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")

if os.path.isdir(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))

# ── Run directly ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "hmas.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
