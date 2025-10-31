import uuid
import json
import re
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sentence_transformers import SentenceTransformer
import redis
import PyPDF2
from pinecone import Pinecone, ServerlessSpec

from . import db, schemas
from .config import settings

# PINECONE
pc = Pinecone(api_key=settings.PINECONE_API_KEY)
PINECONE_INDEX_NAME = "rag-project"
if PINECONE_INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=PINECONE_INDEX_NAME, dimension=384, metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
pinecone_index = pc.Index(PINECONE_INDEX_NAME)

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


# Document Ingestion

def extract_text_from_file(file: Any) -> str:
    if file.filename.endswith(".pdf"):
        reader = PyPDF2.PdfReader(file.file)
        return "".join(page.extract_text() for page in reader.pages)
    elif file.filename.endswith(".txt"):
        return file.file.read().decode("utf-8")
    return ""

def chunk_text(text: str, strategy: str) -> List[str]:
    if strategy == "simple":
        chunk_size = 1000
        overlap = 100
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - overlap)]
    elif strategy == "paragraph":
        return [p.strip() for p in text.split("\n\n") if p.strip()]
    raise ValueError("Invalid chunking strategy")


def process_and_store_document(db_session: Session, file: Any, chunking_strategy: str) -> Dict:
    db_document = db.Document(filename=file.filename)
    db_session.add(db_document)
    db_session.commit()
    db_session.refresh(db_document)

    text = extract_text_from_file(file)
    chunks = chunk_text(text, chunking_strategy)
    
    vectors_to_upsert = []
    
    for i, text_chunk in enumerate(chunks):
        pinecone_id = str(uuid.uuid4())
        vectors_to_upsert.append({
            "id": pinecone_id,
            "values": [],
            "metadata": {"text": text_chunk}
        })
        db_chunk = db.Chunk(
            chunk_id_pinecone=pinecone_id,
            document_id=db_document.id,
            chunk_index=i,
            chunking_strategy=chunking_strategy
        )
        db_session.add(db_chunk)

    if not vectors_to_upsert:
        db_session.commit()
        return {"document_id": db_document.id, "chunks_created": 0}

    all_chunks_text = [v['metadata']['text'] for v in vectors_to_upsert]
    all_embeddings = embedding_model.encode(all_chunks_text).tolist()

    for i, vector in enumerate(vectors_to_upsert):
        vector['values'] = all_embeddings[i]
        
    pinecone_index.upsert(vectors=vectors_to_upsert)
    db_session.commit()

    return {"document_id": db_document.id, "chunks_created": len(chunks)}


# Conversational RAG

def get_chat_history(session_id: str) -> List[Dict]:
    history = redis_client.lrange(session_id, 0, -1)
    return [json.loads(h) for h in history]

def add_to_chat_history(session_id: str, user_query: str, bot_response: str):
    redis_client.rpush(session_id, json.dumps({"user": user_query, "bot": bot_response}))
    redis_client.ltrim(session_id, -10, -1)
    redis_client.expire(session_id, 86400)


def custom_rag(query: str, session_id: str) -> str:
    query_embedding = embedding_model.encode(query).tolist()
    search_results = pinecone_index.query(vector=query_embedding, top_k=3, include_metadata=True)

    
    context = " ".join([hit['metadata']['text'] for hit in search_results['matches']])

    # Simple keyword-based filtering to avoid dumping entire text
    query_words = [w.lower() for w in re.findall(r'\w+', query)]
    sentences = re.split(r'(?<=[.!?]) +', context)
    relevant_sentences = [
        s for s in sentences if any(qw in s.lower() for qw in query_words)
    ]

    if relevant_sentences:
        final_answer = " ".join(relevant_sentences[:2])
        response = f"Based on the document, here's what I found:\n{final_answer}"
    elif context.strip():
        response = "I found some related information but couldn’t identify a direct answer."
    else:
        response = "I couldn't find any relevant information in the documents."

    add_to_chat_history(session_id, query, response)
    return response


# Interview Booking

def book_interview(db_session: Session, booking_data: schemas.BookingRequest) -> db.InterviewBooking:
    booking_datetime_str = f"{booking_data.date} {booking_data.time}"
    try:
        booking_datetime = datetime.strptime(booking_datetime_str, "%Y-%m-%d %H:%M")
    except ValueError:
        booking_datetime = datetime.strptime(booking_datetime_str, "%Y-%m-%d %I:%M%p")
    
    booking = db.InterviewBooking(
        name=booking_data.name, email=booking_data.email, datetime=booking_datetime
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)
    return booking
