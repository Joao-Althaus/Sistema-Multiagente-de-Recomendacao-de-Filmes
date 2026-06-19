"""
RAG Engine

Núcleo do sistema de recuperação. Carrega os artefatos gerados pelo
pipeline ETL (embeddings.npy, metadata.pkl, chunks.pkl) e implementa:

- Busca semântica: similaridade coseno entre query embedding e base
- Busca keyword:   match parcial em campos de metadata (cast, director, title)
- Busca híbrida:   combinação ponderada dos dois sinais
    score_final = 0.6 * cosine_score + 0.4 * keyword_score
"""
