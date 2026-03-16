"""
hmas.core.config
────────────────
Central configuration — environment variables, model paths, energy-label
boundaries, LLM provider settings.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class LLMProvider(str, Enum):
    OPENAI    = "openai"
    ANTHROPIC = "anthropic"
    LOCAL     = "local"


class Settings(BaseSettings):
    """
    All values can be overridden by env vars prefixed with ``HMAS_``.
    e.g.  ``HMAS_LLM_PROVIDER=anthropic``
    """

    # ── Paths ─────────────────────────────────────────────────────────────
    dataset_path: Path = Field(
        default=Path("MD-1M.csv"),
        description="Path to the MER-1M master CSV",
    )

    # ── LLM ───────────────────────────────────────────────────────────────
    llm_provider: LLMProvider = LLMProvider.OPENAI
    openai_api_key: Optional[str]    = None
    openai_model: str                = "gpt-4o"
    anthropic_api_key: Optional[str] = None
    anthropic_model: str             = "claude-sonnet-4-20250514"
    local_model_url: str             = "http://localhost:11434/v1"
    local_model_name: str            = "llama3"
    llm_temperature: float           = 0.3
    llm_max_tokens: int              = 1024

    # ── ML Classification ─────────────────────────────────────────────────
    default_classifier: str = "random_forest"  # or "xgboost"

    # ── Energy-label bin edges (applied to the 0-1 Energy column) ─────────
    energy_low_upper: float      = 0.35
    energy_medium_upper: float   = 0.60
    energy_high_upper: float     = 0.80
    # anything above high_upper → Very High

    # ── Embedding / FAISS ─────────────────────────────────────────────────
    faiss_index_path: Path = Field(
        default=Path("data/faiss_index.bin"),
        description="Path to the saved FAISS index",
    )
    artist_profiles_path: Path = Field(
        default=Path("data/artist_profiles.pkl"),
        description="Path to the pickled artist profiles DataFrame",
    )
    embedding_model_name: str = "all-MiniLM-L6-v2"

    # ── TinyFish Agent ────────────────────────────────────────────────────
    tinyfish_api_key: Optional[str] = None
    tinyfish_api_url: str = "https://agent.tinyfish.ai/v1/automation/run-sse"

    # ── API ───────────────────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool   = False

    model_config = {
        "env_prefix": "HMAS_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


# Singleton (import `settings` anywhere)
settings = Settings()
