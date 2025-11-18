# Os 3Cs do Sistema Colaborativo

Este documento descreve como o projeto implementa os 3Cs: **Comunicação**, **Colaboração** e **Coordenação**. Cada seção explica o objetivo conceitual, como o recurso é realizado no código e exemplos práticos de uso.

---

## 1. Comunicação

- Objetivo: permitir troca de mensagens entre usuários e o agente (LLM), mantendo histórico e registro de ações.

- Onde no código:
  - Interface Web: `streamlit_app.py` (seção Chat). O campo de entrada recebe mensagens do usuário e exibe o histórico armazenado em `st.session_state.messages`.
  - Logging: `langgraph/tools.py` → `log_action()` grava eventos em `data/logs/actions.jsonl`.

- Fluxo e exemplos:
  - Usuário escreve uma mensagem livre: o texto é enviado ao LLM local (`Ollama`) e a resposta é adicionada ao histórico.
  - Mensagens especiais: prefixos como `buscar:`, `resumir:` ou `votar:` acionam caminhos/funcionalidades específicas.

- Arquivos e estruturas de dados relevantes:
  - Histórico em sessão: `st.session_state.messages` (lista de mensagens com `role`, `user`, `content`).
  - Log persistente: `data/logs/actions.jsonl` (uma linha JSON por evento).

---

## 2. Colaboração

- Objetivo: permitir construção coletiva de respostas, decisões e documentos a partir de contribuições dos participantes e do agente.

- Onde no código:
  - RAG (Recuperação + Geração): `langgraph/rag.py` + `streamlit_app.py` — usuários fazem perguntas sobre PDFs indexados; o sistema recupera trechos e usa o LLM para responder com contexto compartilhado.
  - Sumário colaborativo: `langgraph/tools.py` → `summarizer_tool()` (placeholder que pode ser substituído por um LLM para consolidar contribuições).
  - Workflow: `langgraph/workflow.py` define nós (LLM, RAG, summarizer, vote, task) que podem ser encadeados para compor respostas ou ações.

- Fluxo e exemplos:
  - Usuários indexam PDFs via sidebar e, ao perguntar sobre o conteúdo, o agente retorna respostas construídas a partir dos mesmos documentos — isto garante um contexto comum de colaboração.
  - Resumos: comandos `resumir:` permitem que trechos ou textos sejam condensados, servindo como base para decisões coletivas.

- Arquivos e dados:
  - Vectorstore (Chroma): pasta `vectorstore/` contém dados indexados para RAG.

---

## 3. Coordenação

- Objetivo: orquestrar atividades, controlar o fluxo de trabalho, atribuir tarefas e gerenciar decisões (votações).

- Onde no código:
  - Dashboard de Tarefas: `streamlit_app.py` (sessão "Dashboard de Tarefas e Votações"). Criação de tarefas grava `data/logs/tasks.json`.
  - Votação: `langgraph/tools.py` → `vote_tool()` registra votos em `data/logs/votes/<task_id>.json` e garante que cada usuário vote apenas uma vez.
  - Workflow programático: `langgraph/workflow.py` (o grafo compilado define nós e transições condicionalmente, coordenando execução automatizada de ferramentas).

- Fluxo e exemplos:
  - Criar tarefa: o formulário cria um objeto de tarefa salvo em `tasks.json` e inicializa um arquivo de votos correspondente em `data/logs/votes/`.
  - Votar: cada usuário é identificado por `st.session_state.user_id`; `vote_tool` valida repetição e atualiza o placar (sim / não / abster).
  - Concluir tarefa: botão `✔ Concluir` remove a tarefa e seu arquivo de votos.

- Arquivos e estruturas de dados:
  - `data/logs/tasks.json` — lista de tarefas.
  - `data/logs/votes/<task_id>.json` — estrutura padrão: `{"sim": n, "não": n, "abster": n, "votes": [...]}`.

---

## Integração entre os 3Cs

- Comunicação fornece os dados brutos (mensagens, perguntas, feedback).
- Colaboração agrega e processa esses dados para produzir conteúdo compartilhável (resumos, respostas, decisões).
- Coordenação organiza quando e como ações coletivas ocorrem (tarefas, votações, execução do workflow).

Exemplo prático (fim a fim):
1. Usuário A indexa um PDF (Comunicação/Colaboração).
2. Usuário B pergunta sobre o PDF e o agente responde com trechos e resumo (Colaboração).
3. O grupo decide criar uma tarefa para revisar o documento; cria-se a tarefa no dashboard (Coordenação).
4. Usuários votam na tarefa; o sistema conta e bloqueia votos duplicados (Coordenação + Comunicação).

---

## Sugestões de evolução

- Tornar o `summarizer_tool` um passo LLM configurável para melhorar a qualidade dos resumos colaborativos.
- Implementar edição e alteração de voto (atualmente o sistema bloqueia votos duplicados; é possível estender para permitir troca de voto).
- Exibir no UI indicadores visuais de quem já votou (melhoria na camada de Comunicação/Coordenação).

---

## Referências rápidas no código

- Chat / interface: `streamlit_app.py`
- RAG / embeddings: `langgraph/rag.py`
- Workflow de nós: `langgraph/workflow.py`
- Ferramentas auxiliares: `langgraph/tools.py`
- Logs e armazenamento: `data/logs/`, `vectorstore/`

