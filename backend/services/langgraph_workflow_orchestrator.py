"""
LangGraph Multi-Agent Workflow Orchestrator
Manages complex workflows involving multiple specialized agents with state persistence
"""
import logging
import json
import asyncio
from typing import Dict, List, Optional, Any, Union, TypedDict, Annotated
from datetime import datetime
import uuid

from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

# Optional Redis imports for checkpointing
try:
    from langgraph_checkpoint.redis import RedisSaver
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    RedisSaver = None
    redis = None
    REDIS_AVAILABLE = False

from models.agent import (
    AgentType, AgentRequest, AgentResponse, RequestType, 
    WorkflowStatus, AgentWorkflow
)
from services.base_agent import BaseAgent
from services.career_strategy_agent import CareerStrategyAgent
from services.skills_analysis_agent import SkillsAnalysisAgent
from services.learning_resource_agent import LearningResourceAgent
from services.resume_optimization_agent import ResumeOptimizationAgent
from services.ai_service import AIService

logger = logging.getLogger(__name__)

class WorkflowState(TypedDict):
    """State schema for LangGraph workflows"""
    # Input data
    user_id: str
    request_type: str
    request_content: Dict[str, Any]
    
    # Workflow metadata
    workflow_id: str
    current_step: str
    steps_completed: List[str]
    
    # Agent outputs
    career_strategy_output: Optional[Dict[str, Any]]
    skills_analysis_output: Optional[Dict[str, Any]]
    learning_resources_output: Optional[Dict[str, Any]]
    
    # Final results
    final_response: Optional[Dict[str, Any]]
    error_messages: List[str]
    
    # Workflow control
    should_continue: bool
    retry_count: int

