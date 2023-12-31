from minimal_rvc.model import VoiceConvertModel
import sys
import logging
from pydub import AudioSegment
from tqdm import tqdm
from typing import Optional
from pathlib import Path
import numpy as np
import soundfile as sf
import librosa
import torch
import os
import shutil
import argparse
import concurrent.futures
import multiprocessing
from opuslib import Decoder, Encoder
import time 
from scipy.io import wavfile
import ffmpeg
import io
import struct
import uuid
import os

multiprocessing.set_start_method("spawn", force=True)


f0_method = "rmvpe"
f0_up_key = 0
model_path = "model.pth"  # placed `model.pth` download from https://www.weights.gg/models/clo5vughf00anwswmzw3f4678
model_name = "matpat"  # Name to be added to output filenames

device = "cuda" if torch.cuda.is_available() else "cpu"
model = VoiceConvertModel(model_name, torch.load(model_path, map_location=device))

print('Device is ', device)


def load_opus_audio(packet):
   return Decoder.decode(packet, 16000)


# def load_audio(buffer, sr):
#     try:
#         input_stream = io.BytesIO(buffer.tobytes())
#         ffmpeg_command = (
#             ffmpeg.input('pipe:', threads=5)
#             .output('pipe:', format="f32le", acodec="pcm_f32le", ac=1, ar=sr)
#             .run_async(pipe_stdin=True, pipe_stdout=True)
#         )

#         print(input_stream)

#         out, _ = ffmpeg_command.communicate(input=input_stream.read())
#         print(f'---log---: out type: {type(out)}')
#     except Exception as e:
#         raise RuntimeError(f"Failed to load audio: {e}")

#     return np.frombuffer(out, np.float32).flatten()

def load_audio(file: str, sr):
    try:
        # https://github.com/openai/whisper/blob/main/whisper/audio.py#L26
        # This launches a subprocess to decode audio while down-mixing and resampling as necessary.
        # Requires the ffmpeg CLI and `ffmpeg-python` package to be installed.
        file = (
            file.strip(" ").strip('"').strip("\n").strip('"').strip(" ")
        )  # Prevent small white copy path head and tail with spaces and " and return
        out, _ = (
            ffmpeg.input(file, threads=0)
            .output("-", format="f32le", acodec="pcm_f32le", ac=1, ar=sr)
            .run(cmd=["ffmpeg", "-nostdin"], capture_stdout=True, capture_stderr=True)
        )
        print(f'---log---: out type: {type(out)}')
    except Exception as e:
        raise RuntimeError(f"Failed to load audio: {e}")

    #os.remove(file)

    return np.frombuffer(out, np.float32).flatten()

def convert_webm_to_fl32(webm_audio_buffer):
    # Input the WebM audio buffer as bytes
    input_data = io.BytesIO(webm_audio_buffer)

    # Input format as WebM and output format as FL32
    process = (
        ffmpeg
        .input('pipe:', format="f32le")
        .output('pipe:', format="f32le", acodec="pcm_f32le", ac=1, ar=16000)  # FL32 format
        .run_async(pipe_stdin=True, pipe_stdout=True)
    )

    output_audio, _ = process.communicate(input=input_data.read())

    return np.frombuffer(output_audio, np.float32).flatten()

def writeFloat32toFile(buff, path):
    ######## DEBUGGING
    sample_rate = 44100  # You can change this to your desired sample rate
    output_file = path

    # # Convert audio_data_for_js back to a NumPy array of float32
    audio_array = np.frombuffer(buff, dtype=np.float32)

    # Scale the float32 array to int16
    audio_array = (audio_array * (2 ** 15)).astype(np.int16)

    # Write the NumPy array to a .wav file
    wavfile.write(output_file, sample_rate, audio_array)
    ########

def infer(audio_buffer):
    a = time.time()

    # fname = f'/src/debug/{str(uuid.uuid4())}.wav'

    # ##fname = '/src/debug/input.wav'

    writeFloat32toFile(audio_buffer, '/src/debug/input.wav')    

    # writeFloat32toFile(audio_buffer, fname)

    # audio_buffer = load_audio(fname, 16000)

    audio = model.single_custom(
        sid=1,
        audio=audio_buffer,
        embedder_model_name="hubert_base",
        embedding_output_layer="auto",
        f0_up_key=f0_up_key,
        f0_file=None,
        f0_method=f0_method,
        auto_load_index=False,
        faiss_index_file=None,
        index_rate=None,
        f0_relative=True,
        output_dir="out",
    )

    b = time.time()

    print ('Inference took', b - a)

    print('audio converted is', audio)

    raw_audio = audio.raw_data
    sample_width = audio.sample_width
    channels = audio.channels
    frame_rate = audio.frame_rate

    print('raw audio info is ', sample_width, channels, frame_rate)

    # Convert raw audio data to a NumPy array of floats
    audio_array = np.frombuffer(raw_audio, dtype=np.int16 if sample_width == 2 else np.int8)
    audio_array = audio_array.astype(np.float32, order='C') / (2 ** (8 * sample_width - 1))

    # Reshape the array to represent channels if needed
    audio_array = audio_array.reshape(-1, channels)

    # Now you have a NumPy array containing the audio data as float32
    # You can convert it to a Float32Array in the desired format if needed
    # For instance, to get the audio data in a format compatible with JavaScript's Float32Array:
    audio_data_for_js = audio_array.flatten().tobytes()

    writeFloat32toFile(audio_data_for_js, '/src/debug/output.wav')    
    return audio_data_for_js
