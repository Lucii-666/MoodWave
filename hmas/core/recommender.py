"""
hmas.core.recommender
─────────────────────
Mood-to-Artist recommendation engine.
Loads the FAISS index + artist profiles at startup, then provides
fast semantic search: encode a mood string → find top-K matching artists.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from .config import settings


class MoodRecommender:
    """Singleton-style recommender backed by FAISS cosine-similarity search."""

    _instance: Optional["MoodRecommender"] = None

    def __init__(self):
        self._model: Optional[SentenceTransformer] = None
        self._index: Optional[faiss.Index] = None
        self._artist_df = None
        self._loaded = False

    @classmethod
    def get(cls) -> "MoodRecommender":
        """Return the global singleton, creating it on first call."""
        if cls._instance is None:
            cls._instance = cls()
        if not cls._instance._loaded:
            cls._instance._load()
        return cls._instance

    def _load(self):
        """Load the embedding model, FAISS index, and artist profiles."""
        root = Path(__file__).resolve().parent.parent.parent  # project root

        index_path = root / settings.faiss_index_path
        profiles_path = root / settings.artist_profiles_path

        if not index_path.exists():
            raise FileNotFoundError(
                f"FAISS index not found at {index_path}. "
                "Run `python scripts/build_embeddings.py` first."
            )

        print(f"[Recommender] Loading model: {settings.embedding_model_name}")
        self._model = SentenceTransformer(settings.embedding_model_name)

        print(f"[Recommender] Loading FAISS index: {index_path}")
        self._index = faiss.read_index(str(index_path))

        print(f"[Recommender] Loading artist profiles: {profiles_path}")
        with open(profiles_path, "rb") as f:
            self._artist_df = pickle.load(f)

        self._loaded = True
        print(f"[Recommender] Ready! {self._index.ntotal} artists indexed.")

    def recommend(self, mood: str, top_k: int = 3) -> list[dict]:
        """
        Given a natural-language mood string, return the top-K matching artists.

        Returns:
            List of dicts: { artist, genre, primary_emotion, song_count, score }
        """
        if not self._loaded:
            self._load()

        # Encode the mood query
        q_vec = self._model.encode([mood])
        q_vec = q_vec.astype(np.float32)
        faiss.normalize_L2(q_vec)

        # Search
        scores, ids = self._index.search(q_vec, top_k)

        results = []
        for j, idx in enumerate(ids[0]):
            if idx < 0:  # FAISS returns -1 for empty slots
                continue
            row = self._artist_df.iloc[idx]
            results.append({
                "artist": row["artist"],
                "genre": row.get("genre", "Unknown"),
                "primary_emotion": row.get("primary_emotion", "Unknown"),
                "song_count": int(row.get("song_count", 0)),
                "score": round(float(scores[0][j]), 4),
            })

        return results
