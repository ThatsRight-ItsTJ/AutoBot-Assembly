"""
Compatibility & License Analysis System

Framework compatibility checking and license compliance analysis.
"""

from .framework_checker import FrameworkCompatibilityChecker, CompatibilityCheck
from .license_analyzer import LicenseAnalyzer, LicenseAnalysis
from .compatibility_matrix import CompatibilityMatrixGenerator

__all__ = [
    'FrameworkCompatibilityChecker',
    'CompatibilityCheck',
    'LicenseAnalyzer', 
    'LicenseAnalysis',
    'CompatibilityMatrixGenerator',
    'MatrixEntry'
]