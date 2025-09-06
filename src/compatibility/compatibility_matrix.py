"""
Compatibility Matrix Generator

Generates comprehensive compatibility matrices combining framework, license, 
and technical compatibility analysis.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from .framework_checker import FrameworkCompatibilityChecker, CompatibilityMatrix as FrameworkMatrix
from .license_analyzer import LicenseAnalyzer, LicenseAnalysis
from ..analysis.unified_scorer import UnifiedFileScorer, CompositeFileScore
from ..search.tier1_packages import PackageResult
from ..search.tier2_curated import RepositoryResult
from ..search.tier3_discovery import SearchResult


@dataclass
class TechnicalCompatibility:
    language_compatibility: float
    version_compatibility: float
    dependency_conflicts: List[str]
    runtime_compatibility: float


@dataclass
class IntegrationComplexity:
    setup_complexity: float
    configuration_conflicts: List[str]
    integration_effort_hours: int
    risk_factors: List[str]


@dataclass
class ComprehensiveCompatibility:
    component_id: str
    component_name: str
    framework_compatibility: float
    license_compatibility: str
    technical_compatibility: TechnicalCompatibility
    integration_complexity: IntegrationComplexity
    overall_score: float
    recommendation: str
    priority: str


@dataclass
class CompatibilityReport:
    components: List[ComprehensiveCompatibility]
    framework_analysis: FrameworkMatrix
    license_analysis: LicenseAnalysis
    recommended_combinations: List[List[str]]
    integration_roadmap: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    summary: Dict[str, Any]


class CompatibilityMatrixGenerator:
    """Generate comprehensive compatibility analysis combining all factors."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.framework_checker = FrameworkCompatibilityChecker()
        self.license_analyzer = LicenseAnalyzer()
        self.file_scorer = UnifiedFileScorer()
        
        # Integration complexity weights
        self.complexity_weights = {
            'dependency_count': 0.25,
            'framework_coupling': 0.25,
            'license_restrictions': 0.2,
            'technical_debt': 0.15,
            'documentation_quality': 0.15
        }
    
    async def generate_comprehensive_matrix(self, components: List[Any], 
                                          language: str,
                                          project_requirements: Optional[Dict[str, Any]] = None) -> CompatibilityReport:
        """
        Generate comprehensive compatibility matrix.
        
        Args:
            components: List of discovered components
            language: Target programming language
            project_requirements: Optional project-specific requirements
            
        Returns:
            CompatibilityReport with comprehensive analysis
        """
        
        self.logger.info(f"Generating compatibility matrix for {len(components)} components")
        
        # Run all analyses
        framework_analysis = await self.framework_checker.analyze_component_compatibility(components, language)
        license_analysis = await self.license_analyzer.analyze_license_compliance(components)
        
        # Generate individual component compatibility assessments
        component_compatibilities = []
        for i, component in enumerate(components):
            compatibility = await self._assess_component_compatibility(
                component, i, framework_analysis, license_analysis, language, project_requirements
            )
            component_compatibilities.append(compatibility)
        
        # Find recommended combinations
        recommended_combinations = self._find_recommended_combinations(
            component_compatibilities, framework_analysis
        )
        
        # Generate integration roadmap
        integration_roadmap = self._generate_integration_roadmap(
            component_compatibilities, recommended_combinations
        )
        
        # Assess overall risks
        risk_assessment = self._assess_integration_risks(
            component_compatibilities, framework_analysis, license_analysis
        )
        
        # Generate summary
        summary = self._generate_compatibility_summary(
            component_compatibilities, framework_analysis, license_analysis
        )
        
        return CompatibilityReport(
            components=component_compatibilities,
            framework_analysis=framework_analysis,
            license_analysis=license_analysis,
            recommended_combinations=recommended_combinations,
            integration_roadmap=integration_roadmap,
            risk_assessment=risk_assessment,
            summary=summary
        )
    
    async def _assess_component_compatibility(self, component: Any, component_index: int,
                                            framework_analysis: FrameworkMatrix,
                                            license_analysis: LicenseAnalysis,
                                            language: str,
                                            project_requirements: Optional[Dict[str, Any]]) -> ComprehensiveCompatibility:
        """Assess compatibility for a single component."""
        
        component_id = f"component_{component_index}"
        component_name = getattr(component, 'name', f'Component {component_index}')
        
        # Framework compatibility score
        framework_score = self._calculate_framework_score(component_id, framework_analysis)
        
        # License compatibility status
        license_status = self._get_license_status(component_id, license_analysis)
        
        # Technical compatibility
        technical_compatibility = await self._assess_technical_compatibility(component, language)
        
        # Integration complexity
        integration_complexity = self._assess_integration_complexity(
            component, framework_analysis, license_analysis, project_requirements
        )
        
        # Calculate overall score
        overall_score = self._calculate_overall_compatibility_score(
            framework_score, license_status, technical_compatibility, integration_complexity
        )
        
        # Generate recommendation
        recommendation = self._generate_component_recommendation(
            overall_score, framework_score, license_status, integration_complexity
        )
        
        # Determine priority
        priority = self._determine_integration_priority(overall_score, integration_complexity)
        
        return ComprehensiveCompatibility(
            component_id=component_id,
            component_name=component_name,
            framework_compatibility=framework_score,
            license_compatibility=license_status,
            technical_compatibility=technical_compatibility,
            integration_complexity=integration_complexity,
            overall_score=overall_score,
            recommendation=recommendation,
            priority=priority
        )
    
    def _calculate_framework_score(self, component_id: str, framework_analysis: FrameworkMatrix) -> float:
        """Calculate framework compatibility score for component."""
        
        # Check if component is involved in any conflicts
        conflicts_involving_component = []
        
        # This is a simplified approach - in practice, you'd need better mapping
        # between components and framework conflicts
        for conflict in framework_analysis.conflicts:
            # Assume component is involved if it has matching frameworks
            component_info = framework_analysis.components.get(component_id, {})
            component_frameworks = component_info.get('frameworks', [])
            
            if conflict.framework1 in component_frameworks or conflict.framework2 in component_frameworks:
                conflicts_involving_component.append(conflict)
        
        # Calculate score based on conflicts
        base_score = 1.0
        for conflict in conflicts_involving_component:
            if conflict.severity.value == 'critical':
                base_score -= 0.4
            elif conflict.severity.value == 'high':
                base_score -= 0.3
            elif conflict.severity.value == 'medium':
                base_score -= 0.2
            elif conflict.severity.value == 'low':
                base_score -= 0.1
        
        return max(0.0, base_score)
    
    def _get_license_status(self, component_id: str, license_analysis: LicenseAnalysis) -> str:
        """Get license compatibility status for component."""
        
        license_info = license_analysis.detected_licenses.get(component_id)
        if not license_info:
            return "Unknown"
        
        # Check if this license is involved in any incompatibilities
        for compatibility in license_analysis.compatibility_matrix:
            if (compatibility.license1 == license_info.license_type or 
                compatibility.license2 == license_info.license_type):
                if compatibility.status.value == 'incompatible':
                    return "Incompatible"
                elif compatibility.status.value == 'conditional':
                    return "Conditional"
        
        return "Compatible"
    
    async def _assess_technical_compatibility(self, component: Any, language: str) -> TechnicalCompatibility:
        """Assess technical compatibility factors."""
        
        # Language compatibility (simplified)
        component_language = getattr(component, 'language', language)
        language_compatibility = 1.0 if component_language.lower() == language.lower() else 0.5
        
        # Version compatibility (simplified - would need more sophisticated analysis)
        version_compatibility = 0.8  # Default assumption
        
        # Dependency conflicts (simplified)
        dependency_conflicts = []
        dependencies = getattr(component, 'dependencies', [])
        if len(dependencies) > 20:
            dependency_conflicts.append("High dependency count may cause conflicts")
        
        # Runtime compatibility
        runtime_compatibility = 0.9  # Default assumption
        
        return TechnicalCompatibility(
            language_compatibility=language_compatibility,
            version_compatibility=version_compatibility,
            dependency_conflicts=dependency_conflicts,
            runtime_compatibility=runtime_compatibility
        )
    
    def _assess_integration_complexity(self, component: Any,
                                     framework_analysis: FrameworkMatrix,
                                     license_analysis: LicenseAnalysis,
                                     project_requirements: Optional[Dict[str, Any]]) -> IntegrationComplexity:
        """Assess integration complexity."""
        
        # Setup complexity based on dependencies and configuration
        dependencies_count = getattr(component, 'dependencies_count', 0)
        setup_complexity = min(1.0, dependencies_count / 20.0)  # Normalize to 0-1
        
        # Configuration conflicts
        configuration_conflicts = []
        
        # Check for framework conflicts
        component_name = getattr(component, 'name', '')
        for conflict in framework_analysis.conflicts:
            if component_name in [conflict.framework1, conflict.framework2]:
                configuration_conflicts.append(f"Framework conflict: {conflict.reason}")
        
        # Integration effort estimation
        base_hours = 4  # Base integration time
        complexity_hours = int(setup_complexity * 16)  # Up to 16 additional hours
        license_hours = 2 if any(req.component_name == component_name 
                               for req in license_analysis.attribution_requirements) else 0
        
        integration_effort_hours = base_hours + complexity_hours + license_hours
        
        # Risk factors
        risk_factors = []
        if setup_complexity > 0.7:
            risk_factors.append("High setup complexity")
        if configuration_conflicts:
            risk_factors.append("Configuration conflicts present")
        if not getattr(component, 'license', None):
            risk_factors.append("Unknown license")
        
        return IntegrationComplexity(
            setup_complexity=setup_complexity,
            configuration_conflicts=configuration_conflicts,
            integration_effort_hours=integration_effort_hours,
            risk_factors=risk_factors
        )
    
    def _calculate_overall_compatibility_score(self, framework_score: float,
                                             license_status: str,
                                             technical_compatibility: TechnicalCompatibility,
                                             integration_complexity: IntegrationComplexity) -> float:
        """Calculate overall compatibility score."""
        
        # License score
        license_score_map = {
            "Compatible": 1.0,
            "Conditional": 0.7,
            "Incompatible": 0.0,
            "Unknown": 0.5
        }
        license_score = license_score_map.get(license_status, 0.5)
        
        # Technical score (average of technical factors)
        technical_score = (
            technical_compatibility.language_compatibility * 0.3 +
            technical_compatibility.version_compatibility * 0.3 +
            technical_compatibility.runtime_compatibility * 0.4
        )
        
        # Integration score (inverse of complexity)
        integration_score = 1.0 - integration_complexity.setup_complexity
        
        # Weighted overall score
        overall_score = (
            framework_score * 0.3 +
            license_score * 0.25 +
            technical_score * 0.25 +
            integration_score * 0.2
        )
        
        return overall_score
    
    def _generate_component_recommendation(self, overall_score: float,
                                         framework_score: float,
                                         license_status: str,
                                         integration_complexity: IntegrationComplexity) -> str:
        """Generate recommendation for component."""
        
        if overall_score >= 0.8:
            recommendation = "Highly recommended - Low risk, high compatibility"
        elif overall_score >= 0.6:
            recommendation = "Recommended - Good compatibility with minor considerations"
        elif overall_score >= 0.4:
            recommendation = "Consider carefully - Moderate compatibility issues"
        else:
            recommendation = "Not recommended - Significant compatibility issues"
        
        # Add specific concerns
        concerns = []
        if framework_score < 0.5:
            concerns.append("framework conflicts")
        if license_status == "Incompatible":
            concerns.append("license incompatibility")
        if integration_complexity.setup_complexity > 0.7:
            concerns.append("high integration complexity")
        
        if concerns:
            recommendation += f" (Issues: {', '.join(concerns)})"
        
        return recommendation
    
    def _determine_integration_priority(self, overall_score: float,
                                      integration_complexity: IntegrationComplexity) -> str:
        """Determine integration priority."""
        
        if overall_score >= 0.8 and integration_complexity.setup_complexity < 0.5:
            return "High"
        elif overall_score >= 0.6:
            return "Medium"
        elif overall_score >= 0.4:
            return "Low"
        else:
            return "Skip"
    
    def _find_recommended_combinations(self, component_compatibilities: List[ComprehensiveCompatibility],
                                     framework_analysis: FrameworkMatrix) -> List[List[str]]:
        """Find recommended component combinations."""
        
        # Use framework analysis compatible sets as base
        combinations = []
        
        for compatible_set in framework_analysis.compatible_sets:
            if compatible_set.compatibility_score >= 0.6:
                # Map components back to names
                component_names = []
                for component in compatible_set.components:
                    name = getattr(component, 'name', 'Unknown')
                    component_names.append(name)
                
                combinations.append(component_names)
        
        # Add individual high-scoring components
        high_scoring_components = [
            comp.component_name for comp in component_compatibilities
            if comp.overall_score >= 0.8 and comp.priority in ["High", "Medium"]
        ]
        
        if high_scoring_components and len(high_scoring_components) <= 5:
            combinations.append(high_scoring_components)
        
        return combinations[:5]  # Limit to top 5 combinations
    
    def _generate_integration_roadmap(self, component_compatibilities: List[ComprehensiveCompatibility],
                                    recommended_combinations: List[List[str]]) -> List[Dict[str, Any]]:
        """Generate integration roadmap."""
        
        roadmap = []
        
        # Phase 1: High priority, low complexity components
        phase1_components = [
            comp for comp in component_compatibilities
            if comp.priority == "High" and comp.integration_complexity.setup_complexity < 0.5
        ]
        
        if phase1_components:
            roadmap.append({
                "phase": 1,
                "title": "Quick Wins - High Value, Low Complexity",
                "components": [comp.component_name for comp in phase1_components],
                "estimated_hours": sum(comp.integration_complexity.integration_effort_hours for comp in phase1_components),
                "description": "Start with these components for immediate value"
            })
        
        # Phase 2: Medium priority components
        phase2_components = [
            comp for comp in component_compatibilities
            if comp.priority == "Medium"
        ]
        
        if phase2_components:
            roadmap.append({
                "phase": 2,
                "title": "Core Integration - Moderate Complexity",
                "components": [comp.component_name for comp in phase2_components],
                "estimated_hours": sum(comp.integration_complexity.integration_effort_hours for comp in phase2_components),
                "description": "Integrate these components after establishing foundation"
            })
        
        # Phase 3: Complex but valuable components
        phase3_components = [
            comp for comp in component_compatibilities
            if comp.priority == "Low" and comp.overall_score >= 0.5
        ]
        
        if phase3_components:
            roadmap.append({
                "phase": 3,
                "title": "Advanced Features - High Complexity",
                "components": [comp.component_name for comp in phase3_components],
                "estimated_hours": sum(comp.integration_complexity.integration_effort_hours for comp in phase3_components),
                "description": "Consider these components for advanced functionality"
            })
        
        return roadmap
    
    def _assess_integration_risks(self, component_compatibilities: List[ComprehensiveCompatibility],
                                framework_analysis: FrameworkMatrix,
                                license_analysis: LicenseAnalysis) -> Dict[str, Any]:
        """Assess overall integration risks."""
        
        risks = {
            "high_risk_components": [],
            "license_risks": [],
            "framework_conflicts": [],
            "technical_risks": [],
            "mitigation_strategies": []
        }
        
        # High risk components
        high_risk = [comp for comp in component_compatibilities if comp.overall_score < 0.4]
        risks["high_risk_components"] = [
            {"name": comp.component_name, "score": comp.overall_score, "issues": comp.integration_complexity.risk_factors}
            for comp in high_risk
        ]
        
        # License risks
        if "Non-compliant" in license_analysis.overall_compliance_status:
            risks["license_risks"].append("Incompatible licenses detected")
        if license_analysis.source_disclosure_required:
            risks["license_risks"].append("Source code disclosure required")
        
        # Framework conflicts
        critical_conflicts = [c for c in framework_analysis.conflicts if c.severity.value == 'critical']
        risks["framework_conflicts"] = [
            {"frameworks": [c.framework1, c.framework2], "reason": c.reason}
            for c in critical_conflicts
        ]
        
        # Technical risks
        high_complexity_components = [
            comp for comp in component_compatibilities 
            if comp.integration_complexity.setup_complexity > 0.7
        ]
        if high_complexity_components:
            risks["technical_risks"].append(f"{len(high_complexity_components)} components have high integration complexity")
        
        # Mitigation strategies
        if high_risk:
            risks["mitigation_strategies"].append("Remove or replace high-risk components")
        if critical_conflicts:
            risks["mitigation_strategies"].append("Use microservices architecture to isolate conflicting frameworks")
        if license_analysis.source_disclosure_required:
            risks["mitigation_strategies"].append("Prepare for open source compliance requirements")
        
        return risks
    
    def _generate_compatibility_summary(self, component_compatibilities: List[ComprehensiveCompatibility],
                                      framework_analysis: FrameworkMatrix,
                                      license_analysis: LicenseAnalysis) -> Dict[str, Any]:
        """Generate compatibility summary."""
        
        total_components = len(component_compatibilities)
        if total_components == 0:
            return {"status": "No components to analyze"}
        
        # Score distribution
        high_score = len([c for c in component_compatibilities if c.overall_score >= 0.8])
        medium_score = len([c for c in component_compatibilities if 0.6 <= c.overall_score < 0.8])
        low_score = len([c for c in component_compatibilities if c.overall_score < 0.6])
        
        # Priority distribution
        high_priority = len([c for c in component_compatibilities if c.priority == "High"])
        medium_priority = len([c for c in component_compatibilities if c.priority == "Medium"])
        low_priority = len([c for c in component_compatibilities if c.priority == "Low"])
        skip_priority = len([c for c in component_compatibilities if c.priority == "Skip"])
        
        # Overall assessment
        avg_score = sum(c.overall_score for c in component_compatibilities) / total_components
        
        if avg_score >= 0.8:
            overall_assessment = "Excellent compatibility - Low integration risk"
        elif avg_score >= 0.6:
            overall_assessment = "Good compatibility - Moderate integration effort"
        elif avg_score >= 0.4:
            overall_assessment = "Fair compatibility - Significant planning required"
        else:
            overall_assessment = "Poor compatibility - High risk integration"
        
        return {
            "total_components": total_components,
            "average_score": avg_score,
            "score_distribution": {
                "high": high_score,
                "medium": medium_score,
                "low": low_score
            },
            "priority_distribution": {
                "high": high_priority,
                "medium": medium_priority,
                "low": low_priority,
                "skip": skip_priority
            },
            "framework_compatibility": framework_analysis.overall_compatibility,
            "license_status": license_analysis.overall_compliance_status,
            "recommended_combinations": len([s for s in framework_analysis.compatible_sets if s.compatibility_score >= 0.6]),
            "overall_assessment": overall_assessment,
            "total_integration_hours": sum(c.integration_complexity.integration_effort_hours for c in component_compatibilities)
        }


