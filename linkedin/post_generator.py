"""LinkedIn post generator using Claude API."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


LINKEDIN_PROMPT_TEMPLATE = """Je schrijft LinkedIn-posts voor senior Accenture consultants in de Nederlandse zorgsector.

STIJL — Accenture thought leadership:
- Open met een pakkende hook (vraag, bold statement, of verrassend cijfer)
- Persoonlijke toon: "In mijn werk met ziekenhuizen zie ik..." / "Deze week werd duidelijk dat..."
- Onderbouw met data en concrete voorbeelden waar mogelijk
- Positioneer Accenture subtiel: niet "wij bij Accenture", maar laat expertise blijken door diepgang en visie
- Structuur: hook → context → insight → visie → call-to-action
- Gebruik witruimte (korte alinea's, max 3-4 zinnen per blok)
- Sluit af met een vraag of uitnodiging tot dialoog
- Relevante hashtags (3-5): #DigitaleZorg #ZorgInnovatie etc.
- Max 1300 tekens (LinkedIn sweet spot voor engagement)
- Taal: Nederlands

{global_prompt}

CONTEXT VOOR DEZE POST:
Expert: {sme_name}
Expertisegebied: {sme_prompt_hint}

ARTIKEL:
Titel: {article_title}
Samenvatting: {article_summary}
Bron: {article_source}
Tags: {article_tags}
Relevantie: {article_action_hint}

Schrijf een LinkedIn-post vanuit het perspectief van {sme_name}.
De post moet thought leadership uitstralen en Accenture's expertise in dit domein subtiel laten zien.
Verwijs naar het nieuws als relevante context, niet als "ik las dit artikel".

Antwoord ALLEEN met de LinkedIn-post tekst, geen extra uitleg."""


class LinkedInPostGenerator:
    """Generate LinkedIn posts for high-priority thought leadership articles."""

    def __init__(
        self,
        owners_path: str = "config/owners.json",
        posts_path: str = "data/linkedin_posts.json",
        api_key: Optional[str] = None,
    ):
        self.owners_path = Path(owners_path)
        self.posts_path = Path(posts_path)
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

        if not HAS_ANTHROPIC:
            raise ImportError("anthropic package not installed")

        self.client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else None
        self.owners_config = self._load_owners()

    def _load_owners(self) -> dict:
        """Load SME owners configuration."""
        if self.owners_path.exists():
            with open(self.owners_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"owners": [], "global_prompt": "", "score_threshold": 80}

    def _load_existing_posts(self) -> dict:
        """Load existing generated posts to avoid duplicates."""
        if self.posts_path.exists():
            with open(self.posts_path, "r", encoding="utf-8") as f:
                posts = json.load(f)
                return {p["article_id"]: p for p in posts}
        return {}

    def _find_owner_for_tags(self, tags: list[str]) -> Optional[dict]:
        """Find the best SME owner for given tags."""
        owners = self.owners_config.get("owners", [])

        for tag in tags:
            for owner in owners:
                if owner["tag"].lower() == tag.lower():
                    return owner

        # Return fallback owner if no match
        return self.owners_config.get("fallback_owner")

    def _generate_post(self, article: dict, owner: dict) -> str:
        """Generate a LinkedIn post using Claude API."""
        if not self.client:
            return self._generate_fallback_post(article, owner)

        prompt = LINKEDIN_PROMPT_TEMPLATE.format(
            global_prompt=self.owners_config.get("global_prompt", ""),
            sme_name=owner.get("name", "Expert"),
            sme_prompt_hint=owner.get("prompt_hint", ""),
            article_title=article.get("title", ""),
            article_summary=article.get("summary_nl") or article.get("summary", ""),
            article_source=article.get("source", {}).get("name", ""),
            article_tags=", ".join(article.get("tags", [])),
            article_action_hint=article.get("action_hint", ""),
        )

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            print(f"  Error generating post: {e}")
            return self._generate_fallback_post(article, owner)

    def _generate_fallback_post(self, article: dict, owner: dict) -> str:
        """Generate a simple fallback post without API."""
        title = article.get("title", "")
        summary = article.get("summary_nl") or article.get("summary", "")[:200]
        tags = article.get("tags", [])

        hashtags = " ".join([f"#{tag.replace(' ', '')}" for tag in tags[:3]])
        hashtags += " #DigitaleZorg #ZorgInnovatie"

        return f"""Dit is een belangrijk signaal voor de zorgsector.

{summary}

De impact hiervan op digitale transformatie in de zorg verdient onze aandacht.

Wat zijn jullie gedachten hierover?

{hashtags}"""

    def generate_posts(self, scored_articles: list[dict]) -> list[dict]:
        """Generate LinkedIn posts for qualifying articles."""
        threshold = self.owners_config.get("score_threshold", 80)
        existing_posts = self._load_existing_posts()

        qualifying = [
            a for a in scored_articles
            if a.get("score", {}).get("total", 0) >= threshold
            and a.get("category") in ["thought-leadership", "innovatie", "overheid", "klant"]
            and a["id"] not in existing_posts
        ]

        print(f"Found {len(qualifying)} articles qualifying for LinkedIn posts")

        new_posts = []
        for article in qualifying[:5]:  # Max 5 posts per run
            owner = self._find_owner_for_tags(article.get("tags", []))
            if not owner:
                continue

            print(f"  Generating post for: {article['title'][:50]}...")
            print(f"    SME: {owner.get('name')}")

            post_text = self._generate_post(article, owner)

            post_data = {
                "article_id": article["id"],
                "article_title": article["title"],
                "article_url": article["url"],
                "article_score": article.get("score", {}).get("total", 0),
                "article_tags": article.get("tags", []),
                "sme_name": owner.get("name"),
                "sme_email": owner.get("email"),
                "post_text": post_text,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "emailed": False,
            }
            new_posts.append(post_data)

        # Save all posts (existing + new)
        all_posts = list(existing_posts.values()) + new_posts
        all_posts.sort(key=lambda x: x.get("generated_at", ""), reverse=True)

        self.posts_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.posts_path, "w", encoding="utf-8") as f:
            json.dump(all_posts, f, ensure_ascii=False, indent=2)

        print(f"Generated {len(new_posts)} new LinkedIn posts")
        return new_posts
