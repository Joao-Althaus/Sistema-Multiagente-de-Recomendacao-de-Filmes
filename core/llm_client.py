"""
LLM Client

Interface com o modelo de linguagem local via Ollama (llama3.2:3b).
Abstrai as chamadas de geração de texto usadas pelos agentes:

- chat(messages)          : chamada genérica de chat completion
- generate_query(profile) : constrói query semântica a partir do perfil
- generate_justification(movie, profile) : gera justificativa personalizada
"""

from typing import List

import ollama

from core.user_profile import UserProfile

_MODEL = "llama3.2:3b"


class LLMClient:
    def chat(self, messages: List[dict]) -> str:
        response = ollama.chat(model=_MODEL, messages=messages)
        return response.message.content.strip()

    def generate_query(self, profile: UserProfile) -> str:
        prompt = (
            "You are a movie recommendation assistant. "
            "Based on the user's profile below, write a single descriptive sentence "
            "in English that captures what kind of movie they want. "
            "Output only the sentence, no explanation.\n\n"
            f"Profile:\n{profile.to_text()}"
        )
        return self.chat([{"role": "user", "content": prompt}])

    def generate_justification(self, movie: dict, profile: UserProfile) -> str:
        movie_info = (
            f"Title: {movie['title']} ({movie.get('year', '')})\n"
            f"Genres: {', '.join(movie.get('genres', []))}\n"
            f"Director: {', '.join(movie.get('director', []))}\n"
            f"Cast: {', '.join(movie.get('cast', [])[:3])}\n"
            f"Overview: {movie.get('overview', '')[:300]}"
        )
        prompt = (
            "You are a movie recommendation assistant. "
            "Write one short sentence in Portuguese explaining why this movie fits the user's profile. "
            "Be specific — mention a genre, director, or actor from the profile if relevant. "
            "Output only the sentence.\n\n"
            f"User profile:\n{profile.to_text()}\n\n"
            f"Movie:\n{movie_info}"
        )
        return self.chat([{"role": "user", "content": prompt}])

    def ask_dynamic_question(self, question_num: int, history: List[dict]) -> str:
        """Gera a próxima pergunta dinâmica com base no histórico da conversa."""
        system = (
            "You are a friendly movie recommendation assistant conducting a short interview. "
            "Ask ONE short question in Portuguese to understand the user's movie taste. "
            "You have already asked some questions (see history). "
            f"This is question {question_num} of 3. "
            "On question 1: ask about favorite movies or genres. "
            "On question 2: ask about favorite actors or directors. "
            "On question 3: ask about something they want to avoid or a mood/theme they enjoy. "
            "Be conversational and brief. Output only the question."
        )
        messages = [{"role": "system", "content": system}] + history
        return self.chat(messages)

    def extract_profile_from_chat(self, history: List[dict]) -> UserProfile:
        """Extrai um UserProfile estruturado a partir do histórico de conversa."""
        prompt = (
            "Based on this conversation, extract the user's movie preferences. "
            "Return ONLY a JSON object with these keys (use empty lists if not mentioned):\n"
            '{"watched_movies": [], "favorite_genres": [], "favorite_actors": [], '
            '"favorite_directors": [], "avoid": []}\n\n'
            "Conversation:\n"
        )
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            prompt += f"{role}: {msg['content']}\n"

        response = self.chat([{"role": "user", "content": prompt}])

        import json, re
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                return UserProfile(
                    watched_movies=data.get("watched_movies", []),
                    favorite_genres=data.get("favorite_genres", []),
                    favorite_actors=data.get("favorite_actors", []),
                    favorite_directors=data.get("favorite_directors", []),
                    avoid=data.get("avoid", []),
                )
            except Exception:
                pass
        return UserProfile()

    def refine_profile_from_feedback(
        self,
        feedback: str,
        profile: UserProfile,
        shown_movies: List[dict],
    ) -> tuple:
        """
        Processa o feedback do usuário sobre as recomendações.
        Retorna (novo_perfil, titulos_a_excluir).
        """
        shown_list = "\n".join(
            f"- #{i+1} {m['title']} ({m.get('year','')})"
            for i, m in enumerate(shown_movies)
        )
        prompt = (
            "The user received movie recommendations and gave feedback. "
            "Based on the feedback, return a JSON with two keys:\n"
            '1. "exclude_titles": list of movie titles the user already saw or disliked\n'
            '2. "profile_updates": object with keys watched_movies, favorite_genres, '
            'favorite_actors, favorite_directors, avoid — with NEW info from feedback only '
            '(empty lists if nothing new)\n\n'
            f"Current profile:\n{profile.to_text()}\n\n"
            f"Movies shown:\n{shown_list}\n\n"
            f"User feedback: {feedback}\n\n"
            'Return only the JSON object.'
        )
        response = self.chat([{"role": "user", "content": prompt}])

        import json, re
        exclude = []
        updates = {}
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                exclude = data.get("exclude_titles", [])
                updates = data.get("profile_updates", {})
            except Exception:
                pass

        # mescla o perfil atual com as atualizações
        new_profile = UserProfile(
            watched_movies=profile.watched_movies + updates.get("watched_movies", []),
            favorite_genres=profile.favorite_genres + updates.get("favorite_genres", []),
            favorite_actors=profile.favorite_actors + updates.get("favorite_actors", []),
            favorite_directors=profile.favorite_directors + updates.get("favorite_directors", []),
            avoid=profile.avoid + updates.get("avoid", []),
        )
        return new_profile, exclude

    def rerank(self, candidates: List[dict], profile: UserProfile) -> List[int]:
        """
        Pede ao LLM para reordenar os candidatos e retornar os índices top-5.
        Retorna lista de índices (0-based) na ordem de preferência.
        """
        lines = []
        for i, m in enumerate(candidates):
            genres = ", ".join(m.get("genres", []))
            director = ", ".join(m.get("director", []))
            lines.append(f"{i}. {m['title']} ({m.get('year','')}) | {genres} | Dir: {director}")

        candidates_text = "\n".join(lines)
        prompt = (
            "You are a movie recommendation assistant. "
            "Given the user profile and a list of candidate movies, "
            "select the 5 best matches and return ONLY their numbers separated by commas. "
            "Example output: 3,7,1,12,0\n\n"
            f"User profile:\n{profile.to_text()}\n\n"
            f"Candidates:\n{candidates_text}\n\n"
            "Return only 5 numbers separated by commas:"
        )
        response = self.chat([{"role": "user", "content": prompt}])

        indices = []
        for token in response.replace(" ", "").split(","):
            try:
                idx = int(token.strip())
                if 0 <= idx < len(candidates) and idx not in indices:
                    indices.append(idx)
            except ValueError:
                continue

        # fallback: primeiros 5 se o LLM não retornou indices válidos
        if len(indices) < 5:
            for i in range(len(candidates)):
                if i not in indices:
                    indices.append(i)
                if len(indices) == 5:
                    break

        return indices[:5]
