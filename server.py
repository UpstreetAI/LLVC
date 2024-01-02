from io import BytesIO
from fastapi import FastAPI, WebSocket,  File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import numpy as np
from inference import all_models, baseInference, infer, load_opus_audio, writeFloat32toFile, convert_webm_to_fl32
from typing import List, Dict
import json
import torchaudio
import torch
import uvicorn
import pickle as pkl
import wave
import uuid
import time

app = FastAPI()

# Store active connections
active_connections: Dict[str, WebSocket] = {}

@app.get("/")
async def get():
    html = """
    <!DOCTYPE html>
    <html>

    <head>
        <title>Voice Chat</title>
    </head>

    <body>
        <h1>Voice Chat</h1>
        <select id="modelSelect">
        <option>NA</option>
        <option>
        """ + "</option><option>".join(word.replace('.pth','') for word in all_models()) +"""
        </option>
        </select>
        <button id="startVoiceChat">Start Voice Chat</button>
        <button id="stopVoiceChat">Stop Voice Chat</button>

        <br/>        <br/>

        <div> Upload Model </div>
        <form id="uploadForm">
        <label for="model_name">Model Name</label>
        <input id="fileName" type="text" name="model_name">

        <label for="file">Model(.pth) file</label>
        <input id="fileInput" type="file" name="file">

        <button type="submit">Upload Model</button>

        </form>

        <script type="module" src="./script.mjs"></script>
    </body>

    </html>
    """
    return HTMLResponse(html)

@app.post("/add-model/{model_name}")
def upload(model_name:str, file: UploadFile = File(...)):
    try:
        contents = file.file.read()
        with open(f'/src/models/{model_name}__{str(uuid.uuid4())}.pth', 'wb') as f:
            f.write(contents)
    except Exception:
        return {"message": "There was an error uploading the file"}
    finally:
        file.file.close()

    return {"message": f"Successfully uploaded {file.filename}"}

@app.websocket("/ws/{user_id}/{friend_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, friend_id: str):
    await websocket.accept()
    active_connections[user_id] = websocket
    print("=========> User ID", user_id)
    chunk_size = 1000
    try:
        while True:
            a = time.time()
            # Receive voice data from one user and broadcast to the other user
            data = await websocket.receive_bytes()

            # with open(f'/src/debug/pkl_input.pkl', 'wb') as file:
            #     pkl.dump(data, file) 
            
            out = baseInference(data)

            print("========== IFER TIME", b - a)
            if friend_id in active_connections:
                await active_connections[friend_id].send_bytes(out)
    except Exception as e:
        print(e)
        del active_connections[user_id]

@app.websocket("/ws/{user_id}/{friend_id}/{modelId}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, friend_id: str, modelId:str):
    await websocket.accept()
    active_connections[user_id] = websocket
    print("=========> User ID", user_id)
    chunk_size = 1000
    try:
        while True:
            a = time.time()
            # Receive voice data from one user and broadcast to the other user
            data = await websocket.receive_bytes()

            out = baseInference(data, modelId)
            
            if friend_id in active_connections:
                await active_connections[friend_id].send_bytes(out)
    except Exception as e:
        print('Exception occured' , e)
        del active_connections[user_id]


app.mount("/", StaticFiles(directory="public"), name="static")


if __name__ == '__main__':
    uvicorn.run(app, port=8000, host='0.0.0.0')