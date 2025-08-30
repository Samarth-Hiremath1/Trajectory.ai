"""
Example integration of multi-agent system with existing services
This shows how the new agent system can be integrated with current chat and roadmap services
"""
import asyncio
import logging
from typing import Dict, Any, Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.agent import (
    AgentType, RequestType, RequestPriority, AgentRequest, 
    AgentCapability, AgentResponse
)
from services.base_agent import BaseAgent
from services.agent_orchestrator_service import AgentOrchestratorService
from services.career_strategy_agent import CareerStrategyAgent
from services.ai_service import AIService
from services.embedding_service import EmbeddingService
from services.database_service import DatabaseService

logger = logging.getLogger(__name__)

class CareerMentorAgent(BaseAgent):
    """
    Career Mentor Agent - provides personalized career coaching and advice
    """
    
    def _define_capabilities(self):
        return [
            AgentCapability(
                name="career_advice",
                description="Provide personalized career advice and coaching",
                input_types=["career_question", "user_context"],
                output_types=["career_advice", "action_plan"]
            ),
            AgentCapability(
                name="interview_preparation",
                description="Help with interview preparation and mock interviews",
                input_types=["target_role", "user_background"],
                output_types=["interview_tips", "practice_questions"]
            )
        ]
    
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """Process career mentoring requests"""
        try:
            content = request.content
            context = request.context
            
            # Extract user question and context
            question = content.get("question", "")
            user_background = context.get("user_background", "")
            
            # Create system prompt for career mentoring
            system_prompt = """You are an experienced career mentor providing personalized advice. 
            Use the user's background to give specific, actionable guidance. Be encouraging but realistic.
            Focus on practical steps they can take to advance their career."""
            
            # Create user prompt with context
            user_prompt = f"""User Background:
{user_background}

Question: {question}

Please provide specific, actionable career advice based on the user's background and current situation."""
            
            # Generate AI response
            response_text = await self.generate_ai_response(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=800,
                temperature=0.8
            )
            
            # Calculate confidence based on response quality
            confidence = self._calculate_confidence(response_text, question)
            
            return AgentResponse(
                request_id=request.id,
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                response_content={
                    "advice": response_text,
                    "question": question,
                    "context_used": bool(user_background)
                },
                confidence_score=confidence,
                processing_time=0.0  # Will be set by base class
            )
            
        except Exception as e:
            logger.error(f"Career mentor agent failed to process request: {str(e)}")
            raise
    
    def _calculate_confidence(self, response: str, question: str) -> float:
        """Calculate confidence score based on response quality"""
        # Simple heuristic - longer responses with specific advice tend to be better
        base_confidence = 0.7
        
        if len(response) > 200:
            base_confidence += 0.1
        if "specific" in response.lower() or "actionable" in response.lower():
            base_confidence += 0.1
        if len(question) > 20:  # More detailed questions get better responses
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)

class SkillsAnalysisAgent(BaseAgent):
    """
    Skills Analysis Agent - analyzes user skills and identifies gaps
    """
    
    def _define_capabilities(self):
        return [
            AgentCapability(
                name="skill_gap_analysis",
                description="Analyze skill gaps between current and target roles",
                input_types=["current_role", "target_role", "user_skills"],
                output_types=["skill_gaps", "development_plan"]
            ),
            AgentCapability(
                name="skill_assessment",
                description="Assess current skill levels and competencies",
                input_types=["resume_content", "self_assessment"],
                output_types=["skill_evaluation", "strengths_weaknesses"]
            )
        ]
    
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """Process skills analysis requests"""
        try:
            content = request.content
            context = request.context
            
            current_role = content.get("current_role", "")
            target_role = content.get("target_role", "")
            user_background = context.get("user_background", "")
            
            system_prompt = """You are a skills analysis expert. Analyze the user's current skills 
            and identify gaps for their target role. Provide specific, actionable recommendations 
            for skill development."""
            
            user_prompt = f"""Current Role: {current_role}
Target Role: {target_role}
User Background: {user_background}

Please analyze:
1. Current skills and competencies
2. Skills required for the target role
3. Specific skill gaps to address
4. Prioritized development recommendations
5. Timeline for skill development"""
            
            response_text = await self.generate_ai_response(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=1000,
                temperature=0.6
            )
            
            return AgentResponse(
                request_id=request.id,
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                response_content={
                    "analysis": response_text,
                    "current_role": current_role,
                    "target_role": target_role,
                    "methodology": "AI-powered skills gap analysis"
                },
                confidence_score=0.85,
                processing_time=0.0
            )
            
        except Exception as e:
            logger.error(f"Skills analysis agent failed to process request: {str(e)}")
            raise

