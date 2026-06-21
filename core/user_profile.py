"""
UserProfile

Estrutura de dados que representa o perfil do usuário coletado
pelo Orquestrador no início de cada sessão.

Campos:
    watched_movies  : List[str]  — títulos dos últimos filmes assistidos
    favorite_genres : List[str]  — gêneros favoritos
    favorite_actors : List[str]  — atores preferidos
    favorite_directors: List[str] — diretores preferidos
    avoid           : List[str]  — elementos a evitar (opcional)
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class UserProfile:
    watched_movies: List[str] = field(default_factory=list)
    favorite_genres: List[str] = field(default_factory=list)
    favorite_actors: List[str] = field(default_factory=list)
    favorite_directors: List[str] = field(default_factory=list)
    avoid: List[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not any([
            self.watched_movies,
            self.favorite_genres,
            self.favorite_actors,
            self.favorite_directors,
        ])

    def to_text(self) -> str:
        parts = []
        if self.watched_movies:
            parts.append(f"Watched: {', '.join(self.watched_movies)}")
        if self.favorite_genres:
            parts.append(f"Genres: {', '.join(self.favorite_genres)}")
        if self.favorite_actors:
            parts.append(f"Actors: {', '.join(self.favorite_actors)}")
        if self.favorite_directors:
            parts.append(f"Directors: {', '.join(self.favorite_directors)}")
        if self.avoid:
            parts.append(f"Avoid: {', '.join(self.avoid)}")
        return '. '.join(parts)
