"""Tests for scorer module."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scorer.fallback_scorer import FallbackScorer


class TestFallbackScorer:
    """Tests for FallbackScorer - Accenture focus."""

    def test_scorer_initialization(self):
        """Test scorer can be initialized."""
        scorer = FallbackScorer()
        assert scorer is not None

    def test_score_cloud_transformation_article(self):
        """Test scoring a cloud transformation article (high relevance for Accenture)."""
        scorer = FallbackScorer()

        article = {
            "id": "test_cloud",
            "title": "UMC Utrecht start cloud transformatie programma",
            "summary": "Het ziekenhuis migreert naar Azure met focus op digitale transformatie.",
            "source": {"name": "Skipr", "type": "rss", "url": "https://skipr.nl"},
        }

        scored = scorer.score_article(article)

        assert scored["score"]["relevance"] >= 30  # Cloud + transformatie = high relevance
        assert "Cloud" in scored["tags"] or "Transformatie" in scored["tags"]

    def test_score_ai_article(self):
        """Test scoring an AI article."""
        scorer = FallbackScorer()

        article = {
            "id": "test_ai",
            "title": "Generative AI in de zorg: kansen en risico's",
            "summary": "Machine learning en ChatGPT worden steeds vaker ingezet in ziekenhuizen.",
            "source": {"name": "ICT&health", "type": "rss", "url": "https://icthealth.nl"},
        }

        scored = scorer.score_article(article)

        assert scored["score"]["relevance"] >= 35  # AI = very high relevance
        assert "AI" in scored["tags"]

    def test_score_epd_article(self):
        """Test scoring an EPD-related article."""
        scorer = FallbackScorer()

        article = {
            "id": "test123",
            "title": "Chipsoft lanceert nieuwe HiX EPD module",
            "summary": "De nieuwe module verbetert de interoperabiliteit met FHIR.",
            "source": {"name": "Skipr", "type": "rss", "url": "https://skipr.nl"},
        }

        scored = scorer.score_article(article)

        assert scored["score"]["relevance"] >= 25  # EPD, HiX, FHIR keywords
        assert scored["category"] == "concurrent"  # Chipsoft = concurrent
        assert "EPD" in scored["tags"]

    def test_score_tender_article(self):
        """Test scoring a tender article."""
        scorer = FallbackScorer()

        article = {
            "id": "test456",
            "title": "TENDER: ICT diensten voor ziekenhuis",
            "summary": "Aanbesteding voor EPD implementatie.",
            "source": {"name": "TenderNed", "type": "api", "url": "https://tenderned.nl"},
        }

        scored = scorer.score_article(article)

        assert scored["score"]["urgency"] >= 20  # Tender keyword
        assert scored["score"]["action_potential"] >= 20  # Tender = opportunity
        assert scored["category"] == "opportunity"  # Changed from "tender" to "opportunity"

    def test_score_general_article(self):
        """Test scoring a general healthcare article."""
        scorer = FallbackScorer()

        article = {
            "id": "test789",
            "title": "Wachtlijsten in de zorg lopen op",
            "summary": "Steeds meer patiënten moeten langer wachten.",
            "source": {"name": "NOS", "type": "rss", "url": "https://nos.nl"},
        }

        scored = scorer.score_article(article)

        assert scored["score"]["total"] < 40  # General news, low relevance
        assert scored["priority"] == "low"

    def test_score_irrelevant_tender(self):
        """Test that irrelevant tenders (cleaning, etc.) get score 0."""
        scorer = FallbackScorer()

        article = {
            "id": "test_irrelevant",
            "title": "TENDER: Schoonmaakdiensten ziekenhuis",
            "summary": "Aanbesteding voor schoonmaak en catering faciliteiten.",
            "source": {"name": "TenderNed", "type": "api", "url": "https://tenderned.nl"},
        }

        scored = scorer.score_article(article)

        assert scored["score"]["total"] == 0  # Schoonmaak = not relevant
        assert scored["category"] == "niet-relevant"
        assert scored["priority"] == "low"

    def test_score_batch(self):
        """Test scoring multiple articles."""
        scorer = FallbackScorer()

        articles = [
            {
                "id": "1",
                "title": "HiX EPD update",
                "summary": "Chipsoft release",
                "source": {"name": "Test", "type": "rss", "url": "https://test.nl"},
            },
            {
                "id": "2",
                "title": "Algemeen zorgnieuws",
                "summary": "Geen IT",
                "source": {"name": "Test", "type": "rss", "url": "https://test.nl"},
            },
        ]

        scored = scorer.score(articles)

        assert len(scored) == 2
        assert all("score" in a for a in scored)
        assert all("priority" in a for a in scored)

    def test_category_detection(self):
        """Test category detection - Accenture categories."""
        scorer = FallbackScorer()

        # Opportunity
        assert scorer._detect_category("tender voor ict") == "opportunity"
        assert scorer._detect_category("aanbesteding software") == "opportunity"

        # Concurrent
        assert scorer._detect_category("chipsoft lanceert") == "concurrent"
        assert scorer._detect_category("deloitte rapport") == "concurrent"

        # Overheid
        assert scorer._detect_category("rijksoverheid besluit") == "overheid"
        assert scorer._detect_category("vws kamerbrief") == "overheid"

        # Klant
        assert scorer._detect_category("umc utrecht transformatie") == "klant"
        assert scorer._detect_category("ggz instelling") == "klant"

        # Niet-relevant (no match)
        assert scorer._detect_category("algemeen nieuws") == "niet-relevant"

    def test_priority_levels(self):
        """Test priority level assignment."""
        scorer = FallbackScorer()

        # Simulate different score levels
        articles = [
            {"id": "1", "title": "TENDER: EPD HiX implementatie cybersecurity",
             "summary": "Aanbesteding deadline ICT zorg", "source": {"name": "T"}},
            {"id": "2", "title": "Nieuw ziekenhuis", "summary": "Opens", "source": {"name": "T"}},
        ]

        scored = scorer.score(articles)

        # First should be high/critical, second should be low
        assert scored[0]["priority"] in ["critical", "high"]
        assert scored[1]["priority"] == "low"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
