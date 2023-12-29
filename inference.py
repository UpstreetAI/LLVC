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

multiprocessing.set_start_method("spawn", force=True)


f0_method = "rmvpe"
f0_up_key = 0
model_path = "model.pth"  # placed `model.pth` download from https://www.weights.gg/models/clo5vughf00anwswmzw3f4678
model_name = "matpat"  # Name to be added to output filenames

device = "cuda" if torch.cuda.is_available() else "cpu"
model = VoiceConvertModel(model_name, torch.load(model_path, map_location=device))


def infer(audio_buffer):
    model.single(
        sid=1,
        input_audio=audio_buffer,
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
