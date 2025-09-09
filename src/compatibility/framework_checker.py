"""
Framework Compatibility Checker

Ensures discovered components can work together by analyzing framework dependencies,
version constraints, and potential conflicts.
"""

import logging
import json
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from ..analysis.astgrep_client import StructureAnalysis
from ..search.tier1_packages import PackageResult
from ..search.tier2_curated import RepositoryResult
from ..search.tier3_discovery import DiscoveredRepository


class ConflictSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class FrameworkConflict:
    framework1: str
    framework2: str
    reason: str
    severity: ConflictSeverity
    resolution_suggestions: List[str]


@dataclass
class VersionConstraint:
    package: str
    min_version: Optional[str]
    max_version: Optional[str]
    exact_version: Optional[str]
    conflicts_with: List[str]


@dataclass
class CompatibilityCheck:
    has_conflicts: bool
    conflicts: List[FrameworkConflict]
    compatibility_score: float
    resolution_difficulty: str


@dataclass
class CompatibleSet:
    components: List[Any]
    frameworks: List[str]
    shared_dependencies: List[str]
    compatibility_score: float


@dataclass
class CompatibilityMatrix:
    components: Dict[str, Dict[str, Any]]
    conflicts: List[FrameworkConflict]
    compatible_sets: List[CompatibleSet]
    recommendations: List[str]
    overall_compatibility: float


