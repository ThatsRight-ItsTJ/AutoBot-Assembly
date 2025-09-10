#!/usr/bin/env python3
"""
Framework Compatibility Checker with Tree-sitter Integration

Ensures discovered components can work together by analyzing framework dependencies,
version constraints, and potential conflicts using enhanced Tree-sitter structural analysis
via UniversalCodeAnalyzer for more accurate signature and import validation.
"""

import logging
import json
import os
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# Import UniversalCodeAnalyzer for Tree-sitter integration
try:
    from src.analysis.universal_code_analyzer import UniversalCodeAnalyzer
    UNIVERSAL_ANALYZER_AVAILABLE = True
except ImportError:
    UNIVERSAL_ANALYZER_AVAILABLE = False
    UniversalCodeAnalyzer = None


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
    """Analyze compatibility between discovered components with Tree-sitter structural validation."""
    
    def __init__(self, enable_tree_sitter: bool = True):
        """Initialize the compatibility checker."""
        
        # Initialize Tree-sitter analyzer if enabled and available
        self.enable_tree_sitter = enable_tree_sitter and UNIVERSAL_ANALYZER_AVAILABLE
        self.tree_sitter_analyzer = None
        if self.enable_tree_sitter:
            try:
                self.tree_sitter_analyzer = UniversalCodeAnalyzer()
                logging.info("UniversalCodeAnalyzer initialized for Tree-sitter structural validation")
            except Exception as e:
                logging.warning(f"Failed to initialize UniversalCodeAnalyzer: {e}")
                self.tree_sitter_analyzer = None
                self.enable_tree_sitter = False
        self.framework_ecosystems = {
            'python': {
                'web_frameworks': ['django', 'flask', 'fastapi', 'tornado', 'pyramid', 'bottle'],
                'data_science': ['pandas', 'numpy', 'scipy', 'scikit-learn', 'tensorflow', 'pytorch'],
                'databases': ['sqlalchemy', 'django-orm', 'peewee', 'tortoise-orm'],
                'testing': ['pytest', 'unittest', 'nose2', 'doctest'],
                'async': ['asyncio', 'aiohttp', 'uvloop', 'trio'],
                'web_scraping': ['beautifulsoup4', 'scrapy', 'selenium', 'requests'],
            },
            'javascript': {
                'frontend_frameworks': ['react', 'vue', 'angular', 'svelte'],
                'backend_frameworks': ['express', 'koa', 'nestjs', 'fastify'],
                'build_tools': ['webpack', 'rollup', 'parcel', 'vite'],
                'testing': ['jest', 'mocha', 'cypress', 'playwright'],
            },
            'java': {
                'frameworks': ['spring-boot', 'dropwizard', 'quarkus', 'micronaut'],
                'build_tools': ['maven', 'gradle'],
                'testing': ['junit', 'testng', 'mockito'],
            }
        }
        
        self.known_conflicts = {
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
    
    async def analyze_component_compatibility(self, components: List[Any], language: str,
                                           source_files: Optional[List[str]] = None) -> CompatibilityMatrix:
        """
        Analyze compatibility between discovered components with enhanced Tree-sitter validation.
        
        Args:
            components: List of discovered components (PackageResult, RepositoryResult, DiscoveredRepository)
            language: Target programming language
            source_files: Optional list of source files for Tree-sitter structural validation
            
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
        
        # Enhance with Tree-sitter structural analysis if source files provided
        if source_files and self.enable_tree_sitter:
            await self._enhance_with_structural_analysis(component_frameworks, source_files, language)
        
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
    
    async def _enhance_with_structural_analysis(self, component_frameworks: Dict[str, Dict],
                                              source_files: List[str], language: str):
        """
        Enhance component analysis with Tree-sitter structural validation.
        
        Args:
            component_frameworks: Dictionary of component framework information
            source_files: List of source files to analyze
            language: Target programming language
        """
        if not self.tree_sitter_analyzer:
            return
        
        try:
            logging.info("Performing Tree-sitter structural analysis on source files")
            
            # Analyze source files for structural patterns
            structural_patterns = await self._analyze_source_files_patterns(source_files, language)
            
            # Enhance component framework detection with structural insights
            for comp_id, comp_info in component_frameworks.items():
                component = comp_info['component']
                
                # Extract structural insights from the component
                if hasattr(component, 'repository_url') and component.repository_url:
                    # Check if structural patterns match this component
                    for pattern_name, pattern_data in structural_patterns.items():
                        if self._component_matches_patterns(component, pattern_data):
                            # Add detected frameworks based on structural patterns
                            for framework in pattern_data.get('detected_frameworks', []):
                                if framework not in comp_info['frameworks']:
                                    comp_info['frameworks'].append(framework)
                                    logging.info(f"Detected {framework} in {comp_id} via structural analysis")
                            
                            # Add structural dependencies
                            for dep in pattern_data.get('structural_dependencies', []):
                                if dep not in comp_info['dependencies']:
                                    comp_info['dependencies'].append(dep)
            
            logging.info("Enhanced component analysis with Tree-sitter structural data")
            
        except Exception as e:
            logging.warning(f"Failed to enhance with structural analysis: {e}")
    
    async def _analyze_source_files_patterns(self, source_files: List[str], language: str) -> Dict[str, Any]:
        """
        Analyze source files for structural patterns using Tree-sitter.
        
        Args:
            source_files: List of source file paths
            language: Target programming language
            
        Returns:
            Dictionary of detected structural patterns
        """
        patterns = {}
        
        try:
            for file_path in source_files:
                if not os.path.exists(file_path):
                    continue
                
                try:
                    # Analyze file with Tree-sitter
                    file_result = self.tree_sitter_analyzer.analyze_file(file_path, language)
                    
                    if file_result and file_result.get('success'):
                        # Extract structural patterns
                        structure = file_result.get('structure', {})
                        metrics = file_result.get('metrics', {})
                        
                        # Detect frameworks based on imports and dependencies
                        detected_frameworks = self._detect_frameworks_from_structure(structure, language)
                        
                        # Extract structural dependencies
                        structural_dependencies = structure.get('dependencies', [])
                        
                        # Create pattern entry
                        pattern_key = f"file_{len(patterns)}"
                        patterns[pattern_key] = {
                            'file_path': file_path,
                            'detected_frameworks': detected_frameworks,
                            'structural_dependencies': structural_dependencies,
                            'complexity_score': float(metrics.get('complexity_score', 0.0)),
                            'has_tests': structure.get('has_tests', False),
                            'has_docs': structure.get('has_docs', False)
                        }
                        
                except Exception as e:
                    logging.warning(f"Error analyzing {file_path}: {e}")
                    continue
            
            # Group similar patterns
            patterns = self._group_similar_patterns(patterns)
            
        except Exception as e:
            logging.error(f"Error in structural pattern analysis: {e}")
        
        return patterns
    
    def _detect_frameworks_from_structure(self, structure: Dict[str, Any], language: str) -> List[str]:
        """
        Detect frameworks from structural analysis results.
        
        Args:
            structure: Structural analysis results
            language: Target programming language
            
        Returns:
            List of detected frameworks
        """
        detected_frameworks = []
        imports = structure.get('imports', [])
        dependencies = structure.get('dependencies', [])
        
        # Combine imports and dependencies for analysis
        all_references = imports + dependencies
        
        # Language-specific framework detection patterns
        framework_patterns = {
            'python': {
                'django': ['django', 'django.db', 'django.http', 'django.views'],
                'flask': ['flask', 'flask.request', 'flask.Blueprint'],
                'fastapi': ['fastapi', 'fastapi.HTTPException', 'fastapi.Depends'],
                'sqlalchemy': ['sqlalchemy', 'declarative_base', 'sessionmaker'],
                'pydantic': ['pydantic', 'BaseModel', 'Field'],
                'pytest': ['pytest', 'fixture', 'mark']
            },
            'javascript': {
                'react': ['react', 'useState', 'useEffect', 'jsx'],
                'express': ['express', 'app.get', 'app.post', 'req', 'res'],
                'vue': ['vue', 'Vue.component', 'v-', '@'],
                'angular': ['@angular', 'ngOnInit', 'HttpClient'],
                'jest': ['describe', 'it', 'expect', 'jest']
            },
            'java': {
                'spring': ['@SpringBootApplication', '@RestController', '@Autowired'],
                'hibernate': ['@Entity', '@Table', '@Column', 'SessionFactory'],
                'junit': ['@Test', '@BeforeEach', '@AfterEach', 'assertEquals']
            }
        }
        
        # Check for framework patterns
        lang_patterns = framework_patterns.get(language.lower(), {})
        for framework, patterns in lang_patterns.items():
            if any(pattern in ' '.join(all_references).lower() for pattern in patterns):
                detected_frameworks.append(framework)
        
        return detected_frameworks
    
    def _group_similar_patterns(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """
        Group similar structural patterns together.
        
        Args:
            patterns: Dictionary of structural patterns
            
        Returns:
            Grouped patterns
        """
        if not patterns:
            return {}
        
        # Simple grouping by detected frameworks
        grouped_patterns = {}
        
        for pattern_id, pattern_data in patterns.items():
            frameworks = tuple(sorted(pattern_data.get('detected_frameworks', [])))
            
            if frameworks:
                if frameworks not in grouped_patterns:
                    grouped_patterns[frameworks] = {
                        'detected_frameworks': list(frameworks),
                        'file_count': 0,
                        'average_complexity': 0.0,
                        'has_tests': False,
                        'has_docs': False,
                        'files': []
                    }
                
                grouped_patterns[frameworks]['file_count'] += 1
                grouped_patterns[frameworks]['files'].append(pattern_data)
                
                # Update average complexity
                complexity = pattern_data.get('complexity_score', 0.0)
                current_avg = grouped_patterns[frameworks]['average_complexity']
                count = grouped_patterns[frameworks]['file_count']
                grouped_patterns[frameworks]['average_complexity'] = (current_avg * (count - 1) + complexity) / count
                
                # Update test and doc flags
                grouped_patterns[frameworks]['has_tests'] = grouped_patterns[frameworks]['has_tests'] or pattern_data.get('has_tests', False)
                grouped_patterns[frameworks]['has_docs'] = grouped_patterns[frameworks]['has_docs'] or pattern_data.get('has_docs', False)
        
        return grouped_patterns
    
    def _component_matches_patterns(self, component: Any, pattern_data: Dict[str, Any]) -> bool:
        """
        Check if a component matches given structural patterns.
        
        Args:
            component: Component to check
            pattern_data: Structural pattern data
            
        Returns:
            True if component matches patterns
        """
        try:
            # Check if component name or description contains detected frameworks
            component_text = ""
            if hasattr(component, 'name'):
                component_text += component.name.lower() + " "
            if hasattr(component, 'description'):
                component_text += (component.description or "").lower() + " "
            
            detected_frameworks = pattern_data.get('detected_frameworks', [])
            for framework in detected_frameworks:
                if framework in component_text:
                    return True
            
            return False
            
        except Exception as e:
            logging.warning(f"Error checking component pattern match: {e}")
            return False
    
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
    
    def get_tree_sitter_status(self) -> Dict[str, Any]:
        """Get status of Tree-sitter integration."""
        return {
            'enabled': self.enable_tree_sitter,
            'analyzer_available': self.tree_sitter_analyzer is not None,
            'supported_languages': self.tree_sitter_analyzer.get_supported_languages() if self.tree_sitter_analyzer else [],
            'cache_info': self.tree_sitter_analyzer.get_cache_info() if self.tree_sitter_analyzer else None
        }
    
    async def validate_function_signatures(self, source_files: List[str], language: str) -> Dict[str, Any]:
        """
        Validate function signatures using Tree-sitter structural analysis.
        
        Args:
            source_files: List of source files to validate
            language: Target programming language
            
        Returns:
            Dictionary with validation results
        """
        if not self.enable_tree_sitter or not self.tree_sitter_analyzer:
            return {'enabled': False, 'results': []}
        
        validation_results = {
            'enabled': True,
            'total_files': len(source_files),
            'validated_files': 0,
            'signature_issues': [],
            'import_issues': [],
            'structural_warnings': []
        }
        
        try:
            for file_path in source_files:
                if not os.path.exists(file_path):
                    continue
                
                try:
                    file_result = self.tree_sitter_analyzer.analyze_file(file_path, language)
                    
                    if file_result and file_result.get('success'):
                        validation_results['validated_files'] += 1
                        
                        # Extract signature validation issues
                        signature_issues = self._extract_signature_issues(file_result)
                        import_issues = self._extract_import_issues(file_result)
                        structural_warnings = self._extract_structural_warnings(file_result)
                        
                        validation_results['signature_issues'].extend(signature_issues)
                        validation_results['import_issues'].extend(import_issues)
                        validation_results['structural_warnings'].extend(structural_warnings)
                        
                except Exception as e:
                    logging.warning(f"Error validating {file_path}: {e}")
                    continue
            
        except Exception as e:
            logging.error(f"Error in signature validation: {e}")
        
        return validation_results
    
    def _extract_signature_issues(self, file_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract function signature validation issues."""
        issues = []
        
        try:
            structure = file_result.get('structure', {})
            metrics = file_result.get('metrics', {})
            
            # Check for extremely high complexity
            complexity = float(metrics.get('complexity_score', 0.0))
            if complexity > 0.8:
                issues.append({
                    'type': 'high_complexity',
                    'severity': 'high',
                    'message': f'High complexity score: {complexity:.2f}',
                    'file': file_result.get('file_path', 'unknown')
                })
            
            # Check for extremely large functions (would need Tree-sitter enhancement)
            functions_count = int(metrics.get('functions_count', 0))
            if functions_count > 50:
                issues.append({
                    'type': 'too_many_functions',
                    'severity': 'medium',
                    'message': f'Many functions detected: {functions_count}',
                    'file': file_result.get('file_path', 'unknown')
                })
            
        except Exception as e:
            logging.warning(f"Error extracting signature issues: {e}")
        
        return issues
    
    def _extract_import_issues(self, file_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract import validation issues."""
        issues = []
        
        try:
            structure = file_result.get('structure', {})
            imports = structure.get('imports', [])
            
            # Check for potential circular imports (simplified detection)
            if len(imports) > 20:
                issues.append({
                    'type': 'too_many_imports',
                    'severity': 'medium',
                    'message': f'Many imports detected: {len(imports)}',
                    'file': file_result.get('file_path', 'unknown')
                })
            
            # Check for relative imports in main modules
            relative_imports = [imp for imp in imports if imp.startswith('.')]
            if len(relative_imports) > 5:
                issues.append({
                    'type': 'many_relative_imports',
                    'severity': 'low',
                    'message': f'Many relative imports: {len(relative_imports)}',
                    'file': file_result.get('file_path', 'unknown')
                })
            
        except Exception as e:
            logging.warning(f"Error extracting import issues: {e}")
        
        return issues
    
    def _extract_structural_warnings(self, file_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract structural warnings from analysis."""
        warnings = []
        
        try:
            structure = file_result.get('structure', {})
            metrics = file_result.get('metrics', {})
            
            # Check for lack of tests
            if not structure.get('has_tests', False):
                warnings.append({
                    'type': 'missing_tests',
                    'severity': 'medium',
                    'message': 'No tests detected in file',
                    'file': file_result.get('file_path', 'unknown')
                })
            
            # Check for lack of documentation
            if not structure.get('has_docs', False):
                warnings.append({
                    'type': 'missing_docs',
                    'severity': 'low',
                    'message': 'No documentation detected in file',
                    'file': file_result.get('file_path', 'unknown')
                })
            
            # Check for very large files
            file_size = file_result.get('file_size', 0)
            if file_size > 5000:  # 5KB threshold
                warnings.append({
                    'type': 'large_file',
                    'severity': 'low',
                    'message': f'Large file detected: {file_size} bytes',
                    'file': file_result.get('file_path', 'unknown')
                })
            
        except Exception as e:
            logging.warning(f"Error extracting structural warnings: {e}")
        
        return warnings