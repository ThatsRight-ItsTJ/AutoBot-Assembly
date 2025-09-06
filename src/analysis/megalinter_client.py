"""
MegaLinter Integration

Comprehensive multi-language analysis using MegaLinter Docker container.
"""

import asyncio
import json
import logging
import tempfile
import shutil
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

import docker
import aiofiles


@dataclass
class FileQualityScore:
    complexity: float
    maintainability: float
    style_compliance: float
    documentation: float
    overall_score: float


@dataclass
class MegaLinterResults:
    total_files: int
    analyzed_files: int
    errors: int
    warnings: int
    fixed_issues: int
    file_scores: Dict[str, FileQualityScore]
    summary: Dict[str, Any]
    execution_time: float


class MegaLinterAnalyzer:
    """Comprehensive multi-language analysis using MegaLinter."""
    
    def __init__(self, docker_image: str = "oxsecurity/megalinter:v7"):
        self.docker_image = docker_image
        self.docker_client = docker.from_env()
        self.logger = logging.getLogger(__name__)
        
        # MegaLinter configuration
        self.megalinter_config = {
            "APPLY_FIXES": "none",  # Don't modify files, just analyze
            "DEFAULT_BRANCH": "main",
            "DISABLE_ERRORS": "true",  # Don't fail on errors, just report
            "FILEIO_REPORTER": "true",
            "JSON_REPORTER": "true",
            "LOG_LEVEL": "WARNING",
            "PARALLEL": "true",
            "SHOW_ELAPSED_TIME": "true",
            "VALIDATE_ALL_CODEBASE": "true"
        }
    
    async def analyze_repository(self, repo_path: str, language_hint: Optional[str] = None) -> MegaLinterResults:
        """
        Run MegaLinter analysis on repository.
        
        Args:
            repo_path: Path to repository to analyze
            language_hint: Optional language hint for optimization
            
        Returns:
            MegaLinterResults with comprehensive analysis
        """
        start_time = asyncio.get_event_loop().time()
        
        # Prepare temporary directory for analysis
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            analysis_path = temp_path / "analysis"
            reports_path = temp_path / "reports"
            
            # Copy repository to temporary location
            shutil.copytree(repo_path, analysis_path)
            reports_path.mkdir()
            
            try:
                # Run MegaLinter container
                container_result = await self._run_megalinter_container(
                    analysis_path, reports_path, language_hint
                )
                
                # Parse results
                results = await self._parse_megalinter_results(reports_path, container_result)
                
                execution_time = asyncio.get_event_loop().time() - start_time
                results.execution_time = execution_time
                
                return results
                
            except Exception as e:
                self.logger.error(f"MegaLinter analysis failed: {e}")
                return self._create_empty_results()
    
    async def analyze_files(self, file_paths: List[str], base_path: str) -> Dict[str, FileQualityScore]:
        """
        Analyze specific files within a repository.
        
        Args:
            file_paths: List of file paths to analyze
            base_path: Base repository path
            
        Returns:
            Dict mapping file paths to quality scores
        """
        # Create temporary directory with only specified files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            analysis_path = temp_path / "analysis"
            analysis_path.mkdir()
            
            # Copy only specified files
            for file_path in file_paths:
                src_file = Path(base_path) / file_path
                if src_file.exists():
                    dest_file = analysis_path / file_path
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dest_file)
            
            # Run analysis
            results = await self.analyze_repository(str(analysis_path))
            return results.file_scores
    
    async def _run_megalinter_container(self, analysis_path: Path, reports_path: Path, 
                                      language_hint: Optional[str] = None) -> dict:
        """Run MegaLinter Docker container."""
        
        # Prepare environment variables
        env_vars = self.megalinter_config.copy()
        if language_hint:
            env_vars["DEFAULT_WORKSPACE"] = f"/tmp/lint"
            # Add language-specific optimizations
            if language_hint.lower() == 'python':
                env_vars["ENABLE_LINTERS"] = "PYTHON_PYLINT,PYTHON_FLAKE8,PYTHON_BLACK,PYTHON_ISORT"
            elif language_hint.lower() == 'javascript':
                env_vars["ENABLE_LINTERS"] = "JAVASCRIPT_ES,JAVASCRIPT_PRETTIER,TYPESCRIPT_ES"
            elif language_hint.lower() == 'java':
                env_vars["ENABLE_LINTERS"] = "JAVA_CHECKSTYLE,JAVA_PMD"
        
        # Prepare volumes
        volumes = {
            str(analysis_path): {'bind': '/tmp/lint', 'mode': 'ro'},
            str(reports_path): {'bind': '/tmp/lint/megalinter-reports', 'mode': 'rw'}
        }
        
        try:
            # Run container
            container = self.docker_client.containers.run(
                self.docker_image,
                environment=env_vars,
                volumes=volumes,
                working_dir='/tmp/lint',
                detach=True,
                remove=True,
                mem_limit='2g',
                cpu_count=2
            )
            
            # Wait for completion with timeout
            result = container.wait(timeout=300)  # 5 minute timeout
            logs = container.logs().decode('utf-8')
            
            return {
                'exit_code': result['StatusCode'],
                'logs': logs
            }
            
        except docker.errors.ContainerError as e:
            self.logger.error(f"Container error: {e}")
            return {'exit_code': 1, 'logs': str(e)}
        except Exception as e:
            self.logger.error(f"Docker execution error: {e}")
            return {'exit_code': 1, 'logs': str(e)}
    
    async def _parse_megalinter_results(self, reports_path: Path, container_result: dict) -> MegaLinterResults:
        """Parse MegaLinter output files."""
        
        # Look for JSON report
        json_report_path = reports_path / "megalinter-report.json"
        if not json_report_path.exists():
            # Try alternative locations
            for alt_path in reports_path.glob("**/megalinter-report.json"):
                json_report_path = alt_path
                break
        
        if json_report_path.exists():
            try:
                async with aiofiles.open(json_report_path, 'r') as f:
                    content = await f.read()
                    report_data = json.loads(content)
                    return self._process_json_report(report_data)
            except Exception as e:
                self.logger.error(f"Error parsing JSON report: {e}")
        
        # Fallback to log parsing
        return self._parse_logs_fallback(container_result.get('logs', ''))
    
    def _process_json_report(self, report_data: dict) -> MegaLinterResults:
        """Process MegaLinter JSON report."""
        
        file_scores = {}
        
        # Extract file-level results
        linters = report_data.get('linters', [])
        for linter in linters:
            files = linter.get('files', [])
            for file_info in files:
                file_path = file_info.get('file', '')
                if file_path:
                    score = self._calculate_file_score_from_linter(file_info, linter)
                    if file_path in file_scores:
                        # Average scores from multiple linters
                        existing_score = file_scores[file_path]
                        file_scores[file_path] = FileQualityScore(
                            complexity=(existing_score.complexity + score.complexity) / 2,
                            maintainability=(existing_score.maintainability + score.maintainability) / 2,
                            style_compliance=(existing_score.style_compliance + score.style_compliance) / 2,
                            documentation=(existing_score.documentation + score.documentation) / 2,
                            overall_score=(existing_score.overall_score + score.overall_score) / 2
                        )
                    else:
                        file_scores[file_path] = score
        
        # Extract summary statistics
        summary = {
            'total_linters': len(linters),
            'active_linters': len([l for l in linters if l.get('status') == 'success']),
            'total_errors': sum(l.get('total_number_errors', 0) for l in linters),
            'total_warnings': sum(l.get('total_number_warnings', 0) for l in linters),
            'elapsed_time': report_data.get('elapsed_time', 0)
        }
        
        return MegaLinterResults(
            total_files=len(file_scores),
            analyzed_files=len(file_scores),
            errors=summary['total_errors'],
            warnings=summary['total_warnings'],
            fixed_issues=0,
            file_scores=file_scores,
            summary=summary,
            execution_time=0  # Will be set by caller
        )
    
    def _calculate_file_score_from_linter(self, file_info: dict, linter: dict) -> FileQualityScore:
        """Calculate file quality score from linter results."""
        
        errors = file_info.get('errors_number', 0)
        warnings = file_info.get('warnings_number', 0)
        fixed = file_info.get('fixed_number', 0)
        
        # Base score starts high and decreases with issues
        base_score = 1.0
        
        # Penalty for errors (more severe)
        error_penalty = min(0.5, errors * 0.1)
        
        # Penalty for warnings (less severe)
        warning_penalty = min(0.3, warnings * 0.05)
        
        # Bonus for having fixable issues (shows tool engagement)
        fix_bonus = min(0.1, fixed * 0.02)
        
        overall_score = max(0.0, base_score - error_penalty - warning_penalty + fix_bonus)
        
        # Calculate component scores based on linter type
        linter_name = linter.get('linter_name', '').lower()
        
        if 'complexity' in linter_name or 'cyclomatic' in linter_name:
            complexity = max(0.0, 1.0 - (errors + warnings) * 0.1)
        else:
            complexity = overall_score
        
        if 'maintainability' in linter_name or 'quality' in linter_name:
            maintainability = max(0.0, 1.0 - (errors + warnings) * 0.08)
        else:
            maintainability = overall_score
        
        if 'style' in linter_name or 'format' in linter_name or 'lint' in linter_name:
            style_compliance = max(0.0, 1.0 - warnings * 0.05)
        else:
            style_compliance = overall_score
        
        if 'doc' in linter_name or 'comment' in linter_name:
            documentation = max(0.0, 1.0 - (errors + warnings) * 0.1)
        else:
            documentation = 0.7  # Default documentation score
        
        return FileQualityScore(
            complexity=complexity,
            maintainability=maintainability,
            style_compliance=style_compliance,
            documentation=documentation,
            overall_score=overall_score
        )
    
    def _parse_logs_fallback(self, logs: str) -> MegaLinterResults:
        """Fallback parsing from container logs."""
        
        # Simple log parsing for basic metrics
        lines = logs.split('\n')
        
        errors = 0
        warnings = 0
        analyzed_files = 0
        
        for line in lines:
            if 'error' in line.lower():
                errors += 1
            elif 'warning' in line.lower():
                warnings += 1
            elif 'analyzed' in line.lower() or 'processed' in line.lower():
                try:
                    # Try to extract file count from log line
                    words = line.split()
                    for word in words:
                        if word.isdigit():
                            analyzed_files = max(analyzed_files, int(word))
                            break
                except:
                    pass
        
        # Create basic file scores (fallback)
        file_scores = {}
        if analyzed_files > 0:
            # Create generic scores for estimated files
            base_score = max(0.5, 1.0 - (errors + warnings) * 0.1 / max(1, analyzed_files))
            for i in range(min(analyzed_files, 10)):  # Limit to 10 generic entries
                file_scores[f"file_{i}"] = FileQualityScore(
                    complexity=base_score,
                    maintainability=base_score,
                    style_compliance=base_score,
                    documentation=0.6,
                    overall_score=base_score
                )
        
        return MegaLinterResults(
            total_files=analyzed_files,
            analyzed_files=analyzed_files,
            errors=errors,
            warnings=warnings,
            fixed_issues=0,
            file_scores=file_scores,
            summary={'log_parsing': True, 'errors': errors, 'warnings': warnings},
            execution_time=0
        )
    
    def _create_empty_results(self) -> MegaLinterResults:
        """Create empty results for failed analysis."""
        return MegaLinterResults(
            total_files=0,
            analyzed_files=0,
            errors=0,
            warnings=0,
            fixed_issues=0,
            file_scores={},
            summary={'status': 'failed'},
            execution_time=0
        )


# Example usage
async def main():
    analyzer = MegaLinterAnalyzer()
    
    # Test with current repository
    repo_path = "."
    print("Running MegaLinter analysis...")
    
    results = await analyzer.analyze_repository(repo_path, language_hint="python")
    
    print(f"\nMegaLinter Results:")
    print(f"  Files analyzed: {results.analyzed_files}")
    print(f"  Errors: {results.errors}")
    print(f"  Warnings: {results.warnings}")
    print(f"  Execution time: {results.execution_time:.2f}s")
    
    print(f"\nTop file scores:")
    sorted_files = sorted(results.file_scores.items(), 
                         key=lambda x: x[1].overall_score, reverse=True)
    
    for file_path, score in sorted_files[:5]:
        print(f"  {file_path}: {score.overall_score:.2f}")
        print(f"    Complexity: {score.complexity:.2f}, Maintainability: {score.maintainability:.2f}")
        print(f"    Style: {score.style_compliance:.2f}, Documentation: {score.documentation:.2f}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())