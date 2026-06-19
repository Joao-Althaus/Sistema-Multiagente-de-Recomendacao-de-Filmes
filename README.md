# Sistema Multiagente de Recomendação de Filmes

Sistema de recomendação personalizada de filmes baseado em arquitetura multiagente com RAG (Retrieval-Augmented Generation), busca híbrida e LLM local via Ollama.

---

## Visão Geral

O sistema coleta o perfil do usuário (filmes assistidos, gêneros, atores e diretores favoritos), constrói uma query semântica e utiliza três agentes cooperando para retornar as **5 melhores recomendações** com justificativas personalizadas.

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                     CLI (Terminal)                      │
│         Coleta perfil → exibe recomendações             │
└───────────────────────┬─────────────────────────────────┘
                        │
              ┌─────────▼───────────┐
              │  Agente Orquestrador│
              │  Coordena o fluxo   │
              │  Sintetiza resposta │
              └──┬──────────────┬───┘
                 │              │
     ┌───────────▼──┐    ┌──────▼───────────┐
     │  Agente       │   │  Agente          │
     │  Recuperador  │   │  Validador       │
     │  Busca híbrida│   │  Reordena top-20 │
     │  top-20 filmes│   │  Gera top-5 +    │
     └───────────────┘   │  justificativas  │
                         └──────────────────┘
                 │
     ┌───────────▼───────────┐
     │       RAG Engine      │
     │  embeddings.npy       │
     │  metadata.pkl         │
     │  chunks.pkl           │
     └───────────────────────┘
```

### Agentes

| Agente | Arquivo | Responsabilidade |
|---|---|---|
| Orquestrador | `agents/orchestrator.py` | Recebe input, coordena fluxo, sintetiza resposta final |
| Recuperador | `agents/retriever.py` | Busca híbrida (semântica + keyword), aplica filtros |
| Validador | `agents/validator.py` | Reordena candidatos, seleciona top-5, gera justificativas |

---

## Processo de Recomendação

**1. Coleta de Perfil**
O Orquestrador pergunta ao usuário:
- Últimos 3–5 filmes assistidos
- Gêneros favoritos
- Atores preferidos
- Diretores preferidos
- Elementos a evitar (opcional)

**2. Construção da Query Semântica**
O Orquestrador usa o LLM para montar uma query em linguagem natural combinando o perfil:
```
Films similar to [filmes vistos]. Genres: [favoritos].
Featuring actors like [atores]. Directed by [diretores].
```

**3. Busca Híbrida** (Agente Recuperador)

| Sinal | Mecanismo | Peso |
|---|---|---|
| Semântico | Similaridade coseno sobre embeddings | 60% |
| Keyword | Match em `cast`, `director`, `genres`, `title` | 40% |

`score_final = 0.6 × cosine_score + 0.4 × keyword_score`

Retorna os **20 candidatos** com maior score.

**4. Validação e Justificativa** (Agente Validador)
- Reordena os 20 candidatos considerando o perfil completo
- Seleciona os **5 melhores**
- Gera uma justificativa personalizada por filme explicando *por que* foi recomendado

---

## Stack Tecnológica

| Componente | Tecnologia |
|---|---|
| LLM | LLAMA 3.2 via Ollama (local) |
| Embeddings | `sentence-transformers` — `all-MiniLM-L6-v2` (384 dims) |
| Dataset | TMDB 5000 Movies — `AiresPucrs/tmdb-5000-movies` (HuggingFace) |
| Busca | `numpy` + `scikit-learn` (coseno) — sem banco vetorial |
| Agentes | Python + MCP (Model Context Protocol) |
| Interface | Terminal interativo com histórico de sessão |

---

## Dataset

**[AiresPucrs/tmdb-5000-movies](https://huggingface.co/datasets/AiresPucrs/tmdb-5000-movies)** — ~4.800 filmes

Campos utilizados: `title`, `overview`, `genres`, `cast` (top-5 atores), `crew` (diretores), `release_date`, `vote_average`, `vote_count`, `original_language`

Cada filme é representado por um chunk de texto no formato:
```
Title: {title}
Year: {year}
Genres: {genres}
Director: {director}
Rating: {vote_average}/10
Cast: {actor1}, {actor2}, ...
Overview: {overview}
```

---

## Estrutura do Projeto

```
├── RAG/
│   ├── embeddings_pipeline.ipynb   # Pipeline ETL + geração de embeddings
│   └── data/
│       ├── embeddings.npy          # Embeddings (N × 384, float32)
│       ├── metadata.pkl            # Metadados por filme (List[dict])
│       └── chunks.pkl              # Textos dos chunks (List[str])
│
├── agents/
│   ├── orchestrator.py             # Coordena fluxo e sintetiza resposta
│   ├── retriever.py                # Busca híbrida + filtros
│   └── validator.py                # Reordena e justifica top-5
│
├── MCP/
│   ├── server.py                   # MCP server
│   └── tools/
│       ├── semantic_search.py      # Busca por similaridade semântica
│       ├── keyword_search.py       # Busca textual (título, ator, diretor)
│       └── filter.py               # Filtros por gênero, ano, nota
│
├── core/
│   ├── rag_engine.py               # Carrega artefatos, busca híbrida
│   ├── llm_client.py               # Interface com Ollama
│   └── user_profile.py             # Estrutura do perfil do usuário
│
├── cli/
│   └── terminal.py                 # Interface interativa com histórico
│
├── main.py                         # Entry point
└── requirements.txt
```

---

## Instalação e Uso

### Pré-requisitos
- Python 3.10+
- [Ollama](https://ollama.com) instalado e rodando localmente com LLAMA 3.2: `ollama pull llama3.2`

### Setup

```bash
# Instalar dependências
pip install -r requirements.txt

# Gerar os embeddings (executar o notebook RAG/embeddings_pipeline.ipynb)
# Os arquivos serão salvos em RAG/data/

# Iniciar o sistema
python main.py
```

---

## Exemplo de Sessão

```
🎬 Sistema de Recomendação de Filmes
=====================================

Quais foram os últimos filmes que você assistiu?
> Interstellar, Inception, The Prestige

Quais são seus gêneros favoritos?
> Ficção científica, Thriller

Atores que você gosta?
> Leonardo DiCaprio, Matthew McConaughey

Diretores favoritos?
> Christopher Nolan

Buscando recomendações...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  TOP 5 RECOMENDAÇÕES PARA VOCÊ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. The Martian (2015) ★8.0
   🎬 Dir: Ridley Scott | Ficção Científica, Aventura
   👥 Matt Damon, Jessica Chastain
   💬 Recomendado porque você curte ficção científica com narrativa
      intensa, similar a Interstellar. Matt Damon em papel de destaque.

[...]
```
