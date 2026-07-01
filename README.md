# Sistema Multiagentes de Recomendação de Filmes

Sistema de recomendação personalizada de filmes baseado em arquitetura multiagente com RAG (Retrieval-Augmented Generation), busca híbrida e LLM local via Ollama.

---

## Integrantes

* **João Vitor Althaus Godoi - 204929**

* **Diogo Godoy Brignoni - 201027**

* **Fernando Powzum da Silva - 204124**

* **Guilherme Witte Rambo - 203162**

---

## Descrição do Problema

Recomendar filmes de forma personalizada é um problema que vai além de uma simples busca por gênero ou popularidade. O usuário tem preferências multidimensionais — diretores favoritos, atores preferidos, filmes que já assistiu, temas que quer evitar — e uma solução de agente único teria dificuldade em combinar recuperação eficiente de candidatos com avaliação qualitativa e geração de justificativas personalizadas ao mesmo tempo.

A arquitetura multiagente permite separar essas responsabilidades em agentes especializados que cooperam para entregar as 5 melhores recomendações com justificativas em linguagem natural.

---

## Objetivo

Desenvolver um sistema funcional via terminal onde o usuário informa seu perfil cinematográfico e recebe 5 recomendações personalizadas com justificativas geradas por LLM local, utilizando busca híbrida sobre uma base vetorial de filmes.

---

## Arquitetura Multiagente

```
CLI (terminal interativo)
    │
    │  coleta perfil do usuário
    ▼
┌─────────────────────┐
│  Agente Orquestrador│
│                     │  1. Usa LLM para gerar query semântica
│                     │  2. Coordena Retriever e Validator
│                     │  3. Retorna top-5 ao CLI
└──────┬──────────────┘
       │
       ├──────────────────────────────────┐
       ▼                                  ▼
┌──────────────────┐          ┌────────────────────────┐
│ Agente Retriever │          │  Agente Validator      │
│                  │          │                        │
│ Chama tools via  │  top-20  │ Reordena candidatos    │
│ MCP Server:      │ ────────►│ via LLM                │
│ - semantic_search│          │ Seleciona top-5        │
│ - keyword_search │          │ Gera justificativas    │
│ - filter_movies  │          └────────────────────────┘
└──────────────────┘
       │
       ▼
┌──────────────────┐
│   MCP Server     │  (stdio)
│                  │
│ semantic_search  │──► RAGEngine (embeddings coseno)
│ keyword_search   │──► RAGEngine (match em metadata)
│ filter_movies    │──► filtragem por gênero/ano/nota
└──────────────────┘
       │
       ▼
┌──────────────────┐
│   RAG Engine     │
│                  │
│ embeddings.npy   │  (4391 × 384, float32)
│ metadata.pkl     │  (List[dict] por filme)
│ chunks.pkl       │  (texto estruturado por filme)
└──────────────────┘
```

### Por que multiagente?

| Responsabilidade | Agente único | Multiagente |
|---|---|---|
| Gerar query + buscar + avaliar | Tudo junto, difícil de depurar | Separado por agente |
| Busca híbrida via MCP | Acoplado ao código | Desacoplado via protocolo |
| Justificativas | Geradas sem contexto | Validator usa perfil + candidatos |

---

## Papel de Cada Agente

| Agente | Arquivo | Responsabilidade |
|---|---|---|
| Orquestrador | `AGENTS/orchestrator.py` | Recebe perfil, gera query via LLM, coordena fluxo, sintetiza resposta |
| Recuperador | `AGENTS/retriever.py` | Conecta ao MCP Server, executa busca híbrida, retorna top-20 candidatos |
| Validador | `AGENTS/validator.py` | Reordena candidatos via LLM, seleciona top-5, gera justificativas personalizadas |

---

## Tools Disponíveis

As tools são expostas via MCP Server e acionadas pelo Agente Recuperador:

| Tool | Arquivo | Descrição |
|---|---|---|
| `semantic_search` | `MCP/tools/semantic_search.py` | Busca por similaridade coseno nos embeddings. Recebe query em texto, retorna top-N filmes mais similares |
| `keyword_search` | `MCP/tools/keyword_search.py` | Match parcial de termos em título, elenco, diretor e gêneros. Sinal complementar da busca híbrida |
| `filter_movies` | `MCP/tools/filter.py` | Filtragem hard por gênero, ano mínimo/máximo, nota mínima e idioma |

---

## Como o MCP foi Utilizado

O **Model Context Protocol (MCP)** é utilizado como camada de comunicação entre o Agente Recuperador e as ferramentas de busca. O MCP Server (`MCP/server.py`) roda como subprocesso via transporte **stdio** e expõe as três tools acima como endpoints padronizados.

