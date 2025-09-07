"""
Code Integrator

Automated code integration and conflict resolution for assembled components.
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import ast
import json

from .file_extractor import ExtractionResult, ExtractedFile


class IntegrationStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    CONFLICTS = "conflicts"


@dataclass
class ImportConflict:
    module_name: str
    conflicting_files: List[str]
    conflict_type: str
    resolution_suggestion: str


@dataclass
class ConfigConflict:
    config_key: str
    conflicting_values: Dict[str, Any]
    files: List[str]
    resolution_suggestion: str


@dataclass
class IntegrationResult:
    status: IntegrationStatus
    integrated_files: List[str]
    import_conflicts: List[ImportConflict]
    config_conflicts: List[ConfigConflict]
    integration_path: str
    generated_files: List[str]
    error_message: Optional[str] = None


class CodeIntegrator:
    """Automated code integration with conflict resolution."""
    
    def __init__(self, integration_base_dir: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # Set up integration directory
        if integration_base_dir:
            self.integration_base_dir = Path(integration_base_dir)
        else:
            self.integration_base_dir = Path("integrated_project")
        
        self.integration_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Language-specific integration handlers
        self.language_handlers = {
            'python': self._integrate_python_files,
            'javascript': self._integrate_javascript_files,
            'java': self._integrate_java_files
        }
        
        # Import pattern matchers
        self.import_patterns = {
            'python': {
                'import': re.compile(r'^import\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)', re.MULTILINE),
                'from_import': re.compile(r'^from\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s+import\s+(.+)', re.MULTILINE)
            },
            'javascript': {
                'import': re.compile(r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]', re.MULTILINE),
                'require': re.compile(r'require\([\'"]([^\'"]+)[\'"]\)', re.MULTILINE)
            }
        }
        
        # Configuration file handlers
        self.config_handlers = {
            'requirements.txt': self._merge_requirements_txt,
            'package.json': self._merge_package_json,
            'setup.py': self._merge_setup_py,
            'pyproject.toml': self._merge_pyproject_toml
        }
    
    async def integrate_components(self, 
                                 extraction_results: Dict[str, ExtractionResult],
                                 language: str = "python",
                                 project_name: str = "integrated_project") -> IntegrationResult:
        """
        Integrate extracted components into a cohesive project.
        
        Args:
            extraction_results: Results from file extraction
            language: Target programming language
            project_name: Name for the integrated project
            
        Returns:
            IntegrationResult with integration status and conflicts
        """
        
        self.logger.info(f"Integrating components for {project_name} ({language})")
        
        # Create project directory
        project_path = self.integration_base_dir / project_name
        if project_path.exists():
            import shutil
            shutil.rmtree(project_path)
        project_path.mkdir(parents=True)
        
        try:
            # Collect all extracted files
            all_extracted_files = []
            for result in extraction_results.values():
                if result.status.value == 'success':
                    all_extracted_files.extend(result.extracted_files)
            
            # Analyze imports and dependencies
            import_analysis = await self._analyze_imports(all_extracted_files, language)
            
            # Detect conflicts
            import_conflicts = self._detect_import_conflicts(import_analysis)
            config_conflicts = await self._detect_config_conflicts(all_extracted_files)
            
            # Integrate files using language-specific handler
            handler = self.language_handlers.get(language.lower(), self._integrate_generic_files)
            integrated_files = await handler(all_extracted_files, project_path, import_conflicts)
            
            # Generate integration files
            generated_files = await self._generate_integration_files(
                all_extracted_files, project_path, language, import_analysis
            )
            
            # Determine overall status
            if import_conflicts or config_conflicts:
                status = IntegrationStatus.CONFLICTS
            elif integrated_files:
                status = IntegrationStatus.SUCCESS
            else:
                status = IntegrationStatus.FAILED
            
            return IntegrationResult(
                status=status,
                integrated_files=integrated_files,
                import_conflicts=import_conflicts,
                config_conflicts=config_conflicts,
                integration_path=str(project_path),
                generated_files=generated_files
            )
            
        except Exception as e:
            self.logger.error(f"Integration failed: {e}")
            return IntegrationResult(
                status=IntegrationStatus.FAILED,
                integrated_files=[],
                import_conflicts=[],
                config_conflicts=[],
                integration_path=str(project_path),
                generated_files=[],
                error_message=str(e)
            )
    
    async def _analyze_imports(self, extracted_files: List[ExtractedFile], language: str) -> Dict[str, Any]:
        """Analyze imports across all extracted files."""
        
        import_analysis = {
            'all_imports': set(),
            'file_imports': {},
            'external_dependencies': set(),
            'internal_modules': set()
        }
        
        patterns = self.import_patterns.get(language.lower(), {})
        if not patterns:
            return import_analysis
        
        for extracted_file in extracted_files:
            if extracted_file.file_type != 'code':
                continue
            
            file_path = Path(extracted_file.extracted_path)
            if not file_path.exists():
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_imports = set()
                
                # Extract imports based on language patterns
                for pattern_name, pattern in patterns.items():
                    matches = pattern.findall(content)
                    for match in matches:
                        if isinstance(match, tuple):
                            # Handle from_import case
                            module_name = match[0]
                        else:
                            module_name = match
                        
                        file_imports.add(module_name)
                        import_analysis['all_imports'].add(module_name)
                
                import_analysis['file_imports'][extracted_file.extracted_path] = file_imports
                
                # Classify imports as external or internal
                for import_name in file_imports:
                    if self._is_external_dependency(import_name, language):
                        import_analysis['external_dependencies'].add(import_name)
                    else:
                        import_analysis['internal_modules'].add(import_name)
                
            except Exception as e:
                self.logger.warning(f"Could not analyze imports in {file_path}: {e}")
        
        return import_analysis
    
    def _detect_import_conflicts(self, import_analysis: Dict[str, Any]) -> List[ImportConflict]:
        """Detect potential import conflicts."""
        
        conflicts = []
        
        # Check for duplicate module names from different files
        module_to_files = {}
        for file_path, imports in import_analysis['file_imports'].items():
            for import_name in imports:
                if import_name not in module_to_files:
                    module_to_files[import_name] = []
                module_to_files[import_name].append(file_path)
        
        # Identify potential conflicts (same module name from multiple sources)
        for module_name, files in module_to_files.items():
            if len(files) > 1 and not self._is_standard_library(module_name):
                conflicts.append(ImportConflict(
                    module_name=module_name,
                    conflicting_files=files,
                    conflict_type="duplicate_import",
                    resolution_suggestion=f"Verify {module_name} is the same module in all files"
                ))
        
        return conflicts
    
    async def _detect_config_conflicts(self, extracted_files: List[ExtractedFile]) -> List[ConfigConflict]:
        """Detect configuration conflicts."""
        
        conflicts = []
        config_files = [f for f in extracted_files if f.file_type == 'config']
        
        # Group config files by type
        config_by_type = {}
        for config_file in config_files:
            file_name = Path(config_file.original_path).name
            if file_name not in config_by_type:
                config_by_type[file_name] = []
            config_by_type[file_name].append(config_file)
        
        # Check for conflicts in each config type
        for config_type, files in config_by_type.items():
            if len(files) > 1:
                conflicts.append(ConfigConflict(
                    config_key=config_type,
                    conflicting_values={f.extracted_path: "multiple_files" for f in files},
                    files=[f.extracted_path for f in files],
                    resolution_suggestion=f"Merge {config_type} files manually"
                ))
        
        return conflicts
    
    async def _integrate_python_files(self, extracted_files: List[ExtractedFile], 
                                    project_path: Path, import_conflicts: List[ImportConflict]) -> List[str]:
        """Integrate Python files with conflict resolution."""
        
        integrated_files = []
        
        # Create source directory structure
        src_path = project_path / "src"
        src_path.mkdir(exist_ok=True)
        
        # Copy code files
        for extracted_file in extracted_files:
            if extracted_file.file_type == 'code':
                source_path = Path(extracted_file.extracted_path)
                if not source_path.exists():
                    continue
                
                # Determine destination path
                relative_path = Path(extracted_file.original_path)
                dest_path = src_path / relative_path.name
                
                # Handle naming conflicts
                counter = 1
                original_dest = dest_path
                while dest_path.exists():
                    stem = original_dest.stem
                    suffix = original_dest.suffix
                    dest_path = original_dest.parent / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                # Copy file
                import shutil
                shutil.copy2(source_path, dest_path)
                integrated_files.append(str(dest_path.relative_to(project_path)))
        
        # Copy configuration files to project root
        for extracted_file in extracted_files:
            if extracted_file.file_type == 'config':
                source_path = Path(extracted_file.extracted_path)
                if not source_path.exists():
                    continue
                
                file_name = Path(extracted_file.original_path).name
                dest_path = project_path / file_name
                
                # Handle config file merging
                if dest_path.exists() and file_name in self.config_handlers:
                    # Merge configuration files
                    handler = self.config_handlers[file_name]
                    await handler(source_path, dest_path)
                else:
                    import shutil
                    shutil.copy2(source_path, dest_path)
                
                integrated_files.append(str(dest_path.relative_to(project_path)))
        
        return integrated_files
    
    async def _integrate_javascript_files(self, extracted_files: List[ExtractedFile], 
                                        project_path: Path, import_conflicts: List[ImportConflict]) -> List[str]:
        """Integrate JavaScript files."""
        
        integrated_files = []
        
        # Create source directory
        src_path = project_path / "src"
        src_path.mkdir(exist_ok=True)
        
        # Copy files similar to Python integration
        for extracted_file in extracted_files:
            if extracted_file.file_type in ['code', 'config']:
                source_path = Path(extracted_file.extracted_path)
                if not source_path.exists():
                    continue
                
                if extracted_file.file_type == 'code':
                    dest_path = src_path / Path(extracted_file.original_path).name
                else:
                    dest_path = project_path / Path(extracted_file.original_path).name
                
                import shutil
                shutil.copy2(source_path, dest_path)
                integrated_files.append(str(dest_path.relative_to(project_path)))
        
        return integrated_files
    
    async def _integrate_java_files(self, extracted_files: List[ExtractedFile], 
                                  project_path: Path, import_conflicts: List[ImportConflict]) -> List[str]:
        """Integrate Java files."""
        
        integrated_files = []
        
        # Create Maven-style directory structure
        src_main_java = project_path / "src" / "main" / "java"
        src_main_java.mkdir(parents=True, exist_ok=True)
        
        for extracted_file in extracted_files:
            if extracted_file.file_type == 'code':
                source_path = Path(extracted_file.extracted_path)
                if not source_path.exists():
                    continue
                
                dest_path = src_main_java / Path(extracted_file.original_path).name
                
                import shutil
                shutil.copy2(source_path, dest_path)
                integrated_files.append(str(dest_path.relative_to(project_path)))
        
        return integrated_files
    
    async def _integrate_generic_files(self, extracted_files: List[ExtractedFile], 
                                     project_path: Path, import_conflicts: List[ImportConflict]) -> List[str]:
        """Generic file integration for unsupported languages."""
        
        integrated_files = []
        
        for extracted_file in extracted_files:
            source_path = Path(extracted_file.extracted_path)
            if not source_path.exists():
                continue
            
            dest_path = project_path / Path(extracted_file.original_path).name
            
            import shutil
            shutil.copy2(source_path, dest_path)
            integrated_files.append(str(dest_path.relative_to(project_path)))
        
        return integrated_files
    
    async def _generate_integration_files(self, extracted_files: List[ExtractedFile], 
                                        project_path: Path, language: str, 
                                        import_analysis: Dict[str, Any]) -> List[str]:
        """Generate integration and configuration files."""
        
        generated_files = []
        
        # Generate main entry point
        if language.lower() == 'python':
            main_file = await self._generate_python_main(project_path, import_analysis)
            if main_file:
                generated_files.append(main_file)
            
            # Generate __init__.py files
            init_files = await self._generate_python_init_files(project_path)
            generated_files.extend(init_files)
        
        elif language.lower() == 'javascript':
            main_file = await self._generate_javascript_main(project_path, import_analysis)
            if main_file:
                generated_files.append(main_file)
        
        # Generate README
        readme_file = await self._generate_readme(project_path, extracted_files, language)
        if readme_file:
            generated_files.append(readme_file)
        
        return generated_files
    
    async def _generate_python_main(self, project_path: Path, import_analysis: Dict[str, Any]) -> Optional[str]:
        """Generate Python main entry point."""
        
        main_content = '''#!/usr/bin/env python3
"""
Integrated Project Main Entry Point

