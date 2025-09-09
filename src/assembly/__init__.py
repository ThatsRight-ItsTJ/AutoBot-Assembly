#!/usr/bin/env python3
"""
Assembly Package

Components for assembling and integrating discovered code repositories.
"""

from .repository_cloner import RepositoryCloner, CloneResult
from .file_extractor import FileExtractor, ExtractionResult
from .code_integrator import CodeIntegrator, IntegrationResult
from .project_generator import ProjectGenerator, GeneratedProject

__all__ = [
    'RepositoryCloner', 'CloneResult',
    'FileExtractor', 'ExtractionResult', 
    'CodeIntegrator', 'IntegrationResult',
    'ProjectGenerator', 'GeneratedProject'
]