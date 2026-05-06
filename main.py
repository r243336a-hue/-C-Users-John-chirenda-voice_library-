"""
Main entry point with GUI support.
"""

import os
import sys
import csv
import threading
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import db_utils, stt_utils, tts_utils, intent_classifier, playback_engine
from src.config import LOGS_DIR, PHRASE_HINTS, WAKE_WORD, REQUIRE_WAKE_WORD
from src.intent_classifier import classify_intent
from src.gui import LibraryGUI

gui = None
last_results = []
current_index = -1


def log_command(command, intent, action_success, details=""):
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_file = os.path.join(LOGS_DIR, f"commands_{datetime.now().strftime('%Y%m%d')}.csv")
    file_exists = os.path.isfile(log_file)
    with open(log_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "command", "intent", "success", "details"])
        writer.writerow([datetime.now().isoformat(), command, intent, action_success, details])
    if gui:
        gui.add_log_entry(
            f"[{datetime.now().strftime('%H:%M:%S')}] {command} -> {intent} ({'OK' if action_success else 'FAIL'})"
        )


def handle_typed_search(query):
    global last_results, current_index
    q = (query or "").strip()
    lower_q = q.lower()
    if lower_q.startswith("play "):
        q = q[5:].strip()
    results = db_utils.search_books(q)
    last_results = results
    current_index = 0 if results else -1
    if gui:
        gui.set_results(results)
    if results:
        titles = [r["title"] for r in results[:5]]
        msg = f"Found {len(results)} books. " + ", ".join(titles)
        tts_utils.speak(msg)
        if gui:
            gui.add_log_entry(f"Search results: {msg}")
    else:
        tts_utils.speak("No books found.")
        if gui:
            gui.add_log_entry("No books found.")


def play_book(book):
    if not book:
        return
    playback_engine.engine.play(book)
    tts_utils.speak(f"Now playing {book['title']}")
    if gui:
        gui.add_log_entry(f"Now playing: {book['title']}")


def play_next():
    global current_index
    if not last_results:
        return
    current_index = (current_index + 1) % len(last_results)
    play_book(last_results[current_index])


def pause_playback():
    playback_engine.engine.pause()


def voice_loop():
    tts_utils.speak("Voice library system starting. Please wait.")
    if gui:
        gui.update_status("Starting up...")

    books = db_utils.get_all_books()
    titles_authors = []
    for b in books:
        titles_authors.append(b["title"])
        if b["author"]:
            titles_authors.append(b["author"])
    PHRASE_HINTS.extend(titles_authors)
    PHRASE_HINTS.extend([WAKE_WORD, "search", "play", "pause", "resume", "stop", "help"])

    intent_classifier._load_books()

    ready_msg = "System ready. Say a command to begin."
    tts_utils.speak(ready_msg)
    if gui:
        gui.update_status("Ready - listening for commands...")

    while True:
        if gui:
            gui.update_status("Listening...")
        transcript = stt_utils.listen_for_command(use_wake_word=REQUIRE_WAKE_WORD)
        if not transcript:
            continue

        cleaned = transcript.lower().replace(WAKE_WORD, "").strip()
        if not cleaned:
            tts_utils.speak("Yes?")
            continue

        if gui:
            gui.update_status(f"Processing: '{cleaned}'")

        intent, data = classify_intent(cleaned)
        success = True
        details = ""

        try:
            if intent == "HELP":
                help_text = (
                    "You can say: search for a book, play a book, pause, resume, or stop. "
                    "For example, say 'library play pride and prejudice'."
                )
                tts_utils.speak(help_text)
                details = help_text
            elif intent == "STOP":
                playback_engine.engine.stop()
                tts_utils.speak("Stopped.")
                details = "Playback stopped"
            elif intent == "PAUSE":
                playback_engine.engine.pause()
                details = "Paused"
            elif intent == "RESUME":
                playback_engine.engine.resume()
                details = "Resumed"
            elif intent == "SEARCH":
                query = data
                results = db_utils.search_books(query)
                if results:
                    titles = [r["title"] for r in results[:5]]
                    msg = f"Found {len(results)} books. " + ", ".join(titles)
                    tts_utils.speak(msg)
                    details = msg
                else:
                    tts_utils.speak("No books found.")
                    details = "No books found"
            elif intent == "PLAY":
                book = data
                if playback_engine.engine.current_book == book and playback_engine.engine.is_paused:
                    playback_engine.engine.resume()
                    details = f"Resuming {book['title']}"
                else:
                    playback_engine.engine.play(book)
                    details = f"Playing {book['title']} by {book['author']}"
                    tts_utils.speak(f"Now playing {book['title']}")
            else:
                tts_utils.speak("I did not understand. Please say help for instructions.")
                success = False
                details = "Unhandled intent"
        except Exception as e:
            tts_utils.speak("An error occurred. Please try again.")
            print(f"Error: {e}")
            success = False
            details = str(e)

        log_command(transcript, intent, success, details)
        if gui:
            gui.update_status("Ready - listening for next command")
        time.sleep(0.1)


def main():
    global gui
    db_utils.init_db()
    gui = LibraryGUI(
        on_text_search=handle_typed_search,
        on_play=play_book,
        on_pause=pause_playback,
        on_next=play_next,
    )
    voice_thread = threading.Thread(target=voice_loop, daemon=True)
    voice_thread.start()
    gui.start()


if __name__ == "__main__":
    main()
