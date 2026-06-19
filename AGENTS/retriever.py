"""
Agente Recuperador

Responsabilidades:
- Receber a query semântica e o perfil do usuário do Orquestrador
- Executar busca híbrida via RAGEngine:
    - Busca semântica (coseno sobre embeddings) — peso 60%
    - Busca keyword (match em cast, director, genres, title) — peso 40%
- Aplicar filtros opcionais (gênero, ano, idioma) via MCP tools
- Retornar candidatos (top-20) para o Validator
"""
