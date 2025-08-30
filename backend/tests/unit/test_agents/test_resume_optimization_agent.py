#!/usr/bin/env python3
"""
Test script for Resume Optimization Agent
"""
import asyncio
import logging
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.resume_optimization_agent import ResumeOptimizationAgent
from services.ai_service import AIService
from services.embedding_service import EmbeddingService
from models.agent import AgentRequest, RequestType, RequestPriority

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_resume_optimization_agent():
    """Test the Resume Optimization Agent functionality"""
    try:
        logger.info("Starting Resume Optimization Agent test...")
        
        # Initialize services
        ai_service = AIService()
        embedding_service = EmbeddingService()
        
        # Initialize Resume Optimization Agent
        agent = ResumeOptimizationAgent(
            agent_id="test_resume_agent",
            ai_service=ai_service,
            embedding_service=embedding_service
        )
        
        logger.info(f"Initialized Resume Optimization Agent: {agent.agent_id}")
        
        # Test agent capabilities
        capabilities = agent.capabilities
        logger.info(f"Agent capabilities: {[cap.name for cap in capabilities]}")
        
        # Test resume review request
        test_request = AgentRequest(
            user_id="test_user_123",
            request_type=RequestType.RESUME_REVIEW,
            content={
                "user_id": "test_user_123",
                "target_role": "Software Engineer",
                "job_descriptions": [
                    "Looking for a Software Engineer with Python, SQL, and AWS experience"
                ]
            },
            context={
                "user_background": "Software developer with 3 years experience"
            },
            priority=RequestPriority.MEDIUM
        )
        
        logger.info("Processing resume review request...")
        response = await agent.handle_request(test_request)
        
        logger.info(f"Response received with confidence: {response.confidence_score}")
        logger.info(f"Response content keys: {list(response.response_content.keys())}")
        
        # Test career transition optimization
        transition_request = AgentRequest(
            user_id="test_user_123",
            request_type=RequestType.CAREER_TRANSITION,
            content={
                "user_id": "test_user_123",
                "current_role": "Data Analyst",
                "target_role": "Product Manager"
            },
            context={
                "user_background": "Data analyst looking to transition to product management"
            },
            priority=RequestPriority.HIGH
        )
        
        logger.info("Processing career transition request...")
        transition_response = await agent.handle_request(transition_request)
        
        logger.info(f"Transition response confidence: {transition_response.confidence_score}")
        logger.info(f"Transition response keys: {list(transition_response.response_content.keys())}")
        
        # Test general resume advice
        advice_request = AgentRequest(
            user_id="test_user_123",
            request_type=RequestType.CAREER_ADVICE,
            content={
                "question": "How can I make my resume more ATS-friendly?",
                "user_id": "test_user_123"
            },
            context={},
            priority=RequestPriority.LOW
        )
        
        logger.info("Processing resume advice request...")
        advice_response = await agent.handle_request(advice_request)
        
        logger.info(f"Advice response confidence: {advice_response.confidence_score}")
        logger.info(f"Advice response keys: {list(advice_response.response_content.keys())}")
        
        # Test agent status
        status = agent.get_status()
        logger.info(f"Agent status: Active={status.is_active}, Load={status.current_load}")
        logger.info(f"Performance metrics: {status.performance_metrics}")
        
        logger.info("Resume Optimization Agent test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Resume Optimization Agent test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_agent_capabilities():
    """Test specific agent capabilities"""
    try:
        logger.info("Testing Resume Optimization Agent capabilities...")
        
        # Initialize services (mock for testing)
        ai_service = AIService()
        embedding_service = EmbeddingService()
        
        # Initialize agent
        agent = ResumeOptimizationAgent(
            agent_id="capability_test_agent",
            ai_service=ai_service,
            embedding_service=embedding_service
        )
        
        # Test capability definitions
        capabilities = agent.capabilities
        expected_capabilities = [
            "resume_structure_analysis",
            "keyword_optimization", 
            "achievement_validation",
            "formatting_optimization",
            "ats_compatibility_check"
        ]
        
        actual_capabilities = [cap.name for cap in capabilities]
        
        for expected in expected_capabilities:
            if expected in actual_capabilities:
                logger.info(f"✓ Capability '{expected}' found")
            else:
                logger.error(f"✗ Capability '{expected}' missing")
                return False
        
        # Test confidence calculation
        mock_result = {
            "structure_analysis": {"organization_rating": 0.8},
            "keyword_analysis": {"keyword_match_score": 0.7}
        }
        
        mock_request = AgentRequest(
            user_id="test",
            request_type=RequestType.RESUME_REVIEW,
            content={},
            context={}
        )
        
        confidence = agent._calculate_confidence(mock_result, mock_request)
        logger.info(f"Confidence calculation test: {confidence}")
        
        if 0.0 <= confidence <= 1.0:
            logger.info("✓ Confidence calculation working correctly")
        else:
            logger.error("✗ Confidence calculation out of range")
            return False
        
        logger.info("Agent capabilities test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Agent capabilities test failed: {str(e)}")
        return False

async def main():
    """Main test function"""
    logger.info("=" * 60)
    logger.info("RESUME OPTIMIZATION AGENT TEST SUITE")
    logger.info("=" * 60)
    
    # Run basic functionality test
    basic_test_result = await test_resume_optimization_agent()
    
    # Run capabilities test
    capabilities_test_result = await test_agent_capabilities()
    
    # Summary
    logger.info("=" * 60)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Basic functionality test: {'PASSED' if basic_test_result else 'FAILED'}")
    logger.info(f"Capabilities test: {'PASSED' if capabilities_test_result else 'FAILED'}")
    
    overall_success = basic_test_result and capabilities_test_result
    logger.info(f"Overall test result: {'PASSED' if overall_success else 'FAILED'}")
    
    return overall_success

if __name__ == "__main__":
    # Run the test
    success = asyncio.run(main())
    sys.exit(0 if success else 1)