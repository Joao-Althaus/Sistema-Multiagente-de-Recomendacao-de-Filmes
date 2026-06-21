"""
Entry point do Sistema Multiagente de Recomendação de Filmes.

Inicializa o RAGEngine, instancia os agentes e inicia o terminal interativo.

Flags:
    --test-rag   Abre loop interativo de busca direta no RAG (sem LLM/agentes).
"""

import sys

from core.rag_engine import RAGEngine


def main():
    test_rag = "--test-rag" in sys.argv

    print("Carregando RAG Engine...")
    rag = RAGEngine()
    print("RAG Engine pronto.\n")

    if test_rag:
        from cli.terminal import run_rag_test
        run_rag_test(rag)
        return

    from cli.terminal import run
    from AGENTS.orchestrator import OrchestratorAgent

    orchestrator = OrchestratorAgent()
    run(orchestrator)


if __name__ == "__main__":
    main()
