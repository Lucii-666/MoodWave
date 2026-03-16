"""
scripts/build_embeddings.py
───────────────────────────
Build artist-level semantic profiles from MD-1M.csv,
embed them with SentenceTransformers, and index with FAISS.

Usage:
    python scripts/build_embeddings.py                   # full dataset
    python scripts/build_embeddings.py --sample 10000    # quick test
"""

from __future__ import annotations

import argparse
import pickle
import sys
import time
from pathlib import Path

import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

# ── Resolve project root ─────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

CSV_PATH = ROOT / "MD-1M.csv"
INDEX_PATH = DATA_DIR / "faiss_index.bin"
PROFILES_PATH = DATA_DIR / "artist_profiles.pkl"


def build_artist_profiles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate song-level metadata into artist-level text profiles.

    Each profile concatenates genre, sub-genre, emotions, playlist context,
    narrative arc, and other descriptive columns — giving the embedding model
    rich semantic signal for mood-based matching.
    """
    print(f"  → {len(df):,} songs loaded, {df['Primary_Singer'].nunique():,} unique artists")

    # Build a rich text profile per song
    profile_cols = [
        "Genre", "Sub_Genre",
        "Primary_Emotion", "Secondary_Emotion",
        "Primary_Playlist_Context", "Typical_Listening_Time",
        "Seasonal_Relevance", "Narrative_Arc", "Mode",
    ]

    def _row_profile(row: pd.Series) -> str:
        parts = []
        for col in profile_cols:
            val = row.get(col)
            if pd.notna(val) and str(val).strip():
                parts.append(str(val).strip())
        return " ".join(parts)

    df["_profile"] = df.apply(_row_profile, axis=1)

    # Aggregate per artist (join all song profiles)
    artist_df = (
        df.groupby("Primary_Singer")["_profile"]
        .apply(lambda texts: " ".join(texts))
        .reset_index()
    )
    artist_df.columns = ["artist", "profile"]

    # Also grab representative genre + emotion for display
    meta = (
        df.groupby("Primary_Singer")
        .agg(
            genre=("Genre", lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else "Unknown"),
            primary_emotion=("Primary_Emotion", lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else "Unknown"),
            song_count=("Song_ID", "count"),
        )
        .reset_index()
    )
    meta.columns = ["artist", "genre", "primary_emotion", "song_count"]

    artist_df = artist_df.merge(meta, on="artist", how="left")

    print(f"  → {len(artist_df):,} artist profiles built")
    return artist_df


def embed_and_index(artist_df: pd.DataFrame, model_name: str = "all-MiniLM-L6-v2"):
    """Embed artist profiles and build a FAISS inner-product index."""

    print(f"  → Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)

    profiles = artist_df["profile"].tolist()
    print(f"  → Encoding {len(profiles):,} profiles …")

    t0 = time.time()
    embeddings = model.encode(
        profiles,
        batch_size=256,
        show_progress_bar=True,
        convert_to_numpy=True,
    )
    elapsed = time.time() - t0
    print(f"  → Encoded in {elapsed:.1f}s  |  shape = {embeddings.shape}")

    # L2-normalize so inner product = cosine similarity
    embeddings = embeddings.astype(np.float32)
    faiss.normalize_L2(embeddings)

    # Build index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    print(f"  → FAISS index built: {index.ntotal} vectors, dim={dim}")

    return index, embeddings


def save_artifacts(index, artist_df: pd.DataFrame):
    """Persist the FAISS index and artist profiles to disk."""
    faiss.write_index(index, str(INDEX_PATH))
    print(f"  → Saved FAISS index → {INDEX_PATH}")

    # Save artist_df (without the huge profile text to save space)
    save_df = artist_df[["artist", "genre", "primary_emotion", "song_count"]].copy()
    with open(PROFILES_PATH, "wb") as f:
        pickle.dump(save_df, f)
    print(f"  → Saved artist profiles → {PROFILES_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Build MoodWave embeddings")
    parser.add_argument(
        "--sample", type=int, default=None,
        help="Use only N rows from the CSV (for quick testing)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  MoodWave — Embedding Pipeline")
    print("=" * 60)

    # 1. Load CSV
    print("\n[1/4] Loading dataset …")
    if args.sample:
        df = pd.read_csv(CSV_PATH, nrows=args.sample)
        print(f"  → Sampled {args.sample:,} rows")
    else:
        df = pd.read_csv(CSV_PATH)
    print(f"  → Dataset shape: {df.shape}")

    # 2. Build artist profiles
    print("\n[2/4] Building artist profiles …")
    artist_df = build_artist_profiles(df)

    # 3. Embed + index
    print("\n[3/4] Embedding & indexing …")
    index, _embeddings = embed_and_index(artist_df)

    # 4. Save
    print("\n[4/4] Saving artifacts …")
    save_artifacts(index, artist_df)

    print("\n✅ Done! Embeddings ready for MoodWave.")
    print(f"   Index:    {INDEX_PATH}")
    print(f"   Profiles: {PROFILES_PATH}")


if __name__ == "__main__":
    main()
