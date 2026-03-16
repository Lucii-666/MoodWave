"""
hmas.models.blackboard
──────────────────────
The shared-state Blackboard that every agent reads from and writes to.

Design rules
────────────
1.  Agents NEVER call each other directly.
2.  Each agent reads the fields it needs, performs work, then writes its
    results back — always through the Blackboard.
3.  The Orchestrator manages the lifecycle: it creates the Blackboard,
    triggers agents in the correct order, and reads the final state.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .enums import EnergyLabel
from .track import AcousticFeatures, Track, TrackMetadata


# ── Pipeline status tracking ─────────────────────────────────────────────────

class AgentStatus(str, Enum):
    PENDING    = "pending"
    RUNNING    = "running"
    COMPLETED  = "completed"
    FAILED     = "failed"
    SKIPPED    = "skipped"


class AgentTrace(BaseModel):
    """Lightweight audit record written by each agent on completion."""

    agent_name: str
    status: AgentStatus   = AgentStatus.PENDING
    started_at: Optional[datetime]  = None
    finished_at: Optional[datetime] = None
    error: Optional[str]  = None

    def mark_running(self) -> None:
        self.status = AgentStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)

    def mark_completed(self) -> None:
        self.status = AgentStatus.COMPLETED
        self.finished_at = datetime.now(timezone.utc)

    def mark_failed(self, error: str) -> None:
        self.status = AgentStatus.FAILED
        self.finished_at = datetime.now(timezone.utc)
        self.error = error


# ── Typed payloads written by each agent layer ───────────────────────────────

class ClassificationResult(BaseModel):
    """Written by the Classification Agent."""

    predicted_energy_label: EnergyLabel
    confidence_score: float = Field(..., ge=0, le=1)
    model_name: str = Field(
        ..., description="e.g. 'RandomForest-v1' or 'XGBoost-v2'"
    )


class ContextSummary(BaseModel):
    """Written by the Context Agent."""

    release_context: str = Field(
        ..., description="Free-text about album type, label, language, etc."
    )
    genre_context: str = Field(
        ..., description="Genre + sub-genre positioning"
    )
    playlist_context: str = Field(
        ..., description="Playlist/mood/time-of-day association"
    )
    cultural_note: Optional[str] = Field(
        None, description="Seasonal, regional, or trend note"
    )


class ExplanationResult(BaseModel):
    """Written by the Profiling & Explanation Agent."""

    natural_language_explanation: str = Field(
        ..., description="Human-readable reasoning for the energy label"
    )
    key_contributing_features: list[str] = Field(
        default_factory=list,
        description="Top acoustic features that drove the classification",
    )
    llm_model_used: str = Field(
        ..., description="Which LLM generated the explanation"
    )


class SanityCheckResult(BaseModel):
    """Written by the Orchestrator's sanity-check protocol."""

    is_consistent: bool
    issues: list[str] = Field(default_factory=list)
    corrective_action: Optional[str] = None


# ── The Blackboard itself ────────────────────────────────────────────────────

class Blackboard(BaseModel):
    """
    Central mutable state object for a single pipeline run.

    Lifecycle
    ---------
    1. Orchestrator creates it with `query` + a unique `run_id`.
    2. Feature Extraction Agent writes `track`, `track_metadata`,
       `acoustic_features`, and `feature_vector_42`.
    3. Classification Agent writes `classification`.
    4. Context Agent writes `context_summary`.
    5. Explanation Agent writes `explanation`.
    6. Orchestrator runs sanity check → writes `sanity_check` → returns.
    """

    # ── Identity ──────────────────────────────────────────────────────────
    run_id: str = Field(
        default_factory=lambda: uuid.uuid4().hex[:12],
        description="Unique id for this pipeline execution",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    # ── Input ─────────────────────────────────────────────────────────────
    query: str = Field(
        ..., description="Raw natural-language user query"
    )
    resolved_song_id: Optional[str] = Field(
        None, description="Song_ID resolved from the query (set by Orchestrator)"
    )

    # ── Perception Layer outputs ──────────────────────────────────────────
    track: Optional[Track]               = None
    track_metadata: Optional[TrackMetadata] = None
    acoustic_features: Optional[AcousticFeatures] = None
    feature_vector_42: Optional[list[float]] = Field(
        None,
        min_length=42, max_length=42,
        description="Expanded 42-dimensional numeric vector for ML model input",
    )
    classification: Optional[ClassificationResult] = None

    # ── Cognitive Layer outputs ───────────────────────────────────────────
    context_summary: Optional[ContextSummary] = None
    explanation: Optional[ExplanationResult]   = None

    # ── Orchestration outputs ─────────────────────────────────────────────
    sanity_check: Optional[SanityCheckResult] = None
    final_response: Optional[str] = Field(
        None, description="Fully composed answer returned to the user"
    )

    # ── Observability ─────────────────────────────────────────────────────
    agent_traces: list[AgentTrace] = Field(default_factory=list)

    # ── Helpers ───────────────────────────────────────────────────────────

    def add_trace(self, agent_name: str) -> AgentTrace:
        """Create a new trace, append it, and return a handle."""
        trace = AgentTrace(agent_name=agent_name)
        self.agent_traces.append(trace)
        return trace

    @property
    def is_complete(self) -> bool:
        """True when every pipeline stage has written its output."""
        return all([
            self.track is not None,
            self.classification is not None,
            self.context_summary is not None,
            self.explanation is not None,
            self.sanity_check is not None,
        ])

    model_config = {"arbitrary_types_allowed": True}
