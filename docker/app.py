from fastapi import FastAPI, Request
from sentence_transformers import CrossEncoder
import torch

app = FastAPI()

MODEL_NAME = "mixedbread-ai/mxbai-rerank-base-v1"
model = CrossEncoder(MODEL_NAME)

@app.post("/rerank")
async def rerank(request: Request):
    data = await request.json()
    query = data.get("query")
    docs = data.get("docs")

    if not query or not docs:
        return {"error": "Missing query or docs"}

    # Extract text and metadata
    pairs = [[query, item["doc"]] for item in docs]
    scores = [float(s) for s in model.predict(pairs)]

    # Combine scores with original doc+metadata
    scored_docs = [
        {"score": score, "doc": item["doc"], "metadata": item.get("metadata")}
        for score, item in zip(scores, docs)
    ]

    # Sort by score descending
    reranked = sorted(scored_docs, key=lambda x: x["score"], reverse=True)

    return {"reranked": reranked}
