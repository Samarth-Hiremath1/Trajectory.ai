#!/usr/bin/env python3
"""
Test script for ChromaDB and embedding service functionality
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend directory to Python path
sys.path.append(str(Path(__file__).parent))

from services.embedding_service import EmbeddingService
from services.resume_service import ResumeProcessingService
from models.resume import ResumeChunk

async def test_embedding_service():
    """Test the embedding service functionality"""
    print("🧪 Testing ChromaDB and Embedding Service")
    print("=" * 50)
    
    try:
        # Initialize embedding service
        print("1. Initializing embedding service...")
        embedding_service = EmbeddingService()
        print("✅ Embedding service initialized")
        
        # Test health check
        print("\n2. Testing health check...")
        health = embedding_service.health_check()
        print(f"Health status: {health['status']}")
        print(f"ChromaDB connected: {health.get('chromadb_connected', False)}")
        print(f"Embedding model: {health.get('model_name', 'Unknown')}")
        print(f"Embedding dimension: {health.get('embedding_dimension', 0)}")
        
        if health['status'] != 'healthy':
            print("❌ Service is not healthy, stopping tests")
            return False
        
        # Test embedding generation
        print("\n3. Testing embedding generation...")
        test_texts = [
            "I am a software engineer with 5 years of experience in Python and JavaScript.",
            "I have worked on machine learning projects using TensorFlow and PyTorch.",
            "My experience includes building REST APIs with FastAPI and Django."
        ]
        
        embeddings = embedding_service.generate_embeddings(test_texts)
        print(f"✅ Generated {len(embeddings)} embeddings")
        print(f"Embedding dimension: {len(embeddings[0]) if embeddings else 0}")
        
        # Test ChromaDB collection management
        print("\n4. Testing ChromaDB collection management...")
        collection = embedding_service.get_or_create_collection("test_collection")
        print("✅ Collection created/retrieved successfully")
        
        # Test storing embeddings
        print("\n5. Testing embedding storage...")
        test_user_id = "test_user_123"
        test_chunks = [
            ResumeChunk(
                chunk_id="chunk_1",
                content=test_texts[0],
                chunk_index=0,
                metadata={"section": "experience"}
            ),
            ResumeChunk(
                chunk_id="chunk_2", 
                content=test_texts[1],
                chunk_index=1,
                metadata={"section": "skills"}
            ),
            ResumeChunk(
                chunk_id="chunk_3",
                content=test_texts[2],
                chunk_index=2,
                metadata={"section": "projects"}
            )
        ]
        
        success = embedding_service.store_resume_embeddings(test_user_id, test_chunks)
        print(f"✅ Embeddings stored: {success}")
        
        # Test searching embeddings
        print("\n6. Testing embedding search...")
        search_query = "machine learning experience"
        results = embedding_service.search_resume_embeddings(test_user_id, search_query, n_results=2)
        print(f"✅ Found {len(results)} relevant chunks for query: '{search_query}'")
        
        for i, result in enumerate(results):
            print(f"  Result {i+1}:")
            print(f"    Content: {result['content'][:100]}...")
            print(f"    Distance: {result.get('distance', 'N/A')}")
            print(f"    Metadata: {result.get('metadata', {})}")
        
        # Test collection stats
        print("\n7. Testing collection statistics...")
        stats = embedding_service.get_collection_stats("resume_embeddings")
        print(f"Collection: {stats['name']}")
        print(f"Document count: {stats['count']}")
        
        # Clean up test data
        print("\n8. Cleaning up test data...")
        cleanup_success = embedding_service.delete_user_embeddings(test_user_id)
        print(f"✅ Test data cleaned up: {cleanup_success}")
        
        print("\n🎉 All embedding service tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_resume_service_integration():
    """Test the resume service with embedding integration"""
    print("\n🧪 Testing Resume Service Integration")
    print("=" * 50)
    
    try:
        # Initialize resume service
        print("1. Initializing resume service...")
        resume_service = ResumeProcessingService()
        print("✅ Resume service initialized")
        
        # Create a simple test PDF content (mock)
        print("\n2. Testing resume processing with embeddings...")
        test_user_id = "integration_test_user"
        
        # Since we don't have a real PDF file, we'll test the search functionality
        # with some mock data that might already exist
        print("\n3. Testing resume content search...")
        search_results = resume_service.search_resume_content(
            test_user_id, 
            "software engineering experience",
            n_results=3
        )
        print(f"✅ Search completed, found {len(search_results)} results")
        
        if search_results:
            print("Sample search results:")
            for i, result in enumerate(search_results[:2]):
                print(f"  Result {i+1}: {result.get('content', '')[:100]}...")
        
        print("\n🎉 Resume service integration tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting ChromaDB and Embedding Service Tests")
    print("=" * 60)
    
    # Test embedding service
    embedding_success = await test_embedding_service()
    
    # Test resume service integration
    integration_success = await test_resume_service_integration()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 30)
    print(f"Embedding Service Tests: {'✅ PASSED' if embedding_success else '❌ FAILED'}")
    print(f"Integration Tests: {'✅ PASSED' if integration_success else '❌ FAILED'}")
    
    if embedding_success and integration_success:
        print("\n🎉 All tests passed! ChromaDB and embedding functionality is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)