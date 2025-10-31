from pydantic import BaseModel, EmailStr

class DocumentUploadResponse(BaseModel):
    filename: str
    message: str
    document_id: int
    chunks_created: int

class ChatRequest(BaseModel):
    session_id: str
    query: str

class ChatResponse(BaseModel):
    response: str

class BookingRequest(BaseModel):
    name: str
    email: EmailStr
    date: str  # Format: YYYY-MM-DD
    time: str  # Format: HH:MM or HH:MMam/pm

class BookingResponse(BaseModel):
    message: str
    booking_id: int