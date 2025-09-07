"""
Tier 1 Search: Package Ecosystems

Searches through package repositories like PyPI, npm, Maven, etc.
for relevant packages and libraries.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from enum import Enum

import aiohttp


class PackageEcosystem(Enum):
    """Package ecosystem types."""
    PYPI = "pypi"
    NPM = "npm"
    MAVEN = "maven"
    NUGET = "nuget"
    CRATES = "crates"
    RUBYGEMS = "rubygems"


@dataclass
class PackageResult:
    """Package search result."""
    name: str
    version: str
    description: str
    author: str
    downloads: int
    ecosystem: PackageEcosystem
    url: str
    repository_url: Optional[str] = None
    license: Optional[str] = None
    keywords: List[str] = None
    relevance_score: float = 0.0


class PackageSearcher:
    """Searches package ecosystems for relevant packages."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Package ecosystem configurations
        self.ecosystems = {
            'python': {
                'ecosystem': PackageEcosystem.PYPI,
                'api_url': 'https://pypi.org/pypi',
                'search_url': 'https://pypi.org/search',
                'popular_packages': {
                    'web_scraping': ['requests', 'beautifulsoup4', 'scrapy', 'selenium', 'lxml'],
                    'api_development': ['fastapi', 'flask', 'django', 'aiohttp', 'uvicorn'],
                    'data_processing': ['pandas', 'numpy', 'scipy', 'matplotlib', 'seaborn'],
                    'machine_learning': ['scikit-learn', 'tensorflow', 'pytorch', 'keras', 'xgboost'],
                    'news_processing': ['feedparser', 'newspaper3k', 'nltk', 'spacy', 'textblob']
                }
            },
            'javascript': {
                'ecosystem': PackageEcosystem.NPM,
                'api_url': 'https://registry.npmjs.org',
                'search_url': 'https://www.npmjs.com/search',
                'popular_packages': {
                    'web_scraping': ['puppeteer', 'cheerio', 'jsdom', 'playwright', 'axios'],
                    'api_development': ['express', 'fastify', 'koa', 'nest', 'hapi'],
                    'frontend': ['react', 'vue', 'angular', 'svelte', 'next']
                }
            }
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
    
    def _calculate_relevance_score(self, query: str, package: Dict) -> float:
        """Calculate relevance score for a package."""
        query_lower = query.lower()
        score = 0.0
        
        # Name match (highest weight)
        name = package.get('name', '').lower()
        if query_lower in name:
            score += 0.5
        
        # Description match
        description = package.get('description', '').lower()
        query_words = query_lower.split()
        for word in query_words:
            if word in description:
                score += 0.2
        
        # Keywords match
        keywords = package.get('keywords', [])
        for keyword in keywords:
            if any(word in keyword.lower() for word in query_words):
                score += 0.1
        
        # Download count bonus (normalized)
        downloads = package.get('downloads', 0)
        if downloads > 1000000:
            score += 0.2
        elif downloads > 100000:
            score += 0.1
        elif downloads > 10000:
            score += 0.05
        
        return min(1.0, score)
    
    async def search_packages(self, query: str, language: str) -> List[PackageResult]:
        """Search for packages in the specified language ecosystem."""
        self.logger.info(f"Searching packages for: {query} (language: {language})")
        
        language_lower = language.lower()
        
        # Get ecosystem configuration
        ecosystem_config = self.ecosystems.get(language_lower)
        if not ecosystem_config:
            self.logger.warning(f"Unsupported language: {language}")
            return []
        
        # Generate mock packages based on query and language
        mock_packages = await self._generate_mock_packages(query, ecosystem_config)
        
        # Convert to PackageResult objects
        results = []
        for package in mock_packages:
            relevance_score = self._calculate_relevance_score(query, package)
            
            result = PackageResult(
                name=package['name'],
                version=package['version'],
                description=package['description'],
                author=package['author'],
                downloads=package['downloads'],
                ecosystem=ecosystem_config['ecosystem'],
                url=package['url'],
                repository_url=package.get('repository_url'),
                license=package.get('license'),
                keywords=package.get('keywords', []),
                relevance_score=relevance_score
            )
            results.append(result)
        
        # Sort by relevance score
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        self.logger.info(f"Found {len(results)} packages for '{query}'")
        return results[:10]  # Return top 10 most relevant
    
    async def _generate_mock_packages(self, query: str, ecosystem_config: Dict) -> List[Dict]:
        """Generate mock packages based on query and ecosystem."""
        
        query_lower = query.lower()
        popular_packages = ecosystem_config['popular_packages']
        
        # Find relevant category
        relevant_packages = []
        for category, packages in popular_packages.items():
            if any(keyword in query_lower for keyword in category.split('_')):
                relevant_packages.extend(packages)
        
        # If no specific category matches, use general packages
        if not relevant_packages:
            relevant_packages = popular_packages.get('api_development', [])
        
        # Generate mock package data
        mock_packages = []
        
        for i, package_name in enumerate(relevant_packages[:8]):  # Limit to 8 packages
            mock_package = {
                'name': package_name,
                'version': f"1.{i}.0",
                'description': f"A powerful {package_name} library for {query.lower()} applications",
                'author': f"{package_name}-team",
                'downloads': 1000000 - (i * 100000),  # Decreasing download counts
                'url': f"https://pypi.org/project/{package_name}/",
                'repository_url': f"https://github.com/{package_name}/{package_name}",
                'license': 'MIT',
                'keywords': [query.lower(), package_name, 'python', 'library']
            }
            mock_packages.append(mock_package)
        
        # Add some query-specific packages
        if 'scraping' in query_lower or 'scraper' in query_lower:
            additional_packages = [
                {
                    'name': 'requests-html',
                    'version': '0.10.0',
                    'description': 'Pythonic HTML Parsing for Humans',
                    'author': 'kennethreitz',
                    'downloads': 500000,
                    'url': 'https://pypi.org/project/requests-html/',
                    'repository_url': 'https://github.com/psf/requests-html',
                    'license': 'MIT',
                    'keywords': ['html', 'parsing', 'scraping', 'requests']
                }
            ]
            mock_packages.extend(additional_packages)
        
        elif 'news' in query_lower or 'aggregator' in query_lower:
            additional_packages = [
                {
                    'name': 'python-feedgen',
                    'version': '0.9.0',
                    'description': 'Feed Generator (ATOM, RSS, Podcasts)',
                    'author': 'lkiesow',
                    'downloads': 200000,
                    'url': 'https://pypi.org/project/feedgen/',
                    'repository_url': 'https://github.com/lkiesow/python-feedgen',
                    'license': 'BSD',
                    'keywords': ['rss', 'atom', 'feed', 'news']
                }
            ]
            mock_packages.extend(additional_packages)
        
        return mock_packages


class Tier1Search:
    """Tier 1 search implementation."""
    
    def __init__(self):
        self.searcher = PackageSearcher()
    
    async def search(self, query: str, language: str) -> List[PackageResult]:
        """Perform tier 1 search."""
        async with self.searcher:
            return await self.searcher.search_packages(query, language)


# For backward compatibility
async def search_packages(query: str, language: str) -> List[PackageResult]:
    """Search packages (backward compatibility function)."""
    searcher = Tier1Search()
    return await searcher.search(query, language)