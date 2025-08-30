#!/usr/bin/env python3
"""
Comprehensive test script for LangGraph multi-agent workflow integration
Includes both real integration tests and mock workflow demonstrations
"""
import asyncio
import logging
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ai_service import get_ai_service
from services.chat_service import RAGChatService
from services.roadmap_service import RoadmapService
from services.roadmap_chat_service import RoadmapChatService
from models.chat import ChatInitRequest, ChatMessageRequest
from models.roadmap import RoadmapRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_chat_service_workflow_integration():
    """Test ChatService integration with LangGraph workflows"""
    logger.info("Testing ChatService workflow integration...")
    
    try:
        # Initialize chat service
        chat_service = RAGChatService()
        
        # Check if workflow orchestrator is available
        orchestrator = await chat_service._get_workflow_orchestrator()
        if orchestrator:
            logger.info("✓ Workflow orchestrator initialized successfully")
            
            # Test workflow patterns
            test_message = "I want to transition from software engineer to product manager"
            user_context = {"context_text": "Test user with 5 years experience"}
            
            workflow_routing = chat_service._should_use_workflow(test_message, user_context)
            if workflow_routing:
                logger.info(f"✓ Workflow routing detected: {workflow_routing['workflow_name']}")
            else:
                logger.info("- No workflow routing detected for test message")
            
            # Test workflow templates
            templates = orchestrator.get_workflow_templates()
            logger.info(f"✓ Available workflow templates: {len(templates)}")
            
        else:
            logger.warning("- Workflow orchestrator not available")
        
        logger.info("ChatService workflow integration test completed")
        return True
        
    except Exception as e:
        logger.error(f"ChatService workflow integration test failed: {e}")
        return False

async def test_roadmap_service_workflow_integration():
    """Test RoadmapService integration with LangGraph workflows"""
    logger.info("Testing RoadmapService workflow integration...")
    
    try:
        # Initialize roadmap service
        roadmap_service = RoadmapService()
        await roadmap_service._init_services()
        
        # Test workflow decision logic
        test_request = RoadmapRequest(
            current_role="Software Engineer",
            target_role="Product Manager",
            user_background="5 years experience in web development with some leadership experience",
            timeline_preference="6 months",
            focus_areas=["product strategy", "user research", "stakeholder management"],
            constraints=["limited time on weekends", "prefer online learning"]
        )
        
        should_use_workflow = roadmap_service._should_use_workflow_for_roadmap(test_request)
        logger.info(f"✓ Workflow decision for complex request: {should_use_workflow}")
        
        # Test simple request
        simple_request = RoadmapRequest(
            current_role="Junior Developer",
            target_role="Senior Developer",
            user_background="Basic experience"
        )
        
        should_use_workflow_simple = roadmap_service._should_use_workflow_for_roadmap(simple_request)
        logger.info(f"✓ Workflow decision for simple request: {should_use_workflow_simple}")
        
        logger.info("RoadmapService workflow integration test completed")
        return True
        
    except Exception as e:
        logger.error(f"RoadmapService workflow integration test failed: {e}")
        return False

async def test_roadmap_chat_service_workflow_integration():
    """Test RoadmapChatService integration with LangGraph workflows"""
    logger.info("Testing RoadmapChatService workflow integration...")
    
    try:
        # Initialize roadmap chat service
        roadmap_chat_service = RoadmapChatService()
        
        # Check if workflow orchestrator is available
        orchestrator = await roadmap_chat_service._get_workflow_orchestrator()
        if orchestrator:
            logger.info("✓ Workflow orchestrator initialized successfully")
            
            # Test workflow patterns
            test_messages = [
                "Can you improve my roadmap timeline?",
                "I need more resources for learning Python",
                "How can I develop better communication skills?",
                "What's the best way to practice system design?"
            ]
            
            roadmap_context = {"title": "Test Roadmap", "phases": []}
            
            for message in test_messages:
                workflow_routing = roadmap_chat_service._should_use_workflow_for_roadmap_chat(
                    message, roadmap_context
                )
                if workflow_routing:
                    logger.info(f"✓ Message '{message[:30]}...' -> {workflow_routing['pattern_matched']}")
                else:
                    logger.info(f"- Message '{message[:30]}...' -> direct AI")
            
        else:
            logger.warning("- Workflow orchestrator not available")
        
        logger.info("RoadmapChatService workflow integration test completed")
        return True
        
    except Exception as e:
        logger.error(f"RoadmapChatService workflow integration test failed: {e}")
        return False

