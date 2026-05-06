import pygame
import tempfile
import os
from TTS.api import TTS

class AudioPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.tts = TTS(model_name="tts_models/en/vctk/vits", progress_bar=False)
        self.current_file = None
        self.is_playing = False

    def speak(self, text, speaker='p236'):
        # Convert text to speech and play
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            self.tts.tts_to_file(text=text, speaker=speaker, file_path=tmp.name)
            self.current_file = tmp.name
        pygame.mixer.music.load(self.current_file)
        pygame.mixer.music.play()
        self.is_playing = True

    def play(self):
        if not self.is_playing and self.current_file:
            pygame.mixer.music.unpause()
            self.is_playing = True

    def pause(self):
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False

    def stop(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        if self.current_file and os.path.exists(self.current_file):
            os.remove(self.current_file)
            self.current_file = None

# Global instance
player = AudioPlayer()
