"""
Learning Resource Agent for personalized learning path curation and resource recommendations
"""
import logging
import json
import re
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime

from models.agent import (
    AgentType, AgentRequest, AgentResponse, AgentCapability, 
    MessageType, RequestType
)
from models.roadmap import LearningResource, ResourceType, SkillLevel
from services.base_agent import BaseAgent
from services.ai_service import AIService, ModelType
from services.embedding_service import EmbeddingService
from services.roadmap_scraper import RoadmapScraper

logger = logging.getLogger(__name__)

class LearningResourceAgent(BaseAgent):
    """
    Specialized agent for personalized learning path curation and resource recommendations.
    Provides course recommendations, certification guidance, and project suggestions.
    """
    
    def __init__(
        self,
        agent_id: str,
        ai_service: AIService,
        embedding_service: EmbeddingService,
        roadmap_scraper: Optional[RoadmapScraper] = None,
        max_concurrent_requests: int = 3
    ):
        """
        Initialize Learning Resource Agent
        
        Args:
            agent_id: Unique identifier for this agent instance
            ai_service: AI service for LLM interactions
            embedding_service: Embedding service for ChromaDB access
            roadmap_scraper: Service for scraping external learning resources
            max_concurrent_requests: Maximum concurrent requests
        """
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.LEARNING_RESOURCE,
            ai_service=ai_service,
            max_concurrent_requests=max_concurrent_requests,
            default_confidence_threshold=0.8
        )
        
        self.embedding_service = embedding_service
        self.roadmap_scraper = roadmap_scraper or RoadmapScraper()
        
        # Register message handlers for inter-agent communication
        self._register_message_handlers()
        
        # Learning resource knowledge base
        self.learning_platforms = self._load_learning_platforms()
        self.certification_database = self._load_certification_database()
        self.project_templates = self._load_project_templates()
        
        logger.info(f"Learning Resource Agent {agent_id} initialized")
    
    def _define_capabilities(self) -> List[AgentCapability]:
        """Define the capabilities of the Learning Resource Agent"""
        return [
            AgentCapability(
                name="personalized_learning_path_curation",
                description="Create personalized learning paths based on user goals and constraints",
                input_types=["skills_to_learn", "learning_style", "timeline", "budget", "current_level"],
                output_types=["learning_path", "resource_sequence", "milestone_plan"],
                confidence_threshold=0.85,
                max_processing_time=45
            ),
            AgentCapability(
                name="course_recommendation_system",
                description="Recommend courses with filtering by difficulty, budget, and learning style",
                input_types=["skill_requirements", "difficulty_level", "budget_range", "learning_preferences"],
                output_types=["course_recommendations", "filtered_options", "comparison_matrix"],
                confidence_threshold=0.8,
                max_processing_time=30
            ),
            AgentCapability(
                name="certification_recommendation_engine",
                description="Recommend certifications based on target roles and career goals",
                input_types=["target_role", "current_skills", "industry", "career_level"],
                output_types=["certification_recommendations", "priority_ranking", "preparation_plan"],
                confidence_threshold=0.8,
                max_processing_time=25
            ),
            AgentCapability(
                name="project_suggestion_system",
                description="Suggest hands-on projects for skill development and portfolio building",
                input_types=["skills_to_practice", "experience_level", "time_commitment", "portfolio_goals"],
                output_types=["project_suggestions", "implementation_guide", "skill_mapping"],
                confidence_threshold=0.75,
                max_processing_time=35
            ),
            AgentCapability(
                name="external_platform_integration",
                description="Integrate with external learning platforms and roadmap.sh resources",
                input_types=["platform_preferences", "content_type", "skill_focus"],
                output_types=["platform_resources", "curated_content", "access_information"],
                confidence_threshold=0.7,
                max_processing_time=40
            )
        ]
    
    def _register_message_handlers(self):
        """Register handlers for inter-agent messages"""
        self.register_message_handler(
            MessageType.COLLABORATION_REQUEST,
            self._handle_collaboration_request
        )
        self.register_message_handler(
            MessageType.CONTEXT_SHARE,
            self._handle_context_share
        )
        self.register_message_handler(
            MessageType.INSIGHT_SHARE,
            self._handle_insight_share
        )
    
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """
        Process a learning resource request
        
        Args:
            request: The request to process
            
        Returns:
            AgentResponse with learning resource recommendations
        """
        try:
            # Extract request details
            content = request.content
            context = request.context
            request_type = request.request_type
            
            # Route to appropriate handler based on request type
            if request_type == RequestType.LEARNING_PATH:
                result = await self._create_personalized_learning_path(content, context)
            elif request_type == RequestType.ROADMAP_GENERATION:
                result = await self._contribute_to_roadmap_resources(content, context)
            elif request_type == RequestType.SKILL_ANALYSIS:
                result = await self._recommend_skill_learning_resources(content, context)
            else:
                # Default to general learning resource advice
                result = await self._provide_learning_resource_advice(content, context)
            
            # Calculate confidence score based on result quality
            confidence = self._calculate_confidence(result, request)
            
            return AgentResponse(
                request_id=request.id,
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                response_content=result,
                confidence_score=confidence,
                processing_time=0.0,  # Will be set by base class
                metadata={
                    "resource_type": request_type.value,
                    "resources_recommended": len(result.get("learning_resources", [])),
                    "platforms_covered": len(result.get("platforms", [])),
                    "certifications_suggested": len(result.get("certifications", []))
                }
            )
            
        except Exception as e:
            logger.error(f"Learning Resource Agent failed to process request: {str(e)}")
            raise
    
    async def _create_personalized_learning_path(self, content: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a personalized learning path based on user requirements
        
        Args:
            content: Request content with learning requirements
            context: User context and preferences
            
        Returns:
            Comprehensive personalized learning path
        """
        user_id = content.get("user_id", "")
        skills_to_learn = content.get("skills_to_learn", [])
        learning_style = content.get("learning_style", "mixed")
        timeline = content.get("timeline", "3 months")
        budget = content.get("budget", "flexible")
        current_level = content.get("current_level", "beginner")
        
        # Get user context and preferences
        user_context = await self._get_user_context(user_id)
        
        # Analyze learning requirements
        learning_analysis = await self._analyze_learning_requirements(
            skills_to_learn, learning_style, timeline, budget, current_level, user_context
        )
        
        # Create structured learning path
        learning_path = await self._generate_learning_path_structure(
            learning_analysis, timeline
        )
        
        # Recommend specific resources for each phase
        resource_recommendations = await self._recommend_resources_for_path(
            learning_path, learning_style, budget
        )
        
        # Create milestone and assessment plan
        milestone_plan = await self._create_learning_milestone_plan(
            learning_path, timeline
        )
        
        # Generate project suggestions for hands-on practice
        project_suggestions = await self._suggest_learning_projects(
            skills_to_learn, current_level, timeline
        )
        
        return {
            "personalized_learning_path": {
                "overview": learning_analysis,
                "learning_phases": learning_path,
                "total_duration": timeline,
                "estimated_hours": self._calculate_total_learning_hours(learning_path),
                "difficulty_progression": self._analyze_difficulty_progression(learning_path)
            },
            "resource_recommendations": resource_recommendations,
            "milestone_plan": milestone_plan,
            "project_suggestions": project_suggestions,
            "learning_strategy": await self._create_learning_strategy(learning_style, user_context),
            "progress_tracking": self._create_progress_tracking_plan(learning_path),
            "adaptation_guidelines": self._create_adaptation_guidelines(learning_analysis)
        }
    
    async def _contribute_to_roadmap_resources(self, content: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Contribute learning resources to roadmap generation
        
        Args:
            content: Roadmap generation content
            context: User context
            
        Returns:
            Learning resources contribution to roadmap
        """
        user_id = content.get("user_id", "")
        target_role = content.get("target_role", "")
        current_role = content.get("current_role", "")
        timeline = content.get("timeline", "12 months")
        
        # Get user context
        user_context = await self._get_user_context(user_id)
        
        # Analyze resource needs for career transition
        resource_needs = await self._analyze_career_transition_resource_needs(
            current_role, target_role, user_context
        )
        
        # Get resources from external platforms
        external_resources = await self._get_external_learning_resources(
            resource_needs, target_role
        )
        
        # Recommend certifications for target role
        certification_recommendations = await self._recommend_role_certifications(
            target_role, user_context
        )
        
        # Suggest portfolio projects
        portfolio_projects = await self._suggest_portfolio_projects(
            target_role, resource_needs, user_context
        )
        
        # Create phase-based resource allocation
        phase_resources = await self._allocate_resources_to_phases(
            external_resources, certification_recommendations, portfolio_projects, timeline
        )
        
        return {
            "learning_resources_contribution": {
                "resource_analysis": resource_needs,
                "phase_based_resources": phase_resources,
                "certification_roadmap": certification_recommendations,
                "portfolio_projects": portfolio_projects,
                "external_platform_resources": external_resources,
                "resource_prioritization": self._prioritize_learning_resources(phase_resources),
                "cost_analysis": self._analyze_learning_costs(phase_resources),
                "time_investment": self._calculate_time_investment(phase_resources)
            }
        }
    
    async def _recommend_skill_learning_resources(self, content: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recommend learning resources for specific skills
        
        Args:
            content: Skill analysis content
            context: User context
            
        Returns:
            Skill-specific learning resource recommendations
        """
        skills_needed = content.get("skills_needed", [])
        skill_gaps = content.get("skill_gaps", {})
        priority_skills = content.get("priority_skills", [])
        user_id = content.get("user_id", "")
        
        # Get user context
        user_context = await self._get_user_context(user_id)
        
        # Recommend resources for each skill
        skill_resources = {}
        for skill in skills_needed:
            skill_level = self._determine_skill_level_needed(skill, skill_gaps)
            resources = await self._recommend_resources_for_skill(
                skill, skill_level, user_context
            )
            skill_resources[skill] = resources
        
        # Create learning sequence optimization
        learning_sequence = await self._optimize_skill_learning_sequence(
            skills_needed, skill_resources, priority_skills
        )
        
        # Recommend skill validation methods
        validation_methods = await self._recommend_skill_validation_methods(
            skills_needed, user_context
        )
        
        return {
            "skill_learning_resources": {
                "skill_specific_resources": skill_resources,
                "optimized_learning_sequence": learning_sequence,
                "skill_validation_methods": validation_methods,
                "cross_skill_projects": await self._suggest_cross_skill_projects(skills_needed),
                "learning_communities": self._recommend_learning_communities(skills_needed),
                "mentorship_opportunities": self._identify_mentorship_opportunities(skills_needed)
            }
        }
    
    async def _provide_learning_resource_advice(self, content: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provide general learning resource advice
        
        Args:
            content: Request content with question
            context: User context
            
        Returns:
            Learning resource advice and recommendations
        """
        question = content.get("question", content.get("message", ""))
        user_id = content.get("user_id", "")
        
        # Get user context
        user_context = await self._get_user_context(user_id)
        
        # Generate learning resource advice
        advice_prompt = self._create_learning_resource_advice_prompt(question, user_context)
        
        advice_content = await self.generate_ai_response(
            prompt=advice_prompt,
            system_prompt=self._get_learning_resource_advice_system_prompt(),
            model_type=ModelType.GEMINI_FLASH,
            max_tokens=800,
            temperature=0.7
        )
        
        # Extract specific resource recommendations
        resource_recommendations = await self._extract_resource_recommendations_from_advice(
            advice_content, question
        )
        
        return {
            "learning_resource_advice": advice_content,
            "specific_recommendations": resource_recommendations,
            "learning_strategies": self._extract_learning_strategies(advice_content),
            "platform_suggestions": self._suggest_platforms_for_question(question),
            "next_steps": self._generate_learning_next_steps(advice_content)
        }
    
    async def _get_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieve user context from embeddings and profile data
        
        Args:
            user_id: User identifier
            
        Returns:
            User context dictionary with learning focus
        """
        if not user_id:
            return {}
        
        try:
            # Search for learning-related context
            learning_context = self.embedding_service.search_user_context(
                user_id=user_id,
                query="learning education courses certifications training skills development",
                n_results=8
            )
            
            # Search for preferences and constraints
            preferences_context = self.embedding_service.search_user_context(
                user_id=user_id,
                query="preferences budget time constraints learning style goals",
                n_results=5
            )
            
            # Combine and structure context
            combined_context = {
                "learning_history": [],
                "preferred_learning_style": "mixed",
                "budget_constraints": "flexible",
                "time_availability": "moderate",
                "current_skills": [],
                "learning_goals": [],
                "platform_preferences": [],
                "certification_history": []
            }
            
            # Process learning context
            for result in learning_context:
                content = result.get("content", "")
                source = result.get("source", "unknown")
                
                if source == "resume":
                    # Extract learning-related information from resume
                    learning_info = self._extract_learning_info_from_text(content)
                    combined_context["learning_history"].extend(learning_info.get("courses", []))
                    combined_context["certification_history"].extend(learning_info.get("certifications", []))
                elif source == "profile":
                    # Extract preferences from profile
                    combined_context["learning_goals"].append(content)
            
            return combined_context
            
        except Exception as e:
            logger.error(f"Failed to get user context: {str(e)}")
            return {}
    
    async def _analyze_learning_requirements(
        self, 
        skills_to_learn: List[str], 
        learning_style: str, 
        timeline: str, 
        budget: str,
        current_level: str,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze learning requirements and constraints
        
        Args:
            skills_to_learn: List of skills to learn
            learning_style: Preferred learning style
            timeline: Available timeline
            budget: Budget constraints
            current_level: Current skill level
            user_context: User background and preferences
            
        Returns:
            Learning requirements analysis
        """
        analysis_prompt = f"""
        Analyze learning requirements for the following skills and constraints:
        
        SKILLS TO LEARN: {skills_to_learn}
        LEARNING STYLE: {learning_style}
        TIMELINE: {timeline}
        BUDGET: {budget}
        CURRENT LEVEL: {current_level}
        
        USER CONTEXT:
        {json.dumps(user_context, indent=2)}
        
        Please provide a comprehensive learning requirements analysis including:
        
        1. SKILL COMPLEXITY ANALYSIS
           - Difficulty level of each skill
           - Prerequisites and dependencies
           - Estimated learning time per skill
           - Skill interconnections and synergies
        
        2. LEARNING PATH OPTIMIZATION
           - Optimal skill learning sequence
           - Parallel vs sequential learning opportunities
           - Skill combination strategies
           - Milestone and checkpoint planning
        
        3. RESOURCE REQUIREMENTS
           - Types of resources needed (courses, books, projects, etc.)
           - Platform and format preferences
           - Interactive vs self-paced learning balance
           - Hands-on practice requirements
        
        4. CONSTRAINT ANALYSIS
           - Timeline feasibility assessment
           - Budget allocation recommendations
           - Learning style accommodation strategies
           - Potential bottlenecks and mitigation
        
        5. SUCCESS FACTORS
           - Key factors for learning success
           - Motivation and engagement strategies
           - Progress tracking recommendations
           - Support and community needs
        
        Focus on creating a realistic, achievable learning plan that maximizes effectiveness within the given constraints.
        """
        
        analysis_content = await self.generate_ai_response(
            prompt=analysis_prompt,
            system_prompt=self._get_learning_analysis_system_prompt(),
            model_type=ModelType.GEMINI_FLASH,
            max_tokens=1000,
            temperature=0.6
        )
        
        return {
            "requirements_analysis": analysis_content,
            "skill_complexity_scores": self._calculate_skill_complexity_scores(skills_to_learn),
            "timeline_feasibility": self._assess_timeline_feasibility(skills_to_learn, timeline),
            "budget_requirements": self._estimate_budget_requirements(skills_to_learn, budget),
            "learning_style_match": self._assess_learning_style_match(learning_style, skills_to_learn)
        }
    
    async def _generate_learning_path_structure(
        self, 
        learning_analysis: Dict[str, Any], 
        timeline: str
    ) -> List[Dict[str, Any]]:
        """
        Generate structured learning path with phases
        
        Args:
            learning_analysis: Learning requirements analysis
            timeline: Available timeline
            
        Returns:
            Structured learning path with phases
        """
        path_prompt = f"""
        Create a structured learning path based on the following analysis:
        
        LEARNING ANALYSIS:
        {learning_analysis.get('requirements_analysis', '')}
        
        TIMELINE: {timeline}
        
        Please create a phase-based learning path with:
        
        1. LEARNING PHASES (3-5 phases)
           - Phase objectives and outcomes
           - Skills covered in each phase
           - Duration and time allocation
           - Prerequisites and dependencies
        
        2. PHASE STRUCTURE
           - Foundation phase (basics and prerequisites)
           - Development phases (core skill building)
           - Application phase (hands-on practice and projects)
           - Mastery phase (advanced concepts and specialization)
        
        3. PROGRESSION STRATEGY
           - Skill building sequence within phases
           - Knowledge reinforcement activities
           - Practical application opportunities
           - Assessment and validation checkpoints
        
        4. FLEXIBILITY AND ADAPTATION
           - Alternative paths for different learning speeds
           - Optional advanced topics
           - Remediation strategies for difficult concepts
           - Acceleration opportunities for fast learners
        
        Format as a structured JSON-like response with clear phase definitions.
        """
        
        path_content = await self.generate_ai_response(
            prompt=path_prompt,
            system_prompt="You are a learning path designer creating structured, progressive learning experiences.",
            model_type=ModelType.GEMINI_FLASH,
            max_tokens=1200,
            temperature=0.7
        )
        
        # Parse and structure the learning path
        return await self._parse_learning_path_structure(path_content, timeline)
    
    async def _recommend_resources_for_path(
        self, 
        learning_path: List[Dict[str, Any]], 
        learning_style: str, 
        budget: str
    ) -> Dict[str, Any]:
        """
        Recommend specific resources for each phase of the learning path
        
        Args:
            learning_path: Structured learning path
            learning_style: Preferred learning style
            budget: Budget constraints
            
        Returns:
            Resource recommendations for each phase
        """
        phase_resources = {}
        
        for phase in learning_path:
            phase_name = phase.get("name", f"Phase {phase.get('number', 1)}")
            skills = phase.get("skills", [])
            duration = phase.get("duration", "4 weeks")
            
            # Get resources for phase skills
            resources = await self._get_resources_for_skills(
                skills, learning_style, budget, duration
            )
            
            # Add phase-specific project suggestions
            projects = await self._suggest_phase_projects(skills, phase.get("objectives", []))
            
            # Add assessment resources
            assessments = await self._recommend_phase_assessments(skills)
            
            phase_resources[phase_name] = {
                "learning_resources": resources,
                "project_suggestions": projects,
                "assessment_resources": assessments,
                "estimated_cost": self._calculate_phase_cost(resources),
                "time_investment": self._calculate_phase_time(resources, duration)
            }
        
        return phase_resources
    
    async def _get_resources_for_skills(
        self, 
        skills: List[str], 
        learning_style: str, 
        budget: str, 
        duration: str
    ) -> List[LearningResource]:
        """
        Get learning resources for specific skills
        
        Args:
            skills: List of skills to find resources for
            learning_style: Preferred learning style
            budget: Budget constraints
            duration: Available duration
            
        Returns:
            List of learning resources
        """
        all_resources = []
        
        # Get resources from roadmap scraper
        try:
            scraped_resources = await self.roadmap_scraper.scrape_learning_resources(
                skills, max_per_skill=3
            )
            external_resources = self.roadmap_scraper.convert_to_learning_resources(scraped_resources)
            all_resources.extend(external_resources)
        except Exception as e:
            logger.warning(f"Failed to scrape external resources: {str(e)}")
        
        # Generate additional resource recommendations using AI
        for skill in skills:
            ai_resources = await self._generate_ai_resource_recommendations(
                skill, learning_style, budget
            )
            all_resources.extend(ai_resources)
        
        # Filter and prioritize resources
        filtered_resources = self._filter_resources_by_constraints(
            all_resources, learning_style, budget, duration
        )
        
        return filtered_resources[:10]  # Limit to top 10 resources per phase
    
    async def _generate_ai_resource_recommendations(
        self, 
        skill: str, 
        learning_style: str, 
        budget: str
    ) -> List[LearningResource]:
        """
        Generate resource recommendations using AI
        
        Args:
            skill: Skill to find resources for
            learning_style: Learning style preference
            budget: Budget constraints
            
        Returns:
            List of AI-generated learning resources
        """
        resource_prompt = f"""
        Recommend specific learning resources for the skill: {skill}
        
        LEARNING STYLE: {learning_style}
        BUDGET: {budget}
        
        Please recommend 3-5 high-quality learning resources including:
        
        1. ONLINE COURSES
           - Platform (Coursera, Udemy, edX, etc.)
           - Course title and instructor
           - Duration and format
           - Cost and certification options
        
        2. BOOKS AND DOCUMENTATION
           - Technical books and guides
           - Official documentation
           - Free online resources
           - Community-recommended materials
        
        3. HANDS-ON RESOURCES
           - Interactive tutorials and labs
           - Practice platforms and sandboxes
           - Project-based learning opportunities
           - Coding challenges and exercises
        
        4. COMMUNITY RESOURCES
           - Forums and discussion groups
           - YouTube channels and video series
           - Podcasts and webinars
           - Open source projects to contribute to
        
        Focus on resources that match the learning style and budget constraints.
        Provide specific titles, platforms, and access information where possible.
        """
        
        resource_content = await self.generate_ai_response(
            prompt=resource_prompt,
            system_prompt="You are a learning resource curator with extensive knowledge of educational platforms and materials.",
            model_type=ModelType.GEMINI_FLASH,
            max_tokens=800,
            temperature=0.6
        )
        
        # Parse AI response into LearningResource objects
        return self._parse_ai_resource_recommendations(resource_content, skill)
    
    def _parse_ai_resource_recommendations(self, content: str, skill: str) -> List[LearningResource]:
        """
        Parse AI-generated resource recommendations into LearningResource objects
        
        Args:
            content: AI-generated content
            skill: Skill the resources are for
            
        Returns:
            List of LearningResource objects
        """
        resources = []
        
        # Simple parsing logic - in production, this would be more sophisticated
        lines = content.split('\n')
        current_resource = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for resource indicators
            if any(platform in line.lower() for platform in ['coursera', 'udemy', 'edx', 'youtube', 'book']):
                if current_resource:
                    # Create resource from current data
                    resource = self._create_learning_resource_from_parsed_data(current_resource, skill)
                    if resource:
                        resources.append(resource)
                    current_resource = {}
                
                # Start new resource
                current_resource['title'] = line
                current_resource['description'] = ""
            elif current_resource and line.startswith('-'):
                # Add to description
                current_resource['description'] += f" {line[1:].strip()}"
        
        # Handle last resource
        if current_resource:
            resource = self._create_learning_resource_from_parsed_data(current_resource, skill)
            if resource:
                resources.append(resource)
        
        return resources
    
    def _create_learning_resource_from_parsed_data(self, data: Dict[str, Any], skill: str) -> Optional[LearningResource]:
        """
        Create LearningResource from parsed data
        
        Args:
            data: Parsed resource data
            skill: Skill the resource is for
            
        Returns:
            LearningResource object or None
        """
        try:
            title = data.get('title', '').strip()
            if not title:
                return None
            
            # Determine resource type from title/description
            resource_type = ResourceType.COURSE
            if 'book' in title.lower():
                resource_type = ResourceType.BOOK
            elif 'video' in title.lower() or 'youtube' in title.lower():
                resource_type = ResourceType.VIDEO
            elif 'project' in title.lower():
                resource_type = ResourceType.PROJECT
            elif 'certification' in title.lower():
                resource_type = ResourceType.CERTIFICATION
            
            # Determine provider from title
            provider = None
            for platform in ['coursera', 'udemy', 'edx', 'youtube', 'pluralsight', 'linkedin']:
                if platform in title.lower():
                    provider = platform.title()
                    break
            
            return LearningResource(
                title=title,
                description=data.get('description', '').strip(),
                resource_type=resource_type,
                provider=provider,
                skills_covered=[skill],
                difficulty=SkillLevel.INTERMEDIATE,  # Default
                cost="Varies"  # Default
            )
            
        except Exception as e:
            logger.warning(f"Failed to create learning resource from parsed data: {str(e)}")
            return None
    
    def _filter_resources_by_constraints(
        self, 
        resources: List[LearningResource], 
        learning_style: str, 
        budget: str, 
        duration: str
    ) -> List[LearningResource]:
        """
        Filter resources based on learning constraints
        
        Args:
            resources: List of resources to filter
            learning_style: Learning style preference
            budget: Budget constraints
            duration: Available duration
            
        Returns:
            Filtered list of resources
        """
        filtered = []
        
        for resource in resources:
            # Budget filtering
            if budget.lower() == "free" and resource.cost and "free" not in resource.cost.lower():
                continue
            elif budget.lower() == "low" and resource.cost and any(expensive in resource.cost.lower() for expensive in ["$100", "$200", "$300"]):
                continue
            
            # Learning style filtering
            if learning_style == "visual" and resource.resource_type not in [ResourceType.VIDEO, ResourceType.COURSE]:
                continue
            elif learning_style == "hands-on" and resource.resource_type not in [ResourceType.PROJECT, ResourceType.PRACTICE]:
                continue
            elif learning_style == "reading" and resource.resource_type not in [ResourceType.BOOK, ResourceType.ARTICLE]:
                continue
            
            filtered.append(resource)
        
        # Sort by relevance and quality indicators
        return sorted(filtered, key=lambda r: (
            r.rating or 0,
            1 if r.provider else 0,
            len(r.skills_covered)
        ), reverse=True)
    
    def _calculate_confidence(self, result: Dict[str, Any], request: AgentRequest) -> float:
        """
        Calculate confidence score for the response
        
        Args:
            result: Generated result
            request: Original request
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        base_confidence = 0.8
        
        # Adjust based on result completeness
        resources_count = len(result.get("learning_resources", []))
        if resources_count >= 5:
            base_confidence += 0.05
        elif resources_count < 2:
            base_confidence -= 0.1
        
        # Adjust based on request type
        if request.request_type == RequestType.LEARNING_PATH:
            base_confidence += 0.05  # This is our specialty
        
        # Adjust based on user context availability
        if request.content.get("user_id"):
            base_confidence += 0.05
        
        return min(max(base_confidence, 0.0), 1.0)
    
    # System prompts and helper methods
    def _get_learning_analysis_system_prompt(self) -> str:
        """Get system prompt for learning analysis"""
        return """You are a learning and development specialist with expertise in personalized education, 
        skill development, and learning path optimization. Create comprehensive, realistic learning plans 
        that consider individual constraints, learning styles, and career objectives."""
    
    def _get_learning_resource_advice_system_prompt(self) -> str:
        """Get system prompt for learning resource advice"""
        return """You are a learning resource curator and educational advisor with extensive knowledge 
        of online learning platforms, educational materials, and skill development strategies. 
        Provide specific, actionable recommendations that match user needs and constraints."""
    
    def _create_learning_resource_advice_prompt(self, question: str, user_context: Dict[str, Any]) -> str:
        """Create prompt for learning resource advice"""
        return f"""
        Provide learning resource advice for the following question:
        
        Question: {question}
        
        User Context:
        {json.dumps(user_context, indent=2)}
        
        Please provide comprehensive advice that includes:
        1. Specific resource recommendations (courses, books, platforms)
        2. Learning strategies and approaches
        3. Skill development pathways
        4. Practical application opportunities
        5. Community and support resources
        6. Progress tracking and validation methods
        
        Focus on actionable, specific recommendations that match the user's context and constraints.
        """
    
    # Helper methods for loading knowledge bases
    def _load_learning_platforms(self) -> Dict[str, Any]:
        """Load learning platforms database"""
        return {
            "coursera": {
                "type": "MOOC",
                "strengths": ["University partnerships", "Certificates", "Structured courses"],
                "cost_model": "Subscription or per-course",
                "best_for": ["Academic subjects", "Professional certificates"]
            },
            "udemy": {
                "type": "Marketplace",
                "strengths": ["Practical skills", "Lifetime access", "Frequent sales"],
                "cost_model": "One-time purchase",
                "best_for": ["Technical skills", "Creative skills", "Business skills"]
            },
            "pluralsight": {
                "type": "Professional",
                "strengths": ["Technology focus", "Skill assessments", "Learning paths"],
                "cost_model": "Subscription",
                "best_for": ["Software development", "IT skills", "Creative tools"]
            },
            "edx": {
                "type": "MOOC",
                "strengths": ["University courses", "Free options", "MicroMasters"],
                "cost_model": "Free with paid certificates",
                "best_for": ["Academic subjects", "Computer science", "Data science"]
            }
        }
    
    def _load_certification_database(self) -> Dict[str, Any]:
        """Load certification database"""
        return {
            "aws": {
                "certifications": ["Cloud Practitioner", "Solutions Architect", "Developer"],
                "industry_value": "High",
                "difficulty": "Medium to High",
                "cost": "$100-300 per exam"
            },
            "google_cloud": {
                "certifications": ["Cloud Engineer", "Data Engineer", "Cloud Architect"],
                "industry_value": "High",
                "difficulty": "Medium to High",
                "cost": "$200 per exam"
            },
            "microsoft": {
                "certifications": ["Azure Fundamentals", "Azure Developer", "Azure Solutions Architect"],
                "industry_value": "High",
                "difficulty": "Medium to High",
                "cost": "$165 per exam"
            }
        }
    
    def _load_project_templates(self) -> Dict[str, Any]:
        """Load project templates database"""
        return {
            "web_development": [
                {
                    "title": "Personal Portfolio Website",
                    "skills": ["HTML", "CSS", "JavaScript", "Responsive Design"],
                    "difficulty": "Beginner",
                    "duration": "2-3 weeks"
                },
                {
                    "title": "E-commerce Application",
                    "skills": ["React", "Node.js", "Database", "Payment Integration"],
                    "difficulty": "Intermediate",
                    "duration": "6-8 weeks"
                }
            ],
            "data_science": [
                {
                    "title": "Data Analysis Dashboard",
                    "skills": ["Python", "Pandas", "Visualization", "Streamlit"],
                    "difficulty": "Beginner",
                    "duration": "3-4 weeks"
                },
                {
                    "title": "Machine Learning Model",
                    "skills": ["Python", "Scikit-learn", "Feature Engineering", "Model Deployment"],
                    "difficulty": "Intermediate",
                    "duration": "4-6 weeks"
                }
            ]
        }
    
    # Additional helper methods would be implemented here...
    # (Continuing with placeholder implementations for brevity)
    
    async def _handle_collaboration_request(self, message):
        """Handle collaboration requests from other agents"""
        pass
    
    async def _handle_context_share(self, message):
        """Handle context sharing from other agents"""
        pass
    
    async def _handle_insight_share(self, message):
        """Handle insight sharing from other agents"""
        pass
    
    def _extract_learning_info_from_text(self, text: str) -> Dict[str, List[str]]:
        """Extract learning information from text"""
        return {"courses": [], "certifications": []}
    
    def _calculate_skill_complexity_scores(self, skills: List[str]) -> Dict[str, float]:
        """Calculate complexity scores for skills"""
        return {skill: 0.5 for skill in skills}
    
    def _assess_timeline_feasibility(self, skills: List[str], timeline: str) -> str:
        """Assess if timeline is feasible for learning skills"""
        return "Feasible"
    
    def _estimate_budget_requirements(self, skills: List[str], budget: str) -> Dict[str, Any]:
        """Estimate budget requirements"""
        return {"estimated_cost": "$200-500", "budget_match": "Good"}
    
    def _assess_learning_style_match(self, learning_style: str, skills: List[str]) -> str:
        """Assess how well learning style matches skills"""
        return "Good match"
    
    async def _parse_learning_path_structure(self, content: str, timeline: str) -> List[Dict[str, Any]]:
        """Parse learning path structure from AI content"""
        return [
            {
                "number": 1,
                "name": "Foundation Phase",
                "duration": "4 weeks",
                "skills": ["Basic concepts"],
                "objectives": ["Build foundation"]
            }
        ]
    
    def _calculate_total_learning_hours(self, learning_path: List[Dict[str, Any]]) -> int:
        """Calculate total learning hours"""
        return 120  # Default estimate
    
    def _analyze_difficulty_progression(self, learning_path: List[Dict[str, Any]]) -> str:
        """Analyze difficulty progression"""
        return "Progressive increase from beginner to intermediate"
    
    async def _create_learning_strategy(self, learning_style: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create learning strategy"""
        return {"approach": "Mixed learning with emphasis on " + learning_style}
    
    def _create_progress_tracking_plan(self, learning_path: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create progress tracking plan"""
        return {"checkpoints": "Weekly assessments", "milestones": "Phase completions"}
    
    def _create_adaptation_guidelines(self, learning_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create adaptation guidelines"""
        return {"flexibility": "Adjust pace based on progress", "alternatives": "Multiple resource options"}
    
    # Additional placeholder methods for completeness...
    async def _analyze_career_transition_resource_needs(self, current_role: str, target_role: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        return {"needs": "Skill development resources"}
    
    async def _get_external_learning_resources(self, resource_needs: Dict[str, Any], target_role: str) -> List[LearningResource]:
        return []
    
    async def _recommend_role_certifications(self, target_role: str, user_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []
    
    async def _suggest_portfolio_projects(self, target_role: str, resource_needs: Dict[str, Any], user_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []
    
    async def _allocate_resources_to_phases(self, external_resources: List[LearningResource], certifications: List[Dict[str, Any]], projects: List[Dict[str, Any]], timeline: str) -> Dict[str, Any]:
        return {}
    
    def _prioritize_learning_resources(self, phase_resources: Dict[str, Any]) -> Dict[str, Any]:
        return {"priority": "High-impact resources first"}
    
    def _analyze_learning_costs(self, phase_resources: Dict[str, Any]) -> Dict[str, Any]:
        return {"total_cost": "$300-600", "cost_breakdown": "Per phase analysis"}
    
    def _calculate_time_investment(self, phase_resources: Dict[str, Any]) -> Dict[str, Any]:
        return {"total_hours": 120, "weekly_commitment": "10-15 hours"}
    
    def _determine_skill_level_needed(self, skill: str, skill_gaps: Dict[str, Any]) -> str:
        return "intermediate"
    
    async def _recommend_resources_for_skill(self, skill: str, skill_level: str, user_context: Dict[str, Any]) -> List[LearningResource]:
        return []
    
    async def _optimize_skill_learning_sequence(self, skills: List[str], skill_resources: Dict[str, Any], priority_skills: List[str]) -> List[Dict[str, Any]]:
        return []
    
    async def _recommend_skill_validation_methods(self, skills: List[str], user_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []
    
    async def _suggest_cross_skill_projects(self, skills: List[str]) -> List[Dict[str, Any]]:
        return []
    
    def _recommend_learning_communities(self, skills: List[str]) -> List[Dict[str, Any]]:
        return []
    
    def _identify_mentorship_opportunities(self, skills: List[str]) -> List[Dict[str, Any]]:
        return []
    
    async def _extract_resource_recommendations_from_advice(self, advice_content: str, question: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_learning_strategies(self, advice_content: str) -> List[str]:
        return []
    
    def _suggest_platforms_for_question(self, question: str) -> List[str]:
        return []
    
    def _generate_learning_next_steps(self, advice_content: str) -> List[str]:
        return []
    
    async def _create_learning_milestone_plan(self, learning_path: List[Dict[str, Any]], timeline: str) -> Dict[str, Any]:
        return {"milestones": "Phase-based checkpoints"}
    
    async def _suggest_learning_projects(self, skills: List[str], current_level: str, timeline: str) -> List[Dict[str, Any]]:
        return []
    
    async def _suggest_phase_projects(self, skills: List[str], objectives: List[str]) -> List[Dict[str, Any]]:
        return []
    
    async def _recommend_phase_assessments(self, skills: List[str]) -> List[Dict[str, Any]]:
        return []
    
    def _calculate_phase_cost(self, resources: List[LearningResource]) -> str:
        return "$100-200"
    
    def _calculate_phase_time(self, resources: List[LearningResource], duration: str) -> str:
        return "20-30 hours"