"""
Tier 3: AI-Driven GitHub Discovery

Advanced repository discovery using AI analysis of project requirements
and intelligent GitHub API searches with quality filtering.
"""

import asyncio
import logging
import json
import aiohttp
import os
from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import re


@dataclass
class RepositoryInfo:
    """Information about a discovered repository."""
    
    name: str
    full_name: str
    description: str
    url: str
    clone_url: str
    language: str
    stars: int
    forks: int
    last_updated: str
    topics: List[str]
    license: Optional[str]
    size: int
    open_issues: int
    has_wiki: bool
    has_pages: bool
    archived: bool
    quality_score: float = 0.0
    relevance_score: float = 0.0


@dataclass
class DiscoveryResult:
    """Result from AI-driven repository discovery."""
    
    repositories: List[RepositoryInfo]
    search_query: str
    total_found: int
    search_strategy: str
    quality_threshold: float


class Tier3Search:
    """AI-driven GitHub repository discovery."""
    
    def __init__(self, github_token: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # GitHub API configuration
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.base_url = "https://api.github.com"
        
        # Quality thresholds
        self.min_stars = 10
        self.min_quality_score = 0.4
        self.max_age_days = 365 * 3  # 3 years
        
        # Search strategies
        self.search_strategies = [
            'keyword_search',
            'topic_search',
            'language_specific',
            'trending_search',
            'awesome_lists'
        ]
    
    async def discover_repositories(self, query: str, language: Optional[str] = None, 
                                  max_results: int = 20, quality_threshold: float = 0.4) -> List[RepositoryInfo]:
        """
        Discover repositories using AI-driven search strategies.
        
        Args:
            query: Project description or requirements
            language: Programming language preference
            max_results: Maximum number of repositories to return
            quality_threshold: Minimum quality score threshold
            
        Returns:
            List of discovered repositories with quality scores
        """
        
        self.logger.info(f"Discovering repositories for: {query}")
        
        all_repositories = []
        
        # Generate search queries using different strategies
        search_queries = self._generate_search_queries(query, language)
        
        for search_query in search_queries:
            try:
                repos = await self._search_github_repositories(search_query, max_results)
                all_repositories.extend(repos)
                
                # Add delay to respect rate limits
                await asyncio.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Search failed for query '{search_query}': {e}")
        
        # Remove duplicates
        unique_repos = self._deduplicate_repositories(all_repositories)
        
        # Calculate quality and relevance scores
        scored_repos = []
        for repo in unique_repos:
            quality_score = self._calculate_quality_score(repo)
            relevance_score = self._calculate_relevance_score(repo, query, language)
            
            repo.quality_score = quality_score
            repo.relevance_score = relevance_score
            
            if quality_score >= quality_threshold:
                scored_repos.append(repo)
        
        # Sort by combined score
        scored_repos.sort(key=lambda x: (x.quality_score * x.relevance_score), reverse=True)
        
        self.logger.info(f"Discovered {len(scored_repos)} quality repositories")
        
        return scored_repos[:max_results]
    
    def _generate_search_queries(self, query: str, language: Optional[str]) -> List[str]:
        """Generate multiple search queries from the original query."""
        
        queries = []
        
        # Extract keywords from query
        keywords = self._extract_keywords(query)
        
        # Basic keyword search
        queries.append(' '.join(keywords[:3]))
        
        # Language-specific search
        if language:
            queries.append(f"{' '.join(keywords[:2])} language:{language}")
            queries.append(f"{language} {' '.join(keywords[:2])}")
        
        # Topic-based searches
        topics = self._extract_topics(query)
        for topic in topics[:2]:
            queries.append(f"topic:{topic}")
        
        # Framework/library specific
        frameworks = self._extract_frameworks(query)
        for framework in frameworks:
            queries.append(f"{framework} {' '.join(keywords[:2])}")
        
        # Use case specific
        use_cases = self._extract_use_cases(query)
        for use_case in use_cases:
            queries.append(use_case)
        
        return queries[:8]  # Limit to avoid rate limits
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract relevant keywords from the query."""
        
        # Remove common stop words
        stop_words = {
            'create', 'build', 'make', 'develop', 'implement', 'design',
            'a', 'an', 'the', 'for', 'with', 'using', 'that', 'this',
            'and', 'or', 'but', 'in', 'on', 'at', 'to', 'from'
        }
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', query.lower())
        keywords = [word for word in words if word not in stop_words]
        
        return keywords
    
    def _extract_topics(self, query: str) -> List[str]:
        """Extract GitHub topics from the query."""
        
        topic_mappings = {
            'web': ['web', 'webapp', 'website'],
            'api': ['api', 'rest', 'graphql'],
            'cli': ['cli', 'command-line'],
            'scraping': ['web-scraping', 'scraper'],
            'machine-learning': ['machine-learning', 'ml', 'ai'],
            'data-science': ['data-science', 'data-analysis'],
            'framework': ['framework'],
            'library': ['library'],
            'tool': ['tool', 'utility'],
            'game': ['game', 'gaming'],
            'mobile': ['mobile', 'android', 'ios'],
            'desktop': ['desktop', 'gui']
        }
        
        query_lower = query.lower()
        topics = []
        
        for topic, keywords in topic_mappings.items():
            if any(keyword in query_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def _extract_frameworks(self, query: str) -> List[str]:
        """Extract framework names from the query."""
        
        frameworks = [
            'flask', 'django', 'fastapi', 'express', 'react', 'vue',
            'angular', 'spring', 'rails', 'laravel', 'symfony',
            'tensorflow', 'pytorch', 'scikit-learn', 'pandas',
            'numpy', 'matplotlib', 'opencv', 'requests', 'scrapy'
        ]
        
        query_lower = query.lower()
        found_frameworks = []
        
        for framework in frameworks:
            if framework in query_lower:
                found_frameworks.append(framework)
        
        return found_frameworks
    
    def _extract_use_cases(self, query: str) -> List[str]:
        """Extract use case patterns from the query."""
        
        use_case_patterns = {
            'web scraper': ['scraper', 'scraping', 'crawler'],
            'rest api': ['api', 'rest', 'backend'],
            'web app': ['web app', 'webapp', 'website'],
            'cli tool': ['cli', 'command line', 'terminal'],
            'data analysis': ['data analysis', 'analytics'],
            'machine learning': ['machine learning', 'ml', 'ai'],
            'game': ['game', 'gaming'],
            'mobile app': ['mobile', 'android', 'ios'],
            'desktop app': ['desktop', 'gui']
        }
        
        query_lower = query.lower()
        use_cases = []
        
        for use_case, patterns in use_case_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                use_cases.append(use_case)
        
        return use_cases
    
    async def _search_github_repositories(self, query: str, max_results: int) -> List[RepositoryInfo]:
        """Search GitHub repositories using the API."""
        
        if not self.github_token:
            self.logger.warning("No GitHub token provided, using unauthenticated requests")
        
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'AutoBot-Assembly-System'
        }
        
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'
        
        # Build search URL
        search_url = f"{self.base_url}/search/repositories"
        params = {
            'q': query,
            'sort': 'stars',
            'order': 'desc',
            'per_page': min(max_results, 100)
        }
        
        repositories = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for item in data.get('items', []):
                            repo_info = self._parse_repository_data(item)
                            if repo_info:
                                repositories.append(repo_info)
                    
                    elif response.status == 403:
                        self.logger.warning("GitHub API rate limit exceeded")
                    else:
                        self.logger.error(f"GitHub API error: {response.status}")
        
        except Exception as e:
            self.logger.error(f"Error searching GitHub: {e}")
        
        return repositories
    
    def _parse_repository_data(self, item: Dict[str, Any]) -> Optional[RepositoryInfo]:
        """Parse repository data from GitHub API response."""
        
        try:
            # Skip archived repositories
            if item.get('archived', False):
                return None
            
            # Skip repositories that are too old
            updated_at = datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00'))
            if (datetime.now().astimezone() - updated_at).days > self.max_age_days:
                return None
            
            # Skip repositories with too few stars
            if item.get('stargazers_count', 0) < self.min_stars:
                return None
            
            return RepositoryInfo(
                name=item['name'],
                full_name=item['full_name'],
                description=item.get('description', ''),
                url=item['html_url'],
                clone_url=item['clone_url'],
                language=item.get('language', ''),
                stars=item.get('stargazers_count', 0),
                forks=item.get('forks_count', 0),
                last_updated=item['updated_at'],
                topics=item.get('topics', []),
                license=item.get('license', {}).get('name') if item.get('license') else None,
                size=item.get('size', 0),
                open_issues=item.get('open_issues_count', 0),
                has_wiki=item.get('has_wiki', False),
                has_pages=item.get('has_pages', False),
                archived=item.get('archived', False)
            )
        
        except Exception as e:
            self.logger.error(f"Error parsing repository data: {e}")
            return None
    
    def _deduplicate_repositories(self, repositories: List[RepositoryInfo]) -> List[RepositoryInfo]:
        """Remove duplicate repositories from the list."""
        
        seen = set()
        unique_repos = []
        
        for repo in repositories:
            if repo.full_name not in seen:
                seen.add(repo.full_name)
                unique_repos.append(repo)
        
        return unique_repos
    
    def _calculate_quality_score(self, repo: RepositoryInfo) -> float:
        """Calculate quality score for a repository."""
        
        score = 0.0
        
        # Stars (normalized, max 50 points)
        star_score = min(repo.stars / 1000, 0.5)
        score += star_score
        
        # Forks (normalized, max 20 points)
        fork_score = min(repo.forks / 500, 0.2)
        score += fork_score
        
        # Recent activity (max 15 points)
        try:
            updated_at = datetime.fromisoformat(repo.last_updated.replace('Z', '+00:00'))
            days_since_update = (datetime.now().astimezone() - updated_at).days
            
            if days_since_update < 30:
                score += 0.15
            elif days_since_update < 90:
                score += 0.10
            elif days_since_update < 180:
                score += 0.05
        except:
            pass
        
        # Has documentation (max 10 points)
        if repo.has_wiki or repo.has_pages:
            score += 0.1
        
        # License (max 5 points)
        if repo.license:
            score += 0.05
        
        return min(score, 1.0)
    
    def _calculate_relevance_score(self, repo: RepositoryInfo, query: str, language: Optional[str]) -> float:
        """Calculate relevance score for a repository."""
        
        score = 0.0
        query_lower = query.lower()
        
        # Name relevance (max 30 points)
        name_words = repo.name.lower().split('-')
        query_words = query_lower.split()
        
        name_matches = sum(1 for word in query_words if any(word in name_word for name_word in name_words))
        if name_matches > 0:
            score += min(name_matches / len(query_words) * 0.3, 0.3)
        
        # Description relevance (max 25 points)
        if repo.description:
            desc_lower = repo.description.lower()
            desc_matches = sum(1 for word in query_words if word in desc_lower)
            if desc_matches > 0:
                score += min(desc_matches / len(query_words) * 0.25, 0.25)
        
        # Language match (max 20 points)
        if language and repo.language:
            if repo.language.lower() == language.lower():
                score += 0.2
        
        # Topics relevance (max 15 points)
        if repo.topics:
            topic_matches = sum(1 for word in query_words if any(word in topic for topic in repo.topics))
            if topic_matches > 0:
                score += min(topic_matches / len(query_words) * 0.15, 0.15)
        
        # Popularity bonus (max 10 points)
        if repo.stars > 100:
            score += min(0.1, repo.stars / 10000)
        
        return min(score, 1.0)


# Example usage and testing
async def test_tier3_search():
    """Test the Tier 3 AI-driven repository discovery."""
    
    tier3 = Tier3Search()
    
    test_queries = [
        ("python web scraper", "python"),
        ("react todo app", "javascript"),
        ("cli tool file processing", "python"),
        ("machine learning image classification", "python"),
        ("rest api authentication", "python")
    ]
    
    for query, language in test_queries:
        print(f"\n=== Discovering: '{query}' (Language: {language}) ===")
        
        repositories = await tier3.discover_repositories(query, language, max_results=5)
        
        for i, repo in enumerate(repositories, 1):
            print(f"\n{i}. {repo.name}")
            print(f"   Full Name: {repo.full_name}")
            print(f"   Description: {repo.description[:80]}...")
            print(f"   Language: {repo.language}")
            print(f"   Stars: {repo.stars}, Forks: {repo.forks}")
            print(f"   Quality: {repo.quality_score:.2f}")
            print(f"   Relevance: {repo.relevance_score:.2f}")
            print(f"   Topics: {', '.join(repo.topics[:3])}")


if __name__ == "__main__":
    asyncio.run(test_tier3_search())