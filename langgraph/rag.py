
import os
import uuid
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# Diretório onde os vetores serão salvos
VECTORSTORE_DIR = "data/vectorstore"
os.makedirs(VECTORSTORE_DIR, exist_ok=True)

# Embeddings 100% GRATUITOS e eficientes
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


def load_pdf(file_bytes, filename: str):
    """
    Carrega um PDF enviado pelo usuário e retorna suas páginas como documentos.
    Esse loader funciona offline.
    """
    temp_path = f"/tmp/{uuid.uuid4()}-{filename}"

    with open(temp_path, "wb") as f:
        f.write(file_bytes)

    loader = PyPDFLoader(temp_path)
    pages = loader.load()

    os.remove(temp_path)
    return pages


def build_vectorstore(docs, collection_name: str):
    """
    Cria uma coleção vetorial (Chroma) usando embeddings locais.
    """
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory=VECTORSTORE_DIR
    )

    vectorstore.persist()
    return vectorstore


def get_retriever(collection_name: str):
    """
    Retorna um retriever baseado na coleção salva.
    """
    vectorstore = Chroma(
        persist_directory=VECTORSTORE_DIR,
        collection_name=collection_name,
        embedding_function=embeddings
    )

    return vectorstore.as_retriever(search_kwargs={"k": 3})
