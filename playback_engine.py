"""
Manages playback of a book: reading text in chunks and handling pause/resume/stop.
"""

import os
import threading
import time
from . import tts_utils
from .config import CLEANED_DIR


class PlaybackEngine:
    def __init__(self):
        self.current_book = None
        self.current_chunks = []
        self.chunk_index = 0
        self.is_playing = False
        self.is_paused = False
        self.thread = None
        self.lock = threading.Lock()

    def _read_book_chunks(self, book):
        file_path = book["file_path"]
        if not os.path.exists(file_path):
            alt_path = os.path.join(CLEANED_DIR, os.path.basename(file_path))
            if os.path.exists(alt_path):
                file_path = alt_path
            else:
                raise FileNotFoundError(f"Book file not found: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks = []
        for p in paragraphs:
            if len(p) > 500:
                import re

                sentences = re.split(r"(?<=[.!?])\s+", p)
                chunks.extend([s.strip() for s in sentences if s.strip()])
            else:
                chunks.append(p)
        return chunks

    def play(self, book, start_from_beginning=True):
        with self.lock:
            if self.is_playing:
                self.stop()
            self.current_book = book
            if start_from_beginning:
                self.chunk_index = 0
                self.current_chunks = self._read_book_chunks(book)
            else:
                if not self.current_chunks:
                    self.current_chunks = self._read_book_chunks(book)
            self.is_playing = True
            self.is_paused = False
            self.thread = threading.Thread(target=self._play_loop)
            self.thread.daemon = True
            self.thread.start()

    def _play_loop(self):
        while self.is_playing:
            if self.is_paused:
                time.sleep(0.1)
                continue
            if self.chunk_index >= len(self.current_chunks):
                tts_utils.speak("Finished reading the book.")
                self.stop()
                break
            chunk = self.current_chunks[self.chunk_index]
            tts_utils.speak(chunk, block=True)
            self.chunk_index += 1
            time.sleep(0.2)

    def pause(self):
        with self.lock:
            if self.is_playing and not self.is_paused:
                self.is_paused = True
                tts_utils.stop_playback()
                tts_utils.speak("Paused.")

    def resume(self):
        with self.lock:
            if self.is_playing and self.is_paused:
                self.is_paused = False
                tts_utils.speak("Resuming.")

    def stop(self):
        with self.lock:
            if self.is_playing:
                self.is_playing = False
                self.is_paused = False
                tts_utils.stop_playback()
                self.current_book = None
                self.current_chunks = []
                self.chunk_index = 0
                if self.thread and self.thread.is_alive():
                    pass


engine = PlaybackEngine()
