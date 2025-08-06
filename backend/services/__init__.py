# Services package

from .ai_service import AIService, ModelType, AIProvider, get_ai_service, cleanup_ai_service

# Optional imports with graceful fallback
try:
    from .embedding_service import EmbeddingService
    EMBEDDING_AVAILABLE = True
except ImportError:
    EmbeddingService = None
    EMBEDDING_AVAILABLE = False

try:
    from .resume_service import ResumeProcessingService
    RESUME_AVAILABLE = True
except ImportError:
    ResumeProcessingService = None
    RESUME_AVAILABLE = False

try:
    from .huggingface_service import HuggingFaceService, get_huggingface_service, cleanup_huggingface_service
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    HuggingFaceService = None
    get_huggingface_service = None
    cleanup_huggingface_service = None
    HUGGINGFACE_AVAILABLE = False

__all__ = [
    'AIService',
    'ModelType',
    'AIProvider',
    'get_ai_service',
    'cleanup_ai_service',
    'EMBEDDING_AVAILABLE',
    'RESUME_AVAILABLE',
    'HUGGINGFACE_AVAILABLE'
]

# Add optional exports if available
if EMBEDDING_AVAILABLE:
    __all__.append('EmbeddingService')
if RESUME_AVAILABLE:
    __all__.append('ResumeProcessingService')
if HUGGINGFACE_AVAILABLE:
    __all__.extend(['HuggingFaceService', 'get_huggingface_service', 'cleanup_huggingface_service'])