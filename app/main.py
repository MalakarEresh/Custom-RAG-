from fastapi import FastAPI
from . import api

app = FastAPI(
    title="Custom RAG"
    
)

app.include_router(api.router, prefix="/api", tags=["RAG System"])

@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "ok", "message": "Welcome to the RAG API!"}