class MultiAgentChatService:
    """
    Enhanced chat service that uses the multi-agent system
    """
    
    def __init__(self, ai_service: AIService, db_service: DatabaseService):
        self.ai_service = ai_service
        self.db_service = db_service
        
        # Initialize embedding service for Career Strategy Agent
        self.embedding_service = EmbeddingService()
        
        # Initialize orchestrator
        self.orchestrator = AgentOrchestratorService(ai_service)
        
        # Create and register agents
        self.career_mentor = CareerMentorAgent(
            "career_mentor_1", 
            AgentType.CAREER_MENTOR, 
            ai_service
        )
        
        self.skills_analyst = SkillsAnalysisAgent(
            "skills_analyst_1", 
            AgentType.SKILLS_ANALYSIS, 
            ai_service
        )
        
        # Add Career Strategy Agent
        self.career_strategist = CareerStrategyAgent(
            "career_strategist_1",
            ai_service,
            self.embedding_service
        )
        
    async def start(self):
        """Start the multi-agent chat service"""
        await self.orchestrator.start()
        
        # Register agents
        self.orchestrator.register_agent(self.career_mentor)
        self.orchestrator.register_agent(self.skills_analyst)
        self.orchestrator.register_agent(self.career_strategist)
        
        logger.info("Multi-agent chat service started with Career Strategy Agent")
    
    async def stop(self):
        """Stop the multi-agent chat service"""
        await self.orchestrator.stop()
        logger.info("Multi-agent chat service stopped")
    
    async def process_chat_message(
        self, 
        user_id: str, 
        message: str, 
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a chat message using the multi-agent system
        
        Args:
            user_id: ID of the user sending the message
            message: The chat message
            user_context: Optional user context (profile, resume, etc.)
            
        Returns:
            Dictionary with the agent response
        """
        try:
            # Determine request type based on message content
            request_type = self._classify_message(message)
            
            # Create agent request
            agent_request = AgentRequest(
                user_id=user_id,
                request_type=request_type,
                content={"question": message},
                context=user_context or {},
                priority=RequestPriority.MEDIUM
            )
            
            # Process with orchestrator
            result = await self.orchestrator.process_request(agent_request)
            
            if result["success"]:
                return {
                    "success": True,
                    "response": result["final_response"],
                    "agents_used": [r["agent_type"] for r in result["responses"]],
                    "confidence": result.get("average_confidence", 0.8),
                    "processing_time": result["execution_time"]
                }
            else:
                return {
                    "success": False,
                    "error": result["error"],
                    "fallback_response": "I apologize, but I'm having trouble processing your request right now. Please try again."
                }
                
        except Exception as e:
            logger.error(f"Multi-agent chat processing failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_response": "I'm experiencing technical difficulties. Please try again later."
            }
    
    def _classify_message(self, message: str) -> RequestType:
        """
        Classify the message to determine which type of agent request it is
        
        Args:
            message: The user message
            
        Returns:
            RequestType enum value
        """
        message_lower = message.lower()
        
        # Strategic career planning keywords (Career Strategy Agent)
        strategic_keywords = ["strategy", "strategic", "transition", "career change", "pivot", 
                            "market trends", "networking", "positioning", "competitive advantage"]
        
        # Simple keyword-based classification
        if any(word in message_lower for word in strategic_keywords):
            return RequestType.CAREER_TRANSITION
        elif any(word in message_lower for word in ["skill", "gap", "competenc", "abilit"]):
            return RequestType.SKILL_ANALYSIS
        elif any(word in message_lower for word in ["interview", "prep", "question"]):
            return RequestType.INTERVIEW_PREP
        elif any(word in message_lower for word in ["roadmap", "plan", "path"]):
            return RequestType.ROADMAP_GENERATION
        elif any(word in message_lower for word in ["learn", "course", "study", "resource"]):
            return RequestType.LEARNING_PATH
        else:
            return RequestType.CAREER_ADVICE
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of the multi-agent chat service"""
        return {
            "service_active": True,
            "orchestrator_status": self.orchestrator.get_status(),
            "registered_agents": {
                "career_mentor": self.career_mentor.get_status().dict(),
                "skills_analyst": self.skills_analyst.get_status().dict(),
                "career_strategist": self.career_strategist.get_status().dict()
            }
        }

# Example usage function
async def example_usage():
    """Example of how to use the multi-agent system"""
    logger.info("Starting multi-agent system example...")
    
    # Initialize services
    ai_service = AIService()
    db_service = DatabaseService()
    
    # Create multi-agent chat service
    chat_service = MultiAgentChatService(ai_service, db_service)
    await chat_service.start()
    
    try:
        # Example user context
        user_context = {
            "user_background": "Software developer with 3 years experience in Python and JavaScript",
            "current_role": "Junior Software Developer",
            "target_role": "Senior Software Engineer",
            "education": "Computer Science degree"
        }
        
        # Example chat messages including strategic career questions
        messages = [
            "What skills do I need to become a senior software engineer?",
            "How can I prepare for technical interviews?",
            "What's the best way to learn system design?",
            "What's the best strategic approach for transitioning to a product management role?",
            "How should I position myself competitively in the market for senior engineering roles?",
            "What networking strategies would help me advance my career?"
        ]
        
        for message in messages:
            logger.info(f"Processing message: {message}")
            
            result = await chat_service.process_chat_message(
                user_id="example_user",
                message=message,
                user_context=user_context
            )
            
            logger.info(f"Result: {result}")
            print(f"\nUser: {message}")
            
            # Extract response content
            response_content = result.get('response', {})
            if isinstance(response_content, dict):
                # Try different response keys
                ai_response = (response_content.get('advice') or 
                             response_content.get('analysis') or 
                             response_content.get('synthesized_response') or 
                             str(response_content))
            else:
                ai_response = str(response_content)
            
            print(f"AI: {ai_response[:500]}...")  # Truncate for readability
            print(f"Agents used: {result.get('agents_used', [])}")
            print("-" * 50)
    
    finally:
        await chat_service.stop()
    
    logger.info("Multi-agent system example completed")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example_usage())