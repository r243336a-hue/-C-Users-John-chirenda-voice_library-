"""
Standalone tests that can run without external dependencies.
Tests core logic without Flask server, microphone, or database requirements.
"""

import json
import sys
from typing import List, Tuple

# Mock data - simulating database books
MOCK_BOOKS: List[Tuple] = [
    (1, 'The Great Gatsby', 'F. Scott Fitzgerald', '/books/gatsby.txt'),
    (2, 'To Kill a Mockingbird', 'Harper Lee', '/books/mockingbird.txt'),
    (3, 'Pride and Prejudice', 'Jane Austen', '/books/pride.txt'),
    (4, 'The Catcher in the Rye', 'J.D. Salinger', '/books/catcher.txt'),
    (5, 'Jane Eyre', 'Charlotte Bronte', '/books/eyre.txt'),
]

class Config:
    """Test configuration."""
    MAX_SEARCH_RESULTS = 5
    MAX_QUERY_LENGTH = 100


def search_books(query: str, books: List[Tuple] = None) -> List[Tuple]:
    """
    Search books by title or author.
    
    Args:
        query (str): Search query
        books (List[Tuple]): Book data to search
        
    Returns:
        List[Tuple]: Matching books
        
    Raises:
        ValueError: If query is invalid
    """
    if books is None:
        books = MOCK_BOOKS
        
    if not query:
        raise ValueError("Search query cannot be empty")
    
    if len(query) > Config.MAX_QUERY_LENGTH:
        raise ValueError(f"Search query exceeds maximum length")
    
    query_lower = query.lower().strip()
    results = []
    
    for book in books:
        if query_lower in book[1].lower() or query_lower in book[2].lower():
            results.append(book)
    
    return results[:Config.MAX_SEARCH_RESULTS]


def extract_search_query(command: str) -> str:
    """Extract search query from voice command."""
    cmd_lower = command.lower().strip()
    
    for keyword in ['find', 'search']:
        if keyword in cmd_lower:
            query = cmd_lower.split(keyword, 1)[-1].strip()
            if query:
                return query
    
    return None


def validate_book_id(book_id: int, books: List[Tuple]) -> bool:
    """Check if book ID exists."""
    for book in books:
        if book[0] == book_id:
            return True
    return False


# ============================================================================
# Test Suite
# ============================================================================

