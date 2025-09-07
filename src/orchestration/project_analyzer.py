"""
Project Analyzer

AI-powered project analysis engine that interprets user requirements
and generates comprehensive project specifications.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
import os

# Import AI providers
try:
    import aiohttp
except ImportError:
    aiohttp = None


class ProjectType(Enum):
    """Types of projects that can be analyzed."""
    WEB_APPLICATION = "web_application"
    API_SERVICE = "api_service"
    DATA_PIPELINE = "data_pipeline"
    MOBILE_APP = "mobile_app"
    DESKTOP_APP = "desktop_app"
    MACHINE_LEARNING = "machine_learning"
    AUTOMATION_SCRIPT = "automation_script"
    LIBRARY = "library"


@dataclass
class ProjectAnalysis:
    """Result of project analysis."""
    name: str
    description: str
    project_type: ProjectType
    language: str
    components: List[str]
    dependencies: List[str]
    confidence: float
    estimated_complexity: str
    recommended_architecture: str


class ProjectAnalyzer:
    """AI-powered project analysis engine."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Set Pollinations API key
        self.pollinations_api_key = "D6ivBlSgXRsU1F7r"
        
        # AI provider configurations
        self.ai_providers = {
            'pollinations': {
                'url': 'https://text.pollinations.ai/',
                'available': aiohttp is not None,
                'api_key': self.pollinations_api_key
            }
        }
        
        # Project analysis patterns
        self.analysis_patterns = {
            'web_scraping': {
                'type': ProjectType.WEB_APPLICATION,
                'language': 'python',
                'components': ['web_scraper', 'data_parser', 'storage', 'scheduler'],
                'dependencies': ['requests', 'beautifulsoup4', 'scrapy', 'selenium']
            },
            'news_aggregator': {
                'type': ProjectType.WEB_APPLICATION,
                'language': 'python',
                'components': ['rss_parser', 'sentiment_analysis', 'web_dashboard', 'database'],
                'dependencies': ['feedparser', 'fastapi', 'pandas', 'nltk']
            },
            'api_service': {
                'type': ProjectType.API_SERVICE,
                'language': 'python',
                'components': ['api_endpoints', 'authentication', 'database', 'documentation'],
                'dependencies': ['fastapi', 'uvicorn', 'pydantic', 'sqlalchemy']
            },
            'data_analysis': {
                'type': ProjectType.DATA_PIPELINE,
                'language': 'python',
                'components': ['data_ingestion', 'processing', 'visualization', 'reporting'],
                'dependencies': ['pandas', 'numpy', 'matplotlib', 'jupyter']
            }
        }
    
    async def analyze_project_prompt(self, prompt: str, provider: str = "pollinations") -> ProjectAnalysis:
        """
        Analyze a project prompt and generate comprehensive project specifications.
        
        Args:
            prompt: User's project description/requirements
            provider: AI provider to use for analysis
            
        Returns:
            ProjectAnalysis: Comprehensive analysis of the project requirements
        """
        self.logger.info(f"Analyzing project prompt: {prompt[:100]}...")
        
        # Try AI analysis first
        ai_analysis = await self._get_ai_analysis(prompt, provider)
        
        if ai_analysis:
            return ai_analysis
        
        # Fallback to pattern-based analysis
        return self._pattern_based_analysis(prompt)
    
    async def _get_ai_analysis(self, prompt: str, provider: str) -> Optional[ProjectAnalysis]:
        """Get AI-powered project analysis."""
        
        if provider == "pollinations" and aiohttp:
            try:
                analysis_prompt = f"""
                Analyze this project requirement and provide a structured response:
                
                Project Description: {prompt}
                
                Please provide:
                1. Project name (concise, descriptive)
                2. Project type (web_application, api_service, data_pipeline, etc.)
                3. Primary programming language
                4. Key components needed (list 4-6 main components)
                5. Main dependencies/libraries needed
                6. Confidence level (0.0-1.0)
                7. Estimated complexity (low, medium, high)
                8. Recommended architecture pattern
                
                Format as JSON with keys: name, type, language, components, dependencies, confidence, complexity, architecture
                """
                
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.pollinations_api_key}',
                    'User-Agent': 'AutoBot-Assembly/1.0'
                }
                
                payload = {
                    'messages': [
                        {
                            'role': 'system',
                            'content': 'You are an expert software architect. Analyze project requirements and provide structured technical specifications in valid JSON format.'
                        },
                        {
                            'role': 'user',
                            'content': analysis_prompt
                        }
                    ],
                    'model': 'openai',
                    'seed': 42,
                    'jsonMode': True
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        'https://text.pollinations.ai/',
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=20)
                    ) as response:
                        if response.status == 200:
                            result = await response.text()
                            self.logger.info(f"AI analysis successful: {len(result)} characters")
                            return self._parse_ai_response(result, prompt)
                        else:
                            self.logger.warning(f"Pollinations API returned status {response.status}: {await response.text()}")
            
            except Exception as e:
                self.logger.warning(f"AI analysis failed: {e}")
        
        return None
    
    def _parse_ai_response(self, ai_response: str, original_prompt: str) -> ProjectAnalysis:
        """Parse AI response into ProjectAnalysis object."""
        
        try:
            # Try to extract JSON from response
            if '{' in ai_response and '}' in ai_response:
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                json_str = ai_response[json_start:json_end]
                data = json.loads(json_str)
                
                # Validate project type
                project_type_str = data.get('type', 'web_application')
                try:
                    project_type = ProjectType(project_type_str)
                except ValueError:
                    project_type = ProjectType.WEB_APPLICATION
                
                return ProjectAnalysis(
                    name=data.get('name', 'AI Generated Project'),
                    description=original_prompt,
                    project_type=project_type,
                    language=data.get('language', 'python'),
                    components=data.get('components', []),
                    dependencies=data.get('dependencies', []),
                    confidence=float(data.get('confidence', 0.9)),  # Higher confidence for AI analysis
                    estimated_complexity=data.get('complexity', 'medium'),
                    recommended_architecture=data.get('architecture', 'layered')
                )
        except Exception as e:
            self.logger.warning(f"Failed to parse AI response: {e}")
        
        # Fallback to pattern-based analysis if parsing fails
        return self._pattern_based_analysis(original_prompt)
    
    def _pattern_based_analysis(self, prompt: str) -> ProjectAnalysis:
        """Analyze project using pattern matching as fallback."""
        
        prompt_lower = prompt.lower()
        
        # Determine project pattern
        selected_pattern = None
        for pattern_name, pattern_config in self.analysis_patterns.items():
            if any(keyword in prompt_lower for keyword in pattern_name.split('_')):
                selected_pattern = pattern_config
                break
        
        # Default to web application if no pattern matches
        if not selected_pattern:
            selected_pattern = self.analysis_patterns['api_service']
        
        # Generate project name from prompt
        project_name = self._generate_project_name(prompt)
        
        return ProjectAnalysis(
            name=project_name,
            description=prompt,
            project_type=selected_pattern['type'],
            language=selected_pattern['language'],
            components=selected_pattern['components'].copy(),
            dependencies=selected_pattern['dependencies'].copy(),
            confidence=0.75,  # Medium confidence for pattern-based analysis
            estimated_complexity='medium',
            recommended_architecture='layered'
        )
    
    def _generate_project_name(self, prompt: str) -> str:
        """Generate a project name from the prompt."""
        
        # Extract key words from prompt
        words = prompt.lower().split()
        
        # Filter out common words
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'create', 'build', 'make', 'develop'}
        key_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Take first 2-3 meaningful words and capitalize
        if len(key_words) >= 2:
            name_parts = key_words[:3]
        else:
            name_parts = key_words[:1] + ['System']
        
        # Capitalize and join
        project_name = ''.join(word.capitalize() for word in name_parts)
        
        return project_name if project_name else 'AutoGeneratedProject'
    
    async def get_analysis_summary(self, analysis: ProjectAnalysis) -> Dict[str, Any]:
        """Generate a summary of the project analysis."""
        
        return {
            'project_name': analysis.name,
            'project_type': analysis.project_type.value,
            'primary_language': analysis.language,
            'component_count': len(analysis.components),
            'dependency_count': len(analysis.dependencies),
            'confidence_score': analysis.confidence,
            'complexity_level': analysis.estimated_complexity,
            'architecture_pattern': analysis.recommended_architecture,
            'top_components': analysis.components[:5],
            'key_dependencies': analysis.dependencies[:5]
        }