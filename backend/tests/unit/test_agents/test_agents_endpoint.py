#!/usr/bin/env python3
"""
Test script for agents endpoint
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_agents_endpoint():
    """Test the agents status endpoint"""
    print("Testing agents endpoint...")
    
    try:
        # Test the startup event
        print("\n1. Testing startup event...")
        from main import startup_event
        await startup_event()
        print("✓ Startup event completed")
        
        # Test the agents status endpoint
        print("\n2. Testing agents status endpoint...")
        from api.agents import get_agent_status
        result = await get_agent_status()
        
        print(f"✓ Status endpoint returned successfully")
        print(f"  - Agents count: {len(result['agents'])}")
        print(f"  - Service initialized: {result['service_status']['initialized']}")
        print(f"  - Service running: {result['service_status']['running']}")
        
        if result['agents']:
            print("  - Registered agents:")
            for agent in result['agents']:
                print(f"    * {agent['type']}: {agent['id']} ({agent['status']})")
        
        # Test the health endpoint
        print("\n3. Testing health endpoint...")
        from api.agents import agents_health_check
        health = await agents_health_check()
        print(f"✓ Health check: {health['status']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_agents_endpoint())
    sys.exit(0 if success else 1)