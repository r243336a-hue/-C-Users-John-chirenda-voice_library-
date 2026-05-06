"""
Simple test script to verify components.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import db_utils, tts_utils, intent_classifier, playback_engine


def test_db():
    print("Testing database...")
    db_utils.init_db()
    books = db_utils.get_all_books()
    print(f"Found {len(books)} books in database.")
    if books:
        print("First book:", books[0])


def test_tts():
    print("Testing TTS... (you should hear speech)")
    tts_utils.speak("Hello, this is a test of the text to speech engine.")
    print("TTS test complete.")


def test_intent():
    print("Testing intent classifier...")
    intent_classifier._load_books()
    tests = [
        ("find pride and prejudice", "PLAY"),
        ("search for adventure books", "SEARCH"),
        ("play the hobbit", "PLAY"),
        ("pause", "PAUSE"),
        ("resume", "RESUME"),
        ("stop", "STOP"),
        ("help", "HELP"),
    ]
    for transcript, expected_intent in tests:
        intent, _data = intent_classifier.classify_intent(transcript)
        print(f"'{transcript}' -> {intent} (expected {expected_intent})")
        if intent != expected_intent:
            print("  FAIL")


def test_playback():
    print("Testing playback engine...")
    books = db_utils.get_all_books()
    if not books:
        print("No books in database. Please populate first.")
        return
    book = books[0]
    print(f"Playing {book['title']}... (speech should start)")
    playback_engine.engine.play(book)
    input("Press Enter to stop playback...")
    playback_engine.engine.stop()
    print("Playback test complete.")


if __name__ == "__main__":
    test_db()
    test_tts()
    test_intent()
    test_playback()
