"""
File Extractor

Selective file extraction based on analysis results and integration requirements.
"""

import asyncio
import logging
import shutil
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import fnmatch
import json

from .repository_cloner import CloneResult
from ..analysis.unified_scorer import CompositeFileScore


class ExtractionStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    FILTERED = "filtered"


@dataclass
class ExtractedFile:
    original_path: str
    extracted_path: str
    file_type: str
    size_bytes: int
    quality_score: Optional[float]
    extraction_reason: str


@dataclass
class ExtractionResult:
    repository_name: str
    total_files_found: int
    files_extracted: int
    files_skipped: int
    extracted_files: List[ExtractedFile]
    extraction_path: str
    status: ExtractionStatus
    error_message: Optional[str] = None


class FileExtractor:
    """Selective file extraction based on analysis and requirements."""
    
    def __init__(self, extraction_base_dir: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # Set up extraction directory
        if extraction_base_dir:
            self.extraction_base_dir = Path(extraction_base_dir)
        else:
            self.extraction_base_dir = Path("extracted_components")
        
        self.extraction_base_dir.mkdir(parents=True, exist_ok=True)
        
        # File type patterns
        self.code_file_patterns = {
            'python': ['*.py', '*.pyx', '*.pyi'],
            'javascript': ['*.js', '*.jsx', '*.ts', '*.tsx', '*.mjs'],
            'java': ['*.java'],
            'go': ['*.go'],
            'rust': ['*.rs'],
            'c': ['*.c', '*.h'],
            'cpp': ['*.cpp', '*.cxx', '*.cc', '*.hpp', '*.hxx'],
            'php': ['*.php'],
            'ruby': ['*.rb'],
            'csharp': ['*.cs']
        }
        
        # Configuration file patterns
        self.config_file_patterns = [
            'requirements.txt', 'setup.py', 'setup.cfg', 'pyproject.toml',
            'package.json', 'package-lock.json', 'yarn.lock',
            'pom.xml', 'build.gradle', 'gradle.properties',
            'Cargo.toml', 'Cargo.lock',
            'Gemfile', 'Gemfile.lock',
            'composer.json', 'composer.lock',
            '*.csproj', '*.sln',
            'Makefile', 'CMakeLists.txt',
            'Dockerfile', 'docker-compose.yml',
            '.env', '.env.example', 'config.json', 'config.yaml'
        ]
        
        # Documentation patterns
        self.doc_file_patterns = [
            'README*', 'CHANGELOG*', 'LICENSE*', 'CONTRIBUTING*',
            '*.md', '*.rst', '*.txt'
        ]
        
        # Files/directories to always exclude
        self.exclude_patterns = [
            '.git', '.svn', '.hg',
            '__pycache__', '*.pyc', '*.pyo',
            'node_modules', '.npm',
            'target', 'build', 'dist',
            '.idea', '.vscode',
            '*.log', '*.tmp', '*.cache',
            '.pytest_cache', '.coverage',
            'venv', 'env', '.env'
        ]
        
        # Quality score thresholds
        self.min_quality_score = 0.4
        self.preferred_quality_score = 0.7
    
    async def extract_files(self, 
                          clone_results: Dict[str, CloneResult],
                          file_scores: Optional[Dict[str, Dict[str, CompositeFileScore]]] = None,
                          language: str = "python",
                          extraction_criteria: Optional[Dict[str, Any]] = None) -> Dict[str, ExtractionResult]:
        """
        Extract files from cloned repositories based on analysis and criteria.
        
        Args:
            clone_results: Results from repository cloning
            file_scores: File quality scores from analysis
            language: Target programming language
            extraction_criteria: Custom extraction criteria
            
        Returns:
            Dict mapping repository names to extraction results
        """
        
        self.logger.info(f"Extracting files from {len(clone_results)} repositories...")
        
        # Set default extraction criteria
        if extraction_criteria is None:
            extraction_criteria = {
                'include_code': True,
                'include_config': True,
                'include_docs': True,
                'min_quality_score': self.min_quality_score,
                'max_files_per_repo': 100
            }
        
        extraction_results = {}
        
        for repo_name, clone_result in clone_results.items():
            if clone_result.status.value != 'success':
                extraction_results[repo_name] = ExtractionResult(
                    repository_name=repo_name,
                    total_files_found=0,
                    files_extracted=0,
                    files_skipped=0,
                    extracted_files=[],
                    extraction_path="",
                    status=ExtractionStatus.SKIPPED,
                    error_message="Repository clone failed"
                )
                continue
            
            try:
                result = await self._extract_repository_files(
                    repo_name, clone_result, file_scores, language, extraction_criteria
                )
                extraction_results[repo_name] = result
                
            except Exception as e:
                self.logger.error(f"File extraction failed for {repo_name}: {e}")
                extraction_results[repo_name] = ExtractionResult(
                    repository_name=repo_name,
                    total_files_found=0,
                    files_extracted=0,
                    files_skipped=0,
                    extracted_files=[],
                    extraction_path="",
                    status=ExtractionStatus.FAILED,
                    error_message=str(e)
                )
        
        return extraction_results
    
    async def _extract_repository_files(self, 
                                      repo_name: str,
                                      clone_result: CloneResult,
                                      file_scores: Optional[Dict[str, Dict[str, CompositeFileScore]]],
                                      language: str,
                                      extraction_criteria: Dict[str, Any]) -> ExtractionResult:
        """Extract files from a single repository."""
        
        repo_path = Path(clone_result.local_path)
        extraction_path = self.extraction_base_dir / repo_name
        
        # Create extraction directory
        if extraction_path.exists():
            shutil.rmtree(extraction_path)
        extraction_path.mkdir(parents=True)
        
        # Find all relevant files
        candidate_files = self._find_candidate_files(repo_path, language)
        
        # Get file scores for this repository
        repo_file_scores = file_scores.get(repo_name, {}) if file_scores else {}
        
        # Filter and prioritize files
        selected_files = self._select_files_for_extraction(
            candidate_files, repo_file_scores, extraction_criteria
        )
        
        # Extract selected files
        extracted_files = []
        files_skipped = 0
        
        for file_info in selected_files:
            try:
                extracted_file = await self._extract_single_file(
                    file_info, repo_path, extraction_path
                )
                if extracted_file:
                    extracted_files.append(extracted_file)
                else:
                    files_skipped += 1
            except Exception as e:
                self.logger.warning(f"Failed to extract {file_info['path']}: {e}")
                files_skipped += 1
        
        return ExtractionResult(
            repository_name=repo_name,
            total_files_found=len(candidate_files),
            files_extracted=len(extracted_files),
            files_skipped=files_skipped,
            extracted_files=extracted_files,
            extraction_path=str(extraction_path),
            status=ExtractionStatus.SUCCESS if extracted_files else ExtractionStatus.FILTERED
        )
    
    def _find_candidate_files(self, repo_path: Path, language: str) -> List[Dict[str, Any]]:
        """Find all candidate files for extraction."""
        
        candidate_files = []
        
        # Get file patterns for the language
        code_patterns = self.code_file_patterns.get(language.lower(), ['*'])
        all_patterns = code_patterns + self.config_file_patterns + self.doc_file_patterns
        
        for file_path in repo_path.rglob('*'):
            if not file_path.is_file():
                continue
            
            # Skip excluded files/directories
            if self._should_exclude_file(file_path, repo_path):
                continue
            
            # Check if file matches any pattern
            file_type = self._classify_file(file_path, code_patterns)
            if file_type == 'unknown':
                continue
            
            relative_path = file_path.relative_to(repo_path)
            
            candidate_files.append({
                'path': file_path,
                'relative_path': str(relative_path),
                'file_type': file_type,
                'size_bytes': file_path.stat().st_size
            })
        
        return candidate_files
    
    def _should_exclude_file(self, file_path: Path, repo_path: Path) -> bool:
        """Check if file should be excluded."""
        
        relative_path = file_path.relative_to(repo_path)
        path_str = str(relative_path)
        
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(file_path.name, pattern):
                return True
            
            # Check if any parent directory matches exclude pattern
            for parent in relative_path.parents:
                if fnmatch.fnmatch(str(parent), pattern):
                    return True
        
        return False
    
    def _classify_file(self, file_path: Path, code_patterns: List[str]) -> str:
        """Classify file type."""
        
        file_name = file_path.name
        
        # Check code files
        for pattern in code_patterns:
            if fnmatch.fnmatch(file_name, pattern):
                return 'code'
        
        # Check config files
        for pattern in self.config_file_patterns:
            if fnmatch.fnmatch(file_name, pattern):
                return 'config'
        
        # Check documentation files
        for pattern in self.doc_file_patterns:
            if fnmatch.fnmatch(file_name, pattern):
                return 'documentation'
        
        return 'unknown'
    
    def _select_files_for_extraction(self, 
                                   candidate_files: List[Dict[str, Any]],
                                   file_scores: Dict[str, CompositeFileScore],
                                   extraction_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Select files for extraction based on criteria and scores."""
        
        selected_files = []
        
        # Filter by file type criteria
        for file_info in candidate_files:
            file_type = file_info['file_type']
            
            if file_type == 'code' and not extraction_criteria.get('include_code', True):
                continue
            if file_type == 'config' and not extraction_criteria.get('include_config', True):
                continue
            if file_type == 'documentation' and not extraction_criteria.get('include_docs', True):
                continue
            
            # Check quality score if available
            relative_path = file_info['relative_path']
            file_score = file_scores.get(relative_path)
            
            if file_score:
                quality_score = file_score.overall_score
                min_score = extraction_criteria.get('min_quality_score', self.min_quality_score)
                
                if quality_score < min_score:
                    continue
                
                file_info['quality_score'] = quality_score
                file_info['extraction_reason'] = f"Quality score: {quality_score:.2f}"
            else:
                file_info['quality_score'] = None
                file_info['extraction_reason'] = f"File type: {file_type}"
            
            selected_files.append(file_info)
        
        # Sort by priority (quality score, then file type importance)
        def file_priority(file_info):
            quality_score = file_info.get('quality_score', 0.5)
            file_type = file_info['file_type']
            
            # Type priority: code > config > documentation
            type_priority = {'code': 3, 'config': 2, 'documentation': 1}.get(file_type, 0)
            
            return (quality_score, type_priority)
        
        selected_files.sort(key=file_priority, reverse=True)
        
        # Limit number of files if specified
        max_files = extraction_criteria.get('max_files_per_repo', len(selected_files))
        selected_files = selected_files[:max_files]
        
        return selected_files
    
    async def _extract_single_file(self, 
                                 file_info: Dict[str, Any],
                                 repo_path: Path,
                                 extraction_path: Path) -> Optional[ExtractedFile]:
        """Extract a single file to the extraction directory."""
        
        source_path = file_info['path']
        relative_path = file_info['relative_path']
        
        # Create destination path (preserve directory structure)
        dest_path = extraction_path / relative_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Copy file
            shutil.copy2(source_path, dest_path)
            
            return ExtractedFile(
                original_path=str(source_path.relative_to(repo_path)),
                extracted_path=str(dest_path.relative_to(self.extraction_base_dir)),
                file_type=file_info['file_type'],
                size_bytes=file_info['size_bytes'],
                quality_score=file_info.get('quality_score'),
                extraction_reason=file_info['extraction_reason']
            )
            
        except Exception as e:
            self.logger.error(f"Failed to copy {source_path} to {dest_path}: {e}")
            return None
    
    def get_extraction_summary(self, extraction_results: Dict[str, ExtractionResult]) -> Dict[str, Any]:
        """Generate summary of extraction operations."""
        
        successful = [r for r in extraction_results.values() if r.status == ExtractionStatus.SUCCESS]
        failed = [r for r in extraction_results.values() if r.status == ExtractionStatus.FAILED]
        filtered = [r for r in extraction_results.values() if r.status == ExtractionStatus.FILTERED]
        
        total_files_extracted = sum(r.files_extracted for r in successful)
        total_files_found = sum(r.total_files_found for r in extraction_results.values())
        
        # File type distribution
        file_type_counts = {'code': 0, 'config': 0, 'documentation': 0}
        for result in successful:
            for extracted_file in result.extracted_files:
                file_type_counts[extracted_file.file_type] = file_type_counts.get(extracted_file.file_type, 0) + 1
        
        return {
            'total_repositories': len(extraction_results),
            'successful_extractions': len(successful),
            'failed_extractions': len(failed),
            'filtered_extractions': len(filtered),
            'total_files_found': total_files_found,
            'total_files_extracted': total_files_extracted,
            'extraction_rate': total_files_extracted / max(1, total_files_found),
            'file_type_distribution': file_type_counts,
            'average_files_per_repo': total_files_extracted / max(1, len(successful))
        }


# Example usage
async def main():
    from .repository_cloner import RepositoryCloner
    from ..search.tier1_packages import PackageResult
    from datetime import datetime
    
    # Test with cloned repositories
    cloner = RepositoryCloner()
    extractor = FileExtractor()
    
    # Create test repositories
    test_repos = [
        PackageResult(
            name="requests",
            repository_url="https://github.com/psf/requests",
            description="HTTP library for Python",
            downloads=1000000,
            stars=50000,
            last_updated=datetime.now(),
            license="Apache-2.0",
            quality_score=0.9,
            language="python",
            package_manager="pypi",
            version="2.31.0",
            dependencies_count=5
        )
    ]
    
    print("Testing file extraction...")
    
    # Clone repositories
    clone_results = await cloner.clone_repositories(test_repos)
    
    # Extract files
    extraction_results = await extractor.extract_files(
        clone_results, 
        language="python",
        extraction_criteria={
            'include_code': True,
            'include_config': True,
            'include_docs': True,
            'max_files_per_repo': 20
        }
    )
    
    # Print results
    print(f"\nExtraction Results:")
    for repo_name, result in extraction_results.items():
        print(f"  {repo_name}: {result.status.value}")
        print(f"    Files found: {result.total_files_found}")
        print(f"    Files extracted: {result.files_extracted}")
        print(f"    Extraction path: {result.extraction_path}")
        
        if result.extracted_files:
            print(f"    Top extracted files:")
            for extracted_file in result.extracted_files[:5]:
                print(f"      • {extracted_file.original_path} ({extracted_file.file_type})")
                if extracted_file.quality_score:
                    print(f"        Quality: {extracted_file.quality_score:.2f}")
    
    # Print summary
    summary = extractor.get_extraction_summary(extraction_results)
    print(f"\nSummary:")
    print(f"  Extraction rate: {summary['extraction_rate']:.1%}")
    print(f"  File types: {summary['file_type_distribution']}")
    print(f"  Average files per repo: {summary['average_files_per_repo']:.1f}")
    
    # Cleanup
    await cloner.cleanup_clones(clone_results)
    print("Cleanup completed")


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())