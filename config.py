"""
Configuration settings for the voice library.
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CLEANED_DIR = os.path.join(DATA_DIR, "cleaned")
DB_DIR = os.path.join(DATA_DIR, "database")
DB_PATH = os.path.join(DB_DIR, "library.db")
AUDIO_CACHE_DIR = os.path.join(BASE_DIR, "audio_cache")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

TTS_MODEL_NAME = "tts_models/en/vctk/vits"
TTS_SPEAKER = "p226"

PHRASE_HINTS = []
WAKE_WORD = "library"
REQUIRE_WAKE_WORD = False

STT_ENGINE = os.environ.get("VOICE_LIBRARY_STT_ENGINE", "google").lower().strip()
VOSK_MODEL_DIR = os.environ.get(
    "VOICE_LIBRARY_VOSK_MODEL",
    os.path.join(BASE_DIR, "models", "vosk-model-small-en-us-0.15"),
)

INTENT_KEYWORDS = {
    "SEARCH": ["find", "search", "look for", "get"],
    "PLAY": ["play", "read", "start"],
    "PAUSE": ["pause", "stop reading", "hold"],
    "RESUME": ["resume", "continue", "go on"],
    "STOP": ["stop", "quit", "exit"],
    "HELP": ["help", "what can I say", "instructions"],
}

FUZZY_THRESHOLD = 0.75
