from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    PINECONE_API_KEY: str
    REDIS_URL: str

    class Config:
        env_file = ".env"

settings = Settings()