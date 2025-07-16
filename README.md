# Trajectory.AI

A career navigation platform that provides personalized, AI-generated feedback and roadmaps to help users reach their target career goals.

## Project Structure

```
├── frontend/          # Next.js React application
│   ├── src/
│   │   ├── app/       # Next.js app router pages
│   │   ├── components/
│   │   │   ├── auth/      # Authentication components
│   │   │   ├── chat/      # AI chat interface
│   │   │   ├── onboarding/# User onboarding flow
│   │   │   └── roadmap/   # Career roadmap display
│   │   └── lib/       # Utility functions and configurations
│   └── package.json
├── backend/           # FastAPI Python backend
│   ├── api/           # API route handlers
│   ├── models/        # Data models
│   ├── services/      # Business logic services
│   ├── main.py        # FastAPI application entry point
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml # Container orchestration
└── .kiro/specs/       # Feature specifications and tasks
```

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
- **Deployment**: Vercel (frontend), Kubernetes (backend)

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

### Docker Setup (Optional)
```bash
docker compose up --build
```
This will start both the backend API and ChromaDB services.

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
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_key
HUGGINGFACE_API_KEY=your_huggingface_api_key
```

## Contributing

1. Create a feature branch from `develop`
2. Make your changes
3. Test thoroughly
4. Submit a pull request to `develop`

## License

This project is licensed under the MIT License.