class FrameworkCompatibilityChecker:
    """Analyze compatibility between discovered components."""
    
        
            'python': [
                {
                    'frameworks': ['django', 'fastapi'],
                    'reason': 'Different WSGI/ASGI patterns and ORM approaches',
                    'severity': ConflictSeverity.HIGH,
                    'resolution': ['Use Django REST Framework instead of FastAPI', 'Separate services approach']
                },
                {
                    'frameworks': ['flask', 'django'],
                    'reason': 'Different templating and ORM systems',
                    'severity': ConflictSeverity.MEDIUM,
                    'resolution': ['Choose one as primary framework', 'Use microservices architecture']
                },
                {
                    'frameworks': ['asyncio', 'threading'],
                    'reason': 'Different concurrency models',
                    'severity': ConflictSeverity.HIGH,
                    'resolution': ['Stick to one concurrency model', 'Use asyncio-compatible libraries']
                }
            ],
            'javascript': [
                {
                    'frameworks': ['react', 'vue'],
                    'reason': 'Different component systems and virtual DOM implementations',
                    'severity': ConflictSeverity.CRITICAL,
                    'resolution': ['Choose one frontend framework', 'Use micro-frontends architecture']
                },
                {
                    'frameworks': ['webpack', 'rollup'],
                    'reason': 'Different bundling strategies and plugin systems',
                    'severity': ConflictSeverity.MEDIUM,
                    'resolution': ['Choose primary bundler', 'Use different bundlers for different purposes']
                }
            ],
            'java': [
                {
                    'frameworks': ['spring-boot', 'dropwizard'],
                    'reason': 'Different application bootstrapping and configuration',
                    'severity': ConflictSeverity.HIGH,
                    'resolution': ['Choose one application framework', 'Separate services']
                }
            ]
        }
    
    async def analyze_component_compatibility(self, components: List[Any], language: str) -> CompatibilityMatrix:
        """
        Analyze compatibility between discovered components.
        
        Args:
            components: List of discovered components (PackageResult, RepositoryResult, DiscoveredRepository)
            language: Target programming language
            
        Returns:
            CompatibilityMatrix with comprehensive compatibility analysis
        """
        
        # Extract framework information from each component
        component_frameworks = {}
        for i, component in enumerate(components):
            component_id = f"component_{i}"
            frameworks = await self._extract_component_frameworks(component, language)
            component_frameworks[component_id] = {
                'component': component,
                'frameworks': frameworks,
                'dependencies': self._extract_dependencies(component)
            }
        
        # Check for conflicts
        conflicts = self._identify_conflicts(component_frameworks, language)
        
        # Find compatible sets
        compatible_sets = self._find_compatible_sets(component_frameworks, conflicts)
        
        # Generate recommendations
        recommendations = self._generate_compatibility_recommendations(conflicts, compatible_sets)
        
        # Calculate overall compatibility
        overall_compatibility = self._calculate_overall_compatibility(conflicts, len(components))
        
        return CompatibilityMatrix(
            components=component_frameworks,
            conflicts=conflicts,
            compatible_sets=compatible_sets,
            recommendations=recommendations,
            overall_compatibility=overall_compatibility
        )
    
    async def _extract_component_frameworks(self, component: Any, language: str) -> List[str]:
        """Extract framework information from component."""
        
        frameworks = []
        
        # Extract from component name and description
        component_text = ""
        if hasattr(component, 'name'):
            component_text += component.name.lower() + " "
        if hasattr(component, 'description'):
            component_text += (component.description or "").lower() + " "
        if hasattr(component, 'repository_url'):
            component_text += (component.repository_url or "").lower() + " "
        
        # Check against known frameworks
        lang_ecosystems = self.framework_ecosystems.get(language.lower(), {})
        for category, framework_list in lang_ecosystems.items():
            for framework in framework_list:
                if framework in component_text:
                    frameworks.append(framework)
        
        # Additional framework detection from topics (for RepositoryResult)
        if hasattr(component, 'topics'):
            for topic in component.topics:
                topic_lower = topic.lower()
                for category, framework_list in lang_ecosystems.items():
                    if topic_lower in framework_list:
                        frameworks.append(topic_lower)
        
        return list(set(frameworks))  # Remove duplicates
    
    def _extract_dependencies(self, component: Any) -> List[str]:
        """Extract dependencies from component."""
        
        dependencies = []
        
        # For PackageResult, use dependencies list
        if hasattr(component, 'dependencies') and component.dependencies:
            dependencies.extend(component.dependencies)
        
        # For other types, extract from description or other fields
        if hasattr(component, 'description') and component.description:
            # Simple dependency extraction from description
            desc_lower = component.description.lower()
            common_deps = ['redis', 'postgresql', 'mysql', 'mongodb', 'elasticsearch', 'kafka']
            for dep in common_deps:
                if dep in desc_lower:
                    dependencies.append(dep)
        
        return dependencies
    
    def _identify_conflicts(self, component_frameworks: Dict[str, Dict], language: str) -> List[FrameworkConflict]:
        """Identify conflicts between components."""
        
        conflicts = []
        
        # Get known conflicts for the language
        lang_conflicts = self.known_conflicts.get(language.lower(), [])
        
        # Check each pair of components
        component_ids = list(component_frameworks.keys())
        for i, comp1_id in enumerate(component_ids):
            for comp2_id in component_ids[i+1:]:
                comp1_frameworks = set(component_frameworks[comp1_id]['frameworks'])
                comp2_frameworks = set(component_frameworks[comp2_id]['frameworks'])
                
                # Check for known conflicts
                for conflict_def in lang_conflicts:
                    conflict_frameworks = set(conflict_def['frameworks'])
                    
                    # Check if both components have conflicting frameworks
                    comp1_conflicts = comp1_frameworks.intersection(conflict_frameworks)
                    comp2_conflicts = comp2_frameworks.intersection(conflict_frameworks)
                    
                    if comp1_conflicts and comp2_conflicts and comp1_conflicts != comp2_conflicts:
                        conflict = FrameworkConflict(
                            framework1=list(comp1_conflicts)[0],
                            framework2=list(comp2_conflicts)[0],
                            reason=conflict_def['reason'],
                            severity=conflict_def['severity'],
                            resolution_suggestions=conflict_def['resolution']
                        )
                        conflicts.append(conflict)
        
        return conflicts
    
    def _find_compatible_sets(self, component_frameworks: Dict[str, Dict], 
                            conflicts: List[FrameworkConflict]) -> List[CompatibleSet]:
        """Find sets of components that are compatible with each other."""
        
        compatible_sets = []
        
        # Create conflict graph
        conflict_pairs = set()
        for conflict in conflicts:
            if conflict.severity in [ConflictSeverity.CRITICAL, ConflictSeverity.HIGH]:
                # Find components with these frameworks
                comp1_ids = []
                comp2_ids = []
                
                for comp_id, comp_info in component_frameworks.items():
                    if conflict.framework1 in comp_info['frameworks']:
                        comp1_ids.append(comp_id)
                    if conflict.framework2 in comp_info['frameworks']:
                        comp2_ids.append(comp_id)
                
                # Add all pairs as conflicts
                for c1 in comp1_ids:
                    for c2 in comp2_ids:
                        conflict_pairs.add((c1, c2))
                        conflict_pairs.add((c2, c1))
        
        # Find compatible groups using simple clustering
        component_ids = list(component_frameworks.keys())
        visited = set()
        
        for comp_id in component_ids:
            if comp_id in visited:
                continue
            
            # Start a new compatible set
            compatible_group = [comp_id]
            visited.add(comp_id)
            
            # Add compatible components
            for other_id in component_ids:
                if other_id in visited:
                    continue
                
                # Check if compatible with all components in current group
                is_compatible = True
                for group_comp in compatible_group:
                    if (group_comp, other_id) in conflict_pairs:
                        is_compatible = False
                        break
                
                if is_compatible:
                    compatible_group.append(other_id)
                    visited.add(other_id)
            
            # Create compatible set
            if len(compatible_group) > 1:
                components = [component_frameworks[comp_id]['component'] for comp_id in compatible_group]
                all_frameworks = []
                all_dependencies = []
                
                for comp_id in compatible_group:
                    all_frameworks.extend(component_frameworks[comp_id]['frameworks'])
                    all_dependencies.extend(component_frameworks[comp_id]['dependencies'])
                
                # Calculate compatibility score
                compatibility_score = self._calculate_set_compatibility_score(compatible_group, conflicts)
                
                compatible_set = CompatibleSet(
                    components=components,
                    frameworks=list(set(all_frameworks)),
                    shared_dependencies=list(set(all_dependencies)),
                    compatibility_score=compatibility_score
                )
                compatible_sets.append(compatible_set)
        
        # Sort by compatibility score
        compatible_sets.sort(key=lambda x: x.compatibility_score, reverse=True)
        
        return compatible_sets
    
    def _calculate_set_compatibility_score(self, component_ids: List[str], 
                                         conflicts: List[FrameworkConflict]) -> float:
        """Calculate compatibility score for a set of components."""
        
        base_score = 1.0
        
        # Penalty for each conflict involving components in this set
        for conflict in conflicts:
            # This is a simplified calculation - in practice, you'd need to
            # map frameworks back to components more precisely
            penalty = 0.0
            if conflict.severity == ConflictSeverity.CRITICAL:
                penalty = 0.5
            elif conflict.severity == ConflictSeverity.HIGH:
                penalty = 0.3
            elif conflict.severity == ConflictSeverity.MEDIUM:
                penalty = 0.2
            elif conflict.severity == ConflictSeverity.LOW:
                penalty = 0.1
            
            base_score -= penalty
        
        return max(0.0, base_score)
    
    def _generate_compatibility_recommendations(self, conflicts: List[FrameworkConflict], 
                                              compatible_sets: List[CompatibleSet]) -> List[str]:
        """Generate recommendations for handling compatibility issues."""
        
        recommendations = []
        
        if not conflicts:
            recommendations.append("✅ No major compatibility conflicts detected")
        else:
            # Group conflicts by severity
            critical_conflicts = [c for c in conflicts if c.severity == ConflictSeverity.CRITICAL]
            high_conflicts = [c for c in conflicts if c.severity == ConflictSeverity.HIGH]
            
            if critical_conflicts:
                recommendations.append(f"🚨 {len(critical_conflicts)} critical conflicts require immediate attention")
                for conflict in critical_conflicts[:3]:  # Show top 3
                    recommendations.append(f"   • {conflict.framework1} vs {conflict.framework2}: {conflict.reason}")
            
            if high_conflicts:
                recommendations.append(f"⚠️ {len(high_conflicts)} high-priority conflicts need resolution")
        
        # Recommend best compatible sets
        if compatible_sets:
            best_set = compatible_sets[0]
            recommendations.append(f"🎯 Recommended compatible set: {len(best_set.components)} components with {best_set.compatibility_score:.2f} compatibility score")
            recommendations.append(f"   Frameworks: {', '.join(best_set.frameworks[:5])}")
        
        # General recommendations
        if len(conflicts) > 5:
            recommendations.append("💡 Consider using microservices architecture to isolate conflicting frameworks")
        
        if any(c.severity == ConflictSeverity.CRITICAL for c in conflicts):
            recommendations.append("💡 Focus on one primary framework per category (web, database, etc.)")
        
        return recommendations
    
    def _calculate_overall_compatibility(self, conflicts: List[FrameworkConflict], 
                                       total_components: int) -> float:
        """Calculate overall compatibility score."""
        
        if total_components == 0:
            return 1.0
        
        base_score = 1.0
        
        # Penalty based on conflict severity and count
        for conflict in conflicts:
            if conflict.severity == ConflictSeverity.CRITICAL:
                base_score -= 0.3
            elif conflict.severity == ConflictSeverity.HIGH:
                base_score -= 0.2
            elif conflict.severity == ConflictSeverity.MEDIUM:
                base_score -= 0.1
            elif conflict.severity == ConflictSeverity.LOW:
                base_score -= 0.05
        
        return max(0.0, base_score)
    
    def _load_compatibility_database(self) -> Dict[str, Any]:
        """Load compatibility database from configuration."""
        
        # This would typically load from a JSON file or database
        # For now, return the in-memory structure
        return {
            'version': '1.0',
            'last_updated': '2024-01-01',
            'frameworks': self.framework_ecosystems,
            'conflicts': self.known_conflicts
        }


