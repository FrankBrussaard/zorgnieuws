"""TenderNed API collector for Zorgnieuws."""
from datetime import datetime, timezone, timedelta
from typing import Optional
import requests

from .base import BaseCollector, Article


class TenderNedCollector(BaseCollector):
    """Collector for TenderNed public procurement API."""

    # CPV codes relevant voor zorg
    ZORG_CPV_CODES = [
        "33",      # Medische apparatuur
        "48",      # Software
        "72",      # IT-diensten
        "85",      # Gezondheids- en maatschappelijke diensten
        "79",      # Zakelijke diensten (consultancy)
    ]

    # Zoektermen voor zorg-gerelateerde tenders
    ZORG_KEYWORDS = [
        "zorg", "ziekenhuis", "GGZ", "EPD", "ECD", "medisch",
        "healthcare", "eHealth", "digitalisering", "ICT",
        "software", "informatiesysteem", "patiënt", "cliënt",
        "UMC", "huisarts", "apotheek", "verpleeg", "thuiszorg",
        "jeugdzorg", "WMO", "WLZ", "gezondheidszorg", "klinisch",
        "laboratorium", "radiologie", "farma", "revalidatie",
        "RIVM", "volksgezondheid", "GGD", "sample", "collectie",
    ]

    # Bekende zorg-opdrachtgevers
    ZORG_OPDRACHTGEVERS = [
        "RIVM", "UMC", "ziekenhuis", "GGZ", "zorg", "health",
        "medisch", "GGD", "ZonMw", "NZa", "IGJ", "Erasmus MC",
        "Radboud", "LUMC", "UMCG", "VUmc", "AMC",
    ]

    def __init__(self, days_back: int = 7):
        super().__init__(name="tenderned", source_type="api")
        self.base_url = "https://www.tenderned.nl/papi/tenderned-rs-tns/v2"
        self.days_back = days_back

    def _search_tenders(self, page: int = 0, size: int = 50) -> dict:
        """Search for recent tenders."""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=self.days_back)

        params = {
            "publicatieDatumVanaf": start_date.strftime("%Y-%m-%d"),
            "publicatieDatumTot": end_date.strftime("%Y-%m-%d"),
            "page": page,
            "size": size,
            "sort": "publicatieDatum,desc",
        }

        try:
            response = requests.get(
                f"{self.base_url}/publicaties",
                params=params,
                timeout=30,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"  TenderNed API error: {e}")
            return {"content": []}

    def _is_zorg_relevant(self, tender: dict) -> bool:
        """Check if tender is relevant for healthcare sector."""
        # Check title and description for keywords
        title = tender.get("aanbestedingNaam", "").lower()
        beschrijving = tender.get("opdrachtBeschrijving", "").lower()
        opdrachtgever = tender.get("opdrachtgeverNaam", "").lower()

        text = f"{title} {beschrijving} {opdrachtgever}"

        # Check zorg keywords in text
        for keyword in self.ZORG_KEYWORDS:
            if keyword.lower() in text:
                return True

        # Check known zorg opdrachtgevers
        for org in self.ZORG_OPDRACHTGEVERS:
            if org.lower() in opdrachtgever:
                return True

        return False

    def _parse_tender(self, tender: dict) -> Optional[Article]:
        """Parse tender data into Article format."""
        try:
            tender_id = tender.get("publicatieId", "")

            # Use direct link if available, otherwise construct URL
            link_data = tender.get("link", {})
            if isinstance(link_data, dict) and link_data.get("href"):
                url = link_data["href"]
            else:
                url = f"https://www.tenderned.nl/aankondigingen/overzicht/{tender_id}"

            title = tender.get("aanbestedingNaam", "Geen titel")
            beschrijving = tender.get("opdrachtBeschrijving", "")

            # Parse publication date
            pub_date_str = tender.get("publicatieDatum")
            if pub_date_str:
                # Handle date-only string
                if "T" not in pub_date_str:
                    pub_date_str = f"{pub_date_str}T00:00:00+00:00"
                published = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
            else:
                published = datetime.now(timezone.utc)

            # Get metadata
            opdrachtgever = tender.get("opdrachtgeverNaam", "")
            type_opdracht = tender.get("typeOpdracht", {})
            type_omschrijving = type_opdracht.get("omschrijving", "") if isinstance(type_opdracht, dict) else ""
            procedure = tender.get("procedure", {})
            procedure_omschrijving = procedure.get("omschrijving", "") if isinstance(procedure, dict) else ""

            # Build summary
            summary_parts = []
            if opdrachtgever:
                summary_parts.append(f"Opdrachtgever: {opdrachtgever}")
            if type_omschrijving:
                summary_parts.append(f"Type: {type_omschrijving}")
            if procedure_omschrijving:
                summary_parts.append(f"Procedure: {procedure_omschrijving}")
            if beschrijving:
                summary_parts.append(beschrijving[:250])

            summary = " | ".join(summary_parts) if summary_parts else "Geen beschrijving"

            return Article(
                url=url,
                title=f"TENDER: {title}",
                summary=summary,
                published=published,
                source_name="TenderNed",
                source_type="api",
                source_url="https://www.tenderned.nl",
                collected=self.collected_at,
                category="tender",
                tags=["aanbesteding", type_omschrijving] if type_omschrijving else ["aanbesteding"],
            )
        except Exception as e:
            print(f"  Error parsing tender: {e}")
            return None

    def collect(self) -> list[Article]:
        """Collect healthcare-related tenders from TenderNed."""
        articles = []

        print(f"Collecting from TenderNed API (last {self.days_back} days)...")

        # Fetch tenders
        page = 0
        total_fetched = 0
        max_pages = 5

        while page < max_pages:
            result = self._search_tenders(page=page)
            tenders = result.get("content", [])

            if not tenders:
                break

            total_fetched += len(tenders)

            for tender in tenders:
                if self._is_zorg_relevant(tender):
                    article = self._parse_tender(tender)
                    if article:
                        articles.append(article)

            # Check if more pages
            total_pages = result.get("totalPages", 1)
            if page >= total_pages - 1:
                break

            page += 1

        print(f"  Fetched {total_fetched} tenders, {len(articles)} zorg-relevant")
        return articles
