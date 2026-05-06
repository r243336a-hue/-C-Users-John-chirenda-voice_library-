import sqlite3
import os

db_path = 'data/database/library.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        subject_tags TEXT,
        file_path TEXT NOT NULL,
        word_count INTEGER,
        file_size_bytes INTEGER
    )
''')
conn.commit()
conn.close()
print("Database created.")
