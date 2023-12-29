from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import numpy as np
from inference import infer
from typing import List, Dict
import json

app = FastAPI()

# Store active connections
active_connections: Dict[str, WebSocket] = {}


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    active_connections[user_id] = websocket
    print("=========> User ID", user_id)
    try:
        while True:
            # Receive voice data from one user and broadcast to the other user
            data = await websocket.receive_text()
            data = json.loads(data)

            print(data)
            bytes = str.encode(data["voice"])
            voice = np.frombuffer(bytes, np.float32).flatten()
            other_user_id = data["friendId"]
            out = infer(voice)
            print(out)
            if other_user_id in active_connections:
                await active_connections[other_user_id].send_text(data["voice"])
    except Exception as e:
        print(f"Connection error: {e}")
        del active_connections[user_id]
