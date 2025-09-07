"""
AutoBot Assembly System - Main Package

A comprehensive AI-powered system for automated project assembly and code generation.
"""

__version__ = "1.0.0"
__author__ = "AutoBot Assembly Team"

# Make key classes available at package level
try:
    from .orchestration.project_analyzer import ProjectAnalyzer
    from .orchestration.search_orchestrator import SearchOrchestrator
    from .assembly.project_generator import ProjectGenerator
    from .reporting.ai_integrated_reporter import AIIntegratedReporter
    from .search.tier1_packages import PackageSearcher
    from .search.tier2_curated import CuratedSearcher
    from .search.tier3_discovery import GitHubDiscoverer
except ImportError:
    # Graceful fallback if some modules have issues
    pass

__all__ = [
    'ProjectAnalyzer',
    'SearchOrchestrator', 
    'ProjectGenerator',
    'AIIntegratedReporter',
    'PackageSearcher',
    'CuratedSearcher',
    'GitHubDiscoverer'
]