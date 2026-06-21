"""
Tool: filter_movies

Aplica filtros hard sobre uma lista de candidatos retornada
pela busca híbrida. Todos os parâmetros são opcionais.

Input:
    candidates      : List[dict]    — filmes candidatos
    genres          : List[str]     — gêneros requeridos (OR)
    year_min        : int           — ano mínimo de lançamento
    year_max        : int           — ano máximo de lançamento
    min_rating      : float         — nota mínima (vote_average)
    language        : str           — idioma original (ex: 'en')

Output:
    List[dict] filtrado
"""

import json
from typing import List, Optional


def filter_movies(
    candidates: List[dict],
    genres: Optional[List[str]] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    min_rating: Optional[float] = None,
    language: Optional[str] = None,
) -> str:
    result = []
    for movie in candidates:
        if genres:
            movie_genres = [g.lower() for g in movie.get("genres", [])]
            if not any(g.lower() in movie_genres for g in genres):
                continue
        if year_min and movie.get("year", 0) < year_min:
            continue
        if year_max and movie.get("year", 9999) > year_max:
            continue
        if min_rating and movie.get("vote_average", 0) < min_rating:
            continue
        if language and movie.get("original_language", "") != language:
            continue
        result.append(movie)

    return json.dumps(result, ensure_ascii=False)