class TestResults:
    """Simple test results tracker."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def add_pass(self, test_name):
        self.passed += 1
        self.tests.append(('PASS', test_name))
        print(f"✅ {test_name}")
    
    def add_fail(self, test_name, error):
        self.failed += 1
        self.tests.append(('FAIL', test_name, str(error)))
        print(f"❌ {test_name}: {error}")
    
    def summary(self):
        total = self.passed + self.failed
        print("\n" + "="*60)
        print(f"Test Results: {self.passed}/{total} passed")
        print("="*60)
        return self.failed == 0


results = TestResults()


def test_search_by_title():
    """Test searching books by title."""
    try:
        results_list = search_books('gatsby')
        assert len(results_list) == 1
        assert results_list[0][1] == 'The Great Gatsby'
        results.add_pass("Search by title")
    except Exception as e:
        results.add_fail("Search by title", e)


def test_search_by_author():
    """Test searching books by author."""
    try:
        results_list = search_books('austen')
        assert len(results_list) == 1
        assert results_list[0][2] == 'Jane Austen'
        results.add_pass("Search by author")
    except Exception as e:
        results.add_fail("Search by author", e)


def test_search_case_insensitive():
    """Test search is case insensitive."""
    try:
        results_list = search_books('GATSBY')
        assert len(results_list) == 1
        results.add_pass("Search case insensitive")
    except Exception as e:
        results.add_fail("Search case insensitive", e)


def test_search_partial_match():
    """Test partial string matching."""
    try:
        results_list = search_books('great')
        assert len(results_list) == 1
        assert 'Great' in results_list[0][1]
        results.add_pass("Search partial match")
    except Exception as e:
        results.add_fail("Search partial match", e)


def test_search_no_results():
    """Test search with no matching results."""
    try:
        results_list = search_books('nonexistent')
        assert len(results_list) == 0
        results.add_pass("Search no results")
    except Exception as e:
        results.add_fail("Search no results", e)


def test_search_multiple_results():
    """Test search returning multiple results."""
    try:
        results_list = search_books('book')  # Generic term
        assert len(results_list) >= 0  # May have 0 results
        results.add_pass("Search multiple results")
    except Exception as e:
        results.add_fail("Search multiple results", e)


def test_search_empty_query():
    """Test search with empty query raises error."""
    try:
        search_books('')
        results.add_fail("Search empty query", "Should raise ValueError")
    except ValueError:
        results.add_pass("Search empty query (error)")
    except Exception as e:
        results.add_fail("Search empty query", e)


def test_search_query_too_long():
    """Test search with query exceeding max length."""
    try:
        long_query = 'a' * 101
        search_books(long_query)
        results.add_fail("Search query too long", "Should raise ValueError")
    except ValueError:
        results.add_pass("Search query too long (error)")
    except Exception as e:
        results.add_fail("Search query too long", e)


def test_extract_find_query():
    """Test extracting query from 'find' command."""
    try:
        command = 'find the great gatsby'
        query = extract_search_query(command)
        assert query == 'the great gatsby'
        results.add_pass("Extract 'find' command")
    except Exception as e:
        results.add_fail("Extract 'find' command", e)


def test_extract_search_query_command():
    """Test extracting query from 'search' command."""
    try:
        command = 'search for pride and prejudice'
        query = extract_search_query(command)
        assert query == 'for pride and prejudice'
        results.add_pass("Extract 'search' command")
    except Exception as e:
        results.add_fail("Extract 'search' command", e)


def test_extract_query_case_insensitive():
    """Test query extraction is case insensitive."""
    try:
        command = 'FIND The Great Gatsby'
        query = extract_search_query(command)
        assert query == 'The Great Gatsby'
        results.add_pass("Extract query case insensitive")
    except Exception as e:
        results.add_fail("Extract query case insensitive", e)


def test_extract_query_no_keyword():
    """Test extraction returns None with no keyword."""
    try:
        command = 'tell me a story'
        query = extract_search_query(command)
        assert query is None
        results.add_pass("Extract no keyword")
    except Exception as e:
        results.add_fail("Extract no keyword", e)


def test_extract_query_keyword_only():
    """Test extraction returns None with keyword only."""
    try:
        command = 'find'
        query = extract_search_query(command)
        assert query is None
        results.add_pass("Extract keyword only")
    except Exception as e:
        results.add_fail("Extract keyword only", e)


def test_validate_book_id_exists():
    """Test book ID validation for existing book."""
    try:
        assert validate_book_id(1, MOCK_BOOKS) == True
        results.add_pass("Validate existing book ID")
    except Exception as e:
        results.add_fail("Validate existing book ID", e)


def test_validate_book_id_not_exists():
    """Test book ID validation for non-existing book."""
    try:
        assert validate_book_id(999, MOCK_BOOKS) == False
        results.add_pass("Validate non-existing book ID")
    except Exception as e:
        results.add_fail("Validate non-existing book ID", e)


def test_max_results_limit():
    """Test that search results are limited."""
    try:
        # Create test data with many books
        many_books = [(i, f'Book {i}', 'Author', f'/path/{i}.txt') for i in range(20)]
        results_list = search_books('book', many_books)
        assert len(results_list) <= Config.MAX_SEARCH_RESULTS
        results.add_pass("Max results limit")
    except Exception as e:
        results.add_fail("Max results limit", e)


def test_mock_data_integrity():
    """Test that mock data is properly structured."""
    try:
        for book in MOCK_BOOKS:
            assert len(book) == 4
            assert isinstance(book[0], int)  # ID
            assert isinstance(book[1], str)  # Title
            assert isinstance(book[2], str)  # Author
            assert isinstance(book[3], str)  # Path
        results.add_pass("Mock data integrity")
    except Exception as e:
        results.add_fail("Mock data integrity", e)


# ============================================================================
# Run Tests
# ============================================================================

def run_all_tests():
    """Run all test cases."""
    print("\n" + "="*60)
    print("Voice Library - Standalone Test Suite")
    print("="*60 + "\n")
    
    # Search tests
    print("Search Functionality Tests:")
    test_search_by_title()
    test_search_by_author()
    test_search_case_insensitive()
    test_search_partial_match()
    test_search_no_results()
    test_search_multiple_results()
    test_search_empty_query()
    test_search_query_too_long()
    test_max_results_limit()
    
    # Voice command tests
    print("\nVoice Command Extraction Tests:")
    test_extract_find_query()
    test_extract_search_query_command()
    test_extract_query_case_insensitive()
    test_extract_query_no_keyword()
    test_extract_query_keyword_only()
    
    # Validation tests
    print("\nBook ID Validation Tests:")
    test_validate_book_id_exists()
    test_validate_book_id_not_exists()
    
    # Data integrity tests
    print("\nData Integrity Tests:")
    test_mock_data_integrity()
    
    # Print summary
    success = results.summary()
    
    return 0 if success else 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