# Example usage
async def main():
    from ..search.tier1_packages import PackageResult
    from datetime import datetime
    
    generator = CompatibilityMatrixGenerator()
    
    # Create test components
    test_components = [
        PackageResult(
            name="fastapi",
            repository_url="https://github.com/tiangolo/fastapi",
            description="FastAPI framework for building APIs",
            downloads=1000000,
            stars=50000,
            last_updated=datetime.now(),
            license="MIT",
            quality_score=0.9,
            language="python",
            package_manager="pypi",
            version="0.100.0",
            dependencies_count=5
        ),
        PackageResult(
            name="requests",
            repository_url="https://github.com/psf/requests",
            description="HTTP library for Python",
            downloads=2000000,
            stars=55000,
            last_updated=datetime.now(),
            license="Apache-2.0",
            quality_score=0.95,
            language="python",
            package_manager="pypi",
            version="2.31.0",
            dependencies_count=3
        )
    ]
    
    print("Generating comprehensive compatibility matrix...")
    report = await generator.generate_comprehensive_matrix(test_components, "python")
    
    print(f"\nCompatibility Report Summary:")
    print(f"  Total components: {report.summary['total_components']}")
    print(f"  Average score: {report.summary['average_score']:.2f}")
    print(f"  Overall assessment: {report.summary['overall_assessment']}")
    print(f"  Total integration hours: {report.summary['total_integration_hours']}")
    
    print(f"\nComponent Analysis:")
    for comp in report.components:
        print(f"  {comp.component_name}: {comp.overall_score:.2f} ({comp.priority} priority)")
        print(f"    Recommendation: {comp.recommendation}")
    
    print(f"\nIntegration Roadmap:")
    for phase in report.integration_roadmap:
        print(f"  Phase {phase['phase']}: {phase['title']}")
        print(f"    Components: {', '.join(phase['components'])}")
        print(f"    Estimated hours: {phase['estimated_hours']}")


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())