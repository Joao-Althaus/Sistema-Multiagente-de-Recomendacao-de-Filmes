"""
Tool: keyword_search

Busca filmes por correspondência textual nos campos de metadados.
Utilizado como sinal complementar na busca híbrida.

Campos pesquisáveis:
    - title    : correspondência parcial no título
    - cast     : nome de ator presente na lista de elenco
    - director : nome do diretor

Input:
    field   : str   — campo a pesquisar ('title' | 'cast' | 'director')
    query   : str   — termo de busca

Output:
    List[dict] com os mesmos campos de metadata + keyword_score (0.0–1.0)
"""

import json
from typing import List

from core.rag_engine import RAGEngine


def keyword_search(rag: RAGEngine, terms: List[str], top_n: int = 20) -> str:
    scores = rag.keyword_search(terms)

    import numpy as np
    top_indices = np.argsort(scores)[::-1][:top_n]

    results = []
    for idx in top_indices:
        if scores[idx] == 0:
            break
        entry = dict(rag.metadata[idx])
        entry["keyword_score"] = float(scores[idx])
        results.append(entry)

    return json.dumps(results, ensure_ascii=False)
