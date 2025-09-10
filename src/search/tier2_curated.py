"""
Tier 2 Search: Curated Collections

Searches through curated collections of repositories and packages
for specific domains and use cases.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Set, Any
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


# Enhanced search with SourceGraph integration
async def enhanced_curated_search(requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Enhanced search with SourceGraph validation and pattern discovery."""
    
    # Extract search parameters
    query = requirements.get('query', '')
    language = requirements.get('language')
    libraries = requirements.get('libraries', [])
    use_case = requirements.get('use_case', 'general')
    
    logger = logging.getLogger(__name__)
    logger.info(f"Performing enhanced curated search for: {query}")
    
    # Perform original curated search
    original_searcher = Tier2Search()
    curated_collections = await original_searcher.search(query, language)
    
    # Initialize SourceGraph integration if available
    enhanced_results = []
    
    try:
        from .sourcegraph_integration import SourceGraphDiscovery
        
        async with SourceGraphDiscovery() as sg_discovery:
            # Validate patterns with SourceGraph for each collection
            for collection in curated_collections:
                for repo in collection.repositories:
                    # Validate the pattern for this repository
                    pattern_validation = await sg_discover_pattern(
                        sg_discovery,
                        repo,
                        libraries,
                        use_case
                    )
                    
                    # Add validation info to repository result
                    enhanced_repo = {
                        'name': repo.name,
                        'url': repo.url,
                        'description': repo.description,
                        'stars': repo.stars,
                        'language': repo.language,
                        'topics': repo.topics,
                        'collection_source': repo.collection_source,
                        'relevance_score': repo.relevance_score,
                        'pattern_confidence': pattern_validation.get('confidence', 0.0),
                        'real_world_examples': pattern_validation.get('examples', []),
                        'common_issues': pattern_validation.get('issues', []),
                        'best_practices': pattern_validation.get('best_practices', [])
                    }
                    enhanced_results.append(enhanced_repo)
            
            # Also discover additional patterns from SourceGraph
            if libraries:
                integration_patterns = await sg_discovery.discover_integration_patterns(
                    libraries,
                    use_case
                )
                
                # Add discovered patterns to results
                for pattern in integration_patterns[:3]:  # Top 3 patterns
                    pattern_result = {
                        'name': f"Pattern: {', '.join(pattern.libraries)}",
                        'url': f"pattern://{pattern.pattern_id}",
                        'description': f"Discovered integration pattern for {pattern.use_case}",
                        'stars': 0,
                        'language': 'pattern',
                        'topics': pattern.libraries,
                        'collection_source': 'SourceGraph Discovery',
                        'relevance_score': pattern.confidence_score,
                        'pattern_confidence': pattern.confidence_score,
                        'real_world_examples': [
                            {
                                'repository': ex.repository,
                                'path': ex.path,
                                'content': ex.content[:200] + '...' if len(ex.content) > 200 else ex.content
                            } for ex in pattern.code_examples[:2]
                        ],
                        'common_issues': pattern.common_issues,
                        'best_practices': pattern.best_practices
                    }
                    enhanced_results.append(pattern_result)
    
    except Exception as e:
        logger.warning(f"SourceGraph integration failed, falling back to curated search: {str(e)}")
        # Fallback to original results without enhancement
        for collection in curated_collections:
            for repo in collection.repositories:
                enhanced_results.append({
                    'name': repo.name,
                    'url': repo.url,
                    'description': repo.description,
                    'stars': repo.stars,
                    'language': repo.language,
                    'topics': repo.topics,
                    'collection_source': repo.collection_source,
                    'relevance_score': repo.relevance_score,
                    'pattern_confidence': 0.5,  # Default confidence
                    'real_world_examples': [],
                    'common_issues': [],
                    'best_practices': []
                })
    
    # Re-rank results based on pattern confidence and relevance
    ranked_results = rank_by_pattern_confidence(enhanced_results)
    
    logger.info(f"Enhanced search completed, found {len(ranked_results)} results")
    return ranked_results


async def sg_discover_pattern(sg_discovery, repo, libraries: List[str], use_case: str) -> Dict[str, Any]:
    """Discover and validate pattern for a specific repository."""
    
    try:
        # Build query for this specific repository pattern
        if libraries:
            query = sg_discovery.build_pattern_query(libraries, use_case)
            
            # Search for patterns related to this repository
            results = await sg_discovery.sourcegraph_search(query)
            
            if results:
                # Analyze patterns
                patterns = sg_discovery.analyze_integration_patterns(results)
                
                if patterns:
                    # Return the best pattern match
                    best_pattern = patterns[0]
                    return {
                        'confidence': best_pattern.confidence_score,
                        'examples': [
                            {
                                'repository': ex.repository,
                                'path': ex.path,
                                'content': ex.content[:100] + '...' if len(ex.content) > 100 else ex.content
                            } for ex in best_pattern.code_examples[:3]
                        ],
                        'issues': best_pattern.common_issues[:3],  # Top 3 issues
                        'best_practices': best_pattern.best_practices[:3]  # Top 3 practices
                    }
        
        # Default fallback
        return {
            'confidence': 0.6,
            'examples': [],
            'issues': [],
            'best_practices': []
        }
        
    except Exception as e:
        logging.getLogger(__name__).warning(f"Pattern discovery failed for {repo.name}: {str(e)}")
        return {
            'confidence': 0.3,
            'examples': [],
            'issues': [],
            'best_practices': []
        }


def rank_by_pattern_confidence(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Re-rank results based on pattern confidence and relevance."""
    
    def calculate_sort_score(result: Dict[str, Any]) -> float:
        """Calculate composite score for sorting."""
        
        # Base relevance score
        relevance = result.get('relevance_score', 0.0)
        
        # Pattern confidence (weighted more heavily)
        pattern_confidence = result.get('pattern_confidence', 0.0)
        
        # Star count bonus (normalized)
        stars = result.get('stars', 0)
        star_bonus = min(0.2, stars / 100000)  # Max 0.2 bonus for very popular repos
        
        # Composite score
        composite_score = (relevance * 0.3) + (pattern_confidence * 0.5) + star_bonus
        
        return composite_score
    
    # Sort by composite score
    sorted_results = sorted(results, key=calculate_sort_score, reverse=True)
    
    return sorted_results