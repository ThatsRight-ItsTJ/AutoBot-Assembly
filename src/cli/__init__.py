"""
Command Line Interface

Interactive command-line interface for the AutoBot Assembly System:
- AutoBot CLI: Interactive prompt processing and project generation
- Progress Reporter: Real-time progress tracking and status updates
- Configuration Manager: User settings and preferences management
"""

from .autobot_cli import AutoBotCLI

__all__ = [
    'AutoBotCLI'
]