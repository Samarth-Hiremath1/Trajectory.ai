"""
Test script for Agent Performance Monitoring and Optimization System
"""
import asyncio
import logging
import json
from datetime import datetime, timedelta

from services.ai_service import AIService
from services.embedding_service import EmbeddingService
from services.agent_orchestrator_service import AgentOrchestratorService
from services.career_strategy_agent import CareerStrategyAgent
from services.skills_analysis_agent import SkillsAnalysisAgent
from services.learning_resource_agent import LearningResourceAgent
from models.agent import AgentRequest, RequestType, RequestPriority

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_performance_monitoring_system():
    """Test the complete agent performance monitoring and optimization system"""
    
    logger.info("Starting Agent Performance Monitoring System Test")
    
    # Initialize services
    ai_service = AIService()
    embedding_service = EmbeddingService()
    orchestrator = AgentOrchestratorService(ai_service)
    
    # Start orchestrator
    await orchestrator.start()
    
    # Create and register test agents
    career_agent = CareerStrategyAgent("career_agent_1", ai_service, embedding_service)
    skills_agent = SkillsAnalysisAgent("skills_agent_1", ai_service, embedding_service)
    learning_agent = LearningResourceAgent("learning_agent_1", ai_service, embedding_service)
    
    orchestrator.register_agent(career_agent)
    orchestrator.register_agent(skills_agent)
    orchestrator.register_agent(learning_agent)
    
    logger.info("Registered 3 test agents")
    
    # Test 1: Basic Performance Monitoring
    logger.info("\n=== Test 1: Basic Performance Monitoring ===")
    
    # Create test requests
    test_requests = [
        AgentRequest(
            user_id="test_user_1",
            request_type=RequestType.CAREER_ADVICE,
            content={"question": "How do I transition from software engineering to product management?"},
            priority=RequestPriority.MEDIUM
        ),
        AgentRequest(
            user_id="test_user_2",
            request_type=RequestType.SKILL_ANALYSIS,
            content={"current_skills": ["Python", "JavaScript"], "target_role": "Data Scientist"},
            priority=RequestPriority.HIGH
        ),
        AgentRequest(
            user_id="test_user_3",
            request_type=RequestType.LEARNING_PATH,
            content={"skill": "Machine Learning", "experience_level": "beginner"},
            priority=RequestPriority.LOW
        )
    ]
    
    # Process requests to generate performance data
    for i, request in enumerate(test_requests):
        logger.info(f"Processing test request {i+1}")
        try:
            result = await orchestrator.process_request(request)
            logger.info(f"Request {i+1} processed successfully: {result['success']}")
        except Exception as e:
            logger.error(f"Request {i+1} failed: {str(e)}")
    
    # Check performance status
    performance_status = orchestrator.get_performance_metrics()
    logger.info(f"System Performance Summary:")
    logger.info(f"- Total requests processed: {performance_status['system_performance']['total_requests_processed']}")
    logger.info(f"- Active agents: {performance_status['system_performance']['active_agents']}")
    logger.info(f"- System success rate: {performance_status['system_performance']['system_success_rate']:.2f}")
    
    # Test 2: Load Balancing
    logger.info("\n=== Test 2: Load Balancing ===")
    
    # Get load balancing status
    load_status = orchestrator.load_balancer.get_load_balancing_status()
    logger.info(f"Load Balancing Status:")
    logger.info(f"- Registered agents: {load_status['registered_agents']}")
    logger.info(f"- Default strategy: {load_status['default_strategy']}")
    
    # Test load balancing with multiple requests
    logger.info("Testing load balancing with concurrent requests...")
    
    concurrent_requests = [
        AgentRequest(
            user_id=f"concurrent_user_{i}",
            request_type=RequestType.CAREER_ADVICE,
            content={"question": f"Career advice question {i}"},
            priority=RequestPriority.MEDIUM
        )
        for i in range(5)
    ]
    
    # Process concurrent requests
    tasks = [orchestrator.process_request(req) for req in concurrent_requests]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successful_requests = sum(1 for result in results if isinstance(result, dict) and result.get('success'))
    logger.info(f"Concurrent requests processed: {successful_requests}/{len(concurrent_requests)}")
    
    # Trigger load rebalancing
    await orchestrator.load_balancer.rebalance_load()
    logger.info("Load rebalancing completed")
    
    # Test 3: Learning System
    logger.info("\n=== Test 3: Learning System ===")
    
    # Get learning metrics
    learning_metrics = orchestrator.learning_system.get_learning_metrics()
    logger.info(f"Learning System Metrics:")
    logger.info(f"- Total examples collected: {learning_metrics['total_examples_collected']}")
    logger.info(f"- Agents with examples: {learning_metrics['total_agents_with_examples']}")
    logger.info(f"- Patterns identified: {learning_metrics['patterns_identified']}")
    
    # Generate improvement suggestions for an agent
    if orchestrator.agents:
        test_agent_id = list(orchestrator.agents.keys())[0]
        logger.info(f"Generating improvement suggestions for agent: {test_agent_id}")
        
        suggestions = await orchestrator.learning_system.generate_improvement_suggestions(test_agent_id)
        logger.info(f"Generated {len(suggestions)} improvement suggestions")
        
        if suggestions:
            logger.info(f"Sample suggestion: {suggestions[0].description}")
    
    # Test 4: Conflict Resolution
    logger.info("\n=== Test 4: Conflict Resolution ===")
    
    # Get conflict status
    conflict_status = orchestrator.conflict_resolver.get_conflict_status()
    logger.info(f"Conflict Resolution Status:")
    logger.info(f"- Active conflicts: {conflict_status['active_conflicts']}")
    logger.info(f"- Resolved conflicts: {conflict_status['resolved_conflicts']}")
    
    # Create a request that might generate conflicts (multiple agents)
    complex_request = AgentRequest(
        user_id="conflict_test_user",
        request_type=RequestType.ROADMAP_GENERATION,
        content={
            "current_role": "Software Engineer",
            "target_role": "Product Manager",
            "timeline": "6 months"
        },
        priority=RequestPriority.HIGH
    )
    
    logger.info("Processing complex request that may generate conflicts...")
    try:
        result = await orchestrator.process_request(complex_request)
        logger.info(f"Complex request processed: {result['success']}")
        
        # Check if any conflicts were detected and resolved
        updated_conflict_status = orchestrator.conflict_resolver.get_conflict_status()
        if updated_conflict_status['resolved_conflicts'] > conflict_status['resolved_conflicts']:
            logger.info("Conflicts were detected and resolved during processing")
        
    except Exception as e:
        logger.error(f"Complex request failed: {str(e)}")
    
    # Test 5: Performance Optimization
    logger.info("\n=== Test 5: Performance Optimization ===")
    
    # Get performance alerts
    alerts = orchestrator.performance_monitor.get_performance_alerts()
    logger.info(f"Current performance alerts: {len(alerts)}")
    
    # Trigger system optimization
    logger.info("Triggering system performance optimization...")
    optimization_result = await orchestrator.optimize_system_performance()
    logger.info(f"Optimization results: {optimization_result}")
    
    # Test 6: Agent Knowledge Management
    logger.info("\n=== Test 6: Agent Knowledge Management ===")
    
    if orchestrator.agents:
        test_agent_id = list(orchestrator.agents.keys())[0]
        
        # Get current knowledge
        current_knowledge = orchestrator.learning_system.get_agent_knowledge(test_agent_id)
        logger.info(f"Current knowledge for {test_agent_id}: {len(current_knowledge)} items")
        
        # Update knowledge
        knowledge_update = {
            "test_knowledge": {
                "learned_at": datetime.utcnow().isoformat(),
                "source": "performance_test",
                "content": "Test knowledge update"
            }
        }
        
        orchestrator.learning_system.update_agent_knowledge(test_agent_id, knowledge_update)
        logger.info(f"Updated knowledge for agent {test_agent_id}")
        
        # Verify update
        updated_knowledge = orchestrator.learning_system.get_agent_knowledge(test_agent_id)
        logger.info(f"Updated knowledge for {test_agent_id}: {len(updated_knowledge)} items")
    
    # Test 7: Final Status Report
    logger.info("\n=== Test 7: Final Status Report ===")
    
    final_status = orchestrator.get_status()
    logger.info("Final System Status:")
    logger.info(f"- Registered agents: {final_status['registered_agents']}")
    logger.info(f"- Active workflows: {final_status['active_workflows']}")
    logger.info(f"- Workflow history: {final_status['workflow_history_size']}")
    logger.info(f"- Total requests: {final_status['metrics']['total_requests']}")
    logger.info(f"- Successful workflows: {final_status['metrics']['successful_workflows']}")
    logger.info(f"- Failed workflows: {final_status['metrics']['failed_workflows']}")
    
    # Performance summary
    perf_summary = final_status['performance_summary']
    logger.info(f"- System success rate: {perf_summary['system_success_rate']:.2f}")
    logger.info(f"- Average response time: {perf_summary['average_response_time']:.2f}s")
    logger.info(f"- Performance alerts: {perf_summary['performance_alerts']}")
    
    # Learning metrics
    learning_final = final_status['learning_metrics']
    logger.info(f"- Learning examples: {learning_final['total_examples_collected']}")
    logger.info(f"- Improvements suggested: {learning_final['improvements_suggested']}")
    logger.info(f"- Improvements implemented: {learning_final['improvements_implemented']}")
    
    # Cleanup
    await orchestrator.stop()
    logger.info("\nAgent Performance Monitoring System Test Completed Successfully!")

