# CLAUDE.md — Zorgnieuws

## Project
Statische zorgnieuwssite. Dagelijks gebuild via GitHub Actions.
Draait op GitHub Pages vanuit /docs directory.

## Architectuur
- Python collectors halen nieuws op (RSS, API, scraping)
- Claude API (Sonnet) scoort en categoriseert artikelen
- Python generator bouwt statische HTML
- GitHub Actions orkestreert dagelijks om 06:00 CET

## Commands
- `python scripts/run_collectors.py` — Haal nieuws op
- `python scripts/run_scorer.py` — Score met Claude API
- `python scripts/run_scorer.py --fallback` — Score met keyword fallback
- `python generator/build_site.py` — Genereer site
- `python -m pytest tests/` — Run tests

## Scoring
Score = Relevantie (0-40) + Urgentie (0-30) + Actie-potentieel (0-30)
- 80-100: 🔴 Critical - directe actie nodig
- 60-79: 🟠 High - deze week bespreken
- 40-59: 🟡 Medium - goed om te weten
- 0-39: ⚪ Low - achtergrond

## Code style
- Python 3.12, type hints, docstrings
- Config in YAML, data in JSON
- Geen frameworks voor frontend (vanilla HTML/CSS/JS)
- Collectors erven van BaseCollector
- Alles async-ready maar sync default

## Belangrijke beslissingen
- Scored artikelen worden gecached (alleen nieuwe scoren)
- Deduplicatie op URL + titel-similarity (>85%)
- Fallback scorer als Claude API faalt
- Archief na 30 dagen
- GitHub Pages serveert /docs directory

## Repostructuur
```
collectors/         ← Python collectors (RSS, API, scraper)
config/             ← YAML configuratie (feeds, scrapers, prompts)
scorer/             ← AI scoring module
generator/          ← HTML site generator
data/               ← JSON data (articles, scored, raw)
docs/               ← GitHub Pages output
scripts/            ← Orchestratie scripts
tests/              ← Pytest tests
```

## Uniform Article Format
Elk artikel heeft:
- id (sha256 hash van url)
- url, title, summary, published, collected
- source (name, type, url)
- score (total, relevance, urgency, action_potential, scored_by)
- category, tags, action_hint, summary_nl, priority
