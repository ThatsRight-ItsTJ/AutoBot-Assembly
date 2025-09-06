"""
Unified File Scorer

Combines analysis results from MegaLinter, Semgrep, and AST-grep into composite scores.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .megalinter_client import MegaLinterResults, FileQualityScore
from .semgrep_client import SemgrepResults, SecurityScore, SemgrepFinding, SeverityLevel
from .astgrep_client import StructureAnalysis, AdaptationScore


@dataclass
class CompositeFileScore:
    overall_score: float
    component_scores: Dict[str, float]
    recommendation: str
    integration_priority: str
    detailed_analysis: Dict[str, Any]


class UnifiedFileScorer:
    """Combine all analysis results into actionable scores."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Configurable weights for different analysis components
        self.weight_config = {
            'quality': 0.3,        # MegaLinter results
            'security': 0.25,      # Semgrep results  
            'structure': 0.2,      # AST-grep results
            'standalone': 0.15,    # Dependency analysis
            'documentation': 0.1   # Documentation quality
        }
        
        # Thresholds for recommendations
        self.recommendation_thresholds = {
            'excellent': 0.9,
            'good': 0.75,
            'acceptable': 0.6,
            'needs_work': 0.4,
            'avoid': 0.0
        }
        
        # Priority thresholds
        self.priority_thresholds = {
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4,
            'skip': 0.0
        }
    
    def calculate_composite_score(self, 
                                file_path: str,
                                megalinter_score: Optional[FileQualityScore] = None,
                                semgrep_score: Optional[SecurityScore] = None,
                                astgrep_analysis: Optional[StructureAnalysis] = None) -> CompositeFileScore:
        """
        Generate unified score from all analysis tools.
        
        Args:
            file_path: Path to the file being scored
            megalinter_score: MegaLinter quality analysis
            semgrep_score: Semgrep security analysis  
            astgrep_analysis: AST-grep structure analysis
            
        Returns:
            CompositeFileScore with unified assessment
        """
        
        # Calculate individual component scores
        quality_score = self._normalize_quality_score(megalinter_score) if megalinter_score else 0.5
        security_score = semgrep_score.overall_score if semgrep_score else 0.5
        structure_score = self._calculate_structure_score(astgrep_analysis) if astgrep_analysis else 0.5
        standalone_score = self._calculate_standalone_score(astgrep_analysis) if astgrep_analysis else 0.5
        documentation_score = megalinter_score.documentation if megalinter_score else 0.5
        
        # Calculate weighted composite score
        composite_score = (
            quality_score * self.weight_config['quality'] +
            security_score * self.weight_config['security'] +
            structure_score * self.weight_config['structure'] +
            standalone_score * self.weight_config['standalone'] +
            documentation_score * self.weight_config['documentation']
        )
        
        # Generate recommendation and priority
        recommendation = self._generate_recommendation(composite_score, megalinter_score, semgrep_score, astgrep_analysis)
        integration_priority = self._calculate_priority(composite_score, astgrep_analysis)
        
        # Compile detailed analysis
        detailed_analysis = self._compile_detailed_analysis(
            file_path, megalinter_score, semgrep_score, astgrep_analysis
        )
        
        return CompositeFileScore(
            overall_score=composite_score,
            component_scores={
                'quality': quality_score,
                'security': security_score,
                'structure': structure_score,
                'standalone': standalone_score,
                'documentation': documentation_score
            },
            recommendation=recommendation,
            integration_priority=integration_priority,
            detailed_analysis=detailed_analysis
        )
    
    def score_repository_files(self, 
                             megalinter_results: Optional[MegaLinterResults] = None,
                             semgrep_results: Optional[SemgrepResults] = None,
                             astgrep_analyses: Optional[Dict[str, StructureAnalysis]] = None) -> Dict[str, CompositeFileScore]:
        """Score all files in a repository."""
        
        file_scores = {}
        
        # Get all unique file paths from all analyses
        all_files = set()
        
        if megalinter_results:
            all_files.update(megalinter_results.file_scores.keys())
        
        if semgrep_results:
            all_files.update(finding.file_path for finding in semgrep_results.findings)
        
        if astgrep_analyses:
            all_files.update(astgrep_analyses.keys())
        
        # Score each file
        for file_path in all_files:
            megalinter_score = megalinter_results.file_scores.get(file_path) if megalinter_results else None
            
            # Get Semgrep score for this file
            semgrep_score = None
            if semgrep_results:
                file_findings = [f for f in semgrep_results.findings if f.file_path == file_path]
                if file_findings:
                    # Calculate file-specific security score
                    semgrep_score = self._calculate_file_security_score(file_findings)
            
            astgrep_analysis = astgrep_analyses.get(file_path) if astgrep_analyses else None
            
            composite_score = self.calculate_composite_score(
                file_path, megalinter_score, semgrep_score, astgrep_analysis
            )
            
            file_scores[file_path] = composite_score
        
        return file_scores
    
    def get_top_files(self, file_scores: Dict[str, CompositeFileScore], 
                     top_n: int = 20, min_score: float = 0.6) -> List[tuple]:
        """Get top-scoring files for integration."""
        
        # Filter by minimum score and sort by overall score
        qualified_files = [
            (file_path, score) for file_path, score in file_scores.items()
            if score.overall_score >= min_score
        ]
        
        # Sort by overall score (highest first)
        sorted_files = sorted(qualified_files, key=lambda x: x[1].overall_score, reverse=True)
        
        return sorted_files[:top_n]
    
    def _normalize_quality_score(self, megalinter_score: FileQualityScore) -> float:
        """Normalize MegaLinter quality score."""
        
        # Weight the different quality components
        quality_components = {
            'complexity': megalinter_score.complexity * 0.3,
            'maintainability': megalinter_score.maintainability * 0.4,
            'style_compliance': megalinter_score.style_compliance * 0.3
        }
        
        return sum(quality_components.values())
    
    def _calculate_structure_score(self, astgrep_analysis: StructureAnalysis) -> float:
        """Calculate structure score from AST-grep analysis."""
        
        # Combine complexity and maintainability scores
        structure_score = (
            (1.0 - astgrep_analysis.complexity_score) * 0.4 +  # Lower complexity is better
            astgrep_analysis.maintainability_score * 0.6
        )
        
        return max(0.0, min(1.0, structure_score))
    
    def _calculate_standalone_score(self, astgrep_analysis: StructureAnalysis) -> float:
        """Calculate how standalone/reusable the code is."""
        
        if not astgrep_analysis:
            return 0.5
        
        score = 1.0
        
        # Penalty for too many external dependencies
        dep_count = astgrep_analysis.imports.dependency_count
        if dep_count > 10:
            score -= 0.4
        elif dep_count > 5:
            score -= 0.2
        
        # Penalty for high framework coupling
        coupling = astgrep_analysis.framework_dependencies.coupling_score
        if coupling > 0.8:
            score -= 0.3
        elif coupling > 0.5:
            score -= 0.1
        
        # Bonus for good maintainability
        if astgrep_analysis.maintainability_score > 0.8:
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_file_security_score(self, findings: List[SemgrepFinding]) -> SecurityScore:
        """Calculate security score for a specific file."""
        
        severity_counts = {
            SeverityLevel.ERROR: 0,
            SeverityLevel.WARNING: 0,
            SeverityLevel.INFO: 0
        }
        
        for finding in findings:
            severity_counts[finding.severity] += 1
        
        # Calculate score (starts at 1.0, decreases with findings)
        total_score = 1.0
        
        severity_weights = {
            SeverityLevel.ERROR: 1.0,
            SeverityLevel.WARNING: 0.6,
            SeverityLevel.INFO: 0.2
        }
        
        for severity, count in severity_counts.items():
            weight = severity_weights[severity]
            reduction = min(0.8, count * weight * 0.1)
            total_score -= reduction
        
        overall_score = max(0.0, total_score)
        
        critical_issues = [f for f in findings if f.severity == SeverityLevel.ERROR]
        
        return SecurityScore(
            overall_score=overall_score,
            vulnerability_count=severity_counts[SeverityLevel.ERROR],
            warning_count=severity_counts[SeverityLevel.WARNING],
            info_count=severity_counts[SeverityLevel.INFO],
            critical_issues=critical_issues,
            security_categories={}
        )
    
    def _generate_recommendation(self, composite_score: float,
                               megalinter_score: Optional[FileQualityScore],
                               semgrep_score: Optional[SecurityScore],
                               astgrep_analysis: Optional[StructureAnalysis]) -> str:
        """Generate human-readable recommendation."""
        
        if composite_score >= self.recommendation_thresholds['excellent']:
            recommendation = "Excellent - Highly recommended for integration"
        elif composite_score >= self.recommendation_thresholds['good']:
            recommendation = "Good - Recommended with minor considerations"
        elif composite_score >= self.recommendation_thresholds['acceptable']:
            recommendation = "Acceptable - Consider with caution"
        elif composite_score >= self.recommendation_thresholds['needs_work']:
            recommendation = "Needs work - Significant issues present"
        else:
            recommendation = "Avoid - Too many issues for safe integration"
        
        # Add specific concerns
        concerns = []
        
        if semgrep_score and semgrep_score.vulnerability_count > 0:
            concerns.append(f"{semgrep_score.vulnerability_count} security vulnerabilities")
        
        if megalinter_score and megalinter_score.style_compliance < 0.5:
            concerns.append("poor code style compliance")
        
        if astgrep_analysis and astgrep_analysis.imports.dependency_count > 15:
            concerns.append("high dependency count")
        
        if astgrep_analysis and astgrep_analysis.framework_dependencies.coupling_score > 0.8:
            concerns.append("tight framework coupling")
        
        if concerns:
            recommendation += f" (Concerns: {', '.join(concerns)})"
        
        return recommendation
    
    def _calculate_priority(self, composite_score: float, astgrep_analysis: Optional[StructureAnalysis]) -> str:
        """Calculate integration priority."""
        
        if composite_score >= self.priority_thresholds['high']:
            priority = "High"
        elif composite_score >= self.priority_thresholds['medium']:
            priority = "Medium"
        elif composite_score >= self.priority_thresholds['low']:
            priority = "Low"
        else:
            priority = "Skip"
        
        # Adjust priority based on adaptation effort
        if astgrep_analysis:
            adaptation_score = AdaptationScore(
                overall_effort=0.0,
                estimated_hours=0,
                complexity_factors={}
            )
            
            # Simple adaptation effort calculation
            dep_count = astgrep_analysis.imports.dependency_count
            coupling = astgrep_analysis.framework_dependencies.coupling_score
            
            if dep_count > 20 or coupling > 0.9:
                if priority == "High":
                    priority = "Medium"
                elif priority == "Medium":
                    priority = "Low"
        
        return priority
    
    def _compile_detailed_analysis(self, file_path: str,
                                 megalinter_score: Optional[FileQualityScore],
                                 semgrep_score: Optional[SecurityScore],
                                 astgrep_analysis: Optional[StructureAnalysis]) -> Dict[str, Any]:
        """Compile detailed analysis information."""
        
        analysis = {
            'file_path': file_path,
            'analysis_timestamp': None,  # Would be set by caller
            'tools_used': []
        }
        
        if megalinter_score:
            analysis['tools_used'].append('MegaLinter')
            analysis['quality_analysis'] = {
                'complexity': megalinter_score.complexity,
                'maintainability': megalinter_score.maintainability,
                'style_compliance': megalinter_score.style_compliance,
                'documentation': megalinter_score.documentation,
                'overall_quality': megalinter_score.overall_score
            }
        
        if semgrep_score:
            analysis['tools_used'].append('Semgrep')
            analysis['security_analysis'] = {
                'overall_score': semgrep_score.overall_score,
                'vulnerabilities': semgrep_score.vulnerability_count,
                'warnings': semgrep_score.warning_count,
                'info_issues': semgrep_score.info_count,
                'critical_issues_count': len(semgrep_score.critical_issues),
                'security_categories': semgrep_score.security_categories
            }
        
        if astgrep_analysis:
            analysis['tools_used'].append('AST-grep')
            analysis['structure_analysis'] = {
                'dependency_count': astgrep_analysis.imports.dependency_count,
                'external_dependencies': astgrep_analysis.imports.external_dependencies,
                'class_count': astgrep_analysis.class_metrics.class_count,
                'method_count': astgrep_analysis.class_metrics.method_count,
                'detected_frameworks': astgrep_analysis.framework_dependencies.frameworks,
                'framework_coupling': astgrep_analysis.framework_dependencies.coupling_score,
                'complexity_score': astgrep_analysis.complexity_score,
                'maintainability_score': astgrep_analysis.maintainability_score
            }
        
        return analysis
    
    def generate_integration_report(self, file_scores: Dict[str, CompositeFileScore]) -> Dict[str, Any]:
        """Generate comprehensive integration report."""
        
        # Calculate summary statistics
        all_scores = [score.overall_score for score in file_scores.values()]
        
        if all_scores:
            avg_score = sum(all_scores) / len(all_scores)
            max_score = max(all_scores)
            min_score = min(all_scores)
        else:
            avg_score = max_score = min_score = 0.0
        
        # Count files by recommendation
        recommendation_counts = {}
        priority_counts = {}
        
        for score in file_scores.values():
            rec = score.recommendation.split(' - ')[0]  # Get first part of recommendation
            recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1
            
            priority_counts[score.integration_priority] = priority_counts.get(score.integration_priority, 0) + 1
        
        # Get top files
        top_files = self.get_top_files(file_scores, top_n=10, min_score=0.6)
        
        return {
            'summary': {
                'total_files': len(file_scores),
                'average_score': avg_score,
                'max_score': max_score,
                'min_score': min_score,
                'files_above_threshold': len([s for s in all_scores if s >= 0.6])
            },
            'recommendations': recommendation_counts,
            'priorities': priority_counts,
            'top_files': [
                {
                    'file_path': file_path,
                    'score': score.overall_score,
                    'recommendation': score.recommendation,
                    'priority': score.integration_priority
                }
                for file_path, score in top_files
            ],
            'analysis_coverage': {
                'files_with_quality_analysis': len([s for s in file_scores.values() if 'quality_analysis' in s.detailed_analysis]),
                'files_with_security_analysis': len([s for s in file_scores.values() if 'security_analysis' in s.detailed_analysis]),
                'files_with_structure_analysis': len([s for s in file_scores.values() if 'structure_analysis' in s.detailed_analysis])
            }
        }


