# Sistema Colaborativo — Chat RAG + Dashboard de Tarefas

Projeto demonstrativo de um sistema colaborativo local que integra:
- Chat com RAG (Recuperação + Geração) usando PDFs indexados;
- Dashboard de tarefas e votações colaborativas;
- Um workflow interno (grafo) para coordenar ferramentas e ações.

## Estrutura principal
- `streamlit_app.py` — interface web (Streamlit): upload de PDFs, chat RAG, criação de tarefas e votação.
- `langgraph/` — lógica do grafo e ferramentas:
  - `rag.py` — construção do vectorstore (Chroma) e helper retriever;
  - `workflow.py` — definição do grafo de estado (nós e transições);
  - `tools.py` — utilitários: logging, sumarização, votação e criação de tarefas;
  - `state.py` — modelo de estado usado pelo grafo.
- `data/logs/` — logs de ações e persistência de tarefas/votos.
- `vectorstore/` — coleção Chroma persistida com embeds das páginas de PDF.
- `scripts/` — utilitários de desenvolvimento (por exemplo `show_graph.py` para inspecionar/exportar o grafo).
- `documentacao/` — documentos explicativos (contém `3cs.md`).

## Os 3Cs (resumo)
- Comunicação: troca de mensagens entre usuários e agente; históricos em sessão e log persistente.
- Colaboração: construção conjunta de respostas a partir de documentos indexados e resumos.
- Coordenação: criação/atribuição de tarefas e votações para tomadas de decisão.

(Ver `documentacao/3cs.md` para uma explicação detalhada com exemplos e referências de código.)

## Execução rápida (Windows)
1. Ative o ambiente virtual:
```powershell
. .venv\Scripts\Activate.ps1
```
2. Instale dependências (se necessário):
```powershell
pip install -r requirements.txt
```
3. Rode o app Streamlit:
```powershell
streamlit run streamlit_app.py
```
4. Abra o navegador no endereço que o Streamlit indicar (usualmente `http://localhost:8501`).

## Gerar imagem do grafo (opcional)
- Rode dentro de C:\Colaborativos\colab-rag-system :
    python langgraph\workflow.py
    isso vai gerar um grafo grafo_workflow.mmd, copie e cole em https://mermaid.live

## Votação e tarefas
- Tarefas são salvas em `data/logs/tasks.json`.
- Cada tarefa tem um arquivo de votos `data/logs/votes/<task_id>.json` com estrutura:
```json
{"sim": 0, "não": 0, "abster": 0, "votes": []}
```
- Implementação atual: cada usuário (identificado por `st.session_state.user_id`) só pode votar uma vez por tarefa. Se preferir, posso alterar para permitir troca de voto.

