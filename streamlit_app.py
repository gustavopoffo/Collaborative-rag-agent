# streamlit_app.py
import streamlit as st
import os
import uuid
import json
from pathlib import Path
from datetime import datetime

# RAG & embeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings

# RAG helper
from langgraph.rag import build_vectorstore, get_retriever
# Ferramentas
from langgraph.tools import vote_tool, log_action, summarizer_tool
# LLM local
from langchain_community.llms import Ollama


# -------------------------------
# CONFIGURAÇÃO DE PASTAS
# -------------------------------
DB_DIR = "vectorstore"
LOGS_DIR = Path("data/logs")
VOTES_DIR = LOGS_DIR / "votes"
TASK_FILE = LOGS_DIR / "tasks.json"

os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(VOTES_DIR, exist_ok=True)

# LLM offline via Ollama
llm = Ollama(model="qwen2.5:1.5b")


# -------------------------------
# CONFIG STREAMLIT
# -------------------------------
st.set_page_config(
    page_title="Sistema Colaborativo",
    layout="wide"
)

st.title("📚 Sistema Colaborativo — Chat RAG + Dashboard de Tarefas")

# Session State
if "user_id" not in st.session_state:
    st.session_state.user_id = f"user_{str(uuid.uuid4())[:6]}"
if "messages" not in st.session_state:
    st.session_state.messages = []


# -------------------------------
# SIDEBAR — UPLOAD E INDEXAÇÃO
# -------------------------------
with st.sidebar:
    st.header("📂 Upload de PDFs")

    uploaded_files = st.file_uploader(
        "Selecione PDFs (multi)",
        type="pdf",
        accept_multiple_files=True
    )

    if st.button("📥 Indexar PDFs"):
        if not uploaded_files:
            st.warning("Envie ao menos um PDF.")
        else:
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            docs = []

            for pdf in uploaded_files:
                temp_name = f"{uuid.uuid4()}_{pdf.name}"
                with open(temp_name, "wb") as f:
                    f.write(pdf.getvalue())

                loader = PyPDFLoader(temp_name)
                try:
                    pages = loader.load_and_split()
                except:
                    pages = loader.load()

                docs.extend(pages)
                os.remove(temp_name)

            build_vectorstore(docs, collection_name="pdf_collection")

            st.success(f"{len(docs)} páginas indexadas na coleção.")
            log_action({"type": "index", "count": len(docs), "user": st.session_state.user_id})

    st.markdown("---")
    st.header("👤 Identificação")
    st.text_input("Nome do usuário", key="user_label")
    st.write("ID:", st.session_state.user_id)


# -------------------------------
# CHAT — OCUPA TODA A LARGURA
# -------------------------------
st.markdown("## 💬 Chat (RAG, resumo e perguntas)")

# Mostrar histórico
for msg in st.session_state.messages:
    role = msg["role"]
    author = msg.get("user", "???")

    if role == "user":
        st.markdown(f"**{author}**: {msg['content']}")
    else:
        st.markdown(f"**Assistente**: {msg['content']}")

# Input
user_input = st.text_input(
    "Digite aqui (buscar:, resumir: ou pergunta livre sobre os PDFs)",
    key="chat_input"
)

if st.button("Enviar mensagem"):
    if not user_input.strip():
        st.warning("Digite algo.")
    else:
        text = user_input.strip()
        st.session_state.messages.append(
            {"role": "user", "user": st.session_state.user_id, "content": text}
        )
        log_action({"type": "message", "content": text})

        # buscar:
        if text.lower().startswith("buscar:"):
            query = text.split(":", 1)[1].strip()
            retriever = get_retriever("pdf_collection")
            docs = retriever.get_relevant_documents(query)
            ans = "\n\n".join([d.page_content for d in docs])
            st.session_state.messages.append(
                {"role": "assistant", "content": ans}
            )

        # resumir:
        elif text.lower().startswith("resumir:"):
            payload = text.split(":", 1)[1].strip()
            summary = summarizer_tool(payload)
            st.session_state.messages.append(
                {"role": "assistant", "content": summary}
            )

        # pergunta livre -> RAG + LLM
        else:
            retriever = get_retriever("pdf_collection")
            docs = retriever.get_relevant_documents(text)
            ctx = "\n\n".join([d.page_content for d in docs])

            prompt = f"""Responda usando o contexto abaixo (trechos dos PDFs):
CONTEXT:
{ctx}

PERGUNTA:
{text}
"""

            answer = llm.invoke(prompt)
            st.session_state.messages.append(
                {"role": "assistant", "content": answer}
            )

        st.rerun()


