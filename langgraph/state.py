# langgraph/state.py

from typing import TypedDict, List, Dict, Any, Optional


class State(TypedDict, total=False):
    """
    Estrutura do estado compartilhado entre os nós do LangGraph.
    Cada nó pode adicionar campos sem quebrar o grafo.
    """
    messages: List[Dict[str, Any]]

    # Campos opcionais usados por ferramentas
    tool: Optional[str]

    # RAG
    query: Optional[str]

    # Summarizer
    text: Optional[str]

    # Voting
    topic: Optional[str]
    choice: Optional[str]

    # Tasks
    desc: Optional[str]
    user: Optional[str]
    deadline: Optional[str]
