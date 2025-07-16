# Requirements Document

## Introduction

Trajectory.AI is a career navigation platform that provides personalized, AI-generated feedback and roadmaps to help users reach their target career goals. The platform combines user profile data, resume parsing, and AI-powered mentoring to create customized career development plans for roles like Software Engineer at FAANG companies, Product Manager at Meta, or consultant positions at MBB firms.

## Requirements

### Requirement 1

**User Story:** As a job seeker, I want to create an account and manage my profile, so that I can access personalized career guidance and save my progress.

#### Acceptance Criteria

1. WHEN a user visits the platform THEN the system SHALL provide email/password authentication via Supabase
2. WHEN a user successfully registers THEN the system SHALL create a user dashboard with saved career paths and profile metadata
3. WHEN a user accesses their profile THEN the system SHALL display a form to input background information including education, career status, and additional details
4. WHEN a user updates their profile THEN the system SHALL save the information for RAG-based personalization

### Requirement 2

**User Story:** As a user, I want to upload and have my resume parsed, so that the AI can understand my background and provide relevant career advice.

#### Acceptance Criteria

1. WHEN a user uploads a PDF resume THEN the system SHALL accept and process the file using pdfplumber or unstructured libraries
2. WHEN a resume is processed THEN the system SHALL chunk and embed the content using bge-small-en-v1.5 HuggingFace model
3. WHEN resume embeddings are created THEN the system SHALL store them in local ChromaDB for retrieval
4. WHEN resume parsing fails THEN the system SHALL provide clear error messages and allow re-upload

### Requirement 3

**User Story:** As a user, I want to chat with an AI mentor that knows my background, so that I can get personalized career advice and answers to specific questions.

#### Acceptance Criteria

1. WHEN a user initiates a chat THEN the system SHALL provide a memory-enabled agent that reflects on user roadmap and background
2. WHEN a user asks career-related questions THEN the system SHALL use RAG to provide personalized feedback based on their profile and resume
3. WHEN a user asks questions like "What am I missing for PM interviews?" THEN the system SHALL provide specific, actionable advice
4. WHEN a user requests alternative career paths THEN the system SHALL suggest relevant role transitions based on their background

### Requirement 4

**User Story:** As a user, I want to generate a personalized career roadmap, so that I can follow a structured plan to reach my target role.

#### Acceptance Criteria

1. WHEN a user inputs current and target roles THEN the system SHALL accept role combinations like "SWE → PM" or "Consultant → AI Researcher"
2. WHEN roadmap generation is requested THEN the system SHALL use LangChain prompts combining profile and embedded resume chunks
3. WHEN a roadmap is generated THEN the system SHALL provide a phase-based plan with skills, certifications, projects, and time estimates
4. WHEN generating recommendations THEN the system SHALL use Hugging Face Inference API with Mistral-7B or Gemma models
5. WHEN creating roadmaps THEN the system SHALL reference roadmap.sh resources and embedded skill/course/project documentation
6. WHEN suggesting learning resources THEN the system SHALL use LangChain retriever to augment roadmap suggestions with scraped content from platforms like Coursera

### Requirement 5

**User Story:** As a user, I want to save and load my career data, so that I can track my progress and continue my career development over time.

#### Acceptance Criteria

1. WHEN a user completes their profile or roadmap THEN the system SHALL save resume, roadmap, and profile state via Supabase database
2. WHEN a user returns to the platform THEN the system SHALL load their saved data and display their current progress
3. WHEN a user wants to modify their information THEN the system SHALL enable edit functionality for all saved data
4. WHEN a user wants to share their roadmap THEN the system SHALL provide export features

### Requirement 6

**User Story:** As a user, I want a daily dashboard to track my career development, so that I can stay organized and motivated in pursuing my goals.

#### Acceptance Criteria

1. WHEN a user accesses their daily dashboard THEN the system SHALL display a planned calendar with career development activities
2. WHEN a user views their dashboard THEN the system SHALL show personalized to-do lists based on their roadmap
3. WHEN a user wants to take notes THEN the system SHALL provide note-taking functionality integrated with their career plan
4. WHEN a user returns daily THEN the system SHALL update their dashboard with progress tracking and next steps

### Requirement 7

**User Story:** As a user, I want a streamlined user flow that prioritizes the core AI features, so that I can quickly access career guidance after initial setup.

#### Acceptance Criteria

1. WHEN a new user first visits THEN the system SHALL guide them through account setup and information entry (profile + resume upload)
2. WHEN a user completes initial setup THEN the system SHALL redirect them to the main page featuring LLM chat and roadmap generation
3. WHEN a returning user logs in THEN the system SHALL land them directly on the main page with LLM chat and roadmap generation
4. WHEN a user wants to modify their information THEN the system SHALL provide easily accessible edit functionality for previously entered profile and resume data
5. WHEN a user edits their information THEN the system SHALL update their RAG context and return them to the main page

### Requirement 8

**User Story:** As a system administrator, I want the platform to use only free and open-source technologies, so that we can maintain cost-effectiveness while ensuring scalability.

#### Acceptance Criteria

1. WHEN implementing LLM functionality THEN the system SHALL use Hugging Face Inference API instead of paid APIs like OpenAI
2. WHEN selecting models THEN the system SHALL use open-source models including Mistral-7B, Gemma, and bge-small-en-v1.5 for embeddings
3. WHEN implementing vector storage THEN the system SHALL use ChromaDB instead of paid vector databases
4. WHEN deploying backend services THEN the system SHALL run all logic inside containers that are Kubernetes-compatible
5. WHEN scaling the platform THEN the system SHALL support deployment on GKE or Minikube for production orchestration