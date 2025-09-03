# Trajectory.AI

A career navigation platform that provides personalized, AI-generated feedback and roadmaps to help users reach their target career goals.

## Project Structure

```
├── 📚 docs/                    # Comprehensive documentation
│   ├── setup/                 # Setup & configuration guides
│   ├── architecture/          # System architecture docs
│   ├── testing/               # Testing documentation
│   └── guides/                # Best practices & guides
├── 🔧 backend/                # FastAPI Python backend
│   ├── api/                   # API route handlers
│   ├── models/                # Data models & schemas
│   ├── services/              # Business logic services
│   ├── migrations/            # Database migrations
│   ├── tests/                 # Comprehensive test suite
│   │   ├── unit/              # Unit tests with mocks
│   │   ├── integration/       # Integration tests
│   │   └── e2e/               # End-to-end tests
│   └── config/                # Configuration files
├── 🎨 frontend/               # Next.js React application
│   ├── src/
│   │   ├── app/               # Next.js app router pages
│   │   ├── components/        # React components
│   │   │   ├── auth/          # Authentication components
│   │   │   ├── chat/          # AI chat interface
│   │   │   ├── onboarding/    # User onboarding flow
│   │   │   └── roadmap/       # Career roadmap display
│   │   ├── lib/               # Utility functions
│   │   └── hooks/             # Custom React hooks
│   └── package.json
├── 🧪 Testing & Setup Scripts
│   ├── run_storage_tests.py   # Comprehensive test runner
│   ├── setup_supabase.py      # Supabase setup automation
│   └── check_test_status.py   # Quick status checker
└── 🐳 Infrastructure
    ├── docker-compose.yml     # Container orchestration
    └── .kiro/specs/           # Feature specifications
```

For detailed structure information, see [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md).

## Technology Stack

### Frontend
- **Framework**: Next.js 15 with React 18
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Authentication**: Supabase Auth

### Backend
- **Framework**: FastAPI (Python)
- **AI/ML**: Hugging Face Inference API, LangChain
- **Vector Database**: ChromaDB
- **Database**: Supabase (PostgreSQL)
- **Document Processing**: pdfplumber, unstructured

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Orchestration**: Kubernetes with Helm charts
- **Deployment**: Multi-environment (dev/staging/prod)
- **Monitoring**: Health checks, metrics, and logging

## To Run:

### Option 1: Traditional for development
Backend
```
cd backend
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt
python main.py
```

Frontend
Frontend


cd frontend
npm install
npm run dev

### Option 2: Docker Compose
Development Environment (with hot reloading)
```
# Start all services with hot reloading
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

```
# Or start specific services
docker compose -f docker-compose.yml -f docker-compose.dev.yml up backend chromadb
Production-like Environment
```

```
# Start production-like containers
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build
```

## Development Setup

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- Docker (optional, for containerized development)

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The frontend will be available at http://localhost:3000

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
The backend API will be available at http://localhost:8000

## 🐳 Docker & Kubernetes Deployment

### Quick Start with Docker Compose

For local development:
```bash
# Development environment with hot reloading
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Production-like environment
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build
```

### Container Management

Build container images:
```bash
# Build all services for development
./scripts/build.sh dev all

# Build specific service for production
./scripts/build.sh prod backend
```

Validate configurations:
```bash
# Validate all configurations
./scripts/validate.sh all dev

# Validate only Kubernetes manifests
./scripts/validate.sh k8s prod
```

### Kubernetes Deployment

Deploy to Kubernetes cluster:
```bash
# Deploy to development environment
./scripts/deploy.sh dev deploy

# Deploy to production environment
./scripts/deploy.sh prod deploy

# Check deployment status
./scripts/deploy.sh prod status

# View logs
./scripts/deploy.sh dev logs backend
```

Rollback deployments:
```bash
# Rollback to previous version
./scripts/rollback.sh prod backend previous

# Rollback to specific revision
./scripts/rollback.sh staging frontend 3

# Show rollout history
./scripts/rollback.sh prod all history
```

For detailed deployment instructions, see [docs/deployment/](docs/deployment/).

## 📚 Documentation

### Deployment & Operations
- [Deployment Guide](docs/deployment/README.md) - Complete deployment instructions
- [Troubleshooting Guide](docs/deployment/TROUBLESHOOTING.md) - Common issues and solutions
- [Environment Configuration](docs/deployment/ENVIRONMENT_CONFIGURATION.md) - Environment-specific settings

### Architecture & Development
- [Multi-Agent System](docs/architecture/MULTI_AGENT_SYSTEM.md) - AI agent architecture
- [LangGraph Integration](docs/architecture/LANGGRAPH_INTEGRATION.md) - Workflow orchestration
- [Development Guide](docs/guides/DEVELOPMENT_GUIDE.md) - Development best practices

## Development Workflow

The project uses a feature branch workflow:
- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - Individual feature branches

Available feature branches:
- `feature/auth` - Authentication implementation
- `feature/onboarding` - User onboarding flow
- `feature/ai-chat` - AI chat functionality
- `feature/roadmap` - Career roadmap generation

## API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation.

## Environment Variables

Create `.env` files in both frontend and backend directories:

### Frontend (.env.local)
```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### Backend (.env)
```
# Database Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# AI Service Configuration
GEMINI_API_KEY=your_gemini_api_key
OPENROUTER_API_KEY=your_openrouter_api_key

# Storage Configuration (NEW!)
STORAGE_PROVIDER=supabase

# ChromaDB Configuration
CHROMA_HOST=localhost
CHROMA_PORT=8000
```

## 🚀 Supabase Storage Setup

GoalTrajectory.ai now uses **Supabase Storage** for resume uploads with intelligent quota management!

### Quick Setup

1. **Run the setup script:**
   ```bash
   python setup_supabase.py
   ```

2. **Create the storage bucket:**
   - Go to your Supabase dashboard
   - Navigate to **Storage** section
   - Create a new bucket named `resumes`
   - Set it to **Private** (not public)

3. **Set up security policies:**
   ```bash
   python setup_supabase.py --sql
   ```
   Copy the output and run it in your Supabase SQL Editor.

4. **Test the integration:**
   ```bash
   python test_storage_integration.py
   ```

### 🎯 Features

- **Smart Quota Management**: Automatically handles free tier limits
- **User Notifications**: Clear messages when storage limits are reached
- **Temporary Storage**: Files are processed then deleted when limits reached
- **Secure Access**: Row-level security with user-specific file access
- **Automatic Cleanup**: Old temporary files are automatically removed

### 📊 Storage Modes

- **🟢 Persistent**: Normal operation (< 80% usage)
- **🟡 Warning**: Approaching limits (80-90% usage)  
- **🔴 Temporary**: Limits reached (> 90% usage) - files deleted after processing

When storage limits are reached, users see a friendly message explaining that their resume will be processed but then deleted to save space, with an option to email for storage upgrades.

For detailed setup instructions, see [docs/setup/](docs/setup/).

## Contributing

1. Create a feature branch from `develop`
2. Make your changes
3. Test thoroughly
4. Submit a pull request to `develop`

## License

This project is licensed under the MIT License.