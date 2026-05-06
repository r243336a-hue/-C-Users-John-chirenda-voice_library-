import sqlite3
import os
import re
import difflib

def _resolve_db_path():
    # Prefer explicit override if provided
    override = os.environ.get("VOICE_LIBRARY_DB")
    if override and os.path.exists(override):
        return override

    candidates = []

    # Repo root relative to this file
    file_root = os.path.dirname(os.path.dirname(__file__))
    candidates.append(os.path.join(file_root, "data", "database", "library.db"))

    # Working-directory based fallbacks
    cwd = os.getcwd()
    candidates.append(os.path.join(cwd, "data", "database", "library.db"))
    candidates.append(os.path.join(os.path.dirname(cwd), "data", "database", "library.db"))

    # Walk up a few levels to find a repo root that contains data/database/library.db
    probe = os.path.abspath(os.path.dirname(__file__))
    for _ in range(6):
        candidates.append(os.path.join(probe, "data", "database", "library.db"))
        probe = os.path.dirname(probe)

    for path in candidates:
        if os.path.exists(path):
            return path

    # Default to file-relative path even if missing (for clearer errors)
    return candidates[0]


DB_PATH = _resolve_db_path()


def _resolve_books_path():
    override = os.environ.get("VOICE_LIBRARY_BOOKS")
    candidates = []
    if override:
        candidates.append(override)
    file_root = os.path.dirname(os.path.dirname(__file__))
    candidates.append(os.path.join(file_root, "books"))
    candidates.append(os.path.join(file_root, "data", "cleaned"))
    candidates.append(os.path.join(file_root, "data", "raw"))
    cwd = os.getcwd()
    candidates.append(os.path.join(cwd, "books"))
    candidates.append(os.path.join(os.path.dirname(cwd), "books"))
    candidates.append(os.path.join(os.path.dirname(cwd), "data", "cleaned"))
    candidates.append(os.path.join(os.path.dirname(cwd), "data", "raw"))

    for path in candidates:
        if os.path.exists(path):
            return path

    return None


def get_db_connection():
    """Get database connection."""
    global DB_PATH
    if not os.path.exists(DB_PATH):
        DB_PATH = _resolve_db_path()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def search_books(query='', limit=50, threshold=0.75):
    """
    Search books by title or author with fuzzy matching and keyword fallback.

    Args:
        query (str): Search query string
        limit (int): Maximum number of results to return
        threshold (float): Fuzzy similarity threshold (0-1)

    Returns:
        list: List of book dictionaries matching the search
    """
    query = (query or '').strip().lower()

    if not query:
        conn = get_db_connection()
        books = conn.execute('SELECT * FROM books ORDER BY author LIMIT ?', (limit,)).fetchall()
        conn.close()
        return [dict(book) for book in books]

    # Preprocess query for fuzzy and SQL keyword matching
    cleaned_query = re.sub(r"[^\w\s]", "", query)

    # Load all books for fuzzy title/author matching
    conn = get_db_connection()
    all_books = conn.execute('SELECT * FROM books').fetchall()

    titles = [book['title'].lower() for book in all_books]
    authors = [book['author'].lower() for book in all_books]

    title_match = difflib.get_close_matches(cleaned_query, titles, n=1, cutoff=threshold)
    if title_match:
        matched_title = title_match[0]
        conn.close()
        return [dict(book) for book in all_books if book['title'].lower() == matched_title][:limit]

    author_match = difflib.get_close_matches(cleaned_query, authors, n=1, cutoff=threshold)
    if author_match:
        matched_author = author_match[0]
        conn.close()
        return [dict(book) for book in all_books if book['author'].lower() == matched_author][:limit]

    # Keyword fallback: title/author/subject_tags
    search_term = f"%{cleaned_query}%"
    keyword_results = conn.execute('''
        SELECT * FROM books
        WHERE title LIKE ? OR author LIKE ? OR IFNULL(subject_tags, '') LIKE ?
        ORDER BY word_count DESC
        LIMIT ?
    ''', (search_term, search_term, search_term, limit)).fetchall()

    conn.close()
    return [dict(book) for book in keyword_results]


