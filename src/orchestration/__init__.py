"""
Orchestration Module

Coordinates project analysis and search operations for the AutoBot Assembly System.
"""

from .project_analyzer import ProjectAnalyzer, ProjectAnalysis, ProjectType
from .search_orchestrator import SearchOrchestrator, SearchResults

__all__ = [
    'ProjectAnalyzer',
    'ProjectAnalysis', 
    'ProjectType',
    'SearchOrchestrator',
    'SearchResults'
]