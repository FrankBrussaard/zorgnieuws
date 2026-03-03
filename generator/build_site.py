#!/usr/bin/env python3
"""Build static HTML site from articles."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def get_priority_indicator(score: int | None) -> tuple[str, str]:
    """Get priority indicator emoji and class based on score."""
    if score is None:
        return "⚪", "low"
    if score >= 80:
        return "🔴", "critical"
    if score >= 60:
        return "🟠", "high"
    if score >= 40:
        return "🟡", "medium"
    return "⚪", "low"


def format_time_ago(published: str) -> str:
    """Format time ago string."""
    try:
        dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = now - dt

        hours = diff.total_seconds() / 3600
        if hours < 1:
            return "< 1 uur geleden"
        if hours < 24:
            return f"{int(hours)} uur geleden"
        days = hours / 24
        if days < 7:
            return f"{int(days)} dagen geleden"
        return dt.strftime("%d %b %Y")
    except Exception:
        return ""


def build_index_html(articles: list[dict], output_path: Path):
    """Generate index.html from articles."""

    # Sort by published date (newest first)
    sorted_articles = sorted(
        articles,
        key=lambda x: x.get("published", ""),
        reverse=True,
    )

    # Generate article HTML
    articles_html = []
    for article in sorted_articles[:100]:  # Limit to 100 articles
        score = article.get("score", {}).get("total")
        indicator, priority_class = get_priority_indicator(score)
        source = article.get("source", {})

        tags_html = ""
        if article.get("tags"):
            tags = article["tags"][:3]  # Max 3 tags
            tags_html = " · ".join(f'<span class="tag">{tag}</span>' for tag in tags)

        category = article.get("category", "")
        if category:
            tags_html = f'<span class="category">{category}</span>' + (" · " + tags_html if tags_html else "")

        score_html = f' · Score: {score}' if score else ""

        articles_html.append(f'''
        <article class="article {priority_class}">
            <div class="indicator">{indicator}</div>
            <div class="content">
                <a href="{article["url"]}" target="_blank" class="title">{article["title"]}</a>
                <div class="meta">
                    {source.get("name", "Onbekend")} · {format_time_ago(article.get("published", ""))}
                </div>
                <div class="tags">
                    {tags_html}{score_html}
                </div>
            </div>
        </article>''')

    html = f'''<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zorgnieuws</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <h1>ZORGNIEUWS</h1>
        <nav>
            <a href="index.html" class="active">Alles</a>
            <a href="prio.html">Hoogste Prio</a>
            <a href="settings.html">Instellingen</a>
        </nav>
        <div class="updated">
            Laatst bijgewerkt: {datetime.now().strftime("%d %b %Y %H:%M")}
        </div>
        <button id="theme-toggle" class="theme-toggle" onclick="toggleDarkMode()" title="Toggle dark mode">🌙</button>
    </header>

    <main>
        <div class="articles">
            {"".join(articles_html)}
        </div>
    </main>

    <footer>
        <p>Automatisch verzameld uit {len(set(a.get("source", {}).get("name") for a in articles))} bronnen</p>
    </footer>

    <script src="filter.js"></script>
</body>
</html>'''

    output_path.write_text(html, encoding="utf-8")
    print(f"Generated {output_path}")


def build_prio_html(articles: list[dict], output_path: Path):
    """Generate prio.html with highest priority articles."""

    # Filter: only show medium priority and above (score >= 40)
    scored_articles = [
        a for a in articles
        if a.get("score", {}).get("total", 0) >= 40
    ]
    sorted_articles = sorted(
        scored_articles,
        key=lambda x: x.get("score", {}).get("total", 0),
        reverse=True,
    )

    # Count by priority for stats
    stats = {"critical": 0, "high": 0, "medium": 0}
    for a in sorted_articles:
        p = a.get("priority", "low")
        if p in stats:
            stats[p] += 1

    # Generate article HTML
    articles_html = []
    for article in sorted_articles[:100]:  # Top 100 by score
        score_data = article.get("score", {})
        score = score_data.get("total", 0)
        indicator, priority_class = get_priority_indicator(score)
        source = article.get("source", {})

        # Summary
        summary_nl = article.get("summary_nl", "")
        summary_html = f'<div class="summary">{summary_nl}</div>' if summary_nl else ""

        # Action hint
        action_hint = article.get("action_hint", "")
        action_html = f'<div class="action-hint">→ {action_hint}</div>' if action_hint else ""

        # Tags and category
        category = article.get("category", "")
        tags = article.get("tags", [])[:3]
        tags_parts = []
        if category:
            tags_parts.append(f'<span class="category">{category}</span>')
        for tag in tags:
            tags_parts.append(f'<span class="tag">{tag}</span>')
        tags_html = " ".join(tags_parts)

        # Score breakdown
        rel = score_data.get("relevance", 0)
        urg = score_data.get("urgency", 0)
        act = score_data.get("action_potential", 0)
        score_breakdown = f'<span class="score-breakdown">R:{rel} U:{urg} A:{act}</span>'

        # Data attributes for filtering
        tags_data = ",".join(tags) if tags else ""

        articles_html.append(f'''
        <article class="article {priority_class}" data-category="{category}" data-tags="{tags_data}">
            <div class="indicator">{indicator}</div>
            <div class="content">
                <a href="{article["url"]}" target="_blank" class="title">{article["title"]}</a>
                <div class="meta">
                    {source.get("name", "Onbekend")} · {format_time_ago(article.get("published", ""))}
                </div>
                {summary_html}
                {action_html}
                <div class="tags">
                    {tags_html}
                    <span class="score">Score: {score}</span> {score_breakdown}
                </div>
            </div>
        </article>''')

    # If no scored articles, show a message
    if not articles_html:
        articles_html = ['<p class="no-articles">Nog geen hoog-geprioriteerde artikelen gevonden.</p>']

    total_shown = len(sorted_articles[:100])

    html = f'''<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hoogste Prio - Zorgnieuws</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <h1>ZORGNIEUWS</h1>
        <nav>
            <a href="index.html">Alles</a>
            <a href="prio.html" class="active">Hoogste Prio</a>
            <a href="settings.html">Instellingen</a>
        </nav>
        <div class="updated">
            Laatst bijgewerkt: {datetime.now().strftime("%d %b %Y %H:%M")}
        </div>
        <button id="theme-toggle" class="theme-toggle" onclick="toggleDarkMode()" title="Toggle dark mode">🌙</button>
    </header>

    <div class="stats-bar">
        <span class="stat critical">🔴 {stats["critical"]} critical</span>
        <span class="stat high">🟠 {stats["high"]} high</span>
        <span class="stat medium">🟡 {stats["medium"]} medium</span>
        <span class="stat-count"><span id="visible-count">{total_shown} artikelen</span></span>
    </div>

    <div id="filter-bar" class="filter-bar">
        <div class="filter-group">
            <span class="filter-label">Categorie:</span>
            <div id="category-filter" class="filter-buttons"></div>
        </div>
        <div class="filter-group">
            <span class="filter-label">Tags:</span>
            <div id="tag-filter" class="filter-buttons"></div>
        </div>
        <button class="filter-btn clear-btn" onclick="clearFilters()">✕ Reset</button>
    </div>

    <main>
        <div class="articles">
            {"".join(articles_html)}
        </div>
    </main>

    <footer>
        <p>Score = Relevantie (0-40) + Urgentie (0-30) + Actie-potentieel (0-30) | Keys: j/k navigeer, o open, Esc reset</p>
    </footer>

    <script src="filter.js"></script>
</body>
</html>'''

    output_path.write_text(html, encoding="utf-8")
    print(f"Generated {output_path}")


def build_site():
    """Build the complete static site."""
    data_dir = project_root / "data"
    docs_dir = project_root / "docs"
    docs_dir.mkdir(exist_ok=True)

    # Load articles - prefer scored.json if available
    scored_file = data_dir / "scored.json"
    articles_file = data_dir / "articles.json"

    if scored_file.exists():
        print("Using scored.json (with AI scores)")
        with open(scored_file, "r", encoding="utf-8") as f:
            articles = json.load(f)
    elif articles_file.exists():
        print("Using articles.json (no scores yet)")
        with open(articles_file, "r", encoding="utf-8") as f:
            articles = json.load(f)
    else:
        print("No articles found. Run collectors first.")
        return

    print(f"Building site with {len(articles)} articles...")

    # Generate HTML files
    build_index_html(articles, docs_dir / "index.html")
    build_prio_html(articles, docs_dir / "prio.html")

    # Copy static files
    static_dir = project_root / "generator" / "static"
    for static_file in ["style.css", "filter.js", "settings.js"]:
        src = static_dir / static_file
        if src.exists():
            (docs_dir / static_file).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"Copied {static_file}")

    # Copy settings page
    templates_dir = project_root / "generator" / "templates"
    settings_src = templates_dir / "settings.html"
    if settings_src.exists():
        (docs_dir / "settings.html").write_text(settings_src.read_text(encoding="utf-8"), encoding="utf-8")
        print("Copied settings.html")

    # Generate JSON feed
    feed_file = docs_dir / "feed.json"
    with open(feed_file, "w", encoding="utf-8") as f:
        json.dump(articles[:100], f, ensure_ascii=False, indent=2)
    print(f"Generated {feed_file}")

    print()
    print("Site built successfully!")
    print(f"Open {docs_dir / 'index.html'} in your browser.")


if __name__ == "__main__":
    build_site()
