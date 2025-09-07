"""
Tier 2 Search: Curated Collections

Searches through curated collections of repositories and packages
for specific domains and use cases.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from enum import Enum

import aiohttp


class CollectionType(Enum):
    """Types of curated collections."""
    AWESOME_LIST = "awesome_list"
    TOPIC_COLLECTION = "topic_collection"
    FRAMEWORK_ECOSYSTEM = "framework_ecosystem"
    DOMAIN_SPECIFIC = "domain_specific"


@dataclass
class RepositoryResult:
    """Repository result from curated collections."""
    name: str
    url: str
    description: str
    stars: int
    language: str
    topics: List[str]
    collection_source: str
    relevance_score: float = 0.0


@dataclass
class CuratedCollection:
    """Curated collection information."""
    name: str
    url: str
    description: str
    collection_type: CollectionType
    repositories: List[RepositoryResult]
    total_repositories: int
    last_updated: Optional[str] = None


class CuratedSearcher:
    """Searches curated collections for relevant repositories."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Curated collection sources
        self.collections = {
            'web_scraping': [
                {
                    'name': 'Awesome Web Scraping',
                    'url': 'https://github.com/lorien/awesome-web-scraping',
                    'type': CollectionType.AWESOME_LIST,
                    'keywords': ['scraping', 'crawler', 'spider', 'parser']
                },
                {
                    'name': 'Awesome Python Web Scraping',
                    'url': 'https://github.com/REMitchell/python-scraping',
                    'type': CollectionType.DOMAIN_SPECIFIC,
                    'keywords': ['beautifulsoup', 'scrapy', 'selenium', 'requests']
                }
            ],
            'api_development': [
                {
                    'name': 'Awesome REST API',
                    'url': 'https://github.com/marmelab/awesome-rest',
                    'type': CollectionType.AWESOME_LIST,
                    'keywords': ['rest', 'api', 'fastapi', 'flask']
                },
                {
                    'name': 'FastAPI Ecosystem',
                    'url': 'https://github.com/mjhea0/awesome-fastapi',
                    'type': CollectionType.FRAMEWORK_ECOSYSTEM,
                    'keywords': ['fastapi', 'pydantic', 'uvicorn', 'starlette']
                }
            ],
            'machine_learning': [
                {
                    'name': 'Awesome Machine Learning',
                    'url': 'https://github.com/josephmisiti/awesome-machine-learning',
                    'type': CollectionType.AWESOME_LIST,
                    'keywords': ['ml', 'ai', 'tensorflow', 'pytorch', 'scikit-learn']
                }
            ],
            'data_processing': [
                {
                    'name': 'Awesome Data Science',
                    'url': 'https://github.com/academic/awesome-datascience',
                    'type': CollectionType.AWESOME_LIST,
                    'keywords': ['pandas', 'numpy', 'data', 'analytics']
                }
            ]
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'AutoBot-Assembly/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _calculate_relevance_score(self, query: str, repo: Dict) -> float:
        """Calculate relevance score for a repository."""
        query_lower = query.lower()
        score = 0.0
        
        # Name match
        if query_lower in repo.get('name', '').lower():
            score += 0.4
        
        # Description match
        description = repo.get('description', '').lower()
        query_words = query_lower.split()
        for word in query_words:
            if word in description:
                score += 0.2
        
        # Topics match
        topics = repo.get('topics', [])
        for topic in topics:
            if any(word in topic.lower() for word in query_words):
                score += 0.1
        
        # Star count bonus (normalized)
        stars = repo.get('stars', 0)
        if stars > 1000:
            score += 0.1
        elif stars > 100:
            score += 0.05
        
        return min(1.0, score)
    
    async def search_collections(self, query: str, language: Optional[str] = None) -> List[CuratedCollection]:
        """Search curated collections for relevant repositories."""
        self.logger.info(f"Searching curated collections for: {query}")
        
        results = []
        query_lower = query.lower()
        
        # Find relevant collection categories
        relevant_categories = []
        for category, collections in self.collections.items():
            for collection in collections:
                if any(keyword in query_lower for keyword in collection['keywords']):
                    relevant_categories.append((category, collection))
        
        # If no specific matches, use general categories
        if not relevant_categories:
            for category in ['web_scraping', 'api_development']:
                if category in self.collections:
                    relevant_categories.extend([(category, col) for col in self.collections[category]])
        
        # Generate mock repositories for each relevant collection
        for category, collection_info in relevant_categories[:4]:  # Limit to 4 collections
            mock_repos = await self._generate_mock_repositories(
                query, collection_info, language
            )
            
            collection = CuratedCollection(
                name=collection_info['name'],
                url=collection_info['url'],
                description=f"Curated collection of {category.replace('_', ' ')} resources",
                collection_type=collection_info['type'],
                repositories=mock_repos,
                total_repositories=len(mock_repos),
                last_updated="2024-12-19"
            )
            
            results.append(collection)
        
        self.logger.info(f"Found {len(results)} relevant curated collections")
        return results
    
    async def _generate_mock_repositories(
        self, 
        query: str, 
        collection_info: Dict, 
        language: Optional[str]
    ) -> List[RepositoryResult]:
        """Generate mock repositories for a collection."""
        
        # Mock repository data based on collection type and query
        mock_repos = []
        
        if 'scraping' in query.lower() or 'scraper' in query.lower():
            mock_repos = [
                {
                    'name': 'scrapy',
                    'description': 'A fast high-level web crawling and web scraping framework',
                    'stars': 52000,
                    'language': 'Python',
                    'topics': ['web-scraping', 'crawler', 'spider']
                },
                {
                    'name': 'beautifulsoup4',
                    'description': 'Screen-scraping library for Python',
                    'stars': 13000,
                    'language': 'Python',
                    'topics': ['html-parser', 'web-scraping', 'xml-parser']
                },
                {
                    'name': 'selenium',
                    'description': 'Web browser automation',
                    'stars': 30000,
                    'language': 'Python',
                    'topics': ['automation', 'browser', 'testing']
                }
            ]
        elif 'api' in query.lower() or 'rest' in query.lower():
            mock_repos = [
                {
                    'name': 'fastapi',
                    'description': 'Modern, fast web framework for building APIs with Python',
                    'stars': 75000,
                    'language': 'Python',
                    'topics': ['api', 'fastapi', 'async', 'web-framework']
                },
                {
                    'name': 'flask-restful',
                    'description': 'Simple framework for creating REST APIs',
                    'stars': 6800,
                    'language': 'Python',
                    'topics': ['flask', 'rest-api', 'web-framework']
                }
            ]
        elif 'news' in query.lower() or 'aggregator' in query.lower():
            mock_repos = [
                {
                    'name': 'feedparser',
                    'description': 'Parse RSS and Atom feeds in Python',
                    'stars': 1900,
                    'language': 'Python',
                    'topics': ['rss', 'atom', 'feed-parser']
                },
                {
                    'name': 'newspaper3k',
                    'description': 'News, full-text, and article metadata extraction',
                    'stars': 14000,
                    'language': 'Python',
                    'topics': ['news', 'article-extraction', 'nlp']
                }
            ]
        else:
            # Generic repositories
            mock_repos = [
                {
                    'name': 'requests',
                    'description': 'HTTP library for Python',
                    'stars': 52000,
                    'language': 'Python',
                    'topics': ['http', 'requests', 'api-client']
                },
                {
                    'name': 'aiohttp',
                    'description': 'Async HTTP client/server framework',
                    'stars': 15000,
                    'language': 'Python',
                    'topics': ['async', 'http', 'web-framework']
                }
            ]
        
        # Filter by language if specified
        if language:
            mock_repos = [repo for repo in mock_repos if repo['language'].lower() == language.lower()]
        
        # Convert to RepositoryResult objects
        results = []
        for repo in mock_repos:
            relevance_score = self._calculate_relevance_score(query, repo)
            
            result = RepositoryResult(
                name=repo['name'],
                url=f"https://github.com/example/{repo['name']}",
                description=repo['description'],
                stars=repo['stars'],
                language=repo['language'],
                topics=repo['topics'],
                collection_source=collection_info['name'],
                relevance_score=relevance_score
            )
            results.append(result)
        
        # Sort by relevance score
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return results[:5]  # Return top 5 most relevant


class Tier2Search:
    """Tier 2 search implementation."""
    
    def __init__(self):
        self.searcher = CuratedSearcher()
    
    async def search(self, query: str, language: Optional[str] = None) -> List[CuratedCollection]:
        """Perform tier 2 search."""
        async with self.searcher:
            return await self.searcher.search_collections(query, language)


# For backward compatibility
async def search_curated_collections(query: str, language: Optional[str] = None) -> List[CuratedCollection]:
    """Search curated collections (backward compatibility function)."""
    searcher = Tier2Search()
    return await searcher.search(query, language)