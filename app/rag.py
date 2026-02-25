"""
RAG using LangChain + Chroma.This file:
- Loads policy docs from /policies
- Splits into chunks
- Embeds chunks
- Stores them in a persisted Chroma DB (local folder)
- Retrieves top-k relevant chunks for case query

"""

#Import all dependencies
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma



# Load the OPENAI_API_KEY environment variable
load_dotenv()

# root paths for policy and db
REPO_ROOT = Path(__file__).resolve().parent.parent
POLICY_DIR = REPO_ROOT / "policies"
PERSIST_DIR = REPO_ROOT / "db" / "chroma_policy"
COLLECTION_NAME = "policy_docs"



#-----------POLICY INGESTION PIPELINE--------
# Define the policy ingestion pipeline that reads policy docs, chunk them, embed and persist them into chroma db
def ingest_policies() -> None:
    #Check if the directory exists
    if not POLICY_DIR.exists():
        raise FileNotFoundError(f"Policy directory not found: {POLICY_DIR}")

    #--------LOADING / PARSING-----------
    # Load all the .md and .txt files from policies/
    loader = DirectoryLoader(
        str(POLICY_DIR),
        glob="**/*.*",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    docs = loader.load()

    if not docs:    #If no .md or /txt files
        raise FileNotFoundError("No policy documents found in /policies")

    #--------CHUNKING---------
    # Split docs into small chunks for retrieval
    splitter = CharacterTextSplitter(
        chunk_size=450,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(docs)

    # Add source and chunk_id as metadata for citations (source + chunk_id)
    # 'source'is already retrieved from DirectoryLoader in doc.metadata
    for i, d in enumerate(chunks):
        d.metadata["chunk_id"] = i


    #----------EMBEDDING------------
    # Create embeddings model (OpenAI)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # Create vector store to 
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(PERSIST_DIR),
        collection_name=COLLECTION_NAME,
    )




#--------------RETRIEVAL PIPELINE-------------
#Load the persisted Chroma DB and return top k.
def get_retriever(k: int = 3):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    db = Chroma(
        persist_directory=str(PERSIST_DIR),
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
    )
    return db.as_retriever(search_kwargs={"k": k})  # Retrieve top k


# Function to build policy from case using risk band and the signal that was fired
def build_policy_query_from_case(case_obj: Dict[str, Any]) -> str:

    risk_band = case_obj.get("risk_assessment", {}).get("risk_band", "UNKNOWN")
    fired = case_obj.get("risk_assessment", {}).get("fired_signals", [])
    fired_text = " ".join(fired)

    return f"risk_band {risk_band}; signals {fired_text}"


# Retrieve what part of the policy that applies to the search. Returns a list with {source, chunk_id, snippet}
def retrieve_policy_snippets(query: str, top_k: int = 3) -> List[Dict[str, Any]]:

    retriever = get_retriever(k=top_k)
    docs = retriever.invoke(query)

    results: List[Dict[str, Any]] = []
    for d in docs:
        source = str(d.metadata.get("source", "unknown")).split("/")[-1].split("\\")[-1]
        chunk_id = int(d.metadata.get("chunk_id", -1))

        results.append({
            "source": source,
            "chunk_id": chunk_id,
            "snippet": d.page_content
        })

    return results