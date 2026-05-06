# Voice Library Application

A modern Flask-based application for searching and retrieving books using voice commands and text-based APIs.

## Features

- **Voice Search**: Use Google Speech Recognition to search for books by voice
- **Text Search**: Standard text-based search via API
- **Book Management**: SQLite database for storing book metadata and file paths
- **Error Handling**: Comprehensive error handling with detailed logging
- **Security**: Input validation, error hiding, and safe file operations
- **Performance**: In-memory caching of book catalog for fast searches
- **Testing**: Full test suite with pytest
- **Documentation**: Inline code documentation and API reference

## Quick Start

### Installation

1. Clone the repository
```bash
git clone <repository-url>
cd voice_library
```

2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure environment variables
```bash
cp .env.example .env
# Edit .env with your settings
```

5. Run the application
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## API Documentation

### Health Check
**GET** `/health`

Check application status and database connection.

**Response:**
```json
{
  "status": "healthy",
  "books_loaded": 42,
  "database": "connected"
}
```

### Get All Books
**GET** `/api/books`

Retrieve all available books.

**Response:**
```json
{
  "status": "success",
  "count": 3,
  "books": [
    {
      "id": 1,
      "title": "The Great Gatsby",
      "author": "F. Scott Fitzgerald"
    }
  ]
}
```

### Search Books (API)
**POST** `/api/search`

Search for books by title or author.

**Request Body:**
```json
{
  "query": "gatsby"
}
```

**Response:**
```json
{
  "status": "success",
  "query": "gatsby",
  "count": 1,
  "books": [
    {
      "id": 1,
      "title": "The Great Gatsby",
      "author": "F. Scott Fitzgerald"
    }
  ],
  "message": "Found 1 book(s)."
}
```

### Voice Search
**POST** `/listen`

Listens for voice commands and searches for books. Requires microphone access.

**Voice Command Examples:**
- "Find The Great Gatsby"
- "Search for mystery books"
- "Find books by Austen"

**Response:**
```json
{
  "message": "Found 2 book(s).",
  "status": "success",
  "query": "mystery books",
  "books": []
}
```

### Get Book Text
**GET** `/book_text/<book_id>`

Retrieve the full text content of a specific book.

**Response:**
```json
{
  "status": "success",
  "id": 1,
  "title": "The Great Gatsby",
  "author": "F. Scott Fitzgerald",
  "text": "The full book text...",
  "length": 47094
}
```

## Testing

Run the test suite:
```bash
pytest test_app.py -v
```

Run tests with coverage:
```bash
pytest test_app.py --cov=app --cov-report=html
```

## Code Quality

Format code with black:
```bash
black app.py test_app.py
```

Check code quality with flake8:
```bash
flake8 app.py test_app.py
```

Type checking with mypy:
```bash
mypy app.py
```

## Logging

Logs are written to `voice_library.log` and also printed to console.

Log levels:
- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for potentially problematic situations
- **ERROR**: Error messages for serious issues
- **CRITICAL**: Critical messages for system failures

## Configuration

Application configuration is managed through `config.py` and environment variables.

### Environment Variables
- `FLASK_ENV`: Set to `development`, `testing`, or `production`
- `FLASK_DEBUG`: Enable/disable debug mode
- `SECRET_KEY`: Secret key for session management
- `DB_PATH`: Path to SQLite database
- `LOG_LEVEL`: Logging level

## Database Schema

The application expects a SQLite database with a `books` table:

```sql
CREATE TABLE books (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    file_path TEXT NOT NULL
);
```

## File Encoding Support

The application supports multiple file encodings:
- UTF-8 (default)
- Latin-1
- ASCII

The system automatically detects and uses the appropriate encoding when reading book files.

## Error Handling

The application includes comprehensive error handling:
- Input validation for all user inputs
- Safe database operations with proper error reporting
- Graceful degradation when services are unavailable
- Detailed logging of all errors for debugging

## Performance Optimizations

- In-memory caching of book catalog
- Efficient search algorithm with early termination
- Result limiting to prevent large responses
- Optimized database queries

## Security Measures

- Input validation and sanitization
- SQL injection prevention through parameterized queries
- Error message hiding in production
- File path validation
- Maximum request size limits

## Troubleshooting

### No microphone detected
Ensure PyAudio is properly installed:
```bash
pip install --upgrade PyAudio
```

### Database errors
Check that the database file exists at the configured path and is readable:
```bash
ls -la data/database/library.db
```

### Speech recognition not working
Verify internet connection (Google Speech Recognition requires internet):
```bash
curl https://www.google.com
```

### File encoding errors
The application will automatically try multiple encodings. If a file still fails, ensure it's saved in a supported encoding (UTF-8 recommended).

## Development

Contribution guidelines:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues or questions, please create an issue in the repository.
