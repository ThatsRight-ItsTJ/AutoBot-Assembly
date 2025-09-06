"""
Tier 1: Package Ecosystem Search

Discovers established, maintained packages from package registries.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

import aiohttp
from pydantic import BaseModel


@dataclass
class PackageResult:
    name: str
    repository_url: str
    description: str
    downloads: int
    stars: int
    last_updated: datetime
    license: str
    quality_score: float
    language: str
    package_manager: str
    version: str
    dependencies_count: int


class Tier1Search:
    """Search established package ecosystems for high-quality components."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sources = {
            'python': [
                'https://pypi.org/pypi',
                'https://libraries.io/api/pypi'
            ],
            'javascript': [
                'https://registry.npmjs.org',
                'https://libraries.io/api/npm'
            ],
            'java': [
                'https://search.maven.org/solrsearch/select',
                'https://libraries.io/api/maven'
            ],
            'go': [
                'https://pkg.go.dev',
                'https://libraries.io/api/go'
            ],
            'rust': [
                'https://crates.io/api/v1',
                'https://libraries.io/api/cargo'
            ]
        }
        
    async def search_packages(self, component: str, language: str, max_results: int = 20) -> List[PackageResult]:
        """
        Search established package ecosystems for components.
        
        Args:
            component: Component name to search for
            language: Programming language
            max_results: Maximum number of results to return
            
        Returns:
            List of PackageResult objects ranked by quality
        """
        results = []
        
        # Get sources for the language
        sources = self.sources.get(language.lower(), [])
        
        for source in sources:
            try:
                if 'libraries.io' in source:
                    packages = await self._search_libraries_io(source, component, language)
                elif language.lower() == 'python' and 'pypi' in source:
                    packages = await self._search_pypi(component)
                elif language.lower() == 'javascript' and 'npmjs' in source:
                    packages = await self._search_npm(component)
                elif language.lower() == 'java' and 'maven' in source:
                    packages = await self._search_maven(component)
                elif language.lower() == 'go' and 'pkg.go.dev' in source:
                    packages = await self._search_go_packages(component)
                elif language.lower() == 'rust' and 'crates.io' in source:
                    packages = await self._search_crates(component)
                else:
                    continue
                    
                results.extend(packages)
                
            except Exception as e:
                self.logger.error(f"Error searching {source}: {e}")
                continue
        
        # Remove duplicates and rank by quality
        unique_results = self._deduplicate_results(results)
        ranked_results = self._rank_by_quality(unique_results)
        
        return ranked_results[:max_results]
    
    async def _search_libraries_io(self, base_url: str, component: str, language: str) -> List[PackageResult]:
        """Search libraries.io API."""
        url = f"{base_url}/{language.lower()}/{component}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_libraries_io_response(data, language)
            except Exception as e:
                self.logger.error(f"Libraries.io search error: {e}")
                
        return []
    
    async def _search_pypi(self, component: str) -> List[PackageResult]:
        """Search PyPI for Python packages."""
        url = f"https://pypi.org/pypi/{component}/json"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_pypi_response(data)
            except Exception as e:
                self.logger.error(f"PyPI search error: {e}")
                
        return []
    
    async def _search_npm(self, component: str) -> List[PackageResult]:
        """Search NPM for JavaScript packages."""
        url = f"https://registry.npmjs.org/{component}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_npm_response(data)
            except Exception as e:
                self.logger.error(f"NPM search error: {e}")
                
        return []
    
    async def _search_maven(self, component: str) -> List[PackageResult]:
        """Search Maven Central for Java packages."""
        url = f"https://search.maven.org/solrsearch/select?q={component}&rows=10&wt=json"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_maven_response(data)
            except Exception as e:
                self.logger.error(f"Maven search error: {e}")
                
        return []
    
    async def _search_go_packages(self, component: str) -> List[PackageResult]:
        """Search Go packages."""
        # Note: pkg.go.dev doesn't have a public API, so this is a placeholder
        # In practice, you'd use the Go module proxy or scrape the website
        return []
    
    async def _search_crates(self, component: str) -> List[PackageResult]:
        """Search Rust crates."""
        url = f"https://crates.io/api/v1/crates?q={component}&per_page=10"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_crates_response(data)
            except Exception as e:
                self.logger.error(f"Crates.io search error: {e}")
                
        return []
    
    def _parse_libraries_io_response(self, data: dict, language: str) -> List[PackageResult]:
        """Parse libraries.io API response."""
        results = []
        
        if isinstance(data, list):
            packages = data
        else:
            packages = [data]
            
        for pkg in packages:
            try:
                result = PackageResult(
                    name=pkg.get('name', ''),
                    repository_url=pkg.get('repository_url', ''),
                    description=pkg.get('description', ''),
                    downloads=pkg.get('downloads', 0),
                    stars=pkg.get('stars', 0),
                    last_updated=datetime.fromisoformat(pkg.get('latest_release_published_at', '2020-01-01T00:00:00Z').replace('Z', '+00:00')),
                    license=pkg.get('license', 'Unknown'),
                    quality_score=self._calculate_quality_score(pkg),
                    language=language,
                    package_manager=pkg.get('platform', ''),
                    version=pkg.get('latest_stable_release', {}).get('number', ''),
                    dependencies_count=pkg.get('dependencies_count', 0)
                )
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error parsing package data: {e}")
                continue
                
        return results
    
    def _parse_pypi_response(self, data: dict) -> List[PackageResult]:
        """Parse PyPI API response."""
        try:
            info = data.get('info', {})
            urls = data.get('urls', [])
            
            # Get download count from recent releases
            downloads = 0
            for url_info in urls:
                downloads += url_info.get('downloads', 0)
            
            result = PackageResult(
                name=info.get('name', ''),
                repository_url=info.get('project_urls', {}).get('Repository', ''),
                description=info.get('summary', ''),
                downloads=downloads,
                stars=0,  # PyPI doesn't provide stars directly
                last_updated=datetime.fromisoformat(info.get('upload_time', '2020-01-01T00:00:00')),
                license=info.get('license', 'Unknown'),
                quality_score=self._calculate_pypi_quality_score(info, downloads),
                language='python',
                package_manager='pypi',
                version=info.get('version', ''),
                dependencies_count=len(info.get('requires_dist', []) or [])
            )
            return [result]
        except Exception as e:
            self.logger.error(f"Error parsing PyPI response: {e}")
            return []
    
    def _parse_npm_response(self, data: dict) -> List[PackageResult]:
        """Parse NPM API response."""
        try:
            latest_version = data.get('dist-tags', {}).get('latest', '')
            version_info = data.get('versions', {}).get(latest_version, {})
            
            result = PackageResult(
                name=data.get('name', ''),
                repository_url=version_info.get('repository', {}).get('url', ''),
                description=version_info.get('description', ''),
                downloads=0,  # Would need separate API call to get download stats
                stars=0,  # NPM doesn't provide stars directly
                last_updated=datetime.fromisoformat(data.get('time', {}).get(latest_version, '2020-01-01T00:00:00Z').replace('Z', '+00:00')),
                license=version_info.get('license', 'Unknown'),
                quality_score=self._calculate_npm_quality_score(data, version_info),
                language='javascript',
                package_manager='npm',
                version=latest_version,
                dependencies_count=len(version_info.get('dependencies', {}) or {})
            )
            return [result]
        except Exception as e:
            self.logger.error(f"Error parsing NPM response: {e}")
            return []
    
    def _parse_maven_response(self, data: dict) -> List[PackageResult]:
        """Parse Maven Central API response."""
        results = []
        
        try:
            docs = data.get('response', {}).get('docs', [])
            
            for doc in docs:
                result = PackageResult(
                    name=f"{doc.get('g', '')}:{doc.get('a', '')}",
                    repository_url='',  # Maven doesn't provide repo URLs directly
                    description='',
                    downloads=0,
                    stars=0,
                    last_updated=datetime.fromtimestamp(doc.get('timestamp', 0) / 1000),
                    license='Unknown',
                    quality_score=self._calculate_maven_quality_score(doc),
                    language='java',
                    package_manager='maven',
                    version=doc.get('latestVersion', ''),
                    dependencies_count=0
                )
                results.append(result)
        except Exception as e:
            self.logger.error(f"Error parsing Maven response: {e}")
            
        return results
    
    def _parse_crates_response(self, data: dict) -> List[PackageResult]:
        """Parse Crates.io API response."""
        results = []
        
        try:
            crates = data.get('crates', [])
            
            for crate in crates:
                result = PackageResult(
                    name=crate.get('name', ''),
                    repository_url=crate.get('repository', ''),
                    description=crate.get('description', ''),
                    downloads=crate.get('downloads', 0),
                    stars=0,  # Would need GitHub API to get stars
                    last_updated=datetime.fromisoformat(crate.get('updated_at', '2020-01-01T00:00:00Z').replace('Z', '+00:00')),
                    license='Unknown',
                    quality_score=self._calculate_crates_quality_score(crate),
                    language='rust',
                    package_manager='cargo',
                    version=crate.get('max_version', ''),
                    dependencies_count=0
                )
                results.append(result)
        except Exception as e:
            self.logger.error(f"Error parsing Crates response: {e}")
            
        return results
    
    def _calculate_quality_score(self, pkg: dict) -> float:
        """Calculate quality score for libraries.io packages."""
        score = 0.5  # Base score
        
        # Downloads factor (0-0.3)
        downloads = pkg.get('downloads', 0)
        if downloads > 1000000:
            score += 0.3
        elif downloads > 100000:
            score += 0.2
        elif downloads > 10000:
            score += 0.1
        
        # Stars factor (0-0.2)
        stars = pkg.get('stars', 0)
        if stars > 1000:
            score += 0.2
        elif stars > 100:
            score += 0.1
        
        # Maintenance factor (0-0.2)
        last_update = pkg.get('latest_release_published_at', '')
        if last_update:
            try:
                last_date = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                days_old = (datetime.now().replace(tzinfo=last_date.tzinfo) - last_date).days
                if days_old < 90:
                    score += 0.2
                elif days_old < 365:
                    score += 0.1
            except:
                pass
        
        return min(1.0, score)
    
    def _calculate_pypi_quality_score(self, info: dict, downloads: int) -> float:
        """Calculate quality score for PyPI packages."""
        score = 0.5
        
        if downloads > 100000:
            score += 0.3
        elif downloads > 10000:
            score += 0.2
        elif downloads > 1000:
            score += 0.1
        
        # Check for documentation
        if info.get('home_page') or info.get('project_urls', {}).get('Documentation'):
            score += 0.1
        
        # Check for recent activity
        upload_time = info.get('upload_time', '')
        if upload_time:
            try:
                upload_date = datetime.fromisoformat(upload_time)
                days_old = (datetime.now() - upload_date).days
                if days_old < 90:
                    score += 0.1
            except:
                pass
        
        return min(1.0, score)
    
    def _calculate_npm_quality_score(self, data: dict, version_info: dict) -> float:
        """Calculate quality score for NPM packages."""
        score = 0.5
        
        # Check for repository
        if version_info.get('repository'):
            score += 0.1
        
        # Check for license
        if version_info.get('license') and version_info.get('license') != 'Unknown':
            score += 0.1
        
        # Check for dependencies (fewer is often better for libraries)
        deps = len(version_info.get('dependencies', {}) or {})
        if deps < 5:
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_maven_quality_score(self, doc: dict) -> float:
        """Calculate quality score for Maven packages."""
        score = 0.5
        
        # Recent timestamp
        timestamp = doc.get('timestamp', 0)
        if timestamp > 0:
            days_old = (datetime.now().timestamp() - timestamp / 1000) / 86400
            if days_old < 365:
                score += 0.2
        
        return min(1.0, score)
    
    def _calculate_crates_quality_score(self, crate: dict) -> float:
        """Calculate quality score for Rust crates."""
        score = 0.5
        
        downloads = crate.get('downloads', 0)
        if downloads > 100000:
            score += 0.3
        elif downloads > 10000:
            score += 0.2
        elif downloads > 1000:
            score += 0.1
        
        return min(1.0, score)
    
    def _deduplicate_results(self, results: List[PackageResult]) -> List[PackageResult]:
        """Remove duplicate packages based on name and repository URL."""
        seen = set()
        unique_results = []
        
        for result in results:
            key = (result.name.lower(), result.repository_url.lower())
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        return unique_results
    
    def _rank_by_quality(self, results: List[PackageResult]) -> List[PackageResult]:
        """Sort results by quality score (highest first)."""
        return sorted(results, key=lambda x: x.quality_score, reverse=True)


# Example usage
async def main():
    searcher = Tier1Search()
    
    test_cases = [
        ("authentication", "python"),
        ("http-server", "javascript"),
        ("json-parser", "java"),
        ("web-framework", "rust")
    ]
    
    for component, language in test_cases:
        print(f"\nSearching for {component} in {language}:")
        results = await searcher.search_packages(component, language, max_results=5)
        
        for result in results:
            print(f"  {result.name} - Score: {result.quality_score:.2f}")
            print(f"    Downloads: {result.downloads}, Stars: {result.stars}")
            print(f"    Repository: {result.repository_url}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())