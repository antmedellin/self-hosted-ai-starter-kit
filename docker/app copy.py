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
    # Prepare pairs for cross-encoder
    pairs = [[query, doc] for doc in docs]
    scores = [float(s) for s in model.predict(pairs)]    # Sort docs by score descending
    score_doc_pairs = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)
    sorted_scores = [score for score, _ in score_doc_pairs]
    reranked = [doc for _, doc in score_doc_pairs]
    return {"reranked": reranked, "scores": sorted_scores}



# test command in bash shell 
"""
curl -X POST http://localhost:8001/rerank \
  -H "Content-Type: application/json" \
  -d '{"query": "What is AI?", "docs": ["AI is artificial intelligence.", "Bananas are yellow.", "AI can learn from data and improve over time."]}' 
"""