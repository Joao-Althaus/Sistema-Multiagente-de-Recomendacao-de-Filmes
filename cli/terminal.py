"""
Terminal Interativo

Interface de linha de comando do sistema. Responsabilidades:
- Exibir banner e menu principal
- Modo 1: coleta de perfil por perguntas estruturadas
- Modo 2: chat com 3 perguntas antes da query
- Modo 3: histórico de recomendações da sessão
- Menu pós-recomendação: nova busca, avaliar, voltar
"""

from typing import List, Optional

import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

from core.user_profile import UserProfile

# ── helpers de cor ────────────────────────────────────────────────────────────

def bold(t):        return Style.BRIGHT + str(t) + Style.RESET_ALL
def dim(t):         return Style.DIM    + str(t) + Style.RESET_ALL
def cyan(t):        return Fore.CYAN    + str(t) + Style.RESET_ALL
def yellow(t):      return Fore.YELLOW  + str(t) + Style.RESET_ALL
def green(t):       return Fore.GREEN   + str(t) + Style.RESET_ALL
def red(t):         return Fore.RED     + str(t) + Style.RESET_ALL
def magenta(t):     return Fore.MAGENTA + str(t) + Style.RESET_ALL
def white(t):       return Fore.WHITE   + str(t) + Style.RESET_ALL
def gray(t):        return Fore.WHITE + Style.DIM + str(t) + Style.RESET_ALL
def bold_cyan(t):   return Style.BRIGHT + Fore.CYAN    + str(t) + Style.RESET_ALL
def bold_yellow(t): return Style.BRIGHT + Fore.YELLOW  + str(t) + Style.RESET_ALL
def bold_white(t):  return Style.BRIGHT + Fore.WHITE   + str(t) + Style.RESET_ALL
def bold_green(t):  return Style.BRIGHT + Fore.GREEN   + str(t) + Style.RESET_ALL

W = 56

# ── separadores ───────────────────────────────────────────────────────────────

def _sep():      print(Fore.WHITE + Style.DIM + "─" * W + Style.RESET_ALL)
def _sep_bold(): print(Fore.CYAN  + "═" * W + Style.RESET_ALL)
def _sep_thin(): print(Fore.WHITE + Style.DIM + "·" * W + Style.RESET_ALL)

# ── banner ────────────────────────────────────────────────────────────────────

def print_banner():
    b = Fore.CYAN + Style.BRIGHT
    r = Style.RESET_ALL
    inner  = W - 2
    title  = "SISTEMA DE RECOMENDACAO DE FILMES"
    sub    = "LLaMA 3.2  |  RAG  |  MCP  |  Multiagente"
    credit = "Trabalho Final - Inteligencia Artificial"
    print()
    print(b + "╔" + "═" * inner + "╗" + r)
    print(b + "║" + r + bold_yellow("  🎬  " + title.center(inner - 6)) + b + "║" + r)
    print(b + "║" + r + gray(sub.center(inner))    + b + "║" + r)
    print(b + "║" + r + gray(credit.center(inner)) + b + "║" + r)
    print(b + "╚" + "═" * inner + "╝" + r)
    print()

# ── menus ─────────────────────────────────────────────────────────────────────

def print_menu():
    _sep_bold()
    print(f"  {bold_cyan('MENU PRINCIPAL')}")
    _sep_bold()
    print(f"\n  {bold_yellow('1')}  {white('Perguntas guiadas')}    {gray('— formulario rapido de perfil')}")
    print(f"  {bold_yellow('2')}  {white('Chat dinamico')}        {gray('— 3 perguntas antes da busca')}")
    print(f"  {bold_yellow('3')}  {white('Ver historico')}        {gray('— recomendacoes desta sessao')}")
    print(f"  {bold_yellow('0')}  {white('Sair')}\n")
    _sep_bold()
    print()

def print_post_menu():
    _sep_bold()
    print(f"  {bold_cyan('O QUE DESEJA FAZER?')}")
    _sep_bold()
    print(f"\n  {bold_yellow('1')}  {white('Nova recomendacao')}    {gray('— buscar com novo perfil')}")
    print(f"  {bold_yellow('2')}  {white('Avaliar resultados')}   {gray('— refinar com base no que achou')}")
    print(f"  {bold_yellow('3')}  {white('Voltar ao menu')}       {gray('— menu principal')}\n")
    _sep_bold()
    print()

def _input(prompt: str) -> str:
    try:
        return input(f"  {cyan('❯')} {prompt}").strip()
    except (KeyboardInterrupt, EOFError):
        return ""

def _menu_input() -> str:
    return _input(f"{gray('Opcao: ')}")

# ── helpers de filme ──────────────────────────────────────────────────────────

def _ask(prompt: str, optional: bool = False) -> List[str]:
    suffix = gray("  (opcional, Enter para pular)") if optional else ""
    raw = input(f"  {cyan('›')} {white(prompt)}{suffix}: ").strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]

