"""
Integration test for Skills Analysis Agent with the orchestrator system
"""
import asyncio
import logging
from typing import Dict, Any

from models.agent import AgentRequest, RequestType, AgentType
from services.skills_analysis_agent import SkillsAnalysisAgent
from services.career_strategy_agent import CareerStrategyAgent
from services.agent_orchestrator_service import AgentOrchestratorService
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
                "content": "Python, JavaScript, React, Node.js, SQL, AWS, Docker, machine learning",
                "source": "resume"
            },
            {
                "content": "Software Engineer with 4 years experience in full-stack development",
                "source": "resume"
            },
            {
                "content": "Interested in transitioning to Product Manager role at a tech startup",
                "source": "profile"
            }
        ]

async def test_skills_agent_integration():
    """Test Skills Analysis Agent integration with orchestrator"""
    
    print("🔧 Testing Skills Analysis Agent Integration...")
    
    # Initialize services
    ai_service = AIService()
    embedding_service = MockEmbeddingService()
    
    # Initialize orchestrator
    orchestrator = AgentOrchestratorService(ai_service)
    await orchestrator.start()
    
    # Initialize Skills Analysis Agent
    skills_agent = SkillsAnalysisAgent(
        agent_id="skills_agent_integration",
        ai_service=ai_service,
        embedding_service=embedding_service
    )
    
    # Initialize Career Strategy Agent for comparison
    career_agent = CareerStrategyAgent(
        agent_id="career_agent_integration",
        ai_service=ai_service,
        embedding_service=embedding_service
    )
    
    # Register agents with orchestrator
    orchestrator.register_agent(skills_agent)
    orchestrator.register_agent(career_agent)
    
    print(f"✅ Registered Skills Analysis Agent: {skills_agent.agent_id}")
    print(f"✅ Registered Career Strategy Agent: {career_agent.agent_id}")
    
    # Check orchestrator status
    status = orchestrator.get_status()
    print(f"📊 Orchestrator Status:")
    print(f"  • Registered agents: {status['registered_agents']}")
    print(f"  • Agents by type: {status['agents_by_type']}")
    
    # Verify Skills Analysis Agent is properly registered
    if AgentType.SKILLS_ANALYSIS.value in status['agents_by_type']:
        skills_count = status['agents_by_type'][AgentType.SKILLS_ANALYSIS.value]
        print(f"✅ Skills Analysis agents registered: {skills_count}")
    else:
        print("❌ Skills Analysis Agent not found in orchestrator")
    
    # Test routing rules include Skills Analysis Agent
    print("\n🗺️  Testing Routing Rules...")
    
    routing_rules = orchestrator.routing_rules
    
    # Check SKILL_ANALYSIS requests
    if RequestType.SKILL_ANALYSIS in routing_rules:
        rule = routing_rules[RequestType.SKILL_ANALYSIS]
        required_agents = rule.get("required_agents", [])
        if AgentType.SKILLS_ANALYSIS in required_agents:
            print("✅ SKILL_ANALYSIS requests route to Skills Analysis Agent")
        else:
            print("❌ SKILL_ANALYSIS requests don't route to Skills Analysis Agent")
    
    # Check ROADMAP_GENERATION requests
    if RequestType.ROADMAP_GENERATION in routing_rules:
        rule = routing_rules[RequestType.ROADMAP_GENERATION]
        required_agents = rule.get("required_agents", [])
        if AgentType.SKILLS_ANALYSIS in required_agents:
            print("✅ ROADMAP_GENERATION requests include Skills Analysis Agent")
        else:
            print("❌ ROADMAP_GENERATION requests don't include Skills Analysis Agent")
    
    # Check CAREER_TRANSITION requests
    if RequestType.CAREER_TRANSITION in routing_rules:
        rule = routing_rules[RequestType.CAREER_TRANSITION]
        required_agents = rule.get("required_agents", [])
        if AgentType.SKILLS_ANALYSIS in required_agents:
            print("✅ CAREER_TRANSITION requests include Skills Analysis Agent")
        else:
            print("❌ CAREER_TRANSITION requests don't include Skills Analysis Agent")
    
    # Test agent selection for skill analysis request
    print("\n🎯 Testing Agent Selection...")
    
    skill_request = AgentRequest(
        user_id="test_user_integration",
        request_type=RequestType.SKILL_ANALYSIS,
        content={
            "user_id": "test_user_integration",
            "target_role": "Senior Product Manager",
            "timeline": "12 months"
        }
    )
    
    # Analyze request (this will determine which agents are needed)
    try:
        analysis = await orchestrator._analyze_request(skill_request)
        print(f"✅ Request analysis completed")
        print(f"  • Required agents: {[agent.value for agent in analysis.required_agents]}")
        print(f"  • Complexity score: {analysis.complexity_score:.2f}")
        print(f"  • Success probability: {analysis.success_probability:.2f}")
        
        if AgentType.SKILLS_ANALYSIS in analysis.required_agents:
            print("✅ Skills Analysis Agent correctly identified as required")
        else:
            print("❌ Skills Analysis Agent not identified as required")
            
    except Exception as e:
        print(f"❌ Request analysis failed: {str(e)}")
    
    # Test workflow creation
    print("\n⚙️  Testing Workflow Creation...")
    
    try:
        analysis = await orchestrator._analyze_request(skill_request)
        workflow = await orchestrator._create_workflow(skill_request, analysis)
        
        print(f"✅ Workflow created: {workflow.id}")
        print(f"  • Participating agents: {workflow.participating_agents}")
        print(f"  • Workflow steps: {len(workflow.workflow_steps)}")
        
        # Check if Skills Analysis Agent is in the workflow
        skills_agent_in_workflow = any(
            step.get("agent_id") == skills_agent.agent_id 
            for step in workflow.workflow_steps
        )
        
        if skills_agent_in_workflow:
            print("✅ Skills Analysis Agent included in workflow")
        else:
            print("❌ Skills Analysis Agent not included in workflow")
            
    except Exception as e:
        print(f"❌ Workflow creation failed: {str(e)}")
    
    # Test agent capabilities matching
    print("\n🎯 Testing Agent Capabilities...")
    
    # Check if agent can handle the request
    can_handle = skills_agent.can_handle_request(skill_request)
    print(f"✅ Skills agent can handle request: {can_handle}")
    
    # Check agent status
    agent_status = skills_agent.get_status()
    print(f"✅ Agent status: Active={agent_status.is_active}, Load={agent_status.current_load}")
    
    # Print agent capabilities
    print(f"📋 Agent Capabilities ({len(agent_status.capabilities)}):")
    for capability in agent_status.capabilities:
        print(f"  • {capability.name}")
        print(f"    Confidence threshold: {capability.confidence_threshold}")
        print(f"    Max processing time: {capability.max_processing_time}s")
    
    # Cleanup
    await orchestrator.stop()
    
    print("\n🎉 Skills Analysis Agent integration testing completed!")

