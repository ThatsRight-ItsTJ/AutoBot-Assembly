"""
Tiered Search System

Three-tier search strategy for discovering GitHub repositories:
- Tier 1: Package ecosystem search (PyPI, NPM, Maven, etc.)
- Tier 2: Curated collections (GitHub Topics, Awesome Lists)
- Tier 3: Live GitHub discovery with AI-generated queries
"""

from .tier1_packages import Tier1Search, PackageResult
from .tier2_curated import Tier2Search, RepositoryResult
from .tier3_discovery import Tier3Search, SearchResult

__all__ = [
    'Tier1Search', 'PackageResult',
    'Tier2Search', 'RepositoryResult', 
    'Tier3Search', 'SearchResult'
]