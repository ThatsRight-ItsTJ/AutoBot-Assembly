"""
Compatibility & License Analysis System

Framework compatibility checking and license compliance analysis.
"""

from .framework_checker import FrameworkCompatibilityChecker, CompatibilityResult
from .license_analyzer import LicenseAnalyzer, LicenseAnalysisResult
from .compatibility_matrix import CompatibilityMatrix, MatrixEntry

__all__ = [
    'FrameworkCompatibilityChecker',
    'CompatibilityResult',
    'LicenseAnalyzer', 
    'LicenseAnalysisResult',
    'CompatibilityMatrix',
    'MatrixEntry'
]