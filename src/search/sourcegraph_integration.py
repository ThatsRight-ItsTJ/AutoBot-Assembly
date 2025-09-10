import os
import requests
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class SourceGraphResult:
    repository: str
    file_path: str
    code_snippet: str
    language: str
    stars: int
    last_updated: str
    match_score: float

class SourceGraphIntegration:
    def __init__(self):
        self.api_token = os.getenv('SOURCEGRAPH_API_TOKEN')
        self.endpoint = os.getenv('SOURCEGRAPH_ENDPOINT', 'https://sourcegraph.com/.api/graphql')
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_token}' if self.api_token else None
        }
    
    def build_pattern_query(self, libraries: List[str], use_case: str) -> str:
        """Build SourceGraph query for specific integration patterns"""
        base_libs = " AND ".join([f"lang:python {lib}" for lib in libraries])
        
        if use_case == "web_scraper":
            return f"{base_libs} AND (requests OR beautifulsoup OR selenium) AND (json OR csv)"
        elif use_case == "api_server":
            return f"{base_libs} AND (fastapi OR flask) AND (router OR endpoint)"
        elif use_case == "data_processing":
            return f"{base_libs} AND (pandas OR numpy) AND (transform OR process)"
        
        return base_libs
    
    def sourcegraph_search(self, query: str, limit: int = 10) -> List[SourceGraphResult]:
        """Search SourceGraph for code patterns"""
        search_query = {
            'query': query,
            'version': 'https://github.com/sourcegraph/sourcegraph@main',
            'patternType': 'literal',
            'limit': limit
        }
        
        try:
            response = requests.post(
                self.endpoint,
                json=search_query,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return self._parse_search_results(response.json())
        except Exception as e:
            print(f"SourceGraph search failed: {e}")
            return []
    
    def _parse_search_results(self, response_data: Dict) -> List[SourceGraphResult]:
        """Parse SourceGraph API response"""
        results = []
        
        if 'results' not in response_data:
            return results
        
        for result in response_data['results']:
            try:
                source_graph_result = SourceGraphResult(
                    repository=result.get('repository', ''),
                    file_path=result.get('file', ''),
                    code_snippet=result.get('snippet', ''),
                    language=result.get('language', ''),
                    stars=result.get('stars', 0),
                    last_updated=result.get('last_updated', ''),
                    match_score=result.get('score', 0.0)
                )
                results.append(source_graph_result)
            except Exception as e:
                print(f"Error parsing result: {e}")
                continue
        
        return results
    
    def discover_integration_patterns(self, libraries: List[str], use_case: str) -> List[SourceGraphResult]:
        """Find real-world integration examples"""
        search_query = self.build_pattern_query(libraries, use_case)
        results = self.sourcegraph_search(search_query)
        
        # Sort by match score and repository stars
        results.sort(key=lambda x: (x.match_score, x.stars), reverse=True)
        
        return results
    
    def analyze_integration_patterns(self, results: List[SourceGraphResult]) -> Dict[str, Any]:
        """Analyze and rank integration patterns"""
        if not results:
            return {'confidence': 'low', 'patterns': [], 'common_issues': []}
        
        pattern_analysis = {
            'confidence': 'high' if len(results) > 5 else 'medium',
            'patterns': [],
            'common_issues': []
        }
        
        # Extract common patterns
        for result in results[:5]:  # Top 5 results
            pattern_analysis['patterns'].append({
                'repository': result.repository,
                'file_path': result.file_path,
                'code_snippet': result.code_snippet,
                'language': result.language,
                'stars': result.stars
            })
        
        return pattern_analysis

    def validate_pattern(self, libraries: List[str], use_case: str) -> Dict[str, Any]:
        """Validate integration pattern against real-world usage"""
        patterns = self.discover_integration_patterns(libraries, use_case)
        analysis = self.analyze_integration_patterns(patterns)
        
        return {
            'confidence': analysis['confidence'],
            'examples': analysis['patterns'],
            'libraries_used': libraries,
            'use_case': use_case
        }