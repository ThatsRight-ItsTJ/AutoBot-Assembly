"""
AI Prompt Analysis Engine

Transforms user prompts into structured project requirements using Pollinations AI.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

import aiohttp
from pydantic import BaseModel, Field


class ProjectType(str, Enum):
    WEB_APP = "web_app"
    API_SERVICE = "api_service"
    CLI_TOOL = "cli_tool"
    DESKTOP_APP = "desktop_app"
    MOBILE_APP = "mobile_app"
    LIBRARY = "library"
    GAME = "game"


class ComplexityLevel(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


@dataclass
class ProjectStructure:
    project_type: ProjectType
    core_components: List[str]
    file_structure: Dict[str, List[str]]
    dependencies: List[str]
    search_keywords: List[str]
    complexity_level: ComplexityLevel
    language: str
    frameworks: List[str]
    estimated_files: int


class ProjectAnalyzer:
    """Converts natural language prompts to structured project requirements."""
    
    def __init__(self, pollinations_endpoint: str = "https://text.pollinations.ai/openai"):
        self.pollinations_endpoint = pollinations_endpoint
        self.logger = logging.getLogger(__name__)
        
    async def analyze_prompt(self, user_prompt: str, language: str) -> ProjectStructure:
        """
        Converts natural language to structured project requirements.
        
        Args:
            user_prompt: Natural language description of the project
            language: Target programming language
            
        Returns:
            ProjectStructure with analyzed requirements
        """
        analysis_prompt = self._create_analysis_prompt(user_prompt, language)
        
        try:
            response = await self._call_pollinations(analysis_prompt)
            return self._parse_project_structure(response, language)
        except Exception as e:
            self.logger.error(f"Error analyzing prompt: {e}")
            return self._create_fallback_structure(user_prompt, language)
    
    def _create_analysis_prompt(self, user_prompt: str, language: str) -> str:
        """Create structured prompt for AI analysis."""
        return f"""
        Analyze this project request: "{user_prompt}"
        Target Language: {language}
        
        Return JSON with:
        1. project_type: (web_app, api_service, cli_tool, desktop_app, mobile_app, library, game)
        2. core_components: [list of required components like "authentication", "database", "api", "frontend"]
        3. file_structure: {{"folder": ["files"]}} - typical project structure
        4. dependencies: [framework/library requirements]
        5. search_keywords: [GitHub search terms for finding relevant repos]
        6. complexity_level: (simple, moderate, complex)
        7. frameworks: [specific frameworks mentioned or implied]
        8. estimated_files: approximate number of files needed
        
        Focus on technical implementation details, not business logic.
        Be specific about component names that would appear in GitHub repositories.
        
        Example output:
        {{
            "project_type": "api_service",
            "core_components": ["authentication", "database", "api_routes", "middleware"],
            "file_structure": {{
                "src": ["main.py", "models.py", "routes.py"],
                "config": ["settings.py", "database.py"],
                "tests": ["test_api.py", "test_auth.py"]
            }},
            "dependencies": ["fastapi", "sqlalchemy", "jwt", "redis"],
            "search_keywords": ["fastapi jwt", "sqlalchemy models", "api authentication"],
            "complexity_level": "moderate",
            "frameworks": ["FastAPI", "SQLAlchemy"],
            "estimated_files": 15
        }}
        """
    
    async def _call_pollinations(self, prompt: str) -> str:
        """Make API call to Pollinations AI."""
        payload = {
            "model": "openai",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a technical project analyzer. Return only valid JSON."
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
                    result = await response.text()
                    return result
                else:
                    raise Exception(f"API call failed with status {response.status}")
    
    def _parse_project_structure(self, response: str, language: str) -> ProjectStructure:
        """Parse AI response into ProjectStructure."""
        try:
            data = json.loads(response)
            
            return ProjectStructure(
                project_type=ProjectType(data.get("project_type", "api_service")),
                core_components=data.get("core_components", []),
                file_structure=data.get("file_structure", {}),
                dependencies=data.get("dependencies", []),
                search_keywords=data.get("search_keywords", []),
                complexity_level=ComplexityLevel(data.get("complexity_level", "moderate")),
                language=language,
                frameworks=data.get("frameworks", []),
                estimated_files=data.get("estimated_files", 10)
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.logger.error(f"Error parsing AI response: {e}")
            return self._create_fallback_structure("", language)
    
    def _create_fallback_structure(self, user_prompt: str, language: str) -> ProjectStructure:
        """Create basic structure when AI analysis fails."""
        # Simple keyword-based fallback
        components = []
        keywords = []
        project_type = ProjectType.API_SERVICE
        
        prompt_lower = user_prompt.lower()
        
        if any(word in prompt_lower for word in ["web", "website", "frontend", "react", "vue"]):
            project_type = ProjectType.WEB_APP
            components = ["frontend", "routing", "components"]
            keywords = ["react components", "web app", "frontend"]
        elif any(word in prompt_lower for word in ["api", "service", "backend", "server"]):
            project_type = ProjectType.API_SERVICE
            components = ["api", "routes", "middleware"]
            keywords = ["api service", "backend", "server"]
        elif any(word in prompt_lower for word in ["cli", "command", "terminal"]):
            project_type = ProjectType.CLI_TOOL
            components = ["cli", "commands", "parser"]
            keywords = ["cli tool", "command line", "argparse"]
        
        if "auth" in prompt_lower:
            components.append("authentication")
            keywords.append("authentication")
        if "database" in prompt_lower or "db" in prompt_lower:
            components.append("database")
            keywords.append("database")
        
        return ProjectStructure(
            project_type=project_type,
            core_components=components,
            file_structure={"src": ["main.py"], "config": ["settings.py"]},
            dependencies=[],
            search_keywords=keywords,
            complexity_level=ComplexityLevel.MODERATE,
            language=language,
            frameworks=[],
            estimated_files=8
        )


# Example usage and testing
async def main():
    analyzer = ProjectAnalyzer()
    
    test_prompts = [
        ("Create a Python FastAPI application with JWT authentication", "python"),
        ("Build a React dashboard with user management", "javascript"),
        ("Make a CLI tool for file processing", "python")
    ]
    
    for prompt, language in test_prompts:
        print(f"\nAnalyzing: {prompt}")
        result = await analyzer.analyze_prompt(prompt, language)
        print(f"Type: {result.project_type}")
        print(f"Components: {result.core_components}")
        print(f"Keywords: {result.search_keywords}")
        print(f"Complexity: {result.complexity_level}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())