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

multiprocessing.set_start_method("spawn", force=True)


f0_method = "rmvpe"
f0_up_key = 0
model_path = "model.pth"  # placed `model.pth` download from https://www.weights.gg/models/clo5vughf00anwswmzw3f4678
model_name = "matpat"  # Name to be added to output filenames

device = "cuda" if torch.cuda.is_available() else "cpu"
model = VoiceConvertModel(model_name, torch.load(model_path, map_location=device))



def load_opus_audio(packet):
   return Decoder.decode(packet, 16000)



def infer(audio_buffer):
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

    raw_audio = audio.raw_data
    sample_width = audio.sample_width
    channels = audio.channels
    frame_rate = audio.frame_rate

    # Convert raw audio data to a NumPy array of floats
    audio_array = np.frombuffer(raw_audio, dtype=np.int16 if sample_width == 2 else np.int8)
    audio_array = audio_array.astype(np.float32, order='C') / (2 ** (8 * sample_width - 1))

    # Reshape the array to represent channels if needed
    audio_array = audio_array.reshape(-1, channels)

    # Now you have a NumPy array containing the audio data as float32
    # You can convert it to a Float32Array in the desired format if needed
    # For instance, to get the audio data in a format compatible with JavaScript's Float32Array:
    audio_data_for_js = audio_array.flatten().tobytes()

    return audio_data_for_js
