"""
Base Agent class with common functionality for all specialized agents
"""
import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from models.agent import (
    AgentType, AgentRequest, AgentResponse, AgentCapability, 
    AgentStatus, RequestStatus, MessageType, AgentMessage
)
from services.ai_service import AIService, ModelType
from services.agent_logger import agent_logger, ActivityType, LogLevel

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Abstract base class for all specialized agents in the system.
    Provides common functionality like communication, status tracking, and AI integration.
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: AgentType,
        ai_service: AIService,
        max_concurrent_requests: int = 3,
        default_confidence_threshold: float = 0.7
    ):
        """
        Initialize base agent
        
        Args:
            agent_id: Unique identifier for this agent instance
            agent_type: Type of agent (from AgentType enum)
            ai_service: AI service instance for LLM interactions
            max_concurrent_requests: Maximum concurrent requests this agent can handle
            default_confidence_threshold: Default confidence threshold for responses
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.ai_service = ai_service
        self.max_concurrent_requests = max_concurrent_requests
        self.default_confidence_threshold = default_confidence_threshold
        
        # Status tracking
        self.is_active = True
        self.current_load = 0
        self.last_heartbeat = datetime.utcnow()
        
        # Performance metrics
        self.performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_processing_time": 0.0,
            "average_confidence": 0.0,
            "last_request_time": None
        }
        
        # Communication
        self.message_handlers = {}
        self.communication_bus = None  # Will be set by orchestrator
        
        # Capabilities (to be defined by subclasses)
        self.capabilities = self._define_capabilities()
        
        logger.info(f"Initialized {self.agent_type.value} agent with ID {self.agent_id}")
    
    @abstractmethod
    def _define_capabilities(self) -> List[AgentCapability]:
        """
        Define the capabilities of this agent.
        Must be implemented by subclasses.
        
        Returns:
            List of AgentCapability objects
        """
        pass
    
    @abstractmethod
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """
        Process a request and return a response.
        Must be implemented by subclasses.
        
        Args:
            request: The request to process
            
        Returns:
            AgentResponse with the processing results
        """
        pass
    
    async def handle_request(self, request: AgentRequest) -> AgentResponse:
        """
        Main entry point for handling requests with error handling and metrics tracking
        
        Args:
            request: The request to handle
            
        Returns:
            AgentResponse with processing results
        """
        start_time = time.time()
        
        try:
            # Check if agent can handle more requests
            if self.current_load >= self.max_concurrent_requests:
                raise Exception(f"Agent {self.agent_id} is at maximum capacity")
            
            # Increment load
            self.current_load += 1
            self.performance_metrics["total_requests"] += 1
            
            # Update heartbeat
            self.last_heartbeat = datetime.utcnow()
            
            # Log request received
            agent_logger.log_request_received(
                agent_id=self.agent_id,
                agent_type=self.agent_type.value,
                request_id=request.id,
                request_type=request.request_type.value,
                user_id=request.user_id
            )
            
            # Process the request
            logger.info(f"Agent {self.agent_id} processing request {request.id}")
            response = await self.process_request(request)
            
            # Update success metrics
            processing_time = time.time() - start_time
            response.processing_time = processing_time
            
            self.performance_metrics["successful_requests"] += 1
            self._update_average_processing_time(processing_time)
            self._update_average_confidence(response.confidence_score)
            self.performance_metrics["last_request_time"] = datetime.utcnow().isoformat()
            
            # Log successful processing
            agent_logger.log_request_processed(
                agent_id=self.agent_id,
                agent_type=self.agent_type.value,
                request_id=request.id,
                processing_time=processing_time,
                confidence_score=response.confidence_score,
                success=True,
                user_id=request.user_id
            )
            
            logger.info(f"Agent {self.agent_id} completed request {request.id} in {processing_time:.2f}s")
            return response
            
        except Exception as e:
            # Handle errors
            processing_time = time.time() - start_time
            self.performance_metrics["failed_requests"] += 1
            
            # Log error
            agent_logger.log_error(
                agent_id=self.agent_id,
                agent_type=self.agent_type.value,
                error_message=str(e),
                error_type=type(e).__name__,
                request_id=request.id,
                user_id=request.user_id
            )
            
            logger.error(f"Agent {self.agent_id} failed to process request {request.id}: {str(e)}")
            
            # Return error response
            return AgentResponse(
                request_id=request.id,
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                response_content={"error": str(e)},
                confidence_score=0.0,
                processing_time=processing_time,
                metadata={"error": True, "error_type": type(e).__name__}
            )
        
        finally:
            # Decrement load
            self.current_load = max(0, self.current_load - 1)
    
    async def send_message(self, recipient_id: str, message_type: MessageType, content: Dict[str, Any]) -> bool:
        """
        Send a message to another agent
        
        Args:
            recipient_id: ID of the recipient agent
            message_type: Type of message
            content: Message content
            
        Returns:
            True if message was sent successfully
        """
        if not self.communication_bus:
            logger.warning(f"Agent {self.agent_id} has no communication bus configured")
            return False
        
        message = AgentMessage(
            sender_agent_id=self.agent_id,
            recipient_agent_id=recipient_id,
            message_type=message_type,
            content=content
        )
        
        return await self.communication_bus.send_message(message)
    
    async def broadcast_message(self, message_type: MessageType, content: Dict[str, Any]) -> bool:
        """
        Broadcast a message to all agents
        
        Args:
            message_type: Type of message
            content: Message content
            
        Returns:
            True if message was broadcast successfully
        """
        if not self.communication_bus:
            logger.warning(f"Agent {self.agent_id} has no communication bus configured")
            return False
        
        return await self.communication_bus.broadcast_message(self.agent_id, message_type, content)
    
    async def receive_message(self, message: AgentMessage) -> bool:
        """
        Receive and handle a message from another agent
        
        Args:
            message: The received message
            
        Returns:
            True if message was handled successfully
        """
        try:
            # Get handler for message type
            handler = self.message_handlers.get(message.message_type)
            
            if handler:
                await handler(message)
                return True
            else:
                logger.warning(f"Agent {self.agent_id} has no handler for message type {message.message_type}")
                return False
                
        except Exception as e:
            logger.error(f"Agent {self.agent_id} failed to handle message: {str(e)}")
            return False
    
    def register_message_handler(self, message_type: MessageType, handler):
        """
        Register a handler for a specific message type
        
        Args:
            message_type: Type of message to handle
            handler: Async function to handle the message
        """
        self.message_handlers[message_type] = handler
        logger.info(f"Agent {self.agent_id} registered handler for {message_type}")
    
    def set_communication_bus(self, communication_bus):
        """
        Set the communication bus for inter-agent messaging
        
        Args:
            communication_bus: The communication bus instance
        """
        self.communication_bus = communication_bus
        logger.info(f"Agent {self.agent_id} connected to communication bus")
    
    def get_status(self) -> AgentStatus:
        """
        Get current agent status
        
        Returns:
            AgentStatus object with current status information
        """
        return AgentStatus(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            is_active=self.is_active,
            current_load=self.current_load,
            max_concurrent_requests=self.max_concurrent_requests,
            capabilities=self.capabilities,
            last_heartbeat=self.last_heartbeat,
            performance_metrics=self.performance_metrics
        )
    
    def can_handle_request(self, request: AgentRequest) -> bool:
        """
        Check if this agent can handle a specific request
        
        Args:
            request: The request to check
            
        Returns:
            True if agent can handle the request
        """
        # Check load capacity
        if self.current_load >= self.max_concurrent_requests:
            return False
        
        # Check if agent is active
        if not self.is_active:
            return False
        
        # Check capabilities (to be implemented by subclasses if needed)
        return True
    
    async def generate_ai_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model_type: Optional[ModelType] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate AI response using the configured AI service
        
        Args:
            prompt: The prompt to send to the AI
            system_prompt: Optional system prompt
            model_type: Model to use for generation
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated response text
        """
        if system_prompt:
            messages = [{"role": "user", "content": prompt}]
            return await self.ai_service.generate_chat_response(
                messages=messages,
                system_prompt=system_prompt,
                model_type=model_type,
                max_tokens=max_tokens,
                temperature=temperature
            )
        else:
            return await self.ai_service.generate_text(
                prompt=prompt,
                model_type=model_type,
                max_tokens=max_tokens,
                temperature=temperature
            )
    
    def _update_average_processing_time(self, processing_time: float):
        """Update average processing time metric"""
        successful_requests = self.performance_metrics["successful_requests"]
        if successful_requests <= 1:
            self.performance_metrics["average_processing_time"] = processing_time
        else:
            current_avg = self.performance_metrics["average_processing_time"]
            total_time = current_avg * (successful_requests - 1)
            self.performance_metrics["average_processing_time"] = (total_time + processing_time) / successful_requests
    
    def _update_average_confidence(self, confidence: float):
        """Update average confidence metric"""
        successful_requests = self.performance_metrics["successful_requests"]
        if successful_requests <= 1:
            self.performance_metrics["average_confidence"] = confidence
        else:
            current_avg = self.performance_metrics["average_confidence"]
            total_confidence = current_avg * (successful_requests - 1)
            self.performance_metrics["average_confidence"] = (total_confidence + confidence) / successful_requests
    
    async def shutdown(self):
        """
        Gracefully shutdown the agent
        """
        self.is_active = False
        
        # Wait for current requests to complete
        while self.current_load > 0:
            await asyncio.sleep(0.1)
        
        logger.info(f"Agent {self.agent_id} shutdown complete")
    
    def __str__(self) -> str:
        return f"{self.agent_type.value}Agent({self.agent_id})"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id='{self.agent_id}', type='{self.agent_type.value}', active={self.is_active})"