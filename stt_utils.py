"""
Handles voice command capture and transcription using either:
- Google Speech Recognition (online) via SpeechRecognition
- Vosk (offline) via Vosk model files
"""

import json
import speech_recognition as sr
from .config import STT_ENGINE, VOSK_MODEL_DIR, WAKE_WORD

_vosk_model = None


def _load_vosk():
    global _vosk_model
    if _vosk_model is not None:
        return _vosk_model

    try:
        from vosk import Model, SetLogLevel
    except Exception as e:
        raise RuntimeError(
            "Vosk is not installed. Install it with: pip install vosk"
        ) from e

    SetLogLevel(-1)
    _vosk_model = Model(VOSK_MODEL_DIR)
    return _vosk_model


def _recognize_vosk(audio: sr.AudioData) -> str:
    from vosk import KaldiRecognizer

    model = _load_vosk()
    # Vosk expects 16kHz, 16-bit, mono PCM.
    pcm = audio.get_raw_data(convert_rate=16000, convert_width=2)
    rec = KaldiRecognizer(model, 16000)
    rec.SetWords(True)
    rec.AcceptWaveform(pcm)
    result = json.loads(rec.Result() or "{}")
    return (result.get("text") or "").strip()


def listen_for_command(use_wake_word=True):
    """
    Listen for a command, optionally requiring a wake word.
    Returns transcribed text or None if failed.
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        except sr.WaitTimeoutError:
            print("No speech detected.")
            return None

    try:
        if STT_ENGINE == "vosk":
            text = _recognize_vosk(audio)
        else:
            text = recognizer.recognize_google(
                audio,
                language="en-US",
                show_all=False,
            )

        if not text:
            print("Could not understand audio.")
            return None

        print(f"You said: {text}")
        if use_wake_word and WAKE_WORD.lower() not in text.lower():
            print(f"Wake word '{WAKE_WORD}' not detected. Ignoring command.")
            return None
        return text
    except sr.UnknownValueError:
        print("Could not understand audio.")
        return None
    except sr.RequestError as e:
        print(f"STT service error: {e}")
        return None
    except Exception as e:
        print(f"STT error: {e}")
        return None
