from io import BytesIO
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import numpy as np
from inference import infer
from typing import List, Dict
import json
import torchaudio
import torch

app = FastAPI()

# Store active connections
active_connections: Dict[str, WebSocket] = {}


@app.websocket("/ws/{user_id}/{friend_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, friend_id: str):
    await websocket.accept()
    active_connections[user_id] = websocket
    print("=========> User ID", user_id)
    chunk_size = 1000
    try:
        while True:
            # Receive voice data from one user and broadcast to the other user
            data = await websocket.receive_bytes()
            f = BytesIO(data)
            s = torchaudio.io.StreamReader(f)
            s.add_basic_audio_stream(chunk_size)
            array = torch.concat([chunk[0] for chunk in s.stream()])
            array = array.numpy()

            print(array)

            out = infer(array)

            print(out)
            if friend_id in active_connections:
                await active_connections[friend_id].send_text(data["voice"])
    except Exception as e:
        print(e)
        del active_connections[user_id]
