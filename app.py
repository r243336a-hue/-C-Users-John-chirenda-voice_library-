"""
Voice Library Application
A Flask-based application for searching and retrieving books via voice commands.

This application provides:
- Voice-activated book search using Google Speech Recognition
- SQLite database integration for book management
- Comprehensive error handling and logging
- Security measures and input validation
- API documentation and structured responses
"""

import logging
import os
import sqlite3
from functools import wraps
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

import speech_recognition as sr
from flask import Flask, render_template, request, jsonify
from werkzeug.exceptions import HTTPException

# ============================================================================
# Configuration and Setup
# ============================================================================

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('voice_library.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configuration
class Config:
    """Application configuration settings."""
    DB_PATH = Path(__file__).parent / "data" / "database" / "library.db"
    MAX_SEARCH_RESULTS = 5
    SPEECH_TIMEOUT = 5
    PHRASE_TIME_LIMIT = 5
    MAX_QUERY_LENGTH = 100
    SUPPORTED_ENCODINGS = ['utf-8', 'latin-1', 'ascii']
    DEBUG = os.getenv('FLASK_DEBUG', 'False') == 'True'
    TESTING = os.getenv('FLASK_TESTING', 'False') == 'True'

app.config.from_object(Config)

# Cache for books - will be populated on startup
BOOKS_CACHE: List[Tuple] = []


# ============================================================================
# Database Functions
# ============================================================================

def get_db_connection() -> sqlite3.Connection:
    """
    Create a database connection.
    
    Returns:
        sqlite3.Connection: Database connection object
        
    Raises:
        sqlite3.OperationalError: If database connection fails
    """
    try:
        conn = sqlite3.connect(str(app.config['DB_PATH']))
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.OperationalError as e:
        logger.error(f"Database connection failed: {e}")
        raise


def load_books() -> List[Tuple]:
    """
    Load all books from the database into cache.
    
    Returns:
        List[Tuple]: List of book tuples (id, title, author, file_path)
        
    Raises:
        sqlite3.OperationalError: If database query fails
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, author, file_path FROM books ORDER BY title")
        books = cursor.fetchall()
        conn.close()
        logger.info(f"Loaded {len(books)} books from database")
        return books
    except sqlite3.OperationalError as e:
        logger.error(f"Failed to load books: {e}")
        return []


def initialize_books_cache() -> None:
    """Initialize the books cache on application startup."""
    global BOOKS_CACHE
    BOOKS_CACHE = load_books()


# ============================================================================
# Search and Filter Functions
# ============================================================================

def search_books(query: str) -> List[Tuple]:
    """
    Search books by title or author.
    
    Args:
        query (str): Search query string
        
    Returns:
        List[Tuple]: List of matching book tuples, limited to MAX_SEARCH_RESULTS
        
    Raises:
        ValueError: If query is invalid or too long
    """
    if not query:
        raise ValueError("Search query cannot be empty")
    
    if len(query) > app.config['MAX_QUERY_LENGTH']:
        raise ValueError(f"Search query exceeds maximum length of {app.config['MAX_QUERY_LENGTH']}")
    
    query_lower = query.lower().strip()
    results = []
    
    for book in BOOKS_CACHE:
        # Search in title (index 1) and author (index 2)
        if query_lower in book[1].lower() or query_lower in book[2].lower():
            results.append(book)
    
    logger.info(f"Search query '{query}' returned {len(results)} results")
    return results[:app.config['MAX_SEARCH_RESULTS']]


def extract_search_query(command: str) -> Optional[str]:
    """
    Extract search query from voice command.
    
    Args:
        command (str): Voice command string
        
    Returns:
        Optional[str]: Extracted query, or None if no valid query found
    """
    cmd_lower = command.lower().strip()
    
    for keyword in ['find', 'search']:
        if keyword in cmd_lower:
            query = cmd_lower.split(keyword, 1)[-1].strip()
            if query:
                return query
    
    return None


# ============================================================================
# Error Handling and Decorators
# ============================================================================

def validate_input(f):
    """
    Decorator to validate request input.
    
    Validates that requests contain necessary data and are of correct type.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"Input validation error: {e}")
            return jsonify({'error': str(e), 'status': 'error'}), 400
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {e}")
            return jsonify({'error': 'Internal server error', 'status': 'error'}), 500
    
    return decorated_function


