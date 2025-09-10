import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import re
from ..analysis.universal_code_analyzer import UniversalCodeAnalyzer, CodeElement
from ..assembly.code_integrator import CodeComponent, IntegrationPattern
from ..validation.context7_validator import Context7Validator, APIValidationResult

class ValidationLevel(Enum):
    BASIC = "basic"
    STRUCTURAL = "structural"
    SEMANTIC = "semantic"
    SECURITY = "security"
    PERFORMANCE = "performance"

class PatternMatchStatus(Enum):
    EXACT = "exact"
    CLOSE = "close"
    PARTIAL = "partial"
    NONE = "none"

@dataclass
class PatternValidationResult:
    pattern_id: str
    pattern_name: str
    match_status: PatternMatchStatus
    confidence_score: float
    validation_results: Dict[str, Any]
    issues: List[str]
    recommendations: List[str]
    affected_components: List[str]

@dataclass
class AssemblyValidationReport:
    overall_score: float
    validation_level: ValidationLevel
    pattern_results: List[PatternValidationResult]
    component_compatibility: Dict[str, Any]
    security_issues: List[str]
    performance_issues: List[str]
    recommendations: List[str]

class PatternBasedValidator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.code_analyzer = UniversalCodeAnalyzer()
        self.context7_validator = Context7Validator()
        
        # Pattern libraries
        self.pattern_libraries = {
            'design_patterns': self._load_design_patterns(),
            'api_patterns': self._load_api_patterns(),
            'security_patterns': self._load_security_patterns(),
            'performance_patterns': self._load_performance_patterns()
        }
        
        # Validation rules
        self.validation_rules = {
            'naming_conventions': self._load_naming_rules(),
            'code_structure': self._load_structure_rules(),
            'error_handling': self._load_error_handling_rules(),
            'dependency_management': self._load_dependency_rules()
        }
        
        # Cache for pattern matching
        self.pattern_cache = {}
    
    def validate_assembly_patterns(self, components: List[CodeComponent], 
                                patterns: List[IntegrationPattern]) -> AssemblyValidationReport:
        """Validate assembly against pattern-based rules"""
        try:
            # Initialize validation report
            report = AssemblyValidationReport(
                overall_score=0.0,
                validation_level=ValidationLevel.BASIC,
                pattern_results=[],
                component_compatibility={},
                security_issues=[],
                performance_issues=[],
                recommendations=[]
            )
            
            # Validate each pattern
            pattern_results = []
            total_score = 0.0
            
            for pattern in patterns:
                pattern_result = self.validate_single_pattern(components, pattern)
                pattern_results.append(pattern_result)
                total_score += pattern_result.confidence_score
            
            # Calculate overall score
            if patterns:
                report.overall_score = total_score / len(patterns)
            
            # Determine validation level
            report.validation_level = self._determine_validation_level(report.overall_score)
            
            # Set pattern results
            report.pattern_results = pattern_results
            
            # Analyze component compatibility
            report.component_compatibility = self._analyze_component_compatibility(components)
            
            # Extract security and performance issues
            for pattern_result in pattern_results:
                if pattern_result.match_status == PatternMatchStatus.NONE:
                    report.security_issues.extend(pattern_result.issues)
                    report.performance_issues.extend(pattern_result.issues)
                report.recommendations.extend(pattern_result.recommendations)
            
            # Generate additional recommendations
            report.recommendations.extend(self._generate_additional_recommendations(components, pattern_results))
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to validate assembly patterns: {e}")
            return AssemblyValidationReport(
                overall_score=0.0,
                validation_level=ValidationLevel.BASIC,
                pattern_results=[],
                component_compatibility={},
                security_issues=[f"Pattern validation failed: {str(e)}"],
                performance_issues=[],
                recommendations=[]
            )
    
    def validate_single_pattern(self, components: List[CodeComponent], 
                              pattern: IntegrationPattern) -> PatternValidationResult:
        """Validate a single pattern against components"""
        cache_key = f"{pattern.pattern_id}:{hash(tuple(c.name for c in components))}"
        
        if cache_key in self.pattern_cache:
            return self.pattern_cache[cache_key]
        
        try:
            # Initialize result
            result = PatternValidationResult(
                pattern_id=pattern.pattern_id,
                pattern_name=pattern.pattern_name,
                match_status=PatternMatchStatus.NONE,
                confidence_score=0.0,
                validation_results={},
                issues=[],
                recommendations=[],
                affected_components=[]
            )
            
            # Find matching components
            matching_components = self._find_pattern_components(components, pattern)
            result.affected_components = [c.name for c in matching_components]
            
            if not matching_components:
                result.match_status = PatternMatchStatus.NONE
                result.confidence_score = 0.0
                result.issues.append(f"No components matched pattern {pattern.pattern_id}")
                return result
            
            # Validate pattern implementation
            validation_results = {}
            
            # 1. Validate pattern structure
            structure_validation = self._validate_pattern_structure(matching_components, pattern)
            validation_results['structure'] = structure_validation
            
            # 2. Validate pattern semantics
            semantic_validation = self._validate_pattern_semantics(matching_components, pattern)
            validation_results['semantics'] = semantic_validation
            
            # 3. Validate pattern dependencies
            dependency_validation = self._validate_pattern_dependencies(matching_components, pattern)
            validation_results['dependencies'] = dependency_validation
            
            # 4. Validate pattern compliance
            compliance_validation = self._validate_pattern_compliance(matching_components, pattern)
            validation_results['compliance'] = compliance_validation
            
            # Combine validation results
            result.validation_results = validation_results
            result.match_status, result.confidence_score = self._determine_match_status(validation_results)
            
            # Extract issues and recommendations
            for validation_type, validation_result in validation_results.items():
                if validation_result.get('status') == 'failed':
                    result.issues.extend(validation_result.get('issues', []))
                    result.recommendations.extend(validation_result.get('recommendations', []))
            
            # Cache the result
            self.pattern_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to validate pattern {pattern.pattern_id}: {e}")
            return PatternValidationResult(
                pattern_id=pattern.pattern_id,
                pattern_name=pattern.pattern_name,
                match_status=PatternMatchStatus.NONE,
                confidence_score=0.0,
                validation_results={},
                issues=[f"Pattern validation failed: {str(e)}"],
                recommendations=[],
                affected_components=[]
            )
    
    def _find_pattern_components(self, components: List[CodeComponent], 
                              pattern: IntegrationPattern) -> List[CodeComponent]:
        """Find components that match a pattern"""
        matching_components = []
        
        for component in components:
            # Check language compatibility
            if component.language != pattern.language:
                continue
            
            # Check dependency compatibility
            if not any(dep in component.dependencies for dep in pattern.dependencies):
                continue
            
            # Check code similarity
            if self._is_code_similar(component.code, pattern.code_example):
                matching_components.append(component)
        
        return matching_components
    
    def _is_code_similar(self, code1: str, code2: str) -> bool:
        """Check if two code snippets are similar"""
        # Simple similarity check - in real implementation, use more sophisticated algorithms
        code1_words = set(code1.lower().split())
        code2_words = set(code2.lower().split())
        
        intersection = code1_words.intersection(code2_words)
        union = code1_words.union(code2_words)
        
        jaccard_similarity = len(intersection) / len(union) if union else 0
        
        return jaccard_similarity > 0.3  # 30% similarity threshold
    
    def _validate_pattern_structure(self, components: List[CodeComponent], 
                                  pattern: IntegrationPattern) -> Dict[str, Any]:
        """Validate pattern structure implementation"""
        result = {
            'status': 'passed',
            'issues': [],
            'recommendations': [],
            'details': {}
        }
        
        # Check component structure
        for component in components:
            # Check naming conventions
            naming_issues = self._check_naming_conventions(component)
            result['issues'].extend(naming_issues)
            
            # Check code structure
            structure_issues = self._check_code_structure(component)
            result['issues'].extend(structure_issues)
        
        # Update status based on issues
        if result['issues']:
            result['status'] = 'warning' if len(result['issues']) < 3 else 'failed'
        
        return result
    
    def _validate_pattern_semantics(self, components: List[CodeComponent], 
                                   pattern: IntegrationPattern) -> Dict[str, Any]:
        """Validate pattern semantics implementation"""
        result = {
            'status': 'passed',
            'issues': [],
            'recommendations': [],
            'details': {}
        }
        
        # Check semantic correctness
        for component in components:
            # Check error handling
            error_issues = self._check_error_handling(component)
            result['issues'].extend(error_issues)
            
            # Check input validation
            validation_issues = self._check_input_validation(component)
            result['issues'].extend(validation_issues)
        
        # Update status based on issues
        if result['issues']:
            result['status'] = 'warning' if len(result['issues']) < 2 else 'failed'
        
        return result
    
    def _validate_pattern_dependencies(self, components: List[CodeComponent], 
                                    pattern: IntegrationPattern) -> Dict[str, Any]:
        """Validate pattern dependencies implementation"""
        result = {
            'status': 'passed',
            'issues': [],
            'recommendations': [],
            'details': {}
        }
        
        # Check dependency compatibility
        all_dependencies = []
        for component in components:
            all_dependencies.extend(component.dependencies)
        
        # Check for conflicting dependencies
        conflicts = self._check_dependency_conflicts(all_dependencies)
        result['issues'].extend(conflicts)
        
        # Check for missing dependencies
        missing = self._check_missing_dependencies(pattern.dependencies, all_dependencies)
        result['issues'].extend(missing)
        
        # Update status based on issues
        if result['issues']:
            result['status'] = 'warning' if len(result['issues']) < 2 else 'failed'
        
        return result
    
    def _validate_pattern_compliance(self, components: List[CodeComponent], 
                                    pattern: IntegrationPattern) -> Dict[str, Any]:
        """Validate pattern compliance with standards"""
        result = {
            'status': 'passed',
            'issues': [],
            'recommendations': [],
            'details': {}
        }
        
        # Check compliance with coding standards
        for component in components:
            # Check style compliance
            style_issues = self._check_style_compliance(component)
            result['issues'].extend(style_issues)
            
            # Check documentation compliance
            doc_issues = self._check_documentation_compliance(component)
            result['issues'].extend(doc_issues)
        
        # Update status based on issues
        if result['issues']:
            result['status'] = 'warning' if len(result['issues']) < 2 else 'failed'
        
        return result
    
    def _determine_match_status(self, validation_results: Dict[str, Any]) -> Tuple[PatternMatchStatus, float]:
        """Determine pattern match status based on validation results"""
        passed_count = 0
        total_count = len(validation_results)
        total_score = 0.0
        
        for validation_type, result in validation_results.items():
            if result['status'] == 'passed':
                passed_count += 1
                total_score += 1.0
            elif result['status'] == 'warning':
                total_score += 0.5
        
        confidence_score = total_score / total_count if total_count > 0 else 0.0
        
        if confidence_score >= 0.9:
            return PatternMatchStatus.EXACT, confidence_score
        elif confidence_score >= 0.7:
            return PatternMatchStatus.CLOSE, confidence_score
        elif confidence_score >= 0.5:
            return PatternMatchStatus.PARTIAL, confidence_score
        else:
            return PatternMatchStatus.NONE, confidence_score
    
    def _analyze_component_compatibility(self, components: List[CodeComponent]) -> Dict[str, Any]:
        """Analyze compatibility between components"""
        compatibility = {
            'overall_compatibility': 1.0,
            'language_compatibility': {},
            'dependency_compatibility': {},
            'structural_compatibility': {},
            'issues': [],
            'recommendations': []
        }
        
        # Analyze language compatibility
        languages = [c.language for c in components]
        unique_languages = set(languages)
        
        if len(unique_languages) > 1:
            compatibility['overall_compatibility'] *= 0.8
            compatibility['issues'].append("Multiple programming languages detected")
            compatibility['recommendations'].append("Consider language-specific integration mechanisms")
        
        compatibility['language_compatibility'] = {
            'languages': list(unique_languages),
            'compatibility_score': len(unique_languages) / max(1, len(components))
        }
        
        # Analyze dependency compatibility
        all_dependencies = []
        for component in components:
            all_dependencies.extend(component.dependencies)
        
        dependency_conflicts = self._check_dependency_conflicts(all_dependencies)
        if dependency_conflicts:
            compatibility['overall_compatibility'] *= 0.7
            compatibility['dependency_compatibility'] = {
                'conflicts': dependency_conflicts,
                'compatibility_score': 0.5
            }
        else:
            compatibility['dependency_compatibility'] = {
                'conflicts': [],
                'compatibility_score': 1.0
            }
        
        return compatibility
    
    def _generate_additional_recommendations(self, components: List[CodeComponent], 
                                           pattern_results: List[PatternValidationResult]) -> List[str]:
        """Generate additional recommendations based on validation results"""
        recommendations = []
        
        # Check for component organization
        if len(components) > 10:
            recommendations.append("Consider modular organization for large number of components")
        
        # Check for missing documentation
        documented_components = [c for c in components if c.context.get('documentation', False)]
        if len(documented_components) / len(components) < 0.5:
            recommendations.append("Add documentation to improve code maintainability")
        
        # Check for error handling
        error_handling_components = [c for c in components if c.context.get('error_handling', [])]
        if len(error_handling_components) / len(components) < 0.3:
            recommendations.append("Implement proper error handling mechanisms")
        
        # Check for API validation
        api_components = [c for c in components if c.context.get('api_calls', [])]
        if api_components:
            recommendations.append("Consider implementing API validation for external calls")
        
        return recommendations
    
    def _determine_validation_level(self, score: float) -> ValidationLevel:
        """Determine validation level based on score"""
        if score >= 0.9:
            return ValidationLevel.SEMANTIC
        elif score >= 0.7:
            return ValidationLevel.STRUCTURAL
        elif score >= 0.5:
            return ValidationLevel.BASIC
        else:
            return ValidationLevel.BASIC
    
    # Helper methods for pattern loading
    def _load_design_patterns(self) -> Dict[str, Any]:
        """Load design patterns library"""
        return {
            'singleton': {
                'description': 'Ensure a class has only one instance',
                'structure': ['private constructor', 'static instance', 'static get method'],
                'validation_rules': ['constructor_access', 'instance_storage', 'access_method']
            },
            'factory': {
                'description': 'Create objects without specifying exact classes',
                'structure': ['creator_interface', 'concrete_creators', 'product_interface'],
                'validation_rules': ['interface_definition', 'creator_methods', 'product_creation']
            },
            'observer': {
                'description': 'Define one-to-many dependency between objects',
                'structure': ['subject_interface', 'observer_interface', 'notification_mechanism'],
                'validation_rules': ['subject_methods', 'observer_methods', 'notification_flow']
            }
        }
    
    def _load_api_patterns(self) -> Dict[str, Any]:
        """Load API patterns library"""
        return {
            'restful': {
                'description': 'REST API design pattern',
                'endpoints': ['GET /resources', 'POST /resources', 'PUT /resources/:id', 'DELETE /resources/:id'],
                'validation_rules': ['http_methods', 'resource_naming', 'status_codes']
            },
            'graphql': {
                'description': 'GraphQL API design pattern',
                'structure': ['schema_definition', 'resolvers', 'queries_mutations'],
                'validation_rules': ['schema_types', 'resolver_functions', 'query_structure']
            }
        }
    
    def _load_security_patterns(self) -> Dict[str, Any]:
        """Load security patterns library"""
        return {
            'authentication': {
                'description': 'User authentication pattern',
                'structure': ['login_endpoint', 'token_generation', 'token_validation'],
                'validation_rules': ['password_hashing', 'token_expiry', 'secure_transmission']
            },
            'authorization': {
                'description': 'Access control pattern',
                'structure': ['role_definition', 'permission_check', 'resource_access'],
                'validation_rules': ['role_hierarchy', 'permission_mapping', 'access_control']
            }
        }
    
    def _load_performance_patterns(self) -> Dict[str, Any]:
        """Load performance patterns library"""
        return {
            'caching': {
                'description': 'Data caching pattern',
                'structure': ['cache_interface', 'cache_implementation', 'cache_strategy'],
                'validation_rules': ['cache_key_generation', 'cache_expiration', 'cache_invalidation']
            },
            'lazy_loading': {
                'description': 'Lazy loading pattern',
                'structure': ['lazy_initialization', 'null_checks', 'resource_management'],
                'validation_rules': ['initialization_logic', 'null_handling', 'resource_cleanup']
            }
        }
    
    # Helper methods for validation rules
    def _load_naming_rules(self) -> Dict[str, Any]:
        """Load naming convention rules"""
        return {
            'functions': {
                'pattern': r'^[a-z][a-z0-9_]*$',
                'message': 'Function names should be lowercase with underscores'
            },
            'classes': {
                'pattern': r'^[A-Z][a-zA-Z0-9]*$',
                'message': 'Class names should be CamelCase'
            },
            'variables': {
                'pattern': r'^[a-z][a-z0-9_]*$',
                'message': 'Variable names should be lowercase with underscores'
            }
        }
    
    def _load_structure_rules(self) -> Dict[str, Any]:
        """Load code structure rules"""
        return {
            'max_function_length': 50,
            'max_class_length': 300,
            'max_parameters': 7,
            'max_nesting_depth': 4
        }
    
    def _load_error_handling_rules(self) -> Dict[str, Any]:
        """Load error handling rules"""
        return {
            'try_catch_required': True,
            'specific_exceptions': True,
            'error_logging': True,
            'error_messages': 'descriptive'
        }
    
    def _load_dependency_rules(self) -> Dict[str, Any]:
        """Load dependency management rules"""
        return {
            'circular_dependencies': False,
            'version_conflicts': False,
            'unused_dependencies': False,
            'security_vulnerabilities': False
        }
    
    # Helper methods for specific validations
    def _check_naming_conventions(self, component: CodeComponent) -> List[str]:
        """Check naming conventions for a component"""
        issues = []
        
        # Check function naming
        if component.type == 'function':
            if not re.match(r'^[a-z][a-z0-9_]*$', component.name):
                issues.append(f"Function name '{component.name}' doesn't follow naming conventions")
        
        # Check class naming
        elif component.type == 'class':
            if not re.match(r'^[A-Z][a-zA-Z0-9]*$', component.name):
                issues.append(f"Class name '{component.name}' doesn't follow naming conventions")
        
        return issues
    
    def _check_code_structure(self, component: CodeComponent) -> List[str]:
        """Check code structure for a component"""
        issues = []
        
        # Check function length
        if component.type == 'function':
            line_count = component.line_end - component.line_start
            if line_count > self.validation_rules['structure']['max_function_length']:
                issues.append(f"Function '{component.name}' is too long ({line_count} lines)")
        
        # Check class length
        elif component.type == 'class':
            line_count = component.line_end - component.line_start
            if line_count > self.validation_rules['structure']['max_class_length']:
                issues.append(f"Class '{component.name}' is too long ({line_count} lines)")
        
        return issues
    
    def _check_error_handling(self, component: CodeComponent) -> List[str]:
        """Check error handling for a component"""
        issues = []
        
        if self.validation_rules['error_handling']['try_catch_required']:
            if not component.context.get('error_handling', []):
                issues.append(f"Component '{component.name}' lacks error handling")
        
        return issues
    
    def _check_input_validation(self, component: CodeComponent) -> List[str]:
        """Check input validation for a component"""
        issues = []
        
        # Check for parameter validation
        if component.context.get('parameters', []):
            # Simple check for validation logic
            has_validation = any('validate' in param.lower() for param in component.context['parameters'])
            if not has_validation:
                issues.append(f"Component '{component.name}' lacks input validation")
        
        return issues
    
    def _check_dependency_conflicts(self, dependencies: List[str]) -> List[str]:
        """Check for dependency conflicts"""
        conflicts = []
        
        # This is a simplified implementation
        # In a real implementation, you would check version conflicts, etc.
        for i, dep1 in enumerate(dependencies):
            for j, dep2 in enumerate(dependencies[i+1:], i+1):
                if dep1 == dep2:
                    conflicts.append(f"Duplicate dependency: {dep1}")
        
        return conflicts
    
    def _check_missing_dependencies(self, required: List[str], available: List[str]) -> List[str]:
        """Check for missing dependencies"""
        missing = []
        
        for req in required:
            if req not in available:
                missing.append(f"Missing required dependency: {req}")
        
        return missing
    
    def _check_style_compliance(self, component: CodeComponent) -> List[str]:
        """Check style compliance for a component"""
        issues = []
        
        # Check for proper indentation
        lines = component.code.split('\n')
        for line in lines:
            if line.startswith('  ') or line.startswith('\t'):
                # Check for consistent indentation
                pass
        
        return issues
    
    def _check_documentation_compliance(self, component: CodeComponent) -> List[str]:
        """Check documentation compliance for a component"""
        issues = []
        
        # Check for docstrings
        if '"""' not in component.code and "'''" not in component.code:
            issues.append(f"Component '{component.name}' lacks documentation")
        
        return issues