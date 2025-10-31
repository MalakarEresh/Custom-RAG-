from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Literal

from . import services, schemas, db

router = APIRouter()

@router.post("/ingest", response_model=schemas.DocumentUploadResponse)
async def document_ingestion(
    chunking_strategy: Literal["simple", "paragraph"] = Form(...),
    file: UploadFile = File(...),
    db_session: Session = Depends(db.get_db)
):
    if not (file.filename.endswith(".pdf") or file.filename.endswith(".txt")):
        raise HTTPException(status_code=400, detail="Invalid file type.")
    
    try:
        
        result = services.process_and_store_document(db_session, file, chunking_strategy)
        
       
        return {
            "filename": file.filename,
            "message": "Document processed successfully.",
            **result  
        }
    except Exception as e:
       
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.post("/chat", response_model=schemas.ChatResponse)
async def conversational_rag(request: schemas.ChatRequest):
    try:
        response = services.custom_rag(request.query, request.session_id)
        return {"response": response}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.post("/book-interview", response_model=schemas.BookingResponse)
async def interview_booking(
    booking_data: schemas.BookingRequest,
    db_session: Session = Depends(db.get_db)
):
    try:
        booking = services.book_interview(db_session, booking_data)
        return {"message": "Interview booked successfully.", "booking_id": booking.id}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")