"""
Centralized initialization system for all external services and configurations.
This module handles the setup and initialization of all third-party services,
AI models, and other resources that need to be configured once at startup.
"""
import os
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from supabase import create_client, Client
from app.config.config import load_config, set_env
from app.config.logging import get_logger

# Initialize logger for this module
logger = get_logger(__name__)


class ServiceManager:
    """
    Singleton class to manage all service initializations.
    Ensures services are initialized only once and provides easy access.
    """
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._genai_model = None
            self._supabase_client = None
            self._embedding_model = None
            self._magic_available = None
            self._initialize_all()
            ServiceManager._initialized = True
    
    def _initialize_all(self):
        """Initialize all services in the correct order."""
        logger.info("Starting service initialization...")
        
        # Load configuration first
        self._load_configuration()
        
        # Initialize services
        self._initialize_genai()
        self._initialize_supabase()
        self._initialize_embedding_model()
        self._check_magic_availability()
        
        logger.info("All services initialized successfully!")
    
    def _load_configuration(self):
        """Load and set environment configuration."""
        try:
            config = load_config()
            set_env(config)
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _initialize_genai(self):
        """Initialize Google Generative AI model."""
        try:
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
            
            genai.configure(api_key=api_key)
            model = os.getenv("GENAI_MODEL", "gemini-2.0-flash")
            logger.info(f"Using GenAI model: {model}")
            # Initialize the GenAI model with the specified model name
            self._genai_model = genai.GenerativeModel(model)
            logger.info(f"Initialized GenAI model: {self._genai_model._model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize GenAI: {e}")
            raise
    
    def _initialize_supabase(self):
        """Initialize Supabase client."""
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            
            if not supabase_url or not supabase_key:
                raise ValueError("Supabase credentials not found in environment variables")
            
            self._supabase_client = create_client(supabase_url, supabase_key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase: {e}")
            raise
    
    def _initialize_embedding_model(self):
        """Initialize Gemini embedding model using LangChain."""
        try:
            # Use LangChain's GoogleGenerativeAIEmbeddings for proper integration
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
            
            self._embedding_model = GoogleGenerativeAIEmbeddings(
                model="models/gemini-embedding-exp-03-07",
                google_api_key=api_key
            )
            logger.info("Gemini embedding model initialized: models/gemini-embedding-exp-03-07")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise
    
    def _check_magic_availability(self):
        """Check if python-magic is available."""
        try:
            import magic
            self._magic_available = True
            logger.info("python-magic is available")
        except ImportError:
            self._magic_available = False
            logger.warning("python-magic not available, using mimetypes fallback for file detection")
    
    # Property methods to access initialized services
    @property
    def genai_model(self):
        """Get the initialized GenAI model."""
        if self._genai_model is None:
            raise RuntimeError("GenAI model not initialized")
        return self._genai_model
    
    @property
    def supabase_client(self) -> Client:
        """Get the initialized Supabase client."""
        if self._supabase_client is None:
            raise RuntimeError("Supabase client not initialized")
        return self._supabase_client
    
    @property
    def embedding_model(self):
        """Get the initialized Gemini embedding model instance."""
        if self._embedding_model is None:
            raise RuntimeError("Embedding model not initialized")
        return self._embedding_model
    
    @property
    def magic_available(self) -> bool:
        """Check if python-magic is available."""
        return self._magic_available
    
    def get_file_mime_type(self, file_path: str) -> str:
        """
        Get MIME type of a file using python-magic if available, 
        otherwise fall back to mimetypes module.
        """
        if self._magic_available:
            try:
                import magic
                mime = magic.Magic(mime=True)
                return mime.from_file(file_path)
            except Exception as e:
                logger.warning(f"Magic MIME detection failed: {e}, falling back to mimetypes")
        
        # Fallback to mimetypes
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"
    
    def generate_embeddings(self, text: str) -> list:
        """
        Generate embeddings using Gemini's embedding model via LangChain.
        
        Args:
            text (str): Text to generate embeddings for
            
        Returns:
            list: Embedding vector
        """
        try:
            if self._embedding_model is None:
                raise RuntimeError("Embedding model not initialized")
            
            # Use LangChain's embed_query method
            embedding_vector = self._embedding_model.embed_query(text)
            return embedding_vector
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise


# Global service manager instance
service_manager = ServiceManager()

# Convenience functions for easy access
def get_genai_model():
    """Get the initialized GenAI model."""
    return service_manager.genai_model

def get_supabase_client() -> Client:
    """Get the initialized Supabase client."""
    return service_manager.supabase_client

def get_embedding_model():
    """Get the initialized Gemini embedding model instance."""
    return service_manager.embedding_model

def get_file_mime_type(file_path: str) -> str:
    """Get MIME type of a file."""
    return service_manager.get_file_mime_type(file_path)

def is_magic_available() -> bool:
    """Check if python-magic is available."""
    return service_manager.magic_available

def generate_embeddings(text: str) -> list:
    """Generate embeddings using Gemini's embedding model."""
    return service_manager.generate_embeddings(text)
