from __future__ import annotations

import csv
import difflib
import os
import sqlite3
from datetime import datetime
from pathlib import Path

import speech_recognition as sr
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "database" / "library.db"
CSV_PATH = REPO_ROOT / "books_metadata.csv"
LOGS_DIR = REPO_ROOT / "logs"

FUZZY_THRESHOLD = 0.75


# ---------------------------------------------------------------------------
# Book loading
# ---------------------------------------------------------------------------

def normalize_book_path(value: str) -> Path:
    path = Path(value or "")
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def load_books_from_csv() -> list[dict[str, str]]:
    """Primary source: books_metadata.csv in repo root."""
    if not CSV_PATH.exists():
        return []

    books: list[dict[str, str]] = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=1):
            file_path = row.get("file_path", "").strip()
            resolved_path = normalize_book_path(file_path)
            if not resolved_path.exists():
                # Try just the filename in the cleaned dir
                alternate = REPO_ROOT / "data" / "cleaned" / Path(file_path).name
                if alternate.exists():
                    resolved_path = alternate

            books.append(
                {
                    "id": str(idx),
                    "title": row.get("title", "Unknown Title").strip(),
                    "author": row.get("author", "Unknown Author").strip(),
                    "tags": row.get("subject_tags", "").strip(),
                    "category": row.get("category", "General").strip() or "General",
                    "language": row.get("language", "English").strip() or "English",
                    "file_path": str(resolved_path),
                }
            )

    return books


def load_books_from_db() -> list[dict[str, str]]:
    """Fallback source: SQLite database."""
    if not DB_PATH.exists():
        return []

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title, author, subject_tags, file_path FROM books"
        )
        rows = cursor.fetchall()
        conn.close()
    except Exception as exc:
        print(f"[WARN] DB read failed: {exc}")
        return []

    books: list[dict[str, str]] = []
    for book_id, title, author, tags, file_path in rows:
        resolved_path = normalize_book_path(file_path or "")
        books.append(
            {
                "id": str(book_id),
                "title": (title or "Unknown Title").strip(),
                "author": (author or "Unknown Author").strip(),
                "tags": (tags or "").strip(),
                "category": "General",
                "language": "English",
                "file_path": str(resolved_path),
            }
        )

    return books


def load_books() -> list[dict[str, str]]:
    books = load_books_from_csv()
    if books:
        return books
    print("[INFO] CSV not found or empty — falling back to SQLite database.")
    return load_books_from_db()


try:
    BOOKS = load_books()
    print(f"[INFO] Loaded {len(BOOKS)} books.")
except Exception as exc:
    print(f"[ERROR] Failed to load books: {exc}")
    BOOKS = []


# ---------------------------------------------------------------------------
# Search helpers
# ---------------------------------------------------------------------------

def _fuzzy_search(query: str) -> list[dict[str, str]]:
    """
    Fuzzy title/author match using difflib with threshold 0.75,
    falling back to substring match on title, author, and tags.
    """
    q = query.lower().strip()
    if not q:
        return list(BOOKS)

    # Build candidate strings for fuzzy matching
    candidates = []
    for book in BOOKS:
        candidates.append(book["title"].lower())
        candidates.append(book["author"].lower())

    title_matches = difflib.get_close_matches(q, candidates, n=5, cutoff=FUZZY_THRESHOLD)

    matched: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    # Fuzzy hits first
    for m in title_matches:
        for book in BOOKS:
            if book["id"] not in seen_ids and (
                book["title"].lower() == m or book["author"].lower() == m
            ):
                matched.append(book)
                seen_ids.add(book["id"])

    # Substring fallback
    for book in BOOKS:
        if book["id"] not in seen_ids:
            searchable = f"{book['title']} {book['author']} {book['tags']} {book['category']}".lower()
            if q in searchable:
                matched.append(book)
                seen_ids.add(book["id"])

    return matched


def search_books(
    query: str,
    category: str | None = None,
    language: str | None = None,
) -> list[dict[str, str]]:
    results = _fuzzy_search(query)

    category_filter = (category or "").lower().strip()
    language_filter = (language or "").lower().strip()

    if category_filter and category_filter not in ("all categories", ""):
        results = [b for b in results if b["category"].lower() == category_filter]

    if language_filter and language_filter not in ("all languages", ""):
        results = [b for b in results if b["language"].lower() == language_filter]

    return results