O Agente Recuperador se conecta ao servidor usando `mcp.ClientSession` e `stdio_client`, e chama as tools com `session.call_tool()`. Isso desacopla a lógica de busca dos agentes — qualquer agente pode chamar qualquer tool sem conhecer a implementação interna.

```
RetrieverAgent
    └── stdio_client → MCP Server (subprocesso Python)
            ├── call_tool("semantic_search", {"query": ...})
            ├── call_tool("keyword_search", {"terms": [...]})
            └── call_tool("filter_movies", {"candidates": [...]})
```

---

## Estratégia de RAG

O sistema implementa **busca híbrida** combinando dois sinais:

| Sinal | Mecanismo | Peso |
|---|---|---|
| Semântico | Similaridade coseno entre embedding da query e embeddings dos filmes | 60% |
| Keyword | Match parcial de termos do perfil em `title`, `cast`, `director`, `genres` | 40% |

```
score_final = 0.6 × cosine_score + 0.4 × keyword_score
```

**Fluxo RAG:**
1. O Orquestrador usa o LLM para converter o perfil do usuário em uma query semântica em inglês
2. O Retriever gera o embedding da query via `all-MiniLM-L6-v2`
3. Calcula similaridade coseno contra os 4391 embeddings pré-computados
4. Combina com o score keyword dos termos do perfil (atores, diretores, gêneros)
5. Retorna top-20 candidatos ao Validator
6. O Validator usa o LLM para reordenar e selecionar os top-5

---

## Base de Conhecimento

