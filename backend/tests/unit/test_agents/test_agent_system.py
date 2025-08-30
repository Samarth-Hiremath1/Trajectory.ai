"""
Test script for the multi-agent system foundation
"""
import asyncio
import logging
from datetime import datetime

from models.agent import (
    AgentType, RequestType, RequestPriority, AgentRequest, 
    AgentCapability, MessageType
)
from services.base_agent import BaseAgent
from services.agent_communication_bus import AgentCommunicationBus
from services.agent_orchestrator_service import AgentOrchestratorService
from services.ai_service import AIService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestAgent(BaseAgent):
    """Simple test agent for testing the foundation"""
    
    def _define_capabilities(self):
        """Define test agent capabilities"""
        return [
            AgentCapability(
                name="test_processing",
                description="Process test requests",
                input_types=["test_request"],
                output_types=["test_response"]
            )
        ]
    
    async def process_request(self, request):
        """Process a test request"""
        logger.info(f"Test agent {self.agent_id} processing request: {request.content}")
        
        # Simulate some processing time
        await asyncio.sleep(0.1)
        
        from models.agent import AgentResponse
        
        return AgentResponse(
            request_id=request.id,
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            response_content={
                "message": f"Processed by {self.agent_type.value} agent",
                "request_content": request.content,
                "timestamp": datetime.utcnow().isoformat()
            },
            confidence_score=0.9,
            processing_time=0.1
        )

async def test_communication_bus():
    """Test the agent communication bus"""
    logger.info("Testing Agent Communication Bus...")
    
    # Create AI service (mock for testing)
    ai_service = AIService()
    
    # Create communication bus
    bus = AgentCommunicationBus()
    await bus.start()
    
    # Create test agents
    agent1 = TestAgent("test_agent_1", AgentType.CAREER_STRATEGY, ai_service)
    agent2 = TestAgent("test_agent_2", AgentType.SKILLS_ANALYSIS, ai_service)
    
    # Register agents with bus
    bus.register_agent(agent1.agent_id, agent1)
    bus.register_agent(agent2.agent_id, agent2)
    
    # Test message sending
    from models.agent import AgentMessage
    
    message = AgentMessage(
        sender_agent_id=agent1.agent_id,
        recipient_agent_id=agent2.agent_id,
        message_type=MessageType.CONTEXT_SHARE,
        content={"test": "message"}
    )
    
    success = await bus.send_message(message)
    logger.info(f"Message sent successfully: {success}")
    
    # Wait a bit for message processing
    await asyncio.sleep(0.2)
    
    # Check statistics
    stats = bus.get_statistics()
    logger.info(f"Communication bus stats: {stats}")
    
    await bus.stop()
    logger.info("Communication bus test completed")

async def test_orchestrator():
    """Test the agent orchestrator"""
    logger.info("Testing Agent Orchestrator...")
    
    # Create AI service
    ai_service = AIService()
    
    # Create orchestrator
    orchestrator = AgentOrchestratorService(ai_service)
    await orchestrator.start()
    
    # Create and register test agents
    agent1 = TestAgent("test_agent_1", AgentType.CAREER_STRATEGY, ai_service)
    agent2 = TestAgent("test_agent_2", AgentType.SKILLS_ANALYSIS, ai_service)
    
    orchestrator.register_agent(agent1)
    orchestrator.register_agent(agent2)
    
    # Create test request
    test_request = AgentRequest(
        user_id="test_user",
        request_type=RequestType.CAREER_ADVICE,
        content={"question": "How can I improve my career?"},
        context={"user_background": "Software developer with 3 years experience"},
        priority=RequestPriority.MEDIUM
    )
    
    # Process request
    result = await orchestrator.process_request(test_request)
    logger.info(f"Orchestrator result: {result}")
    
    # Check orchestrator status
    status = orchestrator.get_status()
    logger.info(f"Orchestrator status: {status}")
    
    await orchestrator.stop()
    logger.info("Orchestrator test completed")

async def test_base_agent():
    """Test the base agent functionality"""
    logger.info("Testing Base Agent...")
    
    # Create AI service
    ai_service = AIService()
    
    # Create test agent
    agent = TestAgent("test_agent", AgentType.CAREER_MENTOR, ai_service)
    
    # Test agent status
    status = agent.get_status()
    logger.info(f"Agent status: {status}")
    
    # Create test request
    test_request = AgentRequest(
        user_id="test_user",
        request_type=RequestType.CAREER_ADVICE,
        content={"message": "Test request"},
        priority=RequestPriority.LOW
    )
    
    # Test request handling
    response = await agent.handle_request(test_request)
    logger.info(f"Agent response: {response}")
    
    # Test agent capabilities
    can_handle = agent.can_handle_request(test_request)
    logger.info(f"Agent can handle request: {can_handle}")
    
    logger.info("Base agent test completed")

async def main():
    """Run all tests"""
    logger.info("Starting Multi-Agent System Foundation Tests...")
    
    try:
        await test_base_agent()
        await test_communication_bus()
        await test_orchestrator()
        
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())