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

# Import ConfigManager
try:
    from src.cli.config_manager import ConfigManager
except ImportError:
    ConfigManager = None


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
    
    def __init__(self, config_manager=None):
        self.logger = logging.getLogger(__name__)
        
        # Initialize configuration manager with error handling
        if config_manager:
            self.config_manager = config_manager
        elif ConfigManager:
            try:
                self.config_manager = ConfigManager()
                self.logger.info("ConfigManager initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize ConfigManager: {e}")
                self.config_manager = None
        else:
            self.logger.warning("ConfigManager not available, using fallback behavior")
            self.config_manager = None
        
        # Initialize AI provider configurations
        self.ai_providers = {}
        self._initialize_providers()
        
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
    
    def _initialize_providers(self):
        """Initialize AI provider configurations."""
        
        # Initialize Pollinations provider (always available)
        if aiohttp is not None:
            self.ai_providers['pollinations'] = {
                'url': 'https://text.pollinations.ai/openai',
                'available': True,
                'api_key': None  # Pollinations doesn't require API key for free tier
            }
        
        # If ConfigManager is not available, only use Pollinations
        if not self.config_manager:
            self.logger.warning("ConfigManager not available, only Pollinations AI will be available")
            return
        
        try:
            # Get preferred provider for this function
            api_config = self.config_manager.get_function_api_key('project_analyzer')
            
            # Get global API keys for other providers
            api_keys = self.config_manager.get_api_keys()
            
            # Initialize OpenAI provider
            if api_keys.get('openai_api_key'):
                self.ai_providers['openai'] = {
                    'url': 'https://api.openai.com/v1/chat/completions',
                    'available': True,
                    'api_key': api_keys['openai_api_key']
                }
            
            # Initialize Anthropic provider
            if api_keys.get('anthropic_api_key'):
                self.ai_providers['anthropic'] = {
                    'url': 'https://api.anthropic.com/v1/messages',
                    'available': True,
                    'api_key': api_keys['anthropic_api_key']
                }
            
            # Initialize Google provider
            if api_keys.get('google_api_key'):
                self.ai_providers['google'] = {
                    'url': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent',
                    'available': True,
                    'api_key': api_keys['google_api_key']
                }
            
            # Initialize Z.ai provider
            if api_keys.get('zai_api_key'):
                self.ai_providers['zai'] = {
                    'url': 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
                    'available': True,
                    'api_key': api_keys['zai_api_key']
                }
        except Exception as e:
            self.logger.error(f"Failed to initialize AI providers: {e}")
    
    async def analyze_project_prompt(self, prompt: str, provider: str = None) -> ProjectAnalysis:
        """
        Analyze a project prompt and generate comprehensive project specifications.
        
        Args:
            prompt: User's project description/requirements
            provider: AI provider to use for analysis (None for function's preferred provider)
            
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
    
    async def _get_ai_analysis(self, prompt: str, provider: str = None) -> Optional[ProjectAnalysis]:
        """Get AI-powered project analysis."""
        
        # If ConfigManager is not available, use Pollinations as fallback
        if not self.config_manager:
            self.logger.warning("ConfigManager not available, using Pollinations fallback")
            if 'pollinations' in self.ai_providers and self.ai_providers['pollinations']['available']:
                timeout = aiohttp.ClientTimeout(total=15)
                return await self._call_ai_provider('pollinations', prompt, timeout)
            return None
        
        try:
            # Get function API configuration
            api_config = self.config_manager.get_function_api_key('project_analyzer')
            timeout = aiohttp.ClientTimeout(total=api_config.get('timeout', 15))
            
            # If no provider specified, use function's preferred provider
            if not provider:
                provider = api_config['provider']
            
            # Try function-specific providers first
            if provider in self.ai_providers and self.ai_providers[provider]['available']:
                return await self._call_ai_provider(provider, prompt, timeout)
            
            # Try fallback providers
            fallback_providers = api_config.get('fallback_providers', [])
            for fallback_provider in fallback_providers:
                if fallback_provider in self.ai_providers and self.ai_providers[fallback_provider]['available']:
                    return await self._call_ai_provider(fallback_provider, prompt, timeout)
            
            # No available providers
            self.logger.warning(f"No available AI providers for project analysis")
            return None
        except Exception as e:
            self.logger.error(f"Error getting AI analysis: {e}")
            # Try Pollinations as final fallback
            if 'pollinations' in self.ai_providers and self.ai_providers['pollinations']['available']:
                timeout = aiohttp.ClientTimeout(total=15)
                return await self._call_ai_provider('pollinations', prompt, timeout)
            return None
    
    async def _call_ai_provider(self, provider: str, prompt: str, timeout: aiohttp.ClientTimeout) -> Optional[ProjectAnalysis]:
        """Call a specific AI provider."""
        
        provider_config = self.ai_providers[provider]
        url = provider_config['url']
        api_key = provider_config['api_key']
        
        if not api_key:
            self.logger.warning(f"No API key available for {provider}")
            return None
        
        try:
            # Simplified prompt for better AI response
            analysis_prompt = f"Analyze this project: {prompt}. Respond with project name, type (web_application/api_service/data_pipeline), language (python/javascript), 4 key components, and 4 main dependencies."
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'AutoBot-Assembly/1.0'
            }
            
            # Add authorization header if needed
            if provider != 'pollinations':
                headers['Authorization'] = f"Bearer {api_key}"
            
            # Prepare payload based on provider
            if provider == 'pollinations':
                payload = {
                    'messages': [
                        {
                            'role': 'user',
                            'content': f"You are a software architect. Analyze this project requirement: {analysis_prompt}"
                        }
                    ],
                    'model': 'gpt-4'
                }
            else:
                payload = {
                    'messages': [
                        {
                            'role': 'user',
                            'content': f"You are a software architect. Analyze this project requirement: {analysis_prompt}"
                        }
                    ],
                    'model': 'gpt-4' if provider == 'openai' else 'claude-3-sonnet-20240229' if provider == 'anthropic' else 'gemini-pro'
                }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=timeout) as response:
                    if response.status == 200:
                        result = await response.text()
                        self.logger.info(f"AI analysis successful with {provider}: {len(result)} characters")
                        return self._parse_ai_response(result, prompt)
                    else:
                        response_text = await response.text()
                        self.logger.warning(f"{provider} API returned status {response.status}: {response_text}")
        
        except Exception as e:
            self.logger.warning(f"AI analysis failed with {provider}: {e}")
        
        return None
    
    def _parse_ai_response(self, ai_response: str, original_prompt: str) -> ProjectAnalysis:
        """Parse AI response into ProjectAnalysis object."""
        
        try:
            # Try to extract meaningful information from any response format
            response_lower = ai_response.lower()
            
            # Extract project name from response or generate from prompt
            project_name = self._generate_project_name(original_prompt)
            
            # Determine project type from response or prompt
            project_type = ProjectType.WEB_APPLICATION
            if 'api' in response_lower or 'api' in original_prompt.lower():
                project_type = ProjectType.API_SERVICE
            elif 'data' in response_lower or 'analysis' in response_lower:
                project_type = ProjectType.DATA_PIPELINE
            
            # Use pattern-based components as fallback with AI enhancement
            pattern_analysis = self._pattern_based_analysis(original_prompt)
            
            return ProjectAnalysis(
                name=project_name,
                description=original_prompt,
                project_type=project_type,
                language='python',  # Default to Python
                components=pattern_analysis.components,
                dependencies=pattern_analysis.dependencies,
                confidence=0.85,  # Higher confidence for AI-assisted analysis
                estimated_complexity='medium',
                recommended_architecture='layered'
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