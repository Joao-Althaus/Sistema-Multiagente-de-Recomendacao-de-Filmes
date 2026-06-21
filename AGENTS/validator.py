"""
Agente Validador

Responsabilidades:
- Receber os candidatos (top-20) do Retriever
- Usar o LLM para reordenar e selecionar os 5 melhores filmes
- Gerar justificativa personalizada para cada recomendação,
  explicando por que o filme foi escolhido com base no perfil
  (ex: mesmo diretor, gênero favorito, ator preferido)
"""

from typing import List, Tuple

from core.llm_client import LLMClient
from core.user_profile import UserProfile


class ValidatorAgent:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def validate(
        self, candidates: List[dict], profile: UserProfile
    ) -> Tuple[List[dict], List[str]]:
        """
        Reordena os candidatos via LLM e gera justificativas.
        Retorna (top5_movies, justifications).
        """
        top5_indices = self.llm.rerank(candidates, profile)
        top5 = [candidates[i] for i in top5_indices]

        justifications = []
        for movie in top5:
            justification = self.llm.generate_justification(movie, profile)
            justifications.append(justification)

        return top5, justifications