def get_book_by_id(book_id):
    """
    Get a specific book by ID.

    Args:
        book_id (int): Book ID to retrieve

    Returns:
        dict or None: Book data dictionary or None if not found
    """
    conn = get_db_connection()
    book = conn.execute('SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()
    conn.close()

    if book:
        return dict(book)
    return None


def get_book_content(book_id_or_name):
    """
    Get the full text content of a book.

    Args:
        book_id_or_name (int | str): Book ID or filename to retrieve content for

    Returns:
        str or None: Book content or None if not found
    """
    file_path = None
    if isinstance(book_id_or_name, str) and book_id_or_name.lower().endswith(".txt"):
        file_path = book_id_or_name
        if not os.path.isabs(file_path):
            books_root = _resolve_books_path()
            if books_root:
                file_path = os.path.join(books_root, file_path)
    else:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM books WHERE id = ?", (book_id_or_name,))
        row = cursor.fetchone()
        conn.close()
        if not row or not row[0]:
            return None
        file_path = row[0]
    if not os.path.isabs(file_path):
        books_root = _resolve_books_path()
        if books_root:
            file_path = os.path.join(books_root, file_path)

    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading book content: {e}")
            return None

    return None


def get_books_by_author(author_name, limit=20):
    """
    Get all books by a specific author.

    Args:
        author_name (str): Author name to search for
        limit (int): Maximum number of results

    Returns:
        list: List of books by the author
    """
    conn = get_db_connection()
    books = conn.execute('''
        SELECT * FROM books
        WHERE author LIKE ?
        ORDER BY title
        LIMIT ?
    ''', (f"%{author_name}%", limit)).fetchall()
    conn.close()
    return [dict(book) for book in books]


def get_random_books(count=5):
    """
    Get random books from the library.

    Args:
        count (int): Number of random books to return

    Returns:
        list: List of random books
    """
    conn = get_db_connection()
    books = conn.execute('''
        SELECT * FROM books
        ORDER BY RANDOM()
        LIMIT ?
    ''', (count,)).fetchall()
    conn.close()
    return [dict(book) for book in books]


def get_library_stats():
    """
    Get statistics about the library.

    Returns:
        dict: Library statistics
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total books
    cursor.execute('SELECT COUNT(*) FROM books')
    total_books = cursor.fetchone()[0]

    # Total authors
    cursor.execute('SELECT COUNT(DISTINCT author) FROM books')
    total_authors = cursor.fetchone()[0]

    # Total words
    cursor.execute('SELECT SUM(word_count) FROM books')
    total_words = cursor.fetchone()[0] or 0

    # Total file size
    cursor.execute('SELECT SUM(file_size_bytes) FROM books')
    total_size = cursor.fetchone()[0] or 0

    conn.close()

    return {
        'total_books': total_books,
        'total_authors': total_authors,
        'total_words': total_words,
        'total_size_mb': round(total_size / (1024 * 1024), 2)
    }


def fuzzy_search(query, threshold=0.6):
    """
    Perform fuzzy search on books.

    Args:
        query (str): Search query
        threshold (float): Similarity threshold (0-1)

    Returns:
        list: List of books with similarity scores
    """
    import difflib

    all_books = search_books('', limit=1000)  # Get all books
    results = []

    query_lower = query.lower()
    for book in all_books:
        title_similarity = difflib.SequenceMatcher(None, query_lower, book['title'].lower()).ratio()
        author_similarity = difflib.SequenceMatcher(None, query_lower, book['author'].lower()).ratio()

        max_similarity = max(title_similarity, author_similarity)

        if max_similarity >= threshold:
            book_with_score = dict(book)
            book_with_score['similarity'] = max_similarity
            results.append(book_with_score)

    # Sort by similarity score
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:20]  # Return top 20 matches


def search(query='', limit=50):
    """Alias for search_books to match existing API usage."""
    return search_books(query, limit)


def load_books(limit=200):
    """
    Load a basic list of books for simple listings.

    Returns:
        list: List of (id, title, author) tuples.
    """
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, title, author FROM books ORDER BY title LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [(row["id"], row["title"], row["author"]) for row in rows]


# Example usage
if __name__ == '__main__':
    # Test the search functions
    print("Library Statistics:")
    stats = get_library_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\nSample Search Results:")
    results = search_books("author")
    for book in results[:3]:
        print(f"  {book['title']} by {book['author']}")

    print("\nRandom Books:")
    random_books = get_random_books(2)
    for book in random_books:
        print(f"  {book['title']} by {book['author']}")
