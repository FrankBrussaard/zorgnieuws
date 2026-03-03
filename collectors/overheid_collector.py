"""Overheid.nl API collector for Zorgnieuws."""
from datetime import datetime, timezone, timedelta
from typing import Optional
import requests
import xml.etree.ElementTree as ET

from .base import BaseCollector, Article


class OverheidCollector(BaseCollector):
    """Collector for Overheid.nl official publications API."""

    # Zoektermen voor zorg-gerelateerde documenten
    ZORG_KEYWORDS = [
        "zorg", "volksgezondheid", "VWS", "ziekenhuis", "GGZ",
        "eHealth", "EPD", "digitalisering zorg", "medisch",
        "Wet langdurige zorg", "Zorgverzekeringswet", "NZa",
        "IGJ", "RIVM", "zorgsector",
    ]

    def __init__(self, days_back: int = 7):
        super().__init__(name="overheid", source_type="api")
        self.base_url = "https://zoek.officielebekendmakingen.nl"
        self.days_back = days_back

    def _search_documents(self, keyword: str) -> list[dict]:
        """Search for documents with keyword."""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=self.days_back)

        # SRU (Search/Retrieve via URL) API
        params = {
            "query": f'(dt.modified>={start_date.strftime("%Y-%m-%d")}) AND "{keyword}"',
            "maximumRecords": 20,
            "operation": "searchRetrieve",
            "version": "1.2",
            "recordSchema": "gzd",
        }

        try:
            response = requests.get(
                f"{self.base_url}/sru/Search",
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            return self._parse_sru_response(response.text)
        except requests.RequestException as e:
            print(f"  Overheid.nl API error for '{keyword}': {e}")
            return []

    def _parse_sru_response(self, xml_text: str) -> list[dict]:
        """Parse SRU XML response."""
        documents = []

        try:
            # Remove namespaces for easier parsing
            xml_text = xml_text.replace(' xmlns="', ' xmlns_="')

            root = ET.fromstring(xml_text)

            # Find all records
            for record in root.iter():
                if "record" in record.tag.lower():
                    doc = self._extract_document(record)
                    if doc:
                        documents.append(doc)

        except ET.ParseError as e:
            print(f"  XML parse error: {e}")

        return documents

    def _extract_document(self, record: ET.Element) -> Optional[dict]:
        """Extract document info from record element."""
        doc = {}

        def find_text(element: ET.Element, tag_partial: str) -> str:
            for child in element.iter():
                if tag_partial.lower() in child.tag.lower():
                    return child.text or ""
            return ""

        doc["title"] = find_text(record, "title")
        doc["identifier"] = find_text(record, "identifier")
        doc["date"] = find_text(record, "modified") or find_text(record, "date")
        doc["type"] = find_text(record, "type")
        doc["creator"] = find_text(record, "creator")
        doc["description"] = find_text(record, "description")

        if doc["title"] and doc["identifier"]:
            return doc
        return None

    def _parse_document(self, doc: dict) -> Optional[Article]:
        """Parse document into Article format."""
        try:
            identifier = doc.get("identifier", "")

            # Build URL from identifier
            if identifier.startswith("http"):
                url = identifier
            else:
                url = f"https://zoek.officielebekendmakingen.nl/{identifier}"

            title = doc.get("title", "Geen titel")
            doc_type = doc.get("type", "Document")

            # Parse date
            date_str = doc.get("date", "")
            if date_str:
                try:
                    published = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except ValueError:
                    published = datetime.now(timezone.utc)
            else:
                published = datetime.now(timezone.utc)

            # Build summary
            creator = doc.get("creator", "")
            description = doc.get("description", "")

            summary_parts = []
            if creator:
                summary_parts.append(f"Van: {creator}")
            if doc_type:
                summary_parts.append(f"Type: {doc_type}")
            if description:
                summary_parts.append(description[:200])

            summary = " | ".join(summary_parts) if summary_parts else "Officiële publicatie"

            # Determine category based on type
            category = "overheid"
            if "kamerstuk" in doc_type.lower():
                category = "kamerstuk"
            elif "staatscourant" in doc_type.lower():
                category = "staatscourant"

            return Article(
                url=url,
                title=title,
                summary=summary,
                published=published,
                source_name="Officiële Bekendmakingen",
                source_type="api",
                source_url="https://www.officielebekendmakingen.nl",
                collected=self.collected_at,
                category=category,
                tags=["overheid", "beleid"],
            )
        except Exception as e:
            print(f"  Error parsing document: {e}")
            return None

    def collect(self) -> list[Article]:
        """Collect healthcare-related government publications."""
        articles = []
        seen_urls = set()

        print(f"Collecting from Overheid.nl API (last {self.days_back} days)...")

        for keyword in self.ZORG_KEYWORDS[:5]:  # Limit keywords to avoid rate limiting
            docs = self._search_documents(keyword)

            for doc in docs:
                article = self._parse_document(doc)
                if article and article.url not in seen_urls:
                    seen_urls.add(article.url)
                    articles.append(article)

        print(f"  Collected {len(articles)} government documents")
        return articles
