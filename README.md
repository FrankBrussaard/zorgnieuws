# Zorgnieuws

Automatische nieuwsaggregator voor de Nederlandse zorgsector, geoptimaliseerd voor strategische consultancy.

## Features

- **Automatische nieuwsverzameling** uit 8+ bronnen (RSS, TenderNed API)
- **AI-prioritering** met Claude API (of keyword fallback)
- **Filtering** op categorie (opportunity, concurrent, overheid) en tags (AI, Cloud, EPD)
- **Dark mode** met systeemvoorkeur detectie
- **Dagelijkse updates** via GitHub Actions

## Lokaal draaien

```bash
# Install dependencies
pip install -r requirements.txt

# Collect news
python scripts/run_collectors.py

# Score articles (requires ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=your-key
python scripts/run_scorer.py

# Or use keyword fallback
python scripts/run_scorer.py --fallback

# Build site
python generator/build_site.py

# Open docs/index.html in browser
```

## GitHub Actions

De site wordt dagelijks om 06:00 CET automatisch gebouwd en gepubliceerd naar GitHub Pages.

### Secrets configureren

1. Ga naar repo Settings → Secrets and variables → Actions
2. Voeg toe: `ANTHROPIC_API_KEY` met je Claude API key

### Pages configureren

1. Ga naar repo Settings → Pages
2. Source: GitHub Actions

## Projectstructuur

```
├── collectors/          # Nieuwsverzamelaars (RSS, API)
├── scorer/              # AI scoring (Claude + fallback)
├── generator/           # Static site generator
├── config/              # Configuratie (feeds, prompt)
├── data/                # Verzamelde artikelen (JSON)
├── docs/                # Gegenereerde site
├── scripts/             # Orchestratie scripts
├── tests/               # Pytest tests
└── .github/workflows/   # GitHub Actions
```

## Scoring

Elk artikel krijgt een score van 0-100:

| Component | Range | Beschrijving |
|-----------|-------|--------------|
| Relevantie | 0-40 | Past bij strategische focus (cloud, AI, transformatie) |
| Urgentie | 0-30 | Deadline, momentum, breaking news |
| Actie-potentieel | 0-30 | BD opportunity, thought leadership |

**Priority levels:**
- 🔴 Critical (80-100): Directe actie
- 🟠 High (60-79): Deze week bespreken
- 🟡 Medium (40-59): Goed om te weten
- ⚪ Low (0-39): Achtergrond

## Prompt aanpassen

Ga naar `/settings.html` (wachtwoord: `admin`) om de scoring prompt aan te passen voor je organisatie.

## License

Private - Internal use only
