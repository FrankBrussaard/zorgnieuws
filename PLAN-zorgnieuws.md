# Zorgnieuws — Projectplan

> Actionable nieuwssite voor zorg(tech)consultancy | GitHub Pages + GitHub Actions
> Repo: `FrankBrussaard/zorgnieuws`

---

## 1. Wat we bouwen

Een statische nieuwssite die dagelijks automatisch wordt opgebouwd met drie kernfuncties:

1. **Nieuwsfeed** — Chronologisch overzicht van alle zorgnieuws
2. **Hoogste Prio** — AI-geprioriteerde feed: "hier moeten we iets mee"
3. **Categorieën & filters** — Snel filteren op thema, brontype, en actie-urgentie

### Design: Hacker News-stijl, maar dan actionable

```
┌─────────────────────────────────────────────────────────┐
│  ZORGNIEUWS                    [Hoogste Prio] [Alles]   │
│─────────────────────────────────────────────────────────│
│  🔴 TENDER: MSZ-platform aanbesteding UMC Utrecht       │
│     TenderNed · 2 uur geleden · Deadline: 15 apr        │
│     → EPD/EHR · Aanbesteding · Score: 94                │
│                                                         │
│  🟠 Chipsoft lanceert HiX 7.0 met AI-module             │
│     Chipsoft.nl · 5 uur geleden                         │
│     → Concurrent · EPD · AI/ML · Score: 87              │
│                                                         │
│  🟡 Kamerbrief: Voortgang digitalisering zorg           │
│     Rijksoverheid · 8 uur geleden                       │
│     → Overheid · Digitale transformatie · Score: 72     │
│                                                         │
│  ⚪ NOS: Wachtlijsten GGZ lopen verder op               │
│     NOS · 12 uur geleden                                │
│     → Algemeen · GGZ · Score: 35                        │
└─────────────────────────────────────────────────────────┘
```

Elke entry heeft:
- **Urgentie-indicator** (🔴🟠🟡⚪) op basis van AI-score
- **Bron en tijd**
- **Tags**: thema + brontype + relevantie-score
- **Klikbare link** naar origineel artikel

---

## 2. Architectuur

```
┌──────────────────────────────────────────────────────────┐
│                   GitHub Actions (dagelijks 06:00)        │
│                                                          │
│  ┌─────────┐  ┌──────────┐  ┌───────────┐               │
│  │  RSS     │  │  API     │  │  Scraper  │  ← Collectors │
│  │ Collector│  │ Collector│  │ Collector │               │
│  └────┬─────┘  └────┬─────┘  └─────┬─────┘               │
│       │              │              │                     │
│       └──────────────┼──────────────┘                     │
│                      ▼                                    │
│              ┌───────────────┐                            │
│              │  Normalize &  │  ← Uniform artikel-format  │
│              │  Deduplicate  │                            │
│              └───────┬───────┘                            │
│                      ▼                                    │
│              ┌───────────────┐                            │
│              │  Claude API   │  ← Prioritering + tagging  │
│              │  (Sonnet 4)   │    ~200 artikelen/dag      │
│              └───────┬───────┘    ~$0.10-0.50/dag         │
│                      ▼                                    │
│              ┌───────────────┐                            │
│              │  Static Site  │  ← HTML generatie           │
│              │  Generator    │                            │
│              └───────┬───────┘                            │
│                      ▼                                    │
│              ┌───────────────┐                            │
│              │  GitHub Pages │  ← Deploy                   │
│              └───────────────┘                            │
└──────────────────────────────────────────────────────────┘
```

### Waarom deze architectuur?

- **Geen server nodig** — alles draait in GitHub Actions
- **Minimale kosten** — alleen Claude API (~$0.10-0.50/dag voor Sonnet)
- **Geen tokens voor ophalen** — RSS/APIs/scraping zijn gratis
- **Versiebeheer** — alle data zit in de repo (JSON bestanden)
- **Uitbreidbaar** — nieuwe collector = nieuw Python-bestand