def _stars(rating: float) -> str:
    filled = int(round(rating / 2))
    bar = "★" * filled + "☆" * (5 - filled)
    if rating >= 7.5:   return bold_green(bar) + gray(f"  {rating:.1f}/10")
    elif rating >= 6.0: return yellow(bar)     + gray(f"  {rating:.1f}/10")
    else:               return red(bar)        + gray(f"  {rating:.1f}/10")

def _print_movie(rank: int, movie: dict, justification: str = "") -> None:
    title     = movie.get("title", "?")
    year      = movie.get("year", "")
    genres    = ", ".join(movie.get("genres", []))
    directors = ", ".join(movie.get("director", []))
    cast      = ", ".join(movie.get("cast", [])[:3])
    rating    = float(movie.get("vote_average", 0))

    rank_fmt = [bold_yellow, bold_white, bold_cyan, bold_cyan, bold_cyan]
    fmt = rank_fmt[rank - 1] if rank <= 5 else bold_white

    print(f"\n  {fmt(f'#{rank}')}  {bold_white(title)}  {gray(str(year))}")
    print(f"      {_stars(rating)}")
    if genres:    print(f"      {gray('Generos  ·')}  {cyan(genres)}")
    if directors: print(f"      {gray('Diretor  ·')}  {magenta(directors)}")
    if cast:      print(f"      {gray('Elenco   ·')}  {white(cast)}")
    if justification:
        print(f"      {yellow('💬')}  {dim(justification.strip().strip(chr(34)))}")

# ── exibição de recomendações ─────────────────────────────────────────────────

def display_recommendations(movies: List[dict], justifications: List[str] = None) -> None:
    justifications = justifications or [""] * len(movies)
    print()
    _sep_bold()
    print(f"  {bold_yellow('🏆  TOP 5 RECOMENDACOES PARA VOCE')}")
    _sep_bold()
    for rank, (movie, just) in enumerate(zip(movies, justifications), 1):
        _print_movie(rank, movie, just)
        if rank < len(movies):
            print(f"\n  ", end="")
            _sep_thin()
    print()
    _sep_bold()
    print()

# ── modo 1: perguntas guiadas ─────────────────────────────────────────────────

def collect_profile_guided() -> UserProfile:
    print()
    _sep_bold()
    print(f"  {bold_yellow('📋  Perguntas Guiadas')}")
    _sep_bold()
    print()
    watched   = _ask("Ultimos filmes que assistiu (separe por virgula)")
    genres    = _ask("Generos favoritos", optional=True)
    actors    = _ask("Atores que voce gosta", optional=True)
    directors = _ask("Diretores favoritos", optional=True)
    avoid     = _ask("Algo que prefere evitar (generos, temas)", optional=True)
    print()
    _sep()
    return UserProfile(
        watched_movies=watched,
        favorite_genres=genres,
        favorite_actors=actors,
        favorite_directors=directors,
        avoid=avoid,
    )

# ── modo 2: chat dinâmico ─────────────────────────────────────────────────────

_CHAT_QUESTIONS = [
    "Que tipo de filme voce gosta de assistir? "
    "(pode falar sobre genero, clima ou tema — ex: acao intensa, algo que emocione, comedia leve...)",

    "Tem algum filme que voce adorou recentemente ou que serve de referencia do que voce gosta?",

    "Tem algo que prefere evitar, ou algum ator ou diretor favorito que podemos considerar?",
]

def collect_profile_chat(llm) -> UserProfile:
    print()
    _sep_bold()
    print(f"  {bold_yellow('💬  Chat Dinamico')}")
    print(f"  {gray('Responda 3 perguntas e buscaremos o filme certo pra voce, caso esteja indeciso pode apertar Enter para pular a pergunta.')}")
    _sep_bold()
    print()

    history = []
    for i, question in enumerate(_CHAT_QUESTIONS, 1):
        print(f"  {bold_cyan(f'Pergunta {i}/3:')} {white(question)}")
        history.append({"role": "assistant", "content": question})
        try:
            answer = input(f"  {cyan('Voce')} {gray('›')} ").strip()
        except (KeyboardInterrupt, EOFError):
            answer = ""
        if not answer:
            answer = "Sem preferencia especifica"
        history.append({"role": "user", "content": answer})
        print()

    print(f"  {gray('Analisando suas respostas...')}")
    profile = llm.extract_profile_from_chat(history)
    print()
    _sep()

    if not profile.is_empty():
        print(f"\n  {bold_cyan('Perfil extraido:')}")
        if profile.watched_movies:   print(f"  {gray('Filmes:')}    {white(', '.join(profile.watched_movies))}")
        if profile.favorite_genres:  print(f"  {gray('Generos:')}   {cyan(', '.join(profile.favorite_genres))}")
        if profile.favorite_actors:  print(f"  {gray('Atores:')}    {white(', '.join(profile.favorite_actors))}")
        if profile.favorite_directors: print(f"  {gray('Diretores:')} {magenta(', '.join(profile.favorite_directors))}")
        if profile.avoid:            print(f"  {gray('Evitar:')}    {red(', '.join(profile.avoid))}")
        print()

    return profile

