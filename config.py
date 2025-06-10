import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Ollama settings
    OLLAMA_BASE_URL = "http://localhost:11434"
    LLM_MODEL = "llama2:7b"  # or "mistral:7b", "codellama:7b"
    
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