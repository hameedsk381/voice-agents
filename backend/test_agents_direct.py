import asyncio
import websockets
import json
import uuid

BACKEND_URL = "ws://localhost:8001/api/v1/orchestrator/ws/chat"

async def test_agent(agent_id, agent_name, message):
    uri = f"{BACKEND_URL}?agent_id={agent_id}"
    print(f"\n--- Testing {agent_name} ({agent_id}) ---")
    print(f"Message: {message}")
    
    try:
        async with websockets.connect(uri) as websocket:
            # Wait for session start
            start_msg = await websocket.recv()
            print(f"Server: {start_msg}")
            
            # Send text message
            payload = {"type": "text", "text": message}
            await websocket.send(json.dumps(payload))
            print("Sent message...")
            
            # Listen for responses
            full_text = ""
            while True:
                resp = await websocket.recv()
                data = json.loads(resp)
                
                if data["type"] == "text_chunk":
                    full_text += data["text"]
                    print(data["text"], end="", flush=True)
                elif data["type"] == "end_response":
                    print("\n[Response Finished]")
                    break
                elif data["type"] == "audio":
                    # Ignore audio bytes for this test
                    pass
                elif data["type"] == "error":
                    print(f"\nError: {data['message']}")
                    break
                    
            return full_text
    except Exception as e:
        print(f"\nFailed to connect/process: {e}")
        return None

async def main():
    agents_to_test = [
        ("47a2c409-2aaa-4853-9a6e-a5ab73dc171a", "Support Agent 1", "Hello, I have a question about my bank account."),
        ("94b69134-1d00-4ddf-b776-f535432df75b", "Super-Agent Hub", "I want to buy a subscription and I also forgot my password.")
    ]
    
    for agent_id, name, msg in agents_to_test:
        await test_agent(agent_id, name, msg)

if __name__ == "__main__":
    asyncio.run(main())
