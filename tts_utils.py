"""
Handles text-to-speech using Coqui TTS (offline) and audio playback via pygame.
"""

import os
import hashlib
import tempfile
import pygame
from .config import AUDIO_CACHE_DIR, TTS_MODEL_NAME, TTS_SPEAKER

pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

_tts = None


def _get_tts():
    """Lazy load the TTS model."""
    global _tts
    if _tts is None:
        # Ensure eSpeak-NG is discoverable on Windows
        espeak_dir = os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "eSpeak NG")
        espeak_bin = os.path.join(espeak_dir, "espeak-ng.exe")
        if os.path.exists(espeak_bin):
            os.environ["PATH"] = espeak_dir + os.pathsep + os.environ.get("PATH", "")
            os.environ["PHONEMIZER_ESPEAK_PATH"] = espeak_bin
            os.environ["ESPEAK_PATH"] = espeak_bin
            espeak_data = os.path.join(espeak_dir, "espeak-ng-data")
            if os.path.isdir(espeak_data):
                os.environ["ESPEAK_DATA_PATH"] = espeak_data
        os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)
        print(f"Loading TTS model {TTS_MODEL_NAME}... (this may take a while the first time)")
        from TTS.api import TTS
        _tts = TTS(model_name=TTS_MODEL_NAME, progress_bar=False)
    return _tts


def _get_audio_file(text, speaker=None):
    """Generate or retrieve cached audio file for given text."""
    key = f"{text}_{speaker or TTS_SPEAKER}"
    hash_key = hashlib.md5(key.encode()).hexdigest()
    cache_path = os.path.join(AUDIO_CACHE_DIR, f"{hash_key}.wav")
    if os.path.exists(cache_path):
        return cache_path

    tts = _get_tts()
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_file.close()
    tts.tts_to_file(text=text, speaker=speaker or TTS_SPEAKER, file_path=temp_file.name)
    os.rename(temp_file.name, cache_path)
    return cache_path


def speak(text, speaker=None, block=True):
    """Convert text to speech and play it."""
    if not text.strip():
        return
    audio_file = _get_audio_file(text, speaker)
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play()
    if block:
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)


def speak_nonblocking(text, speaker=None):
    """Start playing audio and return immediately."""
    audio_file = _get_audio_file(text, speaker)
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play()


def stop_playback():
    """Stop any currently playing speech."""
    pygame.mixer.music.stop()