# Example usage
async def main():
    from .megalinter_client import MegaLinterAnalyzer
    from .semgrep_client import SemgrepAnalyzer
    from .astgrep_client import ASTGrepAnalyzer
    
    # Initialize analyzers
    megalinter = MegaLinterAnalyzer()
    semgrep = SemgrepAnalyzer()
    astgrep = ASTGrepAnalyzer()
    scorer = UnifiedFileScorer()
    
    # Test with current repository
    repo_path = "."
    print("Running comprehensive file analysis...")
    
    # Run all analyses
    print("  Running MegaLinter...")
    megalinter_results = await megalinter.analyze_repository(repo_path, "python")
    
    print("  Running Semgrep...")
    semgrep_results = await semgrep.analyze_repository(repo_path, "python")
    
    print("  Running AST-grep...")
    astgrep_analyses = await astgrep.analyze_repository_structure(repo_path, "python")
    
    # Calculate composite scores
    print("  Calculating composite scores...")
    file_scores = scorer.score_repository_files(megalinter_results, semgrep_results, astgrep_analyses)
    
    # Generate report
    report = scorer.generate_integration_report(file_scores)
    
    print(f"\nIntegration Report:")
    print(f"  Total files analyzed: {report['summary']['total_files']}")
    print(f"  Average score: {report['summary']['average_score']:.2f}")
    print(f"  Files above threshold: {report['summary']['files_above_threshold']}")
    
    print(f"\nTop files for integration:")
    for file_info in report['top_files'][:5]:
        print(f"  {file_info['file_path']}: {file_info['score']:.2f} ({file_info['priority']} priority)")


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())