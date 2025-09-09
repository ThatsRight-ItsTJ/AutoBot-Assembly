"""
Documentation Generator

Automated documentation generation for assembled projects.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json
import re

from ..assembly.generated_project import GeneratedProject
from .quality_validator import ValidationResult


class DocType(str, Enum):
    README = "readme"
    API_DOCS = "api_docs"
    USER_GUIDE = "user_guide"
    DEVELOPER_GUIDE = "developer_guide"
    CHANGELOG = "changelog"
    LICENSE = "license"


@dataclass
class DocumentationResult:
    project_name: str
    generated_documents: Dict[DocType, str]
    documentation_coverage: float
    generation_duration: float
    warnings: List[str]


class DocumentationGenerator:
    """Automated documentation generation system."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Documentation templates
        self.templates = {
            DocType.README: self._generate_readme,
            DocType.API_DOCS: self._generate_api_docs,
            DocType.USER_GUIDE: self._generate_user_guide,
            DocType.DEVELOPER_GUIDE: self._generate_developer_guide,
            DocType.CHANGELOG: self._generate_changelog,
            DocType.LICENSE: self._generate_license
        }
    
    async def generate_documentation(self, 
                                   generated_project: GeneratedProject,
                                   validation_result: Optional[ValidationResult] = None,
                                   doc_types: Optional[List[DocType]] = None) -> DocumentationResult:
        """
        Generate comprehensive documentation for a project.
        
        Args:
            generated_project: The generated project
            validation_result: Optional quality validation results
            doc_types: Specific documentation types to generate
            
        Returns:
            DocumentationResult with generated documentation
        """
        
        self.logger.info(f"Generating documentation for {generated_project.project_name}")
        start_time = asyncio.get_event_loop().time()
        
        if doc_types is None:
            doc_types = [DocType.README, DocType.USER_GUIDE, DocType.DEVELOPER_GUIDE, DocType.CHANGELOG]
        
        generated_documents = {}
        warnings = []
        
        project_path = Path(generated_project.project_path)
        
        try:
            # Analyze project structure for documentation context
            project_analysis = await self._analyze_project_structure(project_path, generated_project)
            
            # Generate each requested document type
            for doc_type in doc_types:
                try:
                    if doc_type in self.templates:
                        self.logger.info(f"Generating {doc_type.value} documentation...")
                        
                        generator_func = self.templates[doc_type]
                        content = await generator_func(
                            generated_project, validation_result, project_analysis
                        )
                        
                        if content:
                            generated_documents[doc_type] = content
                            
                            # Write to file
                            await self._write_documentation_file(
                                project_path, doc_type, content
                            )
                        else:
                            warnings.append(f"Could not generate {doc_type.value} documentation")
                            
                    else:
                        warnings.append(f"No generator available for {doc_type.value}")
                        
                except Exception as e:
                    self.logger.error(f"Failed to generate {doc_type.value}: {e}")
                    warnings.append(f"Failed to generate {doc_type.value}: {str(e)}")
            
            # Calculate documentation coverage
            coverage = len(generated_documents) / len(doc_types) if doc_types else 0.0
            
            generation_duration = asyncio.get_event_loop().time() - start_time
            
            return DocumentationResult(
                project_name=generated_project.project_name,
                generated_documents=generated_documents,
                documentation_coverage=coverage,
                generation_duration=generation_duration,
                warnings=warnings
            )
            
        except Exception as e:
            self.logger.error(f"Documentation generation failed: {e}")
            generation_duration = asyncio.get_event_loop().time() - start_time
            
            return DocumentationResult(
                project_name=generated_project.project_name,
                generated_documents={},
                documentation_coverage=0.0,
                generation_duration=generation_duration,
                warnings=[f"Documentation generation failed: {str(e)}"]
            )
    
    async def _analyze_project_structure(self, project_path: Path, 
                                       generated_project: GeneratedProject) -> Dict[str, Any]:
        """Analyze project structure to inform documentation generation."""
        
        analysis = {
            'source_files': [],
            'config_files': [],
            'test_files': [],
            'functions': [],
            'classes': [],
            'imports': [],
            'has_main': False,
            'has_tests': False,
            'has_config': False
        }
        
        try:
            # Analyze source files
            for src_dir in generated_project.structure.source_directories:
                src_path = project_path / src_dir
                if src_path.exists():
                    if generated_project.language.lower() == 'python':
                        source_files = list(src_path.rglob('*.py'))
                        analysis['source_files'].extend([str(f.relative_to(project_path)) for f in source_files])
                        
                        # Analyze Python files for functions and classes
                        for source_file in source_files:
                            try:
                                with open(source_file, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                
                                # Find functions
                                functions = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', content)
                                analysis['functions'].extend(functions)
                                
                                # Find classes
                                classes = re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
                                analysis['classes'].extend(classes)
                                
                                # Find imports
                                imports = re.findall(r'(?:from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+)?import\s+([a-zA-Z_][a-zA-Z0-9_.,\s]*)', content)
                                analysis['imports'].extend(imports)
                                
                            except Exception as e:
                                self.logger.debug(f"Could not analyze {source_file}: {e}")
                    
                    elif generated_project.language.lower() == 'javascript':
                        js_files = list(src_path.rglob('*.js')) + list(src_path.rglob('*.ts'))
                        analysis['source_files'].extend([str(f.relative_to(project_path)) for f in js_files])
                        
                        # Basic JavaScript analysis
                        for js_file in js_files:
                            try:
                                with open(js_file, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                
                                # Find functions
                                functions = re.findall(r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', content)
                                functions.extend(re.findall(r'const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\(', content))
                                analysis['functions'].extend(functions)
                                
                            except Exception as e:
                                self.logger.debug(f"Could not analyze {js_file}: {e}")
            
            # Check for main entry points
            for entry_point in generated_project.structure.entry_points:
                entry_path = project_path / entry_point
                if entry_path.exists():
                    analysis['has_main'] = True
                    break
            
            # Check for configuration files
            for config_file in generated_project.structure.config_files:
                config_path = project_path / config_file
                if config_path.exists():
                    analysis['has_config'] = True
                    analysis['config_files'].append(config_file)
            
            # Check for test files
            for test_dir in generated_project.structure.test_directories:
                test_path = project_path / test_dir
                if test_path.exists() and any(test_path.iterdir()):
                    analysis['has_tests'] = True
                    if generated_project.language.lower() == 'python':
                        test_files = list(test_path.rglob('*.py'))
                        analysis['test_files'].extend([str(f.relative_to(project_path)) for f in test_files])
            
            # Remove duplicates
            analysis['functions'] = list(set(analysis['functions']))
            analysis['classes'] = list(set(analysis['classes']))
            
        except Exception as e:
            self.logger.warning(f"Project structure analysis failed: {e}")
        
        return analysis
    
    async def _generate_readme(self, generated_project: GeneratedProject, 
                             validation_result: Optional[ValidationResult],
                             project_analysis: Dict[str, Any]) -> str:
        """Generate comprehensive README.md."""
        
        readme_content = f"""# {generated_project.project_name}

> Auto-generated project assembled by AutoBot Assembly System

## Overview

This {generated_project.language.title()} {generated_project.project_type.value.replace('_', ' ')} was automatically assembled from multiple open-source components to meet your requirements.

## Project Information

- **Language**: {generated_project.language.title()}
- **Project Type**: {generated_project.project_type.value.replace('_', ' ').title()}
- **Dependencies**: {len(generated_project.dependencies)} packages
"""
        
        # Add quality information if available
        if validation_result:
            readme_content += f"""- **Quality Score**: {validation_result.overall_score:.2f}/1.0 ({validation_result.overall_quality_level.value.title()})
"""
        
        readme_content += """
## Quick Start

### Prerequisites

"""
        
        # Add language-specific prerequisites
        if generated_project.language.lower() == 'python':
            readme_content += """- Python 3.8 or higher
- pip package manager
"""
        elif generated_project.language.lower() == 'javascript':
            readme_content += """- Node.js 16 or higher
- npm package manager
"""
        elif generated_project.language.lower() == 'java':
            readme_content += """- Java 11 or higher
- Maven build tool
"""
        
        readme_content += """
### Installation

"""
        
        # Add installation instructions
        if generated_project.build_commands:
            readme_content += "```bash\n"
            for cmd in generated_project.build_commands:
                readme_content += f"{cmd}\n"
            readme_content += "```\n\n"
        else:
            readme_content += "No build commands required.\n\n"
        
        readme_content += "### Usage\n\n"
        
        # Add usage instructions
        if generated_project.run_commands:
            readme_content += "```bash\n"
            for cmd in generated_project.run_commands:
                readme_content += f"{cmd}\n"
            readme_content += "```\n\n"
        
        # Add project structure
        readme_content += "## Project Structure\n\n"
        readme_content += "```\n"
        readme_content += f"{generated_project.project_name}/\n"
        
        for src_dir in generated_project.structure.source_directories:
            readme_content += f"├── {src_dir}/          # Source code\n"
        
        for test_dir in generated_project.structure.test_directories:
            readme_content += f"├── {test_dir}/         # Test files\n"
        
        for entry_point in generated_project.structure.entry_points:
            readme_content += f"├── {entry_point}       # Main entry point\n"
        
        readme_content += "├── README.md       # This file\n"
        
        for config_file in generated_project.structure.config_files:
            readme_content += f"└── {config_file}   # Configuration\n"
        
        readme_content += "```\n\n"
        
        # Add component information
        if project_analysis['functions'] or project_analysis['classes']:
            readme_content += "## Components\n\n"
            
            if project_analysis['classes']:
                readme_content += f"**Classes**: {', '.join(project_analysis['classes'][:10])}"
                if len(project_analysis['classes']) > 10:
                    readme_content += f" (and {len(project_analysis['classes']) - 10} more)"
                readme_content += "\n\n"
            
            if project_analysis['functions']:
                readme_content += f"**Functions**: {', '.join(project_analysis['functions'][:10])}"
                if len(project_analysis['functions']) > 10:
                    readme_content += f" (and {len(project_analysis['functions']) - 10} more)"
                readme_content += "\n\n"
        
        # Add testing information
        if generated_project.test_commands:
            readme_content += "## Testing\n\n"
            readme_content += "```bash\n"
            for cmd in generated_project.test_commands:
                readme_content += f"{cmd}\n"
            readme_content += "```\n\n"
        
        # Add quality information
        if validation_result:
            readme_content += "## Quality Metrics\n\n"
            
            if validation_result.strengths:
                readme_content += "### Strengths\n\n"
                for strength in validation_result.strengths:
                    readme_content += f"- {strength}\n"
                readme_content += "\n"
            
            if validation_result.recommendations:
                readme_content += "### Recommendations\n\n"
                for rec in validation_result.recommendations[:5]:
                    readme_content += f"- {rec}\n"
                readme_content += "\n"
        
        # Add dependencies
        if generated_project.dependencies:
            readme_content += "## Dependencies\n\n"
            for dep in generated_project.dependencies[:15]:
                readme_content += f"- {dep}\n"
            if len(generated_project.dependencies) > 15:
                readme_content += f"- ... and {len(generated_project.dependencies) - 15} more\n"
            readme_content += "\n"
        
        # Add footer
        readme_content += """## Notes

- This project was automatically assembled from multiple open-source components
- Manual review and testing is recommended before production use
- Some components may require additional configuration or customization

## License

Please review the licenses of individual components for compliance requirements.

---

*Generated by [AutoBot Assembly System](https://github.com/autobot-assembly)*
"""
        
        return readme_content
    
    async def _generate_api_docs(self, generated_project: GeneratedProject, 
                               validation_result: Optional[ValidationResult],
                               project_analysis: Dict[str, Any]) -> str:
        """Generate API documentation."""
        
        if not project_analysis['functions'] and not project_analysis['classes']:
            return ""  # No API to document
        
        api_docs = f"""# {generated_project.project_name} API Documentation

## Overview

This document describes the API for the {generated_project.project_name} {generated_project.project_type.value}.

"""
        
        # Document classes
        if project_analysis['classes']:
            api_docs += "## Classes\n\n"
            for class_name in project_analysis['classes']:
                api_docs += f"### {class_name}\n\n"
                api_docs += f"Description: Auto-generated class from assembled components.\n\n"
                api_docs += "```python\n"
                api_docs += f"class {class_name}:\n"
                api_docs += "    # Implementation details...\n"
                api_docs += "```\n\n"
        
        # Document functions
        if project_analysis['functions']:
            api_docs += "## Functions\n\n"
            for func_name in project_analysis['functions'][:20]:  # Limit to first 20
                if not func_name.startswith('_'):  # Skip private functions
                    api_docs += f"### {func_name}()\n\n"
                    api_docs += f"Description: Auto-generated function from assembled components.\n\n"
                    api_docs += "```python\n"
                    api_docs += f"def {func_name}():\n"
                    api_docs += "    # Implementation details...\n"
                    api_docs += "```\n\n"
        
        api_docs += """
## Usage Examples

```python
# Import the module
from src import main_module

# Use the functions and classes
# (Add specific examples based on your use case)
```

---

*Auto-generated API documentation*
"""
        
        return api_docs
    
    async def _generate_user_guide(self, generated_project: GeneratedProject, 
                                 validation_result: Optional[ValidationResult],
                                 project_analysis: Dict[str, Any]) -> str:
        """Generate user guide."""
        
        user_guide = f"""# {generated_project.project_name} User Guide

## Introduction

Welcome to {generated_project.project_name}! This guide will help you get started with using this {generated_project.project_type.value.replace('_', ' ')}.

## Getting Started

### Step 1: Installation

"""
        
        if generated_project.build_commands:
            user_guide += "Follow these commands to install the project:\n\n"
            user_guide += "```bash\n"
            for cmd in generated_project.build_commands:
                user_guide += f"{cmd}\n"
            user_guide += "```\n\n"
        
        user_guide += "### Step 2: Basic Usage\n\n"
        
        if generated_project.project_type.value == 'cli_tool':
            user_guide += """This is a command-line tool. Here are the basic commands:

```bash
# Get help
python cli.py --help

# Run with default options
python cli.py

# Run with verbose output
python cli.py --verbose
```

"""
        elif generated_project.project_type.value == 'web_service':
            user_guide += """This is a web service. To start the server:

```bash
python app.py
```

The service will be available at `http://localhost:5000` (or the configured port).

### API Endpoints

- `GET /` - Health check
- `GET /health` - Service status

"""
        elif generated_project.project_type.value == 'library':
            user_guide += """This is a library that you can import into your projects:

```python
import your_library

# Use the library functions
result = your_library.main_function()
```

"""
        else:
            user_guide += """To run the application:

```bash
python main.py
```

"""
        
        # Add configuration section
        if project_analysis['has_config']:
            user_guide += "## Configuration\n\n"
            user_guide += "The project uses the following configuration files:\n\n"
            for config_file in project_analysis['config_files']:
                user_guide += f"- `{config_file}` - Configuration settings\n"
            user_guide += "\n"
        
        # Add troubleshooting
        user_guide += """## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are installed
2. **Permission Errors**: Check file permissions
3. **Configuration Issues**: Verify configuration files are properly formatted

### Getting Help

- Check the README.md file for additional information
- Review the error messages for specific guidance
- Ensure all prerequisites are met

## Advanced Usage

For more advanced usage patterns and customization options, refer to the Developer Guide.

---

*User Guide - Generated by AutoBot Assembly System*
"""
        
        return user_guide
    
    async def _generate_developer_guide(self, generated_project: GeneratedProject, 
                                      validation_result: Optional[ValidationResult],
                                      project_analysis: Dict[str, Any]) -> str:
        """Generate developer guide."""
        
        dev_guide = f"""# {generated_project.project_name} Developer Guide

## Development Setup

### Prerequisites

- {generated_project.language.title()} development environment
- Git for version control
"""
        
        if generated_project.language.lower() == 'python':
            dev_guide += "- Virtual environment (recommended)\n"
        elif generated_project.language.lower() == 'javascript':
            dev_guide += "- Node.js and npm\n"
        
        dev_guide += """
### Development Installation

```bash
# Clone the repository
git clone <repository-url>
cd """ + generated_project.project_name + """

"""
        
        if generated_project.build_commands:
            dev_guide += "# Install dependencies\n"
            for cmd in generated_project.build_commands:
                dev_guide += f"{cmd}\n"
            dev_guide += "\n"
        
        dev_guide += "```\n\n"
        
        # Add project structure
        dev_guide += "## Project Architecture\n\n"
        dev_guide += f"This {generated_project.project_type.value} follows these architectural patterns:\n\n"
        
        if project_analysis['source_files']:
            dev_guide += "### Source Code Organization\n\n"
            for src_file in project_analysis['source_files'][:10]:
                dev_guide += f"- `{src_file}` - Source module\n"
            dev_guide += "\n"
        
        if project_analysis['functions']:
            dev_guide += f"### Key Functions ({len(project_analysis['functions'])} total)\n\n"
            for func in project_analysis['functions'][:10]:
                if not func.startswith('_'):
                    dev_guide += f"- `{func}()` - Core functionality\n"
            dev_guide += "\n"
        
        if project_analysis['classes']:
            dev_guide += f"### Classes ({len(project_analysis['classes'])} total)\n\n"
            for cls in project_analysis['classes'][:10]:
                dev_guide += f"- `{cls}` - Data/logic container\n"
            dev_guide += "\n"
        
        # Add testing information
        if generated_project.test_commands:
            dev_guide += "## Testing\n\n"
            dev_guide += "Run tests using:\n\n"
            dev_guide += "```bash\n"
            for cmd in generated_project.test_commands:
                dev_guide += f"{cmd}\n"
            dev_guide += "```\n\n"
        
        # Add quality information
        if validation_result:
            dev_guide += "## Code Quality\n\n"
            dev_guide += f"Current quality score: **{validation_result.overall_score:.2f}/1.0** ({validation_result.overall_quality_level.value.title()})\n\n"
            
            if validation_result.recommendations:
                dev_guide += "### Improvement Recommendations\n\n"
                for rec in validation_result.recommendations:
                    dev_guide += f"- {rec}\n"
                dev_guide += "\n"
        
        # Add contribution guidelines
        dev_guide += """## Contributing

### Code Style

- Follow language-specific style guidelines
- Add docstrings to functions and classes
- Include unit tests for new functionality

### Development Workflow

1. Create a feature branch
2. Make your changes
3. Add tests
4. Run quality checks
5. Submit a pull request

### Build and Deployment

"""
        
        if generated_project.build_commands:
            dev_guide += "Build commands:\n\n```bash\n"
            for cmd in generated_project.build_commands:
                dev_guide += f"{cmd}\n"
            dev_guide += "```\n\n"
        
        dev_guide += """## Debugging

### Common Development Issues

1. **Import path issues**: Check PYTHONPATH or module structure
2. **Dependency conflicts**: Use virtual environments
3. **Configuration problems**: Verify config file formats

### Debugging Tools

- Use IDE debugger for step-through debugging
- Add logging statements for runtime debugging
- Use profiling tools for performance analysis

---

*Developer Guide - Generated by AutoBot Assembly System*
"""
        
        return dev_guide
    
    async def _generate_changelog(self, generated_project: GeneratedProject, 
                                validation_result: Optional[ValidationResult],
                                project_analysis: Dict[str, Any]) -> str:
        """Generate changelog."""
        
        from datetime import datetime
        
        changelog = f"""# Changelog

All notable changes to {generated_project.project_name} will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - {datetime.now().strftime('%Y-%m-%d')}

### Added

- Initial project assembly by AutoBot Assembly System
- {generated_project.language.title()} {generated_project.project_type.value.replace('_', ' ')} structure
"""
        
        if project_analysis['functions']:
            changelog += f"- {len(project_analysis['functions'])} core functions\n"
        
        if project_analysis['classes']:
            changelog += f"- {len(project_analysis['classes'])} classes\n"
        
        if generated_project.dependencies:
            changelog += f"- {len(generated_project.dependencies)} dependencies integrated\n"
        
        if generated_project.build_commands:
            changelog += "- Build system configuration\n"
        
        if generated_project.test_commands:
            changelog += "- Test framework setup\n"
        
        changelog += """- Documentation generation
- Quality validation

### Notes

- This version was automatically assembled from multiple open-source components
- Manual review and testing recommended before production use

---

*Changelog maintained by AutoBot Assembly System*
"""
        
        return changelog
    
    async def _generate_license(self, generated_project: GeneratedProject, 
                              validation_result: Optional[ValidationResult],
                              project_analysis: Dict[str, Any]) -> str:
        """Generate license file."""
        
        from datetime import datetime
        
        # Default to MIT license for assembled projects
        license_content = f"""MIT License

Copyright (c) {datetime.now().year} AutoBot Assembly System

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

NOTICE: This project was assembled from multiple open-source components.
Please review the licenses of individual components for compliance requirements.

Component licenses may include but are not limited to:
- MIT License
- Apache License 2.0
- BSD Licenses
- GPL Licenses

For a complete list of component licenses, please refer to the project
documentation or contact the maintainers.
"""
        
        return license_content
    
    async def _write_documentation_file(self, project_path: Path, doc_type: DocType, content: str):
        """Write documentation content to appropriate file."""
        
        file_mapping = {
            DocType.README: "README.md",
            DocType.API_DOCS: "docs/API.md",
            DocType.USER_GUIDE: "docs/USER_GUIDE.md",
            DocType.DEVELOPER_GUIDE: "docs/DEVELOPER_GUIDE.md",
            DocType.CHANGELOG: "CHANGELOG.md",
            DocType.LICENSE: "LICENSE"
        }
        
        filename = file_mapping.get(doc_type, f"{doc_type.value}.md")
        file_path = project_path / filename
        
        # Create docs directory if needed
        if filename.startswith("docs/"):
            docs_dir = project_path / "docs"
            docs_dir.mkdir(exist_ok=True)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"Generated {filename}")
            
        except Exception as e:
            self.logger.error(f"Failed to write {filename}: {e}")


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
    
    doc_generator = DocumentationGenerator()
    
    print("Testing documentation generator...")
    print("Documentation generator is ready for use with real generated projects")


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())