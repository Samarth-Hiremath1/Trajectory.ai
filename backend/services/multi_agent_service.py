"""
Multi-Agent Service for initializing and managing the agent system
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any
import uuid

from services.ai_service import AIService, get_ai_service
from services.embedding_service import EmbeddingService, get_embedding_service
from services.agent_orchestrator_service import AgentOrchestratorService
from services.langgraph_workflow_orchestrator import LangGraphWorkflowOrchestrator
from services.career_strategy_agent import CareerStrategyAgent
from services.skills_analysis_agent import SkillsAnalysisAgent
from services.learning_resource_agent import LearningResourceAgent
from services.resume_optimization_agent import ResumeOptimizationAgent
from services.roadmap_scraper import RoadmapScraper
from models.agent import AgentType, AgentRequest, RequestType

logger = logging.getLogger(__name__)

class MultiAgentService:
    """
    Service for managing the multi-agent system including initialization,
    agent registration, and request processing coordination.
    """
    
    def __init__(self):
        """Initialize the multi-agent service"""
        self.ai_service: Optional[AIService] = None
        self.embedding_service: Optional[EmbeddingService] = None
        self.orchestrator: Optional[AgentOrchestratorService] = None
        self.langgraph_orchestrator: Optional[LangGraphWorkflowOrchestrator] = None
        
        # Agent instances
        self.agents: Dict[str, Any] = {}
        
        # Service status
        self.is_initialized = False
        self.is_running = False
        
        logger.info("Multi-Agent Service created")
    
    async def initialize(self) -> bool:
        """
        Initialize all services and agents
        
        Returns:
            True if initialization successful
        """
        try:
            logger.info("Initializing Multi-Agent Service...")
            
            # Initialize core services
            self.ai_service = await get_ai_service()
            self.embedding_service = get_embedding_service()
            
            # Initialize orchestrators
            self.orchestrator = AgentOrchestratorService(self.ai_service)
            self.langgraph_orchestrator = LangGraphWorkflowOrchestrator(self.ai_service)
            
            # Initialize Redis for LangGraph checkpointing
            await self.langgraph_orchestrator.initialize_redis()
            
            # Initialize and register agents
            await self._initialize_agents()
            
            self.is_initialized = True
            logger.info("Multi-Agent Service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Multi-Agent Service: {str(e)}")
            return False
    
    async def start(self) -> bool:
        """
        Start the multi-agent service
        
        Returns:
            True if started successfully
        """
        try:
            if not self.is_initialized:
                logger.error("Cannot start service - not initialized")
                return False
            
            # Start orchestrator
            await self.orchestrator.start()
            
            self.is_running = True
            logger.info("Multi-Agent Service started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Multi-Agent Service: {str(e)}")
            return False
    
    async def stop(self) -> bool:
        """
        Stop the multi-agent service
        
        Returns:
            True if stopped successfully
        """
        try:
            if self.orchestrator:
                await self.orchestrator.stop()
            
            self.is_running = False
            logger.info("Multi-Agent Service stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop Multi-Agent Service: {str(e)}")
            return False
    
    async def _initialize_agents(self):
        """Initialize and register all agents"""
        try:
            # Initialize Career Strategy Agent
            career_strategy_agent = CareerStrategyAgent(
                agent_id=f"career_strategy_{uuid.uuid4().hex[:8]}",
                ai_service=self.ai_service,
                embedding_service=self.embedding_service,
                max_concurrent_requests=3
            )
            
            # Register with orchestrators
            self.orchestrator.register_agent(career_strategy_agent)
            self.langgraph_orchestrator.register_agent(career_strategy_agent)
            self.agents[career_strategy_agent.agent_id] = career_strategy_agent
            
            logger.info(f"Initialized and registered Career Strategy Agent: {career_strategy_agent.agent_id}")
            
            # Initialize Learning Resource Agent
            roadmap_scraper = RoadmapScraper()
            learning_resource_agent = LearningResourceAgent(
                agent_id=f"learning_resource_{uuid.uuid4().hex[:8]}",
                ai_service=self.ai_service,
                embedding_service=self.embedding_service,
                roadmap_scraper=roadmap_scraper,
                max_concurrent_requests=3
            )
            
            # Register with orchestrators
            self.orchestrator.register_agent(learning_resource_agent)
            self.langgraph_orchestrator.register_agent(learning_resource_agent)
            self.agents[learning_resource_agent.agent_id] = learning_resource_agent
            
            logger.info(f"Initialized and registered Learning Resource Agent: {learning_resource_agent.agent_id}")
            
            # Initialize Skills Analysis Agent
            skills_analysis_agent = SkillsAnalysisAgent(
                agent_id=f"skills_analysis_{uuid.uuid4().hex[:8]}",
                ai_service=self.ai_service,
                embedding_service=self.embedding_service,
                max_concurrent_requests=3
            )
            
            # Register with orchestrators
            self.orchestrator.register_agent(skills_analysis_agent)
            self.langgraph_orchestrator.register_agent(skills_analysis_agent)
            self.agents[skills_analysis_agent.agent_id] = skills_analysis_agent
            
            logger.info(f"Initialized and registered Skills Analysis Agent: {skills_analysis_agent.agent_id}")
            
            # Initialize Resume Optimization Agent
            resume_optimization_agent = ResumeOptimizationAgent(
                agent_id=f"resume_optimization_{uuid.uuid4().hex[:8]}",
                ai_service=self.ai_service,
                embedding_service=self.embedding_service,
                max_concurrent_requests=3
            )
            
            # Register with orchestrators
            self.orchestrator.register_agent(resume_optimization_agent)
            self.langgraph_orchestrator.register_agent(resume_optimization_agent)
            self.agents[resume_optimization_agent.agent_id] = resume_optimization_agent
            
            logger.info(f"Initialized and registered Resume Optimization Agent: {resume_optimization_agent.agent_id}")
            
            # Initialize Career Mentor Agent
            from services.career_mentor_agent import CareerMentorAgent
            career_mentor_agent = CareerMentorAgent(
                agent_id="career_mentor_1",
                ai_service=self.ai_service,
                embedding_service=self.embedding_service
            )
            self.orchestrator.register_agent(career_mentor_agent)
            
            logger.info(f"Initialized and registered Career Mentor Agent: {career_mentor_agent.agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize agents: {str(e)}")
            raise
    
    async def process_request(
        self,
        user_id: str,
        request_type: RequestType,
        content: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a request through the multi-agent system
        
        Args:
            user_id: User identifier
            request_type: Type of request
            content: Request content
            context: Optional context
            
        Returns:
            Processing results
        """
        try:
            if not self.is_running:
                raise Exception("Multi-Agent Service is not running")
            
            # Create agent request
            agent_request = AgentRequest(
                user_id=user_id,
                request_type=request_type,
                content=content,
                context=context or {}
            )
            
            # Process through orchestrator
            result = await self.orchestrator.process_request(agent_request)
            
            logger.info(f"Processed request {agent_request.id} with result: {result.get('success', False)}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process request: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "request_id": None,
                "workflow_id": None,
                "responses": []
            }
    
    async def get_career_strategy_analysis(
        self,
        user_id: str,
        current_role: str,
        target_role: str,
        timeline: str = "12 months"
    ) -> Dict[str, Any]:
        """
        Get career strategy analysis for a transition
        
        Args:
            user_id: User identifier
            current_role: Current role
            target_role: Target role
            timeline: Desired timeline
            
        Returns:
            Career strategy analysis
        """
        content = {
            "current_role": current_role,
            "target_role": target_role,
            "user_id": user_id,
            "timeline": timeline
        }
        
        return await self.process_request(
            user_id=user_id,
            request_type=RequestType.CAREER_TRANSITION,
            content=content
        )
    
    async def generate_strategic_roadmap(
        self,
        user_id: str,
        current_role: str,
        target_role: str,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a strategic career roadmap
        
        Args:
            user_id: User identifier
            current_role: Current role
            target_role: Target role
            constraints: Optional constraints
            
        Returns:
            Strategic roadmap
        """
        content = {
            "current_role": current_role,
            "target_role": target_role,
            "user_id": user_id,
            "constraints": constraints or {}
        }
        
        return await self.process_request(
            user_id=user_id,
            request_type=RequestType.ROADMAP_GENERATION,
            content=content
        )
    
    async def get_strategic_career_advice(
        self,
        user_id: str,
        question: str
    ) -> Dict[str, Any]:
        """
        Get strategic career advice
        
        Args:
            user_id: User identifier
            question: Career question
            
        Returns:
            Strategic career advice
        """
        content = {
            "question": question,
            "user_id": user_id
        }
        
        return await self.process_request(
            user_id=user_id,
            request_type=RequestType.CAREER_ADVICE,
            content=content
        )
    
    async def create_personalized_learning_path(
        self,
        user_id: str,
        skills_to_learn: List[str],
        learning_style: str = "mixed",
        timeline: str = "3 months",
        budget: str = "flexible",
        current_level: str = "beginner"
    ) -> Dict[str, Any]:
        """
        Create a personalized learning path
        
        Args:
            user_id: User identifier
            skills_to_learn: List of skills to learn
            learning_style: Preferred learning style
            timeline: Available timeline
            budget: Budget constraints
            current_level: Current skill level
            
        Returns:
            Personalized learning path
        """
        content = {
            "user_id": user_id,
            "skills_to_learn": skills_to_learn,
            "learning_style": learning_style,
            "timeline": timeline,
            "budget": budget,
            "current_level": current_level
        }
        
        return await self.process_request(
            user_id=user_id,
            request_type=RequestType.LEARNING_PATH,
            content=content
        )
    
    async def get_learning_resource_recommendations(
        self,
        user_id: str,
        skills_needed: List[str],
        skill_gaps: Optional[Dict[str, Any]] = None,
        priority_skills: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get learning resource recommendations for specific skills
        
        Args:
            user_id: User identifier
            skills_needed: List of skills needing resources
            skill_gaps: Optional skill gap analysis
            priority_skills: Optional priority skills list
            
        Returns:
            Learning resource recommendations
        """
        content = {
            "user_id": user_id,
            "skills_needed": skills_needed,
            "skill_gaps": skill_gaps or {},
            "priority_skills": priority_skills or []
        }
        
        return await self.process_request(
            user_id=user_id,
            request_type=RequestType.SKILL_ANALYSIS,
            content=content
        )
    
    async def get_learning_resource_advice(
        self,
        user_id: str,
        question: str
    ) -> Dict[str, Any]:
        """
        Get learning resource advice for general queries
        
        Args:
            user_id: User identifier
            question: Learning-related question
            
        Returns:
            Learning resource advice
        """
        content = {
            "question": question,
            "user_id": user_id
        }
        
        return await self.process_request(
            user_id=user_id,
            request_type=RequestType.LEARNING_PATH,
            content=content
        )
    
    # LangGraph Workflow Methods
    
    async def execute_career_transition_workflow(
        self,
        user_id: str,
        current_role: str,
        target_role: str,
        timeline: str = "12 months",
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute comprehensive career transition workflow using LangGraph
        
        Args:
            user_id: User identifier
            current_role: Current role
            target_role: Target role
            timeline: Desired timeline
            constraints: Optional constraints
            
        Returns:
            Comprehensive career transition analysis
        """
        if not self.langgraph_orchestrator:
            raise Exception("LangGraph orchestrator not initialized")
        
        content = {
            "current_role": current_role,
            "target_role": target_role,
            "user_id": user_id,
            "timeline": timeline,
            "constraints": constraints or {}
        }
        
        return await self.langgraph_orchestrator.execute_workflow(
            workflow_name="career_transition",
            user_id=user_id,
            request_type=RequestType.CAREER_TRANSITION,
            request_content=content
        )
    
    async def execute_roadmap_enhancement_workflow(
        self,
        user_id: str,
        existing_roadmap: Dict[str, Any],
        enhancement_goals: List[str]
    ) -> Dict[str, Any]:
        """
        Execute roadmap enhancement workflow using LangGraph
        
        Args:
            user_id: User identifier
            existing_roadmap: Existing roadmap to enhance
            enhancement_goals: Goals for enhancement
            
        Returns:
            Enhanced roadmap
        """
        if not self.langgraph_orchestrator:
            raise Exception("LangGraph orchestrator not initialized")
        
        content = {
            "existing_roadmap": existing_roadmap,
            "enhancement_goals": enhancement_goals,
            "user_id": user_id
        }
        
        return await self.langgraph_orchestrator.execute_workflow(
            workflow_name="roadmap_enhancement",
            user_id=user_id,
            request_type=RequestType.ROADMAP_GENERATION,
            request_content=content
        )
    
    async def execute_comprehensive_analysis_workflow(
        self,
        user_id: str,
        analysis_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute comprehensive analysis workflow using LangGraph
        
        Args:
            user_id: User identifier
            analysis_request: Analysis request details
            
        Returns:
            Comprehensive analysis results
        """
        if not self.langgraph_orchestrator:
            raise Exception("LangGraph orchestrator not initialized")
        
        return await self.langgraph_orchestrator.execute_workflow(
            workflow_name="comprehensive_analysis",
            user_id=user_id,
            request_type=RequestType.CAREER_ADVICE,
            request_content=analysis_request
        )
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get status of a running LangGraph workflow
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Workflow status information
        """
        if not self.langgraph_orchestrator:
            raise Exception("LangGraph orchestrator not initialized")
        
        return await self.langgraph_orchestrator.get_workflow_status(workflow_id)
    
    async def resume_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Resume a workflow from checkpoint
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Workflow resumption results
        """
        if not self.langgraph_orchestrator:
            raise Exception("LangGraph orchestrator not initialized")
        
        return await self.langgraph_orchestrator.resume_workflow(workflow_id)
    
    def get_available_workflows(self) -> List[str]:
        """
        Get list of available LangGraph workflows
        
        Returns:
            List of workflow names
        """
        if not self.langgraph_orchestrator:
            return []
        
        return self.langgraph_orchestrator.get_available_workflows()
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get service status and metrics
        
        Returns:
            Service status information
        """
        status = {
            "initialized": self.is_initialized,
            "running": self.is_running,
            "agents_count": len(self.agents),
            "agents": {
                agent_id: {
                    "type": agent.agent_type.value,
                    "status": agent.get_status().model_dump() if hasattr(agent, 'get_status') else "unknown"
                }
                for agent_id, agent in self.agents.items()
            }
        }
        
        if self.orchestrator:
            status["orchestrator"] = self.orchestrator.get_status()
        
        return status
    
    def get_available_agents(self) -> List[Dict[str, Any]]:
        """
        Get list of available agents and their capabilities
        
        Returns:
            List of agent information
        """
        agents_info = []
        
        for agent_id, agent in self.agents.items():
            agent_info = {
                "id": agent_id,
                "type": agent.agent_type.value,
                "capabilities": [cap.model_dump() for cap in agent.capabilities] if hasattr(agent, 'capabilities') else [],
                "status": agent.get_status().model_dump() if hasattr(agent, 'get_status') else {}
            }
            agents_info.append(agent_info)
        
        return agents_info
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all services
        
        Returns:
            Health check results
        """
        health_status = {
            "service_status": "healthy" if self.is_running else "unhealthy",
            "initialized": self.is_initialized,
            "running": self.is_running
        }
        
        # Check AI service
        if self.ai_service:
            try:
                ai_health = await self.ai_service.health_check()
                health_status["ai_service"] = ai_health
            except Exception as e:
                health_status["ai_service"] = {"status": "unhealthy", "error": str(e)}
        
        # Check embedding service
        if self.embedding_service:
            try:
                embedding_health = self.embedding_service.health_check()
                health_status["embedding_service"] = embedding_health
            except Exception as e:
                health_status["embedding_service"] = {"status": "unhealthy", "error": str(e)}
        
        # Check LangGraph orchestrator
        if self.langgraph_orchestrator:
            try:
                langgraph_health = await self.langgraph_orchestrator.health_check()
                health_status["langgraph_orchestrator"] = langgraph_health
            except Exception as e:
                health_status["langgraph_orchestrator"] = {"status": "unhealthy", "error": str(e)}
        
        # Check agents
        agent_health = {}
        for agent_id, agent in self.agents.items():
            try:
                agent_status = agent.get_status()
                agent_health[agent_id] = {
                    "status": "healthy" if agent_status.is_active else "inactive",
                    "load": agent_status.current_load,
                    "performance": agent_status.performance_metrics
                }
            except Exception as e:
                agent_health[agent_id] = {"status": "unhealthy", "error": str(e)}
        
        health_status["agents"] = agent_health
        
        return health_status

# Singleton instance
_multi_agent_service_instance: Optional[MultiAgentService] = None

async def get_multi_agent_service() -> MultiAgentService:
    """
    Get or create singleton multi-agent service instance
    
    Returns:
        MultiAgentService instance
    """
    global _multi_agent_service_instance
    
    if _multi_agent_service_instance is None:
        _multi_agent_service_instance = MultiAgentService()
        
        # Initialize if not already done
        if not _multi_agent_service_instance.is_initialized:
            await _multi_agent_service_instance.initialize()
        
        # Start if not already running
        if not _multi_agent_service_instance.is_running:
            await _multi_agent_service_instance.start()
    
    return _multi_agent_service_instance

async def cleanup_multi_agent_service():
    """Cleanup singleton service instance"""
    global _multi_agent_service_instance
    
    if _multi_agent_service_instance:
        await _multi_agent_service_instance.stop()
        _multi_agent_service_instance = None