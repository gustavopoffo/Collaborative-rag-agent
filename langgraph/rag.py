import os
import uuid
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings


# Diretório onde o VectorStore será salvo
VECTORSTORE_DIR = "vectorstore"   # Compatível com o Streamlit
os.makedirs(VECTORSTORE_DIR, exist_ok=True)

# Nome padrão da coleção usada pelo workflow
DEFAULT_COLLECTION = "pdf_collection"

# Embeddings totalmente offline
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# ---------------------------------------------------------
# CARREGAR PDF (COMPATÍVEL COM WINDOWS)
# ---------------------------------------------------------
def load_pdf(file_bytes, filename: str):
    """
    Salva o PDF temporariamente e carrega suas páginas.
    Funciona em Windows e Linux.
    """
    temp_path = f"{uuid.uuid4()}-{filename}"  # sem /tmp/
    
    with open(temp_path, "wb") as f:
        f.write(file_bytes)

    loader = PyPDFLoader(temp_path)
    pages = loader.load()

    # Remover arquivo temporário
    os.remove(temp_path)

    return pages


# ---------------------------------------------------------
# CRIAR VECTORESTORE
# ---------------------------------------------------------
def build_vectorstore(docs, collection_name: str = DEFAULT_COLLECTION):
    """
    Cria e salva a coleção vetorial usada pelo RAG.
    O nome precisa ser pdf_collection para o workflow funcionar.
    """
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=VECTORSTORE_DIR,
        collection_name=collection_name
    )

    vectorstore.persist()
    return vectorstore


# ---------------------------------------------------------
# RETRIEVER PADRÃO PARA O WORKFLOW
# ---------------------------------------------------------
def get_retriever(collection_name: str = DEFAULT_COLLECTION):
    """
    Carrega a coleção salva e retorna seu retriever.
    """
    vectorstore = Chroma(
        persist_directory=VECTORSTORE_DIR,
        collection_name=collection_name,
        embedding_function=embeddings
    )

    # Some versions of the vectorstore retriever object may not expose
    # `get_relevant_documents` directly. Provide a small wrapper that
    # guarantees this method is available and delegates to the underlying
    # vectorstore `similarity_search` implementation.
    class _SimpleRetriever:
        def __init__(self, vs, k=3):
            self._vs = vs
            self._k = k

        def get_relevant_documents(self, query: str):
            return self._vs.similarity_search(query, k=self._k)

        # keep compatibility with some calling code that may use different
        # method names in other environments
        def get_relevant_documents_with_scores(self, query: str):
            return self._vs.similarity_search_with_score(query, k=self._k)

    return _SimpleRetriever(vectorstore, k=3)
