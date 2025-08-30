"""
Test script for Skills Analysis Agent functionality
"""
import asyncio
import logging
from typing import Dict, Any

from models.agent import AgentRequest, RequestType, RequestPriority
from services.skills_analysis_agent import SkillsAnalysisAgent
from services.ai_service import AIService
from services.embedding_service import EmbeddingService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockEmbeddingService:
    """Mock embedding service for testing"""
    
    def search_user_context(self, user_id: str, query: str, n_results: int = 5):
        """Mock user context search"""
        return [
            {
                "content": "Python programming, machine learning, data analysis, SQL, AWS, Docker",
                "source": "resume"
            },
            {
                "content": "Software Engineer with 3 years experience in web development and data science",
                "source": "resume"
            },
            {
                "content": "Looking to transition to Product Manager role at a tech company",
                "source": "profile"
            }
        ]

async def test_skills_analysis_agent():
    """Test the Skills Analysis Agent functionality"""
    
    print("🧪 Testing Skills Analysis Agent...")
    
    # Initialize services
    ai_service = AIService()
    embedding_service = MockEmbeddingService()
    
    # Initialize agent
    agent = SkillsAnalysisAgent(
        agent_id="skills_agent_test",
        ai_service=ai_service,
        embedding_service=embedding_service
    )
    
    print(f"✅ Initialized Skills Analysis Agent: {agent.agent_id}")
    print(f"📋 Agent capabilities: {len(agent.capabilities)}")
    
    # Test 1: Comprehensive Skills Analysis
    print("\n🔍 Test 1: Comprehensive Skills Analysis")
    
    skills_request = AgentRequest(
        user_id="test_user_123",
        request_type=RequestType.SKILL_ANALYSIS,
        content={
            "user_id": "test_user_123",
            "target_role": "Product Manager",
            "timeline": "9 months"
        },
        context={
            "current_role": "Software Engineer",
            "experience_level": "Mid-level"
        }
    )
    
    try:
        response = await agent.handle_request(skills_request)
        print(f"✅ Skills analysis completed")
        print(f"📊 Confidence score: {response.confidence_score:.2f}")
        print(f"⏱️  Processing time: {response.processing_time:.2f}s")
        
        # Check response content
        content = response.response_content
        if "current_skills" in content:
            print("✅ Current skills analysis included")
        if "skill_gaps" in content:
            print("✅ Skill gaps identification included")
        if "prioritized_development" in content:
            print("✅ Prioritized development plan included")
        if "certification_recommendations" in content:
            print("✅ Certification recommendations included")
            
    except Exception as e:
        print(f"❌ Skills analysis failed: {str(e)}")
    
    # Test 2: Career Transition Skills Analysis
    print("\n🔄 Test 2: Career Transition Skills Analysis")
    
    transition_request = AgentRequest(
        user_id="test_user_123",
        request_type=RequestType.CAREER_TRANSITION,
        content={
            "user_id": "test_user_123",
            "current_role": "Software Engineer",
            "target_role": "Product Manager",
            "timeline": "12 months"
        },
        context={
            "experience_years": 3,
            "industry": "Technology"
        }
    )
    
    try:
        response = await agent.handle_request(transition_request)
        print(f"✅ Transition analysis completed")
        print(f"📊 Confidence score: {response.confidence_score:.2f}")
        
        # Check response content
        content = response.response_content
        if "transition_analysis" in content:
            print("✅ Transition analysis included")
        if "transferable_skills" in content:
            print("✅ Transferable skills analysis included")
        if "feasibility_assessment" in content:
            print("✅ Feasibility assessment included")
            
    except Exception as e:
        print(f"❌ Transition analysis failed: {str(e)}")
    
    # Test 3: Roadmap Skills Contribution
    print("\n🗺️  Test 3: Roadmap Skills Contribution")
    
    roadmap_request = AgentRequest(
        user_id="test_user_123",
        request_type=RequestType.ROADMAP_GENERATION,
        content={
            "user_id": "test_user_123",
            "target_role": "Senior Product Manager",
            "timeline": "18 months"
        },
        context={
            "current_role": "Software Engineer",
            "career_level": "Mid-level"
        }
    )
    
    try:
        response = await agent.handle_request(roadmap_request)
        print(f"✅ Roadmap contribution completed")
        print(f"📊 Confidence score: {response.confidence_score:.2f}")
        
        # Check response content
        content = response.response_content
        if "skills_contribution" in content:
            print("✅ Skills contribution included")
            skills_contrib = content["skills_contribution"]
            if "phase_based_skills" in skills_contrib:
                print("✅ Phase-based skills analysis included")
            if "skill_milestones" in skills_contrib:
                print("✅ Skill milestones included")
                
    except Exception as e:
        print(f"❌ Roadmap contribution failed: {str(e)}")
    
    # Test 4: General Skills Advice
    print("\n💡 Test 4: General Skills Advice")
    
    advice_request = AgentRequest(
        user_id="test_user_123",
        request_type=RequestType.CAREER_ADVICE,
        content={
            "user_id": "test_user_123",
            "question": "What technical skills should I focus on to become a better product manager?",
            "message": "I'm a software engineer looking to transition to product management. What skills should I prioritize?"
        },
        context={
            "current_role": "Software Engineer",
            "target_role": "Product Manager"
        }
    )
    
    try:
        response = await agent.handle_request(advice_request)
        print(f"✅ Skills advice completed")
        print(f"📊 Confidence score: {response.confidence_score:.2f}")
        
        # Check response content
        content = response.response_content
        if "skills_advice" in content:
            print("✅ Skills advice included")
        if "actionable_recommendations" in content:
            print("✅ Actionable recommendations included")
            
    except Exception as e:
        print(f"❌ Skills advice failed: {str(e)}")
    
    # Test 5: Agent Status and Capabilities
    print("\n📊 Test 5: Agent Status and Capabilities")
    
    status = agent.get_status()
    print(f"✅ Agent ID: {status.agent_id}")
    print(f"✅ Agent Type: {status.agent_type.value}")
    print(f"✅ Is Active: {status.is_active}")
    print(f"✅ Current Load: {status.current_load}")
    print(f"✅ Max Concurrent Requests: {status.max_concurrent_requests}")
    print(f"✅ Capabilities Count: {len(status.capabilities)}")
    
    # Print capabilities
    print("\n🎯 Agent Capabilities:")
    for capability in status.capabilities:
        print(f"  • {capability.name}: {capability.description}")
        print(f"    Input types: {capability.input_types}")
        print(f"    Output types: {capability.output_types}")
        print(f"    Confidence threshold: {capability.confidence_threshold}")
        print(f"    Max processing time: {capability.max_processing_time}s")
        print()
    
    # Test 6: Performance Metrics
    print("📈 Performance Metrics:")
    metrics = status.performance_metrics
    print(f"  • Total requests: {metrics.get('total_requests', 0)}")
    print(f"  • Successful requests: {metrics.get('successful_requests', 0)}")
    print(f"  • Failed requests: {metrics.get('failed_requests', 0)}")
    print(f"  • Average processing time: {metrics.get('average_processing_time', 0):.2f}s")
    print(f"  • Average confidence: {metrics.get('average_confidence', 0):.2f}")
    
    print("\n🎉 Skills Analysis Agent testing completed!")

