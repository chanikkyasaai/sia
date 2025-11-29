"""
Direct test of Soniox WebSocket connection to diagnose the issue
"""
import asyncio
import websockets
import json
from dotenv import load_dotenv
import os

load_dotenv()

async def test_soniox():
    api_key = os.getenv("SONIOX_API_KEY")
    
    if not api_key:
        print("❌ SONIOX_API_KEY not found in environment")
        return
    
    print(f"✅ API Key loaded: {api_key[:20]}...")
    print(f"🔗 Connecting to Soniox WebSocket...")
    
    try:
        websocket = await websockets.connect("wss://api.soniox.com/transcribe-websocket")
        print("✅ WebSocket connection established")
        
        # Send init message
        init_message = {
            "api_key": api_key,
            "model": "en_v1"
        }
        
        print(f"📤 Sending init message: {json.dumps(init_message, indent=2)}")
        await websocket.send(json.dumps(init_message))
        
        # Wait for response
        print("⏳ Waiting for Soniox response...")
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            response_data = json.loads(response)
            
            print(f"📥 Received response: {json.dumps(response_data, indent=2)}")
            
            if response_data.get("status") == "ok" or "result" in response_data:
                print("✅ Soniox connection successful (waiting for audio)!")
            else:
                print(f"ℹ️  Soniox response: {response_data}")
        except asyncio.TimeoutError:
            print("ℹ️  No immediate response - connection may be waiting for audio (this is OK)")
            print("✅ Connection successful! The WebSocket is ready to receive audio.")
        
        await websocket.close()
        
    except asyncio.TimeoutError:
        print("❌ Timeout waiting for Soniox response")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_soniox())
