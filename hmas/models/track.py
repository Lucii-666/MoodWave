"""
hmas.models.track
─────────────────
Pydantic schema for a single row in the MER-1M dataset (MD-1M.csv).
This is the **source-of-truth** representation; every downstream agent
consumes a validated Track instance (or a projection of it).
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .enums import (
    AlbumType,
    Emotion,
    Genre,
    ListeningTime,
    Mode,
    NarrativeArc,
    PlaylistContext,
    SeasonalRelevance,
    StructuralPattern,
    SubGenre,
)


class TrackMetadata(BaseModel):
    """Non-acoustic metadata attached to every track."""

    song_id: str                          = Field(..., alias="Song_ID",                    description="Unique 12-char hex identifier")
    song_name: str                        = Field(..., alias="Song_Name")
    primary_singer: str                   = Field(..., alias="Primary_Singer")
    featured_singers: Optional[str]       = Field(None, alias="Featured_Singers")
    album_name: str                       = Field(..., alias="Album_Name")
    album_type: AlbumType                 = Field(..., alias="Album_Type")
    language: str                         = Field(..., alias="Language")
    record_label: str                     = Field(..., alias="Record_Label")
    genre: Genre                          = Field(..., alias="Genre")
    sub_genre: SubGenre                   = Field(..., alias="Sub_Genre")
    primary_playlist_context: PlaylistContext = Field(..., alias="Primary_Playlist_Context")
    typical_listening_time: ListeningTime = Field(..., alias="Typical_Listening_Time")
    seasonal_relevance: SeasonalRelevance = Field(..., alias="Seasonal_Relevance")
    narrative_arc: NarrativeArc           = Field(..., alias="Narrative_Arc")
    explicit_content: bool                = Field(..., alias="Explicit_Content")

    model_config = {"populate_by_name": True}


class AcousticFeatures(BaseModel):
    """
    The 18 raw numeric features extracted per track.

    When combined with one-hot encodings of the 6 categorical feature
    groups (Mode[2] + Genre[18] + StructuralPattern[5] + NarrativeArc[7]
    + SubGenre[24] …) this expands to the full **42-dimensional** feature
    vector consumed by the Classification Agent.  The expansion is
    performed by `FeatureExtractionAgent.to_vector_42()`.
    """

    # ── Core Spotify-style audio descriptors ──────────────────────────────
    danceability: float          = Field(..., ge=0, le=1,    alias="Danceability")
    energy: float                = Field(..., ge=0, le=1,    alias="Energy")
    valence: float               = Field(..., ge=0, le=1,    alias="Valence")
    tempo_bpm: float             = Field(..., ge=0,          alias="Tempo_BPM")
    loudness_db: float           = Field(...,                alias="Loudness_dB",
                                         description="Typically negative, in dBFS")
    acousticness: float          = Field(..., ge=0, le=1,    alias="Acousticness")
    instrumentalness: float      = Field(..., ge=0, le=1,    alias="Instrumentalness")
    liveness: float              = Field(..., ge=0, le=1,    alias="Liveness")
    speechiness: float           = Field(..., ge=0, le=1,    alias="Speechiness")

    # ── Musical structure ─────────────────────────────────────────────────
    mode: Mode                   = Field(...,                alias="Mode")
    structural_pattern: StructuralPattern = Field(...,       alias="Structural_Pattern")

    # ── Behavioural / platform signals ────────────────────────────────────
    platform_popularity_index: float = Field(..., ge=0, le=100, alias="Platform_Popularity_Index")
    skip_rate_estimate: float    = Field(..., ge=0, le=1,    alias="Skip_Rate_Estimate")
    repeat_listen_probability: float = Field(..., ge=0, le=1, alias="Repeat_Listen_Probability")

    # ── Emotion ground-truth from the dataset ─────────────────────────────
    primary_emotion: Emotion     = Field(...,                alias="Primary_Emotion")
    secondary_emotion: Emotion   = Field(...,                alias="Secondary_Emotion")
    emotional_intensity: float   = Field(..., ge=0, le=1,    alias="Emotional_Intensity")

    # ── Production / composition descriptors ──────────────────────────────
    song_duration_ms: int        = Field(..., ge=0,          alias="Song_Duration_ms")
    vocal_presence: float        = Field(..., ge=0, le=1,    alias="Vocal_Presence")
    production_density: float    = Field(..., ge=0, le=1,    alias="Production_Density")
    lyric_abstraction_level: float = Field(..., ge=0, le=1,  alias="Lyric_Abstraction_Level")

    # ── Model target (kept for reference / evaluation) ────────────────────
    predicted_emotional_impact_score: float = Field(
        ..., ge=0, le=1, alias="Predicted_Emotional_Impact_Score",
    )

    model_config = {"populate_by_name": True}


class Track(BaseModel):
    """
    Complete representation of a single MER-1M track.
    Composed of metadata + acoustic features.
    """

    metadata: TrackMetadata
    features: AcousticFeatures

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> "Track":
        """
        Factory that accepts a raw CSV DictReader row (all strings)
        and splits it into the two sub-models.

        Pydantic coercion handles str→float / str→int / str→bool.
        """
        # Normalise empty strings to None for Optional fields
        cleaned = {k: (v if v != "" else None) for k, v in row.items()}
        # Map 'TRUE'/'FALSE' strings → Python bools
        if "Explicit_Content" in cleaned:
            cleaned["Explicit_Content"] = cleaned["Explicit_Content"] in ("TRUE", "True", "true", "1")
        return cls(
            metadata=TrackMetadata(**cleaned),
            features=AcousticFeatures(**cleaned),
        )

    @property
    def song_id(self) -> str:
        return self.metadata.song_id

    @property
    def display_name(self) -> str:
        feat = f" ft. {self.metadata.featured_singers}" if self.metadata.featured_singers else ""
        return f"{self.metadata.primary_singer}{feat} – {self.metadata.song_name}"