This file was automatically generated by AutoBot Assembly System.
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


def main():
    """Main entry point for the integrated project."""
    print("Integrated project started successfully!")
    
    # TODO: Add your main application logic here
    pass


if __name__ == "__main__":
    main()
'''
        
        main_path = project_path / "main.py"
        with open(main_path, 'w', encoding='utf-8') as f:
            f.write(main_content)
        
        return str(main_path.relative_to(project_path))
    
    async def _generate_python_init_files(self, project_path: Path) -> List[str]:
        """Generate __init__.py files for Python packages."""
        
        generated_files = []
        src_path = project_path / "src"
        
        if src_path.exists():
            init_path = src_path / "__init__.py"
            with open(init_path, 'w', encoding='utf-8') as f:
                f.write('"""Integrated project source package."""\n')
            generated_files.append(str(init_path.relative_to(project_path)))
        
        return generated_files
    
    async def _generate_javascript_main(self, project_path: Path, import_analysis: Dict[str, Any]) -> Optional[str]:
        """Generate JavaScript main entry point."""
        
        main_content = '''/**
 * Integrated Project Main Entry Point
 * 
 * This file was automatically generated by AutoBot Assembly System.
 */

console.log("Integrated project started successfully!");

// TODO: Add your main application logic here

module.exports = {
    // Export your main functions here
};
'''
        
        main_path = project_path / "index.js"
        with open(main_path, 'w', encoding='utf-8') as f:
            f.write(main_content)
        
        return str(main_path.relative_to(project_path))
    
    async def _generate_readme(self, project_path: Path, extracted_files: List[ExtractedFile], language: str) -> Optional[str]:
        """Generate project README."""
        
        # Count file types
        file_counts = {'code': 0, 'config': 0, 'documentation': 0}
        for f in extracted_files:
            file_counts[f.file_type] = file_counts.get(f.file_type, 0) + 1
        
        readme_content = f'''# Integrated Project

