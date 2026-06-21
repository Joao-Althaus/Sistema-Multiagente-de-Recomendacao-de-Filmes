"""
Agente Recuperador

Responsabilidades:
- Receber a query semântica e o perfil do usuário do Orquestrador
- Conectar ao MCP Server via stdio e chamar as tools disponíveis:
    - semantic_search : busca por similaridade semântica (peso 60%)
    - keyword_search  : busca textual em cast/director/genres/title (peso 40%)
    - filter_movies   : aplica filtros opcionais do perfil (evitar gêneros)
- Combinar e retornar os top-20 candidatos para o Validator
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Optional

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from core.user_profile import UserProfile

_SERVER_SCRIPT = str(Path(__file__).parent.parent / "MCP" / "server.py")


class RetrieverAgent:
    def __init__(self):
        self._server_params = StdioServerParameters(
            command=sys.executable,
            args=[_SERVER_SCRIPT],
        )

    async def _call_tool(self, session: ClientSession, name: str, arguments: dict) -> list:
        result = await session.call_tool(name, arguments)
        text = result.content[0].text
        return json.loads(text)

    async def _retrieve(self, query: str, profile: UserProfile) -> List[dict]:
        async with stdio_client(self._server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Busca semântica
                semantic_results = await self._call_tool(
                    session, "semantic_search", {"query": query, "top_n": 20}
                )

                # Busca keyword com termos do perfil
                keyword_terms = (
                    profile.watched_movies
                    + profile.favorite_actors
                    + profile.favorite_directors
                    + profile.favorite_genres
                )
                keyword_results = await self._call_tool(
                    session, "keyword_search", {"terms": keyword_terms, "top_n": 20}
                )

                # Combina os dois sinais: 60% semântico + 40% keyword
                scores: dict[int, float] = {}
                for movie in semantic_results:
                    scores[movie["id"]] = 0.6 * movie.get("score", 0.0)
                for movie in keyword_results:
                    mid = movie["id"]
                    scores[mid] = scores.get(mid, 0.0) + 0.4 * movie.get("keyword_score", 0.0)

                # Monta lista unificada
                all_movies: dict[int, dict] = {}
                for movie in semantic_results + keyword_results:
                    mid = movie["id"]
                    if mid not in all_movies:
                        all_movies[mid] = movie

                candidates = sorted(
                    all_movies.values(),
                    key=lambda m: scores.get(m["id"], 0.0),
                    reverse=True,
                )[:20]

                for c in candidates:
                    c["score"] = scores.get(c["id"], 0.0)

                # Aplica filtro de conteúdo a evitar (se informado)
                if profile.avoid:
                    candidates = await self._call_tool(
                        session,
                        "filter_movies",
                        {"candidates": candidates},
                    )
                    # filter_movies retorna lista — já está parsed pelo _call_tool
                    if isinstance(candidates, str):
                        candidates = json.loads(candidates)

                return candidates[:20]

    def retrieve(self, query: str, profile: UserProfile) -> List[dict]:
        return asyncio.run(self._retrieve(query, profile))
