"""
File Analysis System

Comprehensive code analysis using multiple tools:
- MegaLinter: Multi-language code quality analysis
- Semgrep: Security and pattern analysis  
- AST-grep: Structural code analysis
- Unified Scorer: Combined scoring algorithm
"""

# Try to import MegaLinter with graceful handling of missing docker
try:
    from .megalinter_client import MegaLinterAnalyzer, MegaLinterResults, FileQualityScore
    MEGALINTER_AVAILABLE = True
except ImportError as e:
    if 'docker' in str(e):
        MEGALINTER_AVAILABLE = False
        # Create placeholder classes to avoid import errors
        class MegaLinterAnalyzer:
            def __init__(self, *args, **kwargs):
                raise ImportError("MegaLinter requires docker module")
        
        class MegaLinterResults:
            pass
        
        class FileQualityScore:
            pass
    else:
        # Re-raise if it's not a docker-related error
        raise

from .semgrep_client import SemgrepAnalyzer, SemgrepResults, SecurityScore
from .astgrep_client import ASTGrepAnalyzer, StructureAnalysis, AdaptationScore
from .unified_scorer import UnifiedFileScorer, CompositeFileScore

__all__ = [
    'MegaLinterAnalyzer', 'MegaLinterResults', 'FileQualityScore',
    'SemgrepAnalyzer', 'SemgrepResults', 'SecurityScore',
    'ASTGrepAnalyzer', 'StructureAnalysis', 'AdaptationScore',
    'UnifiedFileScorer', 'CompositeFileScore'
]