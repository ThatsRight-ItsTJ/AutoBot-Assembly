"""
AST-grep Integration

Structural code analysis using ast-grep for pattern matching and code structure analysis.
"""

import asyncio
import json
import logging
import subprocess
import tempfile
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ImportAnalysis:
    imports: List[str]
    external_dependencies: List[str]
    internal_dependencies: List[str]
    dependency_count: int


@dataclass
class ClassMetrics:
    class_count: int
    average_complexity: float
    method_count: int
    inheritance_depth: int


@dataclass
class FrameworkDependencies:
    frameworks: List[str]
    coupling_score: float
    framework_specific_patterns: Dict[str, int]


@dataclass
class StructureAnalysis:
    imports: ImportAnalysis
    class_metrics: ClassMetrics
    framework_dependencies: FrameworkDependencies
    config_patterns: List[str]
    complexity_score: float
    maintainability_score: float


@dataclass
class AdaptationScore:
    overall_effort: float
    estimated_hours: int
    complexity_factors: Dict[str, Any]


class ASTGrepAnalyzer:
    """Structural code analysis using ast-grep."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Analysis patterns for different languages
        self.patterns = {
            'python': {
                'imports': {
                    'pattern': 'import $NAME',
                    'kind': 'import_statement'
                },
                'from_imports': {
                    'pattern': 'from $MODULE import $NAMES',
                    'kind': 'import_from_statement'
                },
                'class_definitions': {
                    'pattern': 'class $NAME($BASES): $BODY',
                    'kind': 'class_definition'
                },
                'function_definitions': {
                    'pattern': 'def $NAME($PARAMS): $BODY',
                    'kind': 'function_definition'
                },
                'method_definitions': {
                    'pattern': 'def $NAME(self, $PARAMS): $BODY',
                    'kind': 'function_definition'
                },
                'config_patterns': {
                    'pattern': '$VAR = $VALUE',
                    'kind': 'assignment'
                }
            },
            'javascript': {
                'imports': {
                    'pattern': 'import $NAMES from $MODULE',
                    'kind': 'import_statement'
                },
                'require_imports': {
                    'pattern': 'const $NAME = require($MODULE)',
                    'kind': 'variable_declaration'
                },
                'class_definitions': {
                    'pattern': 'class $NAME extends $BASE { $BODY }',
                    'kind': 'class_declaration'
                },
                'function_definitions': {
                    'pattern': 'function $NAME($PARAMS) { $BODY }',
                    'kind': 'function_declaration'
                },
                'arrow_functions': {
                    'pattern': '$NAME = ($PARAMS) => { $BODY }',
                    'kind': 'arrow_function'
                }
            },
            'java': {
                'imports': {
                    'pattern': 'import $PACKAGE.$CLASS;',
                    'kind': 'import_declaration'
                },
                'class_definitions': {
                    'pattern': 'class $NAME extends $BASE { $BODY }',
                    'kind': 'class_declaration'
                },
                'method_definitions': {
                    'pattern': 'public $TYPE $NAME($PARAMS) { $BODY }',
                    'kind': 'method_declaration'
                },
                'annotations': {
                    'pattern': '@$ANNOTATION',
                    'kind': 'annotation'
                }
            }
        }
        
        # Framework detection patterns
        self.framework_patterns = {
            'python': {
                'fastapi': ['from fastapi', 'FastAPI()', '@app.'],
                'flask': ['from flask', 'Flask(__name__)', '@app.route'],
                'django': ['from django', 'django.conf', 'models.Model'],
                'sqlalchemy': ['from sqlalchemy', 'declarative_base', 'Column'],
                'pydantic': ['from pydantic', 'BaseModel', 'Field'],
                'pytest': ['import pytest', '@pytest.', 'def test_']
            },
            'javascript': {
                'react': ['import React', 'useState', 'useEffect', 'jsx'],
                'express': ['express()', 'app.get', 'app.post'],
                'vue': ['Vue.component', 'new Vue', 'v-'],
                'angular': ['@Component', '@Injectable', 'ngOnInit'],
                'jest': ['describe(', 'it(', 'expect(']
            },
            'java': {
                'spring': ['@SpringBootApplication', '@RestController', '@Autowired'],
                'hibernate': ['@Entity', '@Table', '@Column'],
                'junit': ['@Test', '@BeforeEach', '@AfterEach']
            }
        }
        
        # Adaptation effort weights
        self.adaptation_weights = {
            'dependency_count': 0.3,
            'class_complexity': 0.25,
            'framework_coupling': 0.25,
            'configuration_requirements': 0.2
        }
    
    async def analyze_code_structure(self, file_path: str, language: str) -> StructureAnalysis:
        """
        Analyze code structure using AST-grep patterns.
        
        Args:
            file_path: Path to file to analyze
            language: Programming language
            
        Returns:
            StructureAnalysis with structural metrics
        """
        try:
            # Get patterns for the language
            lang_patterns = self.patterns.get(language.lower(), {})
            if not lang_patterns:
                return self._create_empty_analysis()
            
            # Run pattern matching
            pattern_results = {}
            for pattern_name, pattern_config in lang_patterns.items():
                try:
                    matches = await self._run_astgrep_pattern(
                        file_path, pattern_config['pattern'], language
                    )
                    pattern_results[pattern_name] = matches
                except Exception as e:
                    self.logger.error(f"Error running pattern {pattern_name}: {e}")
                    pattern_results[pattern_name] = []
            
            # Analyze results
            imports_analysis = self._analyze_imports(pattern_results, language)
            class_metrics = self._analyze_classes(pattern_results)
            framework_deps = self._analyze_framework_dependencies(file_path, language)
            config_patterns = self._analyze_config_patterns(pattern_results)
            
            # Calculate scores
            complexity_score = self._calculate_complexity_score(pattern_results)
            maintainability_score = self._calculate_maintainability_score(
                imports_analysis, class_metrics, framework_deps
            )
            
            return StructureAnalysis(
                imports=imports_analysis,
                class_metrics=class_metrics,
                framework_dependencies=framework_deps,
                config_patterns=config_patterns,
                complexity_score=complexity_score,
                maintainability_score=maintainability_score
            )
            
        except Exception as e:
            self.logger.error(f"Structure analysis failed: {e}")
            return self._create_empty_analysis()
    
    def assess_adaptation_effort(self, structure_analysis: StructureAnalysis) -> AdaptationScore:
        """
        Estimate how much work needed to integrate this code.
        
        Args:
            structure_analysis: Structural analysis results
            
        Returns:
            AdaptationScore with effort estimation
        """
        factors = {
            'dependency_count': structure_analysis.imports.dependency_count,
            'class_complexity': structure_analysis.class_metrics.average_complexity,
            'framework_coupling': structure_analysis.framework_dependencies.coupling_score,
            'configuration_requirements': len(structure_analysis.config_patterns)
        }
        
        # Calculate weighted adaptation effort score
        effort_score = self._calculate_weighted_score(factors, self.adaptation_weights)
        
        # Estimate integration time based on complexity factors
        estimated_hours = self._estimate_integration_time(factors)
        
        return AdaptationScore(
            overall_effort=effort_score,
            estimated_hours=estimated_hours,
            complexity_factors=factors
        )
    
    async def _run_astgrep_pattern(self, file_path: str, pattern: str, language: str) -> List[Dict[str, Any]]:
        """Run ast-grep with a specific pattern."""
        
        cmd = [
            'ast-grep',
            '--pattern', pattern,
            '--lang', language,
            '--json',
            file_path
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                output = stdout.decode('utf-8')
                if output.strip():
                    return json.loads(output)
            else:
                self.logger.debug(f"ast-grep pattern failed: {stderr.decode()}")
                
        except Exception as e:
            self.logger.error(f"Error running ast-grep: {e}")
        
        return []
    
    def _analyze_imports(self, pattern_results: Dict[str, List], language: str) -> ImportAnalysis:
        """Analyze import statements."""
        
        all_imports = []
        
        # Collect imports from different pattern types
        if 'imports' in pattern_results:
            all_imports.extend(pattern_results['imports'])
        if 'from_imports' in pattern_results:
            all_imports.extend(pattern_results['from_imports'])
        if 'require_imports' in pattern_results:
            all_imports.extend(pattern_results['require_imports'])
        
        # Extract import names
        import_names = []
        for imp in all_imports:
            # Extract import name from match text
            text = imp.get('text', '')
            if text:
                import_names.extend(self._extract_import_names(text, language))
        
        # Categorize imports
        external_deps = []
        internal_deps = []
        
        for imp_name in import_names:
            if self._is_external_dependency(imp_name, language):
                external_deps.append(imp_name)
            else:
                internal_deps.append(imp_name)
        
        return ImportAnalysis(
            imports=import_names,
            external_dependencies=list(set(external_deps)),
            internal_dependencies=list(set(internal_deps)),
            dependency_count=len(set(external_deps))
        )
    
    def _analyze_classes(self, pattern_results: Dict[str, List]) -> ClassMetrics:
        """Analyze class definitions."""
        
        classes = pattern_results.get('class_definitions', [])
        methods = pattern_results.get('method_definitions', []) + pattern_results.get('function_definitions', [])
        
        class_count = len(classes)
        method_count = len(methods)
        
        # Calculate average complexity (simplified)
        if class_count > 0:
            average_complexity = method_count / class_count
        else:
            average_complexity = 0.0
        
        # Estimate inheritance depth (simplified)
        inheritance_depth = 1  # Default depth
        for cls in classes:
            text = cls.get('text', '')
            if 'extends' in text or '(' in text:  # Has inheritance
                inheritance_depth = max(inheritance_depth, 2)
        
        return ClassMetrics(
            class_count=class_count,
            average_complexity=average_complexity,
            method_count=method_count,
            inheritance_depth=inheritance_depth
        )
    
    def _analyze_framework_dependencies(self, file_path: str, language: str) -> FrameworkDependencies:
        """Analyze framework dependencies by reading file content."""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return FrameworkDependencies([], 0.0, {})
        
        detected_frameworks = []
        framework_patterns = {}
        
        lang_frameworks = self.framework_patterns.get(language.lower(), {})
        
        for framework, patterns in lang_frameworks.items():
            pattern_count = 0
            for pattern in patterns:
                if pattern in content:
                    pattern_count += 1
            
            if pattern_count > 0:
                detected_frameworks.append(framework)
                framework_patterns[framework] = pattern_count
        
        # Calculate coupling score (0-1, higher means more tightly coupled)
        total_patterns = sum(framework_patterns.values())
        coupling_score = min(1.0, total_patterns / 10.0)  # Normalize to 0-1
        
        return FrameworkDependencies(
            frameworks=detected_frameworks,
            coupling_score=coupling_score,
            framework_specific_patterns=framework_patterns
        )
    
    def _analyze_config_patterns(self, pattern_results: Dict[str, List]) -> List[str]:
        """Analyze configuration patterns."""
        
        config_matches = pattern_results.get('config_patterns', [])
        config_items = []
        
        for match in config_matches:
            text = match.get('text', '')
            if text and any(keyword in text.lower() for keyword in ['config', 'setting', 'env', 'secret']):
                config_items.append(text)
        
        return config_items
    
    def _calculate_complexity_score(self, pattern_results: Dict[str, List]) -> float:
        """Calculate complexity score based on structural elements."""
        
        # Count various structural elements
        classes = len(pattern_results.get('class_definitions', []))
        functions = len(pattern_results.get('function_definitions', []))
        methods = len(pattern_results.get('method_definitions', []))
        
        # Simple complexity calculation
        total_elements = classes + functions + methods
        
        if total_elements == 0:
            return 0.0
        elif total_elements <= 5:
            return 0.2  # Low complexity
        elif total_elements <= 15:
            return 0.5  # Medium complexity
        elif total_elements <= 30:
            return 0.8  # High complexity
        else:
            return 1.0  # Very high complexity
    
    def _calculate_maintainability_score(self, imports: ImportAnalysis, 
                                       classes: ClassMetrics, 
                                       frameworks: FrameworkDependencies) -> float:
        """Calculate maintainability score."""
        
        score = 1.0
        
        # Penalty for too many dependencies
        if imports.dependency_count > 20:
            score -= 0.3
        elif imports.dependency_count > 10:
            score -= 0.1
        
        # Penalty for high class complexity
        if classes.average_complexity > 10:
            score -= 0.3
        elif classes.average_complexity > 5:
            score -= 0.1
        
        # Penalty for high framework coupling
        if frameworks.coupling_score > 0.8:
            score -= 0.2
        elif frameworks.coupling_score > 0.5:
            score -= 0.1
        
        return max(0.0, score)
    
    def _extract_import_names(self, import_text: str, language: str) -> List[str]:
        """Extract import names from import statement text."""
        
        import_names = []
        
        if language.lower() == 'python':
            if import_text.startswith('import '):
                # Handle "import module" or "import module as alias"
                parts = import_text.replace('import ', '').split(' as ')[0].split(',')
                import_names.extend([part.strip() for part in parts])
            elif import_text.startswith('from '):
                # Handle "from module import names"
                if ' import ' in import_text:
                    module_part = import_text.split(' import ')[0].replace('from ', '').strip()
                    import_names.append(module_part)
        
        elif language.lower() == 'javascript':
            if 'import ' in import_text and ' from ' in import_text:
                # Handle "import names from 'module'"
                module_part = import_text.split(' from ')[-1].strip().strip('\'"')
                import_names.append(module_part)
            elif 'require(' in import_text:
                # Handle "const name = require('module')"
                start = import_text.find('require(') + 8
                end = import_text.find(')', start)
                if end > start:
                    module_name = import_text[start:end].strip('\'"')
                    import_names.append(module_name)
        
        elif language.lower() == 'java':
            if import_text.startswith('import '):
                # Handle "import package.Class;"
                import_name = import_text.replace('import ', '').replace(';', '').strip()
                import_names.append(import_name)
        
        return import_names
    
    def _is_external_dependency(self, import_name: str, language: str) -> bool:
        """Determine if an import is an external dependency."""
        
        # Standard library modules (simplified detection)
        stdlib_modules = {
            'python': ['os', 'sys', 'json', 'datetime', 'collections', 'itertools', 'functools', 'typing'],
            'javascript': ['fs', 'path', 'http', 'https', 'url', 'util', 'crypto'],
            'java': ['java.util', 'java.io', 'java.lang', 'java.net', 'java.time']
        }
        
        std_modules = stdlib_modules.get(language.lower(), [])
        
        # Check if it's a standard library module
        for std_module in std_modules:
            if import_name.startswith(std_module):
                return False
        
        # Check if it's a relative import (internal)
        if import_name.startswith('.') or import_name.startswith('./') or import_name.startswith('../'):
            return False
        
        # Otherwise, assume it's external
        return True
    
    def _calculate_weighted_score(self, factors: Dict[str, Any], weights: Dict[str, float]) -> float:
        """Calculate weighted score from factors."""
        
        total_score = 0.0
        total_weight = 0.0
        
        for factor_name, factor_value in factors.items():
            weight = weights.get(factor_name, 0.0)
            if weight > 0:
                # Normalize factor value to 0-1 range
                normalized_value = min(1.0, factor_value / 10.0)
                total_score += normalized_value * weight
                total_weight += weight
        
        if total_weight > 0:
            return total_score / total_weight
        else:
            return 0.0
    
    def _estimate_integration_time(self, factors: Dict[str, Any]) -> int:
        """Estimate integration time in hours."""
        
        base_hours = 2  # Minimum time
        
        # Add time based on complexity factors
        dependency_hours = min(8, factors.get('dependency_count', 0) * 0.5)
        complexity_hours = min(12, factors.get('class_complexity', 0) * 2)
        coupling_hours = min(6, factors.get('framework_coupling', 0) * 10)
        config_hours = min(4, factors.get('configuration_requirements', 0) * 0.5)
        
        total_hours = base_hours + dependency_hours + complexity_hours + coupling_hours + config_hours
        
        return int(total_hours)
    
    def _get_file_extensions(self, language: str) -> List[str]:
        """Get file extensions for language."""
        
        extensions = {
            'python': ['py', 'pyw'],
            'javascript': ['js', 'jsx', 'ts', 'tsx'],
            'java': ['java'],
            'go': ['go'],
            'rust': ['rs'],
            'php': ['php'],
            'ruby': ['rb'],
            'c': ['c', 'h'],
            'cpp': ['cpp', 'cxx', 'cc', 'hpp']
        }
        
        return extensions.get(language.lower(), ['py'])  # Default to Python
    
    def _should_analyze_file(self, file_path: Path) -> bool:
        """Determine if file should be analyzed."""
        
        # Skip test files, build files, etc.
        skip_patterns = [
            'test_', '_test.', 'tests/', '__pycache__/', 'node_modules/',
            '.git/', 'build/', 'dist/', '.pytest_cache/', 'coverage/'
        ]
        
        file_str = str(file_path)
        return not any(pattern in file_str for pattern in skip_patterns)
    
    def _create_empty_analysis(self) -> StructureAnalysis:
        """Create empty analysis for failed cases."""
        
        return StructureAnalysis(
            imports=ImportAnalysis([], [], [], 0),
            class_metrics=ClassMetrics(0, 0.0, 0, 1),
            framework_dependencies=FrameworkDependencies([], 0.0, {}),
            config_patterns=[],
            complexity_score=0.0,
            maintainability_score=0.5
        )


# Example usage
async def main():
    analyzer = ASTGrepAnalyzer()
    
    # Test with a Python file
    test_file = "src/orchestration/project_analyzer.py"
    if Path(test_file).exists():
        print(f"Analyzing {test_file}...")
        
        analysis = await analyzer.analyze_code_structure(test_file, "python")
        
        print(f"\nStructure Analysis Results:")
        print(f"  Dependencies: {analysis.imports.dependency_count}")
        print(f"  External deps: {analysis.imports.external_dependencies}")
        print(f"  Classes: {analysis.class_metrics.class_count}")
        print(f"  Methods: {analysis.class_metrics.method_count}")
        print(f"  Frameworks: {analysis.framework_dependencies.frameworks}")
        print(f"  Complexity: {analysis.complexity_score:.2f}")
        print(f"  Maintainability: {analysis.maintainability_score:.2f}")
        
        # Test adaptation effort
        effort = analyzer.assess_adaptation_effort(analysis)
        print(f"\nAdaptation Effort:")
        print(f"  Overall effort: {effort.overall_effort:.2f}")
        print(f"  Estimated hours: {effort.estimated_hours}")
    else:
        print(f"Test file {test_file} not found")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())