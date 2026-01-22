#!/usr/bin/env python3
"""Test script to verify toggle-permission endpoint"""
import asyncio
import httpx
import json

async def test_toggle():
    """Test the toggle-permission endpoint"""
    api_url = "http://localhost:8002"
    api_key = "your-api-key-here"  # Replace with actual key
    
    # Test data
    group_id = -1003447608920
    user_id = 501166051
    
    # Test 1: Send with json parameter (what httpx.post(json=...) does)
    print("\n=== Test 1: Using json parameter ===")
    payload = {
        "user_id": user_id,
        "metadata": {
            "permission_type": "send_messages"
        }
    }
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(
            f"{api_url}/api/v2/groups/{group_id}/enforcement/toggle-permission",
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        print(f"Headers: {response.request.headers}")
        print(f"Request body: {response.request.content}")
    
    # Test 2: Send with explicit content-type
    print("\n=== Test 2: With explicit content-type ===")
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(
            f"{api_url}/api/v2/groups/{group_id}/enforcement/toggle-permission",
            content=json.dumps(payload),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_toggle())
