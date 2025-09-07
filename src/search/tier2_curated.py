"""
Tier 2: Curated Collections Search

Search through curated collections of high-quality repositories
organized by use case, framework, and domain expertise.
"""

import asyncio
import logging
import json
import aiohttp
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CuratedCollection:
    """Represents a curated collection of repositories."""
    
    name: str
    description: str
    category: str
    repositories: List[str]  # GitHub repo URLs
    maintainer: str
    last_updated: str
    tags: List[str]
    quality_score: float = 0.0


@dataclass
class CollectionResult:
    """Result from curated collection search."""
    
    collection: CuratedCollection
    relevance_score: float
    matching_repos: List[str]
    reason: str


class Tier2Search:
    """Curated collections search implementation."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Load curated collections
        self.collections = self._load_curated_collections()
        
        # Category mappings
        self.category_keywords = {
            'web_frameworks': ['web', 'framework', 'api', 'server', 'http', 'rest'],
            'data_science': ['data', 'analysis', 'machine learning', 'ai', 'ml', 'pandas', 'numpy'],
            'cli_tools': ['cli', 'command line', 'terminal', 'script', 'automation'],
            'mobile_development': ['mobile', 'android', 'ios', 'react native', 'flutter'],
            'game_development': ['game', 'gaming', 'unity', 'pygame', 'graphics'],
            'security': ['security', 'encryption', 'auth', 'authentication', 'vulnerability'],
            'devops': ['docker', 'kubernetes', 'ci/cd', 'deployment', 'infrastructure'],
            'testing': ['test', 'testing', 'unit test', 'integration', 'qa']
        }
    
    def _load_curated_collections(self) -> List[CuratedCollection]:
        """Load curated collections from various sources."""
        
        collections = []
        
        # Add built-in curated collections
        collections.extend(self._get_builtin_collections())
        
        # TODO: Load from external sources (awesome lists, etc.)
        
        return collections
    
    def _get_builtin_collections(self) -> List[CuratedCollection]:
        """Get built-in curated collections."""
        
        return [
            CuratedCollection(
                name="Python Web Frameworks",
                description="Popular and well-maintained Python web frameworks",
                category="web_frameworks",
                repositories=[
                    "https://github.com/pallets/flask",
                    "https://github.com/django/django",
                    "https://github.com/tiangolo/fastapi",
                    "https://github.com/encode/starlette",
                    "https://github.com/huge-success/sanic"
                ],
                maintainer="AutoBot Curators",
                last_updated="2024-01-01",
                tags=["python", "web", "framework", "api"],
                quality_score=0.95
            ),
            
            CuratedCollection(
                name="JavaScript Frontend Libraries",
                description="Essential JavaScript libraries for frontend development",
                category="web_frameworks",
                repositories=[
                    "https://github.com/facebook/react",
                    "https://github.com/vuejs/vue",
                    "https://github.com/angular/angular",
                    "https://github.com/sveltejs/svelte",
                    "https://github.com/alpinejs/alpine"
                ],
                maintainer="AutoBot Curators",
                last_updated="2024-01-01",
                tags=["javascript", "frontend", "ui", "framework"],
                quality_score=0.98
            ),
            
            CuratedCollection(
                name="Data Science Essentials",
                description="Core libraries for data science and machine learning",
                category="data_science",
                repositories=[
                    "https://github.com/pandas-dev/pandas",
                    "https://github.com/numpy/numpy",
                    "https://github.com/scikit-learn/scikit-learn",
                    "https://github.com/matplotlib/matplotlib",
                    "https://github.com/jupyter/notebook"
                ],
                maintainer="AutoBot Curators",
                last_updated="2024-01-01",
                tags=["python", "data", "science", "ml", "analysis"],
                quality_score=0.97
            ),
            
            CuratedCollection(
                name="CLI Development Tools",
                description="Tools and libraries for building command-line applications",
                category="cli_tools",
                repositories=[
                    "https://github.com/pallets/click",
                    "https://github.com/google/python-fire",
                    "https://github.com/tiangolo/typer",
                    "https://github.com/spf13/cobra",
                    "https://github.com/urfave/cli"
                ],
                maintainer="AutoBot Curators",
                last_updated="2024-01-01",
                tags=["cli", "command", "terminal", "python", "go"],
                quality_score=0.92
            ),
            
            CuratedCollection(
                name="Web Scraping Tools",
                description="Libraries and tools for web scraping and data extraction",
                category="data_science",
                repositories=[
                    "https://github.com/psf/requests",
                    "https://github.com/scrapy/scrapy",
                    "https://github.com/MechanicalSoup/MechanicalSoup",
                    "https://github.com/codelucas/newspaper",
                    "https://github.com/binux/pyspider"
                ],
                maintainer="AutoBot Curators",
                last_updated="2024-01-01",
                tags=["python", "scraping", "web", "data", "extraction"],
                quality_score=0.89
            ),
            
            CuratedCollection(
                name="Testing Frameworks",
                description="Popular testing frameworks across different languages",
                category="testing",
                repositories=[
                    "https://github.com/pytest-dev/pytest",
                    "https://github.com/facebook/jest",
                    "https://github.com/rspec/rspec",
                    "https://github.com/junit-team/junit5",
                    "https://github.com/stretchr/testify"
                ],
                maintainer="AutoBot Curators",
                last_updated="2024-01-01",
                tags=["testing", "framework", "unit", "integration"],
                quality_score=0.94
            )
        ]
    
    async def search_curated_collections(self, query: str, language: Optional[str] = None, max_results: int = 10) -> List[CollectionResult]:
        """
        Search through curated collections for relevant repositories.
        
        Args:
            query: Search query describing the project requirements
            language: Programming language preference
            max_results: Maximum number of results to return
            
        Returns:
            List of relevant curated collections with matching repositories
        """
        
        self.logger.info(f"Searching curated collections for: {query}")
        
        query_lower = query.lower()
        results = []
        
        for collection in self.collections:
            relevance_score = self._calculate_collection_relevance(collection, query_lower, language)
            
            if relevance_score > 0.3:  # Minimum relevance threshold
                matching_repos = self._get_matching_repositories(collection, query_lower)
                
                result = CollectionResult(
                    collection=collection,
                    relevance_score=relevance_score,
                    matching_repos=matching_repos,
                    reason=self._generate_match_reason(collection, query_lower)
                )
                
                results.append(result)
        
        # Sort by relevance score and quality
        results.sort(key=lambda x: (x.relevance_score * x.collection.quality_score), reverse=True)
        
        self.logger.info(f"Found {len(results)} relevant collections")
        
        return results[:max_results]
    
    def _calculate_collection_relevance(self, collection: CuratedCollection, query: str, language: Optional[str]) -> float:
        """Calculate how relevant a collection is to the query."""
        
        score = 0.0
        
        # Check name and description
        if any(word in collection.name.lower() for word in query.split()):
            score += 0.4
        
        if any(word in collection.description.lower() for word in query.split()):
            score += 0.3
        
        # Check tags
        query_words = set(query.split())
        tag_words = set(' '.join(collection.tags).lower().split())
        
        if query_words & tag_words:
            score += 0.3
        
        # Check category keywords
        for category, keywords in self.category_keywords.items():
            if collection.category == category:
                if any(keyword in query for keyword in keywords):
                    score += 0.2
                    break
        
        # Language preference bonus
        if language and language.lower() in ' '.join(collection.tags).lower():
            score += 0.2
        
        return min(score, 1.0)
    
    def _get_matching_repositories(self, collection: CuratedCollection, query: str) -> List[str]:
        """Get repositories from the collection that match the query."""
        
        # For now, return all repositories in relevant collections
        # TODO: Implement more sophisticated repository filtering
        return collection.repositories
    
    def _generate_match_reason(self, collection: CuratedCollection, query: str) -> str:
        """Generate a reason why this collection matches the query."""
        
        reasons = []
        
        # Check what matched
        if any(word in collection.name.lower() for word in query.split()):
            reasons.append(f"Collection name matches '{collection.name}'")
        
        if any(word in collection.description.lower() for word in query.split()):
            reasons.append("Description contains relevant keywords")
        
        query_words = set(query.split())
        tag_words = set(' '.join(collection.tags).lower().split())
        
        if query_words & tag_words:
            matching_tags = query_words & tag_words
            reasons.append(f"Tags match: {', '.join(matching_tags)}")
        
        if not reasons:
            reasons.append("Category relevance")
        
        return "; ".join(reasons)
    
    async def get_collection_details(self, collection_name: str) -> Optional[CuratedCollection]:
        """Get detailed information about a specific collection."""
        
        for collection in self.collections:
            if collection.name.lower() == collection_name.lower():
                return collection
        
        return None
    
    def get_available_categories(self) -> List[str]:
        """Get list of available collection categories."""
        
        return list(set(collection.category for collection in self.collections))
    
    async def get_collections_by_category(self, category: str) -> List[CuratedCollection]:
        """Get all collections in a specific category."""
        
        return [
            collection for collection in self.collections
            if collection.category.lower() == category.lower()
        ]


# Example usage and testing
async def test_tier2_search():
    """Test the Tier 2 curated collections search."""
    
    tier2 = Tier2Search()
    
    test_queries = [
        ("web framework python", "python"),
        ("machine learning data analysis", "python"),
        ("cli tool development", None),
        ("web scraping", "python"),
        ("testing framework", "javascript")
    ]
    
    for query, language in test_queries:
        print(f"\n=== Searching: '{query}' (Language: {language}) ===")
        
        results = await tier2.search_curated_collections(query, language, max_results=3)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.collection.name}")
            print(f"   Category: {result.collection.category}")
            print(f"   Relevance: {result.relevance_score:.2f}")
            print(f"   Quality: {result.collection.quality_score:.2f}")
            print(f"   Repositories: {len(result.matching_repos)}")
            print(f"   Reason: {result.reason}")
            
            # Show first few repositories
            for repo in result.matching_repos[:2]:
                repo_name = repo.split('/')[-1]
                print(f"   - {repo_name}")


if __name__ == "__main__":
    asyncio.run(test_tier2_search())