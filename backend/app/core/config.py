import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Automated Expense Auditor"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ENVIRONMENT: str = "development"
    
    POSTGRES_DB: str = "expense_auditor"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: str = "5432"
    
    DATABASE_URL: str = "sqlite:///./project40.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_database_url(self) -> str:
        # If explicitly set in environment
        env_url = os.getenv("DATABASE_URL")
        if env_url:
            return env_url
        
        # If running inside Docker (detected by env or container environment)
        if os.getenv("DOCKER_CONTAINER") or self.ENVIRONMENT == "production":
            return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            
        # Default local/test fallback to SQLite
        return self.DATABASE_URL

settings = Settings()