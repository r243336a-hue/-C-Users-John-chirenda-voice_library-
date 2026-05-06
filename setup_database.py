#!/usr/bin/env python3
"""
Setup script to create and populate the voice library database.
Run this once to initialize your library.
"""

import sqlite3
import os
from pathlib import Path

DB_PATH = Path('data/database/library.db')
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create books table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        file_path TEXT NOT NULL
    )
''')

# Populate with your cleaned books
# Adjust this path if your books are stored elsewhere
books_folder = Path('books')
if books_folder.exists():
    for txt in sorted(books_folder.glob('*_cleaned.txt')):
        # Extract title and author from filename (adjust as needed)
        name = txt.stem.replace('_cleaned', '')
        parts = name.split('_')
        if len(parts) >= 2:
            author = ' '.join(parts[1:]).title()
            title = parts[0].title()
        else:
            title = name.title()
            author = 'Unknown'
        
        cursor.execute('INSERT INTO books (title, author, file_path) VALUES (?, ?, ?)',
                       (title, author, str(txt)))
        print(f"Added: {title} by {author}")
else:
    print(f"Warning: {books_folder} folder not found.")
    print("Please create a 'books' folder with your cleaned text files named like: title_author_cleaned.txt")

conn.commit()
conn.close()
print(f"\nDatabase created at: {DB_PATH}")
print("You can now run: python app.py")
