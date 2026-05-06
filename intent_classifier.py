"""
Rule-based intent classification with fuzzy matching for books.
"""

import difflib
from .config import INTENT_KEYWORDS, FUZZY_THRESHOLD
from .db_utils import get_all_books

_all_books = None
_titles_and_authors = []


def _load_books():
    global _all_books, _titles_and_authors
    if _all_books is None:
        _all_books = get_all_books()
        for book in _all_books:
            _titles_and_authors.append(book["title"].lower())
            _titles_and_authors.append(f"{book['title']} by {book['author']}".lower())
            if book["author"]:
                _titles_and_authors.append(book["author"].lower())


def classify_intent(transcript):
    """
    Determine intent from transcript.
    Returns (intent, data) where data varies per intent.
    """
    _load_books()
    transcript_lower = transcript.lower()

    if any(kw in transcript_lower for kw in INTENT_KEYWORDS["HELP"]):
        return "HELP", None
    if any(kw in transcript_lower for kw in INTENT_KEYWORDS["STOP"]):
        return "STOP", None
    if any(kw in transcript_lower for kw in INTENT_KEYWORDS["PAUSE"]):
        return "PAUSE", None
    if any(kw in transcript_lower for kw in INTENT_KEYWORDS["RESUME"]):
        return "RESUME", None

    has_play = any(kw in transcript_lower for kw in INTENT_KEYWORDS["PLAY"])
    has_search = any(kw in transcript_lower for kw in INTENT_KEYWORDS["SEARCH"])

    book_match = None
    matches = difflib.get_close_matches(transcript_lower, _titles_and_authors, n=1, cutoff=FUZZY_THRESHOLD)
    if matches:
        matched_str = matches[0]
        for book in _all_books:
            if book["title"].lower() == matched_str or book["author"].lower() == matched_str:
                book_match = book
                break
            if f"{book['title']} by {book['author']}".lower() == matched_str:
                book_match = book
                break
        if not book_match:
            for book in _all_books:
                if book["title"].lower() == matched_str:
                    book_match = book
                    break
    else:
        for book in _all_books:
            if book["title"].lower() in transcript_lower or (
                book["author"] and book["author"].lower() in transcript_lower
            ):
                book_match = book
                break

    if book_match:
        if has_play or has_search:
            return "PLAY", book_match
        return "PLAY", book_match

    if has_search:
        return "SEARCH", transcript_lower

    return "SEARCH", transcript_lower
