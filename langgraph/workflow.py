from typing import TypedDict, List, Dict, Any

# importa suas ferramentas locais
from tools import summarizer_tool, vote_tool, create_task, log_action

# RAG
from rag import get_retriever


# StateGraph moderno
from langgraph.graph import StateGraph, END

# LLM local via Ollama
from langchain_community.llms import Ollama


# ----------------------------------------------------------
# STATE — substitui o antigo "State" (que não existe mais)
# ----------------------------------------------------------
class GraphState(TypedDict, total=False):
    messages: List[Dict[str, Any]]
    tool: str
    query: str
    text: str
    topic: str
    choice: str
    user: str
    desc: str
    deadline: str


# LLM offline - Qwen rodando no Ollama
llm = Ollama(model="qwen2.5:1.5b")


# ----------------------------------------------------------
# NODE 1 — LLM NODE
# ----------------------------------------------------------
def llm_node(state: GraphState):

    last_message = state["messages"][-1]["content"].lower()

    # Ferramentas ativadas por comando
    if last_message.startswith("buscar:"):
        query = last_message.replace("buscar:", "").strip()
        return {"tool": "rag", "query": query}

    if last_message.startswith("resumir:"):
        text = last_message.replace("resumir:", "").strip()
        return {"tool": "summarizer", "text": text}

    if last_message.startswith("votar:"):
        try:
            _, rest = last_message.split(":", 1)
            topic, choice = rest.split(";")
            return {"tool": "vote", "topic": topic.strip(), "choice": choice.strip()}
        except:
            return {
                "messages": state["messages"] + [
                    {"role": "assistant", "content": "Formato inválido. Use: votar: tema ; escolha"}
                ]
            }

    if last_message.startswith("tarefa:"):
        try:
            _, rest = last_message.split(":", 1)
            desc, user, deadline = rest.split(";")
            return {
                "tool": "task",
                "desc": desc.strip(),
                "user": user.strip(),
                "deadline": deadline.strip()
            }
        except:
            return {
                "messages": state["messages"] + [
                    {"role": "assistant", "content": "Formato inválido. Use: tarefa: descrição ; usuário ; prazo"}
                ]
            }

    # Resposta normal do LLM
    answer = llm.invoke(last_message)

    return {
        "messages": state["messages"] + [
            {"role": "assistant", "content": answer}
        ]
    }


# ----------------------------------------------------------
# NODE 2 — RAG NODE
# ----------------------------------------------------------
def rag_node(state: GraphState):

    query = state["query"]
    retriever = get_retriever("pdf_collection")   # seu índice
    docs = retriever.get_relevant_documents(query)

    text = "\n".join([d.page_content for d in docs]) if docs else "Nenhum resultado encontrado."

    log_action({"type": "rag_query", "query": query})

    return {
        "messages": state["messages"] + [
            {"role": "assistant", "content": text}
        ]
    }


# ----------------------------------------------------------
# NODE 3 — SUMMARIZER NODE
# ----------------------------------------------------------
def summarizer_node(state: GraphState):

    summary = summarizer_tool(state["text"])
    log_action({"type": "summary"})

    return {
        "messages": state["messages"] + [
            {"role": "assistant", "content": summary}
        ]
    }


# ----------------------------------------------------------
# NODE 4 — VOTING NODE
# ----------------------------------------------------------
def voting_node(state: GraphState):

    topic = state["topic"]
    choice = state["choice"]

    user = state["messages"][-1].get("user", "desconhecido")

    result = vote_tool(topic, user, choice)

    return {
        "messages": state["messages"] + [
            {"role": "assistant", "content": str(result)}
        ]
    }


# ----------------------------------------------------------
# NODE 5 — TASK NODE
# ----------------------------------------------------------
def task_node(state: GraphState):

    desc = state["desc"]
    user = state["user"]
    deadline = state["deadline"]

    create_task(desc, user, deadline)

    return {
        "messages": state["messages"] + [
            {"role": "assistant", "content": "Tarefa criada com sucesso!"}
        ]
    }


# ----------------------------------------------------------
# FUNÇÃO PRINCIPAL — build_graph()
# ----------------------------------------------------------
def build_graph():

    graph = StateGraph(GraphState)

    graph.add_node("llm", llm_node)
    graph.add_node("rag", rag_node)
    graph.add_node("summarizer", summarizer_node)
    graph.add_node("vote", voting_node)
    graph.add_node("task", task_node)

    graph.set_entry_point("llm")

    graph.add_conditional_edges(
        "llm",
        lambda state: state.get("tool", None),
        {
            "rag": "rag",
            "summarizer": "summarizer",
            "vote": "vote",
            "task": "task",
            None: END
        }
    )

    graph.add_edge("rag", END)
    graph.add_edge("summarizer", END)
    graph.add_edge("vote", END)
    graph.add_edge("task", END)

    return graph.compile()

# ----------------------------------------------------------
# EXECUTAR PARA GERAR O GRAFO (PNG E MERMAID NO TERMINAL)
# ----------------------------------------------------------
if __name__ == "__main__":
    compiled = build_graph()
    g = compiled.get_graph()

    mermaid = "graph TD;\n"

    # Lista nós
    for node in g.nodes:
        mermaid += f"    {node};\n"

    # Lista arestas
    for edge in g.edges:
        mermaid += f"    {edge[0]} --> {edge[1]};\n"

    with open("grafo_workflow.mmd", "w", encoding="utf-8") as f:
        f.write(mermaid)

    print("\nArquivo gerado: grafo_workflow.mmd")
    print("Abra em https://mermaid.live para visualizar o grafo.\n")