---

## 3. Bronnen (Collectors)

### 3A. RSS Feeds (v1 — dag 1)

| Bron | Feed URL | Type |
|------|----------|------|
| Skipr | skipr.nl/feed | Zorgsector nieuws |
| ICT&health | icthealth.nl/feed | Zorg-IT nieuws |
| Zorgvisie | zorgvisie.nl/feed | Zorgmanagement |
| NOS Gezondheid | feeds.nos.nl/nosnieuwsgezondheid | Algemeen zorgnieuws |
| Rijksoverheid — VWS | rijksoverheid.nl (RSS) | Kamerbrieven, beleid |
| Digitale Overheid | digitaleoverheid.nl/feed | Digitaal beleid |
| KNMG | knmg.nl/feed | Artsenorganisatie |
| NZa | nza.nl/feed | Zorgautoriteit |
| ZonMw | zonmw.nl/feed | Onderzoek & innovatie |
| Nictiz | nictiz.nl/feed | Standaarden & interop |
| RIVM | rivm.nl/feed | Volksgezondheid |
| Tweakers — IT | tweakers.net/feeds/mixed.xml | IT (filter op zorg) |

### 3B. API's (v1 — dag 1-2)

| Bron | API | Wat we ophalen |
|------|-----|---------------|
| TenderNed | tenderned.nl/papi/v1 | Zorggerelateerde aanbestedingen |
| Overheid.nl | zoek.officielebekendmakingen.nl | Kamerstukken, Staatscourant |
| RVO / SBIR | rvo.nl | Innovatiesubsidies zorg |

### 3C. Webscraping (v1 — dag 3-5)

| Bron | URL | Wat we scrapen |
|------|-----|---------------|
| **Zorgtech-bedrijven** | | |
| Chipsoft | chipsoft.nl/nieuws | Persberichten, releases |
| Nexus (Nedap) | nedap-healthcare.com/nl/nieuws | Product updates |
| Topicus | topicus.nl/nieuws | Persberichten |
| Luscii | luscii.com/blog | Persberichten |
| Philips Healthcare | philips.nl/healthcare/nieuws | Persberichten |
| Epic (NL) | epic.com/nl | NL-specifiek nieuws |
| **Consultancies** | | |
| Accenture Health | accenture.com/nl/health | Publicaties, cases |
| Deloitte Health | deloitte.nl/health | Insights, rapporten |
| Capgemini Health | capgemini.com/nl/health | Publicaties |
| KPMG Health | kpmg.nl/health | Rapporten |
| McKinsey Health | mckinsey.com/health | Publicaties |
| M&I Partners | mxi.nl/publicaties | Zorg-IT rapporten |
| **Zorginstellingen** | | |
| Zorginstituut NL | zorginstituutnederland.nl/nieuws | Standpunten, pakketbeheer |
| GGD GHOR | ggdghor.nl/nieuws | Publieke gezondheid |
| Top-5 UMC's | umcutrecht.nl etc. | Innovatie, persberichten |
| **Patent & publicaties** | | |
| Espacenet | worldwide.espacenet.com | Zorgtech patenten (NL) |
| PubMed | pubmed.ncbi.nlm.nih.gov | NL zorg-IT research |

---

## 4. AI-Prioritering (Claude Sonnet bij build-time)

### Scoringsmodel

Elk artikel krijgt een score van 0-100 gebaseerd op:

```
Score = Relevantie (0-40) + Urgentie (0-30) + Actie-potentieel (0-30)
```

**Relevantie (0-40):** Hoe dicht raakt dit onze dienstverlening?
- Direct gerelateerd aan onze diensten (EPD, data, AI, security, interop, cloud) → 30-40
- Gerelateerd aan zorg-IT in het algemeen → 15-29
- Gerelateerd aan zorg in het algemeen → 1-14

