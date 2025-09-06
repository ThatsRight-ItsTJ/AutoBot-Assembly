"""
Compatibility & License Analysis System

Framework compatibility checking and license compliance analysis:
- Framework Compatibility Checker: Ensures components can work together
- License Analyzer: Legal compliance and attribution requirements
- Compatibility Matrix Generator: Comprehensive compatibility assessment
"""

from .framework_checker import FrameworkCompatibilityChecker, CompatibilityMatrix, CompatibilityCheck
from .license_analyzer import LicenseAnalyzer, LicenseAnalysis, LicenseCompatibility

__all__ = [
    'FrameworkCompatibilityChecker', 'CompatibilityMatrix', 'CompatibilityCheck',
    'LicenseAnalyzer', 'LicenseAnalysis', 'LicenseCompatibility'
]