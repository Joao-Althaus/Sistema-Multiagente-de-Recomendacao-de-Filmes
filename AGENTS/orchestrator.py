"""
Agente Orquestrador

Responsabilidades:
- Receber o perfil do usuário coletado pelo CLI
- Usar o LLM para construir uma query semântica a partir do perfil
- Coordenar o fluxo: Retriever → Validator
- Sintetizar e retornar as 5 recomendações com justificativas
"""

from typing import List, Tuple

from core.llm_client import LLMClient
from core.user_profile import UserProfile
from AGENTS.retriever import RetrieverAgent
from AGENTS.validator import ValidatorAgent


class OrchestratorAgent:
    def __init__(self):
        self.llm = LLMClient()
        self.retriever = RetrieverAgent()
        self.validator = ValidatorAgent(self.llm)

    def recommend(
        self,
        profile: UserProfile,
        exclude_titles: List[str] = None,
    ) -> Tuple[List[dict], List[str]]:
        """
        Fluxo completo: perfil → query → candidatos → top-5 com justificativas.
        exclude_titles: títulos a remover dos candidatos (filmes já vistos/rejeitados).
        """
        query = self.llm.generate_query(profile)
        print(f"  [Orquestrador] Query gerada: {query}")

        candidates = self.retriever.retrieve(query, profile)
        print(f"  [Retriever] {len(candidates)} candidatos recuperados via MCP.")

        # remove filmes excluídos pelo feedback
        if exclude_titles:
            excluded_lower = [t.lower() for t in exclude_titles]
            candidates = [
                c for c in candidates
                if c.get("title", "").lower() not in excluded_lower
            ]

        top5, justifications = self.validator.validate(candidates, profile)
        print(f"  [Validator] Top-5 selecionados e justificativas geradas.")

        return top5, justifications
