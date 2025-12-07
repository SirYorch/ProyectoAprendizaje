import subprocess
import json
import base64
from pathlib import Path
from pydub import AudioSegment
import os

def generate_lipsync(text, output_name="output"):
    mp3_path = Path(f"audios/audio.mp3")
    wav_path = Path(f"audios/audio.wav")
    json_path = Path(f"audios/audio.json")
    
    # Convertir MP3 a WAV solo si el MP3 existe
    if mp3_path.exists():
        print(f"MP3 encontrado. Convirtiendo a WAV...")
        audio = AudioSegment.from_mp3(mp3_path)
        audio.export(wav_path, format="wav")
        print(f"WAV generado: {wav_path}")
    else:
        print(f"Advertencia: No se encontró {mp3_path}")
        if not wav_path.exists():
            raise FileNotFoundError(f"No existe ni MP3 ni WAV en {mp3_path.parent}")

    # 3. LIPSYNC con Rhubarb
    result = subprocess.run([
        "./lipsync/bin/rhubarb",
        "-f", "json",
        "-o", json_path,
        wav_path,
        "-r", "phonetic"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode != 0:
        print("Error Rhubarb:", result.stderr.decode())
        raise RuntimeError("Error al ejecutar Rhubarb.")

    # 4. Cargar lipsync
    with open(json_path, "r") as f:
        lipsync_data = json.load(f)

    # 5. Retornar WAV en base64
    with open(wav_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")

    return {
        "audio_wav": audio_b64,
        "lipsync": lipsync_data
    }