This project was automatically assembled by the AutoBot Assembly System.

## Project Structure

- **Language**: {language.title()}
- **Code files**: {file_counts['code']}
- **Configuration files**: {file_counts['config']}
- **Documentation files**: {file_counts['documentation']}

## Getting Started

### Prerequisites

Make sure you have {language.title()} installed on your system.

### Installation

1. Clone or download this project
2. Install dependencies (if any)
3. Run the main entry point

### Usage

```bash
# For Python projects
python main.py

# For JavaScript projects
node index.js
```

## Components

This project integrates the following components:

'''
        
        # Add component information
        repo_names = set()
        for f in extracted_files:
            # Extract repository name from path
            path_parts = Path(f.extracted_path).parts
            if len(path_parts) > 0:
                repo_names.add(path_parts[0])
        
        for repo_name in sorted(repo_names):
            readme_content += f"- {repo_name}\n"
        
        readme_content += '''
## Notes

- This is an automatically generated integration
- Manual review and testing is recommended
- Some components may require additional configuration

## License

Please review the licenses of individual components for compliance requirements.
'''
        
        readme_path = project_path / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        return str(readme_path.relative_to(project_path))
    
    async def _merge_requirements_txt(self, source_path: Path, dest_path: Path):
        """Merge requirements.txt files."""
        
        # Read existing requirements
        existing_reqs = set()
        if dest_path.exists():
            with open(dest_path, 'r') as f:
                existing_reqs = set(line.strip() for line in f if line.strip() and not line.startswith('#'))
        
        # Read new requirements
        new_reqs = set()
        with open(source_path, 'r') as f:
            new_reqs = set(line.strip() for line in f if line.strip() and not line.startswith('#'))
        
        # Merge and write
        all_reqs = sorted(existing_reqs.union(new_reqs))
        with open(dest_path, 'w') as f:
            f.write("# Merged requirements from multiple components\n")
            for req in all_reqs:
                f.write(f"{req}\n")
    
    async def _merge_package_json(self, source_path: Path, dest_path: Path):
        """Merge package.json files."""
        
        # This is a simplified merge - in practice, you'd want more sophisticated merging
        import json
        
        # Read existing package.json
        existing_data = {}
        if dest_path.exists():
            with open(dest_path, 'r') as f:
                existing_data = json.load(f)
        
        # Read new package.json
        with open(source_path, 'r') as f:
            new_data = json.load(f)
        
        # Merge dependencies
        if 'dependencies' in new_data:
            if 'dependencies' not in existing_data:
                existing_data['dependencies'] = {}
            existing_data['dependencies'].update(new_data['dependencies'])
        
        if 'devDependencies' in new_data:
            if 'devDependencies' not in existing_data:
                existing_data['devDependencies'] = {}
            existing_data['devDependencies'].update(new_data['devDependencies'])
        
        # Write merged file
        with open(dest_path, 'w') as f:
            json.dump(existing_data, f, indent=2)
    
    async def _merge_setup_py(self, source_path: Path, dest_path: Path):
        """Merge setup.py files (simplified)."""
        
        # For setup.py, we'll just append a comment about the conflict
        with open(dest_path, 'a') as f:
            f.write(f"\n# NOTE: Conflicting setup.py from {source_path.name}\n")
            f.write(f"# Manual merge required\n")
    
    async def _merge_pyproject_toml(self, source_path: Path, dest_path: Path):
        """Merge pyproject.toml files (simplified)."""
        
        # Similar to setup.py, add a note about the conflict
        with open(dest_path, 'a') as f:
            f.write(f"\n# NOTE: Conflicting pyproject.toml from {source_path.name}\n")
            f.write(f"# Manual merge required\n")
    
    def _is_external_dependency(self, import_name: str, language: str) -> bool:
        """Check if import is an external dependency."""
        
        # Standard library modules (simplified)
        stdlib_modules = {
            'python': ['os', 'sys', 'json', 'datetime', 'collections', 'itertools', 're', 'pathlib'],
            'javascript': ['fs', 'path', 'http', 'https', 'url', 'util']
        }
        
        std_modules = stdlib_modules.get(language.lower(), [])
        
        # Check if it's a standard library module
        for std_module in std_modules:
            if import_name.startswith(std_module):
                return False
        
        # Check if it's a relative import
        if import_name.startswith('.'):
            return False
        
        return True
    
    def _is_standard_library(self, module_name: str) -> bool:
        """Check if module is part of standard library."""
        
        # Common standard library modules
        stdlib = [
            'os', 'sys', 'json', 'datetime', 'collections', 'itertools', 're', 'pathlib',
            'asyncio', 'logging', 'typing', 'dataclasses', 'enum', 'functools'
        ]
        
        return any(module_name.startswith(std) for std in stdlib)


# Example usage
async def main():
    from .repository_cloner import RepositoryCloner
    from .file_extractor import FileExtractor
    from ..search.tier1_packages import PackageResult
    from datetime import datetime
    
    # Test integration workflow
    cloner = RepositoryCloner()
    extractor = FileExtractor()
    integrator = CodeIntegrator()
    
    # Create test repository
    test_repos = [
        PackageResult(
            name="requests",
            repository_url="https://github.com/psf/requests",
            description="HTTP library for Python",
            downloads=1000000,
            stars=50000,
            last_updated=datetime.now(),
            license="Apache-2.0",
            quality_score=0.9,
            language="python",
            package_manager="pypi",
            version="2.31.0",
            dependencies_count=5
        )
    ]
    
    print("Testing code integration workflow...")
    
    # Clone repositories
    clone_results = await cloner.clone_repositories(test_repos)
    
    # Extract files
    extraction_results = await extractor.extract_files(
        clone_results, 
        language="python",
        extraction_criteria={'max_files_per_repo': 10}
    )
    
    # Integrate components
    integration_result = await integrator.integrate_components(
        extraction_results, 
        language="python",
        project_name="test_integration"
    )
    
    # Print results
    print(f"\nIntegration Result:")
    print(f"  Status: {integration_result.status.value}")
    print(f"  Integrated files: {len(integration_result.integrated_files)}")
    print(f"  Generated files: {len(integration_result.generated_files)}")
    print(f"  Import conflicts: {len(integration_result.import_conflicts)}")
    print(f"  Config conflicts: {len(integration_result.config_conflicts)}")
    print(f"  Integration path: {integration_result.integration_path}")
    
    if integration_result.import_conflicts:
        print(f"\nImport Conflicts:")
        for conflict in integration_result.import_conflicts:
            print(f"  • {conflict.module_name}: {conflict.conflict_type}")
            print(f"    Files: {', '.join(conflict.conflicting_files)}")
            print(f"    Suggestion: {conflict.resolution_suggestion}")
    
    # Cleanup
    await cloner.cleanup_clones(clone_results)
    print("Test completed")


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())