async def test_multi_agent_coordination():
    """Test coordination between Skills Analysis Agent and other agents"""
    
    print("\n🤝 Testing Multi-Agent Coordination...")
    
    # Initialize services
    ai_service = AIService()
    embedding_service = MockEmbeddingService()
    
    # Initialize orchestrator
    orchestrator = AgentOrchestratorService(ai_service)
    await orchestrator.start()
    
    # Initialize multiple agents
    skills_agent = SkillsAnalysisAgent(
        agent_id="skills_coord_test",
        ai_service=ai_service,
        embedding_service=embedding_service
    )
    
    career_agent = CareerStrategyAgent(
        agent_id="career_coord_test",
        ai_service=ai_service,
        embedding_service=embedding_service
    )
    
    # Register agents
    orchestrator.register_agent(skills_agent)
    orchestrator.register_agent(career_agent)
    
    # Test multi-agent request (roadmap generation)
    roadmap_request = AgentRequest(
        user_id="test_user_coord",
        request_type=RequestType.ROADMAP_GENERATION,
        content={
            "user_id": "test_user_coord",
            "current_role": "Software Engineer",
            "target_role": "Product Manager",
            "timeline": "15 months"
        }
    )
    
    try:
        # Analyze request
        analysis = await orchestrator._analyze_request(roadmap_request)
        print(f"✅ Multi-agent request analyzed")
        print(f"  • Required agents: {[agent.value for agent in analysis.required_agents]}")
        
        # Check if both agents are required
        has_skills = AgentType.SKILLS_ANALYSIS in analysis.required_agents
        has_career = AgentType.CAREER_STRATEGY in analysis.required_agents
        
        print(f"  • Skills Analysis Agent required: {has_skills}")
        print(f"  • Career Strategy Agent required: {has_career}")
        
        if has_skills and has_career:
            print("✅ Multi-agent coordination properly configured")
        else:
            print("❌ Multi-agent coordination not properly configured")
        
        # Create workflow
        workflow = await orchestrator._create_workflow(roadmap_request, analysis)
        print(f"✅ Multi-agent workflow created with {len(workflow.workflow_steps)} steps")
        
    except Exception as e:
        print(f"❌ Multi-agent coordination test failed: {str(e)}")
    
    # Cleanup
    await orchestrator.stop()
    
    print("🤝 Multi-agent coordination testing completed!")

if __name__ == "__main__":
    print("🚀 Starting Skills Analysis Agent Integration Tests...")
    
    # Run integration tests
    asyncio.run(test_skills_agent_integration())
    asyncio.run(test_multi_agent_coordination())
    
    print("\n✨ All integration tests completed!")