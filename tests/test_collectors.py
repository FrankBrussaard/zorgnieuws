"""Tests for collectors."""
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from collectors.base import Article, BaseCollector
from collectors.rss_collector import RSSCollector
from collectors.tenderned_collector import TenderNedCollector
from collectors.dedup import deduplicate_articles, title_similarity


class TestArticle:
    """Tests for Article dataclass."""

    def test_article_creation(self):
        """Test creating an article."""
        article = Article(
            url="https://example.com/test",
            title="Test Article",
            summary="This is a test summary",
            published=datetime(2025, 3, 3, 8, 0, 0, tzinfo=timezone.utc),
            source_name="Test Source",
            source_type="rss",
            source_url="https://example.com",
        )

        assert article.title == "Test Article"
        assert article.source_type == "rss"
        assert len(article.id) == 16

    def test_article_to_dict(self):
        """Test converting article to dict."""
        article = Article(
            url="https://example.com/test",
            title="Test Article",
            summary="This is a test summary",
            published=datetime(2025, 3, 3, 8, 0, 0, tzinfo=timezone.utc),
            source_name="Test Source",
            source_type="rss",
            source_url="https://example.com",
        )

        data = article.to_dict()

        assert data["id"] is not None
        assert data["url"] == "https://example.com/test"
        assert data["source"]["name"] == "Test Source"
        assert data["source"]["type"] == "rss"

    def test_article_roundtrip(self):
        """Test converting article to dict and back."""
        original = Article(
            url="https://example.com/test",
            title="Test Article",
            summary="This is a test summary",
            published=datetime(2025, 3, 3, 8, 0, 0, tzinfo=timezone.utc),
            source_name="Test Source",
            source_type="rss",
            source_url="https://example.com",
        )

        data = original.to_dict()
        restored = Article.from_dict(data)

        assert restored.url == original.url
        assert restored.title == original.title
        assert restored.source_name == original.source_name


class TestDeduplication:
    """Tests for deduplication logic."""

    def test_title_similarity_exact(self):
        """Test exact title match."""
        assert title_similarity("Test Title", "Test Title") == 1.0

    def test_title_similarity_different(self):
        """Test different titles."""
        similarity = title_similarity("Completely different", "Another title")
        assert similarity < 0.5

    def test_title_similarity_similar(self):
        """Test similar titles."""
        similarity = title_similarity(
            "Chipsoft lanceert nieuwe EPD-module",
            "Chipsoft lanceert nieuwe EPD module"
        )
        assert similarity > 0.85

    def test_deduplicate_by_url(self):
        """Test deduplication by exact URL."""
        articles = [
            Article(
                url="https://example.com/1",
                title="Article 1",
                summary="Summary 1",
                published=datetime.now(timezone.utc),
                source_name="Source",
                source_type="rss",
                source_url="https://example.com",
            ),
            Article(
                url="https://example.com/1",  # Duplicate URL
                title="Article 1 duplicate",
                summary="Summary 1 dup",
                published=datetime.now(timezone.utc),
                source_name="Source",
                source_type="rss",
                source_url="https://example.com",
            ),
        ]

        unique = deduplicate_articles(articles)
        assert len(unique) == 1

    def test_deduplicate_by_title(self):
        """Test deduplication by similar title."""
        articles = [
            Article(
                url="https://example.com/1",
                title="Nieuw ziekenhuis opent in Amsterdam",
                summary="Summary 1",
                published=datetime.now(timezone.utc),
                source_name="Source A",
                source_type="rss",
                source_url="https://source-a.com",
            ),
            Article(
                url="https://example.com/2",  # Different URL
                title="Nieuw ziekenhuis opent in Amsterdam",  # Same title
                summary="Summary 2",
                published=datetime.now(timezone.utc),
                source_name="Source B",
                source_type="rss",
                source_url="https://source-b.com",
            ),
        ]

        unique = deduplicate_articles(articles, title_threshold=0.85)
        assert len(unique) == 1


class TestRSSCollector:
    """Tests for RSS Collector."""

    def test_rss_collector_loads_config(self):
        """Test that RSS collector loads feed config."""
        config_path = project_root / "config" / "feeds.yml"
        if config_path.exists():
            collector = RSSCollector(config_path=str(config_path))
            assert len(collector.feeds) > 0
            assert collector.source_type == "rss"

    def test_rss_collector_collect(self):
        """Test collecting from RSS feeds (integration test)."""
        config_path = project_root / "config" / "feeds.yml"
        if not config_path.exists():
            return

        collector = RSSCollector(config_path=str(config_path))
        articles = collector.collect()

        assert isinstance(articles, list)

        if articles:
            article = articles[0]
            assert article.url is not None
            assert article.title is not None
            assert article.source_type == "rss"


class TestTenderNedCollector:
    """Tests for TenderNed Collector."""

    def test_tenderned_collector_init(self):
        """Test TenderNed collector initialization."""
        collector = TenderNedCollector(days_back=7)
        assert collector.source_type == "api"
        assert collector.days_back == 7

    def test_tenderned_zorg_relevance(self):
        """Test zorg relevance detection."""
        collector = TenderNedCollector()

        # Should match - contains zorg keyword
        tender_zorg = {
            "aanbestedingNaam": "ICT diensten voor ziekenhuis",
            "opdrachtBeschrijving": "Software implementatie",
            "opdrachtgeverNaam": "Test BV",
        }
        assert collector._is_zorg_relevant(tender_zorg) is True

        # Should match - RIVM opdrachtgever
        tender_rivm = {
            "aanbestedingNaam": "Opslag diensten",
            "opdrachtBeschrijving": "Sample storage",
            "opdrachtgeverNaam": "RIVM",
        }
        assert collector._is_zorg_relevant(tender_rivm) is True


def run_quick_test():
    """Run a quick test of the collectors."""
    print("Running quick collector test...")
    print()

    config_path = project_root / "config" / "feeds.yml"
    collector = RSSCollector(config_path=str(config_path))
    articles = collector.collect()

    print()
    print("Sample RSS articles:")
    print("-" * 50)

    for article in articles[:3]:
        print(f"  [{article.source_name}] {article.title[:60]}...")
        print()

    # Test TenderNed
    print()
    print("Testing TenderNed collector...")
    tender_collector = TenderNedCollector(days_back=7)
    tenders = tender_collector.collect()

    print()
    print("Sample tenders:")
    print("-" * 50)

    for tender in tenders[:3]:
        print(f"  {tender.title[:70]}...")
        print(f"    {tender.summary[:80]}...")
        print()

    return articles


if __name__ == "__main__":
    run_quick_test()