async def test_agent_collaboration():
    """Test agent collaboration capabilities"""
    
    print("\n🤝 Testing Agent Collaboration...")
    
    # Initialize services
    ai_service = AIService()
    embedding_service = MockEmbeddingService()
    
    # Initialize agent
    agent = SkillsAnalysisAgent(
        agent_id="skills_agent_collab",
        ai_service=ai_service,
        embedding_service=embedding_service
    )
    
    # Test collaboration message handling
    from models.agent import AgentMessage, MessageType
    
    # Test collaboration request
    collab_message = AgentMessage(
        sender_agent_id="career_strategy_agent",
        recipient_agent_id=agent.agent_id,
        message_type=MessageType.COLLABORATION_REQUEST,
        content={
            "type": "skill_input_for_roadmap",
            "user_id": "test_user_123",
            "target_role": "Product Manager",
            "collaboration_id": "collab_123"
        }
    )
    
    try:
        result = await agent.receive_message(collab_message)
        print(f"✅ Collaboration request handled: {result}")
    except Exception as e:
        print(f"❌ Collaboration request failed: {str(e)}")
    
    # Test context sharing
    context_message = AgentMessage(
        sender_agent_id="orchestrator",
        recipient_agent_id=agent.agent_id,
        message_type=MessageType.CONTEXT_SHARE,
        content={
            "type": "user_profile_update",
            "user_id": "test_user_123",
            "updated_fields": ["skills", "experience"]
        }
    )
    
    try:
        result = await agent.receive_message(context_message)
        print(f"✅ Context sharing handled: {result}")
    except Exception as e:
        print(f"❌ Context sharing failed: {str(e)}")
    
    print("🤝 Agent collaboration testing completed!")

if __name__ == "__main__":
    print("🚀 Starting Skills Analysis Agent Tests...")
    
    # Run tests
    asyncio.run(test_skills_analysis_agent())
    asyncio.run(test_agent_collaboration())
    
    print("\n✨ All tests completed!")