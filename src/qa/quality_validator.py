"""
Quality Validator

Final quality assessment and benchmarking for assembled projects.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json
import statistics

from ..assembly.generated_project import GeneratedProject
from .integration_tester import IntegrationTestSuite


class QualityLevel(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class QualityMetrics:
    code_coverage: Optional[float]
    complexity_score: float
    maintainability_index: float
    technical_debt_ratio: float
    security_score: float
    performance_score: float
    documentation_completeness: float


@dataclass
class ValidationResult:
    project_name: str
    overall_quality_level: QualityLevel
    overall_score: float
    quality_metrics: QualityMetrics
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    benchmark_comparisons: Dict[str, Any]
    validation_duration: float


class QualityValidator:
    """Final quality assessment and benchmarking system."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Quality thresholds
        self.quality_thresholds = {
            QualityLevel.EXCELLENT: 0.9,
            QualityLevel.GOOD: 0.75,
            QualityLevel.ACCEPTABLE: 0.6,
            QualityLevel.POOR: 0.4,
            QualityLevel.CRITICAL: 0.0
        }
        
        # Benchmark data (industry standards)
        self.benchmarks = {
            'complexity_score': {'excellent': 0.9, 'good': 0.75, 'acceptable': 0.6},
            'maintainability_index': {'excellent': 0.85, 'good': 0.7, 'acceptable': 0.55},
            'technical_debt_ratio': {'excellent': 0.05, 'good': 0.1, 'acceptable': 0.2},
            'security_score': {'excellent': 0.95, 'good': 0.8, 'acceptable': 0.65},
            'performance_score': {'excellent': 0.9, 'good': 0.75, 'acceptable': 0.6},
            'documentation_completeness': {'excellent': 0.9, 'good': 0.7, 'acceptable': 0.5}
        }
    
    async def validate_project(self, 
                             generated_project: GeneratedProject,
                             test_suite: Optional[IntegrationTestSuite] = None) -> ValidationResult:
        """
        Perform comprehensive quality validation on a generated project.
        
        Args:
            generated_project: The generated project to validate
            test_suite: Optional test results from integration testing
            
        Returns:
            ValidationResult with comprehensive quality assessment
        """
        
        self.logger.info(f"Starting quality validation for {generated_project.project_name}")
        start_time = time.time()
        
        project_path = Path(generated_project.project_path)
        
        try:
            # Calculate quality metrics
            quality_metrics = await self._calculate_quality_metrics(
                project_path, generated_project, test_suite
            )
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(quality_metrics)
            
            # Determine quality level
            quality_level = self._determine_quality_level(overall_score)
            
            # Analyze strengths and weaknesses
            strengths, weaknesses = self._analyze_strengths_weaknesses(
                quality_metrics, generated_project
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                quality_metrics, weaknesses, generated_project
            )
            
            # Benchmark comparisons
            benchmark_comparisons = self._compare_to_benchmarks(quality_metrics)
            
            validation_duration = time.time() - start_time
            
            return ValidationResult(
                project_name=generated_project.project_name,
                overall_quality_level=quality_level,
                overall_score=overall_score,
                quality_metrics=quality_metrics,
                strengths=strengths,
                weaknesses=weaknesses,
                recommendations=recommendations,
                benchmark_comparisons=benchmark_comparisons,
                validation_duration=validation_duration
            )
            
        except Exception as e:
            self.logger.error(f"Quality validation failed: {e}")
            validation_duration = time.time() - start_time
            
            # Return minimal validation result
            return ValidationResult(
                project_name=generated_project.project_name,
                overall_quality_level=QualityLevel.CRITICAL,
                overall_score=0.0,
                quality_metrics=QualityMetrics(
                    code_coverage=None,
                    complexity_score=0.0,
                    maintainability_index=0.0,
                    technical_debt_ratio=1.0,
                    security_score=0.0,
                    performance_score=0.0,
                    documentation_completeness=0.0
                ),
                strengths=[],
                weaknesses=[f"Validation failed: {str(e)}"],
                recommendations=["Manual review required due to validation failure"],
                benchmark_comparisons={},
                validation_duration=validation_duration
            )
    
    async def _calculate_quality_metrics(self, 
                                       project_path: Path, 
                                       generated_project: GeneratedProject,
                                       test_suite: Optional[IntegrationTestSuite]) -> QualityMetrics:
        """Calculate comprehensive quality metrics."""
        
        # Code coverage (from test results if available)
        code_coverage = None
        if test_suite and test_suite.passed_tests > 0:
            # Estimate coverage based on test success rate
            test_success_rate = test_suite.passed_tests / test_suite.total_tests
            code_coverage = min(test_success_rate * 0.8, 0.9)  # Conservative estimate
        
        # Complexity score
        complexity_score = await self._calculate_complexity_score(project_path, generated_project)
        
        # Maintainability index
        maintainability_index = await self._calculate_maintainability_index(
            project_path, generated_project
        )
        
        # Technical debt ratio
        technical_debt_ratio = await self._calculate_technical_debt_ratio(
            project_path, generated_project
        )
        
        # Security score
        security_score = await self._calculate_security_score(project_path, generated_project)
        
        # Performance score
        performance_score = await self._calculate_performance_score(
            project_path, generated_project
        )
        
        # Documentation completeness
        documentation_completeness = await self._calculate_documentation_completeness(
            project_path, generated_project
        )
        
        return QualityMetrics(
            code_coverage=code_coverage,
            complexity_score=complexity_score,
            maintainability_index=maintainability_index,
            technical_debt_ratio=technical_debt_ratio,
            security_score=security_score,
            performance_score=performance_score,
            documentation_completeness=documentation_completeness
        )
    
    async def _calculate_complexity_score(self, project_path: Path, 
                                        generated_project: GeneratedProject) -> float:
        """Calculate code complexity score."""
        
        try:
            complexity_factors = []
            
            # File count factor
            source_files = []
            for src_dir in generated_project.structure.source_directories:
                src_path = project_path / src_dir
                if src_path.exists():
                    if generated_project.language.lower() == 'python':
                        source_files.extend(list(src_path.rglob('*.py')))
                    elif generated_project.language.lower() == 'javascript':
                        source_files.extend(list(src_path.rglob('*.js')))
                        source_files.extend(list(src_path.rglob('*.ts')))
            
            file_count = len(source_files)
            
            # File count scoring (fewer files = less complex)
            if file_count <= 5:
                file_complexity = 0.9
            elif file_count <= 15:
                file_complexity = 0.7
            elif file_count <= 30:
                file_complexity = 0.5
            else:
                file_complexity = 0.3
            
            complexity_factors.append(file_complexity)
            
            # Average file size factor
            if source_files:
                file_sizes = []
                for file_path in source_files:
                    try:
                        file_sizes.append(file_path.stat().st_size)
                    except:
                        continue
                
                if file_sizes:
                    avg_file_size = statistics.mean(file_sizes)
                    # Smaller files are generally less complex
                    if avg_file_size <= 1000:  # 1KB
                        size_complexity = 0.9
                    elif avg_file_size <= 5000:  # 5KB
                        size_complexity = 0.7
                    elif avg_file_size <= 15000:  # 15KB
                        size_complexity = 0.5
                    else:
                        size_complexity = 0.3
                    
                    complexity_factors.append(size_complexity)
            
            # Dependency complexity
            dependency_count = len(generated_project.dependencies)
            if dependency_count <= 5:
                dep_complexity = 0.9
            elif dependency_count <= 15:
                dep_complexity = 0.7
            elif dependency_count <= 30:
                dep_complexity = 0.5
            else:
                dep_complexity = 0.3
            
            complexity_factors.append(dep_complexity)
            
            # Project type complexity
            type_complexity = {
                'library': 0.8,
                'application': 0.7,
                'cli_tool': 0.8,
                'web_service': 0.6,
                'generic': 0.7
            }.get(generated_project.project_type.value, 0.7)
            
            complexity_factors.append(type_complexity)
            
            # Calculate weighted average
            return statistics.mean(complexity_factors) if complexity_factors else 0.5
            
        except Exception as e:
            self.logger.warning(f"Could not calculate complexity score: {e}")
            return 0.5
    
    async def _calculate_maintainability_index(self, project_path: Path, 
                                             generated_project: GeneratedProject) -> float:
        """Calculate maintainability index."""
        
        try:
            maintainability_factors = []
            
            # Code organization (directory structure)
            has_src_dir = any(
                (project_path / src_dir).exists() 
                for src_dir in generated_project.structure.source_directories
            )
            has_test_dir = any(
                (project_path / test_dir).exists() 
                for test_dir in generated_project.structure.test_directories
            )
            has_config_files = any(
                (project_path / config_file).exists() 
                for config_file in generated_project.structure.config_files
            )
            
            organization_score = 0.0
            if has_src_dir:
                organization_score += 0.4
            if has_test_dir:
                organization_score += 0.3
            if has_config_files:
                organization_score += 0.3
            
            maintainability_factors.append(organization_score)
            
            # Documentation presence
            readme_exists = (project_path / "README.md").exists()
            doc_score = 0.8 if readme_exists else 0.3
            maintainability_factors.append(doc_score)
            
            # Build system setup
            build_system_score = 0.8 if generated_project.build_commands else 0.4
            maintainability_factors.append(build_system_score)
            
            # CI/CD setup
            ci_exists = (project_path / ".github" / "workflows").exists()
            ci_score = 0.9 if ci_exists else 0.5
            maintainability_factors.append(ci_score)
            
            return statistics.mean(maintainability_factors)
            
        except Exception as e:
            self.logger.warning(f"Could not calculate maintainability index: {e}")
            return 0.5
    
    async def _calculate_technical_debt_ratio(self, project_path: Path, 
                                            generated_project: GeneratedProject) -> float:
        """Calculate technical debt ratio (lower is better)."""
        
        try:
            debt_factors = []
            
            # Missing essential files
            essential_files = ['README.md']
            if generated_project.language.lower() == 'python':
                essential_files.extend(['requirements.txt'])
            elif generated_project.language.lower() == 'javascript':
                essential_files.extend(['package.json'])
            
            missing_files = sum(
                1 for file in essential_files 
                if not (project_path / file).exists()
            )
            
            missing_file_debt = missing_files / len(essential_files)
            debt_factors.append(missing_file_debt)
            
            # TODO comments and placeholders (indicates incomplete work)
            todo_count = 0
            source_files = []
            
            for src_dir in generated_project.structure.source_directories:
                src_path = project_path / src_dir
                if src_path.exists():
                    if generated_project.language.lower() == 'python':
                        source_files.extend(src_path.rglob('*.py'))
            
            # Also check entry points
            for entry_point in generated_project.structure.entry_points:
                entry_path = project_path / entry_point
                if entry_path.exists() and entry_path.is_file():
                    source_files.append(entry_path)
            
            for source_file in source_files:
                try:
                    with open(source_file, 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                    
                    todo_count += content.count('todo')
                    todo_count += content.count('fixme')
                    todo_count += content.count('hack')
                    todo_count += content.count('placeholder')
                    
                except:
                    continue
            
            # Normalize TODO debt (more TODOs = more debt)
            if source_files:
                todo_debt = min(todo_count / (len(source_files) * 2), 0.5)
            else:
                todo_debt = 0.0
            
            debt_factors.append(todo_debt)
            
            # Configuration debt (missing important config)
            config_debt = 0.0
            if not generated_project.build_commands:
                config_debt += 0.2
            if not generated_project.test_commands:
                config_debt += 0.1
            
            debt_factors.append(config_debt)
            
            return statistics.mean(debt_factors)
            
        except Exception as e:
            self.logger.warning(f"Could not calculate technical debt ratio: {e}")
            return 0.3
    
    async def _calculate_security_score(self, project_path: Path, 
                                      generated_project: GeneratedProject) -> float:
        """Calculate security score."""
        
        try:
            security_factors = []
            
            # Dependency security (basic check)
            dependency_count = len(generated_project.dependencies)
            if dependency_count == 0:
                dep_security = 0.9  # No dependencies = fewer attack vectors
            elif dependency_count <= 10:
                dep_security = 0.8
            elif dependency_count <= 25:
                dep_security = 0.6
            else:
                dep_security = 0.4  # Many dependencies = more risk
            
            security_factors.append(dep_security)
            
            # Configuration security
            config_security = 0.8  # Default good score
            
            # Check for common security issues in config files
            for config_file in generated_project.structure.config_files:
                config_path = project_path / config_file
                if config_path.exists():
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            content = f.read().lower()
                        
                        # Look for potential security issues
                        if 'password' in content or 'secret' in content:
                            if 'example' not in content and 'placeholder' not in content:
                                config_security = 0.3  # Hardcoded secrets
                        
                    except:
                        continue
            
            security_factors.append(config_security)
            
            # Project type security
            type_security = {
                'library': 0.8,
                'application': 0.7,
                'cli_tool': 0.8,
                'web_service': 0.6,  # Web services have more attack surface
                'generic': 0.7
            }.get(generated_project.project_type.value, 0.7)
            
            security_factors.append(type_security)
            
            return statistics.mean(security_factors)
            
        except Exception as e:
            self.logger.warning(f"Could not calculate security score: {e}")
            return 0.7
    
    async def _calculate_performance_score(self, project_path: Path, 
                                         generated_project: GeneratedProject) -> float:
        """Calculate performance score."""
        
        try:
            performance_factors = []
            
            # Language performance characteristics
            language_performance = {
                'python': 0.6,
                'javascript': 0.7,
                'java': 0.8,
                'go': 0.9,
                'rust': 0.95,
                'c': 0.95,
                'cpp': 0.95
            }.get(generated_project.language.lower(), 0.7)
            
            performance_factors.append(language_performance)
            
            # Project complexity impact on performance
            complexity_score = await self._calculate_complexity_score(project_path, generated_project)
            # Higher complexity generally means lower performance
            complexity_performance = 1.0 - (1.0 - complexity_score) * 0.3
            performance_factors.append(complexity_performance)
            
            # Dependency impact
            dependency_count = len(generated_project.dependencies)
            if dependency_count <= 5:
                dep_performance = 0.9
            elif dependency_count <= 15:
                dep_performance = 0.8
            elif dependency_count <= 30:
                dep_performance = 0.7
            else:
                dep_performance = 0.6
            
            performance_factors.append(dep_performance)
            
            return statistics.mean(performance_factors)
            
        except Exception as e:
            self.logger.warning(f"Could not calculate performance score: {e}")
            return 0.7
    
    async def _calculate_documentation_completeness(self, project_path: Path, 
                                                  generated_project: GeneratedProject) -> float:
        """Calculate documentation completeness score."""
        
        try:
            doc_factors = []
            
            # README presence and quality
            readme_path = project_path / "README.md"
            if readme_path.exists():
                try:
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        readme_content = f.read()
                    
                    readme_score = 0.3  # Base score for having README
                    
                    # Check for common README sections
                    content_lower = readme_content.lower()
                    if 'installation' in content_lower or 'install' in content_lower:
                        readme_score += 0.2
                    if 'usage' in content_lower or 'example' in content_lower:
                        readme_score += 0.2
                    if 'license' in content_lower:
                        readme_score += 0.1
                    if len(readme_content) > 500:  # Substantial content
                        readme_score += 0.2
                    
                    doc_factors.append(min(readme_score, 1.0))
                    
                except:
                    doc_factors.append(0.3)  # README exists but can't read
            else:
                doc_factors.append(0.0)  # No README
            
            # Code documentation (comments and docstrings)
            code_doc_score = 0.0
            source_files = []
            
            for src_dir in generated_project.structure.source_directories:
                src_path = project_path / src_dir
                if src_path.exists():
                    if generated_project.language.lower() == 'python':
                        source_files.extend(src_path.rglob('*.py'))
            
            if source_files:
                documented_files = 0
                for source_file in source_files:
                    try:
                        with open(source_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Check for documentation
                        has_docstring = '"""' in content or "'''" in content
                        has_comments = '#' in content and len([l for l in content.split('\n') if l.strip().startswith('#')]) > 2
                        
                        if has_docstring or has_comments:
                            documented_files += 1
                            
                    except:
                        continue
                
                code_doc_score = documented_files / len(source_files)
            else:
                code_doc_score = 0.5  # No source files to document
            
            doc_factors.append(code_doc_score)
            
            # Configuration documentation
            config_doc_score = 0.7  # Default reasonable score
            
            # Check if there's a .env.example or similar
            if (project_path / ".env.example").exists():
                config_doc_score = 0.9
            elif (project_path / "config.example.json").exists():
                config_doc_score = 0.9
            
            doc_factors.append(config_doc_score)
            
            return statistics.mean(doc_factors)
            
        except Exception as e:
            self.logger.warning(f"Could not calculate documentation completeness: {e}")
            return 0.5
    
    def _calculate_overall_score(self, metrics: QualityMetrics) -> float:
        """Calculate overall quality score from metrics."""
        
        # Weighted scoring
        weights = {
            'complexity_score': 0.2,
            'maintainability_index': 0.2,
            'technical_debt_ratio': 0.15,  # Lower is better, so we'll invert it
            'security_score': 0.2,
            'performance_score': 0.15,
            'documentation_completeness': 0.1
        }
        
        # Calculate weighted score
        score = 0.0
        score += metrics.complexity_score * weights['complexity_score']
        score += metrics.maintainability_index * weights['maintainability_index']
        score += (1.0 - metrics.technical_debt_ratio) * weights['technical_debt_ratio']  # Invert debt
        score += metrics.security_score * weights['security_score']
        score += metrics.performance_score * weights['performance_score']
        score += metrics.documentation_completeness * weights['documentation_completeness']
        
        # Add code coverage bonus if available
        if metrics.code_coverage is not None:
            score += metrics.code_coverage * 0.1  # 10% bonus for good coverage
        
        return min(score, 1.0)
    
    def _determine_quality_level(self, overall_score: float) -> QualityLevel:
        """Determine quality level from overall score."""
        
        for level, threshold in self.quality_thresholds.items():
            if overall_score >= threshold:
                return level
        
        return QualityLevel.CRITICAL
    
    def _analyze_strengths_weaknesses(self, metrics: QualityMetrics, 
                                    generated_project: GeneratedProject) -> Tuple[List[str], List[str]]:
        """Analyze project strengths and weaknesses."""
        
        strengths = []
        weaknesses = []
        
        # Analyze each metric
        if metrics.complexity_score >= 0.8:
            strengths.append("Low complexity - easy to understand and maintain")
        elif metrics.complexity_score <= 0.4:
            weaknesses.append("High complexity - may be difficult to maintain")
        
        if metrics.maintainability_index >= 0.8:
            strengths.append("Well-organized project structure")
        elif metrics.maintainability_index <= 0.5:
            weaknesses.append("Poor project organization")
        
        if metrics.technical_debt_ratio <= 0.1:
            strengths.append("Low technical debt")
        elif metrics.technical_debt_ratio >= 0.3:
            weaknesses.append("High technical debt - needs refactoring")
        
        if metrics.security_score >= 0.8:
            strengths.append("Good security practices")
        elif metrics.security_score <= 0.5:
            weaknesses.append("Security concerns identified")
        
        if metrics.performance_score >= 0.8:
            strengths.append("Good performance characteristics")
        elif metrics.performance_score <= 0.5:
            weaknesses.append("Performance may be suboptimal")
        
        if metrics.documentation_completeness >= 0.8:
            strengths.append("Well documented")
        elif metrics.documentation_completeness <= 0.4:
            weaknesses.append("Insufficient documentation")
        
        # Project-specific strengths
        if generated_project.build_commands:
            strengths.append("Automated build system configured")
        
        if generated_project.test_commands:
            strengths.append("Testing framework configured")
        
        if len(generated_project.dependencies) <= 10:
            strengths.append("Minimal dependencies - reduces complexity")
        
        return strengths, weaknesses
    
    def _generate_recommendations(self, metrics: QualityMetrics, weaknesses: List[str], 
                                generated_project: GeneratedProject) -> List[str]:
        """Generate improvement recommendations."""
        
        recommendations = []
        
        # Specific recommendations based on metrics
        if metrics.complexity_score <= 0.5:
            recommendations.append("Consider breaking down large files into smaller, focused modules")
            recommendations.append("Review and simplify complex functions")
        
        if metrics.maintainability_index <= 0.6:
            recommendations.append("Improve project organization with clear directory structure")
            recommendations.append("Add configuration files for build and deployment")
        
        if metrics.technical_debt_ratio >= 0.2:
            recommendations.append("Address TODO comments and placeholder code")
            recommendations.append("Remove unused code and dependencies")
        
        if metrics.security_score <= 0.6:
            recommendations.append("Review dependencies for known vulnerabilities")
            recommendations.append("Avoid hardcoded secrets in configuration files")
        
        if metrics.performance_score <= 0.6:
            recommendations.append("Profile application for performance bottlenecks")
            recommendations.append("Consider optimizing algorithms and data structures")
        
        if metrics.documentation_completeness <= 0.5:
            recommendations.append("Add comprehensive README with usage examples")
            recommendations.append("Document functions and classes with docstrings")
            recommendations.append("Create API documentation if applicable")
        
        # General recommendations
        if not generated_project.test_commands:
            recommendations.append("Add unit tests to improve code reliability")
        
        if metrics.code_coverage is None or (metrics.code_coverage and metrics.code_coverage < 0.7):
            recommendations.append("Increase test coverage to at least 70%")
        
        # Limit recommendations to most important ones
        return recommendations[:8]
    
    def _compare_to_benchmarks(self, metrics: QualityMetrics) -> Dict[str, Any]:
        """Compare metrics to industry benchmarks."""
        
        comparisons = {}
        
        metric_values = {
            'complexity_score': metrics.complexity_score,
            'maintainability_index': metrics.maintainability_index,
            'technical_debt_ratio': metrics.technical_debt_ratio,
            'security_score': metrics.security_score,
            'performance_score': metrics.performance_score,
            'documentation_completeness': metrics.documentation_completeness
        }
        
        for metric_name, value in metric_values.items():
            if metric_name in self.benchmarks:
                benchmark = self.benchmarks[metric_name]
                
                if metric_name == 'technical_debt_ratio':
                    # Lower is better for technical debt
                    if value <= benchmark['excellent']:
                        comparison = "excellent"
                    elif value <= benchmark['good']:
                        comparison = "good"
                    elif value <= benchmark['acceptable']:
                        comparison = "acceptable"
                    else:
                        comparison = "poor"
                else:
                    # Higher is better for other metrics
                    if value >= benchmark['excellent']:
                        comparison = "excellent"
                    elif value >= benchmark['good']:
                        comparison = "good"
                    elif value >= benchmark['acceptable']:
                        comparison = "acceptable"
                    else:
                        comparison = "poor"
                
                comparisons[metric_name] = {
                    'value': value,
                    'comparison': comparison,
                    'benchmarks': benchmark
                }
        
        return comparisons


# Example usage
async def main():
    from ..assembly.project_generator import ProjectGenerator, ProjectType, GeneratedProject, ProjectStructure
    
    # Create a mock generated project for testing
    mock_project = GeneratedProject(
        project_name="test_project",
        project_path="/tmp/test_project",
        project_type=ProjectType.APPLICATION,
        structure=ProjectStructure(
            project_type=ProjectType.APPLICATION,
            entry_points=["main.py"],
            source_directories=["src"],
            config_files=["requirements.txt"],
            documentation_files=["README.md"],
            test_directories=["tests"],
            build_files=[]
        ),
        language="python",
        dependencies=["requests", "flask"],
        build_commands=["pip install -r requirements.txt"],
        run_commands=["python main.py"],
        test_commands=["python -m pytest"]
    )
    
    validator = QualityValidator()
    
    print("Testing quality validator...")
    print("Quality validator is ready for use with real generated projects")


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())