from flask import Flask, render_template, request, jsonify, session
import sqlite3
import os
from pathlib import Path

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

DB_PATH = Path(__file__).parent.parent / "data" / "database" / "library.db"

# Conversation states
STATE_WELCOME = 0
STATE_AWAITING_BOOK_SELECTION = 1
STATE_PLAYING = 2

def load_books():
    """Load all books from the database."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, author, file_path FROM books")
        books = cursor.fetchall()
        conn.close()
        print(f"✓ Loaded {len(books)} books from database")
        return books
    except Exception as e:
        print(f"✗ Error loading books: {e}")
        return []

books_list = load_books()

def search_books(query):
    """Search for books by title or author."""
    if not query or not books_list:
        return []
    
    query = query.lower().strip()
    results = []
    
    # If asking for all books
    if query in {"title", "all", "books", "list", "*"}:
        return books_list[:20]  # Return first 20 books
    
    # Search by title and author
    for book in books_list:
        title = book[1].lower() if book[1] else ""
        author = book[2].lower() if book[2] else ""
        
        if query in title or query in author:
            results.append(book)
    
    return results[:5]  # Return max 5 results

def format_book_titles(books, max_items=10):
    """Format book titles for spoken output."""
    if not books:
        return "No books available"
    
    titles = [book[1] for book in books[:max_items]]
    if len(books) > max_items:
        return ", ".join(titles) + f", and {len(books) - max_items} more"
    return ", ".join(titles)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search_route():
    """Web search endpoint for the UI."""
    query = request.args.get("q", "").strip()
    results = search_books(query) if query else books_list
    return jsonify([{
        'id': b[0],
        'title': b[1],
        'author': b[2],
        'file_path': b[3]
    } for b in results])

@app.route('/listen', methods=['POST'])
def listen():
    """Handle voice commands using a state machine."""
    try:
        data = request.get_json(silent=True) or {}
        command = (data.get("command") or "").strip()
        state = session.get("conv_state", STATE_WELCOME)
        
        print(f"[DEBUG] State: {state}, Command: '{command}'")
        
        # STATE: WELCOME - Just moved past welcome message
        if state == STATE_WELCOME:
            session["conv_state"] = STATE_AWAITING_BOOK_SELECTION
            book_count = len(books_list)
            
            if book_count == 0:
                return jsonify({
                    "action": "speak",
                    "text": "I'm sorry, but there are no books available in the library right now."
                })
            
            return jsonify({
                "action": "speak",
                "text": f"You can say 'find' followed by a title, author, or genre. "
                        f"I have {book_count} books. To hear some book titles, say 'list books'. "
                        f"Which book would you like to read?"
            })
        
        # STATE: AWAITING BOOK SELECTION - User should speak a command
        elif state == STATE_AWAITING_BOOK_SELECTION:
            if not command:
                return jsonify({
                    "action": "speak",
                    "text": "I didn't hear anything. Please say 'find' followed by a title or author, or say 'list books'."
                })
            
            cmd_lower = command.lower()
            
            # User wants to hear the list
            if "list" in cmd_lower and "books" in cmd_lower:
                title_list = format_book_titles(books_list, max_items=15)
                return jsonify({
                    "action": "speak",
                    "text": f"Available books: {title_list}. Which book would you like to read?"
                })
            
            # User wants to search
            if "find" in cmd_lower or "search" in cmd_lower or "look for" in cmd_lower:
                # Extract query after the search word
                query = cmd_lower
                for prefix in ["find ", "search ", "look for ", "lookup ", "show me "]:
                    if query.startswith(prefix):
                        query = query[len(prefix):].strip()
                        break
                
                if not query:
                    return jsonify({
                        "action": "speak",
                        "text": "Please say a title, author, or genre after 'find'."
                    })
                
                results = search_books(query)
                if not results:
                    return jsonify({
                        "action": "speak",
                        "text": f"No books found matching '{query}'. Try another title, author, or genre."
                    })
                
                # Store results in session
                session["search_results"] = [(b[0], b[1], b[2], b[3]) for b in results]
                
                # Format response
                if len(results) == 1:
                    book = results[0]
                    session["current_book_id"] = book[0]
                    return jsonify({
                        "action": "speak",
                        "text": f"I found one book: {book[1]} by {book[2]}. Say 'play' to read it, or say 'find' to search again.",
                        "search_results": [{"id": b[0], "title": b[1], "author": b[2]} for b in results]
                    })
                else:
                    result_text = ", ".join([f"{i+1}. {b[1]} by {b[2]}" for i, b in enumerate(results[:3])])
                    return jsonify({
                        "action": "speak",
                        "text": f"I found {len(results)} books. {result_text}. Say the number or title to select, or say 'find' to search again.",
                        "search_results": [{"id": b[0], "title": b[1], "author": b[2]} for b in results]
                    })
            
            # User might be saying a book title directly
            cmd_lower_stripped = cmd_lower.strip()
            for book in books_list:
                if cmd_lower_stripped in book[1].lower() or cmd_lower_stripped == book[1].lower():
                    session["current_book_id"] = book[0]
                    session["conv_state"] = STATE_PLAYING
                    return jsonify({
                        "action": "speak",
                        "text": f"Starting {book[1]} by {book[2]}. You can say pause, resume, or stop."
                    })
            
            # If we get here, didn't understand
            return jsonify({
                "action": "speak",
                "text": "I didn't understand. Please say 'find' followed by a title or author, or say 'list books'."
            })
        
        # STATE: PLAYING - Handle playback commands
        elif state == STATE_PLAYING:
            cmd_lower = command.lower()
            
            if "pause" in cmd_lower:
                return jsonify({"action": "pause"})
            elif "resume" in cmd_lower or "continue" in cmd_lower:
                return jsonify({"action": "resume"})
            elif "stop" in cmd_lower:
                session["conv_state"] = STATE_AWAITING_BOOK_SELECTION
                return jsonify({
                    "action": "stop",
                    "text": "Playback stopped. Say 'find' to search for another book."
                })
            elif "next" in cmd_lower:
                return jsonify({"action": "next"})
            elif "slow" in cmd_lower:
                return jsonify({"action": "rate", "value": 0.7})
            elif "fast" in cmd_lower:
                return jsonify({"action": "rate", "value": 1.2})
            else:
                return jsonify({
                    "action": "speak",
                    "text": "Say pause, resume, stop, or find to search again."
                })
        
        return jsonify({"action": "error", "text": "Unknown state"})
    
    except Exception as e:
        print(f"Error in /listen: {e}")
        return jsonify({"action": "error", "text": str(e)})

@app.route('/book_text/<int:book_id>', methods=['GET'])
def book_text(book_id):
    """Get the full text of a book."""
    try:
        for book in books_list:
            if book[0] == book_id:
                file_path = book[3]
                if not os.path.exists(file_path):
                    return jsonify({"error": "File not found"}), 404
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                
                return jsonify({
                    "id": book[0],
                    "title": book[1],
                    "author": book[2],
                    "text": text
                })
        
        return jsonify({"error": "Book not found"}), 404
    except Exception as e:
        print(f"Error reading book: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("Voice Library Backend Starting")
    print("=" * 60)
    print(f"Database: {DB_PATH}")
    print(f"Books loaded: {len(books_list)}")
    if books_list:
        print(f"First book: {books_list[0][1]} by {books_list[0][2]}")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)


@app.route("/book_text/<path:book_name>", methods=["GET"])
def book_text(book_name):
    book_name = unquote(book_name)
    file_path = os.path.join(BOOKS_FOLDER, book_name)
    if not os.path.exists(file_path):
        return jsonify({"error": "Book not found"}), 404
    meta = get_metadata_for_file(book_name)
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    return jsonify({"text": text, "title": meta.get("title", book_name), "author": meta.get("author", "")})


@app.route("/metadata")
def metadata():
    items = []
    for file in os.listdir(BOOKS_FOLDER):
        if not file.endswith(".txt"):
            continue
        meta = get_metadata_for_file(file)
        items.append(
            {
                "file": file,
                "title": meta.get("title") or file.replace("title_", "").replace(".txt", ""),
                "author": meta.get("author", ""),
                "tags": meta.get("tags", []),
                "category": meta.get("category", "General"),
                "language": meta.get("language", "unknown"),
            }
        )
    return jsonify(items)

@app.route("/log", methods=["POST"])
def log_event():
    payload = request.get_json(silent=True) or {}
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_file = os.path.join(LOGS_DIR, f"web_events_{datetime.now().strftime('%Y%m%d')}.csv")
    is_new = not os.path.exists(log_file)
    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "event": payload.get("event", ""),
        "query": payload.get("query", ""),
        "file": payload.get("file", ""),
        "lang": payload.get("lang", ""),
        "category": payload.get("category", ""),
        "rating": payload.get("rating", ""),
        "extra": payload.get("extra", ""),
    }

    with open(log_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if is_new:
            writer.writeheader()
        writer.writerow(row)

    return jsonify({"ok": True})


@app.route("/read/<path:book_name>")
def read_book(book_name):
    book_name = unquote(book_name)
    file_path = os.path.join(BOOKS_FOLDER, book_name)

    if not os.path.exists(file_path):
        return jsonify({"error": "Book not found"})

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    return jsonify({"title": book_name, "content": content})


@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
