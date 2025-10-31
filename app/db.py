from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime
from .config import settings

# SQL Database for Metadata and Bookings 
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()



class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
  
    chunks = relationship("Chunk", back_populates="document")

class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(Integer, primary_key=True, index=True)
    chunk_id_pinecone = Column(String, unique=True, index=True) # The UUID stored in Pinecone
    document_id = Column(Integer, ForeignKey("documents.id")) 
    chunk_index = Column(Integer)
    chunking_strategy = Column(String)

    document = relationship("Document", back_populates="chunks")


# INTERVIEW BOOKING

class InterviewBooking(Base):
    __tablename__ = "interview_bookings"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, index=True)
    datetime = Column(DateTime)

# Create all tables in the database
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()