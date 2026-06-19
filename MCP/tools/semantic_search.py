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
