"""Fallback keyword-based scorer for Zorgnieuws articles - Accenture focus."""
import re
from typing import Optional


class FallbackScorer:
    """Score articles using keyword matching when Claude API is unavailable.

    Optimized for Accenture Nederland Healthcare practice focus:
    - Digitale transformatie
    - Cloud, Data, AI
    - Strategische opportunities
    """

    # Keywords with relevance weights - Accenture focus
    RELEVANCE_KEYWORDS = {
        # High relevance (30-40) - direct strategische focus
        "digitale transformatie": 38, "digital transformation": 38,
        "cloud migratie": 36, "cloud transformatie": 38, "cloud": 32, "azure": 34, "aws": 34,
        "data platform": 36, "data governance": 35, "analytics": 32,
        "artificial intelligence": 38, "machine learning": 35, "generative ai": 40,
        "ai zorg": 38, "chatgpt": 35, "llm": 35,
        "cybersecurity": 35, "zero trust": 38, "nen 7510": 35,
        "operating model": 35, "agile transformatie": 35,

        # Medium relevance (20-29) - zorg-IT
        "epd": 28, "ecd": 28, "hix": 25, "chipsoft": 25, "epic": 25,
        "fhir": 30, "hl7": 25, "interoperabiliteit": 28,
        "patiëntportaal": 25, "e-health": 28, "ehealth": 28,
        "zorginformatie": 25, "zorgplatform": 25,

        # Lower relevance (10-19) - algemeen
        "digitalisering": 18, "ict": 15, "software": 12,
        "implementatie": 15, "systeem": 10,
    }

    # Urgency keywords - focus op grote opportunities
    URGENCY_KEYWORDS = {
        # High urgency (25-30)
        "tender": 28, "aanbesteding": 28, "europese aanbesteding": 30,
        "rfp": 28, "rfi": 25, "marktconsultatie": 28,
        "deadline": 25, "inschrijving": 25,

        # Medium urgency (15-24)
        "subsidie": 22, "innovatiesubsidie": 24,
        "nieuw programma": 20, "transformatieprogramma": 22,
        "wet": 18, "regelgeving": 18, "verplicht": 20,

        # Lower urgency (10-14) - concurrent/markt
        "lanceert": 12, "introduceert": 12, "overname": 14,
        "fusie": 14, "samenwerking": 12, "partnerschap": 14,
    }

    # Action potential keywords
    ACTION_KEYWORDS = {
        # High action (25-30) - directe BD kans
        "tender": 28, "aanbesteding": 28, "rfp": 28,
        "marktconsultatie": 30, "subsidie": 25,
        "transformatieprogramma": 28, "digitaliseringsprogramma": 28,

        # Medium action (15-24) - thought leadership
        "onderzoek": 18, "rapport": 18, "whitepaper": 20,
        "congres": 18, "summit": 20, "conferentie": 18,
        "standaard": 16, "richtlijn": 16,

        # Lower action (10-14) - intelligence
        "concurrent": 12, "deloitte": 14, "kpmg": 14, "capgemini": 14,
        "mckinsey": 14, "pwc": 14, "ey": 14,
    }

    # Category detection - Accenture categories
    CATEGORY_PATTERNS = {
        "opportunity": ["tender", "aanbesteding", "rfp", "rfi", "subsidie", "marktconsultatie"],
        "concurrent": ["chipsoft", "epic", "nedap", "philips", "topicus", "deloitte", "kpmg", "capgemini", "mckinsey"],
        "klant": ["umc", "ziekenhuis", "ggz", "zorgverzekeraar", "vvt"],
        "overheid": ["rijksoverheid", "ministerie", "kamerbrief", "vws", "nza", "rivm", "nictiz"],
        "innovatie": ["innovatie", "pilot", "experiment", "startup", "scale-up"],
        "thought-leadership": ["onderzoek", "rapport", "whitepaper", "congres", "publicatie"],
    }

    # Tag extraction
    TAG_KEYWORDS = {
        "Cloud": ["cloud", "azure", "aws", "saas", "paas"],
        "Data": ["data", "analytics", "bi", "dashboard", "warehouse"],
        "AI": ["ai", "artificial intelligence", "machine learning", "ml", "chatgpt", "llm", "generative"],
        "EPD": ["epd", "ecd", "hix", "epic", "elektronisch patiëntendossier"],
        "Security": ["security", "cybersecurity", "beveiliging", "nen 7510", "privacy"],
        "Transformatie": ["transformatie", "digitalisering", "modernisering"],
        "Tender": ["tender", "aanbesteding", "rfp", "rfi"],
        "Ziekenhuis": ["ziekenhuis", "umc", "medisch centrum"],
        "GGZ": ["ggz", "geestelijke gezondheidszorg", "psychiatr"],
        "VVT": ["vvt", "verpleeg", "verzorg", "thuiszorg"],
        "Verzekeraar": ["zorgverzekeraar", "verzekeraar", "zorgverzekering"],
        "Subsidie": ["subsidie", "innovatiebudget", "zonmw"],
    }

    def __init__(self):
        pass

    def _calculate_keyword_score(
        self,
        text: str,
        keywords: dict[str, int],
        max_score: int
    ) -> int:
        """Calculate score based on keyword matches."""
        text_lower = text.lower()
        score = 0

        for keyword, weight in keywords.items():
            if keyword.lower() in text_lower:
                score = max(score, weight)

        return min(score, max_score)

    def _detect_category(self, text: str) -> str:
        """Detect article category based on keywords."""
        text_lower = text.lower()

        for category, patterns in self.CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if pattern in text_lower:
                    return category

        return "niet-relevant"

    def _extract_tags(self, text: str) -> list[str]:
        """Extract relevant tags from text."""
        tags = []
        text_lower = text.lower()

        for tag, keywords in self.TAG_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    tags.append(tag)
                    break
            if len(tags) >= 3:
                break

        return tags

    def _generate_summary(self, title: str, summary: str) -> str:
        """Generate Dutch summary."""
        if summary:
            clean = re.sub(r"<[^>]+>", "", summary)
            clean = re.sub(r"\s+", " ", clean).strip()
            if len(clean) > 150:
                return clean[:147] + "..."
            return clean
        return title

    def _is_not_relevant(self, text: str) -> bool:
        """Check if article is clearly not relevant for Accenture."""
        not_relevant_patterns = [
            "schoonmaak", "catering", "groenvoorziening", "veegmachine",
            "kantoorartikelen", "meubilair", "verbouwing", "onderhoud gebouw",
            "zwerfafval", "afvalverwerking", "printservices",
        ]
        text_lower = text.lower()
        return any(p in text_lower for p in not_relevant_patterns)

    def score_article(self, article: dict) -> dict:
        """Score a single article using keyword matching."""
        title = article.get("title", "")
        summary = article.get("summary", "")
        source = article.get("source", {}).get("name", "")
        text = f"{title} {summary} {source}"

        # Check if clearly not relevant
        if self._is_not_relevant(text):
            scored = article.copy()
            scored["score"] = {
                "total": 0,
                "relevance": 0,
                "urgency": 0,
                "action_potential": 0,
                "scored_by": "fallback",
            }
            scored["category"] = "niet-relevant"
            scored["tags"] = []
            scored["action_hint"] = None
            scored["summary_nl"] = self._generate_summary(title, summary)
            scored["priority"] = "low"
            return scored

        # Calculate scores
        relevance = self._calculate_keyword_score(text, self.RELEVANCE_KEYWORDS, 40)
        urgency = self._calculate_keyword_score(text, self.URGENCY_KEYWORDS, 30)
        action_potential = self._calculate_keyword_score(text, self.ACTION_KEYWORDS, 30)

        # Boost for TenderNed source
        if "tender" in source.lower():
            urgency = max(urgency, 20)
            action_potential = max(action_potential, 22)

        total = relevance + urgency + action_potential

        # Determine priority
        if total >= 80:
            priority = "critical"
        elif total >= 60:
            priority = "high"
        elif total >= 40:
            priority = "medium"
        else:
            priority = "low"

        # Create scored article
        scored = article.copy()
        scored["score"] = {
            "total": total,
            "relevance": relevance,
            "urgency": urgency,
            "action_potential": action_potential,
            "scored_by": "fallback",
        }
        scored["category"] = self._detect_category(text)
        scored["tags"] = self._extract_tags(text)
        scored["action_hint"] = None
        scored["summary_nl"] = self._generate_summary(title, summary)
        scored["priority"] = priority

        return scored

    def score(self, articles: list[dict]) -> list[dict]:
        """Score all articles using keyword matching."""
        print(f"Scoring {len(articles)} articles with fallback scorer...")

        scored = []
        for article in articles:
            scored.append(self.score_article(article))

        # Count by priority
        priorities = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for article in scored:
            priorities[article["priority"]] += 1

        print(f"  Results: {priorities['critical']} critical, {priorities['high']} high, "
              f"{priorities['medium']} medium, {priorities['low']} low")

        return scored
