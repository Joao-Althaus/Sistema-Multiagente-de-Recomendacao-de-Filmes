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
