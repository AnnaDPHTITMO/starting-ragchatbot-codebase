import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class Config:
    """Configuration settings for the RAG system"""
    # LLM API settings (supports any LiteLLM-compatible provider)
    # Model format: provider/model-name (e.g., anthropic/claude-sonnet-4-20250514, openai/gpt-4o, ollama/llama3)
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))
    LLM_MODEL: str = os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4-20250514")
    
    # Embedding model settings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Document processing settings
    CHUNK_SIZE: int = 800       # Size of text chunks for vector storage
    CHUNK_OVERLAP: int = 100     # Characters to overlap between chunks
    MAX_RESULTS: int = 5         # Maximum search results to return
    MAX_HISTORY: int = 2         # Number of conversation messages to remember
    
    # Database paths
    CHROMA_PATH: str = "./chroma_db"  # ChromaDB storage location

config = Config()


