"""Deduplication logic for Zorgnieuws articles."""
from difflib import SequenceMatcher
from .base import Article


def title_similarity(title1: str, title2: str) -> float:
    """Calculate similarity between two titles (0.0 to 1.0)."""
    # Normalize titles
    t1 = title1.lower().strip()
    t2 = title2.lower().strip()

    return SequenceMatcher(None, t1, t2).ratio()


def deduplicate_articles(
    articles: list[Article],
    url_exact: bool = True,
    title_threshold: float = 0.85,
) -> list[Article]:
    """
    Remove duplicate articles based on URL and title similarity.

    Args:
        articles: List of articles to deduplicate
        url_exact: Remove exact URL duplicates
        title_threshold: Title similarity threshold (0.85 = 85% similar)

    Returns:
        List of unique articles
    """
    if not articles:
        return []

    unique = []
    seen_urls = set()
    seen_titles = []

    for article in articles:
        # Skip exact URL duplicates
        if url_exact and article.url in seen_urls:
            continue

        # Check title similarity against existing articles
        is_duplicate = False
        for existing_title in seen_titles:
            similarity = title_similarity(article.title, existing_title)
            if similarity >= title_threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            unique.append(article)
            seen_urls.add(article.url)
            seen_titles.append(article.title)

    return unique
