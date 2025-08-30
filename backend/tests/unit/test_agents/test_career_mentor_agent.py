"""
Test script for Career Mentor Agent functionality
"""
import asyncio
import logging
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.agent import AgentRequest, RequestType, RequestPriority
from services.career_mentor_agent import CareerMentorAgent
from services.ai_service import AIService
from services.embedding_service import EmbeddingService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_career_mentor_agent():
    """Test the Career Mentor Agent functionality"""
    logger.info("Starting Career Mentor Agent tests...")
    
    try:
        # Initialize services
        ai_service = AIService()
        embedding_service = EmbeddingService()
        
        # Initialize Career Mentor Agent
        agent = CareerMentorAgent(
            agent_id="test_career_mentor",
            ai_service=ai_service,
            embedding_service=embedding_service
        )
        
        logger.info(f"Initialized Career Mentor Agent: {agent.agent_id}")
        
        # Test 1: Career Coaching Request
        logger.info("\n=== Test 1: Career Coaching Request ===")
        coaching_request = AgentRequest(
            user_id="test_user_1",
            request_type=RequestType.CAREER_ADVICE,
            content={
                "question": "I'm feeling stuck in my current role and not sure how to advance my career. What should I do?",
                "user_id": "test_user_1",
                "coaching_focus": "career_advancement"
            },
            context={
                "user_background": "Software developer with 3 years experience, looking to move into senior roles"
            },
            priority=RequestPriority.MEDIUM
        )
        
        coaching_response = await agent.handle_request(coaching_request)
        logger.info(f"Coaching Response Confidence: {coaching_response.confidence_score}")
        logger.info(f"Coaching Approach: {coaching_response.response_content.get('coaching_approach', 'N/A')}")
        
        # Test 2: Mock Interview Request
        logger.info("\n=== Test 2: Mock Interview Request ===")
        interview_request = AgentRequest(
            user_id="test_user_2",
            request_type=RequestType.INTERVIEW_PREP,
            content={
                "target_role": "Senior Software Engineer",
                "interview_type": "behavioral",
                "difficulty_level": "intermediate",
                "user_id": "test_user_2"
            },
            context={
                "user_background": "Mid-level developer with experience in Python and JavaScript"
            },
            priority=RequestPriority.HIGH
        )
        
        interview_response = await agent.handle_request(interview_request)
        logger.info(f"Interview Response Confidence: {interview_response.confidence_score}")
        mock_interview = interview_response.response_content.get('mock_interview', {})
        logger.info(f"Generated {len(mock_interview.get('questions', []))} interview questions")
        logger.info(f"Estimated Duration: {mock_interview.get('estimated_duration', 'N/A')}")
        
        # Test 3: Career Transition Support
        logger.info("\n=== Test 3: Career Transition Support ===")
        transition_request = AgentRequest(
            user_id="test_user_3",
            request_type=RequestType.CAREER_TRANSITION,
            content={
                "current_role": "Software Developer",
                "target_role": "Product Manager",
                "user_id": "test_user_3",
                "concerns": ["lack of business experience", "interview preparation"]
            },
            context={
                "user_background": "5 years software development, interested in product management"
            },
            priority=RequestPriority.HIGH
        )
        
        transition_response = await agent.handle_request(transition_request)
        logger.info(f"Transition Response Confidence: {transition_response.confidence_score}")
        transition_support = transition_response.response_content.get('transition_support', {})
        logger.info(f"Readiness Score: {transition_support.get('readiness_assessment', {}).get('readiness_score', 'N/A')}")
        
        # Test 4: General Mentoring
        logger.info("\n=== Test 4: General Mentoring ===")
        general_request = AgentRequest(
            user_id="test_user_4",
            request_type=RequestType.CAREER_ADVICE,
            content={
                "question": "How do I build confidence in networking situations?",
                "user_id": "test_user_4"
            },
            context={
                "user_background": "Introverted engineer looking to expand professional network"
            },
            priority=RequestPriority.MEDIUM
        )
        
        general_response = await agent.handle_request(general_request)
        logger.info(f"General Mentoring Confidence: {general_response.confidence_score}")
        logger.info(f"Support Level: {general_response.response_content.get('support_level', 'N/A')}")
        
        # Test Agent Status and Capabilities
        logger.info("\n=== Agent Status and Capabilities ===")
        status = agent.get_status()
        logger.info(f"Agent Active: {status.is_active}")
        logger.info(f"Current Load: {status.current_load}")
        logger.info(f"Capabilities: {len(status.capabilities)}")
        
        for capability in status.capabilities:
            logger.info(f"  - {capability.name}: {capability.description}")
        
        logger.info("\nCareer Mentor Agent tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_career_mentor_agent())