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
from huggingface_hub import InferenceClient
import time

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Supported Hugging Face model types"""
    MISTRAL_7B = "mistralai/Mistral-7B-v0.1"
    GEMMA_7B = "google/gemma-7b"
    GEMMA_2B = "google/gemma-2b-it"  # Keep this for potential future use

@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    name: str
    max_tokens: int = 1024
    temperature: float = 0.7
    top_p: float = 0.9
    repetition_penalty: float = 1.1
    timeout: int = 30

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

class HuggingFaceService:
    """Service for integrating with Hugging Face Inference API"""
    
    def __init__(
        self,
        api_token: Optional[str] = None,
        requests_per_minute: int = 30,
        max_concurrent_requests: int = 5,
        default_timeout: int = 30
    ):
        """
        Initialize Hugging Face service
        
        Args:
            api_token: HF API token (if None, will use HF_TOKEN env var)
            requests_per_minute: Rate limit for API calls
            max_concurrent_requests: Maximum concurrent requests
            default_timeout: Default timeout for requests in seconds
        """
        self.api_token = api_token or os.getenv("HF_TOKEN")
        if not self.api_token:
            logger.warning("No Hugging Face API token provided. Using free tier with limitations.")
        else:
            logger.info("Hugging Face API token loaded successfully")
        
        # Rate limiting and concurrency control
        self.throttler = Throttler(rate_limit=requests_per_minute, period=60)
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        self.default_timeout = default_timeout
        
        # Model configurations
        self.model_configs = {
            ModelType.MISTRAL_7B: ModelConfig(
                name=ModelType.MISTRAL_7B.value,
                max_tokens=1024,
                temperature=0.7
            ),
            ModelType.GEMMA_7B: ModelConfig(
                name=ModelType.GEMMA_7B.value,
                max_tokens=1024,
                temperature=0.7
            ),
            ModelType.GEMMA_2B: ModelConfig(
                name=ModelType.GEMMA_2B.value,
                max_tokens=512,
                temperature=0.7
            )
        }
        
        # Request queue and metrics
        self.request_queue = asyncio.Queue()
        self.metrics = RequestMetrics()
        self.is_processing_queue = False
        
        # Initialize HTTP session
        self.session = None
        
        logger.info("HuggingFace service initialized")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._init_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self._close_session()
    
    async def _init_session(self):
        """Initialize aiohttp session"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.default_timeout)
            headers = {}
            if self.api_token:
                headers["Authorization"] = f"Bearer {self.api_token}"
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )
            logger.info("HTTP session initialized")
    
    async def _close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("HTTP session closed")
    
    def _get_model_config(self, model_type: ModelType) -> ModelConfig:
        """Get configuration for a specific model"""
        return self.model_configs.get(model_type, self.model_configs[ModelType.MISTRAL_7B])
    
    async def _make_request_with_retry(
        self,
        url: str,
        payload: Dict[str, Any],
        max_retries: int = 3,
        backoff_factor: float = 1.0
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic and exponential backoff
        
        Args:
            url: API endpoint URL
            payload: Request payload
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff multiplier for retries
            
        Returns:
            API response as dictionary
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                
                async with self.session.post(url, json=payload) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        # Update metrics
                        self.metrics.successful_requests += 1
                        self.metrics.total_requests += 1
                        self._update_response_time(response_time)
                        
                        return result
                    
                    elif response.status == 429:  # Rate limited
                        error_msg = f"Rate limited (429) on attempt {attempt + 1}"
                        logger.warning(error_msg)
                        self._update_error_metrics("rate_limit")
                        
                        if attempt < max_retries:
                            wait_time = backoff_factor * (2 ** attempt)
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise Exception(f"Rate limited after {max_retries} retries")
                    
                    elif response.status >= 500:  # Server error
                        error_text = await response.text()
                        error_msg = f"Server error ({response.status}): {error_text}"
                        logger.warning(f"{error_msg} on attempt {attempt + 1}")
                        self._update_error_metrics("server_error")
                        
                        if attempt < max_retries:
                            wait_time = backoff_factor * (2 ** attempt)
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise Exception(error_msg)
                    
                    else:  # Client error (4xx)
                        error_text = await response.text()
                        error_msg = f"Client error ({response.status}): {error_text}"
                        logger.error(error_msg)
                        self._update_error_metrics("client_error")
                        raise Exception(error_msg)
            
            except asyncio.TimeoutError as e:
                error_msg = f"Request timeout on attempt {attempt + 1}"
                logger.warning(error_msg)
                self._update_error_metrics("timeout")
                last_exception = e
                
                if attempt < max_retries:
                    wait_time = backoff_factor * (2 ** attempt)
                    await asyncio.sleep(wait_time)
                    continue
            
            except Exception as e:
                error_msg = f"Request failed on attempt {attempt + 1}: {str(e)}"
                logger.warning(error_msg)
                self._update_error_metrics("other")
                last_exception = e
                
                if attempt < max_retries:
                    wait_time = backoff_factor * (2 ** attempt)
                    await asyncio.sleep(wait_time)
                    continue
        
        # All retries failed
        self.metrics.failed_requests += 1
        self.metrics.total_requests += 1
        raise last_exception or Exception("All retry attempts failed")
    
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
    
    async def generate_text(
        self,
        prompt: str,
        model_type: ModelType = ModelType.MISTRAL_7B,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Generate text using specified Hugging Face model
        
        Args:
            prompt: Input prompt for text generation
            model_type: Model to use for generation
            max_tokens: Maximum tokens to generate (overrides model config)
            temperature: Sampling temperature (overrides model config)
            **kwargs: Additional model parameters
            
        Returns:
            Generated text string
        """
        if not self.session:
            await self._init_session()
        
        config = self._get_model_config(model_type)
        
        # Build request payload
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens or config.max_tokens,
                "temperature": temperature or config.temperature,
                "top_p": config.top_p,
                "repetition_penalty": config.repetition_penalty,
                "return_full_text": False,
                **kwargs
            }
        }
        
        # Apply rate limiting and concurrency control
        async with self.throttler:
            async with self.semaphore:
                url = f"https://api-inference.huggingface.co/models/{config.name}"
                
                try:
                    result = await self._make_request_with_retry(url, payload)
                    
                    # Extract generated text
                    if isinstance(result, list) and len(result) > 0:
                        generated_text = result[0].get("generated_text", "")
                    elif isinstance(result, dict):
                        generated_text = result.get("generated_text", "")
                    else:
                        generated_text = str(result)
                    
                    # Update token metrics (approximate)
                    estimated_tokens = len(generated_text.split())
                    self.metrics.total_tokens += estimated_tokens
                    
                    logger.info(f"Generated {estimated_tokens} tokens using {model_type.value}")
                    return generated_text.strip()
                
                except Exception as e:
                    logger.error(f"Text generation failed: {str(e)}")
                    raise
    
    async def generate_chat_response(
        self,
        messages: List[Dict[str, str]],
        model_type: ModelType = ModelType.MISTRAL_7B,
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
        # Format messages into a single prompt
        formatted_prompt = self._format_chat_prompt(messages, system_prompt, model_type)
        
        return await self.generate_text(
            prompt=formatted_prompt,
            model_type=model_type,
            **kwargs
        )
    
    def _format_chat_prompt(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str],
        model_type: ModelType
    ) -> str:
        """
        Format chat messages into model-specific prompt format
        
        Args:
            messages: List of message dictionaries
            system_prompt: Optional system prompt
            model_type: Model type for format-specific handling
            
        Returns:
            Formatted prompt string
        """
        if model_type == ModelType.MISTRAL_7B:
            # Mistral format: <s>[INST] {prompt} [/INST]
            prompt_parts = []
            
            if system_prompt:
                prompt_parts.append(f"<s>[INST] {system_prompt}")
            
            for i, message in enumerate(messages):
                role = message.get("role", "user")
                content = message.get("content", "")
                
                if role == "user":
                    if i == 0 and not system_prompt:
                        prompt_parts.append(f"<s>[INST] {content} [/INST]")
                    else:
                        prompt_parts.append(f"[INST] {content} [/INST]")
                elif role == "assistant":
                    prompt_parts.append(f" {content}</s>")
            
            return " ".join(prompt_parts)
        
        elif model_type in [ModelType.GEMMA_7B, ModelType.GEMMA_2B]:
            # Gemma format: <start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n
            prompt_parts = []
            
            if system_prompt:
                prompt_parts.append(f"<start_of_turn>system\n{system_prompt}<end_of_turn>")
            
            for message in messages:
                role = message.get("role", "user")
                content = message.get("content", "")
                
                if role == "user":
                    prompt_parts.append(f"<start_of_turn>user\n{content}<end_of_turn>")
                elif role == "assistant":
                    prompt_parts.append(f"<start_of_turn>model\n{content}<end_of_turn>")
            
            # Add model turn start for generation
            prompt_parts.append("<start_of_turn>model\n")
            
            return "\n".join(prompt_parts)
        
        else:
            # Generic format - simple concatenation
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
        model_type: ModelType = ModelType.MISTRAL_7B
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
        model_type: ModelType = ModelType.MISTRAL_7B
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
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Hugging Face service
        
        Returns:
            Health status dictionary
        """
        try:
            if not self.session:
                await self._init_session()
            
            # Test with a simple generation
            test_prompt = "Hello, this is a test."
            result = await self.generate_text(
                prompt=test_prompt,
                model_type=ModelType.MISTRAL_7B,
                max_tokens=10
            )
            
            return {
                "status": "healthy",
                "api_accessible": True,
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
                    "error_counts": self.metrics.error_counts
                },
                "available_models": [model.value for model in ModelType],
                "rate_limit": "30 requests/minute",
                "max_concurrent": 5
            }
        
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "api_accessible": False,
                "metrics": {
                    "total_requests": self.metrics.total_requests,
                    "successful_requests": self.metrics.successful_requests,
                    "failed_requests": self.metrics.failed_requests,
                    "error_counts": self.metrics.error_counts
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
            "last_request_time": self.metrics.last_request_time.isoformat() if self.metrics.last_request_time else None
        }
    
    def reset_metrics(self):
        """Reset all metrics to zero"""
        self.metrics = RequestMetrics()
        logger.info("Service metrics reset")

# Singleton instance for global use
_hf_service_instance = None

async def get_huggingface_service() -> HuggingFaceService:
    """Get or create singleton HuggingFace service instance"""
    global _hf_service_instance
    
    if _hf_service_instance is None:
        _hf_service_instance = HuggingFaceService()
        await _hf_service_instance._init_session()
    
    return _hf_service_instance

async def cleanup_huggingface_service():
    """Cleanup singleton service instance"""
    global _hf_service_instance
    
    if _hf_service_instance:
        await _hf_service_instance._close_session()
        _hf_service_instance = None