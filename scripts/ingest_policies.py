"""
To be run anytime the policy documents change

"""

from app.rag import ingest_policies

if __name__ == "__main__":
    ingest_policies()
    print("Policy ingestion complete. Vector DB created in db/chroma_policy/")