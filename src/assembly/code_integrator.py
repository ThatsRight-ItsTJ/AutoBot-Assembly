"""
Precision Code Extraction Module

Automated code extraction and integration using Tree-sitter for enhanced assembly capabilities.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from ..analysis.universal_code_analyzer import UniversalCodeAnalyzer, CodeElement
from ..search.sourcegraph_integration import SourceGraphIntegration

@dataclass
class CodeComponent:
    name: str
    type: str  # 'function', 'class', 'module'
    code: str
    file_path: str
    language: str
    dependencies: List[str]
    imports: List[str]
    line_start: int
    line_end: int
    context: Dict[str, Any]

@dataclass
class IntegrationPattern:
    pattern_id: str
    pattern_name: str
    description: str
    code_example: str
    dependencies: List[str]
    confidence_score: float
    source_repository: str
    language: str

class PrecisionCodeExtractor:
    def __init__(self):
        self.code_analyzer = UniversalCodeAnalyzer()
        self.sourcegraph_integration = SourceGraphIntegration()
        self.logger = logging.getLogger(__name__)
        
        # Cache for extracted components
        self.component_cache = {}
        self.pattern_cache = {}
    
    def extract_function_with_context(self, repo_path: str, function_name: str, file_path: str, language: str) -> Dict[str, Any]:
        """Extract function with full context including dependencies"""
        cache_key = f"{repo_path}:{function_name}:{file_path}:{language}"
        
        if cache_key in self.component_cache:
            return self.component_cache[cache_key]
        
        try:
            # Extract function with dependencies
            extraction_result = self.code_analyzer.extract_function_with_dependencies(
                repo_path, function_name, file_path, language
            )
            
            if 'error' in extraction_result:
                return extraction_result
            
            # Find related imports and dependencies
            context = self.build_function_context(file_path, language, extraction_result)
            
            # Create code component
            component = CodeComponent(
                name=function_name,
                type='function',
                code=extraction_result['code'],
                file_path=file_path,
                language=language,
                dependencies=extraction_result['dependencies'],
                imports=extraction_result['imports'],
                line_start=extraction_result['line_start'],
                line_end=extraction_result['line_end'],
                context=context
            )
            
            result = {
                'component': component,
                'success': True,
                'context': context
            }
            
            # Cache the result
            self.component_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to extract function {function_name}: {e}")
            return {'error': str(e)}
    
    def build_function_context(self, file_path: str, language: str, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Build comprehensive context for function extraction"""
        context = {
            'local_variables': [],
            'function_calls': [],
            'class_references': [],
            'import_symbols': [],
            'api_calls': [],
            'error_handling': [],
            'control_flow': []
        }
        
        try:
            # Parse the function code to extract context
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # Use the code analyzer to extract context
            file_analysis = self.code_analyzer.parse_file_structure(file_path, language)
            
            # Extract local variables (simplified)
            context['local_variables'] = self._extract_local_variables(
                extraction_result['code'], language
            )
            
            # Extract function calls
            context['function_calls'] = self._extract_function_calls(
                extraction_result['code'], language
            )
            
            # Extract class references
            context['class_references'] = self._extract_class_references(
                extraction_result['code'], language
            )
            
            # Extract import symbols
            context['import_symbols'] = self._extract_import_symbols(
                extraction_result['code'], language
            )
            
            # Extract API calls
            context['api_calls'] = self._extract_api_calls(
                extraction_result['code'], language
            )
            
            # Extract error handling
            context['error_handling'] = self._extract_error_handling(
                extraction_result['code'], language
            )
            
            # Extract control flow
            context['control_flow'] = self._extract_control_flow(
                extraction_result['code'], language
            )
            
        except Exception as e:
            self.logger.error(f"Failed to build context: {e}")
        
        return context
    
    def _extract_local_variables(self, code: str, language: str) -> List[str]:
        """Extract local variables from code"""
        variables = []
        
        if language == 'python':
            # Look for variable assignments
            lines = code.split('\n')
            for line in lines:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    var_name = line.split('=')[0].strip()
                    if var_name and not var_name.startswith(('import', 'from', 'class', 'def', 'if', 'for', 'while', 'try', 'except')):
                        variables.append(var_name)
        
        return variables
    
    def _extract_function_calls(self, code: str, language: str) -> List[str]:
        """Extract function calls from code"""
        calls = []
        
        if language == 'python':
            # Look for function calls
            lines = code.split('\n')
            for line in lines:
                line = line.strip()
                if '(' in line and not line.startswith('#'):
                    # Extract function name before parentheses
                    parts = line.split('(')
                    if len(parts) > 1:
                        func_name = parts[0].strip()
                        if func_name and not func_name.startswith(('import', 'from', 'class', 'def', 'if', 'for', 'while', 'try', 'except')):
                            calls.append(func_name)
        
        return calls
    
    def _extract_class_references(self, code: str, language: str) -> List[str]:
        """Extract class references from code"""
        references = []
        
        if language == 'python':
            # Look for class instantiations and references
            lines = code.split('\n')
            for line in lines:
                line = line.strip()
                if '(' in line and '.' in line:
                    # Look for class.method() patterns
                    parts = line.split('.')
                    if len(parts) > 1:
                        class_name = parts[0].strip()
                        if class_name and class_name not in ['self', 'super', 'print', 'len', 'range']:
                            references.append(class_name)
        
        return references
    
    def _extract_import_symbols(self, code: str, language: str) -> List[str]:
        """Extract import symbols from code"""
        symbols = []
        
        if language == 'python':
            # Look for import statements
            lines = code.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('import ') or line.startswith('from '):
                    if line.startswith('import '):
                        # import module
                        module = line.replace('import ', '').strip()
                        symbols.append(module)
                    elif line.startswith('from '):
                        # from module import symbol
                        parts = line.split(' import ')
                        if len(parts) > 1:
                            symbols.extend([s.strip() for s in parts[1].split(',')])
        
        return symbols
    
    def _extract_api_calls(self, code: str, language: str) -> List[str]:
        """Extract API calls from code"""
        api_calls = []
        
        if language == 'python':
            # Look for HTTP requests and external API calls
            lines = code.split('\n')
            for line in lines:
                line = line.strip()
                if any(method in line for method in ['requests.', 'httpx.', 'urllib.', 'aiohttp.', 'http.']) and '(' in line:
                    api_calls.append(line.strip())
        
        return api_calls
    
    def _extract_error_handling(self, code: str, language: str) -> List[str]:
        """Extract error handling patterns from code"""
        error_handling = []
        
        if language == 'python':
            # Look for try-except blocks
            lines = code.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith('try:'):
                    # Found try block, look for except
                    for j in range(i, min(i+10, len(lines))):
                        if lines[j].strip().startswith('except'):
                            error_handling.append(lines[j].strip())
                            break
        
        return error_handling
    
    def _extract_control_flow(self, code: str, language: str) -> List[str]:
        """Extract control flow patterns from code"""
        control_flow = []
        
        if language == 'python':
            # Look for control flow statements
            lines = code.split('\n')
            for line in lines:
                line = line.strip()
                if any(stmt in line for stmt in ['if ', 'for ', 'while ', 'with ', 'elif ', 'else:']):
                    control_flow.append(line.strip())
        
        return control_flow
    
    def discover_integration_patterns(self, libraries: List[str], use_case: str) -> List[IntegrationPattern]:
        """Discover integration patterns from SourceGraph"""
        cache_key = f"{':'.join(libraries)}:{use_case}"
        
        if cache_key in self.pattern_cache:
            return self.pattern_cache[cache_key]
        
        try:
            # Use SourceGraph to find patterns
            pattern_validation = self.sourcegraph_integration.validate_pattern(libraries, use_case)
            
            patterns = []
            
            for example in pattern_validation['examples']:
                pattern = IntegrationPattern(
                    pattern_id=f"{example['repository']}_{example['file_path'].replace('/', '_')}",
                    pattern_name=f"{example['language']}_integration",
                    description=f"Integration pattern from {example['repository']}",
                    code_example=example['code_snippet'],
                    dependencies=libraries,
                    confidence_score=pattern_validation['confidence'],
                    source_repository=example['repository'],
                    language=example['language']
                )
                patterns.append(pattern)
            
            # Cache the result
            self.pattern_cache[cache_key] = patterns
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Failed to discover integration patterns: {e}")
            return []
    
    def match_components_to_patterns(self, components: List[CodeComponent], patterns: List[IntegrationPattern]) -> Dict[str, List[CodeComponent]]:
        """Match extracted components to integration patterns"""
        pattern_matches = {pattern.pattern_id: [] for pattern in patterns}
        
        for component in components:
            for pattern in patterns:
                if self._component_matches_pattern(component, pattern):
                    pattern_matches[pattern.pattern_id].append(component)
        
        return pattern_matches
    
    def _component_matches_pattern(self, component: CodeComponent, pattern: IntegrationPattern) -> bool:
        """Check if component matches a pattern"""
        # Simple matching logic - in real implementation this would be more sophisticated
        if component.language != pattern.language:
            return False
        
        # Check if component uses any of the pattern dependencies
        if not any(dep in component.dependencies for dep in pattern.dependencies):
            return False
        
        # Check code similarity (simplified)
        if len(component.code) > 0 and len(pattern.code_example) > 0:
            # Simple keyword matching
            component_keywords = set(component.code.lower().split())
            pattern_keywords = set(pattern.code_example.lower().split())
            
            # Check for significant overlap
            if len(component_keywords.intersection(pattern_keywords)) > min(5, len(pattern_keywords) // 2):
                return True
        
        return False
    
    def integrate_components(self, components: List[CodeComponent], patterns: List[IntegrationPattern]) -> Dict[str, Any]:
        """Integrate components based on patterns"""
        integration_result = {
            'components': components,
            'patterns': patterns,
            'matches': self.match_components_to_patterns(components, patterns),
            'integration_score': 0.0,
            'recommendations': [],
            'warnings': []
        }
        
        # Calculate integration score
        total_matches = sum(len(matches) for matches in integration_result['matches'].values())
        integration_result['integration_score'] = min(1.0, total_matches / len(components)) if components else 0.0
        
        # Generate recommendations
        if integration_result['integration_score'] < 0.5:
            integration_result['recommendations'].append(
                "Consider reviewing component dependencies against integration patterns"
            )
        
        # Generate warnings
        for pattern_id, matches in integration_result['matches'].items():
            if not matches:
                integration_result['warnings'].append(
                    f"No components matched pattern {pattern_id}"
                )
        
        return integration_result
    
    def validate_integration_compatibility(self, components: List[CodeComponent]) -> Dict[str, Any]:
        """Validate compatibility between components"""
        compatibility_result = {
            'compatible': True,
            'issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Check for conflicting dependencies
        dependency_conflicts = self._find_dependency_conflicts(components)
        if dependency_conflicts:
            compatibility_result['compatible'] = False
            compatibility_result['issues'].extend(dependency_conflicts)
        
        # Check for language compatibility
        language_conflicts = self._find_language_conflicts(components)
        if language_conflicts:
            compatibility_result['warnings'].extend(language_conflicts)
        
        # Check for structural compatibility
        structural_issues = self._find_structural_issues(components)
        if structural_issues:
            compatibility_result['warnings'].extend(structural_issues)
        
        return compatibility_result
    
    def _find_dependency_conflicts(self, components: List[CodeComponent]) -> List[str]:
        """Find dependency conflicts between components"""
        conflicts = []
        
        # Collect all dependencies
        all_dependencies = {}
        for component in components:
            for dep in component.dependencies:
                if dep in all_dependencies:
                    if all_dependencies[dep] != component.language:
                        conflicts.append(
                            f"Dependency conflict: {dep} used by both {all_dependencies[dep]} and {component.language}"
                        )
                else:
                    all_dependencies[dep] = component.language
        
        return conflicts
    
    def _find_language_conflicts(self, components: List[CodeComponent]) -> List[str]:
        """Find language compatibility issues"""
        conflicts = []
        
        # Check for mixed language components that might need integration
        languages = [comp.language for comp in components]
        if len(set(languages)) > 1:
            conflicts.append(
                "Multiple programming languages detected - ensure proper integration mechanisms"
            )
        
        return conflicts
    
    def _find_structural_issues(self, components: List[CodeComponent]) -> List[str]:
        """Find structural compatibility issues"""
        issues = []
        
        # Check for circular dependencies (simplified)
        function_names = [comp.name for comp in components if comp.type == 'function']
        if len(function_names) > 10:
            issues.append(
                "Large number of functions detected - consider modular organization"
            )
        
        # Check for missing main entry point
        main_functions = [comp for comp in components if comp.name.lower() in ['main', 'app', 'run']]
        if not main_functions and len(components) > 5:
            issues.append(
                "No clear entry point detected - consider adding a main function"
            )
        
        return issues