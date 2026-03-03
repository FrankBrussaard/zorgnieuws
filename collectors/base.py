"""Base collector class for Zorgnieuws."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional
import hashlib
import json


@dataclass
class Article:
    """Uniform article format for all collectors."""

    url: str
    title: str
    summary: str
    published: datetime
    source_name: str
    source_type: str  # rss, api, scraper
    source_url: str
    collected: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Fields populated by scorer (optional at collection time)
    score_total: Optional[int] = None
    score_relevance: Optional[int] = None
    score_urgency: Optional[int] = None
    score_action_potential: Optional[int] = None
    scored_by: Optional[str] = None
    category: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    action_hint: Optional[str] = None
    summary_nl: Optional[str] = None
    priority: Optional[str] = None

    @property
    def id(self) -> str:
        """Generate unique ID from URL hash."""
        return hashlib.sha256(self.url.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["id"] = self.id
        data["published"] = self.published.isoformat()
        data["collected"] = self.collected.isoformat()
        data["source"] = {
            "name": data.pop("source_name"),
            "type": data.pop("source_type"),
            "url": data.pop("source_url"),
        }
        if self.score_total is not None:
            data["score"] = {
                "total": data.pop("score_total"),
                "relevance": data.pop("score_relevance"),
                "urgency": data.pop("score_urgency"),
                "action_potential": data.pop("score_action_potential"),
                "scored_by": data.pop("scored_by"),
            }
        else:
            # Remove score fields if not set
            for key in ["score_total", "score_relevance", "score_urgency",
                       "score_action_potential", "scored_by"]:
                data.pop(key, None)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Article":
        """Create Article from dictionary."""
        source = data.get("source", {})
        score = data.get("score", {})

        return cls(
            url=data["url"],
            title=data["title"],
            summary=data["summary"],
            published=datetime.fromisoformat(data["published"]),
            collected=datetime.fromisoformat(data["collected"]),
            source_name=source.get("name", ""),
            source_type=source.get("type", ""),
            source_url=source.get("url", ""),
            score_total=score.get("total"),
            score_relevance=score.get("relevance"),
            score_urgency=score.get("urgency"),
            score_action_potential=score.get("action_potential"),
            scored_by=score.get("scored_by"),
            category=data.get("category"),
            tags=data.get("tags", []),
            action_hint=data.get("action_hint"),
            summary_nl=data.get("summary_nl"),
            priority=data.get("priority"),
        )


class BaseCollector(ABC):
    """Abstract base class for all collectors."""

    def __init__(self, name: str, source_type: str):
        self.name = name
        self.source_type = source_type
        self.collected_at = datetime.now(timezone.utc)

    @abstractmethod
    def collect(self) -> list[Article]:
        """Collect articles from the source. Must be implemented by subclasses."""
        pass

    def save_raw(self, articles: list[Article], output_dir: str) -> str:
        """Save raw collected articles to JSON file."""
        from pathlib import Path

        date_str = self.collected_at.strftime("%Y-%m-%d")
        output_path = Path(output_dir) / date_str
        output_path.mkdir(parents=True, exist_ok=True)

        filename = output_path / f"{self.name}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(
                [article.to_dict() for article in articles],
                f,
                ensure_ascii=False,
                indent=2,
            )

        return str(filename)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