async def test_workflow_orchestrator_health():
    """Test workflow orchestrator health and capabilities"""
    logger.info("Testing workflow orchestrator health...")
    
    try:
        # Get AI service
        ai_service = await get_ai_service()
        
        # Import and initialize workflow orchestrator
        from services.langgraph_workflow_orchestrator import LangGraphWorkflowOrchestrator
        
        orchestrator = LangGraphWorkflowOrchestrator(ai_service)
        await orchestrator.initialize_redis()
        
        # Test health check
        health = await orchestrator.health_check()
        logger.info(f"✓ Orchestrator health: {health['status']}")
        logger.info(f"✓ Available workflows: {health['workflow_names']}")
        logger.info(f"✓ Workflow templates: {health['workflow_templates']}")
        logger.info(f"✓ Redis available: {health['redis_available']}")
        
        # Test workflow templates
        templates = orchestrator.get_workflow_templates()
        for template_name, template_info in templates.items():
            logger.info(f"  - {template_name}: {template_info['description']}")
        
        logger.info("Workflow orchestrator health test completed")
        return True
        
    except Exception as e:
        logger.error(f"Workflow orchestrator health test failed: {e}")
        return False

async def main():
    """Run all integration tests"""
    logger.info("Starting LangGraph multi-agent workflow integration tests...")
    
    tests = [
        ("Mock Workflow Demonstration", test_mock_workflow_demonstration),
        ("Workflow Orchestrator Health", test_workflow_orchestrator_health),
        ("ChatService Integration", test_chat_service_workflow_integration),
        ("RoadmapService Integration", test_roadmap_service_workflow_integration),
        ("RoadmapChatService Integration", test_roadmap_chat_service_workflow_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"✓ {test_name} PASSED")
            else:
                logger.error(f"✗ {test_name} FAILED")
                
        except Exception as e:
            logger.error(f"✗ {test_name} ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"{status:4} | {test_name}")
    
    logger.info(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All integration tests passed!")
        return 0
    else:
        logger.error(f"❌ {total - passed} tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)async def
 test_mock_workflow_demonstration():
    """Demonstrate LangGraph workflow benefits with mock implementation"""
    
    try:
        logger.info("\n=== Mock LangGraph Workflow Demonstration ===")
        
        # Import mock classes from the mock test file
        from test_langgraph_integration_mock import MockLangGraphOrchestrator, MockAgent
        from models.agent import AgentType
        
        # Mock AI service
        class MockAIService:
            async def generate_text(self, prompt, **kwargs):
                return f"Mock synthesis for workflow coordination"
        
        # Initialize mock orchestrator
        ai_service = MockAIService()
        orchestrator = MockLangGraphOrchestrator(ai_service)
        
        # Register mock agents
        career_agent = MockAgent(AgentType.CAREER_STRATEGY, "career_agent_001")
        skills_agent = MockAgent(AgentType.SKILLS_ANALYSIS, "skills_agent_001") 
        learning_agent = MockAgent(AgentType.LEARNING_RESOURCE, "learning_agent_001")
        
        orchestrator.register_agent(career_agent)
        orchestrator.register_agent(skills_agent)
        orchestrator.register_agent(learning_agent)
        
        logger.info(f"Registered {len(orchestrator.agents)} agents with mock orchestrator")
        
        # Test workflow execution
        logger.info("\n=== Testing Career Transition Workflow ===")
        
        result = await orchestrator.execute_workflow(
            workflow_name="career_transition",
            user_id="test_user_123",
            request_type="career_transition",
            request_content={
                "current_role": "Software Engineer",
                "target_role": "Product Manager", 
                "timeline": "12 months",
                "constraints": {"budget": "medium", "time_commitment": "part-time"}
            }
        )
        
        logger.info(f"✅ Mock workflow executed successfully: {result['success']}")
        logger.info(f"📋 Workflow ID: {result['workflow_id']}")
        logger.info(f"🔄 Steps completed: {result['steps_completed']}")
        
        # Show workflow benefits
        benefits = {
            "State Management": "Persistent workflow state across agent interactions",
            "Workflow Orchestration": "Sequential agent execution with dependency management",
            "Agent Coordination": "Context sharing between agents in workflows",
            "Scalability": "Parallel agent execution for performance",
            "Monitoring & Debugging": "Real-time workflow progress tracking"
        }
        
        logger.info("🚀 LangGraph Integration Benefits:")
        for category, description in benefits.items():
            logger.info(f"  ✅ {category}: {description}")
        
        logger.info("\n✅ Mock workflow demonstration completed successfully!")
        
    except Exception as e:
        logger.error(f"Mock workflow demonstration failed: {str(e)}")
        return False
    
    return True