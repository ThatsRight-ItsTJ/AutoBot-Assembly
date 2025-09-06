"""
Search Orchestrator

Coordinates all three tiers of search and combines results.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime

from ..search.tier1_packages import Tier1Search, PackageResult
from ..search.tier2_curated import Tier2Search, RepositoryResult
from ..search.tier3_discovery import Tier3Search, SearchResult
from .project_analyzer import ProjectStructure


@dataclass
class SearchResults:
    tier1_results: List[PackageResult]
    tier2_results: List[RepositoryResult]
    tier3_results: List[SearchResult]
    all_results: List[Union[PackageResult, RepositoryResult, SearchResult]]
    search_summary: Dict[str, int]
    execution_time: float


class SearchOrchestrator:
    """Orchestrates the three-tier search strategy."""
    
    def __init__(self, github_token: Optional[str] = None, pollinations_endpoint: str = "https://text.pollinations.ai/openai"):
        self.tier1_search = Tier1Search()
        self.tier2_search = Tier2Search(github_token)
        self.tier3_search = Tier3Search(github_token, pollinations_endpoint)
        self.logger = logging.getLogger(__name__)
    
    async def execute_tiered_search(self, project_structure: ProjectStructure, max_results_per_tier: int = 50) -> SearchResults:
        """
        Execute complete three-tier search strategy.
        
        Args:
            project_structure: Analyzed project requirements
            max_results_per_tier: Maximum results per search tier
            
        Returns:
            SearchResults containing all discovered repositories
        """
        start_time = datetime.now()
        
        # Prepare search targets from project structure
        search_targets = self._prepare_search_targets(project_structure)
        
        self.logger.info(f"Starting tiered search for {len(search_targets)} components")
        
        # Execute Tier 1: Package Ecosystem Search
        self.logger.info("Executing Tier 1: Package ecosystem search...")
        tier1_results = await self._execute_tier1_search(search_targets, project_structure.language, max_results_per_tier)
        
        # Execute Tier 2: Curated Collections Search
        self.logger.info("Executing Tier 2: Curated collections search...")
        tier2_results = await self._execute_tier2_search(search_targets, project_structure.language, max_results_per_tier)
        
        # Execute Tier 3: Live GitHub Discovery
        self.logger.info("Executing Tier 3: Live GitHub discovery...")
        tier3_results = await self._execute_tier3_search(search_targets, project_structure.language, tier1_results, tier2_results, max_results_per_tier)
        
        # Combine and summarize results
        all_results = []
        all_results.extend(tier1_results)
        all_results.extend(tier2_results)
        all_results.extend(tier3_results)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        search_summary = {
            'tier1_count': len(tier1_results),
            'tier2_count': len(tier2_results),
            'tier3_count': len(tier3_results),
            'total_count': len(all_results),
            'unique_repositories': len(self._get_unique_repositories(all_results))
        }
        
        self.logger.info(f"Search completed in {execution_time:.2f}s: {search_summary}")
        
        return SearchResults(
            tier1_results=tier1_results,
            tier2_results=tier2_results,
            tier3_results=tier3_results,
            all_results=all_results,
            search_summary=search_summary,
            execution_time=execution_time
        )
    
    def _prepare_search_targets(self, project_structure: ProjectStructure) -> Dict[str, List[str]]:
        """Prepare search targets from project structure."""
        search_targets = {}
        
        # Use core components as primary search targets
        for component in project_structure.core_components:
            # Start with the component name itself
            keywords = [component]
            
            # Add related keywords from search_keywords
            for keyword in project_structure.search_keywords:
                if component.lower() in keyword.lower() or keyword.lower() in component.lower():
                    keywords.append(keyword)
            
            # Add framework-specific keywords
            for framework in project_structure.frameworks:
                keywords.append(f"{framework} {component}")
            
            # Add language-specific variations
            if project_structure.language == 'python':
                keywords.extend([f"python {component}", f"{component} python"])
            elif project_structure.language == 'javascript':
                keywords.extend([f"js {component}", f"{component} js", f"node {component}"])
            elif project_structure.language == 'java':
                keywords.extend([f"java {component}", f"{component} java"])
            
            search_targets[component] = list(set(keywords))  # Remove duplicates
        
        # Add search keywords as additional components if not already covered
        for keyword in project_structure.search_keywords:
            if not any(keyword.lower() in component.lower() for component in search_targets.keys()):
                search_targets[keyword] = [keyword]
        
        return search_targets
    
    async def _execute_tier1_search(self, search_targets: Dict[str, List[str]], language: str, max_results: int) -> List[PackageResult]:
        """Execute Tier 1 package ecosystem search."""
        results = []
        
        for component, keywords in search_targets.items():
            for keyword in keywords[:3]:  # Limit keywords per component
                try:
                    component_results = await self.tier1_search.search_packages(keyword, language, max_results=10)
                    results.extend(component_results)
                except Exception as e:
                    self.logger.error(f"Error in Tier 1 search for {keyword}: {e}")
                    continue
        
        # Remove duplicates and limit results
        unique_results = self._deduplicate_tier1_results(results)
        return unique_results[:max_results]
    
    async def _execute_tier2_search(self, search_targets: Dict[str, List[str]], language: str, max_results: int) -> List[RepositoryResult]:
        """Execute Tier 2 curated collections search."""
        try:
            results = await self.tier2_search.search_curated(search_targets, language)
            return results[:max_results]
        except Exception as e:
            self.logger.error(f"Error in Tier 2 search: {e}")
            return []
    
    async def _execute_tier3_search(self, search_targets: Dict[str, List[str]], language: str, 
                                  tier1_results: List[PackageResult], tier2_results: List[RepositoryResult], 
                                  max_results: int) -> List[SearchResult]:
        """Execute Tier 3 live GitHub discovery."""
        try:
            results = await self.tier3_search.comprehensive_search(search_targets, language, tier1_results, tier2_results)
            return results[:max_results]
        except Exception as e:
            self.logger.error(f"Error in Tier 3 search: {e}")
            return []
    
    def _deduplicate_tier1_results(self, results: List[PackageResult]) -> List[PackageResult]:
        """Remove duplicate packages from Tier 1 results."""
        seen = set()
        unique_results = []
        
        for result in results:
            # Use name and repository URL as unique identifier
            key = (result.name.lower(), result.repository_url.lower())
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        return unique_results
    
    def _get_unique_repositories(self, all_results: List) -> set:
        """Get set of unique repository names from all results."""
        unique_repos = set()
        
        for result in all_results:
            if hasattr(result, 'full_name'):
                unique_repos.add(result.full_name)
            elif hasattr(result, 'repository_url') and result.repository_url:
                # Extract repo name from URL
                if 'github.com' in result.repository_url:
                    parts = result.repository_url.split('/')
                    if len(parts) >= 2:
                        unique_repos.add(f"{parts[-2]}/{parts[-1]}")
            elif hasattr(result, 'name'):
                unique_repos.add(result.name)
        
        return unique_repos
    
    def get_top_results(self, search_results: SearchResults, top_n: int = 20) -> List:
        """Get top N results across all tiers based on quality scores."""
        all_scored_results = []
        
        # Add Tier 1 results with their quality scores
        for result in search_results.tier1_results:
            all_scored_results.append((result, result.quality_score, 'tier1'))
        
        # Add Tier 2 results with their quality scores
        for result in search_results.tier2_results:
            all_scored_results.append((result, result.quality_score, 'tier2'))
        
        # Add Tier 3 results with their discovery scores
        for result in search_results.tier3_results:
            all_scored_results.append((result, result.discovery_score, 'tier3'))
        
        # Sort by score (highest first)
        sorted_results = sorted(all_scored_results, key=lambda x: x[1], reverse=True)
        
        return [result[0] for result in sorted_results[:top_n]]


# Example usage
async def main():
    import os
    from .project_analyzer import ProjectAnalyzer
    
    # Initialize components
    github_token = os.getenv('GITHUB_TOKEN')
    orchestrator = SearchOrchestrator(github_token)
    analyzer = ProjectAnalyzer()
    
    # Test with a sample project
    test_prompt = "Create a Python FastAPI application with JWT authentication and PostgreSQL database"
    project_structure = await analyzer.analyze_prompt(test_prompt, "python")
    
    print(f"Project Analysis:")
    print(f"  Type: {project_structure.project_type}")
    print(f"  Components: {project_structure.core_components}")
    print(f"  Keywords: {project_structure.search_keywords}")
    
    # Execute tiered search
    print(f"\nExecuting tiered search...")
    search_results = await orchestrator.execute_tiered_search(project_structure)
    
    print(f"\nSearch Results Summary:")
    for tier, count in search_results.search_summary.items():
        print(f"  {tier}: {count}")
    
    # Show top results
    top_results = orchestrator.get_top_results(search_results, top_n=10)
    print(f"\nTop 10 Results:")
    for i, result in enumerate(top_results, 1):
        if hasattr(result, 'full_name'):
            name = result.full_name
        elif hasattr(result, 'name'):
            name = result.name
        else:
            name = "Unknown"
        
        if hasattr(result, 'quality_score'):
            score = result.quality_score
        elif hasattr(result, 'discovery_score'):
            score = result.discovery_score
        else:
            score = 0.0
        
        print(f"  {i}. {name} (Score: {score:.2f})")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())