# Example usage
async def main():
    from ..search.tier1_packages import PackageResult
    from datetime import datetime
    
    checker = FrameworkCompatibilityChecker()
    
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
            name="django",
            repository_url="https://github.com/django/django",
            description="Django web framework",
            downloads=2000000,
            stars=60000,
            last_updated=datetime.now(),
            license="BSD",
            quality_score=0.95,
            language="python",
            package_manager="pypi",
            version="4.2.0",
            dependencies_count=3
        )
    ]
    
    print("Analyzing framework compatibility...")
    compatibility_matrix = await checker.analyze_component_compatibility(test_components, "python")
    
    print(f"\nCompatibility Analysis Results:")
    print(f"  Overall compatibility: {compatibility_matrix.overall_compatibility:.2f}")
    print(f"  Conflicts found: {len(compatibility_matrix.conflicts)}")
    print(f"  Compatible sets: {len(compatibility_matrix.compatible_sets)}")
    
    if compatibility_matrix.conflicts:
        print(f"\nConflicts:")
        for conflict in compatibility_matrix.conflicts:
            print(f"  {conflict.framework1} vs {conflict.framework2} ({conflict.severity})")
            print(f"    Reason: {conflict.reason}")
    
    print(f"\nRecommendations:")
    for rec in compatibility_matrix.recommendations:
        print(f"  {rec}")


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())