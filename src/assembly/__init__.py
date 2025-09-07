"""
Assembly Engine

Core code assembly and integration system:
- Repository Cloner: Git operations and repository management
- File Extractor: Selective file extraction based on analysis
- Code Integrator: Automated code merging and conflict resolution
- Project Generator: Final project structure and configuration
"""

from .repository_cloner import RepositoryCloner, CloneResult, CloneStatus
from .file_extractor import FileExtractor, ExtractionResult, ExtractedFile
from .code_integrator import CodeIntegrator, IntegrationResult, IntegrationStatus
from .project_generator import ProjectGenerator, GeneratedProject, ProjectStructure

__all__ = [
    'RepositoryCloner', 'CloneResult', 'CloneStatus',
    'FileExtractor', 'ExtractionResult', 'ExtractedFile',
    'CodeIntegrator', 'IntegrationResult', 'IntegrationStatus',
    'ProjectGenerator', 'GeneratedProject', 'ProjectStructure'
]