#!/usr/bin/env python3
"""
Comprehensive test script for agent system integration
Tests agent transparency, multi-agent coordination, and service integration
"""
import asyncio
import sys
import os
import json

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_multi_agent_service_initialization():
    """Test multi-agent service initialization and status"""
    print("Testing Multi-Agent Service Initialization...")
    
    try:
        from services.multi_agent_service import get_multi_agent_service
        
        multi_agent_service = await get_multi_agent_service()
        print(f"✓ Multi-agent service initialized: {multi_agent_service.is_initialized}")
        print(f"✓ Multi-agent service running: {multi_agent_service.is_running}")
        print(f"✓ Number of agents: {len(multi_agent_service.agents)}")
        
        if multi_agent_service.orchestrator:
            print(f"✓ Orchestrator agents: {len(multi_agent_service.orchestrator.agents)}")
            for agent_id, agent in multi_agent_service.orchestrator.agents.items():
                print(f"  - {agent.agent_type.value}: {agent_id}")
        
        return True
        
    except Exception as e:
        print(f"✗ Multi-agent service test failed: {e}")
        return False

async def test_agent_transparency_apis():
    """Test agent transparency API endpoints"""
    print("\nTesting Agent Transparency APIs...")
    
    try:
        # Test agent status API
        from api.agents import get_agent_status
        
        status_result = await get_agent_status()
        print(f"✓ Agent status API returned {len(status_result['agents'])} agents")
        
        for agent in status_result['agents']:
            print(f"  - {agent['type']}: {agent['status']} (load: {agent['currentLoad']}/{agent['maxLoad']})")
        
        # Test agent metrics API
        from api.agents import get_agent_metrics
        
        metrics_result = await get_agent_metrics()
        print(f"✓ System metrics: {metrics_result['system']['registeredAgents']} agents, {metrics_result['system']['activeWorkflows']} workflows")
        
        # Test workflows API
        from api.agents import get_active_workflows
        
        workflows_result = await get_active_workflows()
        print(f"✓ Workflows: {workflows_result['summary']['active']} active, {workflows_result['summary']['totalCompleted']} completed")
        
        return True
        
    except Exception as e:
        print(f"✗ Agent transparency APIs test failed: {e}")
        return False

async def test_chat_service_integration():
    """Test chat service integration with multi-agent system"""
    print("\nTesting Chat Service Integration...")
    
    try:
        from services.chat_service import RAGChatService
        from models.chat import ChatInitRequest, ChatMessageRequest
        
        chat_service = RAGChatService()
        
        # Initialize a test chat session
        init_request = ChatInitRequest(
            user_id="test_user_multi_agent",
            title="Multi-Agent Test Chat"
        )
        
        session = await chat_service.initialize_chat_session(init_request)
        print(f"✓ Chat session created: {session.id}")
        
        # Send a test message that should trigger multi-agent processing
        test_message = "I want to transition from software engineer to product manager. Can you help me create a comprehensive plan?"
        
        message_request = ChatMessageRequest(
            session_id=session.id,
            message=test_message,
            user_id="test_user_multi_agent"
        )
        
        response = await chat_service.send_message(message_request)
        print(f"✓ Chat response received: {len(response.message)} characters")
        print(f"✓ Response preview: {response.message[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Chat service integration test failed: {e}")
        return False

async def test_roadmap_service_integration():
    """Test roadmap service integration with multi-agent system"""
    print("\nTesting Roadmap Service Integration...")
    
    try:
        from services.roadmap_service import RoadmapService
        from models.roadmap import RoadmapRequest
        
        roadmap_service = RoadmapService()
        await roadmap_service._init_services()
        
        # Test workflow decision logic
        test_request = RoadmapRequest(
            current_role="Software Engineer",
            target_role="Product Manager",
            user_background="5 years experience in web development",
            timeline_preference="6 months",
            focus_areas=["product strategy", "user research"],
            constraints=["limited time on weekends"]
        )
        
        should_use_workflow = roadmap_service._should_use_workflow_for_roadmap(test_request)
        print(f"✓ Workflow decision for complex request: {should_use_workflow}")
        
        # Test simple request
        simple_request = RoadmapRequest(
            current_role="Junior Developer",
            target_role="Senior Developer",
            user_background="Basic experience"
        )
        
        should_use_workflow_simple = roadmap_service._should_use_workflow_for_roadmap(simple_request)
        print(f"✓ Workflow decision for simple request: {should_use_workflow_simple}")
        
        return True
        
    except Exception as e:
        print(f"✗ Roadmap service integration test failed: {e}")
        return False

async def test_agent_activity_logging():
    """Test agent activity logging system"""
    print("\nTesting Agent Activity Logging...")
    
    try:
        from api.agents import get_agent_logs
        
        # Get recent agent logs
        logs_result = await get_agent_logs(limit=10)
        print(f"✓ Retrieved {len(logs_result['logs'])} recent log entries")
        print(f"✓ Log statistics: {logs_result['statistics']['totalActivities']} total activities")
        
        # Show sample log entries
        for log in logs_result['logs'][:3]:
            print(f"  - {log['timestamp']}: {log['activityType']} by {log['agentId']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Agent activity logging test failed: {e}")
        return False

async def main():
    """Run all agent system integration tests"""
    print("Starting Agent System Integration Tests...")
    
    tests = [
        ("Multi-Agent Service Initialization", test_multi_agent_service_initialization),
        ("Agent Transparency APIs", test_agent_transparency_apis),
        ("Chat Service Integration", test_chat_service_integration),
        ("Roadmap Service Integration", test_roadmap_service_integration),
        ("Agent Activity Logging", test_agent_activity_logging)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print(f"{'='*50}")
        
        try:
            result = await test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✓ {test_name} PASSED")
            else:
                print(f"✗ {test_name} FAILED")
                
        except Exception as e:
            print(f"✗ {test_name} ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status:4} | {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All agent system integration tests passed!")
        return 0
    else:
        print(f"❌ {total - passed} tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)