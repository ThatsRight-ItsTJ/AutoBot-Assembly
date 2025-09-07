"""
Search Orchestrator

Coordinates all three tiers of search to provide comprehensive
resource discovery for project requirements.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass

from ..search.tier1_packages import PackageSearcher, PackageResult
from ..search.tier2_curated import CuratedSearcher, CuratedCollection
from ..search.tier3_discovery import GitHubDiscoverer, DiscoveredRepository


@dataclass
class SearchResults:
    """Consolidated search results from all tiers."""
    packages: List[PackageResult]
    curated_collections: List[CuratedCollection]
    discovered_repositories: List[DiscoveredRepository]
    total_results: int
    search_duration: float


class SearchOrchestrator:
    """Orchestrates multi-tier search across packages, collections, and repositories."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize search components
        self.package_searcher = PackageSearcher()
        self.curated_searcher = CuratedSearcher()
        self.github_discoverer = GitHubDiscoverer()
    
    async def orchestrate_search(
        self,
        project_name: str,
        language: str,
        components: List[str],
        max_results_per_tier: int = 10
    ) -> SearchResults:
        """
        Orchestrate comprehensive search across all tiers.
        
        Args:
            project_name: Name/description of the project
            language: Primary programming language
            components: List of required components/features
            max_results_per_tier: Maximum results per search tier
            
        Returns:
            SearchResults: Consolidated results from all search tiers
        """
        import time
        start_time = time.time()
        
        self.logger.info(f"Starting orchestrated search for: {project_name}")
        self.logger.info(f"Language: {language}, Components: {components}")
        
        # Prepare search queries
        search_queries = self._prepare_search_queries(project_name, components)
        
        # Execute all search tiers concurrently
        search_tasks = [
            self._search_tier1_packages(search_queries, language, max_results_per_tier),
            self._search_tier2_curated(search_queries, language, max_results_per_tier),
            self._search_tier3_github(search_queries, language, max_results_per_tier)
        ]
        
        try:
            tier1_results, tier2_results, tier3_results = await asyncio.gather(
                *search_tasks, return_exceptions=True
            )
            
            # Handle any exceptions
            packages = tier1_results if isinstance(tier1_results, list) else []
            collections = tier2_results if isinstance(tier2_results, list) else []
            repositories = tier3_results if isinstance(tier3_results, list) else []
            
        except Exception as e:
            self.logger.error(f"Error during orchestrated search: {e}")
            packages, collections, repositories = [], [], []
        
        # Calculate total results and duration
        total_results = len(packages) + len(collections) + len(repositories)
        search_duration = time.time() - start_time
        
        self.logger.info(f"Search completed in {search_duration:.2f}s")
        self.logger.info(f"Results: {len(packages)} packages, {len(collections)} collections, {len(repositories)} repos")
        
        return SearchResults(
            packages=packages,
            curated_collections=collections,
            discovered_repositories=repositories,
            total_results=total_results,
            search_duration=search_duration
        )
    
    def _prepare_search_queries(self, project_name: str, components: List[str]) -> List[str]:
        """Prepare optimized search queries from project requirements."""
        queries = []
        
        # Add project name as primary query
        queries.append(project_name)
        
        # Add component-based queries
        for component in components[:5]:  # Limit to top 5 components
            queries.append(component)
        
        # Add combined queries for better results
        if len(components) >= 2:
            combined = " ".join(components[:2])
            queries.append(combined)
        
        return list(set(queries))  # Remove duplicates
    
    async def _search_tier1_packages(
        self, 
        queries: List[str], 
        language: str, 
        max_results: int
    ) -> List[PackageResult]:
        """Search Tier 1: Package ecosystems."""
        self.logger.info("Executing Tier 1: Package ecosystem search")
        
        all_packages = []
        
        for query in queries[:3]:  # Limit queries to prevent overload
            try:
                packages = await self.package_searcher.search_packages(query, language)
                all_packages.extend(packages)
            except Exception as e:
                self.logger.warning(f"Tier 1 search failed for '{query}': {e}")
        
        # Remove duplicates and limit results
        seen_names = set()
        unique_packages = []
        
        for package in all_packages:
            if package.name not in seen_names:
                seen_names.add(package.name)
                unique_packages.append(package)
                
                if len(unique_packages) >= max_results:
                    break
        
        self.logger.info(f"Tier 1 found {len(unique_packages)} unique packages")
        return unique_packages
    
    async def _search_tier2_curated(
        self, 
        queries: List[str], 
        language: str, 
        max_results: int
    ) -> List[CuratedCollection]:
        """Search Tier 2: Curated collections."""
        self.logger.info("Executing Tier 2: Curated collections search")
        
        all_collections = []
        
        async with self.curated_searcher:
            for query in queries[:2]:  # Limit queries
                try:
                    collections = await self.curated_searcher.search_collections(query, language)
                    all_collections.extend(collections)
                except Exception as e:
                    self.logger.warning(f"Tier 2 search failed for '{query}': {e}")
        
        # Remove duplicates and limit results
        seen_names = set()
        unique_collections = []
        
        for collection in all_collections:
            if collection.name not in seen_names:
                seen_names.add(collection.name)
                unique_collections.append(collection)
                
                if len(unique_collections) >= max_results:
                    break
        
        self.logger.info(f"Tier 2 found {len(unique_collections)} unique collections")
        return unique_collections
    
    async def _search_tier3_github(
        self, 
        queries: List[str], 
        language: str, 
        max_results: int
    ) -> List[DiscoveredRepository]:
        """Search Tier 3: GitHub discovery."""
        self.logger.info("Executing Tier 3: GitHub repository discovery")
        
        all_repositories = []
        
        async with self.github_discoverer:
            for query in queries[:2]:  # Limit queries
                try:
                    repositories = await self.github_discoverer.discover_repositories(query, language)
                    all_repositories.extend(repositories)
                except Exception as e:
                    self.logger.warning(f"Tier 3 search failed for '{query}': {e}")
        
        # Remove duplicates and limit results
        seen_names = set()
        unique_repositories = []
        
        for repo in all_repositories:
            if repo.name not in seen_names:
                seen_names.add(repo.name)
                unique_repositories.append(repo)
                
                if len(unique_repositories) >= max_results:
                    break
        
        self.logger.info(f"Tier 3 found {len(unique_repositories)} unique repositories")
        return unique_repositories
    
    async def get_search_summary(self, results: SearchResults) -> Dict:
        """Generate a summary of search results."""
        return {
            'total_results': results.total_results,
            'search_duration': f"{results.search_duration:.2f}s",
            'breakdown': {
                'packages': len(results.packages),
                'curated_collections': len(results.curated_collections),
                'github_repositories': len(results.discovered_repositories)
            },
            'top_packages': [pkg.name for pkg in results.packages[:5]],
            'top_repositories': [repo.name for repo in results.discovered_repositories[:5]]
        }