@app.errorhandler(400)
def bad_request(error):
    """Handle 400 Bad Request errors."""
    return jsonify({'error': 'Bad request', 'status': 'error'}), 400


@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors."""
    return jsonify({'error': 'Resource not found', 'status': 'error'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error', 'status': 'error'}), 500


@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all uncaught exceptions."""
    logger.error(f"Unhandled exception: {error}", exc_info=True)
    
    if isinstance(error, HTTPException):
        return jsonify({'error': error.description, 'status': 'error'}), error.code
    
    return jsonify({'error': 'Internal server error', 'status': 'error'}), 500


# ============================================================================
# Routes
# ============================================================================

@app.route('/')
def index():
    """
    Serve the main application page.
    
    Returns:
        HTML: Rendered index template
    """
    logger.info("Index page accessed")
    return render_template('index.html')


@app.route('/health')
def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        JSON: Health status and book count
    """
    try:
        book_count = len(BOOKS_CACHE)
        return jsonify({
            'status': 'healthy',
            'books_loaded': book_count,
            'database': 'connected' if book_count > 0 else 'empty'
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503


@app.route('/api/books')
def get_all_books():
    """
    Get all available books.
    
    Returns:
        JSON: List of all books with metadata
    """
    try:
        books_data = [
            {
                'id': b[0],
                'title': b[1],
                'author': b[2]
            }
            for b in BOOKS_CACHE
        ]
        
        return jsonify({
            'status': 'success',
            'count': len(books_data),
            'books': books_data
        }), 200
    except Exception as e:
        logger.error(f"Failed to retrieve books: {e}")
        return jsonify({'error': 'Failed to retrieve books', 'status': 'error'}), 500


@app.route('/api/search', methods=['POST'])
def api_search():
    """
    Search books via API endpoint.
    
    Request JSON:
        query (str): Search query string
    
    Returns:
        JSON: Search results with book details
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                'error': 'Missing query parameter',
                'status': 'error'
            }), 400
        
        query = data['query'].strip()
        
        if not query:
            return jsonify({
                'error': 'Search query cannot be empty',
                'status': 'error'
            }), 400
        
        results = search_books(query)
        
        books_data = [
            {
                'id': b[0],
                'title': b[1],
                'author': b[2]
            }
            for b in results
        ]
        
        return jsonify({
            'status': 'success',
            'query': query,
            'count': len(books_data),
            'books': books_data,
            'message': f"Found {len(books_data)} book(s)." if books_data else "No books found."
        }), 200
    
    except ValueError as e:
        logger.warning(f"Search validation error: {e}")
        return jsonify({'error': str(e), 'status': 'error'}), 400
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': 'Search failed', 'status': 'error'}), 500


