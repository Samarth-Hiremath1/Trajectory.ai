# Services package

from .embedding_service import EmbeddingService
from .resume_service import ResumeProcessingService
from .ai_service import AIService, ModelType, AIProvider, get_ai_service, cleanup_ai_service
# Legacy HuggingFace service (deprecated in favor of AIService)
from .huggingface_service import HuggingFaceService, get_huggingface_service, cleanup_huggingface_service

__all__ = [
    'EmbeddingService',
    'ResumeProcessingService', 
    'AIService',
    'ModelType',
    'AIProvider',
    'get_ai_service',
    'cleanup_ai_service',
    # Legacy exports
    'HuggingFaceService',
    'get_huggingface_service',
    'cleanup_huggingface_service'
]