import os
import json
import time

LOG_FILE = "data/logs/actions.jsonl"
TASK_FILE = "data/logs/tasks.json"
VOTE_DIR = "data/logs/votes"

os.makedirs("data/logs", exist_ok=True)
os.makedirs(VOTE_DIR, exist_ok=True)

# ----------------------------------------------------------
# 1. LOGGING – (Comunicação)
# ----------------------------------------------------------
def log_action(action: dict):
    """
    Registra mensagens, tarefas e votos.
    """
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(action, ensure_ascii=False) + "\n")

# ----------------------------------------------------------
# 2. SUMARIZAÇÃO – (Colaboração)
# ----------------------------------------------------------
def summarizer_tool(text: str) -> str:
    """
    Resumo simples (placeholder).
    Depois o LLM do LangGraph fará refinamento.
    """
    if len(text) < 300:
        return text

    return text[:400] + "..."

# ----------------------------------------------------------
# 3. VOTAÇÃO – (Coordenação)
# ----------------------------------------------------------
def vote_tool(topic: str, user: str, vote: str):
    """
    Registra votos e retorna o placar.
    """
    file_path = f"{VOTE_DIR}/{topic}.json"

    # Carrega votos existentes
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            tally = json.load(f)
    else:
        tally = {"yes": 0, "no": 0, "abstain": 0, "votes": []}

    # Atualiza contagem
    tally[vote] += 1
    tally["votes"].append({"user": user, "vote": vote})

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(tally, f, indent=2, ensure_ascii=False)

    log_action({"type": "vote", "topic": topic, "user": user, "vote": vote})

    return tally

# ----------------------------------------------------------
# 4. TAREFAS – (Coordenação)
# ----------------------------------------------------------
def create_task(description: str, assignee: str, deadline: str):
    """
    Criação e registro de tarefas colaborativas.
    """
    if os.path.exists(TASK_FILE):
        with open(TASK_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)
    else:
        tasks = []

    new_task = {
        "task": description,
        "assignee": assignee,
        "deadline": deadline,
        "created_at": time.time()
    }

    tasks.append(new_task)

    with open(TASK_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)

    log_action({"type": "task", "task": description, "assignee": assignee})

    return tasks