"""
Tier 2: Curated Collections Search

Discovers community-vetted implementations from GitHub Topics and Awesome Lists.
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime

import aiohttp
from github import Github


@dataclass
class RepositoryResult:
    name: str
    full_name: str
    url: str
    description: str
    stars: int
    forks: int
    language: str
    topics: List[str]
    last_updated: datetime
    license: str
    size: int
    open_issues: int
    quality_score: float
    source: str  # 'github_topics' or 'awesome_lists'
    relevance_score: float


class Tier2Search:
    """Search GitHub topics and awesome lists for curated components."""
    
    def __init__(self, github_token: Optional[str] = None):
        self.github_client = Github(github_token) if github_token else Github()
        self.logger = logging.getLogger(__name__)
        self.awesome_lists_cache = {}
        
    async def search_curated(self, search_targets: Dict[str, List[str]], language: str) -> List[RepositoryResult]:
        """
        Search GitHub topics and awesome lists for curated repositories.
        
        Args:
            search_targets: Dict mapping components to search keywords
            language: Target programming language
            
        Returns:
            List of RepositoryResult objects
        """
        results = []
        
        # Search GitHub Topics
        topics_results = await self._search_github_topics(search_targets, language)
        results.extend(topics_results)
        
        # Search Awesome Lists
        awesome_results = await self._search_awesome_lists(search_targets, language)
        results.extend(awesome_results)
        
        # Deduplicate and rank results
        unique_results = self._deduplicate_results(results)
        ranked_results = self._rank_by_relevance(unique_results, search_targets)
        
        return ranked_results
    
    async def _search_github_topics(self, search_targets: Dict[str, List[str]], language: str) -> List[RepositoryResult]:
        """Search GitHub repositories by topics."""
        results = []
        
        for component, keywords in search_targets.items():
            for keyword in keywords:
                try:
                    # Create search query
                    query_parts = [
                        f"topic:{keyword.replace(' ', '-')}",
                        f"language:{language}",
                        "stars:>20",
                        "pushed:>2023-01-01"
                    ]
                    query = " ".join(query_parts)
                    
                    # Search repositories
                    repositories = self.github_client.search_repositories(
                        query=query,
                        sort="stars",
                        order="desc"
                    )
                    
                    # Process results
                    for repo in repositories[:10]:  # Limit to top 10 per keyword
                        result = self._create_repository_result(repo, "github_topics", keyword)
                        if result:
                            results.append(result)
                            
                except Exception as e:
                    self.logger.error(f"Error searching GitHub topics for {keyword}: {e}")
                    continue
        
        return results
    
    async def _search_awesome_lists(self, search_targets: Dict[str, List[str]], language: str) -> List[RepositoryResult]:
        """Search awesome lists for relevant repositories."""
        results = []
        
        # Get relevant awesome lists
        awesome_lists = await self._get_relevant_awesome_lists(language)
        
        for awesome_list in awesome_lists:
            try:
                # Get awesome list content
                content = await self._get_awesome_list_content(awesome_list)
                
                # Extract repository URLs
                repo_urls = self._extract_repository_urls(content)
                
                # Filter repositories by relevance to search targets
                relevant_repos = self._filter_relevant_repositories(repo_urls, search_targets)
                
                # Get repository details
                for repo_url in relevant_repos[:5]:  # Limit per awesome list
                    try:
                        repo = self.github_client.get_repo(self._extract_repo_name(repo_url))
                        result = self._create_repository_result(repo, "awesome_lists", awesome_list)
                        if result:
                            results.append(result)
                    except Exception as e:
                        self.logger.error(f"Error getting repo details for {repo_url}: {e}")
                        continue
                        
            except Exception as e:
                self.logger.error(f"Error processing awesome list {awesome_list}: {e}")
                continue
        
        return results
    
    async def _get_relevant_awesome_lists(self, language: str) -> List[str]:
        """Get list of awesome lists relevant to the language."""
        awesome_lists = {
            'python': [
                'vinta/awesome-python',
                'kirang89/pycrumbs',
                'svaksha/pythonidae'
            ],
            'javascript': [
                'sorrycc/awesome-javascript',
                'sindresorhus/awesome-nodejs',
                'enaqx/awesome-react'
            ],
            'java': [
                'akullpp/awesome-java',
                'Vedenin/useful-java-links'
            ],
            'go': [
                'avelino/awesome-go',
                'golang/go/wiki'
            ],
            'rust': [
                'rust-unofficial/awesome-rust'
            ],
            'cpp': [
                'fffaraz/awesome-cpp'
            ]
        }
        
        return awesome_lists.get(language.lower(), [])
    
    async def _get_awesome_list_content(self, awesome_list: str) -> str:
        """Get the content of an awesome list README."""
        try:
            repo = self.github_client.get_repo(awesome_list)
            readme = repo.get_readme()
            return readme.decoded_content.decode('utf-8')
        except Exception as e:
            self.logger.error(f"Error getting awesome list content for {awesome_list}: {e}")
            return ""
    
    def _extract_repository_urls(self, content: str) -> List[str]:
        """Extract GitHub repository URLs from awesome list content."""
        # Regex pattern to match GitHub repository URLs
        pattern = r'https://github\.com/([^/\s]+/[^/\s\)]+)'
        matches = re.findall(pattern, content)
        
        # Clean and deduplicate URLs
        urls = []
        seen = set()
        
        for match in matches:
            # Remove trailing punctuation and whitespace
            clean_match = re.sub(r'[^\w\-/].*$', '', match)
            if clean_match not in seen and len(clean_match.split('/')) == 2:
                seen.add(clean_match)
                urls.append(f"https://github.com/{clean_match}")
        
        return urls
    
    def _filter_relevant_repositories(self, repo_urls: List[str], search_targets: Dict[str, List[str]]) -> List[str]:
        """Filter repositories based on relevance to search targets."""
        relevant_repos = []
        
        # Create set of all search keywords
        all_keywords = set()
        for keywords in search_targets.values():
            all_keywords.update(keyword.lower() for keyword in keywords)
        
        for url in repo_urls:
            repo_name = url.split('/')[-1].lower()
            repo_owner = url.split('/')[-2].lower()
            
            # Check if repository name or owner contains any keywords
            for keyword in all_keywords:
                if keyword in repo_name or keyword in repo_owner:
                    relevant_repos.append(url)
                    break
        
        return relevant_repos
    
    def _extract_repo_name(self, repo_url: str) -> str:
        """Extract owner/repo format from GitHub URL."""
        parts = repo_url.replace('https://github.com/', '').split('/')
        return f"{parts[0]}/{parts[1]}"
    
    def _create_repository_result(self, repo, source: str, search_term: str) -> Optional[RepositoryResult]:
        """Create RepositoryResult from GitHub repository object."""
        try:
            return RepositoryResult(
                name=repo.name,
                full_name=repo.full_name,
                url=repo.html_url,
                description=repo.description or "",
                stars=repo.stargazers_count,
                forks=repo.forks_count,
                language=repo.language or "Unknown",
                topics=repo.get_topics(),
                last_updated=repo.updated_at,
                license=repo.license.name if repo.license else "Unknown",
                size=repo.size,
                open_issues=repo.open_issues_count,
                quality_score=self._calculate_quality_score(repo),
                source=source,
                relevance_score=self._calculate_relevance_score(repo, search_term)
            )
        except Exception as e:
            self.logger.error(f"Error creating repository result: {e}")
            return None
    
    def _calculate_quality_score(self, repo) -> float:
        """Calculate quality score for repository."""
        score = 0.0
        
        # Stars factor (0-0.4)
        stars = repo.stargazers_count
        if stars > 10000:
            score += 0.4
        elif stars > 1000:
            score += 0.3
        elif stars > 100:
            score += 0.2
        elif stars > 20:
            score += 0.1
        
        # Activity factor (0-0.2)
        if repo.updated_at:
            days_old = (datetime.now() - repo.updated_at.replace(tzinfo=None)).days
            if days_old < 30:
                score += 0.2
            elif days_old < 90:
                score += 0.15
            elif days_old < 365:
                score += 0.1
        
        # Issues factor (0-0.1)
        if repo.open_issues_count < 10:
            score += 0.1
        elif repo.open_issues_count < 50:
            score += 0.05
        
        # License factor (0-0.1)
        if repo.license:
            score += 0.1
        
        # Documentation factor (0-0.1)
        if repo.description and len(repo.description) > 20:
            score += 0.05
        if repo.has_wiki or repo.has_pages:
            score += 0.05
        
        # Fork ratio factor (0-0.1)
        if repo.stargazers_count > 0:
            fork_ratio = repo.forks_count / repo.stargazers_count
            if fork_ratio < 0.3:  # Good star-to-fork ratio
                score += 0.1
        
        return min(1.0, score)
    
    def _calculate_relevance_score(self, repo, search_term: str) -> float:
        """Calculate relevance score based on search term match."""
        score = 0.0
        search_lower = search_term.lower()
        
        # Name match (0-0.4)
        if search_lower in repo.name.lower():
            score += 0.4
        elif any(word in repo.name.lower() for word in search_lower.split()):
            score += 0.2
        
        # Description match (0-0.3)
        if repo.description:
            desc_lower = repo.description.lower()
            if search_lower in desc_lower:
                score += 0.3
            elif any(word in desc_lower for word in search_lower.split()):
                score += 0.15
        
        # Topics match (0-0.3)
        topics = [topic.lower() for topic in repo.get_topics()]
        if search_lower.replace(' ', '-') in topics:
            score += 0.3
        elif any(word in ' '.join(topics) for word in search_lower.split()):
            score += 0.15
        
        return min(1.0, score)
    
    def _deduplicate_results(self, results: List[RepositoryResult]) -> List[RepositoryResult]:
        """Remove duplicate repositories."""
        seen = set()
        unique_results = []
        
        for result in results:
            if result.full_name not in seen:
                seen.add(result.full_name)
                unique_results.append(result)
        
        return unique_results
    
    def _rank_by_relevance(self, results: List[RepositoryResult], search_targets: Dict[str, List[str]]) -> List[RepositoryResult]:
        """Rank results by combined quality and relevance scores."""
        def combined_score(result):
            return (result.quality_score * 0.6) + (result.relevance_score * 0.4)
        
        return sorted(results, key=combined_score, reverse=True)


# Example usage
async def main():
    import os
    
    # Initialize with GitHub token if available
    github_token = os.getenv('GITHUB_TOKEN')
    searcher = Tier2Search(github_token)
    
    # Test search targets
    search_targets = {
        'authentication': ['jwt', 'oauth', 'auth', 'authentication'],
        'database': ['database', 'orm', 'sql', 'postgresql'],
        'api': ['api', 'rest', 'fastapi', 'flask']
    }
    
    print("Searching curated collections...")
    results = await searcher.search_curated(search_targets, 'python')
    
    print(f"\nFound {len(results)} repositories:")
    for result in results[:10]:  # Show top 10
        print(f"\n{result.name} ({result.full_name})")
        print(f"  Stars: {result.stars}, Quality: {result.quality_score:.2f}, Relevance: {result.relevance_score:.2f}")
        print(f"  Description: {result.description[:100]}...")
        print(f"  Source: {result.source}")
        print(f"  Topics: {', '.join(result.topics[:5])}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())