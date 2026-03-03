#!/usr/bin/env python3
"""Run all collectors and save output."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from collectors import RSSCollector, TenderNedCollector, OverheidCollector
from collectors.dedup import deduplicate_articles


def run_collectors():
    """Run all collectors and aggregate results."""
    all_articles = []
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"

    # Ensure directories exist
    data_dir.mkdir(exist_ok=True)
    raw_dir.mkdir(exist_ok=True)

    # 1. RSS Collector
    print("=" * 60)
    print("1. RSS Collector")
    print("=" * 60)
    try:
        rss_collector = RSSCollector(config_path=str(project_root / "config" / "feeds.yml"))
        rss_articles = rss_collector.collect()
        all_articles.extend(rss_articles)
        rss_collector.save_raw(rss_articles, str(raw_dir))
    except Exception as e:
        print(f"Error running RSS collector: {e}")

    # 2. TenderNed Collector
    print()
    print("=" * 60)
    print("2. TenderNed Collector")
    print("=" * 60)
    try:
        tender_collector = TenderNedCollector(days_back=14)
        tender_articles = tender_collector.collect()
        all_articles.extend(tender_articles)
        tender_collector.save_raw(tender_articles, str(raw_dir))
    except Exception as e:
        print(f"Error running TenderNed collector: {e}")

    # 3. Overheid.nl Collector
    print()
    print("=" * 60)
    print("3. Overheid.nl Collector")
    print("=" * 60)
    try:
        overheid_collector = OverheidCollector(days_back=14)
        overheid_articles = overheid_collector.collect()
        all_articles.extend(overheid_articles)
        overheid_collector.save_raw(overheid_articles, str(raw_dir))
    except Exception as e:
        print(f"Error running Overheid.nl collector: {e}")

    # Deduplicate
    print()
    print("=" * 60)
    print("Deduplication")
    print("=" * 60)
    print(f"Before deduplication: {len(all_articles)} articles")

    unique_articles = deduplicate_articles(
        all_articles,
        url_exact=True,
        title_threshold=0.85,
    )

    print(f"After deduplication: {len(unique_articles)} articles")
    print(f"Removed {len(all_articles) - len(unique_articles)} duplicates")

    # Sort by published date (newest first)
    unique_articles.sort(key=lambda a: a.published, reverse=True)

    # Save aggregated articles
    print()
    print("=" * 60)
    print("Saving Results")
    print("=" * 60)

    articles_file = data_dir / "articles.json"
    with open(articles_file, "w", encoding="utf-8") as f:
        json.dump(
            [a.to_dict() for a in unique_articles],
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Saved {len(unique_articles)} articles to {articles_file}")

    # Print summary by source
    print()
    print("Summary by source:")
    sources = {}
    for article in unique_articles:
        source = article.source_name
        sources[source] = sources.get(source, 0) + 1

    for source, count in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"  {source}: {count}")

    return unique_articles


if __name__ == "__main__":
    run_collectors()
