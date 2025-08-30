"""
Career Mentor Agent for personalized career coaching and guidance
"""
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from models.agent import (
    AgentType, AgentRequest, AgentResponse, AgentCapability, 
    MessageType, RequestType
)
from services.base_agent import BaseAgent
from services.ai_service import AIService, ModelType
from services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class CareerMentorAgent(BaseAgent):
    """
    Specialized agent for personalized career coaching and mentoring.
    Provides mock interviews, motivational support, career experiments, and decision-making facilitation.
    """
    
    def __init__(
        self,
        agent_id: str,
        ai_service: AIService,
        embedding_service: EmbeddingService,
        max_concurrent_requests: int = 3
    ):
        """Initialize Career Mentor Agent"""
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.CAREER_MENTOR,
            ai_service=ai_service,
            max_concurrent_requests=max_concurrent_requests,
            default_confidence_threshold=0.8
        )
        
        self.embedding_service = embedding_service
        self._register_message_handlers()
        
        logger.info(f"Career Mentor Agent {agent_id} initialized")
    
    def _define_capabilities(self) -> List[AgentCapability]:
        """Define the capabilities of the Career Mentor Agent"""
        return [
            AgentCapability(
                name="career_coaching",
                description="Provide personalized career coaching and guidance",
                input_types=["career_question", "user_context", "career_goals"],
                output_types=["coaching_advice", "action_plan", "motivation"],
                confidence_threshold=0.8,
                max_processing_time=30
            ),
            AgentCapability(
                name="mock_interview",
                description="Conduct mock interviews with role-specific questions and feedback",
                input_types=["target_role", "user_background", "interview_type"],
                output_types=["interview_questions", "feedback", "improvement_tips"],
                confidence_threshold=0.85,
                max_processing_time=45
            ),
            AgentCapability(
                name="motivational_support",
                description="Provide motivational support based on user progress and challenges",
                input_types=["user_progress", "challenges", "goals"],
                output_types=["motivation", "encouragement", "perspective"],
                confidence_threshold=0.8,
                max_processing_time=20
            ),
            AgentCapability(
                name="career_experiments",
                description="Suggest career experiments for exploring new paths",
                input_types=["interests", "constraints", "current_role"],
                output_types=["experiment_suggestions", "implementation_plan", "success_metrics"],
                confidence_threshold=0.75,
                max_processing_time=25
            ),
            AgentCapability(
                name="decision_facilitation",
                description="Facilitate career decision-making with structured approaches",
                input_types=["decision_options", "criteria", "constraints"],
                output_types=["decision_framework", "analysis", "recommendations"],
                confidence_threshold=0.8,
                max_processing_time=35
            )
        ]
    
    def _register_message_handlers(self):
        """Register handlers for inter-agent messages"""
        self.register_message_handler(MessageType.COLLABORATION_REQUEST, self._handle_collaboration_request)
        self.register_message_handler(MessageType.CONTEXT_SHARE, self._handle_context_share)
        self.register_message_handler(MessageType.INSIGHT_SHARE, self._handle_insight_share)    

    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """Process a career mentoring request"""
        try:
            content = request.content
            context = request.context
            request_type = request.request_type
            
            # Route to appropriate handler based on request type
            if request_type == RequestType.INTERVIEW_PREP:
                result = await self._conduct_mock_interview(content, context)
            elif request_type == RequestType.CAREER_ADVICE:
                result = await self._provide_career_coaching(content, context)
            elif request_type == RequestType.CAREER_TRANSITION:
                result = await self._support_career_transition(content, context)
            else:
                result = await self._provide_general_mentoring(content, context)
            
            confidence = self._calculate_confidence(result, request)
            
            return AgentResponse(
                request_id=request.id,
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                response_content=result,
                confidence_score=confidence,
                processing_time=0.0,
                metadata={
                    "mentoring_type": request_type.value,
                    "coaching_approach": result.get("coaching_approach", "general"),
                    "support_level": result.get("support_level", "standard"),
                    "follow_up_recommended": result.get("follow_up_recommended", False)
                }
            )
            
        except Exception as e:
            logger.error(f"Career Mentor Agent failed to process request: {str(e)}")
            raise
    
    async def _conduct_mock_interview(self, content: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct a mock interview with role-specific questions and feedback"""
        target_role = content.get("target_role", "")
        interview_type = content.get("interview_type", "behavioral")
        difficulty_level = content.get("difficulty_level", "intermediate")
        
        # Generate interview questions using AI
        questions_prompt = f"""
        Generate {interview_type} interview questions for a {target_role} position at {difficulty_level} level.
        Provide 5-8 questions with explanations of what interviewers are looking for.
        """
        
        questions_content = await self.generate_ai_response(
            prompt=questions_prompt,
            system_prompt="You are an expert interview coach generating realistic interview questions.",
            model_type=ModelType.GEMINI_FLASH,
            max_tokens=800,
            temperature=0.6
        )
        
        # Parse questions into structured format
        questions = self._parse_interview_questions(questions_content)
        
        return {
            "mock_interview": {
                "target_role": target_role,
                "interview_type": interview_type,
                "difficulty_level": difficulty_level,
                "questions": questions,
                "estimated_duration": self._estimate_interview_duration(questions)
            },
            "preparation_tips": [
                f"Research the company and {target_role} responsibilities thoroughly",
                "Prepare STAR method examples for behavioral questions",
                "Practice technical concepts relevant to the role"
            ],
            "coaching_approach": "mock_interview",
            "support_level": "intensive",
            "follow_up_recommended": True
        }  
  
    async def _provide_career_coaching(self, content: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide personalized career coaching and guidance"""
        question = content.get("question", content.get("message", ""))
        user_id = content.get("user_id", "")
        
        # Get user context
        user_context = await self._get_user_context(user_id)
        
        # Generate coaching advice
        coaching_prompt = f"""
        Provide personalized career coaching advice for: {question}
        
        User Context: {json.dumps(user_context, indent=2)}
        
        Provide immediate guidance, deeper insights, strategic recommendations,
        and mindset support. Be encouraging, practical, and specific.
        """
        
        coaching_advice = await self.generate_ai_response(
            prompt=coaching_prompt,
            system_prompt=self._get_coaching_system_prompt(),
            model_type=ModelType.GEMINI_FLASH,
            max_tokens=800,
            temperature=0.8
        )
        
        # Generate motivational support
        motivation = await self._provide_motivational_support(user_context, question)
        
        return {
            "coaching_session": {
                "question": question,
                "personalized_advice": coaching_advice
            },
            "motivational_support": motivation,
            "follow_up_questions": [
                "What specific outcome would make you feel most successful?",
                "What's the biggest obstacle you're facing right now?",
                "How will you know when you've made progress on this goal?"
            ],
            "coaching_approach": "personalized_guidance",
            "support_level": "comprehensive",
            "follow_up_recommended": True
        }
    
    async def _support_career_transition(self, content: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide mentoring support for career transitions"""
        current_role = content.get("current_role", "")
        target_role = content.get("target_role", "")
        user_id = content.get("user_id", "")
        
        # Get user context
        user_context = await self._get_user_context(user_id)
        
        # Generate transition coaching
        transition_coaching = f"""
        Career transitions can be challenging but also incredibly rewarding. Based on your background and goals:

        **Acknowledge Your Courage**: Making a career change takes courage and self-awareness.

        **Leverage Your Strengths**: Your experience in {current_role} has given you valuable skills 
        that will transfer to {target_role}. Focus on identifying and articulating these transferable skills.

        **Take Incremental Steps**: Consider gradual steps like skill building, networking, 
        or taking on projects that bridge your current and target roles.

        Remember, career transitions are journeys, not destinations. Focus on continuous learning and growth.
        """
        
        return {
            "transition_support": {
                "current_role": current_role,
                "target_role": target_role,
                "readiness_assessment": {
                    "readiness_score": 0.7,
                    "strengths": ["Clear career goals", "Relevant experience", "Motivation to change"],
                    "areas_for_development": ["Target role skills", "Industry network", "Interview skills"]
                },
                "coaching_guidance": transition_coaching
            },
            "success_strategies": [
                "Start with the end in mind - clearly define your target role",
                "Build bridges before you need them - develop relationships in your target field",
                "Tell a compelling story - connect your past experience to future goals"
            ],
            "coaching_approach": "transition_support",
            "support_level": "intensive",
            "follow_up_recommended": True
        }    

    async def _provide_general_mentoring(self, content: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide general mentoring advice for various career topics"""
        question = content.get("question", content.get("message", ""))
        user_id = content.get("user_id", "")
        
        # Get user context
        user_context = await self._get_user_context(user_id)
        
        # Generate mentoring advice
        mentoring_prompt = f"""
        Provide career mentoring advice for: {question}
        
        User Background: {json.dumps(user_context, indent=2)}
        
        Provide a direct response, broader perspective, actionable guidance, 
        and mindset/motivation support. Be encouraging, practical, and specific.
        """
        
        mentoring_advice = await self.generate_ai_response(
            prompt=mentoring_prompt,
            system_prompt=self._get_mentoring_system_prompt(),
            model_type=ModelType.GEMINI_FLASH,
            max_tokens=800,
            temperature=0.8
        )
        
        encouragement = """
        I want you to know that seeking guidance shows real wisdom and self-awareness. 
        The fact that you're asking thoughtful questions about your career demonstrates 
        your commitment to growth and success.
        
        Remember, career development is a journey, not a destination. Be patient with yourself 
        as you navigate this process, and celebrate the progress you make along the way.
        """
        
        return {
            "mentoring_advice": mentoring_advice,
            "encouragement": encouragement,
            "reflection_questions": [
                "What assumptions might you be making about this situation?",
                "How does this challenge connect to your long-term goals?",
                "What's one small step you could take today to move forward?"
            ],
            "coaching_approach": "general_mentoring",
            "support_level": "standard",
            "follow_up_recommended": False
        }
    
    async def _get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Retrieve user context from embeddings and profile data"""
        if not user_id:
            return {}
        
        try:
            # Search for career-related context
            career_context = self.embedding_service.search_user_context(
                user_id=user_id,
                query="career goals experience background achievements challenges",
                n_results=8
            )
            
            # Combine and structure context
            combined_context = {
                "career_background": "",
                "career_goals": "",
                "achievements": [],
                "learning_preferences": ""
            }
            
            # Process career context
            for result in career_context:
                content = result.get("content", "")
                source = result.get("source", "unknown")
                
                if source == "resume":
                    combined_context["career_background"] += f" {content}"
                elif source == "profile":
                    combined_context["career_goals"] += f" {content}"
            
            return combined_context
            
        except Exception as e:
            logger.error(f"Failed to get user context: {str(e)}")
            return {}    

    async def _provide_motivational_support(self, user_context: Dict[str, Any], question: str) -> Dict[str, Any]:
        """Provide motivational support based on user context"""
        motivation_prompt = f"""
        Provide motivational support for someone asking: {question}
        
        User Context: {json.dumps(user_context, indent=2)}
        
        Provide personalized encouragement, perspective, and confidence building.
        """
        
        motivation_content = await self.generate_ai_response(
            prompt=motivation_prompt,
            system_prompt=self._get_motivational_system_prompt(),
            model_type=ModelType.GEMINI_FLASH,
            max_tokens=600,
            temperature=0.9
        )
        
        return {
            "motivational_message": motivation_content,
            "affirmations": [
                "I have the skills and experience to achieve my career goals",
                "I am capable of learning and growing in new areas",
                "My unique background gives me valuable perspectives"
            ],
            "success_reminders": [
                "You've overcome challenges before and can do it again",
                "Every expert was once a beginner",
                "Your willingness to grow shows your potential for success"
            ]
        }
    
    # System prompts
    def _get_mentoring_system_prompt(self) -> str:
        """Get system prompt for general mentoring"""
        return """You are an experienced career mentor with 15+ years of experience helping professionals 
        navigate their careers. You provide personalized, practical advice that is encouraging yet realistic. 
        You focus on actionable steps, mindset development, and long-term career growth."""
    
    def _get_coaching_system_prompt(self) -> str:
        """Get system prompt for coaching advice"""
        return """You are a senior career coach providing personalized guidance. Your advice is practical, 
        actionable, and tailored to the individual's specific situation. You balance encouragement with 
        realism and help people see their strengths while providing concrete steps for moving forward."""
    
    def _get_motivational_system_prompt(self) -> str:
        """Get system prompt for motivational support"""
        return """You are an inspiring career mentor who excels at providing motivation and encouragement. 
        You help people see their potential, overcome self-doubt, and maintain momentum in their career 
        development. Your approach is authentic, empathetic, and empowering."""
    
    def _calculate_confidence(self, result: Dict[str, Any], request: AgentRequest) -> float:
        """Calculate confidence score for the response"""
        base_confidence = 0.8
        
        # Adjust based on result completeness
        if len(str(result)) < 500:
            base_confidence -= 0.1
        
        # Adjust based on request type
        if request.request_type == RequestType.INTERVIEW_PREP:
            base_confidence += 0.05
        elif request.request_type == RequestType.CAREER_ADVICE:
            base_confidence += 0.05
        
        # Adjust based on user context availability
        if request.content.get("user_id"):
            base_confidence += 0.05
        
        return min(max(base_confidence, 0.0), 1.0)   
 
    # Utility methods
    def _parse_interview_questions(self, content: str) -> List[Dict[str, Any]]:
        """Parse AI-generated interview questions into structured format"""
        questions = []
        lines = content.split('\n')
        current_question = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.')):
                if current_question:
                    questions.append(current_question)
                current_question = {
                    "question": line,
                    "category": "general",
                    "looking_for": "Comprehensive response with specific examples"
                }
        
        if current_question:
            questions.append(current_question)
        
        return questions[:8]
    
    def _estimate_interview_duration(self, questions: List[Dict[str, Any]]) -> str:
        """Estimate interview duration based on questions"""
        num_questions = len(questions)
        if num_questions <= 5:
            return "30-45 minutes"
        elif num_questions <= 8:
            return "45-60 minutes"
        else:
            return "60-90 minutes"
    
    # Inter-agent communication handlers
    async def _handle_collaboration_request(self, message):
        """Handle collaboration requests from other agents"""
        try:
            content = message.content
            collaboration_type = content.get("type", "")
            
            if collaboration_type == "interview_prep_support":
                return {
                    "coaching_advice": "Focus on learning agility and transferable skills",
                    "interview_strategies": ["Highlight transferable skills", "Show concrete development plan"],
                    "confidence_building": "Focus on your strengths while showing commitment to growth"
                }
            elif collaboration_type == "transition_mentoring":
                return {
                    "mentoring_support": "Break down the strategic plan into actionable steps and celebrate progress",
                    "motivation_strategies": ["Create vision board", "Connect with successful transitioners"],
                    "accountability_framework": {"weekly_check_ins": "Review progress weekly"}
                }
            else:
                return {"status": "unsupported", "message": "Collaboration type not supported"}
                
        except Exception as e:
            logger.error(f"Failed to handle collaboration request: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _handle_context_share(self, message):
        """Handle context sharing from other agents"""
        shared_context = message.content
        logger.info(f"Received context share from {message.sender_agent_id}")
        return {"status": "received", "message": "Context received and stored"}
    
    async def _handle_insight_share(self, message):
        """Handle insight sharing from other agents"""
        insights = message.content
        logger.info(f"Received insights from {message.sender_agent_id}: {insights}")
        return {"status": "received", "message": "Insights received and will be incorporated"}