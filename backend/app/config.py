from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./github_intel.db"
    GITHUB_TOKEN: str = ""
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    GROQ_API_KEY: str = ""
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    REPOS_DIR: str = "./repos"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
