"""
Tool: semantic_search

Recebe uma query em linguagem natural, gera seu embedding via
SentenceTransformer e retorna os N filmes mais similares por
similaridade coseno sobre os embeddings pré-computados.

Input:
    query   : str   — texto da busca
    top_n   : int   — quantidade de resultados (default 20)

Output:
    List[dict] com campos: id, title, year, genres, director,
                           cast, vote_average, overview, score
"""

import json

import numpy as np

from core.rag_engine import RAGEngine


def semantic_search(rag: RAGEngine, query: str, top_n: int = 20) -> str:
    scores = rag.semantic_search(query)
    top_indices = np.argsort(scores)[::-1][:top_n]

    results = []
    for idx in top_indices:
        entry = dict(rag.metadata[idx])
        entry["score"] = float(scores[idx])
        results.append(entry)

    return json.dumps(results, ensure_ascii=False)
