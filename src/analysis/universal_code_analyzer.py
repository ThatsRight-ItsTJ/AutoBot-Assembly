import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from tree_sitter_languages import get_language, get_parser

@dataclass
class CodeElement:
    name: str
    type: str  # 'function', 'class', 'import', 'variable'
    line_start: int
    line_end: int
    code: str
    file_path: str
    language: str

@dataclass
class RepositoryAnalysis:
    functions: List[CodeElement]
    classes: List[CodeElement]
    imports: List[CodeElement]
    dependencies: List[str]
    api_calls: List[CodeElement]
    file_count: int
    language_distribution: Dict[str, int]

class UniversalCodeAnalyzer:
    def __init__(self):
        self.parsers = {}
        self.supported_languages = [
            'python', 'javascript', 'typescript', 'java', 'go', 
            'rust', 'cpp', 'c_sharp', 'php', 'ruby', 'swift'
        ]
        self.logger = logging.getLogger(__name__)
        
        # Initialize cache directory
        cache_dir = os.getenv('TREESITTER_CACHE_DIR', './cache/tree-sitter')
        os.makedirs(cache_dir, exist_ok=True)
    
    def analyze_repository_structure(self, repo_path: str) -> RepositoryAnalysis:
        """Deep structural analysis of repository"""
        analysis = RepositoryAnalysis(
            functions=[],
            classes=[],
            imports=[],
            dependencies=[],
            api_calls=[],
            file_count=0,
            language_distribution={}
        )
        
        code_files = self.find_code_files(repo_path)
        analysis.file_count = len(code_files)
        
        for file_path in code_files:
            language = self.detect_language(file_path)
            if language and language in self.supported_languages:
                file_analysis = self.parse_file_structure(file_path, language)
                self.merge_analysis(analysis, file_analysis)
                
                # Update language distribution
                analysis.language_distribution[language] = analysis.language_distribution.get(language, 0) + 1
        
        return analysis
    
    def find_code_files(self, repo_path: str) -> List[str]:
        """Find all code files in repository"""
        code_files = []
        supported_extensions = {
            'python': ['.py'],
            'javascript': ['.js', '.jsx'],
            'typescript': ['.ts', '.tsx'],
            'java': ['.java'],
            'go': ['.go'],
            'rust': ['.rs'],
            'cpp': ['.cpp', '.cc', '.cxx', '.c++'],
            'c_sharp': ['.cs'],
            'php': ['.php'],
            'ruby': ['.rb'],
            'swift': ['.swift']
        }
        
        for root, dirs, files in os.walk(repo_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', 'venv', 'env']]
            
            for file in files:
                for language, extensions in supported_extensions.items():
                    if any(file.endswith(ext) for ext in extensions):
                        code_files.append(os.path.join(root, file))
                        break
        
        return code_files
    
    def detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension"""
        extension = os.path.splitext(file_path)[1].lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.c++': 'cpp',
            '.cs': 'c_sharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift'
        }
        
        return language_map.get(extension)
    
    def get_parser(self, language: str):
        """Get parser for specific language"""
        if language not in self.parsers:
            try:
                parser = get_parser(language)
                self.parsers[language] = parser
            except Exception as e:
                self.logger.error(f"Failed to get parser for {language}: {e}")
                raise
        return self.parsers[language]
    
    def parse_file_structure(self, file_path: str, language: str) -> Dict[str, List[CodeElement]]:
        """Extract structural elements from code file"""
        parser = self.get_parser(language)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    source_code = f.read()
            except Exception as e:
                self.logger.error(f"Failed to read file {file_path}: {e}")
                return {}
        
        try:
            tree = parser.parse(bytes(source_code, 'utf-8'))
        except Exception as e:
            self.logger.error(f"Failed to parse file {file_path}: {e}")
            return {}
        
        return self.extract_code_elements(tree, source_code, file_path, language)
    
    def extract_code_elements(self, tree, source_code: str, file_path: str, language: str) -> Dict[str, List[CodeElement]]:
        """Extract code elements from parsed tree"""
        elements = {
            'functions': [],
            'classes': [],
            'imports': [],
            'api_calls': []
        }
        
        root_node = tree.root_node
        
        # Language-specific extraction
        if language == 'python':
            self._extract_python_elements(root_node, source_code, file_path, elements)
        elif language in ['javascript', 'typescript']:
            self._extract_javascript_elements(root_node, source_code, file_path, elements)
        elif language == 'java':
            self._extract_java_elements(root_node, source_code, file_path, elements)
        elif language == 'go':
            self._extract_go_elements(root_node, source_code, file_path, elements)
        else:
            # Generic extraction for other languages
            self._extract_generic_elements(root_node, source_code, file_path, elements)
        
        return elements
    
    def _extract_python_elements(self, node, source_code: str, file_path: str, elements: Dict[str, List[CodeElement]]):
        """Extract Python-specific elements"""
        for child in node.children:
            if child.type == 'function_definition':
                start_line = child.start_point[0] + 1
                end_line = child.end_point[0] + 1
                function_name = child.child_by_field_name('name').text.decode('utf-8') if child.child_by_field_name('name') else 'anonymous'
                
                elements['functions'].append(CodeElement(
                    name=function_name,
                    type='function',
                    line_start=start_line,
                    line_end=end_line,
                    code=source_code[child.start_point[0]:child.end_point[1]],
                    file_path=file_path,
                    language='python'
                ))
            
            elif child.type == 'class_definition':
                start_line = child.start_point[0] + 1
                end_line = child.end_point[0] + 1
                class_name = child.child_by_field_name('name').text.decode('utf-8') if child.child_by_field_name('name') else 'anonymous'
                
                elements['classes'].append(CodeElement(
                    name=class_name,
                    type='class',
                    line_start=start_line,
                    line_end=end_line,
                    code=source_code[child.start_point[0]:child.end_point[1]],
                    file_path=file_path,
                    language='python'
                ))
            
            elif child.type == 'import_from_statement' or child.type == 'import_statement':
                start_line = child.start_point[0] + 1
                end_line = child.end_point[0] + 1
                
                elements['imports'].append(CodeElement(
                    name=child.text.decode('utf-8'),
                    type='import',
                    line_start=start_line,
                    line_end=end_line,
                    code=source_code[child.start_point[0]:child.end_point[1]],
                    file_path=file_path,
                    language='python'
                ))
            
            # Recursively process children
            self._extract_python_elements(child, source_code, file_path, elements)
    
    def _extract_javascript_elements(self, node, source_code: str, file_path: str, elements: Dict[str, List[CodeElement]]):
        """Extract JavaScript/TypeScript-specific elements"""
        for child in node.children:
            if child.type == 'function_declaration' or child.type == 'function':
                start_line = child.start_point[0] + 1
                end_line = child.end_point[0] + 1
                function_name = child.child_by_field_name('name').text.decode('utf-8') if child.child_by_field_name('name') else 'anonymous'
                
                elements['functions'].append(CodeElement(
                    name=function_name,
                    type='function',
                    line_start=start_line,
                    line_end=end_line,
                    code=source_code[child.start_point[0]:child.end_point[1]],
                    file_path=file_path,
                    language='javascript'
                ))
            
            elif child.type == 'class_declaration' or child.type == 'class':
                start_line = child.start_point[0] + 1
                end_line = child.end_point[0] + 1
                class_name = child.child_by_field_name('name').text.decode('utf-8') if child.child_by_field_name('name') else 'anonymous'
                
                elements['classes'].append(CodeElement(
                    name=class_name,
                    type='class',
                    line_start=start_line,
                    line_end=end_line,
                    code=source_code[child.start_point[0]:child.end_point[1]],
                    file_path=file_path,
                    language='javascript'
                ))
            
            elif child.type == 'import_statement':
                start_line = child.start_point[0] + 1
                end_line = child.end_point[0] + 1
                
                elements['imports'].append(CodeElement(
                    name=child.text.decode('utf-8'),
                    type='import',
                    line_start=start_line,
                    line_end=end_line,
                    code=source_code[child.start_point[0]:child.end_point[1]],
                    file_path=file_path,
                    language='javascript'
                ))
            
            # Recursively process children
            self._extract_javascript_elements(child, source_code, file_path, elements)
    
    def _extract_java_elements(self, node, source_code: str, file_path: str, elements: Dict[str, List[CodeElement]]):
        """Extract Java-specific elements"""
        for child in node.children:
            if child.type == 'method_declaration':
                start_line = child.start_point[0] + 1
                end_line = child.end_point[0] + 1
                method_name = child.child_by_field_name('name').text.decode('utf-8') if child.child_by_field_name('name') else 'anonymous'
                
                elements['functions'].append(CodeElement(
                    name=method_name,
                    type='function',
                    line_start=start_line,
                    line_end=end_line,
                    code=source_code[child.start_point[0]:child.end_point[1]],
                    file_path=file_path,
                    language='java'
                ))
            
            elif child.type == 'class_declaration':
                start_line = child.start_point[0] + 1
                end_line = child.end_point[0] + 1
                class_name = child.child_by_field_name('name').text.decode('utf-8') if child.child_by_field_name('name') else 'anonymous'
                
                elements['classes'].append(CodeElement(
                    name=class_name,
                    type='class',
                    line_start=start_line,
                    line_end=end_line,
                    code=source_code[child.start_point[0]:child.end_point[1]],
                    file_path=file_path,
                    language='java'
                ))
            
            elif child.type == 'import_declaration':
                start_line = child.start_point[0] + 1
                end_line = child.end_point[0] + 1
                
                elements['imports'].append(CodeElement(
                    name=child.text.decode('utf-8'),
                    type='import',
                    line_start=start_line,
                    line_end=end_line,
                    code=source_code[child.start_point[0]:child.end_point[1]],
                    file_path=file_path,
                    language='java'
                ))
            
            # Recursively process children
            self._extract_java_elements(child, source_code, file_path, elements)
    
    def _extract_go_elements(self, node, source_code: str, file_path: str, elements: Dict[str, List[CodeElement]]):
        """Extract Go-specific elements"""
        for child in node.children:
            if child.type == 'function_declaration':
                start_line = child.start_point[0] + 1
                end_line = child.end_point[0] + 1
                function_name = child.child_by_field_name('name').text.decode('utf-8') if child.child_by_field_name('name') else 'anonymous'
                
                elements['functions'].append(CodeElement(
                    name=function_name,
                    type='function',
                    line_start=start_line,
                    line_end=end_line,
                    code=source_code[child.start_point[0]:child.end_point[1]],
                    file_path=file_path,
                    language='go'
                ))
            
            elif child.type == 'type_declaration':
                start_line = child.start_point[0] + 1
                end_line = child.end_point[0] + 1
                type_name = child.child_by_field_name('name').text.decode('utf-8') if child.child_by_field_name('name') else 'anonymous'
                
                elements['classes'].append(CodeElement(
                    name=type_name,
                    type='class',
                    line_start=start_line,
                    line_end=end_line,
                    code=source_code[child.start_point[0]:child.end_point[1]],
                    file_path=file_path,
                    language='go'
                ))
            
            elif child.type == 'import_spec':
                start_line = child.start_point[0] + 1
                end_line = child.end_point[0] + 1
                
                elements['imports'].append(CodeElement(
                    name=child.text.decode('utf-8'),
                    type='import',
                    line_start=start_line,
                    line_end=end_line,
                    code=source_code[child.start_point[0]:child.end_point[1]],
                    file_path=file_path,
                    language='go'
                ))
            
            # Recursively process children
            self._extract_go_elements(child, source_code, file_path, elements)
    
    def _extract_generic_elements(self, node, source_code: str, file_path: str, elements: Dict[str, List[CodeElement]]):
        """Generic extraction for unsupported languages"""
        for child in node.children:
            # Look for function-like patterns
            if 'function' in child.type.lower() or 'method' in child.type.lower():
                start_line = child.start_point[0] + 1
                end_line = child.end_point[0] + 1
                
                elements['functions'].append(CodeElement(
                    name=child.type,
                    type='function',
                    line_start=start_line,
                    line_end=end_line,
                    code=source_code[child.start_point[0]:child.end_point[1]],
                    file_path=file_path,
                    language='unknown'
                ))
            
            # Look for class-like patterns
            elif 'class' in child.type.lower() or 'struct' in child.type.lower():
                start_line = child.start_point[0] + 1
                end_line = child.end_point[0] + 1
                
                elements['classes'].append(CodeElement(
                    name=child.type,
                    type='class',
                    line_start=start_line,
                    line_end=end_line,
                    code=source_code[child.start_point[0]:child.end_point[1]],
                    file_path=file_path,
                    language='unknown'
                ))
            
            # Recursively process children
            self._extract_generic_elements(child, source_code, file_path, elements)
    
    def merge_analysis(self, analysis: RepositoryAnalysis, file_analysis: Dict[str, List[CodeElement]]):
        """Merge file analysis into repository analysis"""
        analysis.functions.extend(file_analysis.get('functions', []))
        analysis.classes.extend(file_analysis.get('classes', []))
        analysis.imports.extend(file_analysis.get('imports', []))
        analysis.api_calls.extend(file_analysis.get('api_calls', []))
        
        # Extract dependencies from imports
        for import_element in analysis.imports:
            if 'import' in import_element.name.lower():
                # Simple dependency extraction
                import_text = import_element.name
                if 'import' in import_text:
                    # Extract package/library name
                    parts = import_text.split()
                    if len(parts) > 1:
                        analysis.dependencies.append(parts[1])
    
    def extract_function_with_dependencies(self, repo_path: str, function_name: str, file_path: str, language: str) -> Dict[str, Any]:
        """Extract specific function with all dependencies"""
        try:
            parser = self.get_parser(language)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            tree = parser.parse(bytes(source_code, 'utf-8'))
            
            # Find function node
            function_node = self.find_function_node(tree, function_name, language)
            
            if not function_node:
                return {'error': f'Function {function_name} not found'}
            
            # Extract with proper boundaries
            extracted_code = source_code[function_node.start_point[0]:function_node.end_point[1]]
            
            # Find dependencies in the same file
            dependencies = self.find_local_dependencies(function_node, source_code, language)
            
            return {
                'code': extracted_code,
                'dependencies': dependencies,
                'imports': self.extract_required_imports(function_node, source_code, language),
                'line_start': function_node.start_point[0] + 1,
                'line_end': function_node.end_point[0] + 1
            }
            
        except Exception as e:
            self.logger.error(f"Failed to extract function {function_name}: {e}")
            return {'error': str(e)}
    
    def find_function_node(self, tree, function_name: str, language: str):
        """Find function node by name"""
        # This is a simplified implementation
        # In a real implementation, you would traverse the tree more intelligently
        root_node = tree.root_node
        
        if language == 'python':
            return self._find_python_function(root_node, function_name)
        elif language in ['javascript', 'typescript']:
            return self._find_javascript_function(root_node, function_name)
        elif language == 'java':
            return self._find_java_method(root_node, function_name)
        elif language == 'go':
            return self._find_go_function(root_node, function_name)
        
        return None
    
    def _find_python_function(self, node, function_name: str):
        """Find Python function by name"""
        for child in node.children:
            if child.type == 'function_definition':
                name_node = child.child_by_field_name('name')
                if name_node and name_node.text.decode('utf-8') == function_name:
                    return child
            
            # Recursively search
            result = self._find_python_function(child, function_name)
            if result:
                return result
        
        return None
    
    def _find_javascript_function(self, node, function_name: str):
        """Find JavaScript function by name"""
        for child in node.children:
            if child.type == 'function_declaration':
                name_node = child.child_by_field_name('name')
                if name_node and name_node.text.decode('utf-8') == function_name:
                    return child
            elif child.type == 'function':
                # Anonymous function, check if it's assigned to a variable
                for grandchild in child.children:
                    if grandchild.type == 'variable_declarator':
                        name_node = grandchild.child_by_field_name('name')
                        if name_node and name_node.text.decode('utf-8') == function_name:
                            return child
            
            # Recursively search
            result = self._find_javascript_function(child, function_name)
            if result:
                return result
        
        return None
    
    def _find_java_method(self, node, function_name: str):
        """Find Java method by name"""
        for child in node.children:
            if child.type == 'method_declaration':
                name_node = child.child_by_field_name('name')
                if name_node and name_node.text.decode('utf-8') == function_name:
                    return child
            
            # Recursively search
            result = self._find_java_method(child, function_name)
            if result:
                return result
        
        return None
    
    def _find_go_function(self, node, function_name: str):
        """Find Go function by name"""
        for child in node.children:
            if child.type == 'function_declaration':
                name_node = child.child_by_field_name('name')
                if name_node and name_node.text.decode('utf-8') == function_name:
                    return child
            
            # Recursively search
            result = self._find_go_function(child, function_name)
            if result:
                return result
        
        return None
    
    def find_local_dependencies(self, function_node, source_code: str, language: str) -> List[str]:
        """Find local dependencies within function scope"""
        dependencies = []
        
        # This is a simplified implementation
        # In a real implementation, you would analyze the function body for calls to other functions
        
        return dependencies
    
    def extract_required_imports(self, function_node, source_code: str, language: str) -> List[str]:
        """Extract required imports for a function"""
        imports = []
        
        # This is a simplified implementation
        # In a real implementation, you would analyze the function body for imported symbols
        
        return imports