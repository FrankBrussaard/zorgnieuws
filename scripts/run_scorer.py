#!/usr/bin/env python3
"""Run AI scoring on collected articles."""
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scorer import ClaudeScorer, FallbackScorer


def run_scorer(use_claude: bool = True):
    """Score articles with Claude API or fallback."""
    data_dir = project_root / "data"
    articles_file = data_dir / "articles.json"
    scored_file = data_dir / "scored.json"

    # Load articles
    if not articles_file.exists():
        print("No articles.json found. Run collectors first.")
        return

    with open(articles_file, "r", encoding="utf-8") as f:
        articles = json.load(f)

    print(f"Loaded {len(articles)} articles")
    print()

    # Check for cached scores (only score new articles)
    cached_scores = {}
    if scored_file.exists():
        with open(scored_file, "r", encoding="utf-8") as f:
            cached = json.load(f)
            cached_scores = {a["id"]: a for a in cached if a.get("score")}
        print(f"Found {len(cached_scores)} cached scores")

    # Find articles that need scoring
    to_score = [a for a in articles if a["id"] not in cached_scores]
    already_scored = [cached_scores[a["id"]] for a in articles if a["id"] in cached_scores]

    print(f"Articles to score: {len(to_score)}")
    print(f"Already scored: {len(already_scored)}")
    print()

    if not to_score:
        print("All articles already scored. Skipping.")
        scored_articles = already_scored
    else:
        # Try Claude API first, fallback to keywords
        if use_claude and os.environ.get("ANTHROPIC_API_KEY"):
            try:
                scorer = ClaudeScorer()
                newly_scored = scorer.score(to_score)
            except Exception as e:
                print(f"Claude API failed: {e}")
                print("Falling back to keyword scorer...")
                scorer = FallbackScorer()
                newly_scored = scorer.score(to_score)
        else:
            if use_claude:
                print("ANTHROPIC_API_KEY not set. Using fallback scorer.")
            scorer = FallbackScorer()
            newly_scored = scorer.score(to_score)

        # Combine with cached scores
        scored_articles = already_scored + newly_scored

    # Sort by score (highest first)
    scored_articles.sort(key=lambda x: x.get("score", {}).get("total", 0), reverse=True)

    # Save scored articles
    with open(scored_file, "w", encoding="utf-8") as f:
        json.dump(scored_articles, f, ensure_ascii=False, indent=2)

    print()
    print(f"Saved {len(scored_articles)} scored articles to {scored_file}")

    # Print top 10
    print()
    print("=" * 60)
    print("Top 10 Highest Priority Articles")
    print("=" * 60)

    for i, article in enumerate(scored_articles[:10], 1):
        score = article.get("score", {})
        priority = article.get("priority", "low")
        indicator = {"critical": "[!]", "high": "[+]", "medium": "[~]", "low": "[ ]"}.get(priority, "[ ]")

        title = article['title'][:60]
        print(f"{i:2}. {indicator} [{score.get('total', 0):3}] {title}...")
        if article.get("action_hint"):
            print(f"      -> {article['action_hint']}")
        print()

    return scored_articles


if __name__ == "__main__":
    # Check for --fallback flag
    use_claude = "--fallback" not in sys.argv
    run_scorer(use_claude=use_claude)