# -------------------------------
# DASHBOARD DE TAREFAS
# -------------------------------
st.markdown("---")
st.markdown("## 📋 Dashboard de Tarefas e Votações")

# Carrega tarefas
if TASK_FILE.exists():
    with open(TASK_FILE, "r", encoding="utf-8") as f:
        tasks = json.load(f)
else:
    tasks = []


# -------------------------------
# FORMULÁRIO DE NOVA TAREFA
# -------------------------------
st.markdown("### ➕ Criar nova tarefa")

new_desc = st.text_input("Descrição da tarefa", key="new_desc")
new_assignee = st.text_input("Responsável", key="new_assignee")
new_deadline = st.date_input("Prazo limite", key="new_deadline")

if st.button("Criar tarefa"):
    tid = f"task_{str(uuid.uuid4())[:8]}"

    task = {
        "id": tid,
        "task": new_desc.strip(),
        "assignee": new_assignee.strip(),
        "deadline": str(new_deadline),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    tasks.append(task)
    with open(TASK_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)

    # inicializar votos
    vote_file = VOTES_DIR / f"{tid}.json"
    with open(vote_file, "w", encoding="utf-8") as f:
        json.dump({"sim": 0, "não": 0, "abster": 0, "votes": []}, f)

    st.success(f"Tarefa criada ({tid})")
    st.rerun()


# -------------------------------
# LISTA DE TAREFAS
# -------------------------------
if not tasks:
    st.info("Nenhuma tarefa criada.")
else:
    for task in tasks:
        tid = task["id"]

        st.markdown(f"### 📝 {task['task']}")
        st.write(f"- **ID:** `{tid}`")
        st.write(f"- **Responsável:** {task['assignee']}")
        st.write(f"- **Prazo:** {task['deadline']}")
        st.write(f"- **Criada:** {task['created_at']}")

        # Carregar votação
        vfile = VOTES_DIR / f"{tid}.json"
        with open(vfile, "r", encoding="utf-8") as f:
            tally = json.load(f)

        st.write(f"📊 **Placar:** ")
        st.write(f"- Sim: {tally['sim']}")
        st.write(f"- Não: {tally['não']}")
        st.write(f"- Abster: {tally['abster']}")

        # botões de votação
        c1, c2, c3, c4 = st.columns([1,1,1,1])

        with c1:
            if st.button("👍 Sim", key=f"{tid}_sim"):
                res = vote_tool(tid, st.session_state.user_id, "sim")
                if isinstance(res, dict) and res.get("error"):
                    st.warning(res["error"])
                else:
                    st.success("Voto registrado: sim")
                    st.rerun()

        with c2:
            if st.button("👎 Não", key=f"{tid}_nao"):
                res = vote_tool(tid, st.session_state.user_id, "não")
                if isinstance(res, dict) and res.get("error"):
                    st.warning(res["error"])
                else:
                    st.success("Voto registrado: não")
                    st.rerun()

        with c3:
            if st.button("🤷 Abster", key=f"{tid}_abs"):
                res = vote_tool(tid, st.session_state.user_id, "abster")
                if isinstance(res, dict) and res.get("error"):
                    st.warning(res["error"])
                else:
                    st.success("Voto registrado: abster")
                    st.rerun()

        with c4:
            if st.button("✔ Concluir", key=f"{tid}_del"):
                tasks = [t for t in tasks if t["id"] != tid]
                with open(TASK_FILE, "w", encoding="utf-8") as f:
                    json.dump(tasks, f, indent=2, ensure_ascii=False)
                vfile.unlink(missing_ok=True)
                st.rerun()

        st.markdown("---")
