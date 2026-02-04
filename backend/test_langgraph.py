import asyncio
from typing import List, Dict
import requests
import json

# Setup
BASE_URL = "http://localhost:8001/api/v1/orchestrator"
WS_URL = "ws://localhost:8001/api/v1/orchestrator/ws"

async def test_langgraph_agent(agent_id, input_text):
    import websockets
    uri = f"{WS_URL}/{agent_id}"
    
    print(f"Connecting to {uri}...")
    async with websockets.connect(uri) as websocket:
        # Wait for session start
        resp = await websocket.recv()
        print(f"Received: {resp}")
        
        # Send input
        payload = {"text": input_text}
        print(f"Sending: {payload}")
        await websocket.send(json.dumps(payload))
        
        # Listen for response
        full_response = ""
        while True:
            try:
                msg = await websocket.recv()
                data = json.loads(msg)
                
                if data.get("type") == "text_chunk":
                    print(f"Chunk: {data['text']}", end="", flush=True)
                    full_response += data['text']
                elif data.get("type") == "end_response":
                    print("\nResponse Complete")
                    break
                elif data.get("type") == "audio":
                    print("[Audio Chunk]", end="", flush=True)
            except Exception as e:
                print(f"Error: {e}")
                break
        
        return full_response

if __name__ == "__main__":
    # 1. Fetch the multi-agent template agent ID (or install it if needed)
    # Since we can't easily query by template in this script without auth, 
    # let's assume we use the one created by the browser subagent if available.
    # Alternatively, we can just fetch the first agent with 'multi-agent' in description.
    
    # We need to query DB directly or use API with a token.
    # For now, let's just inspect the DB
    from app.core import database
    from app.models.agent import Agent
    from sqlalchemy.orm import Session
    
    db = list(database.get_db())[0]
    agent = db.query(Agent).filter(Agent.description.ilike("%multi-agent%")).first()
    
    if agent:
        print(f"Found Multi-Agent: {agent.name} ({agent.id})")
        
        # Test 1: Sales Intent
        print("\n--- Testing Sales Intent ---")
        asyncio.run(test_langgraph_agent(agent.id, "I am interested in buying a premium subscription."))
        
        # Test 2: Support Intent
        print("\n--- Testing Support Intent ---")
        asyncio.run(test_langgraph_agent(agent.id, "I forgot my password."))
        
        # Test 3: Compliance Intent
        print("\n--- Testing Compliance Intent ---")
        asyncio.run(test_langgraph_agent(agent.id, "I want to file a formal complaint about data privacy."))
        
    else:
        print("No Multi-Agent found. Please install the template first.")
