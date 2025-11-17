# langgraph/state.py

from typing import TypedDict, List, Dict, Any

class State(TypedDict):
    """
    Estrutura do estado compartilhado entre os nós do LangGraph.
    """
    messages: List[Dict[str, Any]]