# ── menu pós-recomendação + avaliação ────────────────────────────────────────

def run_post_menu(orchestrator, profile: UserProfile, movies: List[dict], justifications: List[str], history: List[dict]) -> str:
    """
    Exibe menu pós-recomendação e gerencia o loop de avaliação.
    Retorna 'new' para nova busca ou 'menu' para voltar ao menu principal.
    """
    current_movies   = movies
    current_just     = justifications
    current_profile  = profile
    excluded_titles: List[str] = []

    while True:
        print_post_menu()
        try:
            choice = _menu_input()
        except (KeyboardInterrupt, EOFError):
            return "menu"

        # ── 1: nova recomendação ──
        if choice == "1":
            return "new"

        # ── 2: avaliar ──
        elif choice == "2":
            print()
            _sep_bold()
            print(f"  {bold_yellow('📝  Avaliacao')}")
            print(f"  {gray('Diga o que achou — pode falar livremente.')}")
            print(f"  {gray('Ex: \"ja vi o #1\", \"nao gostei do #3\", \"quero algo mais pesado\"')}")
            _sep_bold()
            print()

            try:
                feedback = input(f"  {cyan('Voce')} {gray('›')} ").strip()
            except (KeyboardInterrupt, EOFError):
                feedback = ""

            if not feedback:
                print(f"\n  {gray('Nenhum feedback informado.')}\n")
                continue

            print(f"\n  {gray('Processando feedback...')}")
            new_profile, new_excluded = orchestrator.llm.refine_profile_from_feedback(
                feedback, current_profile, current_movies
            )
            excluded_titles += new_excluded

            if new_excluded:
                print(f"  {gray('Removendo:')} {red(', '.join(new_excluded))}")

            print(f"  {cyan('⟳')} {white('Buscando novas recomendacoes...')}\n")
            new_movies, new_just = orchestrator.recommend(new_profile, exclude_titles=excluded_titles)
            display_recommendations(new_movies, new_just)
            history.append({"movies": new_movies, "justifications": new_just})

            current_movies  = new_movies
            current_just    = new_just
            current_profile = new_profile

        # ── 3: voltar ao menu ──
        elif choice == "3":
            return "menu"

        else:
            print(f"\n  {red('✗')} Opcao invalida. Digite {yellow('1')}, {yellow('2')} ou {yellow('3')}.\n")

# ── loop principal ────────────────────────────────────────────────────────────

def run(orchestrator) -> None:
    print_banner()
    history: List[dict] = []

    while True:
        print_menu()
        try:
            choice = _menu_input()
        except (KeyboardInterrupt, EOFError):
            choice = "0"

        # ── 1: perguntas guiadas ──
        if choice == "1":
            profile = collect_profile_guided()
            if profile.is_empty():
                print(f"\n  {red('✗ Perfil de usuário vazio. Responda ao menos uma das perguntas.')}\n")
                continue
            print(f"\n  {cyan('⟳')} {white('Analisando perfil e buscando recomendacoes...')}\n")
            movies, justifications = orchestrator.recommend(profile)
            display_recommendations(movies, justifications)
            history.append({"filmes": movies, "justificativas": justifications})
            run_post_menu(orchestrator, profile, movies, justifications, history)

        # ── 2: chat dinâmico ──
        elif choice == "2":
            profile = collect_profile_chat(orchestrator.llm)
            if profile.is_empty():
                print(f"\n  {red('✗ Nao foi possivel extrair preferencias, favor responder ao menos uma das perguntas. Ou tente a opcao 1.')}\n")
                continue
            print(f"  {cyan('⟳')} {white('Buscando recomendacoes...')}\n")
            movies, justifications = orchestrator.recommend(profile)
            display_recommendations(movies, justifications)
            history.append({"filmes": movies, "justificativas": justifications})
            run_post_menu(orchestrator, profile, movies, justifications, history)

        # ── 3: histórico ──
        elif choice == "3":
            if not history:
                print(f"\n  {gray('Nenhuma recomendacao nesta sessao ainda.')}\n")
            else:
                for i, session in enumerate(history, 1):
                    print(f"\n  {bold(f'── Sessao {i} ──')}")
                    display_recommendations(session["filmes"], session.get("justificativas"))

        # ── 0: sair ──
        elif choice == "0":
            print(f"\n  {yellow('Ate mais! Bons filmes. 🎬')}\n")
            break

        else:
            print(f"\n  {red('✗')} Opcao invalida. Digite {yellow('1')}, {yellow('2')}, {yellow('3')} ou {yellow('0')}.\n")
