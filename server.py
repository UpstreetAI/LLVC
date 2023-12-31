from io import BytesIO
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import numpy as np
from inference import infer, load_opus_audio, writeFloat32toFile, convert_webm_to_fl32
from typing import List, Dict
import json
import torchaudio
import torch
import uvicorn
import pickle as pkl
import wave
import uuid

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

            # with open(f'/src/debug/pkl_{str(uuid.uuid4())}.pkl', 'wb') as file:
            #     pkl.dump(data, file) 
            
            data = convert_webm_to_fl32(data)

            # print('output_audio',output_audio)

            #writeFloat32toFile(output_audio, '/src/debug/input.wav')
            # print('Recieved data in bytes')

            # print(f'---log---: out type: {type(data)}')

            data = np.frombuffer(data, np.float32)
            # # data = data.astype(np.float32) / 0x7FFF 

            print('Input type is', type(data))

            print('About to infer data')

            out = infer(data)
            print('about to dispatch the data')


            if friend_id in active_connections:
                await active_connections[friend_id].send_bytes(out)
    except Exception as e:
        print(e)
        del active_connections[user_id]

app.mount("/", StaticFiles(directory="public"), name="static")


if __name__ == '__main__':
    uvicorn.run(app, port=8000, host='0.0.0.0')