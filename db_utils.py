"""
Handles database connection and queries.
"""

import sqlite3
import os
from .config import DB_PATH, CLEANED_DIR


def init_db():
    """Create the database and books table if not exists."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT,
            subject_tags TEXT,
            file_path TEXT,
            wordcount INTEGER,
            filesize_bytes INTEGER
        )
        """
    )
    cursor.execute("PRAGMA table_info(books)")
    cols = {row[1] for row in cursor.fetchall()}
    expected = {"id", "title", "author", "subject_tags", "file_path", "wordcount", "filesize_bytes"}
    if not expected.issubset(cols):
        cursor.execute("DROP TABLE IF EXISTS books")
        cursor.execute(
            """
            CREATE TABLE books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT,
                subject_tags TEXT,
                file_path TEXT,
                wordcount INTEGER,
                filesize_bytes INTEGER
            )
            """
        )
    conn.commit()
    conn.close()


def populate_from_csv(csv_path):
    """
    Populate database from a CSV file with columns:
    title, author, subject_tags, file_path, wordcount, filesize_bytes
    """
    import csv

    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            file_path = row["file_path"]
            if not os.path.exists(file_path) and CLEANED_DIR:
                alt_path = os.path.join(CLEANED_DIR, os.path.basename(file_path))
                if os.path.exists(alt_path):
                    file_path = alt_path
            cursor.execute(
                """
                INSERT INTO books (title, author, subject_tags, file_path, wordcount, filesize_bytes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    row["title"],
                    row["author"],
                    row["subject_tags"],
                    file_path,
                    int(row["wordcount"]),
                    int(row["filesize_bytes"]),
                ),
            )
    conn.commit()
    conn.close()
    print(f"Database populated from {csv_path}")


def get_all_books():
    """Return all books as list of dicts."""
    _ensure_seeded()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def search_books(query):
    """
    Simple search on title, author, subject_tags.
    Returns list of books matching any field (case-insensitive).
    """
    _ensure_seeded()
    q = (query or "").strip().lower()
    if q in {"", "title", "all", "books", "list", "*"}:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM books ORDER BY title")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    pattern = f"%{q}%"
    cursor.execute(
        """
        SELECT * FROM books
        WHERE LOWER(title) LIKE ? OR LOWER(author) LIKE ? OR LOWER(subject_tags) LIKE ?
        """,
        (pattern, pattern, pattern),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_book_by_id(book_id):
    """Return a single book by its ID."""
    _ensure_seeded()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def _ensure_seeded():
    """Auto-populate from cleaned folder if DB is empty."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM books")
    count = cursor.fetchone()[0]
    if not os.path.isdir(CLEANED_DIR):
        conn.close()
        return

    cursor.execute("SELECT file_path FROM books")
    existing_paths = {row[0] for row in cursor.fetchall()}

    for filename in os.listdir(CLEANED_DIR):
        if not filename.endswith(".txt"):
            continue
        file_path = os.path.join(CLEANED_DIR, filename)
        if file_path in existing_paths:
            continue
        title, author = _title_author_from_file(filename, file_path)
        cursor.execute(
            "INSERT INTO books (title, author, subject_tags, file_path, wordcount, filesize_bytes) VALUES (?, ?, ?, ?, ?, ?)",
            (title, author, "", file_path, 0, os.path.getsize(file_path)),
        )
    conn.commit()
    conn.close()


def _title_author_from_file(filename, file_path):
    base = filename.replace("_cleaned", "").replace(".txt", "").strip()
    if base.lower().startswith("title"):
        base = base[len("title") :].lstrip("_ ").strip()
    parts = [p for p in base.split("_") if p]
    title = ""
    author = "Unknown"
    if len(parts) >= 2:
        title = parts[0].replace("-", " ").strip().title()
        author = " ".join(parts[1:]).replace("-", " ").strip().title()
    elif len(parts) == 1:
        author = parts[0].replace("-", " ").strip().title()
    if not title:
        first_line = _first_non_empty_line(file_path)
        if first_line:
            title = first_line[:200]
    if not title:
        title = "Untitled"
    return title, author


def _first_non_empty_line(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                cleaned = line.strip()
                if cleaned:
                    return cleaned
    except Exception:
        return None
    return None
