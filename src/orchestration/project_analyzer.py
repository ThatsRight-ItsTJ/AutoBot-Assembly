"""
Project Analyzer

AI-powered prompt analysis engine that understands user requirements
and translates them into actionable project specifications.
"""

import asyncio
import logging
import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import aiohttp
import os


class ProjectType(str, Enum):
    APPLICATION = "application"
    LIBRARY = "library"
    WEB_SERVICE = "web_service"
    CLI_TOOL = "cli_tool"
    GAME = "game"
    MOBILE_APP = "mobile_app"
    DESKTOP_APP = "desktop_app"
    UNKNOWN = "unknown"


@dataclass
class AnalysisResult:
    """Result of prompt analysis."""
    
    project_name: str
    project_type: ProjectType
    project_description: str
    recommended_language: str
    required_components: List[str]
    technical_requirements: List[str]
    complexity_score: float  # 0.0 to 1.0
    estimated_effort: str  # "low", "medium", "high"
    suggested_architecture: Dict[str, Any]
    keywords: List[str]
    confidence_score: float  # 0.0 to 1.0


class ProjectAnalyzer:
    """AI-powered project analyzer using multiple API providers."""
    
    def __init__(self, api_key: Optional[str] = None, api_provider: str = "pollinations"):
        self.logger = logging.getLogger(__name__)
        
        # API configuration with fallback support
        self.api_key = api_key or os.getenv('POLLINATIONS_API_KEY') or os.getenv('OPENAI_API_KEY')
        self.api_provider = api_provider.lower()
        
        # Determine which API to use based on available keys and provider preference
        self._setup_api_client()
        
        # Analysis patterns for fallback processing
        self.language_patterns = {
            'python': ['python', 'django', 'flask', 'fastapi', 'pandas', 'numpy', 'machine learning', 'ai', 'data'],
            'javascript': ['javascript', 'node', 'react', 'vue', 'angular', 'express', 'web', 'frontend'],
            'java': ['java', 'spring', 'maven', 'gradle', 'enterprise', 'android'],
            'go': ['go', 'golang', 'microservice', 'api', 'backend'],
            'rust': ['rust', 'performance', 'system', 'memory safe'],
            'cpp': ['c++', 'cpp', 'performance', 'game', 'system'],
            'csharp': ['c#', 'csharp', '.net', 'windows', 'unity']
        }
        
        self.project_type_patterns = {
            ProjectType.WEB_SERVICE: ['api', 'web service', 'rest', 'graphql', 'backend', 'server'],
            ProjectType.CLI_TOOL: ['cli', 'command line', 'terminal', 'script', 'automation'],
            ProjectType.LIBRARY: ['library', 'package', 'module', 'framework', 'sdk'],
            ProjectType.GAME: ['game', 'gaming', 'unity', 'pygame', 'graphics'],
            ProjectType.MOBILE_APP: ['mobile', 'android', 'ios', 'react native', 'flutter'],
            ProjectType.DESKTOP_APP: ['desktop', 'gui', 'tkinter', 'qt', 'electron'],
            ProjectType.APPLICATION: ['app', 'application', 'program', 'software']
        }
    
    def _setup_api_client(self):
        """Setup API client based on available keys and preferences."""
        
        # Check for OpenAI API key
        openai_key = os.getenv('OPENAI_API_KEY')
        
        # Check for other API keys
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        google_key = os.getenv('GOOGLE_API_KEY')
        
        # Determine the best API to use
        if self.api_provider == "openai" and openai_key:
            self.api_endpoint = "https://api.openai.com/v1/chat/completions"
            self.api_key = openai_key
            self.api_provider = "openai"
            self.logger.info("Using OpenAI API")
            
        elif self.api_provider == "anthropic" and anthropic_key:
            self.api_endpoint = "https://api.anthropic.com/v1/messages"
            self.api_key = anthropic_key
            self.api_provider = "anthropic"
            self.logger.info("Using Anthropic Claude API")
            
        elif self.api_provider == "google" and google_key:
            self.api_endpoint = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"
            self.api_key = google_key
            self.api_provider = "google"
            self.logger.info("Using Google Gemini API")
            
        elif openai_key:
            # Fallback to OpenAI if available
            self.api_endpoint = "https://api.openai.com/v1/chat/completions"
            self.api_key = openai_key
            self.api_provider = "openai"
            self.logger.info("Falling back to OpenAI API")
            
        else:
            # Default to Pollinations (free)
            self.api_endpoint = "https://text.pollinations.ai/"
            self.api_key = None
            self.api_provider = "pollinations"
            self.logger.info("Using Pollinations AI (free tier)")
    
    async def analyze_prompt(self, prompt: str, user_preferences: Optional[Dict[str, Any]] = None) -> AnalysisResult:
        """
        Analyze user prompt and extract project requirements.
        
        Args:
            prompt: User's project description
            user_preferences: Optional user preferences (language, type, etc.)
            
        Returns:
            AnalysisResult with extracted project information
        """
        
        self.logger.info(f"Analyzing prompt: {prompt[:100]}...")
        
        try:
            # Try AI analysis first
            if self.api_key or self.api_provider == "pollinations":
                analysis_result = await self._ai_analyze_prompt(prompt, user_preferences)
                if analysis_result:
                    return analysis_result
            
            # Fallback to rule-based analysis
            self.logger.warning("AI analysis failed, using rule-based fallback")
            return await self._fallback_analyze_prompt(prompt, user_preferences)
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            return await self._fallback_analyze_prompt(prompt, user_preferences)
    
    async def _ai_analyze_prompt(self, prompt: str, user_preferences: Optional[Dict[str, Any]] = None) -> Optional[AnalysisResult]:
        """Analyze prompt using AI API."""
        
        try:
            # Create analysis prompt
            system_prompt = """You are an expert software architect. Analyze the user's project description and provide a structured analysis in JSON format.

Return ONLY a valid JSON object with these exact fields:
{
    "project_name": "suggested_project_name",
    "project_type": "application|library|web_service|cli_tool|game|mobile_app|desktop_app",
    "project_description": "clear description of what the project does",
    "recommended_language": "python|javascript|java|go|rust|cpp|csharp",
    "required_components": ["component1", "component2", "component3"],
    "technical_requirements": ["requirement1", "requirement2"],
    "complexity_score": 0.7,
    "estimated_effort": "low|medium|high",
    "suggested_architecture": {"pattern": "mvc", "database": "sqlite", "framework": "flask"},
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "confidence_score": 0.9
}

Consider user preferences if provided. Be specific and practical."""

            user_message = f"Project description: {prompt}"
            if user_preferences:
                user_message += f"\nUser preferences: {json.dumps(user_preferences)}"
            
            # Make API request based on provider
            if self.api_provider == "openai":
                response = await self._call_openai_api(system_prompt, user_message)
            elif self.api_provider == "anthropic":
                response = await self._call_anthropic_api(system_prompt, user_message)
            elif self.api_provider == "google":
                response = await self._call_google_api(system_prompt, user_message)
            else:  # pollinations
                response = await self._call_pollinations_api(system_prompt, user_message)
            
            if not response:
                return None
            
            # Parse JSON response
            try:
                # Extract JSON from response if it contains other text
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    response = json_match.group()
                
                data = json.loads(response)
                
                return AnalysisResult(
                    project_name=data.get('project_name', 'autobot_project'),
                    project_type=ProjectType(data.get('project_type', 'application')),
                    project_description=data.get('project_description', prompt),
                    recommended_language=data.get('recommended_language', 'python'),
                    required_components=data.get('required_components', []),
                    technical_requirements=data.get('technical_requirements', []),
                    complexity_score=float(data.get('complexity_score', 0.5)),
                    estimated_effort=data.get('estimated_effort', 'medium'),
                    suggested_architecture=data.get('suggested_architecture', {}),
                    keywords=data.get('keywords', []),
                    confidence_score=float(data.get('confidence_score', 0.8))
                )
                
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                self.logger.error(f"Failed to parse AI response: {e}")
                return None
                
        except Exception as e:
            self.logger.error(f"AI analysis failed: {e}")
            return None
    
    async def _call_openai_api(self, system_prompt: str, user_message: str) -> Optional[str]:
        """Call OpenAI API."""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 1000,
            "temperature": 0.3
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_endpoint, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['choices'][0]['message']['content']
                else:
                    self.logger.error(f"OpenAI API error: {response.status}")
                    return None
    
    async def _call_anthropic_api(self, system_prompt: str, user_message: str) -> Optional[str]:
        """Call Anthropic Claude API."""
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": 1000,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_message}
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_endpoint, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['content'][0]['text']
                else:
                    self.logger.error(f"Anthropic API error: {response.status}")
                    return None
    
    async def _call_google_api(self, system_prompt: str, user_message: str) -> Optional[str]:
        """Call Google Gemini API."""
        
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "contents": [{
                "parts": [{
                    "text": f"{system_prompt}\n\n{user_message}"
                }]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 1000
            }
        }
        
        url = f"{self.api_endpoint}?key={self.api_key}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['candidates'][0]['content']['parts'][0]['text']
                else:
                    self.logger.error(f"Google API error: {response.status}")
                    return None
    
    async def _call_pollinations_api(self, system_prompt: str, user_message: str) -> Optional[str]:
        """Call Pollinations AI API (free tier)."""
        
        # Pollinations uses a simple text endpoint
        full_prompt = f"{system_prompt}\n\nUser request: {user_message}\n\nResponse:"
        
        data = {
            "messages": [
                {"role": "user", "content": full_prompt}
            ],
            "model": "openai",
            "seed": 42,
            "jsonMode": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_endpoint, json=data) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    self.logger.error(f"Pollinations API error: {response.status}")
                    return None
    
    async def _fallback_analyze_prompt(self, prompt: str, user_preferences: Optional[Dict[str, Any]] = None) -> AnalysisResult:
        """Fallback rule-based analysis when AI is unavailable."""
        
        prompt_lower = prompt.lower()
        
        # Detect project type
        detected_type = ProjectType.APPLICATION
        for project_type, patterns in self.project_type_patterns.items():
            if any(pattern in prompt_lower for pattern in patterns):
                detected_type = project_type
                break
        
        # Detect language
        detected_language = "python"  # Default
        language_scores = {}
        
        for language, patterns in self.language_patterns.items():
            score = sum(1 for pattern in patterns if pattern in prompt_lower)
            if score > 0:
                language_scores[language] = score
        
        if language_scores:
            detected_language = max(language_scores, key=language_scores.get)
        
        # Apply user preferences
        if user_preferences:
            if 'language' in user_preferences:
                detected_language = user_preferences['language']
            if 'project_type' in user_preferences:
                detected_type = ProjectType(user_preferences['project_type'])
        
        # Extract keywords
        keywords = []
        for word in prompt_lower.split():
            if len(word) > 3 and word.isalpha():
                keywords.append(word)
        keywords = list(set(keywords))[:10]  # Unique, max 10
        
        # Generate project name
        project_name = self._generate_project_name(prompt, detected_type, detected_language)
        
        # Estimate complexity
        complexity_indicators = ['complex', 'advanced', 'enterprise', 'scalable', 'distributed', 'machine learning', 'ai']
        complexity_score = min(sum(0.2 for indicator in complexity_indicators if indicator in prompt_lower), 1.0)
        if complexity_score == 0:
            complexity_score = 0.5  # Default medium complexity
        
        # Determine effort
        if complexity_score < 0.3:
            effort = "low"
        elif complexity_score < 0.7:
            effort = "medium"
        else:
            effort = "high"
        
        # Generate components and requirements
        components = self._extract_components(prompt_lower, detected_language, detected_type)
        requirements = self._extract_requirements(prompt_lower, detected_type)
        
        # Suggest architecture
        architecture = self._suggest_architecture(detected_type, detected_language, complexity_score)
        
        return AnalysisResult(
            project_name=project_name,
            project_type=detected_type,
            project_description=prompt,
            recommended_language=detected_language,
            required_components=components,
            technical_requirements=requirements,
            complexity_score=complexity_score,
            estimated_effort=effort,
            suggested_architecture=architecture,
            keywords=keywords,
            confidence_score=0.6  # Lower confidence for rule-based analysis
        )
    
    def _generate_project_name(self, prompt: str, project_type: ProjectType, language: str) -> str:
        """Generate a project name from the prompt."""
        
        # Extract meaningful words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', prompt.lower())
        
        # Filter out common words
        stop_words = {'the', 'and', 'for', 'with', 'that', 'this', 'create', 'build', 'make', 'develop'}
        meaningful_words = [w for w in words if w not in stop_words][:3]
        
        if meaningful_words:
            name = '_'.join(meaningful_words)
        else:
            name = f"{language}_{project_type.value}"
        
        return name
    
    def _extract_components(self, prompt: str, language: str, project_type: ProjectType) -> List[str]:
        """Extract required components from prompt."""
        
        components = []
        
        # Language-specific components
        if language == 'python':
            if 'web' in prompt or 'api' in prompt:
                components.extend(['flask', 'requests', 'sqlalchemy'])
            if 'data' in prompt or 'analysis' in prompt:
                components.extend(['pandas', 'numpy'])
            if 'machine learning' in prompt or 'ai' in prompt:
                components.extend(['scikit-learn', 'tensorflow'])
        
        elif language == 'javascript':
            if 'web' in prompt or 'frontend' in prompt:
                components.extend(['react', 'axios'])
            if 'backend' in prompt or 'api' in prompt:
                components.extend(['express', 'cors'])
        
        elif language == 'java':
            if 'web' in prompt or 'api' in prompt:
                components.extend(['spring-boot', 'jackson'])
            if 'database' in prompt:
                components.extend(['hibernate', 'mysql-connector'])
        
        # Project type specific components
        if project_type == ProjectType.WEB_SERVICE:
            components.extend(['authentication', 'database', 'logging'])
        elif project_type == ProjectType.CLI_TOOL:
            components.extend(['argument-parser', 'configuration'])
        
        return list(set(components))[:10]  # Unique, max 10
    
    def _extract_requirements(self, prompt: str, project_type: ProjectType) -> List[str]:
        """Extract technical requirements from prompt."""
        
        requirements = []
        
        # Common requirements based on keywords
        if 'database' in prompt:
            requirements.append('Database integration')
        if 'api' in prompt:
            requirements.append('REST API endpoints')
        if 'authentication' in prompt or 'login' in prompt:
            requirements.append('User authentication')
        if 'test' in prompt:
            requirements.append('Unit testing')
        if 'deploy' in prompt:
            requirements.append('Deployment configuration')
        if 'docker' in prompt:
            requirements.append('Docker containerization')
        
        # Project type specific requirements
        if project_type == ProjectType.WEB_SERVICE:
            requirements.extend(['HTTP server', 'Request validation', 'Error handling'])
        elif project_type == ProjectType.CLI_TOOL:
            requirements.extend(['Command-line interface', 'Help documentation'])
        elif project_type == ProjectType.LIBRARY:
            requirements.extend(['Public API', 'Documentation', 'Package distribution'])
        
        return list(set(requirements))[:8]  # Unique, max 8
    
    def _suggest_architecture(self, project_type: ProjectType, language: str, complexity: float) -> Dict[str, Any]:
        """Suggest architecture based on project characteristics."""
        
        architecture = {
            'pattern': 'mvc',
            'database': 'sqlite',
            'framework': 'basic'
        }
        
        # Adjust based on project type
        if project_type == ProjectType.WEB_SERVICE:
            architecture.update({
                'pattern': 'rest_api',
                'database': 'postgresql' if complexity > 0.6 else 'sqlite',
                'caching': 'redis' if complexity > 0.7 else None
            })
        
        elif project_type == ProjectType.CLI_TOOL:
            architecture.update({
                'pattern': 'command_pattern',
                'configuration': 'yaml',
                'logging': 'structured'
            })
        
        # Language-specific adjustments
        if language == 'python':
            if project_type == ProjectType.WEB_SERVICE:
                architecture['framework'] = 'fastapi' if complexity > 0.6 else 'flask'
            elif project_type == ProjectType.CLI_TOOL:
                architecture['framework'] = 'click'
        
        elif language == 'javascript':
            if project_type == ProjectType.WEB_SERVICE:
                architecture['framework'] = 'express'
                architecture['runtime'] = 'nodejs'
        
        elif language == 'java':
            architecture['framework'] = 'spring-boot'
            architecture['build_tool'] = 'maven'
        
        return architecture


# Example usage and testing
async def test_analyzer():
    """Test the project analyzer with different API providers."""
    
    test_prompts = [
        "Create a web scraper for news articles using Python",
        "Build a REST API for a todo application",
        "Make a CLI tool for file processing",
        "Develop a machine learning classifier for image recognition"
    ]
    
    # Test with different API providers
    providers = ["pollinations", "openai", "anthropic", "google"]
    
    for provider in providers:
        print(f"\n=== Testing {provider.upper()} API ===")
        
        analyzer = ProjectAnalyzer(api_provider=provider)
        
        for prompt in test_prompts:
            try:
                result = await analyzer.analyze_prompt(prompt)
                print(f"\nPrompt: {prompt}")
                print(f"Project: {result.project_name}")
                print(f"Type: {result.project_type}")
                print(f"Language: {result.recommended_language}")
                print(f"Confidence: {result.confidence_score:.2f}")
                
            except Exception as e:
                print(f"Error analyzing '{prompt}': {e}")


if __name__ == "__main__":
    asyncio.run(test_analyzer())