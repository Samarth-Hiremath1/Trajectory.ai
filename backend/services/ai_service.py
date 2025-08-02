import os
import logging
import asyncio
import json
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
from asyncio_throttle import Throttler
import google.generativeai as genai
import time

logger = logging.getLogger(__name__)

class AIProvider(Enum):
    """Supported AI providers"""
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    HUGGINGFACE = "huggingface"

class ModelType(Enum):
    """Supported model types across providers"""
    # Gemini models
    GEMINI_FLASH = "gemini-1.5-flash"
    GEMINI_PRO = "gemini-1.5-pro"
    
    # OpenRouter free models
    MISTRAL_7B = "mistralai/mistral-7b-instruct:free"
    GEMMA_7B = "google/gemma-7b-it:free"
    LLAMA_3_8B = "meta-llama/llama-3-8b-instruct:free"
    PHI_3_MINI = "microsoft/phi-3-mini-128k-instruct:free"

@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    name: str
    provider: AIProvider
    max_tokens: int = 1024
    temperature: float = 0.7
    timeout: int = 30
    free_tier: bool = True

@dataclass
class RequestMetrics:
    """Metrics for tracking API requests"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    average_response_time: float = 0.0
    last_request_time: Optional[datetime] = None
    error_counts: Dict[str, int] = field(default_factory=dict)
    provider_usage: Dict[str, int] = field(default_factory=dict)

class AIService:
    """Unified AI service with Gemini primary and OpenRouter fallback"""
    
    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        openrouter_api_key: Optional[str] = None,
        requests_per_minute: int = 30,
        max_concurrent_requests: int = 5,
        default_timeout: int = 30
    ):
        """
        Initialize AI service with multiple providers
        
        Args:
            gemini_api_key: Google Gemini API key
            openrouter_api_key: OpenRouter API key
            requests_per_minute: Rate limit for API calls
            max_concurrent_requests: Maximum concurrent requests
            default_timeout: Default timeout for requests in seconds
        """
        # API keys
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.openrouter_api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        
        # Rate limiting and concurrency control
        self.throttler = Throttler(rate_limit=requests_per_minute, period=60)
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        self.default_timeout = default_timeout
        
        # Model configurations
        self.model_configs = {
            ModelType.GEMINI_FLASH: ModelConfig(
                name=ModelType.GEMINI_FLASH.value,
                provider=AIProvider.GEMINI,
                max_tokens=1024,
                temperature=0.7
            ),
            ModelType.GEMINI_PRO: ModelConfig(
                name=ModelType.GEMINI_PRO.value,
                provider=AIProvider.GEMINI,
                max_tokens=1024,
                temperature=0.7
            ),
            ModelType.MISTRAL_7B: ModelConfig(
                name=ModelType.MISTRAL_7B.value,
                provider=AIProvider.OPENROUTER,
                max_tokens=1024,
                temperature=0.7
            ),
            ModelType.GEMMA_7B: ModelConfig(
                name=ModelType.GEMMA_7B.value,
                provider=AIProvider.OPENROUTER,
                max_tokens=1024,
                temperature=0.7
            ),
            ModelType.LLAMA_3_8B: ModelConfig(
                name=ModelType.LLAMA_3_8B.value,
                provider=AIProvider.OPENROUTER,
                max_tokens=1024,
                temperature=0.7
            )
        }
        
        # Initialize providers
        self._init_gemini()
        self.session = None
        
        # Metrics
        self.metrics = RequestMetrics()
        
        logger.info("AI service initialized with Gemini + OpenRouter")
    
    def _init_gemini(self):
        """Initialize Gemini client"""
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            logger.info("Gemini API configured successfully")
        else:
            logger.warning("No Gemini API key provided")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._init_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self._close_session()
    
    async def _init_session(self):
        """Initialize aiohttp session for OpenRouter"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.default_timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
            logger.info("HTTP session initialized")
    
    async def _close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("HTTP session closed")
    
    def _get_model_config(self, model_type: ModelType) -> ModelConfig:
        """Get configuration for a specific model"""
        return self.model_configs.get(model_type, self.model_configs[ModelType.GEMINI_FLASH])
    
    async def _generate_with_gemini(
        self,
        prompt: str,
        model_type: ModelType = ModelType.GEMINI_FLASH,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """Generate text using Gemini API"""
        if not self.gemini_api_key:
            raise Exception("Gemini API key not configured")
        
        config = self._get_model_config(model_type)
        
        try:
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens or config.max_tokens,
                temperature=temperature or config.temperature,
            )
            
            # Initialize model
            model = genai.GenerativeModel(config.name)
            
            # Generate response
            start_time = time.time()
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            response_time = time.time() - start_time
            
            # Update metrics
            self.metrics.successful_requests += 1
            self.metrics.total_requests += 1
            self.metrics.provider_usage[AIProvider.GEMINI.value] = self.metrics.provider_usage.get(AIProvider.GEMINI.value, 0) + 1
            self._update_response_time(response_time)
            
            # Extract text
            generated_text = response.text
            
            # Update token metrics (approximate)
            estimated_tokens = len(generated_text.split())
            self.metrics.total_tokens += estimated_tokens
            
            logger.info(f"Generated {estimated_tokens} tokens using Gemini {model_type.value}")
            return generated_text.strip()
            
        except Exception as e:
            logger.error(f"Gemini generation failed: {str(e)}")
            self._update_error_metrics("gemini_error")
            raise
    
    async def _generate_with_openrouter(
        self,
        prompt: str,
        model_type: ModelType = ModelType.MISTRAL_7B,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """Generate text using OpenRouter API"""
        if not self.openrouter_api_key:
            raise Exception("OpenRouter API key not configured")
        
        if not self.session:
            await self._init_session()
        
        config = self._get_model_config(model_type)
        
        # Build request payload
        payload = {
            "model": config.name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens or config.max_tokens,
            "temperature": temperature or config.temperature,
        }
        
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",  # Required by OpenRouter
            "X-Title": "Trajectory AI"  # Optional but recommended
        }
        
        try:
            start_time = time.time()
            
            async with self.session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    result = await response.json()
                    
                    # Update metrics
                    self.metrics.successful_requests += 1
                    self.metrics.total_requests += 1
                    self.metrics.provider_usage[AIProvider.OPENROUTER.value] = self.metrics.provider_usage.get(AIProvider.OPENROUTER.value, 0) + 1
                    self._update_response_time(response_time)
                    
                    # Extract generated text
                    generated_text = result["choices"][0]["message"]["content"]
                    
                    # Update token metrics
                    usage = result.get("usage", {})
                    completion_tokens = usage.get("completion_tokens", len(generated_text.split()))
                    self.metrics.total_tokens += completion_tokens
                    
                    logger.info(f"Generated {completion_tokens} tokens using OpenRouter {model_type.value}")
                    return generated_text.strip()
                
                else:
                    error_text = await response.text()
                    error_msg = f"OpenRouter error ({response.status}): {error_text}"
                    logger.error(error_msg)
                    self._update_error_metrics("openrouter_error")
                    raise Exception(error_msg)
                    
        except Exception as e:
            logger.error(f"OpenRouter generation failed: {str(e)}")
            self._update_error_metrics("openrouter_error")
            raise
    
    async def generate_text(
        self,
        prompt: str,
        model_type: Optional[ModelType] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        prefer_provider: Optional[AIProvider] = None,
        **kwargs
    ) -> str:
        """
        Generate text with intelligent provider routing
        
        Args:
            prompt: Input prompt for text generation
            model_type: Specific model to use (optional)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            prefer_provider: Preferred provider (optional)
            **kwargs: Additional parameters
            
        Returns:
            Generated text string
        """
        # Apply rate limiting and concurrency control
        async with self.throttler:
            async with self.semaphore:
                
                # Determine provider and model
                if model_type is None:
                    # Default to Gemini Flash (fastest, most reliable)
                    model_type = ModelType.GEMINI_FLASH
                
                config = self._get_model_config(model_type)
                target_provider = prefer_provider or config.provider
                
                # Try primary provider first
                try:
                    if target_provider == AIProvider.GEMINI:
                        return await self._generate_with_gemini(
                            prompt, model_type, max_tokens, temperature, **kwargs
                        )
                    elif target_provider == AIProvider.OPENROUTER:
                        return await self._generate_with_openrouter(
                            prompt, model_type, max_tokens, temperature, **kwargs
                        )
                        
                except Exception as primary_error:
                    logger.warning(f"Primary provider {target_provider.value} failed: {primary_error}")
                    
                    # Try fallback provider
                    try:
                        if target_provider == AIProvider.GEMINI and self.openrouter_api_key:
                            logger.info("Falling back to OpenRouter")
                            fallback_model = ModelType.MISTRAL_7B  # Default OpenRouter model
                            return await self._generate_with_openrouter(
                                prompt, fallback_model, max_tokens, temperature, **kwargs
                            )
                        elif target_provider == AIProvider.OPENROUTER and self.gemini_api_key:
                            logger.info("Falling back to Gemini")
                            fallback_model = ModelType.GEMINI_FLASH  # Default Gemini model
                            return await self._generate_with_gemini(
                                prompt, fallback_model, max_tokens, temperature, **kwargs
                            )
                    except Exception as fallback_error:
                        logger.error(f"Fallback provider also failed: {fallback_error}")
                    
                    # If both providers fail, raise the original error
                    self.metrics.failed_requests += 1
                    self.metrics.total_requests += 1
                    raise primary_error
    
    async def generate_chat_response(
        self,
        messages: List[Dict[str, str]],
        model_type: Optional[ModelType] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate chat response using conversation format
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            model_type: Model to use for generation
            system_prompt: Optional system prompt to prepend
            **kwargs: Additional generation parameters
            
        Returns:
            Generated response string
        """
        # Format messages into a single prompt for text generation
        formatted_prompt = self._format_chat_prompt(messages, system_prompt)
        
        return await self.generate_text(
            prompt=formatted_prompt,
            model_type=model_type,
            **kwargs
        )
    
    def _format_chat_prompt(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Format chat messages into a single prompt
        
        Args:
            messages: List of message dictionaries
            system_prompt: Optional system prompt
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        
        if system_prompt:
            prompt_parts.append(f"System: {system_prompt}")
        
        for message in messages:
            role = message.get("role", "user").title()
            content = message.get("content", "")
            prompt_parts.append(f"{role}: {content}")
        
        prompt_parts.append("Assistant:")
        
        return "\n".join(prompt_parts)
    
    async def generate_roadmap_content(
        self,
        current_role: str,
        target_role: str,
        user_background: str,
        model_type: Optional[ModelType] = None
    ) -> str:
        """
        Generate career roadmap content using AI
        
        Args:
            current_role: User's current role
            target_role: User's target role
            user_background: User's background information
            model_type: Model to use for generation
            
        Returns:
            Generated roadmap content
        """
        system_prompt = """You are a career advisor AI that creates detailed, actionable career roadmaps. 
        Create a structured roadmap with specific phases, skills to develop, certifications to pursue, 
        projects to build, and realistic timelines. Focus on practical, achievable steps."""
        
        user_prompt = f"""Create a detailed career roadmap for transitioning from {current_role} to {target_role}.

User Background:
{user_background}

Please provide:
1. Assessment of current skills vs. target role requirements
2. Phase-by-phase development plan (3-6 phases)
3. Specific skills to develop in each phase
4. Recommended certifications and courses
5. Portfolio projects to build
6. Realistic timeline estimates
7. Key milestones and success metrics

Format the response as a structured roadmap with clear sections and actionable items."""
        
        messages = [{"role": "user", "content": user_prompt}]
        
        return await self.generate_chat_response(
            messages=messages,
            model_type=model_type,
            system_prompt=system_prompt,
            max_tokens=1500,
            temperature=0.7
        )
    
    async def generate_career_advice(
        self,
        question: str,
        user_context: str,
        model_type: Optional[ModelType] = None
    ) -> str:
        """
        Generate personalized career advice based on user question and context
        
        Args:
            question: User's career question
            user_context: User's background and context
            model_type: Model to use for generation
            
        Returns:
            Generated career advice
        """
        system_prompt = """You are an experienced career mentor providing personalized advice. 
        Use the user's background to give specific, actionable guidance. Be encouraging but realistic."""
        
        user_prompt = f"""User Context:
{user_context}

Question: {question}

Please provide specific, actionable advice based on the user's background and current situation."""
        
        messages = [{"role": "user", "content": user_prompt}]
        
        return await self.generate_chat_response(
            messages=messages,
            model_type=model_type,
            system_prompt=system_prompt,
            max_tokens=800,
            temperature=0.8
        )
    
    def _update_response_time(self, response_time: float):
        """Update average response time metric"""
        if self.metrics.successful_requests <= 1:
            self.metrics.average_response_time = response_time
        else:
            # Calculate running average
            total_time = self.metrics.average_response_time * (self.metrics.successful_requests - 1)
            self.metrics.average_response_time = (total_time + response_time) / self.metrics.successful_requests
    
    def _update_error_metrics(self, error_type: str):
        """Update error count metrics"""
        self.metrics.error_counts[error_type] = self.metrics.error_counts.get(error_type, 0) + 1
        self.metrics.last_request_time = datetime.utcnow()
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the AI service
        
        Returns:
            Health status dictionary
        """
        try:
            # Test with a simple generation using default model
            test_prompt = "Hello, this is a test."
            result = await self.generate_text(
                prompt=test_prompt,
                max_tokens=10
            )
            
            return {
                "status": "healthy",
                "providers_available": {
                    "gemini": bool(self.gemini_api_key),
                    "openrouter": bool(self.openrouter_api_key)
                },
                "test_generation_successful": bool(result),
                "metrics": {
                    "total_requests": self.metrics.total_requests,
                    "successful_requests": self.metrics.successful_requests,
                    "failed_requests": self.metrics.failed_requests,
                    "success_rate": (
                        self.metrics.successful_requests / max(self.metrics.total_requests, 1)
                    ) * 100,
                    "average_response_time": self.metrics.average_response_time,
                    "total_tokens": self.metrics.total_tokens,
                    "error_counts": self.metrics.error_counts,
                    "provider_usage": self.metrics.provider_usage
                },
                "available_models": [model.value for model in ModelType],
                "primary_provider": "gemini" if self.gemini_api_key else "openrouter",
                "fallback_available": bool(self.gemini_api_key and self.openrouter_api_key)
            }
        
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "providers_available": {
                    "gemini": bool(self.gemini_api_key),
                    "openrouter": bool(self.openrouter_api_key)
                },
                "metrics": {
                    "total_requests": self.metrics.total_requests,
                    "successful_requests": self.metrics.successful_requests,
                    "failed_requests": self.metrics.failed_requests,
                    "error_counts": self.metrics.error_counts,
                    "provider_usage": self.metrics.provider_usage
                }
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current service metrics"""
        return {
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "success_rate": (
                self.metrics.successful_requests / max(self.metrics.total_requests, 1)
            ) * 100,
            "average_response_time": self.metrics.average_response_time,
            "total_tokens": self.metrics.total_tokens,
            "error_counts": self.metrics.error_counts,
            "provider_usage": self.metrics.provider_usage,
            "last_request_time": self.metrics.last_request_time.isoformat() if self.metrics.last_request_time else None
        }
    
    def reset_metrics(self):
        """Reset all metrics to zero"""
        self.metrics = RequestMetrics()
        logger.info("Service metrics reset")
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """Get available models by provider"""
        models_by_provider = {}
        
        for model_type, config in self.model_configs.items():
            provider = config.provider.value
            if provider not in models_by_provider:
                models_by_provider[provider] = []
            models_by_provider[provider].append(model_type.value)
        
        return models_by_provider

# Singleton instance for global use
_ai_service_instance = None

async def get_ai_service() -> AIService:
    """Get or create singleton AI service instance"""
    global _ai_service_instance
    
    if _ai_service_instance is None:
        _ai_service_instance = AIService()
        await _ai_service_instance._init_session()
    
    return _ai_service_instance

async def cleanup_ai_service():
    """Cleanup singleton service instance"""
    global _ai_service_instance
    
    if _ai_service_instance:
        await _ai_service_instance._close_session()
        _ai_service_instance = None