"""RSS Feed collector for Zorgnieuws."""
from datetime import datetime, timezone
from typing import Optional
import time

import feedparser
import yaml

from .base import BaseCollector, Article


class RSSCollector(BaseCollector):
    """Collector for RSS feeds."""

    def __init__(self, config_path: str = "config/feeds.yml"):
        super().__init__(name="rss", source_type="rss")
        self.config_path = config_path
        self.feeds = self._load_config()

    def _load_config(self) -> list[dict]:
        """Load feed configuration from YAML."""
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config.get("feeds", [])

    def _parse_date(self, entry: dict) -> datetime:
        """Parse publication date from feed entry."""
        # Try different date fields
        for field in ["published_parsed", "updated_parsed", "created_parsed"]:
            if hasattr(entry, field) and getattr(entry, field):
                parsed = getattr(entry, field)
                if parsed:
                    return datetime(*parsed[:6], tzinfo=timezone.utc)

        # Fallback to current time
        return datetime.now(timezone.utc)

    def _get_summary(self, entry: dict) -> str:
        """Extract summary from feed entry."""
        # Try different summary fields
        if hasattr(entry, "summary") and entry.summary:
            summary = entry.summary
        elif hasattr(entry, "description") and entry.description:
            summary = entry.description
        elif hasattr(entry, "content") and entry.content:
            summary = entry.content[0].get("value", "")
        else:
            summary = ""

        # Strip HTML tags (basic)
        import re
        summary = re.sub(r"<[^>]+>", "", summary)
        summary = re.sub(r"\s+", " ", summary).strip()

        # Limit length
        if len(summary) > 500:
            summary = summary[:497] + "..."

        return summary

    def _collect_feed(self, feed_config: dict) -> list[Article]:
        """Collect articles from a single RSS feed."""
        articles = []
        feed_url = feed_config["url"]
        source_name = feed_config["name"]
        source_url = feed_config.get("source_url", feed_url.rsplit("/", 1)[0])

        try:
            feed = feedparser.parse(feed_url)

            if feed.bozo and not feed.entries:
                print(f"  Warning: Feed error for {source_name}: {feed.bozo_exception}")
                return []

            for entry in feed.entries:
                # Skip entries without URL
                link = getattr(entry, "link", None)
                if not link:
                    continue

                title = getattr(entry, "title", "Geen titel")

                article = Article(
                    url=link,
                    title=title,
                    summary=self._get_summary(entry),
                    published=self._parse_date(entry),
                    source_name=source_name,
                    source_type="rss",
                    source_url=source_url,
                    collected=self.collected_at,
                )
                articles.append(article)

            print(f"  Collected {len(articles)} articles from {source_name}")

        except Exception as e:
            print(f"  Error collecting {source_name}: {e}")

        return articles

    def collect(self) -> list[Article]:
        """Collect articles from all configured RSS feeds."""
        all_articles = []

        print(f"Collecting from {len(self.feeds)} RSS feeds...")

        for feed_config in self.feeds:
            if not feed_config.get("enabled", True):
                print(f"  Skipping disabled feed: {feed_config['name']}")
                continue

            articles = self._collect_feed(feed_config)
            all_articles.extend(articles)

            # Small delay between feeds to be polite
            time.sleep(0.5)

        print(f"Total: {len(all_articles)} articles from RSS feeds")
        return all_articles
