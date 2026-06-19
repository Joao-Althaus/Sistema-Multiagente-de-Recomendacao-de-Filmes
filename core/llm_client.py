"""
LLM Client

Interface com o modelo de linguagem local via Ollama (LLAMA 3.2).
Abstrai as chamadas de geração de texto usadas pelos agentes:

- chat(messages)          : chamada genérica de chat completion
- generate_query(profile) : constrói query semântica a partir do perfil
- generate_justification(movie, profile) : gera justificativa personalizada
"""
