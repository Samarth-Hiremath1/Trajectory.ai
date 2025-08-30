# ChromaDB and Embedding Service Documentation

## Overview

This implementation provides ChromaDB integration with BGE (BAAI General Embedding) model for semantic search and retrieval-augmented generation (RAG) capabilities in the Trajectory.AI platform.

## Features

- **BGE-small-en-v1.5 Embeddings**: High-quality sentence embeddings from Hugging Face
- **ChromaDB Vector Storage**: Persistent vector database for semantic search
- **Resume Content Indexing**: Automatic chunking and embedding of resume content
- **Semantic Search**: Query resume content using natural language
- **RAG-Ready**: Prepared for integration with AI chat services

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Resume PDF    │───▶│  Text Chunking   │───▶│   BGE Model     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Search Query   │───▶│  Query Embedding │───▶│   ChromaDB      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                                               ┌─────────────────┐
                                               │ Semantic Results│
                                               └─────────────────┘
```

## Components

### 1. EmbeddingService (`services/embedding_service.py`)

Main service class that handles:
- BGE model initialization and embedding generation
- ChromaDB client management (HTTP + persistent fallback)
- Collection management for different data types
- Semantic search and retrieval operations

**Key Methods:**
- `generate_embeddings(texts)`: Generate embeddings for text chunks
- `store_resume_embeddings(user_id, chunks)`: Store resume embeddings
- `search_resume_embeddings(user_id, query)`: Search user's resume content
- `delete_user_embeddings(user_id)`: Clean up user data

### 2. ResumeProcessingService (`services/resume_service.py`)

Enhanced resume service with embedding integration:
- PDF parsing and text chunking
- Automatic embedding generation and storage
- Integrated search functionality

**Key Methods:**
- `process_resume_with_embeddings()`: Complete processing pipeline
- `search_resume_content()`: Search user's resume using semantic similarity
- `delete_user_resume_data()`: Clean up all user resume data

### 3. API Endpoints (`api/resume.py`)

REST API endpoints for resume and embedding operations:
- `POST /api/resume/upload`: Upload and process resume with embeddings
- `POST /api/resume/search`: Search resume content semantically
- `GET /api/resume/health`: Check service health and status

## Configuration

### ChromaDB Setup

The service supports two deployment modes:

1. **Docker Mode** (Production):
   ```yaml
   # docker-compose.yml
   chromadb:
     image: chromadb/chroma:latest
     ports:
       - "8001:8000"
     volumes:
       - chroma_data:/chroma/chroma
   ```

2. **Persistent Mode** (Development):
   - Automatically falls back to local persistent storage
   - Data stored in `./chroma_db` directory

### Environment Variables

```bash
# Optional: ChromaDB connection settings
CHROMADB_HOST=localhost
CHROMADB_PORT=8001

# BGE model will be downloaded automatically from Hugging Face
```

## Usage Examples

### 1. Upload Resume with Embedding Generation

```python
# Via API
files = {"file": ("resume.pdf", pdf_content, "application/pdf")}
response = requests.post("http://localhost:8000/api/resume/upload", files=files)
```

### 2. Search Resume Content

```python
# Via API
response = requests.post(
    "http://localhost:8000/api/resume/search",
    params={"query": "machine learning experience", "n_results": 5}
)
```

### 3. Direct Service Usage

```python
from services.embedding_service import EmbeddingService
from services.resume_service import ResumeProcessingService

# Initialize services
embedding_service = EmbeddingService()
resume_service = ResumeProcessingService()

# Process resume
result = await resume_service.process_resume_with_embeddings(
    user_id="user123",
    file_content=pdf_bytes,
    filename="resume.pdf"
)

# Search content
results = resume_service.search_resume_content(
    user_id="user123",
    query="Python programming skills",
    n_results=3
)
```

## Data Models

### ChromaDB Collections

1. **resume_embeddings**: User resume content chunks
   - Document: Resume text chunk
   - Metadata: `user_id`, `chunk_index`, `char_count`, `created_at`
   - Embedding: 384-dimensional BGE vector

2. **knowledge_base**: General knowledge and resources (future)
   - For storing scraped learning resources
   - Career guidance content

### Resume Chunk Structure

```python
{
    "chunk_id": "uuid",
    "content": "text content",
    "chunk_index": 0,
    "metadata": {
        "user_id": "user123",
        "char_count": 500,
        "created_at": "2024-01-01T00:00:00",
        "section": "experience"  # optional
    }
}
```

## Testing

### Run Embedding Service Tests

```bash
cd backend
source venv/bin/activate
python test_embedding_service.py
```

### Run Integration Tests

```bash
cd backend
source venv/bin/activate
python test_integration.py
```

### Health Check

```bash
curl http://localhost:8000/api/resume/health
```

## Performance Considerations

### Embedding Generation
- BGE-small-en-v1.5: ~133MB model, 384-dimensional embeddings
- Processing time: ~1 second per text chunk
- Memory usage: ~500MB for model + embeddings

### ChromaDB Storage
- Persistent storage in `./chroma_db` directory
- Automatic indexing with HNSW algorithm
- Efficient similarity search with cosine distance

### Optimization Tips
1. **Batch Processing**: Process multiple chunks together
2. **Caching**: Reuse embeddings for similar content
3. **Chunking Strategy**: Optimize chunk size (current: 500 chars)
4. **Collection Management**: Separate collections by data type

## Troubleshooting

### Common Issues

1. **ChromaDB Connection Failed**
   - Service automatically falls back to persistent mode
   - Check Docker container status: `docker ps`

2. **Model Download Issues**
   - BGE model downloads automatically on first use
   - Requires internet connection and ~133MB download

3. **Memory Issues**
   - BGE model requires ~500MB RAM
   - Consider using smaller models for resource-constrained environments

4. **Telemetry Warnings**
   - ChromaDB telemetry errors are harmless
   - Core functionality works despite warnings

### Debug Commands

```bash
# Check ChromaDB status
curl http://localhost:8001/api/v1/heartbeat

# Check embedding service health
curl http://localhost:8000/api/resume/health

# View ChromaDB collections
python -c "
import chromadb
client = chromadb.PersistentClient('./chroma_db')
print(client.list_collections())
"
```

## Future Enhancements

1. **Multiple Models**: Support for different embedding models
2. **Batch Processing**: Optimize for multiple resume processing
3. **Advanced Chunking**: Semantic-aware text splitting
4. **Caching Layer**: Redis integration for embedding cache
5. **Monitoring**: Detailed metrics and performance tracking

## Requirements Satisfied

This implementation satisfies the following requirements from the spec:

- **2.2**: Resume content chunking and embedding using bge-small-en-v1.5
- **2.3**: ChromaDB storage for embeddings and semantic search
- **Task 5**: Complete ChromaDB and embedding generation setup

The system is now ready for integration with the AI chat service for RAG-enabled conversations.