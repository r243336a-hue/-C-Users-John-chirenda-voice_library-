"""
Unit tests for the Voice Library application.

Tests cover:
- Database operations
- Search functionality
- Voice command processing
- Error handling
- API endpoints
"""

import json
import sqlite3
from unittest.mock import patch, MagicMock
import pytest
from app import app, search_books, extract_search_query, BOOKS_CACHE


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_books():
    """Mock book data for testing."""
    return [
        (1, 'The Great Gatsby', 'F. Scott Fitzgerald', '/path/to/gatsby.txt'),
        (2, 'To Kill a Mockingbird', 'Harper Lee', '/path/to/mockingbird.txt'),
        (3, 'Pride and Prejudice', 'Jane Austen', '/path/to/pride.txt'),
        (4, 'The Catcher in the Rye', 'J.D. Salinger', '/path/to/catcher.txt'),
    ]


class TestSearchFunctionality:
    """Test search functionality."""

    def test_search_books_by_title(self, mock_books):
        """Test searching books by title."""
        # Temporarily replace cache
        global BOOKS_CACHE
        original_cache = BOOKS_CACHE.copy()
        BOOKS_CACHE.clear()
        BOOKS_CACHE.extend(mock_books)
        
        results = search_books('gatsby')
        
        assert len(results) == 1
        assert results[0][1] == 'The Great Gatsby'
        
        # Restore original cache
        BOOKS_CACHE.clear()
        BOOKS_CACHE.extend(original_cache)

    def test_search_books_by_author(self, mock_books):
        """Test searching books by author."""
        global BOOKS_CACHE
        original_cache = BOOKS_CACHE.copy()
        BOOKS_CACHE.clear()
        BOOKS_CACHE.extend(mock_books)
        
        results = search_books('austen')
        
        assert len(results) == 1
        assert results[0][2] == 'Jane Austen'
        
        BOOKS_CACHE.clear()
        BOOKS_CACHE.extend(original_cache)

    def test_search_books_empty_query(self):
        """Test search with empty query raises ValueError."""
        with pytest.raises(ValueError, match='Search query cannot be empty'):
            search_books('')

    def test_search_books_query_too_long(self):
        """Test search with query exceeding max length raises ValueError."""
        long_query = 'a' * 101
        with pytest.raises(ValueError, match='exceeds maximum length'):
            search_books(long_query)

    def test_search_books_no_results(self, mock_books):
        """Test search with no matching results."""
        global BOOKS_CACHE
        original_cache = BOOKS_CACHE.copy()
        BOOKS_CACHE.clear()
        BOOKS_CACHE.extend(mock_books)
        
        results = search_books('nonexistent')
        
        assert len(results) == 0
        
        BOOKS_CACHE.clear()
        BOOKS_CACHE.extend(original_cache)

    def test_search_books_max_results(self, mock_books):
        """Test search returns max results."""
        global BOOKS_CACHE
        original_cache = BOOKS_CACHE.copy()
        BOOKS_CACHE.clear()
        # Add many books with similar titles
        for i in range(10):
            BOOKS_CACHE.append((i, f'Book {i}', 'Author', '/path/to/book.txt'))
        
        results = search_books('book')
        
        assert len(results) <= app.config['MAX_SEARCH_RESULTS']
        
        BOOKS_CACHE.clear()
        BOOKS_CACHE.extend(original_cache)


class TestVoiceCommandProcessing:
    """Test voice command processing."""

    def test_extract_find_query(self):
        """Test extracting query from find command."""
        command = 'find the great gatsby'
        query = extract_search_query(command)
        
        assert query == 'the great gatsby'

    def test_extract_search_query(self):
        """Test extracting query from search command."""
        command = 'search for pride and prejudice'
        query = extract_search_query(command)
        
        assert query == 'for pride and prejudice'

    def test_extract_query_case_insensitive(self):
        """Test query extraction is case insensitive."""
        command = 'FIND The Great Gatsby'
        query = extract_search_query(command)
        
        assert query == 'The Great Gatsby'

    def test_extract_query_no_keyword(self):
        """Test extraction returns None when no keyword found."""
        command = 'tell me a story'
        query = extract_search_query(command)
        
        assert query is None

    def test_extract_query_keyword_only(self):
        """Test extraction returns None when only keyword present."""
        command = 'find'
        query = extract_search_query(command)
        
        assert query is None


class TestAPIEndpoints:
    """Test API endpoints."""

    def test_index_page(self, client):
        """Test index page returns 200."""
        response = client.get('/')
        assert response.status_code == 200

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/health')
        assert response.status_code in [200, 503]
        data = json.loads(response.data)
        assert 'status' in data

    def test_get_all_books(self, client, mock_books):
        """Test get all books endpoint."""
        global BOOKS_CACHE
        original_cache = BOOKS_CACHE.copy()
        BOOKS_CACHE.clear()
        BOOKS_CACHE.extend(mock_books)
        
        response = client.get('/api/books')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['count'] == len(mock_books)
        assert 'books' in data
        
        BOOKS_CACHE.clear()
        BOOKS_CACHE.extend(original_cache)

    def test_api_search_success(self, client, mock_books):
        """Test API search endpoint with valid query."""
        global BOOKS_CACHE
        original_cache = BOOKS_CACHE.copy()
        BOOKS_CACHE.clear()
        BOOKS_CACHE.extend(mock_books)
        
        response = client.post('/api/search',
                             data=json.dumps({'query': 'gatsby'}),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert len(data['books']) > 0
        
        BOOKS_CACHE.clear()
        BOOKS_CACHE.extend(original_cache)

    def test_api_search_missing_query(self, client):
        """Test API search endpoint without query parameter."""
        response = client.post('/api/search',
                             data=json.dumps({}),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'

    def test_api_search_empty_query(self, client):
        """Test API search endpoint with empty query."""
        response = client.post('/api/search',
                             data=json.dumps({'query': ''}),
                             content_type='application/json')
        
        assert response.status_code == 400

    def test_book_text_not_found(self, client):
        """Test book text endpoint with non-existent book."""
        response = client.get('/book_text/99999')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'


class TestErrorHandling:
    """Test error handling."""

    def test_404_error(self, client):
        """Test 404 error handling."""
        response = client.get('/nonexistent')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'

    @patch('app.sr.Recognizer')
    def test_listen_no_speech_detected(self, mock_recognizer, client):
        """Test voice endpoint when no speech is detected."""
        mock_instance = MagicMock()
        mock_recognizer.return_value = mock_instance
        mock_instance.listen.side_effect = Exception('WaitTimeoutError')
        
        # This test would need proper mocking of speech recognition
        # Response depends on implementation


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
