from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import os

def tts(texto, idioma='es', velocidad=1.4, guardar_archivo=True, nombre_archivo="audios/audio.mp3"):
    # Generar audio con gTTS
    tts = gTTS(text=texto, lang=idioma, slow=False)
    
    # Guardar temporalmente
    archivo_temp = "temp_audio.mp3"
    tts.save(archivo_temp)
    
    # Cargar y modificar velocidad con pydub
    audio = AudioSegment.from_mp3(archivo_temp)
    
    # Cambiar velocidad manteniendo el tono
    audio_rapido = audio.speedup(playback_speed=velocidad)
    
    if guardar_archivo:
        audio_rapido.export(nombre_archivo, format="mp3")
        print(f"Audio guardado en: {nombre_archivo}")
    
    # Limpiar archivo temporal
    os.remove(archivo_temp)
    
    return audio_rapido