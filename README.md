# Voice-Navigable Digital Library

A voice-controlled digital library for visually impaired users, built with free and open-source tools.

## Folder Structure

```
voice_library/
│
├── data/
│   ├── cleaned/          # Place cleaned book text files here
│   ├── raw/              # Optional raw files
│   └── database/         # SQLite database will be created here
│
├── audio_cache/          # Cached TTS audio files
├── logs/                 # Command logs (CSV)
├── src/
│   ├── config.py
│   ├── db_utils.py
│   ├── stt_utils.py
│   ├── tts_utils.py
│   ├── intent_classifier.py
│   ├── playback_engine.py
│   ├── main.py
│   └── test_system.py
│
├── books_metadata.csv    # Sample metadata file (you will edit this)
├── requirements.txt
└── README.md
```

## Features

- Voice commands (search, play, pause, resume, stop, help)
- Offline text-to-speech using Coqui TTS
- Speech-to-text using Google Speech Recognition (free tier)
- SQLite database for book metadata
- Fuzzy matching for book titles/authors
- Command logging for usability analysis

## Installation (Windows)

1. Create a virtual environment:
   ```
   python -m venv venv
   ```
2. Activate it:
   ```
   venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Place your cleaned text files in `data/cleaned/`.
5. Edit `books_metadata.csv` with the correct paths and metadata.
6. Populate the database:
   ```
   python -c "from src.db_utils import populate_from_csv; populate_from_csv('books_metadata.csv')"
   ```
7. Run the main program:
   ```
   python src/main.py
   ```

## Usage

- Wake word: "library" (optional)
- Example: "library play pride and prejudice" or just "play pride and prejudice"
- Commands: search, play, pause, resume, stop, help

## Logging

Commands are logged in `logs/commands_YYYYMMDD.csv` with timestamps, intent, and success status.

## Testing

Run:
```
python src/test_system.py
```

## Notes

- The first TTS run can be slow while the model downloads and caches.
- Google Speech Recognition requires internet access.
