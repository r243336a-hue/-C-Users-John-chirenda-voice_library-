from flask import Flask, render_template, request, jsonify
import sqlite3
import speech_recognition as sr
from pathlib import Path

app = Flask(__name__)

# Database path
DB_PATH = Path(__file__).parent / "data" / "database" / "library.db"

# Load books once
def load_books():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, author, file_path FROM books")
    books = cursor.fetchall()
    conn.close()
    return books

BOOKS = load_books()

def search_books(query):
    query = query.lower()
    results = []
    for book in BOOKS:
        if query in book[1].lower() or query in book[2].lower():
            results.append(book)
    return results[:3]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/listen', methods=['POST'])
def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
        except sr.WaitTimeoutError:
            return jsonify({'error': 'No speech detected. Please try again.'}), 400
    try:
        command = recognizer.recognize_google(audio)
        print(f"Command: {command}")
    except sr.UnknownValueError:
        return jsonify({'error': 'Could not understand audio. Please speak clearly.'}), 400
    except sr.RequestError:
        return jsonify({'error': 'Speech recognition service unavailable.'}), 500

    cmd_lower = command.lower()
    if 'find' in cmd_lower or 'search' in cmd_lower:
        # Extract query - take everything after the keyword
        if 'find' in cmd_lower:
            query = cmd_lower.split('find', 1)[-1].strip()
        else:
            query = cmd_lower.split('search', 1)[-1].strip()
        if not query:
            return jsonify({'message': 'What would you like to search for? Try again.'})
        results = search_books(query)
        if results:
            books_data = [{'id': b[0], 'title': b[1], 'author': b[2]} for b in results]
            return jsonify({'message': f"Found {len(results)} book(s).", 'books': books_data, 'results': results})
        else:
            return jsonify({'message': 'No books found. Try a different title, author, or genre.'})
    else:
        return jsonify({'message': "Command not recognised. Say 'find' followed by a title, author, or genre. For example, 'find mystery books'."})

@app.route('/book_text/<int:book_id>')
def book_text(book_id):
    for book in BOOKS:
        if book[0] == book_id:
            try:
                with open(book[3], 'r', encoding='utf-8') as f:
                    text = f.read()
                return jsonify({'text': text, 'title': book[1], 'author': book[2]})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'Book not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