**Urgentie (0-30):** Is er een deadline of momentum?
- Tender met deadline < 30 dagen → 25-30
- Tender met deadline > 30 dagen → 15-24
- Beleid dat binnenkort ingaat → 15-20
- Nieuw product/dienst van concurrent → 10-15
- Algemeen nieuws → 0-9

**Actie-potentieel (0-30):** Kunnen we er concreet iets mee?
- Directe sales-opportunity (tender, RFI, subsidie) → 25-30
- Thought leadership opportunity (publicatie, standpunt) → 15-24
- Concurrentie-intelligentie (weten wat ze doen) → 10-14
- Marktinformatie (goed om te weten) → 0-9

### Prompt-strategie

Per batch van ~20 artikelen sturen we titel + samenvatting naar Claude met:

```
Je bent een strategisch adviseur voor een zorg-IT consultancy.
Onze diensten: [volledige lijst diensten].

Beoordeel elk artikel op:
1. Relevantie (0-40): raakt dit onze dienstverlening?
2. Urgentie (0-30): is er een deadline of momentum?
3. Actie-potentieel (0-30): kunnen we er concreet iets mee?

Geef ook:
- categorie: [tender|concurrent|overheid|innovatie|markt|publicatie|patent]
- tags: [lijst van relevante tags]
- actie_hint: één zin over wat we ermee zouden kunnen doen
- samenvatting_nl: korte samenvatting in het Nederlands (max 2 zinnen)

Antwoord in JSON.
```

### Kosteninschatting

- ~100-200 artikelen per dag
- Batches van 20 artikelen → ~10 API calls
- Sonnet 4: ~$3/M input, ~$15/M output tokens
- Input per batch: ~2000 tokens (artikelen) + ~500 tokens (prompt) = ~2500
- Output per batch: ~1500 tokens (JSON)
- **Totaal: ~25K input + ~15K output ≈ $0.08 + $0.23 = ~$0.30/dag**
- **~$9/maand**

---

## 5. Tech Stack

| Component | Technologie | Waarom |
|-----------|------------|--------|
| Collectors | Python 3.12 | feedparser, requests, beautifulsoup4 |
| Normalisatie | Python | Uniform JSON-format |
| AI-scoring | Python + Claude API | anthropic SDK |
| Site generator | JavaScript (11ty of puur) | Snelle static site generation |
| Styling | Vanilla CSS | Minimaal, snel, Hacker News stijl |
| Hosting | GitHub Pages | Gratis, automatisch |
| CI/CD | GitHub Actions | Dagelijkse build om 06:00 CET |
| Data opslag | JSON in repo | articles.json, scored.json |

### Alternatief: puur vanilla (mijn aanbeveling)

Gezien de Hacker News-stijl is een framework overkill. Ik raad aan:
- **Python script** dat HTML genereert uit JSON
- **Eén CSS file** (~200 regels)
- **Eén JS file** voor client-side filtering (~100 regels)
- Geen build tools, geen npm, geen frameworks

---

## 6. Repostructuur

