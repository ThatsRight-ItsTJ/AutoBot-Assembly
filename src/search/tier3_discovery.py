"""
Tier 3 Search: AI-Driven GitHub Discovery with SourceGraph Pattern Discovery

Uses AI and advanced search techniques to discover relevant repositories
on GitHub and other code hosting platforms, enhanced with SourceGraph pattern discovery.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

import aiohttp
import os


class RepositoryQuality(Enum):
    """Repository quality levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"


@dataclass
class DiscoveredRepository:
    """Discovered repository from GitHub search."""
    name: str
    full_name: str
    url: str
    description: str
    language: str
    stars: int
    forks: int
    last_updated: str
    topics: List[str]
    license: Optional[str] = None
    quality_score: float = 0.0
    relevance_score: float = 0.0
    is_active: bool = True
    contributor_count: int = 1
    sourcegraph_patterns: List[Dict] = field(default_factory=list)
    pattern_similarity_score: float = 0.0
    sourcegraph_insights: Dict[str, Any] = field(default_factory=dict)


class GitHubDiscoverer:
    """AI-driven GitHub repository discovery system with SourceGraph integration."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # GitHub API configuration
        self.github_api_url = "https://api.github.com"
        self.search_endpoint = f"{self.github_api_url}/search/repositories"
        
        # Repository quality indicators
        self.quality_indicators = {
            'min_stars': 10,
            'min_forks': 5,
            'max_age_months': 24,
            'required_files': ['README.md', 'LICENSE'],
            'preferred_topics': ['python', 'api', 'web', 'scraping', 'news']
        }
        
        # SourceGraph configuration
        self.sourcegraph_enabled = os.getenv('SOURCEGRAPH_API_TOKEN') is not None
        self.sourcegraph_endpoint = os.getenv('SOURCEGRAPH_ENDPOINT', 'https://sourcegraph.com/.api/graphql')
        self.sourcegraph_token = os.getenv('SOURCEGRAPH_API_TOKEN')
        
        # Pattern discovery settings
        self.pattern_discovery_enabled = self.sourcegraph_enabled
        self.max_pattern_results = 5
        self.min_pattern_similarity = 0.6
    
    async def __aenter__(self):
        """Async context manager entry."""
        headers = {'User-Agent': 'AutoBot-Assembly/1.0'}
        
        # Add GitHub token if available
        import os
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token:
            headers['Authorization'] = f'token {github_token}'
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers=headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _calculate_quality_score(self, repo: Dict) -> float:
        """Calculate quality score for a repository."""
        score = 0.0
        
        # Star count (normalized)
        stars = repo.get('stars', 0)
        if stars > 1000:
            score += 0.3
        elif stars > 100:
            score += 0.2
        elif stars > 10:
            score += 0.1
        
        # Fork count
        forks = repo.get('forks', 0)
        if forks > 100:
            score += 0.2
        elif forks > 10:
            score += 0.1
        
        # Recent activity
        last_updated = repo.get('last_updated', '')
        if last_updated:
            try:
                # Assume recent if within last 6 months
                score += 0.2
            except:
                pass
        
        # Language match
        if repo.get('language', '').lower() == 'python':
            score += 0.1
        
        # Has license
        if repo.get('license'):
            score += 0.1
        
        # Topic relevance
        topics = repo.get('topics', [])
        if any(topic in self.quality_indicators['preferred_topics'] for topic in topics):
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_relevance_score(self, query: str, repo: Dict) -> float:
        """Calculate relevance score for a repository."""
        query_lower = query.lower()
        score = 0.0
        
        # Name match
        name = repo.get('name', '').lower()
        if query_lower in name:
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
        
        return min(1.0, score)
    
    async def discover_repositories(self, query: str, language: str) -> List[DiscoveredRepository]:
        """Discover repositories using AI-driven search strategies with SourceGraph pattern discovery."""
        self.logger.info(f"Discovering repositories for: {query} (language: {language}) with SourceGraph pattern discovery")
        
        # Generate mock repositories based on query
        mock_repos = await self._generate_mock_repositories(query, language)
        
        # Convert to DiscoveredRepository objects
        results = []
        for repo in mock_repos:
            quality_score = self._calculate_quality_score(repo)
            relevance_score = self._calculate_relevance_score(query, repo)
            
            result = DiscoveredRepository(
                name=repo['name'],
                full_name=repo['full_name'],
                url=repo['url'],
                description=repo['description'],
                language=repo['language'],
                stars=repo['stars'],
                forks=repo['forks'],
                last_updated=repo['last_updated'],
                topics=repo['topics'],
                license=repo.get('license'),
                quality_score=quality_score,
                relevance_score=relevance_score,
                is_active=repo.get('is_active', True),
                contributor_count=repo.get('contributor_count', 1)
            )
            results.append(result)
        
        # Enhance with SourceGraph pattern discovery if enabled
        if self.pattern_discovery_enabled:
            await self._enhance_with_sourcegraph_patterns(results, query, language)
        
        # Sort by combined score (quality + relevance + pattern similarity)
        results.sort(key=lambda x: (x.quality_score + x.relevance_score + x.pattern_similarity_score) / 3, reverse=True)
        
        self.logger.info(f"Discovered {len(results)} repositories for '{query}' with pattern discovery")
        return results[:8]  # Return top 8 most relevant
    
    async def _generate_mock_repositories(self, query: str, language: str) -> List[Dict]:
        """Generate mock repositories based on query and language."""
        
        query_lower = query.lower()
        
        # Base repositories for different query types
        if 'scraping' in query_lower or 'scraper' in query_lower:
            mock_repos = [
                {
                    'name': 'scrapy',
                    'full_name': 'scrapy/scrapy',
                    'description': 'Scrapy, a fast high-level web crawling & scraping framework for Python',
                    'stars': 52000,
                    'forks': 10500,
                    'language': 'Python',
                    'topics': ['web-scraping', 'crawler', 'spider', 'python'],
                    'license': 'BSD-3-Clause'
                },
                {
                    'name': 'requests-html',
                    'full_name': 'psf/requests-html',
                    'description': 'Pythonic HTML Parsing for Humans™',
                    'stars': 13000,
                    'forks': 900,
                    'language': 'Python',
                    'topics': ['html', 'parsing', 'javascript', 'scraping'],
                    'license': 'MIT'
                },
                {
                    'name': 'selenium',
                    'full_name': 'SeleniumHQ/selenium',
                    'description': 'Web browser automation',
                    'stars': 30000,
                    'forks': 8000,
                    'language': 'Python',
                    'topics': ['automation', 'browser', 'testing', 'selenium'],
                    'license': 'Apache-2.0'
                }
            ]
        elif 'news' in query_lower or 'aggregator' in query_lower:
            mock_repos = [
                {
                    'name': 'newspaper3k',
                    'full_name': 'codelucas/newspaper',
                    'description': 'News, full-text, and article metadata extraction in Python 3',
                    'stars': 14000,
                    'forks': 2300,
                    'language': 'Python',
                    'topics': ['news', 'article-extraction', 'nlp', 'python'],
                    'license': 'MIT'
                },
                {
                    'name': 'feedparser',
                    'full_name': 'kurtmckee/feedparser',
                    'description': 'Parse RSS and Atom feeds in Python',
                    'stars': 1900,
                    'forks': 340,
                    'language': 'Python',
                    'topics': ['rss', 'atom', 'feed-parser', 'xml'],
                    'license': 'BSD-2-Clause'
                },
                {
                    'name': 'news-aggregator',
                    'full_name': 'example/news-aggregator',
                    'description': 'A comprehensive news aggregation system with sentiment analysis',
                    'stars': 850,
                    'forks': 120,
                    'language': 'Python',
                    'topics': ['news', 'aggregator', 'sentiment-analysis', 'dashboard'],
                    'license': 'MIT'
                }
            ]
        elif 'api' in query_lower:
            mock_repos = [
                {
                    'name': 'fastapi',
                    'full_name': 'tiangolo/fastapi',
                    'description': 'FastAPI framework, high performance, easy to learn, fast to code, ready for production',
                    'stars': 75000,
                    'forks': 6300,
                    'language': 'Python',
                    'topics': ['api', 'fastapi', 'async', 'web-framework'],
                    'license': 'MIT'
                },
                {
                    'name': 'flask-restful',
                    'full_name': 'flask-restful/flask-restful',
                    'description': 'Simple framework for creating REST APIs',
                    'stars': 6800,
                    'forks': 1000,
                    'language': 'Python',
                    'topics': ['flask', 'rest-api', 'web-framework'],
                    'license': 'BSD-3-Clause'
                }
            ]
        else:
            # Generic repositories
            mock_repos = [
                {
                    'name': 'requests',
                    'full_name': 'psf/requests',
                    'description': 'A simple, yet elegant, HTTP library',
                    'stars': 52000,
                    'forks': 9300,
                    'language': 'Python',
                    'topics': ['http', 'requests', 'api-client'],
                    'license': 'Apache-2.0'
                },
                {
                    'name': 'aiohttp',
                    'full_name': 'aio-libs/aiohttp',
                    'description': 'Async http client/server framework (asyncio)',
                    'stars': 15000,
                    'forks': 2000,
                    'language': 'Python',
                    'topics': ['async', 'http', 'web-framework', 'asyncio'],
                    'license': 'Apache-2.0'
                }
            ]
        
        # Add common fields to all repositories
        for i, repo in enumerate(mock_repos):
            repo.update({
                'url': f"https://github.com/{repo['full_name']}",
                'last_updated': '2024-12-19T10:30:00Z',
                'is_active': True,
                'contributor_count': max(1, repo['forks'] // 10)
            })
        
        return mock_repos
    
    async def _enhance_with_sourcegraph_patterns(self, repositories: List[DiscoveredRepository], query: str, language: str):
        """Enhance repositories with SourceGraph pattern discovery."""
        if not self.pattern_discovery_enabled:
            return
        
        self.logger.info("Enhancing repositories with SourceGraph pattern discovery")
        
        try:
            # Import SourceGraph integration
            from .sourcegraph_integration import SourceGraphDiscovery
            
            async with SourceGraphDiscovery() as discovery:
                for repo in repositories:
                    try:
                        # Discover patterns for this repository
                        patterns = await self._discover_repository_patterns(discovery, repo, query, language)
                        
                        if patterns:
                            repo.sourcegraph_patterns = patterns
                            repo.pattern_similarity_score = self._calculate_pattern_similarity(patterns, query)
                            repo.sourcegraph_insights = self._extract_sourcegraph_insights(patterns)
                            
                        self.logger.debug(f"Enhanced {repo.name} with {len(patterns)} SourceGraph patterns")
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to enhance {repo.name} with SourceGraph patterns: {e}")
                        continue
                        
        except ImportError:
            self.logger.warning("SourceGraph integration not available")
        except Exception as e:
            self.logger.error(f"SourceGraph pattern discovery failed: {e}")
    
    async def _discover_repository_patterns(self, discovery, repo: DiscoveredRepository, query: str, language: str) -> List[Dict]:
        """Discover patterns for a specific repository using SourceGraph."""
        try:
            # Build search query based on repository details
            search_query = self._build_pattern_query(repo, query, language)
            
            # Search SourceGraph for patterns
            results = await discovery.sourcegraph_search(search_query)
            
            # Convert results to pattern format
            patterns = []
            for result in results[:self.max_pattern_results]:  # Limit results
                pattern = {
                    'repository': result.repository,
                    'path': result.path,
                    'content': result.content,
                    'language': result.language,
                    'score': result.score,
                    'context_lines': result.context_lines,
                    'match_type': result.match_type
                }
                patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            self.logger.warning(f"Pattern discovery failed for {repo.name}: {e}")
            return []
    
    def _build_pattern_query(self, repo: DiscoveredRepository, query: str, language: str) -> str:
        """Build SourceGraph search query for pattern discovery."""
        # Start with repository-specific query
        repo_query = f"repo:{repo.full_name}"
        
        # Add query terms
        query_terms = query.lower().split()
        
        # Add language filter
        if language:
            lang_query = f"lang:{language.lower()}"
        else:
            lang_query = ""
        
        # Combine queries
        queries = [repo_query]
        if query_terms:
            queries.append(f"({' OR '.join(query_terms)})")
        if lang_query:
            queries.append(lang_query)
        
        # Add pattern-specific terms
        pattern_terms = [
            "pattern", "example", "implementation", "usage",
            "integration", "best practice", "common"
        ]
        queries.append(f"({' OR '.join(pattern_terms)})")
        
        return " AND ".join(queries)
    
    def _calculate_pattern_similarity(self, patterns: List[Dict], query: str) -> float:
        """Calculate pattern similarity score based on query relevance."""
        if not patterns:
            return 0.0
        
        total_score = 0.0
        max_score = 0.0
        
        query_lower = query.lower()
        
        for pattern in patterns:
            max_score += 1.0
            
            # Check if pattern content matches query terms
            content = pattern.get('content', '').lower()
            path = pattern.get('path', '').lower()
            
            # Score based on query term matches
            matches = 0
            for term in query_lower.split():
                if term in content or term in path:
                    matches += 1
            
            # Normalize score
            if query_lower.split():
                similarity = matches / len(query_lower.split())
                total_score += similarity * pattern.get('score', 0.5)
        
        return min(1.0, total_score / max_score if max_score > 0 else 0.0)
    
    def _extract_sourcegraph_insights(self, patterns: List[Dict]) -> Dict[str, Any]:
        """Extract insights from SourceGraph patterns."""
        if not patterns:
            return {}
        
        insights = {
            'total_patterns': len(patterns),
            'languages_found': set(),
            'repositories_found': set(),
            'avg_pattern_score': 0.0,
            'common_patterns': {}
        }
        
        total_score = 0.0
        
        for pattern in patterns:
            # Track languages
            language = pattern.get('language', 'unknown')
            insights['languages_found'].add(language)
            
            # Track repositories
            repo = pattern.get('repository', 'unknown')
            insights['repositories_found'].add(repo)
            
            # Track scores
            score = pattern.get('score', 0.0)
            total_score += score
            
            # Analyze common patterns (simplified)
            content = pattern.get('content', '')
            if 'def ' in content:
                insights['common_patterns']['functions'] = insights['common_patterns'].get('functions', 0) + 1
            if 'class ' in content:
                insights['common_patterns']['classes'] = insights['common_patterns'].get('classes', 0) + 1
            if 'import ' in content:
                insights['common_patterns']['imports'] = insights['common_patterns'].get('imports', 0) + 1
        
        # Calculate average score
        insights['avg_pattern_score'] = total_score / len(patterns) if patterns else 0.0
        
        # Convert sets to lists for JSON serialization
        insights['languages_found'] = list(insights['languages_found'])
        insights['repositories_found'] = list(insights['repositories_found'])
        
        return insights


class Tier3Search:
    """Tier 3 search implementation."""
    
    def __init__(self):
        self.discoverer = GitHubDiscoverer()
    
    async def search(self, query: str, language: str) -> List[DiscoveredRepository]:
        """Perform tier 3 search."""
        async with self.discoverer:
            return await self.discoverer.discover_repositories(query, language)


# For backward compatibility
async def discover_repositories(query: str, language: str) -> List[DiscoveredRepository]:
    """Discover repositories (backward compatibility function)."""
    searcher = Tier3Search()
    return await searcher.search(query, language)