import os
import json
import time

# Diretórios
LOG_DIR = "data/logs"
VOTE_DIR = "data/logs/votes"
TASK_FILE = "data/logs/tasks.json"
LOG_FILE = "data/logs/actions.jsonl"

# Garantir estrutura de pastas
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(VOTE_DIR, exist_ok=True)


# ----------------------------------------------------------
# 1. LOGGING – (Comunicação)
# ----------------------------------------------------------
def log_action(action: dict):
    """
    Registra mensagens, tarefas, buscas, votos e resumos.
    Cada registro é salvo em formato JSONL.
    """
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(action, ensure_ascii=False) + "\n")


# ----------------------------------------------------------
# 2. SUMARIZAÇÃO – (Colaboração)
# ----------------------------------------------------------
def summarizer_tool(text: str) -> str:
    """
    Resumo simples placeholder. O LLM refinará no workflow.
    """
    if not text:
        return "Nenhum texto fornecido para resumo."

    if len(text) < 300:
        return text

    return text[:400] + "..."


# ----------------------------------------------------------
# 3. VOTAÇÃO – (Coordenação)
# ----------------------------------------------------------
def vote_tool(topic: str, user: str, vote: str):
    """
    Registra votos, valida voto e retorna placar atualizado.
    """
    vote = vote.lower().strip()

    if vote not in ["sim", "não", "nao", "abster"]:
        return {"error": "Voto inválido. Use: sim, não, abster"}

    # Normalizar "não" e "nao"
    if vote == "nao":
        vote = "não"

    file_path = f"{VOTE_DIR}/{topic}.json"

    # Carregar votos existentes
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            tally = json.load(f)
    else:
        tally = {"sim": 0, "não": 0, "abster": 0, "votes": []}

    # Verificar se o usuário já votou — cada usuário só pode votar uma vez
    if any(v.get("user") == user for v in tally.get("votes", [])):
        return {"error": "Usuário já votou nesta pauta."}

    # Registrar novo voto
    tally[vote] += 1
    tally["votes"].append({"user": user, "vote": vote})

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(tally, f, indent=2, ensure_ascii=False)

    # Log
    log_action({"type": "vote", "topic": topic, "user": user, "vote": vote})

    return tally


# ----------------------------------------------------------
# 4. TAREFAS – (Coordenação)
# ----------------------------------------------------------
def create_task(description: str, assignee: str, deadline: str):
    """
    Criação e registro de tarefas no arquivo tasks.json.
    """
    # Carregar tarefas atuais
    if os.path.exists(TASK_FILE):
        with open(TASK_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)
    else:
        tasks = []

    new_task = {
        "task": description,
        "assignee": assignee,
        "deadline": deadline,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    tasks.append(new_task)

    # Salvar
    with open(TASK_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)

    # Log
    log_action({"type": "task", "task": description, "assignee": assignee})

    return tasks