```
FrankBrussaard/zorgnieuws/
├── .github/
│   └── workflows/
│       └── build.yml              ← Dagelijkse GitHub Action
├── collectors/
│   ├── __init__.py
│   ├── base.py                    ← BaseCollector class
│   ├── rss_collector.py           ← RSS feeds ophalen
│   ├── tenderned_collector.py     ← TenderNed API
│   ├── overheid_collector.py      ← Overheid.nl API
│   └── scraper_collector.py       ← Webscraping (per site config)
├── config/
│   ├── feeds.yml                  ← RSS feed URLs + metadata
│   ├── scrapers.yml               ← Scraper configuraties
│   ├── scoring_prompt.txt         ← Claude prompt template
│   └── diensten.yml               ← Onze diensten (voor scoring context)
├── scorer/
│   ├── claude_scorer.py           ← AI prioritering
│   └── fallback_scorer.py         ← Keyword-based fallback
├── generator/
│   ├── build_site.py              ← HTML generatie
│   ├── templates/
│   │   ├── index.html             ← Hoofdpagina template
│   │   ├── prio.html              ← Hoogste prio pagina
│   │   └── article.html           ← Artikel detail (optioneel)
│   └── static/
│       ├── style.css
│       └── filter.js
├── data/
│   ├── raw/                       ← Ruwe data per collector per dag
│   │   └── 2025-03-03/
│   ├── articles.json              ← Alle genormaliseerde artikelen
│   ├── scored.json                ← Met AI-scores
│   └── archive/                   ← Oudere data (per maand)
├── docs/                          ← GitHub Pages output directory
│   ├── index.html
│   ├── prio.html
│   ├── style.css
│   ├── filter.js
│   └── feed.json                  ← JSON API voor eventuele integraties
├── scripts/
│   ├── run_collectors.py          ← Orchestreert alle collectors
│   ├── run_scorer.py              ← Orchestreert AI scoring
│   └── run_build.py               ← Orchestreert site generatie
├── tests/
│   ├── test_collectors.py
│   └── test_scorer.py
├── requirements.txt
├── README.md
└── CLAUDE.md                      ← Claude Code instructies
```

---

## 7. Bouwplan (Claude Code sessies)

### Fase 1: Fundament (Sessie 1-2)

**Sessie 1: Project setup + RSS collectors**
- Repo structuur aanmaken
- BaseCollector class met uniform output format
- RSS collector met feedparser
- Config YAML met eerste 12 RSS feeds
- Test: draai lokaal, krijg JSON output
- Eerste simpele HTML output

**Sessie 2: API collectors + normalisatie**
- TenderNed API collector
- Overheid.nl API collector
- Deduplicatie-logica (URL + titel similarity)
- Normalisatie naar uniform artikel-format

### Fase 2: Intelligentie (Sessie 3-4)

**Sessie 3: AI-scoring pipeline**
- Claude API integratie (anthropic SDK)
- Batch-scoring logica (20 artikelen per call)
- Scoring prompt optimalisatie
- Fallback keyword-scorer (voor als API faalt)
- Output: scored.json met alle metadata

**Sessie 4: Scoring verfijning + testen**
- Prompt tuning met echte artikelen
- Score-kalibratie (zijn de scores zinvol?)
- Edge cases: duplicate handling, lege feeds, API fouten
- Rate limiting en retry logica

### Fase 3: Frontend (Sessie 5-6)

**Sessie 5: Site generator + design**
- Python HTML generator
- Hacker News-stijl CSS
- Twee views: chronologisch + prio-gesorteerd
- Kleurcodes voor urgentie
- Responsive design

**Sessie 6: Interactiviteit + polish**
- Client-side filtering (JS)
- Filter op: categorie, brontype, score-range, tags
- Zoekfunctie
- Keyboard shortcuts (j/k navigatie, o = open)
- Dark mode toggle

### Fase 4: Scraping & Deployment (Sessie 7-8)

**Sessie 7: Webscraping collectors**
- BeautifulSoup scrapers voor top-10 sites
- Configureerbaar per site (CSS selectors in YAML)
- Error handling en fallbacks
- Respecteer robots.txt

**Sessie 8: GitHub Actions + deployment**
- Workflow YAML: dagelijks 06:00 CET
- Secrets configureren (ANTHROPIC_API_KEY)
- Cache strategy (alleen nieuwe artikelen scoren)
- Monitoring: Slack/email alert bij build failure
- GitHub Pages configuratie

### Fase 5: Optimalisatie (Sessie 9-10)

