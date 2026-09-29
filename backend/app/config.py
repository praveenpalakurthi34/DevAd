from pydantic_settings import BaseSettings
from pathlib import Path
import os

# Load .env from project root
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"

class Settings(BaseSettings):
    # Hindsight
    HINDSIGHT_API_URL: str = "http://localhost:8100"
    HINDSIGHT_API_KEY: str = ""
    HINDSIGHT_BANK_ID: str = "devad-demo"
    
    # Groq
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    
    # Database
    DATABASE_URL: str = "sqlite:///./devad.db"
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:5173"
    
    model_config = {
        "env_file": str(ENV_FILE),
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }
    
    def validate_required(self):
        """Fail fast if critical config is missing."""
        missing = []
        if not self.GROQ_API_KEY or self.GROQ_API_KEY == "your-groq-api-key-here":
            missing.append("GROQ_API_KEY")
        if missing:
            import warnings
            warnings.warn(f"Missing required config: {', '.join(missing)}. Some features will be unavailable.")

settings = Settings()
settings.validate_required()
