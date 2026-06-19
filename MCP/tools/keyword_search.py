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