**Sessie 9: Data management**
- Archivering (30 dagen actief, daarna archive/)
- Historische trends (welke thema's stijgen?)
- RSS output feed (zodat anderen kunnen subscriben)
- JSON API endpoint

**Sessie 10: Verfijning**
- Performance optimalisatie
- SEO basics
- Accessibility
- Documentatie (README + CLAUDE.md)
- Monitoring dashboard

---

## 8. CLAUDE.md (voor Claude Code)

Dit bestand komt in de repo root en instrueert Claude Code:

```markdown
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
- `python scripts/run_scorer.py` — Score met AI
- `python scripts/run_build.py` — Genereer site
- `python -m pytest tests/` — Run tests

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
```

---

## 9. Uniform Artikel Format

Elk artikel wordt genormaliseerd naar dit JSON-format:

```json
{
  "id": "sha256-hash-van-url",
  "url": "https://origineel-artikel.nl/...",
  "title": "Titel van het artikel",
  "summary": "Eerste 2-3 zinnen of RSS description",
  "published": "2025-03-03T08:00:00Z",
  "collected": "2025-03-03T06:00:00Z",
  "source": {
    "name": "Skipr",
    "type": "rss|api|scraper",
    "url": "https://skipr.nl"
  },
  "score": {
    "total": 87,
    "relevance": 35,
    "urgency": 28,
    "action_potential": 24,
    "scored_by": "claude-sonnet|fallback"
  },
  "category": "tender|concurrent|overheid|innovatie|markt|publicatie|patent",
  "tags": ["EPD", "AI/ML", "aanbesteding"],
  "action_hint": "Mogelijke tender-opportunity voor EPD-migratie project",
  "summary_nl": "UMC Utrecht zoekt partner voor nieuw MSZ-platform...",
  "priority": "critical|high|medium|low"
}
```

Priority mapping:
- 🔴 `critical`: score 80-100 (directe actie nodig)
- 🟠 `high`: score 60-79 (deze week bespreken)
- 🟡 `medium`: score 40-59 (goed om te weten)
- ⚪ `low`: score 0-39 (achtergrond)

---

## 10. Kosten & Resources

| Item | Kosten/maand | Toelichting |
|------|-------------|-------------|
| GitHub Pages | Gratis | Statische hosting |
| GitHub Actions | Gratis | <2000 min/maand bij 1x/dag |
| Claude API (Sonnet) | ~$9 | ~200 artikelen/dag scoring |
| **Totaal** | **~$9/maand** | |

---

## 11. Risico's & Mitigatie

| Risico | Impact | Mitigatie |
|--------|--------|----------|
| RSS feed gaat offline | Missende bron | Fallback + monitoring alert |
| Website layout verandert | Scraper breekt | Modulaire scrapers, makkelijk te fixen |
| Claude API down | Geen scoring | Fallback keyword-scorer |
| Te veel artikelen | Hoge API kosten | Rate limiting, dedup, max 300/dag |
| GitHub Actions limiet | Build faalt | Efficiënte pipeline (<10 min) |
| Copyright/scraping issues | Juridisch | Alleen titels + summaries, link naar bron |

---

## 12. Toekomstige uitbreidingen (v2+)

- **Email digest**: dagelijkse samenvatting van top-10 naar team
- **Slack integratie**: 🔴-items direct naar Slack channel
- **Trend analyse**: welke thema's stijgen/dalen over weken
- **Competitive intelligence dashboard**: wat doet concurrent X deze maand
- **Tender tracker**: specifieke tenders volgen tot deadline
- **Custom alerts**: "ping me bij alles over FHIR boven score 70"
- **Team annotaties**: collega's kunnen artikelen taggen/becommentariëren
- **Multi-taal**: ook internationale bronnen (HIMSS, EHTEL, etc.)

---

## 13. Eerste stap

Open Claude Code in de `FrankBrussaard/zorgnieuws` repo en geef deze prompt:

```
Lees CLAUDE.md. We bouwen Fase 1, Sessie 1:
- Maak de volledige repostructuur aan
- Implementeer BaseCollector class
- Implementeer RSSCollector
- Configureer de eerste 12 RSS feeds in feeds.yml
- Maak een simpele test die de collectors draait
- Genereer een basic index.html om de output te zien

Start met het opzetten van de structuur en de BaseCollector.
```
