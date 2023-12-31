from io import BytesIO
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import numpy as np
from inference import infer, load_opus_audio, writeFloat32toFile
from typing import List, Dict
import json
import torchaudio
import torch
import uvicorn



app = FastAPI()

# Store active connections
active_connections: Dict[str, WebSocket] = {}


html = """
<!DOCTYPE html>
<html>

<head>
    <title>Voice Chat</title>
</head>

<body>
    <h1>Voice Chat</h1>
    <textarea id="chatlog" cols="50" rows="10" readonly></textarea><br>
    <button id="startVoiceChat">Start Voice Chat</button>
    <button id="stopVoiceChat">Stop Voice Chat</button>

    <script type="module" src="./script.mjs"></script>
</body>

</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)

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
        
            writeFloat32toFile(data, 'input')

            print('Recieved data in bytes')
            audio_np = np.frombuffer(data, dtype=np.float32)
            # audio_np = audio_np.astype(np.float32) / 0x7FFF 
            out = infer(audio_np)
            print('about to dispatch the data')
            if friend_id in active_connections:
                await active_connections[friend_id].send_bytes(out)
    except Exception as e:
        print(e)
        del active_connections[user_id]

app.mount("/", StaticFiles(directory="public"), name="static")


if __name__ == '__main__':
    uvicorn.run(app, port=8000, host='0.0.0.0')