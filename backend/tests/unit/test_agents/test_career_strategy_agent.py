"""
Test script for Career Strategy Agent functionality
"""
import asyncio
import logging
import json
from typing import Dict, Any

from services.multi_agent_service import get_multi_agent_service
from models.agent import RequestType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_career_strategy_agent():
    """Test the Career Strategy Agent functionality"""
    try:
        logger.info("Starting Career Strategy Agent tests...")
        
        # Get multi-agent service
        service = await get_multi_agent_service()
        
        # Test 1: Career Transition Analysis
        logger.info("\n=== Test 1: Career Transition Analysis ===")
        transition_result = await service.get_career_strategy_analysis(
            user_id="test_user_123",
            current_role="Software Engineer",
            target_role="Product Manager",
            timeline="18 months"
        )
        
        print("Career Transition Analysis Result:")
        print(json.dumps(transition_result, indent=2, default=str))
        
        # Test 2: Strategic Roadmap Generation
        logger.info("\n=== Test 2: Strategic Roadmap Generation ===")
        roadmap_result = await service.generate_strategic_roadmap(
            user_id="test_user_123",
            current_role="Software Engineer",
            target_role="Product Manager",
            constraints={
                "timeline": "18 months",
                "budget": "moderate",
                "availability": "part-time learning"
            }
        )
        
        print("Strategic Roadmap Result:")
        print(json.dumps(roadmap_result, indent=2, default=str))
        
        # Test 3: Strategic Career Advice
        logger.info("\n=== Test 3: Strategic Career Advice ===")
        advice_result = await service.get_strategic_career_advice(
            user_id="test_user_123",
            question="What are the most important strategic considerations for transitioning from engineering to product management?"
        )
        
        print("Strategic Career Advice Result:")
        print(json.dumps(advice_result, indent=2, default=str))
        
        # Test 4: Service Health Check
        logger.info("\n=== Test 4: Service Health Check ===")
        health_result = await service.health_check()
        
        print("Health Check Result:")
        print(json.dumps(health_result, indent=2, default=str))
        
        # Test 5: Service Status
        logger.info("\n=== Test 5: Service Status ===")
        status_result = service.get_service_status()
        
        print("Service Status:")
        print(json.dumps(status_result, indent=2, default=str))
        
        # Test 6: Available Agents
        logger.info("\n=== Test 6: Available Agents ===")
        agents_result = service.get_available_agents()
        
        print("Available Agents:")
        print(json.dumps(agents_result, indent=2, default=str))
        
        logger.info("\nAll tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        raise
    
    finally:
        # Cleanup
        try:
            await service.stop()
            logger.info("Service stopped successfully")
        except Exception as e:
            logger.error(f"Failed to stop service: {str(e)}")

async def test_direct_agent_functionality():
    """Test Career Strategy Agent directly without orchestrator"""
    try:
        logger.info("\n=== Direct Agent Test ===")
        
        from services.ai_service import get_ai_service
        from services.embedding_service import get_embedding_service
        from services.career_strategy_agent import CareerStrategyAgent
        from models.agent import AgentRequest, RequestType
        
        # Initialize services
        ai_service = await get_ai_service()
        embedding_service = get_embedding_service()
        
        # Create agent
        agent = CareerStrategyAgent(
            agent_id="test_career_strategy_agent",
            ai_service=ai_service,
            embedding_service=embedding_service
        )
        
        # Test agent capabilities
        capabilities = agent.capabilities
        print("Agent Capabilities:")
        for cap in capabilities:
            print(f"- {cap.name}: {cap.description}")
        
        # Test direct request processing
        test_request = AgentRequest(
            user_id="test_user_direct",
            request_type=RequestType.CAREER_TRANSITION,
            content={
                "current_role": "Data Analyst",
                "target_role": "Data Scientist",
                "user_id": "test_user_direct",
                "timeline": "12 months"
            },
            context={}
        )
        
        # Process request
        response = await agent.handle_request(test_request)
        
        print("\nDirect Agent Response:")
        print(json.dumps(response.dict(), indent=2, default=str))
        
        logger.info("Direct agent test completed successfully!")
        
    except Exception as e:
        logger.error(f"Direct agent test failed: {str(e)}")
        raise

async def main():
    """Main test function"""
    try:
        # Test multi-agent service
        await test_career_strategy_agent()
        
        # Test direct agent functionality
        await test_direct_agent_functionality()
        
        print("\n🎉 All Career Strategy Agent tests passed!")
        
    except Exception as e:
        print(f"\n❌ Tests failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())