async def test_api_endpoints():
    """Test the API endpoints for performance monitoring"""
    
    logger.info("\n=== Testing API Endpoints ===")
    
    # This would require running the FastAPI server
    # For now, just log that API endpoints are available
    
    api_endpoints = [
        "GET /api/agents/performance/status",
        "GET /api/agents/performance/system-summary", 
        "GET /api/agents/performance/agents/{agent_id}/profile",
        "GET /api/agents/performance/load-balancing",
        "POST /api/agents/performance/load-balancing/rebalance",
        "GET /api/agents/performance/learning",
        "GET /api/agents/performance/agents/{agent_id}/improvements",
        "POST /api/agents/performance/agents/{agent_id}/improvements/apply",
        "GET /api/agents/performance/conflicts",
        "GET /api/agents/performance/alerts",
        "DELETE /api/agents/performance/alerts",
        "POST /api/agents/performance/optimize",
        "GET /api/agents/performance/agents/{agent_id}/knowledge",
        "PUT /api/agents/performance/agents/{agent_id}/knowledge",
        "GET /api/agents/performance/metrics/export"
    ]
    
    logger.info("Available API endpoints:")
    for endpoint in api_endpoints:
        logger.info(f"  {endpoint}")
    
    logger.info("API endpoints are ready for testing with FastAPI server")

if __name__ == "__main__":
    # Run the performance monitoring system test
    asyncio.run(test_performance_monitoring_system())
    
    # Test API endpoints (informational)
    asyncio.run(test_api_endpoints())