"""
RAG Engine

Núcleo do sistema de recuperação. Carrega os artefatos gerados pelo
pipeline ETL (embeddings.npy, metadata.pkl, chunks.pkl) e implementa:

- Busca semântica: similaridade coseno entre query embedding e base
- Busca keyword:   match parcial em campos de metadata (cast, director, title, genres)
- Busca híbrida:   combinação ponderada dos dois sinais
    score_final = 0.6 * cosine_score + 0.4 * keyword_score
"""

import pickle
from pathlib import Path
from typing import List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from core.user_profile import UserProfile

_DATA_DIR = Path(__file__).parent.parent / "RAG" / "data"

class RAGEngine:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.embeddings = np.load(_DATA_DIR / "embeddings.npy")
        with open(_DATA_DIR / "metadata.pkl", "rb") as f:
            self.metadata: List[dict] = pickle.load(f)
        with open(_DATA_DIR / "chunks.pkl", "rb") as f:
            self.chunks: List[str] = pickle.load(f)

    # ------------------------------------------------------------------
    # Busca semântica
    # ------------------------------------------------------------------

    def semantic_search(self, query: str, top_n: int = 20) -> np.ndarray:
        """Retorna array de scores coseno para todos os filmes."""
        q_emb = self.model.encode([query], convert_to_numpy=True)
        scores = cosine_similarity(q_emb, self.embeddings)[0]
        return scores

    # ------------------------------------------------------------------
    # Busca keyword
    # ------------------------------------------------------------------

    def keyword_search(self, terms: List[str]) -> np.ndarray:
        """
        Match parcial (case-insensitive) dos termos em title, cast,
        director e genres. Score por filme = matches / total_terms.
        """
        scores = np.zeros(len(self.metadata), dtype=np.float32)
        if not terms:
            return scores

        normalized = [t.lower().strip() for t in terms if t.strip()]
        for i, meta in enumerate(self.metadata):
            searchable = " ".join([
                meta.get("title", ""),
                " ".join(meta.get("cast", [])),
                " ".join(meta.get("director", [])),
                " ".join(meta.get("genres", [])),
            ]).lower()
            hits = sum(1 for t in normalized if t in searchable)
            scores[i] = hits / len(normalized)

        return scores

    # ------------------------------------------------------------------
    # Busca híbrida
    # ------------------------------------------------------------------

    def hybrid_search(
        self,
        query: str,
        profile: Optional[UserProfile] = None,
        top_n: int = 20,
    ) -> List[dict]:
        """
        Combina busca semântica (60%) e keyword (40%).
        Retorna os top_n filmes como lista de dicts com campo 'score'.
        """
        semantic_scores = self.semantic_search(query)

        keyword_terms: List[str] = []
        if profile:
            keyword_terms = (
                profile.watched_movies
                + profile.favorite_actors
                + profile.favorite_directors
                + profile.favorite_genres
            )
        keyword_scores = self.keyword_search(keyword_terms)

        # Normaliza semantic para [0, 1]
        s_min, s_max = semantic_scores.min(), semantic_scores.max()
        if s_max > s_min:
            semantic_scores = (semantic_scores - s_min) / (s_max - s_min)

        final_scores = 0.6 * semantic_scores + 0.4 * keyword_scores

        top_indices = np.argsort(final_scores)[::-1][:top_n]

        results = []
        for idx in top_indices:
            entry = dict(self.metadata[idx])
            entry["score"] = float(final_scores[idx])
            entry["chunk"] = self.chunks[idx]
            results.append(entry)

        return results
