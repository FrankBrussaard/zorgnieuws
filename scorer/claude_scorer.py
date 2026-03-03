"""Claude API scorer for Zorgnieuws articles."""
import json
import os
import time
from pathlib import Path
from typing import Optional

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
RATE_LIMIT_DELAY = 60  # seconds


class ClaudeScorer:
    """Score articles using Claude API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        batch_size: int = 20,
        prompt_path: Optional[str] = None,
    ):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        self.batch_size = batch_size

        if not HAS_ANTHROPIC:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        self.client = anthropic.Anthropic(api_key=self.api_key)

        # Load prompt template
        if prompt_path:
            self.prompt_template = Path(prompt_path).read_text(encoding="utf-8")
        else:
            default_path = Path(__file__).parent.parent / "config" / "scoring_prompt.txt"
            self.prompt_template = default_path.read_text(encoding="utf-8")

    def _prepare_batch(self, articles: list[dict]) -> str:
        """Prepare a batch of articles for scoring."""
        batch_text = []
        for article in articles:
            batch_text.append(
                f"ID: {article['id']}\n"
                f"Titel: {article['title']}\n"
                f"Bron: {article.get('source', {}).get('name', 'Onbekend')}\n"
                f"Samenvatting: {article.get('summary', '')[:500]}\n"
            )
        return "\n---\n".join(batch_text)

    def _parse_response(self, response_text: str) -> dict:
        """Parse Claude's JSON response."""
        # Find JSON in response
        try:
            # Try to find JSON block
            if "```json" in response_text:
                start = response_text.index("```json") + 7
                end = response_text.index("```", start)
                json_str = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.index("```") + 3
                end = response_text.index("```", start)
                json_str = response_text[start:end].strip()
            else:
                # Assume entire response is JSON
                json_str = response_text.strip()

            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"  Warning: Could not parse response: {e}")
            return {"articles": []}

    def _score_batch(self, articles: list[dict], retry_count: int = 0) -> list[dict]:
        """Score a batch of articles using Claude API with retry logic."""
        batch_text = self._prepare_batch(articles)

        user_message = f"""Beoordeel de volgende {len(articles)} artikelen:

{batch_text}

Geef je beoordeling als JSON."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": self.prompt_template + "\n\n" + user_message}
                ],
            )

            response_text = response.content[0].text
            result = self._parse_response(response_text)

            return result.get("articles", [])

        except anthropic.RateLimitError as e:
            if retry_count < MAX_RETRIES:
                print(f"  Rate limit hit, waiting {RATE_LIMIT_DELAY}s before retry...")
                time.sleep(RATE_LIMIT_DELAY)
                return self._score_batch(articles, retry_count + 1)
            print(f"  Rate limit error after {MAX_RETRIES} retries: {e}")
            return []

        except anthropic.APIConnectionError as e:
            if retry_count < MAX_RETRIES:
                print(f"  Connection error, retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY * (retry_count + 1))
                return self._score_batch(articles, retry_count + 1)
            print(f"  Connection error after {MAX_RETRIES} retries: {e}")
            return []

        except anthropic.APIStatusError as e:
            if e.status_code >= 500 and retry_count < MAX_RETRIES:
                print(f"  Server error ({e.status_code}), retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY * (retry_count + 1))
                return self._score_batch(articles, retry_count + 1)
            print(f"  API error: {e}")
            return []

        except Exception as e:
            print(f"  Unexpected error: {e}")
            return []

    def score(self, articles: list[dict]) -> list[dict]:
        """Score all articles in batches."""
        if not articles:
            return []

        print(f"Scoring {len(articles)} articles with Claude API...")
        print(f"  Model: {self.model}")
        print(f"  Batch size: {self.batch_size}")

        scored_articles = []
        article_map = {a["id"]: a for a in articles}

        # Process in batches
        for i in range(0, len(articles), self.batch_size):
            batch = articles[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (len(articles) + self.batch_size - 1) // self.batch_size

            print(f"  Batch {batch_num}/{total_batches} ({len(batch)} articles)...")

            scores = self._score_batch(batch)

            # Merge scores into articles
            for score_data in scores:
                article_id = score_data.get("id")
                if article_id and article_id in article_map:
                    article = article_map[article_id].copy()

                    # Calculate total score
                    relevance = score_data.get("relevance", 0)
                    urgency = score_data.get("urgency", 0)
                    action_potential = score_data.get("action_potential", 0)
                    total = relevance + urgency + action_potential

                    # Add score data
                    article["score"] = {
                        "total": total,
                        "relevance": relevance,
                        "urgency": urgency,
                        "action_potential": action_potential,
                        "scored_by": "claude",
                    }
                    article["category"] = score_data.get("category", "algemeen")
                    article["tags"] = score_data.get("tags", [])
                    article["action_hint"] = score_data.get("action_hint")
                    article["summary_nl"] = score_data.get("summary_nl")

                    # Set priority based on score
                    if total >= 80:
                        article["priority"] = "critical"
                    elif total >= 60:
                        article["priority"] = "high"
                    elif total >= 40:
                        article["priority"] = "medium"
                    else:
                        article["priority"] = "low"

                    scored_articles.append(article)

            # Rate limiting - wait between batches
            if i + self.batch_size < len(articles):
                time.sleep(1)

        # Add unscored articles with default values
        scored_ids = {a["id"] for a in scored_articles}
        for article in articles:
            if article["id"] not in scored_ids:
                article = article.copy()
                article["score"] = {
                    "total": 0,
                    "relevance": 0,
                    "urgency": 0,
                    "action_potential": 0,
                    "scored_by": "skipped",
                }
                article["priority"] = "low"
                scored_articles.append(article)

        print(f"  Scored {len(scored_articles)} articles")
        return scored_articles
