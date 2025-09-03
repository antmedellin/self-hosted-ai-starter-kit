from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os

os.environ["MEM0_TELEMETRY"] = "false"  # Must be before importing mem0
from mem0 import Memory

# Build Mem0 config from env
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text:v1.5")
EMBED_DIMS = int(os.getenv("EMBED_DIMS", "768"))
OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "memories")

MEM0_CONFIG = {
    "llm": {
        "provider": "ollama",
        "config": {
            "model": os.getenv("LLM_MODEL", "gemma3:270m"),
            "temperature": float(os.getenv("LLM_TEMPERATURE", "0.1")),
            "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "2048")),
            "ollama_base_url": OLLAMA_BASE,
        },
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": EMBED_MODEL,
            "embedding_dims": EMBED_DIMS,
            "ollama_base_url": OLLAMA_BASE,
        },
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": QDRANT_COLLECTION,
            "host": QDRANT_HOST,
            "port": QDRANT_PORT,
            "embedding_model_dims": EMBED_DIMS,
        },
    },
}

mem = Memory.from_config(MEM0_CONFIG)

app = FastAPI(title="mem0-local", version="1.0")


# ---- Models for request bodies
class Message(BaseModel):
    role: str
    content: str

class CreateMemoriesBody(BaseModel):
    messages: List[Message]
    metadata: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    # agent_id: Optional[str] = None
    # app_id: Optional[str] = None
    # run_id: Optional[str] = None
    infer: Optional[bool] = False  # If true, run LLM inference after adding memory

class SearchBody(BaseModel):
    query: str
    top_k: Optional[int] = 5
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    run_id: Optional[str] = None


def resolve_user_id(mem0_user_id_header: Optional[str], body_user_id: Optional[str]) -> Optional[str]:
    # Prefer header for compatibility with Mem0 cloud API usage
    return mem0_user_id_header or body_user_id


@app.post("/v1/memories/")
def create_memory(
    body: CreateMemoriesBody,
    mem0_user_id: Optional[str] = Header(default=None, convert_underscores=False, alias="Mem0-User-ID"),
):
    
    print("Received memory payload:", body.model_dump())
    
    user_id = resolve_user_id(mem0_user_id, body.user_id)
    if not body.messages or len(body.messages) == 0:
        raise HTTPException(status_code=400, detail="messages array required")

    # mem.add accepts a list of messages in {role, content} style
    try:
        res = mem.add(
            messages=[m.model_dump() for m in body.messages],
            user_id=user_id,
            metadata=body.metadata or {},
            infer=body.infer,
            
        )
        return {"results": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/memories/search/")
def search_memories(
    body: SearchBody,
    mem0_user_id: Optional[str] = Header(default=None, convert_underscores=False, alias="Mem0-User-ID"),
):
    # Prefer header, then body fields
    user_id = resolve_user_id(mem0_user_id, body.user_id) or body.agent_id or body.run_id
    if not user_id:
        raise HTTPException(status_code=400, detail="At least one of 'user_id', 'agent_id', or 'run_id' must be provided.")
    try:
        results = mem.search(query=body.query, user_id=user_id, limit=body.top_k or 5)
        # results = mem.get_all(user_id=mem0_user_id) # if the above search fails we can try to get all
        return {"results": results.get("results", []), "count": len(results.get("results", []))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
