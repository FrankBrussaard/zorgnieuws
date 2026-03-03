"""Collectors module for Zorgnieuws."""
from .base import BaseCollector, Article
from .rss_collector import RSSCollector
from .tenderned_collector import TenderNedCollector
from .overheid_collector import OverheidCollector

__all__ = [
    "BaseCollector",
    "Article",
    "RSSCollector",
    "TenderNedCollector",
    "OverheidCollector",
]
