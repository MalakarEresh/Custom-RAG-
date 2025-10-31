1. create a virtual environment and install the libraries included in the requirements.txt
2. create an .env file as you require some of the API keys

    eg:     # SQLite Database URL (local file)
            DATABASE_URL="sqlite:///./YOUR_DB_NAMEHERE.db"

            # Pinecone Configuration
            PINECONE_API_KEY="YOUR_PINECONE_API_KEY"


            # Upstash Redis Configuration
            REDIS_URL="YOUR_REDIS_ENDPOINT"

3. To run use command  
            uvicorn app.main:app --reload
    from your root directory

4. This project is just a backend created using FastAPI to demonstrate document ingestion and RAG implementation.
    * For now the RAG implementation uses a simple keyword based filtering in order to give response.
    * In simple the system is not intelligent in order to give the proper response we want and we can improve it 
      by integrating AI models.
    * The document ingestion uses twe chunking technique fixed simple and paragraph with a selector provided.
    * The documents are then stored in vector database, in this i have used Pinecone. 
