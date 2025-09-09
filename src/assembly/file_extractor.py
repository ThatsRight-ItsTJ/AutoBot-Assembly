#!/usr/bin/env python3
"""
File Extractor

Extracts and processes files from cloned repositories for integration.
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import fnmatch
import mimetypes
import json

# Use absolute imports
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.unified_scorer import CompositeFileScore, UnifiedFileScorer


@dataclass
class ExtractedFile:
    """Represents an extracted file with metadata."""
    file_path: str
    relative_path: str
    content: str
    file_type: str
    language: str
    size_bytes: int
    quality_score: Optional[CompositeFileScore] = None
    is_main_file: bool = False
    is_config_file: bool = False
    is_test_file: bool = False
    dependencies: List[str] = None


@dataclass
class ExtractionResult:
    """Result of file extraction from a repository."""
    repository_name: str
    repository_path: str
    extracted_files: List[ExtractedFile]
    total_files_found: int
    extraction_time_seconds: float
    language_distribution: Dict[str, int]
    file_type_distribution: Dict[str, int]
    main_files: List[ExtractedFile]
    config_files: List[ExtractedFile]
    test_files: List[ExtractedFile]


class FileExtractor:
    """Extracts relevant files from cloned repositories."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.file_scorer = UnifiedFileScorer()
        
        # File patterns to include/exclude
        self.include_patterns = {
            'python': ['*.py', '*.pyx', '*.pyi'],
            'javascript': ['*.js', '*.jsx', '*.ts', '*.tsx', '*.mjs'],
            'java': ['*.java', '*.kt', '*.scala'],
            'config': ['*.json', '*.yaml', '*.yml', '*.toml', '*.ini', '*.cfg', '*.conf'],
            'docs': ['*.md', '*.rst', '*.txt', 'README*', 'CHANGELOG*', 'LICENSE*'],
            'build': ['requirements.txt', 'package.json', 'pom.xml', 'build.gradle', 'Dockerfile', 'docker-compose.yml']
        }
        
        self.exclude_patterns = [
            '*/.*',  # Hidden files/directories
            '*/__pycache__/*',
            '*/node_modules/*',
            '*/venv/*',
            '*/env/*',
            '*/.git/*',
            '*/.svn/*',
            '*/build/*',
            '*/dist/*',
            '*/target/*',
            '*.pyc',
            '*.pyo',
            '*.class',
            '*.o',
            '*.so',
            '*.dll',
            '*.exe'
        ]
        
        # Main file indicators
        self.main_file_patterns = [
            'main.py', 'app.py', 'run.py', 'server.py', 'cli.py',
            'index.js', 'app.js', 'server.js', 'main.js',
            'Main.java', 'Application.java', 'App.java'
        ]
        
        # Test file patterns
        self.test_file_patterns = [
            'test_*.py', '*_test.py', 'tests.py',
            '*.test.js', '*.spec.js', 'test*.js',
            '*Test.java', '*Tests.java'
        ]
        
        # Config file patterns
        self.config_file_patterns = [
            'config.py', 'settings.py', 'configuration.py',
            'config.js', 'config.json', 'package.json',
            'application.properties', 'application.yml'
        ]
    
    async def extract_files(
        self,
        clone_results: List[Any],
        language: str = "python",
        extraction_criteria: Optional[Dict[str, Any]] = None
    ) -> List[ExtractionResult]:
        """
        Extract files from cloned repositories.
        
        Args:
            clone_results: List of CloneResult objects
            language: Primary programming language to focus on
            extraction_criteria: Additional criteria for extraction
            
        Returns:
            List of ExtractionResult objects
        """
        
        criteria = extraction_criteria or {}
        max_files_per_repo = criteria.get('max_files_per_repo', 50)
        min_file_size = criteria.get('min_file_size_bytes', 10)
        max_file_size = criteria.get('max_file_size_bytes', 1024 * 1024)  # 1MB
        
        extraction_results = []
        
        for clone_result in clone_results:
            try:
                self.logger.info(f"Extracting files from {clone_result.repository_name}")
                
                start_time = asyncio.get_event_loop().time()
                
                # Get file patterns for the language
                include_patterns = self._get_include_patterns(language)
                
                # Find all relevant files
                all_files = self._find_files(
                    clone_result.local_path,
                    include_patterns,
                    max_files_per_repo
                )
                
                # Extract and process files
                extracted_files = []
                language_dist = {}
                file_type_dist = {}
                
                for file_path in all_files:
                    try:
                        # Check file size
                        file_size = os.path.getsize(file_path)
                        if file_size < min_file_size or file_size > max_file_size:
                            continue
                        
                        # Read file content
                        content = self._read_file_safely(file_path)
                        if not content:
                            continue
                        
                        # Determine file metadata
                        relative_path = os.path.relpath(file_path, clone_result.local_path)
                        file_type = self._determine_file_type(file_path)
                        file_language = self._determine_file_language(file_path, content)
                        
                        # Create extracted file object
                        extracted_file = ExtractedFile(
                            file_path=file_path,
                            relative_path=relative_path,
                            content=content,
                            file_type=file_type,
                            language=file_language,
                            size_bytes=file_size,
                            is_main_file=self._is_main_file(relative_path),
                            is_config_file=self._is_config_file(relative_path),
                            is_test_file=self._is_test_file(relative_path),
                            dependencies=self._extract_dependencies(content, file_language)
                        )
                        
                        # Score the file quality
                        try:
                            quality_score = await self.file_scorer.score_file(file_path, content)
                            extracted_file.quality_score = quality_score
                        except Exception as e:
                            self.logger.warning(f"Failed to score file {file_path}: {e}")
                        
                        extracted_files.append(extracted_file)
                        
                        # Update distributions
                        language_dist[file_language] = language_dist.get(file_language, 0) + 1
                        file_type_dist[file_type] = file_type_dist.get(file_type, 0) + 1
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to process file {file_path}: {e}")
                        continue
                
                end_time = asyncio.get_event_loop().time()
                extraction_time = end_time - start_time
                
                # Categorize files
                main_files = [f for f in extracted_files if f.is_main_file]
                config_files = [f for f in extracted_files if f.is_config_file]
                test_files = [f for f in extracted_files if f.is_test_file]
                
                # Create extraction result
                extraction_result = ExtractionResult(
                    repository_name=clone_result.repository_name,
                    repository_path=clone_result.local_path,
                    extracted_files=extracted_files,
                    total_files_found=len(all_files),
                    extraction_time_seconds=extraction_time,
                    language_distribution=language_dist,
                    file_type_distribution=file_type_dist,
                    main_files=main_files,
                    config_files=config_files,
                    test_files=test_files
                )
                
                extraction_results.append(extraction_result)
                
                self.logger.info(
                    f"Extracted {len(extracted_files)} files from {clone_result.repository_name} "
                    f"in {extraction_time:.2f}s"
                )
                
            except Exception as e:
                self.logger.error(f"Failed to extract from {clone_result.repository_name}: {e}")
                continue
        
        return extraction_results
    
    def _get_include_patterns(self, language: str) -> List[str]:
        """Get file patterns to include based on language."""
        
        patterns = []
        
        # Add language-specific patterns
        if language.lower() in self.include_patterns:
            patterns.extend(self.include_patterns[language.lower()])
        
        # Always include config, docs, and build files
        patterns.extend(self.include_patterns['config'])
        patterns.extend(self.include_patterns['docs'])
        patterns.extend(self.include_patterns['build'])
        
        return patterns
    
    def _find_files(
        self,
        root_path: str,
        include_patterns: List[str],
        max_files: int
    ) -> List[str]:
        """Find files matching the include patterns."""
        
        found_files = []
        
        for root, dirs, files in os.walk(root_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not self._is_excluded_path(os.path.join(root, d))]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # Check if file is excluded
                if self._is_excluded_path(file_path):
                    continue
                
                # Check if file matches include patterns
                if self._matches_patterns(file, include_patterns):
                    found_files.append(file_path)
                    
                    if len(found_files) >= max_files:
                        return found_files
        
        return found_files
    
    def _is_excluded_path(self, path: str) -> bool:
        """Check if a path should be excluded."""
        
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(path, pattern):
                return True
        
        return False
    
    def _matches_patterns(self, filename: str, patterns: List[str]) -> bool:
        """Check if filename matches any of the patterns."""
        
        for pattern in patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True
        
        return False
    
    def _read_file_safely(self, file_path: str) -> Optional[str]:
        """Safely read file content."""
        
        try:
            # Try UTF-8 first
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                # Try with latin-1 as fallback
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception:
                return None
        except Exception as e:
            self.logger.warning(f"Failed to read {file_path}: {e}")
            return None
    
    def _determine_file_type(self, file_path: str) -> str:
        """Determine the type of file."""
        
        filename = os.path.basename(file_path).lower()
        
        if filename in ['readme.md', 'readme.txt', 'readme.rst', 'readme']:
            return 'readme'
        elif filename in ['license', 'license.txt', 'license.md']:
            return 'license'
        elif filename in ['requirements.txt', 'package.json', 'pom.xml', 'build.gradle']:
            return 'dependencies'
        elif filename in ['dockerfile', 'docker-compose.yml']:
            return 'docker'
        elif any(filename.endswith(ext) for ext in ['.py', '.js', '.java', '.kt']):
            return 'source'
        elif any(filename.endswith(ext) for ext in ['.json', '.yaml', '.yml', '.toml']):
            return 'config'
        elif any(filename.endswith(ext) for ext in ['.md', '.rst', '.txt']):
            return 'documentation'
        else:
            return 'other'
    
    def _determine_file_language(self, file_path: str, content: str) -> str:
        """Determine the programming language of a file."""
        
        extension = os.path.splitext(file_path)[1].lower()
        
        language_map = {
            '.py': 'python',
            '.pyx': 'python',
            '.pyi': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.mjs': 'javascript',
            '.java': 'java',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.md': 'markdown',
            '.rst': 'restructuredtext',
            '.txt': 'text'
        }
        
        return language_map.get(extension, 'unknown')
    
    def _is_main_file(self, relative_path: str) -> bool:
        """Check if file is likely a main entry point."""
        
        filename = os.path.basename(relative_path).lower()
        
        for pattern in self.main_file_patterns:
            if fnmatch.fnmatch(filename, pattern.lower()):
                return True
        
        return False
    
    def _is_config_file(self, relative_path: str) -> bool:
        """Check if file is a configuration file."""
        
        filename = os.path.basename(relative_path).lower()
        
        for pattern in self.config_file_patterns:
            if fnmatch.fnmatch(filename, pattern.lower()):
                return True
        
        return False
    
    def _is_test_file(self, relative_path: str) -> bool:
        """Check if file is a test file."""
        
        filename = os.path.basename(relative_path).lower()
        
        for pattern in self.test_file_patterns:
            if fnmatch.fnmatch(filename, pattern.lower()):
                return True
        
        # Also check if it's in a test directory
        path_parts = relative_path.lower().split(os.sep)
        test_dirs = ['test', 'tests', 'testing', '__tests__', 'spec', 'specs']
        
        return any(part in test_dirs for part in path_parts)
    
    def _extract_dependencies(self, content: str, language: str) -> List[str]:
        """Extract dependencies from file content."""
        
        dependencies = []
        
        try:
            if language == 'python':
                # Extract import statements
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('import ') or line.startswith('from '):
                        # Simple extraction - could be more sophisticated
                        if 'import ' in line:
                            parts = line.split('import ')
                            if len(parts) > 1:
                                dep = parts[1].split()[0].split('.')[0]
                                if dep and not dep.startswith('.'):
                                    dependencies.append(dep)
            
            elif language == 'javascript':
                # Extract require/import statements
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if 'require(' in line or 'import ' in line:
                        # Simple extraction
                        if 'require(' in line:
                            start = line.find("require('") + 9
                            if start > 8:
                                end = line.find("'", start)
                                if end > start:
                                    dep = line[start:end]
                                    if not dep.startswith('.'):
                                        dependencies.append(dep)
        
        except Exception as e:
            self.logger.warning(f"Failed to extract dependencies: {e}")
        
        return list(set(dependencies))  # Remove duplicates


# Example usage
async def main():
    """Example usage of the file extractor."""
    
    # Mock clone result for testing
    @dataclass
    class MockCloneResult:
        repository_name: str
        local_path: str
    
    extractor = FileExtractor()
    
    # This would normally come from the repository cloner
    clone_results = [
        MockCloneResult(
            repository_name="test-repo",
            local_path="/tmp/test-repo"
        )
    ]
    
    extraction_results = await extractor.extract_files(
        clone_results=clone_results,
        language="python",
        extraction_criteria={'max_files_per_repo': 20}
    )
    
    for result in extraction_results:
        print(f"Extraction Results for {result.repository_name}:")
        print(f"  Total files found: {result.total_files_found}")
        print(f"  Files extracted: {len(result.extracted_files)}")
        print(f"  Extraction time: {result.extraction_time_seconds:.2f}s")
        print(f"  Language distribution: {result.language_distribution}")
        print(f"  Main files: {len(result.main_files)}")
        print(f"  Config files: {len(result.config_files)}")
        print(f"  Test files: {len(result.test_files)}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())