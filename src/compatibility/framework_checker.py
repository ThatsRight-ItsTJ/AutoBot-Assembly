#!/usr/bin/env python3
"""
Framework Compatibility Checker

Validates compatibility between different frameworks, libraries, and project requirements.
"""

import asyncio
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import re
from pathlib import Path


class CompatibilityLevel(Enum):
    """Compatibility levels between components."""
    COMPATIBLE = "compatible"
    PARTIALLY_COMPATIBLE = "partially_compatible"
    INCOMPATIBLE = "incompatible"
    UNKNOWN = "unknown"


@dataclass
class CompatibilityCheck:
    """Result of a compatibility check."""
    component1: str
    component2: str
    level: CompatibilityLevel
    reason: str
    suggestions: List[str]
    confidence: float


@dataclass
class FrameworkInfo:
    """Information about a framework or library."""
    name: str
    version: str
    language: str
    category: str
    dependencies: List[str]
    conflicts: List[str]
    python_versions: List[str]
    os_support: List[str]


class FrameworkCompatibilityChecker:
    """Checks compatibility between frameworks and libraries."""
    
    def __init__(self):
        """Initialize the compatibility checker."""
        self.compatibility_matrix = self._load_compatibility_matrix()
        self.framework_info = self._load_framework_info()
    
    def _load_compatibility_matrix(self) -> Dict[str, Dict[str, CompatibilityLevel]]:
        """Load the compatibility matrix."""
        # Basic compatibility matrix - can be expanded
        return {
            'flask': {
                'django': CompatibilityLevel.INCOMPATIBLE,
                'fastapi': CompatibilityLevel.PARTIALLY_COMPATIBLE,
                'requests': CompatibilityLevel.COMPATIBLE,
                'sqlalchemy': CompatibilityLevel.COMPATIBLE,
                'pytest': CompatibilityLevel.COMPATIBLE,
            },
            'django': {
                'flask': CompatibilityLevel.INCOMPATIBLE,
                'fastapi': CompatibilityLevel.INCOMPATIBLE,
                'requests': CompatibilityLevel.COMPATIBLE,
                'pytest': CompatibilityLevel.COMPATIBLE,
            },
            'fastapi': {
                'flask': CompatibilityLevel.PARTIALLY_COMPATIBLE,
                'django': CompatibilityLevel.INCOMPATIBLE,
                'requests': CompatibilityLevel.COMPATIBLE,
                'sqlalchemy': CompatibilityLevel.COMPATIBLE,
                'pytest': CompatibilityLevel.COMPATIBLE,
            },
            'requests': {
                'flask': CompatibilityLevel.COMPATIBLE,
                'django': CompatibilityLevel.COMPATIBLE,
                'fastapi': CompatibilityLevel.COMPATIBLE,
                'beautifulsoup4': CompatibilityLevel.COMPATIBLE,
            },
            'beautifulsoup4': {
                'requests': CompatibilityLevel.COMPATIBLE,
                'lxml': CompatibilityLevel.COMPATIBLE,
                'html5lib': CompatibilityLevel.COMPATIBLE,
            }
        }
    
    def _load_framework_info(self) -> Dict[str, FrameworkInfo]:
        """Load framework information."""
        return {
            'flask': FrameworkInfo(
                name='Flask',
                version='>=2.0.0',
                language='python',
                category='web_framework',
                dependencies=['werkzeug', 'jinja2'],
                conflicts=['django'],
                python_versions=['3.7', '3.8', '3.9', '3.10', '3.11'],
                os_support=['linux', 'windows', 'macos']
            ),
            'django': FrameworkInfo(
                name='Django',
                version='>=4.0.0',
                language='python',
                category='web_framework',
                dependencies=['sqlparse', 'asgiref'],
                conflicts=['flask'],
                python_versions=['3.8', '3.9', '3.10', '3.11'],
                os_support=['linux', 'windows', 'macos']
            ),
            'fastapi': FrameworkInfo(
                name='FastAPI',
                version='>=0.68.0',
                language='python',
                category='web_framework',
                dependencies=['starlette', 'pydantic'],
                conflicts=[],
                python_versions=['3.7', '3.8', '3.9', '3.10', '3.11'],
                os_support=['linux', 'windows', 'macos']
            ),
            'requests': FrameworkInfo(
                name='Requests',
                version='>=2.25.0',
                language='python',
                category='http_client',
                dependencies=['urllib3', 'certifi'],
                conflicts=[],
                python_versions=['3.7', '3.8', '3.9', '3.10', '3.11'],
                os_support=['linux', 'windows', 'macos']
            ),
            'beautifulsoup4': FrameworkInfo(
                name='Beautiful Soup',
                version='>=4.9.0',
                language='python',
                category='html_parser',
                dependencies=[],
                conflicts=[],
                python_versions=['3.6', '3.7', '3.8', '3.9', '3.10', '3.11'],
                os_support=['linux', 'windows', 'macos']
            )
        }
    
    async def check_compatibility(self, component1: str, component2: str) -> CompatibilityCheck:
        """Check compatibility between two components."""
        component1_lower = component1.lower()
        component2_lower = component2.lower()
        
        # Check direct compatibility matrix
        if component1_lower in self.compatibility_matrix:
            if component2_lower in self.compatibility_matrix[component1_lower]:
                level = self.compatibility_matrix[component1_lower][component2_lower]
                return CompatibilityCheck(
                    component1=component1,
                    component2=component2,
                    level=level,
                    reason=f"Direct compatibility check: {level.value}",
                    suggestions=self._get_compatibility_suggestions(component1_lower, component2_lower, level),
                    confidence=0.9
                )
        
        # Check reverse compatibility
        if component2_lower in self.compatibility_matrix:
            if component1_lower in self.compatibility_matrix[component2_lower]:
                level = self.compatibility_matrix[component2_lower][component1_lower]
                return CompatibilityCheck(
                    component1=component1,
                    component2=component2,
                    level=level,
                    reason=f"Reverse compatibility check: {level.value}",
                    suggestions=self._get_compatibility_suggestions(component1_lower, component2_lower, level),
                    confidence=0.9
                )
        
        # Check framework info for conflicts
        info1 = self.framework_info.get(component1_lower)
        info2 = self.framework_info.get(component2_lower)
        
        if info1 and info2:
            if component2_lower in info1.conflicts or component1_lower in info2.conflicts:
                return CompatibilityCheck(
                    component1=component1,
                    component2=component2,
                    level=CompatibilityLevel.INCOMPATIBLE,
                    reason="Known conflict between frameworks",
                    suggestions=[f"Consider using {component1} OR {component2}, not both"],
                    confidence=0.8
                )
            
            # Check if same category (potential conflict)
            if info1.category == info2.category and info1.category in ['web_framework', 'orm']:
                return CompatibilityCheck(
                    component1=component1,
                    component2=component2,
                    level=CompatibilityLevel.PARTIALLY_COMPATIBLE,
                    reason=f"Both are {info1.category}s - may conflict",
                    suggestions=[f"Consider using only one {info1.category}"],
                    confidence=0.7
                )
        
        # Default to unknown
        return CompatibilityCheck(
            component1=component1,
            component2=component2,
            level=CompatibilityLevel.UNKNOWN,
            reason="No compatibility information available",
            suggestions=["Test compatibility manually", "Check documentation"],
            confidence=0.3
        )
    
    def _get_compatibility_suggestions(self, comp1: str, comp2: str, level: CompatibilityLevel) -> List[str]:
        """Get suggestions based on compatibility level."""
        if level == CompatibilityLevel.COMPATIBLE:
            return ["These components work well together"]
        elif level == CompatibilityLevel.PARTIALLY_COMPATIBLE:
            return [
                "These components may work together with some configuration",
                "Check for version compatibility",
                "Test thoroughly before deployment"
            ]
        elif level == CompatibilityLevel.INCOMPATIBLE:
            return [
                f"Avoid using {comp1} and {comp2} together",
                f"Choose either {comp1} OR {comp2}",
                "Look for alternative solutions"
            ]
        else:
            return ["Research compatibility manually", "Test in development environment"]
    
    async def check_project_compatibility(self, components: List[str]) -> List[CompatibilityCheck]:
        """Check compatibility for all components in a project."""
        results = []
        
        for i, comp1 in enumerate(components):
            for comp2 in components[i+1:]:
                check = await self.check_compatibility(comp1, comp2)
                results.append(check)
        
        return results
    
    async def get_compatibility_score(self, components: List[str]) -> float:
        """Get overall compatibility score for a set of components."""
        if len(components) < 2:
            return 1.0
        
        checks = await self.check_project_compatibility(components)
        
        if not checks:
            return 1.0
        
        score_map = {
            CompatibilityLevel.COMPATIBLE: 1.0,
            CompatibilityLevel.PARTIALLY_COMPATIBLE: 0.6,
            CompatibilityLevel.INCOMPATIBLE: 0.0,
            CompatibilityLevel.UNKNOWN: 0.5
        }
        
        total_score = sum(score_map[check.level] * check.confidence for check in checks)
        max_score = sum(check.confidence for check in checks)
        
        return total_score / max_score if max_score > 0 else 0.5
    
    def get_framework_info(self, framework: str) -> Optional[FrameworkInfo]:
        """Get information about a specific framework."""
        return self.framework_info.get(framework.lower())
    
    def get_compatible_frameworks(self, framework: str) -> List[str]:
        """Get list of frameworks compatible with the given framework."""
        framework_lower = framework.lower()
        compatible = []
        
        if framework_lower in self.compatibility_matrix:
            for other, level in self.compatibility_matrix[framework_lower].items():
                if level == CompatibilityLevel.COMPATIBLE:
                    compatible.append(other)
        
        return compatible
    
    def suggest_alternatives(self, incompatible_pair: Tuple[str, str]) -> List[str]:
        """Suggest alternatives for incompatible components."""
        comp1, comp2 = incompatible_pair
        suggestions = []
        
        # Get compatible alternatives for each component
        comp1_alternatives = self.get_compatible_frameworks(comp2)
        comp2_alternatives = self.get_compatible_frameworks(comp1)
        
        if comp1_alternatives:
            suggestions.append(f"Instead of {comp1}, consider: {', '.join(comp1_alternatives)}")
        
        if comp2_alternatives:
            suggestions.append(f"Instead of {comp2}, consider: {', '.join(comp2_alternatives)}")
        
        return suggestions


# Example usage
async def main():
    """Example usage of the compatibility checker."""
    checker = FrameworkCompatibilityChecker()
    
    # Check individual compatibility
    result = await checker.check_compatibility("flask", "django")
    print(f"Flask vs Django: {result.level.value} - {result.reason}")
    
    # Check project compatibility
    components = ["flask", "requests", "beautifulsoup4", "pytest"]
    checks = await checker.check_project_compatibility(components)
    
    print(f"\nProject compatibility checks:")
    for check in checks:
        print(f"{check.component1} + {check.component2}: {check.level.value}")
    
    # Get compatibility score
    score = await checker.get_compatibility_score(components)
    print(f"\nOverall compatibility score: {score:.2f}")


if __name__ == "__main__":
    asyncio.run(main())