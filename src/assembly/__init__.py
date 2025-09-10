#!/usr/bin/env python3
"""
Assembly Package

Components for assembling and integrating discovered code repositories.
"""

from .code_integrator import PrecisionCodeExtractor, CodeComponent, IntegrationPattern
from .repository_cloner import RepositoryCloner, CloneResult
from .file_extractor import FileExtractor, ExtractionResult
from .project_generator import ProjectGenerator, GeneratedProject

__all__ = [
    'PrecisionCodeExtractor', 'CodeComponent', 'IntegrationPattern',
    'RepositoryCloner', 'CloneResult',
    'FileExtractor', 'ExtractionResult', 
    'ProjectGenerator', 'GeneratedProject'
]