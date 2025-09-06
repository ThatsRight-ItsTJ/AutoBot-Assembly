"""
File Analysis System

Comprehensive code analysis using multiple tools:
- MegaLinter: Multi-language code quality analysis
- Semgrep: Security and pattern analysis  
- AST-grep: Structural code analysis
- Unified Scorer: Combined scoring algorithm
"""

from .megalinter_client import MegaLinterAnalyzer, MegaLinterResults, FileQualityScore
from .semgrep_client import SemgrepAnalyzer, SemgrepResults, SecurityScore
from .astgrep_client import ASTGrepAnalyzer, StructureAnalysis, AdaptationScore
from .unified_scorer import UnifiedFileScorer, CompositeFileScore

__all__ = [
    'MegaLinterAnalyzer', 'MegaLinterResults', 'FileQualityScore',
    'SemgrepAnalyzer', 'SemgrepResults', 'SecurityScore',
    'ASTGrepAnalyzer', 'StructureAnalysis', 'AdaptationScore',
    'UnifiedFileScorer', 'CompositeFileScore'
]