# ---------------------------------------------------------------------------
# Logging helper
# ---------------------------------------------------------------------------

def log_event(event_type: str, data: dict) -> None:
    """Append a structured event row to today's web_events CSV."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"web_events_{datetime.now().strftime('%Y%m%d')}.csv"
    file_exists = log_file.exists()
    with open(log_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "event_type", "query", "intent", "result_count", "book_id", "score", "details"])
        writer.writerow([
            datetime.now().isoformat(),
            event_type,
            data.get("query", ""),
            data.get("intent", ""),
            data.get("result_count", ""),
            data.get("book_id", ""),
            data.get("score", ""),
            data.get("details", ""),
        ])


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/welcome_audio")
def welcome_audio():
    """Serve the welcome MP3 from the user's Music folder."""
    from flask import send_file
    audio_path = Path(r"C:\Users\John chirenda\Pictures\Welcome message.mp3")
    if not audio_path.exists():
        return jsonify({"error": "Welcome audio file not found"}), 404
    return send_file(str(audio_path), mimetype="audio/mpeg")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/books")
def get_books():
    return jsonify({"books": BOOKS})


@app.route("/search")
def search_route():
    """GET /search?q=...&category=...&language=..."""
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "")
    language = request.args.get("language", "")
    results = search_books(query, category, language)
    log_event("search", {"query": query, "result_count": len(results)})
    return jsonify({"books": results, "count": len(results)})


@app.route("/book_text/<int:book_id>")
def book_text(book_id: int):
    for book in BOOKS:
        if int(book["id"]) == book_id:
            try:
                with open(book["file_path"], "r", encoding="utf-8") as f:
                    text = f.read()
                log_event("play", {"book_id": book_id, "details": book["title"]})
                return jsonify({"text": text, "title": book["title"], "author": book["author"]})
            except Exception as exc:
                return jsonify({"error": f"Could not read book file: {exc}"}), 500

    return jsonify({"error": "Book not found"}), 404


@app.route("/log_event", methods=["POST"])
def log_event_route():
    """POST /log_event — called by the frontend to log UI interactions."""
    data = request.get_json(silent=True) or {}
    log_event(data.get("event_type", "ui_event"), data)
    return jsonify({"status": "ok"})


@app.route("/listen", methods=["POST"])
def listen():
    """Voice command endpoint — accepts JSON {query} or raw microphone audio."""
    if request.is_json:
        data = request.get_json() or {}
        command = data.get("query", "")
    else:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Listening...")
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            except sr.WaitTimeoutError:
                return jsonify({"error": "No speech detected. Please try again."}), 400

        try:
            command = recognizer.recognize_google(audio, language="en-ZA")
            print(f"Command: {command}")
        except sr.UnknownValueError:
            return jsonify({"error": "Could not understand audio. Please speak clearly."}), 400
        except sr.RequestError:
            return jsonify({"error": "Speech recognition service unavailable."}), 500

    cmd_lower = (command or "").lower().strip()

    # --- Intent classification ---
    SEARCH_KEYWORDS = ["find", "search", "look for", "show me", "get"]
    SHONA_SEARCH = ["tsvaga"]  # Shona: "search"

    is_search = any(kw in cmd_lower for kw in SEARCH_KEYWORDS + SHONA_SEARCH)

    if is_search:
        query = cmd_lower
        for kw in SEARCH_KEYWORDS + SHONA_SEARCH:
            if kw in query:
                query = query.split(kw, 1)[-1].strip()
                for filler in ("for ", "a ", "an ", "the "):
                    if query.startswith(filler):
                        query = query[len(filler):]
                break

        if not query:
            return jsonify({"message": "What would you like to search for? Try again."})

        results = search_books(query)
        log_event("voice_search", {"query": query, "result_count": len(results), "intent": "SEARCH"})

        if results:
            return jsonify({"message": f"Found {len(results)} book(s).", "books": results})
        return jsonify({"message": f"No books found for '{query}'. Try a different title, author, or genre."})

    return jsonify({
        "message": (
            "Command not recognised. Say 'find' followed by a title, author, or genre. "
            "For example: 'find mystery books' or 'find Arthur Conan Doyle'."
        )
    })


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
