"""
Search Module

Multi-tier search system for discovering packages, repositories, and resources.
"""

from .tier1_packages import PackageSearcher, PackageResult
from .tier2_curated import CuratedSearcher, CuratedCollection, RepositoryResult
from .tier3_discovery import GitHubDiscoverer, DiscoveredRepository

__all__ = [
    'PackageSearcher',
    'PackageResult',
    'CuratedSearcher', 
    'CuratedCollection',
    'RepositoryResult',
    'GitHubDiscoverer',
    'DiscoveredRepository'
]