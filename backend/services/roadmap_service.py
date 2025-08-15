import asyncio
import json
import logging
import re
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import uuid

from models.roadmap import (
    Roadmap, RoadmapPhase, Skill, LearningResource, Milestone,
    RoadmapRequest, RoadmapGenerationResult, SkillLevel, ResourceType
)
from services.ai_service import get_ai_service, ModelType
from services.roadmap_scraper import get_roadmap_scraper
from services.database_service import DatabaseService

# Optional embedding service import
try:
    from services.embedding_service import get_embedding_service
    EMBEDDING_AVAILABLE = True
except ImportError:
    get_embedding_service = None
    EMBEDDING_AVAILABLE = False

logger = logging.getLogger(__name__)

class RoadmapService:
    """Service for generating and managing career roadmaps"""
    
    def __init__(self):
        self.ai_service = None
        self.scraper = None
        self.embedding_service = None
        self.db_service = DatabaseService()
    
    async def _init_services(self):
        """Initialize required services"""
        if not self.ai_service:
            self.ai_service = await get_ai_service()
        if not self.scraper:
            self.scraper = await get_roadmap_scraper()
        if not self.embedding_service and EMBEDDING_AVAILABLE:
            try:
                self.embedding_service = get_embedding_service()
            except Exception as e:
                logger.warning(f"Could not initialize embedding service: {str(e)}")
                self.embedding_service = None
    
    def _create_roadmap_generation_prompt(
        self,
        current_role: str,
        target_role: str,
        user_background: str,
        timeline_preference: Optional[str] = None,
        focus_areas: List[str] = None,
        constraints: List[str] = None,
        learning_resources: List[LearningResource] = None
    ) -> str:
        """Create LangChain-style prompt for roadmap generation"""
        
        focus_areas = focus_areas or []
        learning_resources = learning_resources or []
        
        # Build resource context
        resource_context = ""
        if learning_resources:
            resource_context = "\n\nAvailable Learning Resources:\n"
            for resource in learning_resources[:10]:  # Limit to avoid token overflow
                resource_context += f"- {resource.title} ({resource.provider}): {resource.description}\n"
                if resource.skills_covered:
                    resource_context += f"  Skills: {', '.join(resource.skills_covered)}\n"
        
        # Build focus areas context
        focus_context = ""
        if focus_areas:
            focus_context = f"\n\nSpecial Focus Areas: {', '.join(focus_areas)}"
        
        # Timeline context
        timeline_context = ""
        if timeline_preference:
            timeline_context = f"\n\nPreferred Timeline: {timeline_preference}"
        
        # Build constraints context with emphasis
        constraints_context = ""
        if constraints:
            constraints_context = f"\n\nIMPORTANT CONSTRAINTS TO CONSIDER:\n"
            for constraint in constraints:
                constraints_context += f"- {constraint}\n"
            constraints_context += "These constraints MUST be reflected in the roadmap design, timeline, and milestone planning."

        prompt = f"""You are an expert career advisor creating a detailed, actionable career roadmap. 
Create a structured transition plan from {current_role} to {target_role}.

User Background:
{user_background}
{timeline_context}
{focus_context}
{constraints_context}
{resource_context}

Create a roadmap with the following structure:

ROADMAP TITLE: [Create a compelling title]

OVERVIEW: [2-3 sentence summary of the transition strategy, considering user constraints and focus areas]

PHASE 1: [Phase Title]
Duration: [X weeks - adjust based on user constraints and timeline preference]
Description: [What this phase accomplishes, considering user constraints]
Skills to Develop:
- [Skill 1]: [Current level] → [Target level] ([Priority 1-5])
- [Skill 2]: [Current level] → [Target level] ([Priority 1-5])
Learning Resources:
- [Resource 1]: [Description] ([Duration])
- [Resource 2]: [Description] ([Duration])
Milestones (3-5 MILESTONES RECOMMENDED):
- Week [X]: [Milestone title] - [Detailed description with specific steps, estimated time (e.g., 10-15 hours), and success criteria. Include specific links to courses, tutorials, or resources when applicable. Consider user constraints in time estimates.]
- Week [Y]: [Milestone title] - [Detailed description with specific steps, estimated time, and success criteria. Include specific links to courses, tutorials, or resources when applicable. Consider user constraints in time estimates.]
- Week [Z]: [Milestone title] - [Detailed description with specific steps, estimated time, and success criteria. Include specific links to courses, tutorials, or resources when applicable. Consider user constraints in time estimates.]
[Add 1-2 more milestones if the phase duration and complexity warrant it]
Prerequisites: [What's needed before starting, considering user constraints]
Outcomes: [What you'll achieve after completion]

PHASE 2: [Phase Title]
[Same structure as Phase 1 - 3-5 MILESTONES RECOMMENDED based on phase complexity]

[Continue for 3-6 phases total - EACH PHASE SHOULD HAVE 3-5 MILESTONES based on complexity and duration]

TOTAL TIMELINE: [X weeks/months - must align with user timeline preference and constraints]

KEY SUCCESS FACTORS:
- [Factor 1 - consider user constraints]
- [Factor 2 - consider user focus areas]
- [Factor 3 - consider user background]

POTENTIAL CHALLENGES:
- [Challenge 1]: [Mitigation strategy considering user constraints]
- [Challenge 2]: [Mitigation strategy considering user constraints]

CRITICAL REQUIREMENTS:
- Each phase should have 3-5 milestones based on complexity and duration
- Each milestone MUST include detailed steps, estimated time commitment, and specific resources/links
- Include real course names, tutorial links, and specific tools/technologies
- Make milestones actionable with clear deliverables
- Ensure each phase builds logically on the previous one
- Reference specific technologies, frameworks, and industry standards relevant to the target role
- ALWAYS consider and accommodate user constraints in timeline, resource recommendations, and time estimates
- Tailor the roadmap to user's focus areas and background experience
- Adjust milestone complexity and number based on phase duration and user constraints"""

        return prompt
    
    def _parse_roadmap_response(self, response: str, request: RoadmapRequest) -> Roadmap:
        """Parse AI response into structured Roadmap object"""
        
        # Extract title
        title_match = re.search(r'ROADMAP TITLE:\s*(.+)', response, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else f"{request.current_role} to {request.target_role} Roadmap"
        
        # Extract overview
        overview_match = re.search(r'OVERVIEW:\s*(.+?)(?=\n\n|\nPHASE)', response, re.IGNORECASE | re.DOTALL)
        description = overview_match.group(1).strip() if overview_match else ""
        
        # Extract phases
        phases = self._extract_phases(response)
        
        # Calculate total timeline
        total_weeks = sum(phase.duration_weeks for phase in phases)
        
        # Create roadmap
        roadmap = Roadmap(
            id=str(uuid.uuid4()),
            user_id="",  # Will be set by the API endpoint
            title=title,
            description=description,
            current_role=request.current_role,
            target_role=request.target_role,
            phases=phases,
            total_estimated_weeks=total_weeks,
            generated_with_model="AI Generated",
            user_context_used={
                "background": request.user_background,
                "timeline_preference": request.timeline_preference,
                "focus_areas": request.focus_areas,
                "constraints": request.constraints
            }
        )
        
        return roadmap
    
    def _extract_phases(self, response: str) -> List[RoadmapPhase]:
        """Extract phases from AI response"""
        phases = []
        
        # Find all phase sections
        phase_pattern = r'PHASE\s+(\d+):\s*(.+?)(?=PHASE\s+\d+:|TOTAL TIMELINE:|KEY SUCCESS FACTORS:|$)'
        phase_matches = re.findall(phase_pattern, response, re.IGNORECASE | re.DOTALL)
        
        for phase_num, phase_content in phase_matches:
            phase = self._parse_phase_content(int(phase_num), phase_content.strip())
            if phase:
                phases.append(phase)
        
        return phases
    
    def _parse_phase_content(self, phase_number: int, content: str) -> Optional[RoadmapPhase]:
        """Parse individual phase content"""
        try:
            # Extract title (first line after phase number)
            lines = content.split('\n')
            title = lines[0].strip() if lines else f"Phase {phase_number}"
            
            # Extract duration
            duration_match = re.search(r'Duration:\s*(\d+)\s*weeks?', content, re.IGNORECASE)
            duration_weeks = int(duration_match.group(1)) if duration_match else 4
            
            # Extract description
            desc_match = re.search(r'Description:\s*(.+?)(?=\n[A-Z]|\nSkills|\nLearning|\nMilestones)', content, re.IGNORECASE | re.DOTALL)
            description = desc_match.group(1).strip() if desc_match else ""
            
            # Extract skills
            skills = self._extract_skills_from_content(content)
            
            # Extract learning resources
            learning_resources = self._extract_learning_resources_from_content(content)
            
            # Extract milestones
            milestones = self._extract_milestones_from_content(content)
            
            # Extract prerequisites and outcomes
            prerequisites = self._extract_list_items(content, r'Prerequisites:\s*(.+?)(?=\n[A-Z]|$)')
            outcomes = self._extract_list_items(content, r'Outcomes:\s*(.+?)(?=\n[A-Z]|$)')
            
            phase = RoadmapPhase(
                phase_number=phase_number,
                title=title,
                description=description,
                duration_weeks=duration_weeks,
                skills_to_develop=skills,
                learning_resources=learning_resources,
                milestones=milestones,
                prerequisites=prerequisites,
                outcomes=outcomes
            )
            
            return phase
            
        except Exception as e:
            logger.error(f"Error parsing phase {phase_number}: {str(e)}")
            return None
    
    def _extract_skills_from_content(self, content: str) -> List[Skill]:
        """Extract skills from phase content"""
        skills = []
        
        # Find skills section
        skills_match = re.search(r'Skills to Develop:\s*(.+?)(?=\nLearning Resources:|$)', content, re.IGNORECASE | re.DOTALL)
        if not skills_match:
            return skills
        
        skills_text = skills_match.group(1)
        
        # Parse individual skills
        skill_lines = [line.strip() for line in skills_text.split('\n') if line.strip().startswith('-')]
        
        for line in skill_lines:
            # Parse format: - Skill Name: beginner → intermediate (Priority 3)
            skill_match = re.search(r'-\s*([^:]+):\s*(\w+)\s*→\s*(\w+)\s*\(Priority\s*(\d+)\)', line, re.IGNORECASE)
            if skill_match:
                name = skill_match.group(1).strip()
                current_level = self._parse_skill_level(skill_match.group(2))
                target_level = self._parse_skill_level(skill_match.group(3))
                priority = int(skill_match.group(4))
                
                skill = Skill(
                    name=name,
                    current_level=current_level,
                    target_level=target_level,
                    priority=priority
                )
                skills.append(skill)
            else:
                # Fallback: just extract skill name
                skill_name = line.replace('-', '').strip()
                if skill_name:
                    skill = Skill(name=skill_name)
                    skills.append(skill)
        
        return skills
    
    def _extract_learning_resources_from_content(self, content: str) -> List[LearningResource]:
        """Extract learning resources from phase content"""
        resources = []
        
        # Find learning resources section
        resources_match = re.search(r'Learning Resources:\s*(.+?)(?=\nMilestones:|$)', content, re.IGNORECASE | re.DOTALL)
        if not resources_match:
            return resources
        
        resources_text = resources_match.group(1)
        
        # Parse individual resources
        resource_lines = [line.strip() for line in resources_text.split('\n') if line.strip().startswith('-')]
        
        for line in resource_lines:
            # Parse format: - Resource Name: Description (Duration)
            resource_match = re.search(r'-\s*([^:]+):\s*([^(]+)\s*\(([^)]+)\)', line)
            if resource_match:
                title = resource_match.group(1).strip()
                description = resource_match.group(2).strip()
                duration = resource_match.group(3).strip()
                
                resource = LearningResource(
                    title=title,
                    description=description,
                    duration=duration,
                    resource_type=ResourceType.COURSE,
                    provider=""
                )
                resources.append(resource)
        
        return resources
    
    def _extract_milestones_from_content(self, content: str) -> List[Milestone]:
        """Extract milestones from phase content with detailed descriptions"""
        milestones = []
        
        # Find milestones section
        milestones_match = re.search(r'Milestones.*?:\s*(.+?)(?=\nPrerequisites:|$)', content, re.IGNORECASE | re.DOTALL)
        if not milestones_match:
            return milestones
        
        milestones_text = milestones_match.group(1)
        
        # Split by milestone markers (- Week X:)
        milestone_sections = re.split(r'(?=- Week \d+:)', milestones_text)
        
        for section in milestone_sections:
            section = section.strip()
            if not section or not section.startswith('- Week'):
                continue
                
            # Parse format: - Week X: Milestone title - Detailed description...
            milestone_match = re.search(r'- Week\s*(\d+):\s*([^-]+)\s*-\s*(.+)', section, re.IGNORECASE | re.DOTALL)
            if milestone_match:
                week = int(milestone_match.group(1))
                title = milestone_match.group(2).strip()
                full_description = milestone_match.group(3).strip()
                
                # Extract links from description
                links = re.findall(r'https?://[^\s\)]+', full_description)
                
                # Extract estimated time if mentioned
                time_match = re.search(r'(\d+[-–]\d+|\d+)\s*hours?', full_description, re.IGNORECASE)
                estimated_hours = time_match.group(1) if time_match else None
                
                # Split description into main description and success criteria
                # Look for patterns like "Success criteria:", "You will:", "Deliverables:", etc.
                criteria_patterns = [
                    r'Success criteria?:\s*(.+?)(?=\n|$)',
                    r'You will:\s*(.+?)(?=\n|$)',
                    r'Deliverables?:\s*(.+?)(?=\n|$)',
                    r'Complete when:\s*(.+?)(?=\n|$)'
                ]
                
                success_criteria = []
                description = full_description
                
                for pattern in criteria_patterns:
                    criteria_match = re.search(pattern, full_description, re.IGNORECASE | re.DOTALL)
                    if criteria_match:
                        criteria_text = criteria_match.group(1).strip()
                        # Split by common delimiters
                        criteria_items = [item.strip() for item in re.split(r'[,;]|\sand\s', criteria_text) if item.strip()]
                        success_criteria.extend(criteria_items)
                        # Remove criteria from description
                        description = re.sub(pattern, '', description, flags=re.IGNORECASE | re.DOTALL).strip()
                        break
                
                # If no explicit success criteria found, use the full description as one criterion
                if not success_criteria:
                    success_criteria = [full_description]
                
                # Create deliverables from description if mentioned
                deliverables = []
                deliverable_patterns = [
                    r'build\s+([^,.]+)',
                    r'create\s+([^,.]+)',
                    r'develop\s+([^,.]+)',
                    r'implement\s+([^,.]+)',
                    r'complete\s+([^,.]+)'
                ]
                
                for pattern in deliverable_patterns:
                    matches = re.findall(pattern, description, re.IGNORECASE)
                    deliverables.extend([match.strip() for match in matches])
                
                milestone = Milestone(
                    title=title,
                    description=description,
                    estimated_completion_weeks=week,
                    success_criteria=success_criteria[:3],  # Limit to 3 criteria
                    deliverables=deliverables[:2] if deliverables else []  # Limit to 2 deliverables
                )
                milestones.append(milestone)
        
        return milestones
    
    def _extract_list_items(self, content: str, pattern: str) -> List[str]:
        """Extract list items using regex pattern"""
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if not match:
            return []
        
        text = match.group(1)
        items = []
        
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('-'):
                items.append(line.replace('-', '').strip())
            elif line and not line.startswith('['):
                items.append(line)
        
        return [item for item in items if item]
    
    def _parse_skill_level(self, level_str: str) -> SkillLevel:
        """Parse skill level string to enum"""
        level_lower = level_str.lower().strip()
        
        if level_lower in ['beginner', 'basic', 'novice']:
            return SkillLevel.BEGINNER
        elif level_lower in ['intermediate', 'medium', 'mid']:
            return SkillLevel.INTERMEDIATE
        elif level_lower in ['advanced', 'high', 'senior']:
            return SkillLevel.ADVANCED
        elif level_lower in ['expert', 'master', 'guru']:
            return SkillLevel.EXPERT
        else:
            return SkillLevel.INTERMEDIATE
    
    async def _generate_strengths_weaknesses_analysis(
        self,
        request: RoadmapRequest,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate analysis of user's current strengths and weaknesses for the target role"""
        
        try:
            # Build context from user background and resume
            context_text = request.user_background or ""
            if user_context:
                resume_context = user_context.get('resume_summary', '')
                if resume_context:
                    context_text += f"\n\nResume Summary: {resume_context}"
            
            # Build additional context for analysis
            focus_areas_text = ""
            if request.focus_areas:
                focus_areas_text = f"\nFocus Areas: {', '.join(request.focus_areas)}"
            
            constraints_text = ""
            if request.constraints:
                constraints_text = f"\nConstraints: {', '.join(request.constraints)}"
            
            timeline_text = ""
            if request.timeline_preference:
                timeline_text = f"\nTimeline Preference: {request.timeline_preference}"

            analysis_prompt = f"""Analyze the user's current strengths and weaknesses for transitioning from {request.current_role} to {request.target_role}.

User Background:
{context_text}

Current Role: {request.current_role}
Target Role: {request.target_role}{timeline_text}{focus_areas_text}{constraints_text}

Provide a concise analysis in the following format:

ROADMAP RATIONALE:
[Provide a 1-2 paragraph explanation of WHY this specific roadmap was created based on their background, focus areas, constraints, and timeline preference. Be specific about key technologies or experiences that influenced the roadmap design. Explain how the roadmap addresses their constraints and emphasizes their focus areas.]

CURRENT STRENGTHS:
- [Strength 1]: [Brief explanation, considering how it relates to focus areas]
- [Strength 2]: [Brief explanation, considering how it relates to focus areas]
- [Strength 3]: [Brief explanation, considering how it relates to focus areas]

AREAS FOR IMPROVEMENT:
- [Gap 1]: [Why important for target role, considering focus areas]
- [Gap 2]: [Why important for target role, considering focus areas]
- [Gap 3]: [Why important for target role, considering focus areas]

KEY TRANSFERABLE SKILLS:
- [Skill 1]: [How it applies to target role and focus areas]
- [Skill 2]: [How it applies to target role and focus areas]

BIGGEST CHALLENGES:
- [Challenge 1]: [Brief mitigation approach considering user constraints]
- [Challenge 2]: [Brief mitigation approach considering user constraints]

COMPETITIVE ADVANTAGES:
- [Advantage 1]: [Why this helps you stand out in the target role]
- [Advantage 2]: [Why this helps you stand out in the target role]

Keep explanations concise and actionable. Always reference the user's constraints and focus areas where relevant."""

            response = await self.ai_service.generate_text(
                prompt=analysis_prompt,
                model_type=ModelType.GEMINI_FLASH,
                max_tokens=1200,
                temperature=0.7
            )
            
            # Parse the analysis into structured data
            analysis = self._parse_strengths_weaknesses_response(response)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error generating strengths/weaknesses analysis: {str(e)}")
            return {
                "roadmap_rationale": "",
                "strengths": [],
                "weaknesses": [],
                "transferable_skills": [],
                "challenges": [],
                "advantages": []
            }
    
    def _parse_strengths_weaknesses_response(self, response: str) -> Dict[str, Any]:
        """Parse the strengths/weaknesses analysis response"""
        
        analysis = {
            "roadmap_rationale": "",
            "strengths": [],
            "weaknesses": [],
            "transferable_skills": [],
            "challenges": [],
            "advantages": []
        }
        
        # Extract roadmap rationale first
        rationale_match = re.search(r'ROADMAP RATIONALE:\s*(.+?)(?=\nCURRENT STRENGTHS:|$)', response, re.IGNORECASE | re.DOTALL)
        if rationale_match:
            analysis["roadmap_rationale"] = rationale_match.group(1).strip()
        
        # Extract each section
        sections = {
            "strengths": r'CURRENT STRENGTHS:\s*(.+?)(?=\nAREAS FOR IMPROVEMENT:|$)',
            "weaknesses": r'AREAS FOR IMPROVEMENT:\s*(.+?)(?=\nKEY TRANSFERABLE SKILLS:|$)',
            "transferable_skills": r'KEY TRANSFERABLE SKILLS:\s*(.+?)(?=\nBIGGEST CHALLENGES:|$)',
            "challenges": r'BIGGEST CHALLENGES:\s*(.+?)(?=\nCOMPETITIVE ADVANTAGES:|$)',
            "advantages": r'COMPETITIVE ADVANTAGES:\s*(.+?)(?=\n[A-Z]|$)'
        }
        
        for key, pattern in sections.items():
            match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
            if match:
                section_text = match.group(1).strip()
                items = []
                
                for line in section_text.split('\n'):
                    line = line.strip()
                    if line.startswith('-'):
                        # Parse format: - Item: Description
                        item_match = re.match(r'-\s*([^:]+):\s*(.+)', line)
                        if item_match:
                            items.append({
                                "title": item_match.group(1).strip(),
                                "description": item_match.group(2).strip()
                            })
                        else:
                            # Fallback: just the item text
                            items.append({
                                "title": line.replace('-', '').strip(),
                                "description": ""
                            })
                
                analysis[key] = items
        
        return analysis
    
    async def generate_roadmap(
        self,
        request: RoadmapRequest,
        user_id: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> RoadmapGenerationResult:
        """Generate a career roadmap based on request"""
        
        start_time = datetime.utcnow()
        
        try:
            await self._init_services()
            
            # Generate strengths and weaknesses analysis first
            strengths_analysis = await self._generate_strengths_weaknesses_analysis(
                request, user_context
            )
            
            # Get learning resources from scraper
            learning_resources = await self.scraper.get_resources_for_transition(
                request.current_role,
                request.target_role,
                max_resources=15
            )
            
            # Enhance user background with context if available
            enhanced_background = request.user_background or ""
            if user_context:
                resume_context = user_context.get('resume_summary', '')
                if resume_context:
                    enhanced_background += f"\n\nResume Summary: {resume_context}"
            
            # Create generation prompt
            prompt = self._create_roadmap_generation_prompt(
                current_role=request.current_role,
                target_role=request.target_role,
                user_background=enhanced_background,
                timeline_preference=request.timeline_preference,
                focus_areas=request.focus_areas,
                constraints=request.constraints,
                learning_resources=learning_resources
            )
            
            # Generate roadmap using AI service
            response = await self.ai_service.generate_text(
                prompt=prompt,
                model_type=ModelType.GEMINI_FLASH,  # Use fast model for roadmap generation
                max_tokens=2000,
                temperature=0.7
            )
            
            # Parse response into structured roadmap
            roadmap = self._parse_roadmap_response(response, request)
            roadmap.user_id = user_id
            roadmap.generation_prompt = prompt[:500] + "..." if len(prompt) > 500 else prompt
            
            # Ensure each phase has at least 3 milestones
            await self._ensure_minimum_milestones(roadmap)
            
            # Enhance with scraped learning resources
            self._enhance_roadmap_with_resources(roadmap, learning_resources)
            
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"Generated roadmap for {user_id}: {request.current_role} → {request.target_role}")
            
            return RoadmapGenerationResult(
                success=True,
                roadmap=roadmap,
                generation_time_seconds=generation_time,
                model_used="Gemini Flash",
                strengths_analysis=strengths_analysis
            )
            
        except Exception as e:
            logger.error(f"Error generating roadmap: {str(e)}")
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            
            return RoadmapGenerationResult(
                success=False,
                error_message=str(e),
                generation_time_seconds=generation_time
            )
    
    def _calculate_target_milestone_count(self, phase: RoadmapPhase) -> int:
        """Calculate the target number of milestones for a phase based on duration and complexity"""
        
        # Base milestone count on phase duration
        if phase.duration_weeks <= 2:
            base_count = 3  # Short phases get minimum 3 milestones
        elif phase.duration_weeks <= 4:
            base_count = 4  # Medium phases get 4 milestones
        elif phase.duration_weeks <= 8:
            base_count = 5  # Longer phases get 5 milestones
        else:
            base_count = 6  # Very long phases get 6+ milestones
        
        # Adjust based on complexity (number of skills to develop)
        skill_count = len(phase.skills_to_develop)
        if skill_count > 5:
            base_count += 1  # Add extra milestone for complex phases
        elif skill_count < 2:
            base_count = max(3, base_count - 1)  # Reduce for simple phases, but keep minimum of 3
        
        # Ensure we stay within reasonable bounds (3-7 milestones)
        return max(3, min(7, base_count))

    async def _ensure_minimum_milestones(self, roadmap: Roadmap):
        """Ensure each phase has appropriate number of milestones (3-7 based on complexity), generate additional ones if needed"""
        
        for phase in roadmap.phases:
            # Determine target milestone count based on phase duration and complexity
            target_milestone_count = self._calculate_target_milestone_count(phase)
            
            if len(phase.milestones) < target_milestone_count:
                # Generate additional milestones for this phase
                missing_count = target_milestone_count - len(phase.milestones)
                
                try:
                    additional_milestones_prompt = f"""Generate {missing_count} additional detailed milestones for this phase:

Phase: {phase.title}
Description: {phase.description}
Duration: {phase.duration_weeks} weeks
Skills to develop: {', '.join([skill.name for skill in phase.skills_to_develop])}

Existing milestones:
{chr(10).join([f"- Week {m.estimated_completion_weeks}: {m.title}" for m in phase.milestones])}

Generate {missing_count} new milestones that:
1. Fill gaps in the timeline (weeks 1-{phase.duration_weeks})
2. Are specific and actionable
3. Include detailed descriptions with steps, estimated time (e.g., 8-12 hours), and resources
4. Have clear success criteria and deliverables
5. Build logically on existing milestones

Format each milestone as:
- Week [X]: [Milestone title] - [Detailed description with specific steps, estimated time commitment, success criteria, and relevant links/resources when applicable]

Only provide the milestone entries, no additional text."""

                    response = await self.ai_service.generate_text(
                        prompt=additional_milestones_prompt,
                        model_type=ModelType.GEMINI_FLASH,
                        max_tokens=800,
                        temperature=0.7
                    )
                    
                    # Parse the additional milestones
                    additional_milestones = self._extract_milestones_from_content(f"Milestones:\n{response}")
                    
                    # Add them to the phase
                    phase.milestones.extend(additional_milestones)
                    
                    # Sort milestones by week
                    phase.milestones.sort(key=lambda m: m.estimated_completion_weeks)
                    
                    logger.info(f"Added {len(additional_milestones)} milestones to phase {phase.phase_number}")
                    
                except Exception as e:
                    logger.error(f"Error generating additional milestones for phase {phase.phase_number}: {str(e)}")
                    
                    # Fallback: create basic milestones
                    for i in range(missing_count):
                        week = min(phase.duration_weeks, len(phase.milestones) + i + 1)
                        fallback_milestone = Milestone(
                            title=f"Complete {phase.title} Milestone {len(phase.milestones) + i + 1}",
                            description=f"Work on developing skills and completing objectives for {phase.title}. Spend 8-10 hours this week focusing on practical application and skill building.",
                            estimated_completion_weeks=week,
                            success_criteria=[f"Complete assigned tasks for week {week}", "Demonstrate progress in key skills"],
                            deliverables=[f"Week {week} progress report"]
                        )
                        phase.milestones.append(fallback_milestone)
                    
                    logger.info(f"Added {missing_count} fallback milestones to phase {phase.phase_number} (target: {target_milestone_count})")

    def _enhance_roadmap_with_resources(self, roadmap: Roadmap, scraped_resources: List[LearningResource]):
        """Enhance roadmap phases with scraped learning resources"""
        
        for phase in roadmap.phases:
            # Match resources to phase skills
            phase_skills = [skill.name.lower() for skill in phase.skills_to_develop]
            
            # Find relevant resources
            relevant_resources = []
            for resource in scraped_resources:
                resource_skills = [skill.lower() for skill in resource.skills_covered]
                
                # Check if resource matches any phase skill
                if any(phase_skill in resource_skill or resource_skill in phase_skill 
                       for phase_skill in phase_skills 
                       for resource_skill in resource_skills):
                    relevant_resources.append(resource)
            
            # Add top 3 relevant resources to phase
            phase.learning_resources.extend(relevant_resources[:3])
    
    async def get_roadmap_suggestions(
        self,
        current_role: str,
        user_background: str,
        max_suggestions: int = 5
    ) -> List[str]:
        """Get suggested target roles based on current role and background"""
        
        try:
            await self._init_services()
            
            prompt = f"""Based on the current role and background, suggest {max_suggestions} realistic career transition options.

Current Role: {current_role}
Background: {user_background}

Provide {max_suggestions} specific target roles that would be good career moves. Consider:
- Natural progression paths
- Transferable skills
- Market demand
- Growth potential

Format as a simple list:
1. [Target Role 1]
2. [Target Role 2]
3. [Target Role 3]
etc.

Only provide the role names, no additional explanation."""
            
            response = await self.ai_service.generate_text(
                prompt=prompt,
                model_type=ModelType.GEMINI_FLASH,
                max_tokens=300,
                temperature=0.8
            )
            
            # Parse suggestions
            suggestions = []
            for line in response.split('\n'):
                line = line.strip()
                if re.match(r'^\d+\.', line):
                    suggestion = re.sub(r'^\d+\.\s*', '', line).strip()
                    if suggestion:
                        suggestions.append(suggestion)
            
            return suggestions[:max_suggestions]
            
        except Exception as e:
            logger.error(f"Error getting roadmap suggestions: {str(e)}")
            return []
    
    # Database persistence methods
    async def save_roadmap(self, roadmap: Roadmap) -> str:
        """Save roadmap to database"""
        return await self.db_service.save_roadmap(roadmap)
    
    async def load_roadmap(self, roadmap_id: str) -> Optional[Roadmap]:
        """Load roadmap from database"""
        return await self.db_service.load_roadmap(roadmap_id)
    
    async def load_user_roadmaps(self, user_id: str) -> List[Roadmap]:
        """Load all roadmaps for a user"""
        return await self.db_service.load_user_roadmaps(user_id)
    
    async def update_roadmap_progress(self, roadmap_id: str, progress_data: Dict[str, Any]) -> bool:
        """Update roadmap progress"""
        return await self.db_service.update_roadmap_progress(roadmap_id, progress_data)
    
    async def delete_roadmap(self, roadmap_id: str) -> bool:
        """Delete a roadmap"""
        return await self.db_service.delete_roadmap(roadmap_id)

# Singleton instance
_roadmap_service_instance = None

async def get_roadmap_service() -> RoadmapService:
    """Get or create singleton roadmap service instance"""
    global _roadmap_service_instance
    
    if _roadmap_service_instance is None:
        _roadmap_service_instance = RoadmapService()
    
    return _roadmap_service_instance