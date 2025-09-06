"""
Tier 3: Live GitHub Discovery

AI-driven GitHub search for comprehensive coverage including hidden gems.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

import aiohttp
from github import Github


@dataclass
class SearchResult:
    repository: str
    full_name: str
    url: str
    description: str
    stars: int
    forks: int
    language: str
    last_updated: datetime
    license: str
    file_matches: List[str]
    search_query: str
    discovery_score: float
    gap_filling_potential: float


class AIQueryGenerator:
    """Generate AI-powered search queries for gap analysis."""
    
    def __init__(self, pollinations_endpoint: str = "https://text.pollinations.ai/openai"):
        self.pollinations_endpoint = pollinations_endpoint
        self.logger = logging.getLogger(__name__)
    
    async def generate_gap_filling_queries(self, gaps: Dict[str, List[str]], language: str) -> List[str]:
        """Generate targeted search queries to fill coverage gaps."""
        prompt = self._create_query_generation_prompt(gaps, language)
        
        try:
            response = await self._call_pollinations(prompt)
            queries = self._parse_query_response(response)
            return queries
        except Exception as e:
            self.logger.error(f"Error generating queries: {e}")
            return self._generate_fallback_queries(gaps, language)
    
    def _create_query_generation_prompt(self, gaps: Dict[str, List[str]], language: str) -> str:
        """Create prompt for AI query generation."""
        gaps_text = "\n".join([f"- {component}: {', '.join(missing)}" for component, missing in gaps.items()])
        
        return f"""
        Generate GitHub search queries to find repositories that fill these gaps:
        
        Missing Components:
        {gaps_text}
        
        Target Language: {language}
        
        Create 5-8 specific GitHub search queries that would find repositories containing these missing components.
        Focus on:
        1. File-level searches (filename: patterns)
        2. Code pattern searches (specific function/class names)
        3. Implementation-specific searches
        4. Integration-focused searches
        
        Return as JSON array of strings:
        ["query1", "query2", "query3", ...]
        
        Example queries:
        - "filename:auth.py jwt OR oauth language:python stars:>10"
        - "path:utils/ 'password hash' language:python"
        - "'class Authentication' language:python size:>1000"
        - "fastapi jwt middleware language:python"
        """
    
    async def _call_pollinations(self, prompt: str) -> str:
        """Make API call to Pollinations AI."""
        payload = {
            "model": "openai",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a GitHub search expert. Return only valid JSON arrays of search queries."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "jsonMode": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.pollinations_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    raise Exception(f"API call failed with status {response.status}")
    
    def _parse_query_response(self, response: str) -> List[str]:
        """Parse AI response into search queries."""
        try:
            import json
            queries = json.loads(response)
            if isinstance(queries, list):
                return [str(q) for q in queries if q]
            return []
        except Exception as e:
            self.logger.error(f"Error parsing query response: {e}")
            return []
    
    def _generate_fallback_queries(self, gaps: Dict[str, List[str]], language: str) -> List[str]:
        """Generate fallback queries when AI fails."""
        queries = []
        
        for component, missing_items in gaps.items():
            for item in missing_items[:2]:  # Limit to avoid too many queries
                # Basic keyword search
                queries.append(f"{item} {component} language:{language} stars:>5")
                
                # File-level search
                if language == 'python':
                    queries.append(f"filename:{item}.py language:python")
                elif language == 'javascript':
                    queries.append(f"filename:{item}.js language:javascript")
                elif language == 'java':
                    queries.append(f"filename:{item.title()}.java language:java")
        
        return queries[:8]  # Limit total queries


class Tier3Search:
    """AI-driven GitHub search for comprehensive coverage."""
    
    def __init__(self, github_token: Optional[str] = None, pollinations_endpoint: str = "https://text.pollinations.ai/openai"):
        self.github_client = Github(github_token) if github_token else Github()
        self.query_generator = AIQueryGenerator(pollinations_endpoint)
        self.logger = logging.getLogger(__name__)
    
    async def comprehensive_search(self, 
                                 search_targets: Dict[str, List[str]], 
                                 language: str,
                                 tier1_results: List = None, 
                                 tier2_results: List = None) -> List[SearchResult]:
        """
        AI-driven GitHub search for comprehensive coverage.
        
        Args:
            search_targets: Dict mapping components to search keywords
            language: Target programming language
            tier1_results: Results from Tier 1 search (for gap analysis)
            tier2_results: Results from Tier 2 search (for gap analysis)
            
        Returns:
            List of SearchResult objects
        """
        # Analyze coverage gaps from previous tiers
        gaps = self._analyze_coverage_gaps(search_targets, tier1_results or [], tier2_results or [])
        
        # Generate targeted search queries
        search_queries = await self.query_generator.generate_gap_filling_queries(gaps, language)
        
        # Add strategic searches
        strategic_queries = self._generate_strategic_queries(search_targets, language)
        search_queries.extend(strategic_queries)
        
        # Execute searches
        results = []
        for query in search_queries:
            try:
                query_results = await self._execute_github_search(query, language)
                results.extend(query_results)
                
                # Rate limiting - pause between searches
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error executing search query '{query}': {e}")
                continue
        
        # Filter and rank results
        filtered_results = self._filter_and_rank(results, search_targets)
        
        return filtered_results
    
    def _analyze_coverage_gaps(self, search_targets: Dict[str, List[str]], 
                             tier1_results: List, tier2_results: List) -> Dict[str, List[str]]:
        """Identify gaps in coverage from previous tiers."""
        gaps = {}
        
        # Get all found components from previous tiers
        found_keywords = set()
        
        # Extract keywords from tier1 results
        for result in tier1_results:
            if hasattr(result, 'name'):
                found_keywords.update(result.name.lower().split())
            if hasattr(result, 'description'):
                found_keywords.update(result.description.lower().split())
        
        # Extract keywords from tier2 results
        for result in tier2_results:
            if hasattr(result, 'name'):
                found_keywords.update(result.name.lower().split())
            if hasattr(result, 'description'):
                found_keywords.update(result.description.lower().split())
            if hasattr(result, 'topics'):
                found_keywords.update([topic.lower() for topic in result.topics])
        
        # Identify missing keywords for each component
        for component, keywords in search_targets.items():
            missing = []
            for keyword in keywords:
                keyword_words = keyword.lower().split()
                if not any(word in found_keywords for word in keyword_words):
                    missing.append(keyword)
            
            if missing:
                gaps[component] = missing
        
        return gaps
    
    def _generate_strategic_queries(self, search_targets: Dict[str, List[str]], language: str) -> List[str]:
        """Generate strategic search queries based on patterns."""
        queries = []
        
        for component, keywords in search_targets.items():
            for keyword in keywords[:2]:  # Limit to avoid too many queries
                # File-level search
                if language == 'python':
                    filename = f"{keyword.replace(' ', '_')}.py"
                    queries.append(f"filename:{filename} language:python stars:>5")
                elif language == 'javascript':
                    filename = f"{keyword.replace(' ', '-')}.js"
                    queries.append(f"filename:{filename} language:javascript stars:>5")
                
                # Pattern search
                queries.append(f'"{keyword}" in:file language:{language} size:>500')
                
                # Implementation search with class patterns
                if language == 'python':
                    class_name = keyword.replace(' ', '').title()
                    queries.append(f'"class {class_name}" language:python')
                elif language == 'java':
                    class_name = keyword.replace(' ', '').title()
                    queries.append(f'"class {class_name}" language:java')
        
        return queries
    
    async def _execute_github_search(self, query: str, language: str) -> List[SearchResult]:
        """Execute a single GitHub search query."""
        results = []
        
        try:
            # Add language filter if not already present
            if f"language:{language}" not in query:
                query += f" language:{language}"
            
            # Search repositories
            repositories = self.github_client.search_repositories(
                query=query,
                sort='stars',
                order='desc'
            )
            
            # Process results (limit to top 20 per query)
            for repo in repositories[:20]:
                try:
                    result = SearchResult(
                        repository=repo.name,
                        full_name=repo.full_name,
                        url=repo.html_url,
                        description=repo.description or "",
                        stars=repo.stargazers_count,
                        forks=repo.forks_count,
                        language=repo.language or language,
                        last_updated=repo.updated_at,
                        license=repo.license.name if repo.license else "Unknown",
                        file_matches=[],  # Simplified for now
                        search_query=query,
                        discovery_score=self._calculate_discovery_score(repo, query),
                        gap_filling_potential=self._calculate_gap_filling_potential(repo, query)
                    )
                    
                    results.append(result)
                    
                except Exception as e:
                    self.logger.error(f"Error processing repository {repo.full_name}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error executing GitHub search: {e}")
        
        return results
    
    def _calculate_discovery_score(self, repo, query: str) -> float:
        """Calculate discovery score based on repository characteristics."""
        score = 0.0
        
        # Stars factor (0-0.3)
        stars = repo.stargazers_count
        if stars > 1000:
            score += 0.3
        elif stars > 100:
            score += 0.2
        elif stars > 10:
            score += 0.1
        
        # Activity factor (0-0.2)
        if repo.updated_at:
            days_old = (datetime.now() - repo.updated_at.replace(tzinfo=None)).days
            if days_old < 90:
                score += 0.2
            elif days_old < 365:
                score += 0.1
        
        # Size factor (0-0.2) - prefer medium-sized repos
        size_kb = repo.size
        if 100 < size_kb < 10000:  # 100KB to 10MB
            score += 0.2
        elif 10 < size_kb < 100000:  # 10KB to 100MB
            score += 0.1
        
        # License factor (0-0.1)
        if repo.license:
            score += 0.1
        
        # Query relevance factor (0-0.2)
        query_words = query.lower().split()
        repo_text = f"{repo.name} {repo.description or ''}".lower()
        
        matching_words = sum(1 for word in query_words if word in repo_text)
        if matching_words > 0:
            score += min(0.2, matching_words * 0.05)
        
        return min(1.0, score)
    
    def _calculate_gap_filling_potential(self, repo, query: str) -> float:
        """Calculate how well this repository fills identified gaps."""
        score = 0.5  # Base score
        
        # Query specificity bonus
        if 'filename:' in query:
            score += 0.2
        if 'in:file' in query:
            score += 0.15
        if '"' in query:  # Exact phrase search
            score += 0.1
        
        # Repository characteristics
        if repo.stargazers_count > 50:
            score += 0.1
        if repo.forks_count > 10:
            score += 0.05
        
        return min(1.0, score)
    
    def _filter_and_rank(self, results: List[SearchResult], search_targets: Dict[str, List[str]]) -> List[SearchResult]:
        """Filter and rank results by combined scores."""
        # Remove duplicates
        seen = set()
        unique_results = []
        
        for result in results:
            if result.full_name not in seen:
                seen.add(result.full_name)
                unique_results.append(result)
        
        # Sort by combined score
        def combined_score(result):
            return (result.discovery_score * 0.6) + (result.gap_filling_potential * 0.4)
        
        return sorted(unique_results, key=combined_score, reverse=True)


# Example usage
async def main():
    import os
    
    github_token = os.getenv('GITHUB_TOKEN')
    searcher = Tier3Search(github_token)
    
    search_targets = {
        'authentication': ['jwt', 'oauth', 'auth'],
        'database': ['postgresql', 'orm', 'sqlalchemy'],
        'api': ['fastapi', 'rest', 'endpoints']
    }
    
    print("Executing Tier 3 discovery search...")
    results = await searcher.comprehensive_search(search_targets, 'python')
    
    print(f"\nFound {len(results)} repositories:")
    for result in results[:10]:
        print(f"\n{result.repository} ({result.full_name})")
        print(f"  Stars: {result.stars}, Discovery: {result.discovery_score:.2f}, Gap-filling: {result.gap_filling_potential:.2f}")
        print(f"  Query: {result.search_query}")
        print(f"  Description: {result.description[:100]}...")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())