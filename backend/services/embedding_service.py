import os
import logging
from typing import List, Dict, Optional, Any
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import uuid
from datetime import datetime

from models.resume import ResumeChunk

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating embeddings and managing ChromaDB collections"""
    
    def __init__(self, chromadb_host: str = "localhost", chromadb_port: int = 8001):
        self.chromadb_host = chromadb_host
        self.chromadb_port = chromadb_port
        self.model_name = "BAAI/bge-small-en-v1.5"
        
        # Initialize embedding model
        self._init_embedding_model()
        
        # Initialize ChromaDB client
        self._init_chromadb_client()
        
        # Collection names
        self.resume_collection_name = "resume_embeddings"
        self.knowledge_base_collection_name = "knowledge_base"
    
    def _init_embedding_model(self):
        """Initialize the BGE embedding model from Hugging Face"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.embedding_model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def _init_chromadb_client(self):
        """Initialize ChromaDB client"""
        try:
            # First try HTTP client for Docker deployment
            self.chroma_client = chromadb.HttpClient(
                host=self.chromadb_host,
                port=self.chromadb_port
            )
            
            # Test connection
            self.chroma_client.heartbeat()
            logger.info("ChromaDB HTTP client initialized successfully")
            
        except Exception as e:
            logger.warning(f"Failed to connect to ChromaDB HTTP client: {e}")
            # Fallback to persistent client for local development
            try:
                import os
                chroma_db_path = os.path.join(os.getcwd(), "chroma_db")
                self.chroma_client = chromadb.PersistentClient(path=chroma_db_path)
                logger.info(f"Using persistent ChromaDB client at: {chroma_db_path}")
            except Exception as fallback_error:
                logger.error(f"Failed to initialize fallback ChromaDB client: {fallback_error}")
                raise
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts using BGE model"""
        try:
            if not texts:
                return []
            
            logger.info(f"Generating embeddings for {len(texts)} texts")
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
            
            # Convert to list of lists for ChromaDB compatibility
            embeddings_list = [embedding.tolist() for embedding in embeddings]
            
            logger.info(f"Generated {len(embeddings_list)} embeddings")
            return embeddings_list
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    def get_or_create_collection(self, collection_name: str, metadata: Optional[Dict] = None) -> Any:
        """Get existing collection or create new one"""
        try:
            # Try to get existing collection
            collection = self.chroma_client.get_collection(name=collection_name)
            logger.info(f"Retrieved existing collection: {collection_name}")
            return collection
            
        except Exception:
            # Collection doesn't exist, create it
            try:
                # Ensure metadata is not empty for ChromaDB
                collection_metadata = metadata or {"description": f"Collection for {collection_name}"}
                
                collection = self.chroma_client.create_collection(
                    name=collection_name,
                    metadata=collection_metadata
                )
                logger.info(f"Created new collection: {collection_name}")
                return collection
                
            except Exception as e:
                logger.error(f"Failed to create collection {collection_name}: {e}")
                raise
    
    def store_resume_embeddings(self, user_id: str, chunks: List[ResumeChunk]) -> bool:
        """Store resume chunk embeddings in ChromaDB"""
        try:
            if not chunks:
                logger.warning("No chunks provided for embedding storage")
                return False
            
            # Get or create resume collection
            collection = self.get_or_create_collection(
                self.resume_collection_name,
                metadata={"description": "Resume content embeddings for RAG"}
            )
            
            # Prepare data for ChromaDB
            texts = [chunk.content for chunk in chunks]
            chunk_ids = [f"{user_id}_{chunk.chunk_id}" for chunk in chunks]
            
            # Generate embeddings
            embeddings = self.generate_embeddings(texts)
            
            # Prepare metadata for each chunk
            metadatas = []
            for chunk in chunks:
                metadata = {
                    "user_id": user_id,
                    "chunk_index": chunk.chunk_index,
                    "char_count": len(chunk.content),
                    "created_at": datetime.utcnow().isoformat(),
                    **chunk.metadata
                }
                metadatas.append(metadata)
            
            # Store in ChromaDB
            collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=chunk_ids
            )
            
            logger.info(f"Stored {len(chunks)} resume embeddings for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store resume embeddings: {e}")
            return False
    
    def search_resume_embeddings(self, user_id: str, query: str, n_results: int = 5) -> List[Dict]:
        """Search for relevant resume chunks using semantic similarity"""
        try:
            # Get resume collection
            collection = self.chroma_client.get_collection(name=self.resume_collection_name)
            
            # Generate query embedding
            query_embedding = self.generate_embeddings([query])[0]
            
            # Search with user filter
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where={"user_id": user_id}
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    result = {
                        "content": doc,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "distance": results['distances'][0][i] if results['distances'] else None,
                        "id": results['ids'][0][i] if results['ids'] else None
                    }
                    formatted_results.append(result)
            
            logger.info(f"Found {len(formatted_results)} relevant resume chunks for user {user_id}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search resume embeddings: {e}")
            return []
    
    def delete_user_embeddings(self, user_id: str) -> bool:
        """Delete all embeddings for a specific user"""
        try:
            # Get resume collection
            collection = self.chroma_client.get_collection(name=self.resume_collection_name)
            
            # Get all documents for the user
            results = collection.get(where={"user_id": user_id})
            
            if results['ids']:
                # Delete all user's embeddings
                collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} embeddings for user {user_id}")
                return True
            else:
                logger.info(f"No embeddings found for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete user embeddings: {e}")
            return False
    
    def get_collection_stats(self, collection_name: str) -> Dict:
        """Get statistics about a ChromaDB collection"""
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
            count = collection.count()
            
            return {
                "name": collection_name,
                "count": count,
                "metadata": collection.metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"name": collection_name, "count": 0, "error": str(e)}
    
    def store_profile_context(self, user_id: str, profile_text: str) -> bool:
        """Store user profile context as embeddings for RAG"""
        try:
            if not profile_text.strip():
                logger.warning("Empty profile text provided")
                return False
            
            # Get or create profile context collection
            collection = self.get_or_create_collection(
                "profile_context",
                metadata={"description": "User profile context embeddings for RAG"}
            )
            
            # Delete existing profile context for this user first
            try:
                existing_results = collection.get(where={"user_id": user_id})
                if existing_results['ids']:
                    collection.delete(ids=existing_results['ids'])
                    logger.info(f"Deleted existing profile context for user {user_id}")
            except Exception as e:
                logger.warning(f"Could not delete existing profile context: {e}")
            
            # Generate embedding for profile text
            embeddings = self.generate_embeddings([profile_text])
            
            # Store in ChromaDB
            profile_id = f"{user_id}_profile_context"
            metadata = {
                "user_id": user_id,
                "content_type": "profile_context",
                "created_at": datetime.utcnow().isoformat(),
                "char_count": len(profile_text)
            }
            
            collection.add(
                embeddings=embeddings,
                documents=[profile_text],
                metadatas=[metadata],
                ids=[profile_id]
            )
            
            logger.info(f"Stored profile context for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store profile context: {e}")
            return False
    
    def get_user_embedding_stats(self, user_id: str, collection_name: str) -> Dict:
        """Get embedding statistics for a specific user and collection"""
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
            
            # Get user's embeddings
            results = collection.get(where={"user_id": user_id})
            
            stats = {
                "count": len(results['ids']) if results['ids'] else 0,
                "collection": collection_name
            }
            
            # Get last updated timestamp if available
            if results['metadatas']:
                timestamps = []
                for metadata in results['metadatas']:
                    if 'created_at' in metadata:
                        timestamps.append(metadata['created_at'])
                
                if timestamps:
                    stats["last_updated"] = max(timestamps)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get user embedding stats: {e}")
            return {"count": 0, "collection": collection_name, "error": str(e)}
    
    def search_user_context(self, user_id: str, query: str, n_results: int = 5) -> List[Dict]:
        """Search across all user context (resume + profile) for relevant information"""
        try:
            all_results = []
            
            # Search resume embeddings
            resume_results = self.search_resume_embeddings(user_id, query, n_results)
            for result in resume_results:
                result["source"] = "resume"
                all_results.append(result)
            
            # Search profile context
            try:
                collection = self.chroma_client.get_collection(name="profile_context")
                query_embedding = self.generate_embeddings([query])[0]
                
                profile_results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    where={"user_id": user_id}
                )
                
                if profile_results['documents'] and profile_results['documents'][0]:
                    for i, doc in enumerate(profile_results['documents'][0]):
                        result = {
                            "content": doc,
                            "metadata": profile_results['metadatas'][0][i] if profile_results['metadatas'] else {},
                            "distance": profile_results['distances'][0][i] if profile_results['distances'] else None,
                            "id": profile_results['ids'][0][i] if profile_results['ids'] else None,
                            "source": "profile"
                        }
                        all_results.append(result)
                        
            except Exception as e:
                logger.warning(f"Could not search profile context: {e}")
            
            # Sort by relevance (distance)
            all_results.sort(key=lambda x: x.get('distance', float('inf')))
            
            # Return top n_results
            return all_results[:n_results]
            
        except Exception as e:
            logger.error(f"Failed to search user context: {e}")
            return []
    
    def health_check(self) -> Dict:
        """Check the health of the embedding service"""
        try:
            # Test ChromaDB connection
            self.chroma_client.heartbeat()
            
            # Test embedding model
            test_embedding = self.generate_embeddings(["test"])
            
            return {
                "status": "healthy",
                "chromadb_connected": True,
                "embedding_model_loaded": True,
                "model_name": self.model_name,
                "embedding_dimension": len(test_embedding[0]) if test_embedding else 0
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "chromadb_connected": False,
                "embedding_model_loaded": False
            }

# Singleton instance
_embedding_service_instance = None

def get_embedding_service() -> EmbeddingService:
    """Get or create singleton embedding service instance"""
    global _embedding_service_instance
    
    if _embedding_service_instance is None:
        _embedding_service_instance = EmbeddingService()
    
    return _embedding_service_instance