@app.route('/listen', methods=['POST'])
@validate_input
def listen():
    """
    Listen to voice commands and search for books.
    
    Uses Google Speech Recognition to convert voice to text,
    then processes the command to search for books.
    
    Returns:
        JSON: Search results or error message
    """
    recognizer = sr.Recognizer()
    
    try:
        # Capture audio from microphone
        with sr.Microphone() as source:
            logger.info("Listening for voice command...")
            try:
                audio = recognizer.listen(
                    source,
                    timeout=app.config['SPEECH_TIMEOUT'],
                    phrase_time_limit=app.config['PHRASE_TIME_LIMIT']
                )
            except sr.WaitTimeoutError:
                logger.warning("No speech detected within timeout")
                return jsonify({
                    'error': 'No speech detected. Please try again.',
                    'status': 'error'
                }), 400
        
        # Convert speech to text
        try:
            command = recognizer.recognize_google(audio)
            logger.info(f"Recognized command: {command}")
        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            return jsonify({
                'error': 'Could not understand audio. Please speak clearly.',
                'status': 'error'
            }), 400
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return jsonify({
                'error': 'Speech recognition service unavailable.',
                'status': 'error'
            }), 503
        
        # Extract and validate search query
        query = extract_search_query(command)
        
        if not query:
            return jsonify({
                'message': "Command not recognized. Say 'find' or 'search' followed by a title, author, or genre. "
                          "For example: 'find mystery books'.",
                'status': 'info'
            }), 200
        
        # Search for books
        results = search_books(query)
        
        if results:
            books_data = [
                {
                    'id': b[0],
                    'title': b[1],
                    'author': b[2]
                }
                for b in results
            ]
            return jsonify({
                'message': f"Found {len(results)} book(s).",
                'status': 'success',
                'query': query,
                'books': books_data
            }), 200
        else:
            return jsonify({
                'message': 'No books found. Try a different title, author, or genre.',
                'status': 'info',
                'query': query
            }), 200
    
    except Exception as e:
        logger.error(f"Voice command processing error: {e}")
        return jsonify({
            'error': 'Failed to process voice command',
            'status': 'error'
        }), 500


@app.route('/book_text/<int:book_id>')
@validate_input
def book_text(book_id: int):
    """
    Retrieve the full text of a specific book.
    
    Args:
        book_id (int): The ID of the book to retrieve
    
    Returns:
        JSON: Book text with metadata
        
    Raises:
        404: If book not found
        500: If file cannot be read
    """
    try:
        # Find book in cache
        book = None
        for b in BOOKS_CACHE:
            if b[0] == book_id:
                book = b
                break
        
        if not book:
            logger.warning(f"Book with ID {book_id} not found")
            return jsonify({
                'error': f'Book with ID {book_id} not found',
                'status': 'error'
            }), 404
        
        # Attempt to read file with multiple encodings
        file_path = book[3]
        
        if not os.path.exists(file_path):
            logger.error(f"Book file not found: {file_path}")
            return jsonify({
                'error': 'Book file not found on server',
                'status': 'error'
            }), 404
        
        text = None
        for encoding in app.config['SUPPORTED_ENCODINGS']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    text = f.read()
                logger.info(f"Successfully read book {book_id} with encoding {encoding}")
                break
            except (UnicodeDecodeError, LookupError):
                continue
        
        if text is None:
            logger.error(f"Could not read book file with any supported encoding: {file_path}")
            return jsonify({
                'error': 'Could not read book file - encoding error',
                'status': 'error'
            }), 500
        
        return jsonify({
            'status': 'success',
            'id': book[0],
            'title': book[1],
            'author': book[2],
            'text': text,
            'length': len(text)
        }), 200
    
    except IOError as e:
        logger.error(f"IO error reading book file: {e}")
        return jsonify({
            'error': 'Error reading book file',
            'status': 'error'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error in book_text: {e}")
        return jsonify({
            'error': 'Failed to retrieve book text',
            'status': 'error'
        }), 500


# ============================================================================
# Application Startup and Shutdown
# ============================================================================

@app.before_request
def before_request():
    """Log incoming requests."""
    logger.debug(f"{request.method} {request.path}")


@app.teardown_request
def teardown_request(exception=None):
    """Clean up after request."""
    if exception:
        logger.error(f"Request ended with exception: {exception}")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Initialize and run the application."""
    try:
        logger.info("Starting Voice Library Application...")
        initialize_books_cache()
        
        if not BOOKS_CACHE:
            logger.warning("No books loaded. Check database connection and file paths.")
        
        app.run(
            debug=app.config['DEBUG'],
            host='0.0.0.0',
            port=5000,
            use_reloader=False
        )
    except Exception as e:
        logger.critical(f"Failed to start application: {e}")
        raise


if __name__ == '__main__':
    main()