class LangGraphWorkflowOrchestrator:
    """
    LangGraph-powered workflow orchestrator for multi-agent coordination
    """
    
    def __init__(
        self,
        ai_service: AIService,
        redis_url: str = "redis://localhost:6379",
        max_retries: int = 3
    ):
        """
        Initialize LangGraph workflow orchestrator
        
        Args:
            ai_service: AI service for LLM interactions
            redis_url: Redis connection URL for checkpointing
            max_retries: Maximum retry attempts for failed steps
        """
        self.ai_service = ai_service
        self.redis_url = redis_url
        self.max_retries = max_retries
        
        # Agent instances (will be set by the multi-agent service)
        self.agents: Dict[AgentType, BaseAgent] = {}
        
        # Redis checkpointer for state persistence
        self.checkpointer = None
        
        # Workflow graphs
        self.workflows: Dict[str, StateGraph] = {}
        
        # RAG integration
        self.rag_service = None
        self.embedding_service = None
        
        # Initialize workflows
        self._initialize_workflows()
        
        logger.info("LangGraph Workflow Orchestrator initialized")
    
    async def initialize_redis(self):
        """Initialize Redis connection for checkpointing"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis checkpointing not available - missing dependencies")
            return
            
        try:
            redis_client = redis.from_url(self.redis_url)
            self.checkpointer = RedisSaver(redis_client)
            logger.info(f"Redis checkpointer initialized: {self.redis_url}")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis checkpointer: {str(e)}")
            logger.warning("Workflows will run without state persistence")
    
    def initialize_rag_services(self, rag_service=None, embedding_service=None):
        """Initialize RAG services for enhanced context awareness"""
        self.rag_service = rag_service
        self.embedding_service = embedding_service
        
        if self.rag_service:
            logger.info("RAG service integrated with workflow orchestrator")
        if self.embedding_service:
            logger.info("Embedding service integrated with workflow orchestrator")
    
    async def _enhance_request_with_rag_context(
        self, 
        user_id: str, 
        request_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance request content with RAG-retrieved context"""
        enhanced_content = request_content.copy()
        
        if not self.embedding_service:
            return enhanced_content
        
        try:
            # Extract query from request content
            query_parts = []
            if "user_message" in request_content:
                query_parts.append(request_content["user_message"])
            if "current_role" in request_content:
                query_parts.append(request_content["current_role"])
            if "target_role" in request_content:
                query_parts.append(request_content["target_role"])
            
            query = " ".join(query_parts)
            
            # Retrieve user context
            context_chunks = self.embedding_service.search_user_context(
                user_id=user_id,
                query=query,
                n_results=5
            )
            
            if context_chunks:
                # Group context by source
                resume_context = []
                profile_context = []
                
                for chunk in context_chunks:
                    if chunk.get("source") == "resume":
                        resume_context.append(chunk["content"])
                    elif chunk.get("source") == "profile":
                        profile_context.append(chunk["content"])
                
                # Add context to enhanced content
                if resume_context:
                    enhanced_content["rag_resume_context"] = " ".join(resume_context)
                if profile_context:
                    enhanced_content["rag_profile_context"] = " ".join(profile_context)
                
                enhanced_content["rag_context_available"] = True
                logger.info(f"Enhanced request with RAG context for user {user_id}")
            
        except Exception as e:
            logger.warning(f"Failed to enhance request with RAG context: {e}")
            enhanced_content["rag_context_available"] = False
        
        return enhanced_content
    
    def register_agent(self, agent: BaseAgent):
        """Register an agent with the orchestrator"""
        self.agents[agent.agent_type] = agent
        logger.info(f"Registered agent {agent.agent_type.value} with workflow orchestrator")
    
    def _initialize_workflows(self):
        """Initialize all workflow graphs"""
        # Career Transition Workflow
        self.workflows["career_transition"] = self._create_career_transition_workflow()
        
        # Roadmap Enhancement Workflow
        self.workflows["roadmap_enhancement"] = self._create_roadmap_enhancement_workflow()
        
        # Comprehensive Analysis Workflow
        self.workflows["comprehensive_analysis"] = self._create_comprehensive_analysis_workflow()
        
        logger.info(f"Initialized {len(self.workflows)} LangGraph workflows")
    
    def _create_career_transition_workflow(self) -> StateGraph:
        """
        Create career transition workflow that coordinates multiple agents
        """
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_workflow)
        workflow.add_node("career_strategy", self._execute_career_strategy_agent)
        workflow.add_node("skills_analysis", self._execute_skills_analysis_agent)
        workflow.add_node("learning_resources", self._execute_learning_resources_agent)
        workflow.add_node("synthesize_results", self._synthesize_career_transition_results)
        workflow.add_node("handle_error", self._handle_workflow_error)
        
        # Define workflow edges
        workflow.add_edge(START, "initialize")
        workflow.add_conditional_edges(
            "initialize",
            self._should_continue_workflow,
            {
                "continue": "career_strategy",
                "error": "handle_error"
            }
        )
        workflow.add_conditional_edges(
            "career_strategy",
            self._should_continue_workflow,
            {
                "continue": "skills_analysis",
                "retry": "career_strategy",
                "error": "handle_error"
            }
        )
        workflow.add_conditional_edges(
            "skills_analysis",
            self._should_continue_workflow,
            {
                "continue": "learning_resources",
                "retry": "skills_analysis",
                "error": "handle_error"
            }
        )
        workflow.add_conditional_edges(
            "learning_resources",
            self._should_continue_workflow,
            {
                "continue": "synthesize_results",
                "retry": "learning_resources",
                "error": "handle_error"
            }
        )
        workflow.add_edge("synthesize_results", END)
        workflow.add_edge("handle_error", END)
        
        return workflow
    
    def _create_roadmap_enhancement_workflow(self) -> StateGraph:
        """
        Create roadmap enhancement workflow for improving existing roadmaps
        """
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_workflow)
        workflow.add_node("analyze_existing_roadmap", self._analyze_existing_roadmap)
        workflow.add_node("enhance_strategy", self._enhance_roadmap_strategy)
        workflow.add_node("update_skills_assessment", self._update_skills_assessment)
        workflow.add_node("refresh_learning_resources", self._refresh_learning_resources)
        workflow.add_node("synthesize_enhancements", self._synthesize_roadmap_enhancements)
        workflow.add_node("handle_error", self._handle_workflow_error)
        
        # Define workflow edges
        workflow.add_edge(START, "initialize")
        workflow.add_conditional_edges(
            "initialize",
            self._should_continue_workflow,
            {
                "continue": "analyze_existing_roadmap",
                "error": "handle_error"
            }
        )
        workflow.add_conditional_edges(
            "analyze_existing_roadmap",
            self._should_continue_workflow,
            {
                "continue": "enhance_strategy",
                "retry": "analyze_existing_roadmap",
                "error": "handle_error"
            }
        )
        workflow.add_conditional_edges(
            "enhance_strategy",
            self._should_continue_workflow,
            {
                "continue": "update_skills_assessment",
                "retry": "enhance_strategy",
                "error": "handle_error"
            }
        )
        workflow.add_conditional_edges(
            "update_skills_assessment",
            self._should_continue_workflow,
            {
                "continue": "refresh_learning_resources",
                "retry": "update_skills_assessment",
                "error": "handle_error"
            }
        )
        workflow.add_conditional_edges(
            "refresh_learning_resources",
            self._should_continue_workflow,
            {
                "continue": "synthesize_enhancements",
                "retry": "refresh_learning_resources",
                "error": "handle_error"
            }
        )
        workflow.add_edge("synthesize_enhancements", END)
        workflow.add_edge("handle_error", END)
        
        return workflow
    
    def _create_comprehensive_analysis_workflow(self) -> StateGraph:
        """
        Create comprehensive analysis workflow for complex user requests
        """
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_workflow)
        workflow.add_node("parallel_analysis", self._execute_parallel_agent_analysis)
        workflow.add_node("cross_validate_results", self._cross_validate_agent_results)
        workflow.add_node("synthesize_comprehensive_response", self._synthesize_comprehensive_response)
        workflow.add_node("handle_error", self._handle_workflow_error)
        
        # Define workflow edges
        workflow.add_edge(START, "initialize")
        workflow.add_conditional_edges(
            "initialize",
            self._should_continue_workflow,
            {
                "continue": "parallel_analysis",
                "error": "handle_error"
            }
        )
        workflow.add_conditional_edges(
            "parallel_analysis",
            self._should_continue_workflow,
            {
                "continue": "cross_validate_results",
                "retry": "parallel_analysis",
                "error": "handle_error"
            }
        )
        workflow.add_conditional_edges(
            "cross_validate_results",
            self._should_continue_workflow,
            {
                "continue": "synthesize_comprehensive_response",
                "retry": "cross_validate_results",
                "error": "handle_error"
            }
        )
        workflow.add_edge("synthesize_comprehensive_response", END)
        workflow.add_edge("handle_error", END)
        
        return workflow
    
    async def execute_workflow(
        self,
        workflow_name: str,
        user_id: str,
        request_type: RequestType,
        request_content: Dict[str, Any],
        config: Optional[RunnableConfig] = None
    ) -> Dict[str, Any]:
        """
        Execute a specific workflow
        
        Args:
            workflow_name: Name of the workflow to execute
            user_id: User identifier
            request_type: Type of request
            request_content: Request content
            config: Optional runnable configuration
            
        Returns:
            Workflow execution results
        """
        try:
            if workflow_name not in self.workflows:
                raise ValueError(f"Unknown workflow: {workflow_name}")
            
            workflow = self.workflows[workflow_name]
            
            # Compile workflow with checkpointer if available
            if self.checkpointer:
                compiled_workflow = workflow.compile(checkpointer=self.checkpointer)
            else:
                compiled_workflow = workflow.compile()
            
            # Enhance request content with RAG context
            enhanced_request_content = await self._enhance_request_with_rag_context(
                user_id, request_content
            )
            
            # Initialize workflow state
            initial_state = WorkflowState(
                user_id=user_id,
                request_type=request_type.value,
                request_content=enhanced_request_content,
                workflow_id=str(uuid.uuid4()),
                current_step="initialize",
                steps_completed=[],
                career_strategy_output=None,
                skills_analysis_output=None,
                learning_resources_output=None,
                final_response=None,
                error_messages=[],
                should_continue=True,
                retry_count=0
            )
            
            # Execute workflow
            logger.info(f"Executing workflow '{workflow_name}' for user {user_id}")
            
            if config is None:
                config = {"configurable": {"thread_id": initial_state["workflow_id"]}}
            
            final_state = await compiled_workflow.ainvoke(initial_state, config=config)
            
            logger.info(f"Workflow '{workflow_name}' completed for user {user_id}")
            
            return {
                "success": True,
                "workflow_id": final_state["workflow_id"],
                "final_response": final_state["final_response"],
                "steps_completed": final_state["steps_completed"],
                "error_messages": final_state["error_messages"]
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "workflow_id": None,
                "final_response": None,
                "steps_completed": [],
                "error_messages": [str(e)]
            }
    
    # Workflow node implementations
    async def _initialize_workflow(self, state: WorkflowState) -> WorkflowState:
        """Initialize workflow state and validate inputs"""
        try:
            logger.info(f"Initializing workflow {state['workflow_id']}")
            
            # Validate required inputs
            if not state["user_id"]:
                raise ValueError("User ID is required")
            
            if not state["request_content"]:
                raise ValueError("Request content is required")
            
            # Update state
            state["current_step"] = "initialize"
            state["steps_completed"].append("initialize")
            state["should_continue"] = True
            
            return state
            
        except Exception as e:
            logger.error(f"Workflow initialization failed: {str(e)}")
            state["error_messages"].append(f"Initialization error: {str(e)}")
            state["should_continue"] = False
            return state
    
    async def _execute_career_strategy_agent(self, state: WorkflowState) -> WorkflowState:
        """Execute Career Strategy Agent"""
        try:
            logger.info(f"Executing Career Strategy Agent for workflow {state['workflow_id']}")
            
            if AgentType.CAREER_STRATEGY not in self.agents:
                raise ValueError("Career Strategy Agent not available")
            
            agent = self.agents[AgentType.CAREER_STRATEGY]
            
            # Create agent request
            agent_request = AgentRequest(
                user_id=state["user_id"],
                request_type=RequestType(state["request_type"]),
                content=state["request_content"],
                context={}
            )
            
            # Execute agent
            response = await agent.handle_request(agent_request)
            
            # Store results
            state["career_strategy_output"] = response.response_content
            state["current_step"] = "career_strategy"
            state["steps_completed"].append("career_strategy")
            state["retry_count"] = 0
            
            return state
            
        except Exception as e:
            logger.error(f"Career Strategy Agent execution failed: {str(e)}")
            state["error_messages"].append(f"Career Strategy error: {str(e)}")
            state["retry_count"] += 1
            return state
    
    async def _execute_skills_analysis_agent(self, state: WorkflowState) -> WorkflowState:
        """Execute Skills Analysis Agent"""
        try:
            logger.info(f"Executing Skills Analysis Agent for workflow {state['workflow_id']}")
            
            if AgentType.SKILLS_ANALYSIS not in self.agents:
                raise ValueError("Skills Analysis Agent not available")
            
            agent = self.agents[AgentType.SKILLS_ANALYSIS]
            
            # Enhance request content with career strategy output
            enhanced_content = state["request_content"].copy()
            if state["career_strategy_output"]:
                enhanced_content["career_strategy_context"] = state["career_strategy_output"]
            
            # Create agent request
            agent_request = AgentRequest(
                user_id=state["user_id"],
                request_type=RequestType.SKILL_ANALYSIS,
                content=enhanced_content,
                context={}
            )
            
            # Execute agent
            response = await agent.handle_request(agent_request)
            
            # Store results
            state["skills_analysis_output"] = response.response_content
            state["current_step"] = "skills_analysis"
            state["steps_completed"].append("skills_analysis")
            state["retry_count"] = 0
            
            return state
            
        except Exception as e:
            logger.error(f"Skills Analysis Agent execution failed: {str(e)}")
            state["error_messages"].append(f"Skills Analysis error: {str(e)}")
            state["retry_count"] += 1
            return state
    
    async def _execute_learning_resources_agent(self, state: WorkflowState) -> WorkflowState:
        """Execute Learning Resources Agent"""
        try:
            logger.info(f"Executing Learning Resources Agent for workflow {state['workflow_id']}")
            
            if AgentType.LEARNING_RESOURCE not in self.agents:
                raise ValueError("Learning Resources Agent not available")
            
            agent = self.agents[AgentType.LEARNING_RESOURCE]
            
            # Enhance request content with previous agent outputs
            enhanced_content = state["request_content"].copy()
            if state["career_strategy_output"]:
                enhanced_content["career_strategy_context"] = state["career_strategy_output"]
            if state["skills_analysis_output"]:
                enhanced_content["skills_analysis_context"] = state["skills_analysis_output"]
            
            # Create agent request
            agent_request = AgentRequest(
                user_id=state["user_id"],
                request_type=RequestType.LEARNING_PATH,
                content=enhanced_content,
                context={}
            )
            
            # Execute agent
            response = await agent.handle_request(agent_request)
            
            # Store results
            state["learning_resources_output"] = response.response_content
            state["current_step"] = "learning_resources"
            state["steps_completed"].append("learning_resources")
            state["retry_count"] = 0
            
            return state
            
        except Exception as e:
            logger.error(f"Learning Resources Agent execution failed: {str(e)}")
            state["error_messages"].append(f"Learning Resources error: {str(e)}")
            state["retry_count"] += 1
            return state
    
    async def _synthesize_career_transition_results(self, state: WorkflowState) -> WorkflowState:
        """Synthesize results from all agents into final response"""
        try:
            logger.info(f"Synthesizing career transition results for workflow {state['workflow_id']}")
            
            # Combine all agent outputs
            final_response = {
                "workflow_type": "career_transition",
                "user_id": state["user_id"],
                "request_content": state["request_content"],
                "career_strategy": state["career_strategy_output"],
                "skills_analysis": state["skills_analysis_output"],
                "learning_resources": state["learning_resources_output"],
                "synthesis": await self._generate_synthesis_summary(state),
                "workflow_metadata": {
                    "workflow_id": state["workflow_id"],
                    "steps_completed": state["steps_completed"],
                    "execution_time": datetime.utcnow().isoformat()
                }
            }
            
            state["final_response"] = final_response
            state["current_step"] = "synthesize_results"
            state["steps_completed"].append("synthesize_results")
            
            return state
            
        except Exception as e:
            logger.error(f"Result synthesis failed: {str(e)}")
            state["error_messages"].append(f"Synthesis error: {str(e)}")
            state["should_continue"] = False
            return state
    
    async def _generate_synthesis_summary(self, state: WorkflowState) -> str:
        """Generate AI-powered synthesis summary of all agent outputs"""
        try:
            synthesis_prompt = f"""
            Synthesize the following multi-agent analysis into a cohesive career transition summary:
            
            CAREER STRATEGY OUTPUT:
            {json.dumps(state["career_strategy_output"], indent=2)}
            
            SKILLS ANALYSIS OUTPUT:
            {json.dumps(state["skills_analysis_output"], indent=2)}
            
            LEARNING RESOURCES OUTPUT:
            {json.dumps(state["learning_resources_output"], indent=2)}
            
            Please provide a comprehensive synthesis that:
            1. Highlights key insights from each agent
            2. Identifies synergies and connections between recommendations
            3. Provides a unified action plan
            4. Addresses any conflicting recommendations
            5. Gives clear next steps for the user
            
            Focus on creating a cohesive narrative that leverages the specialized expertise of each agent.
            """
            
            synthesis = await self.ai_service.generate_text(
                prompt=synthesis_prompt,
                max_tokens=800,
                temperature=0.7
            )
            
            return synthesis
            
        except Exception as e:
            logger.error(f"Synthesis generation failed: {str(e)}")
            return f"Synthesis generation failed: {str(e)}"
    
    def _should_continue_workflow(self, state: WorkflowState) -> str:
        """Determine if workflow should continue, retry, or handle error"""
        if not state["should_continue"]:
            return "error"
        
        if state["retry_count"] > 0 and state["retry_count"] < self.max_retries:
            return "retry"
        
        if state["retry_count"] >= self.max_retries:
            return "error"
        
        return "continue"
    
    async def _handle_workflow_error(self, state: WorkflowState) -> WorkflowState:
        """Handle workflow errors and create error response"""
        logger.error(f"Handling workflow error for {state['workflow_id']}: {state['error_messages']}")
        
        state["final_response"] = {
            "workflow_type": "error",
            "user_id": state["user_id"],
            "error": True,
            "error_messages": state["error_messages"],
            "steps_completed": state["steps_completed"],
            "partial_results": {
                "career_strategy": state["career_strategy_output"],
                "skills_analysis": state["skills_analysis_output"],
                "learning_resources": state["learning_resources_output"]
            }
        }
        
        state["current_step"] = "error_handled"
        state["steps_completed"].append("error_handled")
        
        return state
    
    # Placeholder implementations for roadmap enhancement workflow
    async def _analyze_existing_roadmap(self, state: WorkflowState) -> WorkflowState:
        """Analyze existing roadmap for enhancement opportunities"""
        # Implementation would analyze the existing roadmap
        state["current_step"] = "analyze_existing_roadmap"
        state["steps_completed"].append("analyze_existing_roadmap")
        return state
    
    async def _enhance_roadmap_strategy(self, state: WorkflowState) -> WorkflowState:
        """Enhance roadmap strategy using Career Strategy Agent"""
        # Implementation would enhance strategy
        state["current_step"] = "enhance_strategy"
        state["steps_completed"].append("enhance_strategy")
        return state
    
    async def _update_skills_assessment(self, state: WorkflowState) -> WorkflowState:
        """Update skills assessment using Skills Analysis Agent"""
        # Implementation would update skills assessment
        state["current_step"] = "update_skills_assessment"
        state["steps_completed"].append("update_skills_assessment")
        return state
    
    async def _refresh_learning_resources(self, state: WorkflowState) -> WorkflowState:
        """Refresh learning resources using Learning Resources Agent"""
        # Implementation would refresh resources
        state["current_step"] = "refresh_learning_resources"
        state["steps_completed"].append("refresh_learning_resources")
        return state
    
    async def _synthesize_roadmap_enhancements(self, state: WorkflowState) -> WorkflowState:
        """Synthesize roadmap enhancements"""
        # Implementation would synthesize enhancements
        state["final_response"] = {"enhanced_roadmap": "Enhanced roadmap content"}
        state["current_step"] = "synthesize_enhancements"
        state["steps_completed"].append("synthesize_enhancements")
        return state
    
    # Placeholder implementations for comprehensive analysis workflow
    async def _execute_parallel_agent_analysis(self, state: WorkflowState) -> WorkflowState:
        """Execute all agents in parallel for comprehensive analysis"""
        # Implementation would run agents in parallel
        state["current_step"] = "parallel_analysis"
        state["steps_completed"].append("parallel_analysis")
        return state
    
    async def _cross_validate_agent_results(self, state: WorkflowState) -> WorkflowState:
        """Cross-validate results from different agents"""
        # Implementation would cross-validate results
        state["current_step"] = "cross_validate_results"
        state["steps_completed"].append("cross_validate_results")
        return state
    
    async def _synthesize_comprehensive_response(self, state: WorkflowState) -> WorkflowState:
        """Synthesize comprehensive response from all agents"""
        # Implementation would synthesize comprehensive response
        state["final_response"] = {"comprehensive_analysis": "Comprehensive analysis content"}
        state["current_step"] = "synthesize_comprehensive_response"
        state["steps_completed"].append("synthesize_comprehensive_response")
        return state
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get status of a running workflow"""
        try:
            if not self.checkpointer:
                return {"error": "Checkpointing not available"}
            
            # This would retrieve workflow status from Redis
            # Implementation depends on LangGraph's checkpoint API
            return {
                "workflow_id": workflow_id,
                "status": "running",
                "current_step": "unknown",
                "steps_completed": []
            }
            
        except Exception as e:
            logger.error(f"Failed to get workflow status: {str(e)}")
            return {"error": str(e)}
    
    async def resume_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Resume a workflow from checkpoint"""
        try:
            if not self.checkpointer:
                return {"error": "Checkpointing not available"}
            
            # This would resume workflow from Redis checkpoint
            # Implementation depends on LangGraph's checkpoint API
            return {
                "workflow_id": workflow_id,
                "resumed": True,
                "message": "Workflow resumed from checkpoint"
            }
            
        except Exception as e:
            logger.error(f"Failed to resume workflow: {str(e)}")
            return {"error": str(e)}
    
    def get_available_workflows(self) -> List[str]:
        """Get list of available workflow names"""
        return list(self.workflows.keys())
    
    def create_workflow_template(self, template_name: str, request_pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Create a workflow template for common user request patterns"""
        templates = {
            "career_transition_analysis": {
                "workflow": "career_transition",
                "description": "Comprehensive analysis for career transitions",
                "typical_request_types": [RequestType.CAREER_TRANSITION, RequestType.ROADMAP_GENERATION],
                "expected_outputs": ["career_strategy", "skills_analysis", "learning_resources"],
                "processing_time_estimate": "30-60 seconds"
            },
            "skill_gap_assessment": {
                "workflow": "comprehensive_analysis",
                "description": "Detailed skill gap analysis and development recommendations",
                "typical_request_types": [RequestType.SKILL_ANALYSIS, RequestType.LEARNING_PATH],
                "expected_outputs": ["skills_analysis", "learning_resources"],
                "processing_time_estimate": "20-40 seconds"
            },
            "roadmap_optimization": {
                "workflow": "roadmap_enhancement",
                "description": "Enhancement and optimization of existing roadmaps",
                "typical_request_types": [RequestType.ROADMAP_GENERATION],
                "expected_outputs": ["enhanced_roadmap", "updated_timeline"],
                "processing_time_estimate": "25-45 seconds"
            },
            "comprehensive_career_guidance": {
                "workflow": "comprehensive_analysis",
                "description": "Multi-faceted career guidance using all available agents",
                "typical_request_types": [RequestType.CAREER_ADVICE, RequestType.CAREER_TRANSITION],
                "expected_outputs": ["career_strategy", "skills_analysis", "learning_resources", "synthesis"],
                "processing_time_estimate": "45-90 seconds"
            }
        }
        
        return templates.get(template_name, {})
    
    def get_workflow_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get all available workflow templates"""
        template_names = [
            "career_transition_analysis",
            "skill_gap_assessment", 
            "roadmap_optimization",
            "comprehensive_career_guidance"
        ]
        
        return {name: self.create_workflow_template(name, {}) for name in template_names}
    
    async def execute_template_workflow(
        self,
        template_name: str,
        user_id: str,
        request_content: Dict[str, Any],
        config: Optional[RunnableConfig] = None
    ) -> Dict[str, Any]:
        """Execute a workflow using a predefined template"""
        template = self.create_workflow_template(template_name, {})
        
        if not template:
            return {
                "success": False,
                "error": f"Unknown workflow template: {template_name}",
                "available_templates": list(self.get_workflow_templates().keys())
            }
        
        # Map template to actual workflow and request type
        workflow_name = template["workflow"]
        request_type = template["typical_request_types"][0]  # Use first typical type
        
        # Execute the workflow
        return await self.execute_workflow(
            workflow_name=workflow_name,
            user_id=user_id,
            request_type=request_type,
            request_content=request_content,
            config=config
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the workflow orchestrator"""
        return {
            "status": "healthy",
            "workflows_available": len(self.workflows),
            "workflow_names": list(self.workflows.keys()),
            "workflow_templates": len(self.get_workflow_templates()),
            "agents_registered": len(self.agents),
            "redis_available": self.checkpointer is not None,
            "redis_url": self.redis_url if self.checkpointer else None
        }