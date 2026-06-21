"""
MCP Server

Expõe as tools do sistema como endpoints MCP para os agentes.
Roda via stdio — os agentes se conectam como subprocesso.

Tools registradas:
- semantic_search   : busca por similaridade semântica nos embeddings
- keyword_search    : busca textual por título, ator ou diretor
- filter_movies     : filtragem por gênero, ano e nota mínima
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
import asyncio

from core.rag_engine import RAGEngine
from MCP.tools.semantic_search import semantic_search
from MCP.tools.keyword_search import keyword_search
from MCP.tools.filter import filter_movies

app = Server("movie-recommender")
_rag = RAGEngine()


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="semantic_search",
            description="Busca filmes por similaridade semântica usando embeddings. Retorna os top-N mais similares à query.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Texto descritivo do tipo de filme desejado"},
                    "top_n": {"type": "integer", "description": "Número de resultados (default 20)", "default": 20},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="keyword_search",
            description="Busca filmes por correspondência de termos em título, elenco, diretor e gêneros.",
            inputSchema={
                "type": "object",
                "properties": {
                    "terms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de termos para buscar (atores, diretores, gêneros, títulos)",
                    },
                    "top_n": {"type": "integer", "description": "Número de resultados (default 20)", "default": 20},
                },
                "required": ["terms"],
            },
        ),
        Tool(
            name="filter_movies",
            description="Filtra uma lista de filmes candidatos por gênero, ano, nota mínima ou idioma.",
            inputSchema={
                "type": "object",
                "properties": {
                    "candidates": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Lista de filmes candidatos (saída de semantic_search ou keyword_search)",
                    },
                    "genres": {"type": "array", "items": {"type": "string"}, "description": "Gêneros requeridos (OR)"},
                    "year_min": {"type": "integer", "description": "Ano mínimo de lançamento"},
                    "year_max": {"type": "integer", "description": "Ano máximo de lançamento"},
                    "min_rating": {"type": "number", "description": "Nota mínima (0-10)"},
                    "language": {"type": "string", "description": "Idioma original (ex: 'en')"},
                },
                "required": ["candidates"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "semantic_search":
        result = semantic_search(_rag, arguments["query"], arguments.get("top_n", 20))
    elif name == "keyword_search":
        result = keyword_search(_rag, arguments["terms"], arguments.get("top_n", 20))
    elif name == "filter_movies":
        candidates = arguments["candidates"]
        result = filter_movies(
            candidates,
            genres=arguments.get("genres"),
            year_min=arguments.get("year_min"),
            year_max=arguments.get("year_max"),
            min_rating=arguments.get("min_rating"),
            language=arguments.get("language"),
        )
    else:
        result = json.dumps({"error": f"Tool '{name}' não encontrada"})

    return [TextContent(type="text", text=result)]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
