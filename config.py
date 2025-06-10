import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Model Configuration - Set to use remote API
    USE_REMOTE_API = os.getenv("USE_REMOTE_API", "false").lower() == "true"
    
    # Remote API Settings (OpenAI, Anthropic, Together, etc.)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY") 
    TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
    
    # Remote model options
    REMOTE_MODEL_PROVIDER = os.getenv("REMOTE_MODEL_PROVIDER", "openai")  # openai, anthropic, together
    REMOTE_MODEL_NAME = os.getenv("REMOTE_MODEL_NAME", "gpt-3.5-turbo")
    
    # Ollama settings (local)
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama2:7b")  # or "mistral:7b", "codellama:7b"
    
    # Data paths
    HTS_BASE_URL = "https://hts.usitc.gov"
    VECTOR_DB_PATH = "data/vector_db"
    SQLITE_DB_PATH = "data/hts_data.db"
    DATA_DIR = "data"
    
    # Model settings
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # Country code mappings for enhancement
    COUNTRY_CODES = {
        "AU": "Australia", "CA": "Canada", "CN": "China", 
        "DE": "Germany", "FR": "France", "GB": "United Kingdom",
        "IN": "India", "JP": "Japan", "KR": "South Korea",
        "MX": "Mexico", "RU": "Russia", "US": "United States"
    }
    
    @classmethod
    def get_model_config(cls):
        """Return appropriate model configuration"""
        if cls.USE_REMOTE_API:
            return {
                "provider": cls.REMOTE_MODEL_PROVIDER,
                "model": cls.REMOTE_MODEL_NAME,
                "api_key": cls._get_api_key()
            }
        else:
            return {
                "provider": "ollama",
                "model": cls.LLM_MODEL,
                "base_url": cls.OLLAMA_BASE_URL
            }
    
    @classmethod 
    def _get_api_key(cls):
        """Get the appropriate API key based on provider"""
        if cls.REMOTE_MODEL_PROVIDER == "openai":
            return cls.OPENAI_API_KEY
        elif cls.REMOTE_MODEL_PROVIDER == "anthropic":
            return cls.ANTHROPIC_API_KEY
        elif cls.REMOTE_MODEL_PROVIDER == "together":
            return cls.TOGETHER_API_KEY
        return None