**Dataset:** [AiresPucrs/tmdb-5000-movies](https://huggingface.co/datasets/AiresPucrs/tmdb-5000-movies) — TMDB 5000 Movies

- ~4.800 filmes após limpeza (filtro: `vote_count >= 10`, sem título/overview vazio)
- Campos utilizados: `title`, `overview`, `genres`, `cast` (top-5 atores), `crew` (diretores), `release_date`, `vote_average`, `vote_count`, `original_language`

Cada filme é representado por um chunk de texto estruturado:

```
Title: {title}
Year: {year}
Genres: {genres}
Director: {director}
Rating: {vote_average}/10
Cast: {actor1}, {actor2}, ...
Overview: {overview}
```

O pipeline ETL completo está em `RAG/embeddings_pipeline.ipynb`.

---

## Embeddings e Armazenamento Vetorial

| Componente | Tecnologia |
|---|---|
| Modelo de embeddings | `sentence-transformers` — `all-MiniLM-L6-v2` |
| Dimensão | 384 dimensões, float32 |
| Armazenamento | `numpy` (`.npy`) + `pickle` (`.pkl`) — sem banco vetorial externo |
| Busca | `sklearn.metrics.pairwise.cosine_similarity` |
| Arquivos gerados | `RAG/data/embeddings.npy` (6.4 MB), `metadata.pkl` (2.1 MB), `chunks.pkl` (2.1 MB) |

A escolha de numpy puro (sem ChromaDB, Pinecone, etc.) foi intencional: o dataset tem ~4.400 filmes e o custo de busca é baixo (~ms), tornando um banco vetorial desnecessário.

---

## Modelo Local

| Item | Valor |
|---|---|
| Modelo | `llama3.2:3b` |
| Executor | [Ollama](https://ollama.com) |
| Cliente Python | `ollama` (PyPI) |
| Contexto padrão | 4096 tokens |

**Justificativa:** O `llama3.2:3b` foi escolhido por equilibrar qualidade e desempenho em hardware sem suporte ROCm completo no Windows. Com ~2 GB de RAM, roda confortavelmente em CPU mantendo latência aceitável para geração de queries e justificativas.

O modelo é usado em três momentos:
1. **Orquestrador** — gera query semântica em inglês a partir do perfil
2. **Validator** — reordena os 20 candidatos e seleciona top-5
3. **Validator** — gera justificativa personalizada para cada um dos 5 filmes

---

## Dependências

```
datasets
sentence-transformers
pandas
numpy
tqdm
scikit-learn
ollama
mcp
colorama
```

---

## Instalação e Execução

### Pré-requisitos

- Python 3.10+
- [Ollama](https://ollama.com) instalado




### Setup

```bash
# 1. Clonar o repositório
git clone https://github.com/<usuario>/Sistema-Multiagente-de-Recomendacao-de-Filmes
cd Sistema-Multiagente-de-Recomendacao-de-Filmes

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Gerar embeddings (executar o notebook uma vez)
# Abrir e executar todas as células de RAG/embeddings_pipeline.ipynb
# Os arquivos serão salvos em RAG/data/

# 4. Garantir que o Ollama está rodando com llama3.2:3b
ollama serve   # em um terminal separado
# Em caso de erro verifique o nome do modelo e o local de instalação
# Para debugging utilize:
ollama list
# Faça questão que a versão instalada tem o mesmo exato nome llama3.2:3b

# 5. Iniciar o sistema
python main.py
```

### Modo de teste RAG (sem LLM)

Para testar apenas a busca nos embeddings:

```bash
python main.py --test-rag
```

---

## Exemplos de Uso

### Sessão completa

```
════════════════════════════════════════════════════════
  MENU PRINCIPAL
════════════════════════════════════════════════════════

  1  Perguntas guiadas    — formulario rapido de perfil
  2  Chat dinamico        — 3 perguntas antes da busca
  3  Ver historico        — recomendacoes desta sessao
  0  Sair

❯ Opcao: 1

════════════════════════════════════════════════════════
  📋  Perguntas Guiadas
════════════════════════════════════════════════════════

  › Ultimos filmes que assistiu: Interstellar, Inception
  › Generos favoritos: Ficcao Cientifica, Thriller
  › Atores que voce gosta: Matthew McConaughey
  › Diretores favoritos: Christopher Nolan
  › Algo que prefere evitar:

  ⟳ Analisando perfil e buscando recomendacoes...
  [Orquestrador] Query gerada: Thought-provoking sci-fi thrillers directed by Christopher Nolan.
  [Retriever] 20 candidatos recuperados via MCP.
  [Validator] Top-5 selecionados e justificativas geradas.

════════════════════════════════════════════════════════
  🏆  TOP 5 RECOMENDACOES PARA VOCE
════════════════════════════════════════════════════════

  #1  Interstellar  2014
      ★★★★☆  8.1/10
      Generos  ·  Adventure, Drama, Science Fiction
      Diretor  ·  Christopher Nolan
      Elenco   ·  Matthew McConaughey, Jessica Chastain, Anne Hathaway
      💬  Dirigido por Christopher Nolan, combina ficcao cientifica e drama.

  ...

════════════════════════════════════════════════════════
  O QUE DESEJA FAZER?
════════════════════════════════════════════════════════

  1  Nova recomendacao    — buscar com novo perfil
  2  Avaliar resultados   — refinar com base no que achou
  3  Voltar ao menu       — menu principal

❯ Opcao: 2

  📝  Avaliacao
  Diga o que achou — pode falar livremente.
  Ex: "ja vi o #1", "nao gostei do #3", "quero algo mais pesado"

  Voce › Ja vi o Interstellar e o Inception, quero algo mais recente

  Processando feedback...
  Removendo: Interstellar, Inception
  ⟳ Buscando novas recomendacoes...
```

### Modo teste RAG (sem LLM)

```
  Query › christopher nolan space thriller

  #1  Interstellar  2014  score=0.6000
      Adventure, Drama, Science Fiction  ·  Christopher Nolan
      Interstellar chronicles the adventures of a group of explorers...
```

### Menu do terminal

| Opção | Ação |
|---|---|
| `1` | Perguntas guiadas — formulário rápido de perfil |
| `2` | Chat dinâmico — 3 perguntas geradas antes da busca |
| `3` | Ver histórico da sessão |
| `0` | Sair |

**Menu pós-recomendação:**

| Opção | Ação |
|---|---|
| `1` | Nova recomendação com novo perfil |
| `2` | Avaliar — feedback livre, refina e rebusca sem os filmes rejeitados |
| `3` | Voltar ao menu principal |

---

## Estrutura do Projeto

```
├── RAG/
│   ├── embeddings_pipeline.ipynb   # Pipeline ETL + geração de embeddings
│   └── data/
│       ├── embeddings.npy          # Embeddings (4391 × 384, float32)
│       ├── metadata.pkl            # Metadados por filme
│       └── chunks.pkl              # Textos dos chunks
│
├── AGENTS/
│   ├── orchestrator.py             # Coordena fluxo e sintetiza resposta
│   ├── retriever.py                # Busca híbrida via MCP
│   └── validator.py                # Reordena e justifica top-5
│
├── MCP/
│   ├── server.py                   # MCP Server (stdio)
│   └── tools/
│       ├── semantic_search.py
│       ├── keyword_search.py
│       └── filter.py
│
├── core/
│   ├── rag_engine.py               # Carrega artefatos, busca híbrida
│   ├── llm_client.py               # Interface com Ollama
│   └── user_profile.py             # Dataclass UserProfile
│
├── cli/
│   └── terminal.py                 # Interface interativa
│
├── main.py                         # Entry point
└── requirements.txt
```
