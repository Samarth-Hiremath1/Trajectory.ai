export enum RoadmapStatus {
  DRAFT = "draft",
  ACTIVE = "active",
  COMPLETED = "completed",
  ARCHIVED = "archived"
}

export enum SkillLevel {
  BEGINNER = "beginner",
  INTERMEDIATE = "intermediate",
  ADVANCED = "advanced",
  EXPERT = "expert"
}

export enum ResourceType {
  COURSE = "course",
  CERTIFICATION = "certification",
  PROJECT = "project",
  BOOK = "book",
  ARTICLE = "article",
  VIDEO = "video",
  PRACTICE = "practice"
}

export interface Skill {
  name: string
  description?: string
  current_level: SkillLevel
  target_level: SkillLevel
  priority: number // 1 = highest, 5 = lowest
  estimated_hours?: number
}

export interface LearningResource {
  title: string
  description?: string
  url?: string
  resource_type: ResourceType
  provider?: string
  duration?: string
  cost?: string
  difficulty?: SkillLevel
  rating?: number
  skills_covered: string[]
}

export interface Milestone {
  title: string
  description?: string
  estimated_completion_weeks: number
  success_criteria: string[]
  deliverables: string[]
  is_completed: boolean
  completed_date?: Date
}

export interface RoadmapPhase {
  phase_number: number
  title: string
  description: string
  duration_weeks: number
  skills_to_develop: Skill[]
  learning_resources: LearningResource[]
  milestones: Milestone[]
  prerequisites: string[]
  outcomes: string[]
  is_completed: boolean
  started_date?: Date
  completed_date?: Date
}

export interface Roadmap {
  id: string
  user_id: string
  title: string
  description?: string
  current_role: string
  target_role: string
  status: RoadmapStatus
  phases: RoadmapPhase[]
  total_estimated_weeks: number
  created_date: Date
  updated_date: Date
  last_accessed_date?: Date
  overall_progress_percentage: number
  current_phase?: number
  generated_with_model?: string
  generation_prompt?: string
  user_context_used?: Record<string, unknown>
}

export interface RoadmapRequest {
  current_role: string
  target_role: string
  user_background?: string
  timeline_preference?: string
  focus_areas: string[]
  constraints: string[]
}

export interface RoadmapGenerationResponse {
  success: boolean
  roadmap: {
    id: string
    user_id?: string
    title: string
    description: string
    current_role: string
    target_role: string
    total_estimated_weeks: number
    phase_count: number
    phases: RoadmapPhase[]
    created_date: string
    strengths_analysis?: any
    generation_metadata: {
      model_used: string
      generation_time_seconds: number
      user_context_used: boolean
    }
  }
}

export interface CareerSuggestion {
  current_role: string
  suggestions: string[]
  count: number
}

export interface PhaseUpdateRequest {
  phase_number: number
  milestone_updates?: Array<Record<string, unknown>>
  is_completed?: boolean
  notes?: string
}