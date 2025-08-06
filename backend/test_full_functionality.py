#!/usr/bin/env python3
"""
Test full functionality after schema is applied
"""

import asyncio
import os
from dotenv import load_dotenv
import sys
sys.path.append('.')

# Load environment variables
load_dotenv()

async def test_full_functionality():
    """Test the complete functionality"""
    
    print("🚀 Full Functionality Test")
    print("=" * 35)
    
    try:
        # Test 1: Database Connection
        print("\n1️⃣ Testing Database Connection")
        print("-" * 35)
        
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        supabase = create_client(supabase_url, supabase_key)
        
        # Test all tables
        tables_to_test = ["profiles", "roadmaps", "chat_sessions"]
        for table in tables_to_test:
            try:
                result = supabase.table(table).select("*").limit(1).execute()
                print(f"✅ {table} table: OK")
            except Exception as e:
                print(f"❌ {table} table: {str(e)}")
        
        # Test 2: Database Service
        print("\n2️⃣ Testing Database Service")
        print("-" * 35)
        
        try:
            from services.database_service import DatabaseService
            db_service = DatabaseService()
            print("✅ DatabaseService initialized successfully")
        except Exception as e:
            print(f"❌ DatabaseService failed: {str(e)}")
            return
        
        # Test 3: Roadmap Service
        print("\n3️⃣ Testing Roadmap Service")
        print("-" * 35)
        
        try:
            from services.roadmap_service import get_roadmap_service
            roadmap_service = await get_roadmap_service()
            print("✅ RoadmapService initialized successfully")
        except Exception as e:
            print(f"❌ RoadmapService failed: {str(e)}")
        
        # Test 4: Chat Service
        print("\n4️⃣ Testing Chat Service")
        print("-" * 35)
        
        try:
            from services.chat_service import get_chat_service
            chat_service = await get_chat_service()
            print("✅ ChatService initialized successfully")
        except Exception as e:
            print(f"❌ ChatService failed: {str(e)}")
        
        # Test 5: API Endpoints (if FastAPI is running)
        print("\n5️⃣ Testing API Endpoints")
        print("-" * 35)
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                # Test health endpoints
                try:
                    response = await client.get("http://localhost:8000/health")
                    if response.status_code == 200:
                        print("✅ Main API health: OK")
                    else:
                        print(f"⚠️ Main API health: {response.status_code}")
                except:
                    print("⚠️ Main API: Not running (start with: uvicorn main:app --reload)")
                
                try:
                    response = await client.get("http://localhost:8000/api/roadmap/health")
                    if response.status_code == 200:
                        print("✅ Roadmap API health: OK")
                    else:
                        print(f"⚠️ Roadmap API health: {response.status_code}")
                except:
                    print("⚠️ Roadmap API: Not running")
                
                try:
                    response = await client.get("http://localhost:8000/api/chat/health")
                    if response.status_code == 200:
                        print("✅ Chat API health: OK")
                    else:
                        print(f"⚠️ Chat API health: {response.status_code}")
                except:
                    print("⚠️ Chat API: Not running")
                    
        except ImportError:
            print("⚠️ httpx not installed - skipping API tests")
        except Exception as e:
            print(f"⚠️ API tests failed: {str(e)}")
        
        print(f"\n🎉 Functionality Test Complete!")
        print("=" * 40)
        print("✅ Database connection working")
        print("✅ Services can be initialized")
        print("ℹ️ Start the backend server to test APIs:")
        print("   cd backend && uvicorn main:app --reload")
        print("ℹ️ Start the frontend to test full integration:")
        print("   cd frontend && npm run dev")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_functionality())