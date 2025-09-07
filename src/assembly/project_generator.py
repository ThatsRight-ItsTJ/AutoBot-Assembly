"""
Project Generator

Final project structure generation and configuration for assembled components.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import shutil

from .code_integrator import IntegrationResult


class ProjectType(str, Enum):
    LIBRARY = "library"
    APPLICATION = "application"
    WEB_SERVICE = "web_service"
    CLI_TOOL = "cli_tool"
    GENERIC = "generic"


@dataclass
class ProjectStructure:
    project_type: ProjectType
    entry_points: List[str]
    source_directories: List[str]
    config_files: List[str]
    documentation_files: List[str]
    test_directories: List[str]
    build_files: List[str]


@dataclass
class GeneratedProject:
    project_name: str
    project_path: str
    project_type: ProjectType
    structure: ProjectStructure
    language: str
    dependencies: List[str]
    build_commands: List[str]
    run_commands: List[str]
    test_commands: List[str]
    documentation_url: Optional[str] = None


class ProjectGenerator:
    """Generate final project structure and configuration."""
    
    def __init__(self, output_base_dir: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # Set up output directory
        if output_base_dir:
            self.output_base_dir = Path(output_base_dir)
        else:
            self.output_base_dir = Path("generated_projects")
        
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Project templates by language
        self.project_templates = {
            'python': {
                'library': self._generate_python_library,
                'application': self._generate_python_application,
                'web_service': self._generate_python_web_service,
                'cli_tool': self._generate_python_cli_tool
            },
            'javascript': {
                'library': self._generate_javascript_library,
                'application': self._generate_javascript_application,
                'web_service': self._generate_javascript_web_service
            },
            'java': {
                'library': self._generate_java_library,
                'application': self._generate_java_application,
                'web_service': self._generate_java_web_service
            }
        }
    
    async def generate_project(self, 
                             integration_result: IntegrationResult,
                             project_name: str,
                             language: str,
                             project_type: Optional[ProjectType] = None) -> GeneratedProject:
        """
        Generate final project structure from integration result.
        
        Args:
            integration_result: Result from code integration
            project_name: Name for the generated project
            language: Programming language
            project_type: Type of project to generate
            
        Returns:
            GeneratedProject with complete project information
        """
        
        self.logger.info(f"Generating {language} project: {project_name}")
        
        # Auto-detect project type if not specified
        if project_type is None:
            project_type = self._detect_project_type(integration_result, language)
        
        # Create project directory
        project_path = self.output_base_dir / project_name
        if project_path.exists():
            shutil.rmtree(project_path)
        project_path.mkdir(parents=True)
        
        # Copy integrated files
        integration_path = Path(integration_result.integration_path)
        if integration_path.exists():
            self._copy_integration_files(integration_path, project_path)
        
        # Generate project-specific structure and files
        templates = self.project_templates.get(language.lower(), {})
        generator_func = templates.get(project_type.value, self._generate_generic_project)
        
        structure = await generator_func(project_path, integration_result)
        
        # Generate build and configuration files
        dependencies = await self._extract_dependencies(project_path, language)
        build_commands = self._generate_build_commands(language, project_type)
        run_commands = self._generate_run_commands(language, project_type, project_name)
        test_commands = self._generate_test_commands(language, project_type)
        
        # Generate project metadata
        await self._generate_project_metadata(project_path, project_name, language, project_type, dependencies)
        
        # Generate CI/CD configuration
        await self._generate_cicd_config(project_path, language, project_type)
        
        return GeneratedProject(
            project_name=project_name,
            project_path=str(project_path),
            project_type=project_type,
            structure=structure,
            language=language,
            dependencies=dependencies,
            build_commands=build_commands,
            run_commands=run_commands,
            test_commands=test_commands
        )
    
    def _detect_project_type(self, integration_result: IntegrationResult, language: str) -> ProjectType:
        """Auto-detect project type based on integrated files."""
        
        integrated_files = integration_result.integrated_files
        
        # Check for web service indicators
        web_indicators = ['app.py', 'server.py', 'main.py', 'index.js', 'server.js']
        if any(any(indicator in file for indicator in web_indicators) for file in integrated_files):
            return ProjectType.WEB_SERVICE
        
        # Check for CLI tool indicators
        cli_indicators = ['cli.py', 'command.py', 'main.py']
        if any(any(indicator in file for indicator in cli_indicators) for file in integrated_files):
            return ProjectType.CLI_TOOL
        
        # Check for library indicators
        lib_indicators = ['__init__.py', 'lib/', 'src/']
        if any(any(indicator in file for indicator in lib_indicators) for file in integrated_files):
            return ProjectType.LIBRARY
        
        # Default to application
        return ProjectType.APPLICATION
    
    def _copy_integration_files(self, source_path: Path, dest_path: Path):
        """Copy files from integration directory to project directory."""
        
        for item in source_path.iterdir():
            if item.is_file():
                shutil.copy2(item, dest_path / item.name)
            elif item.is_dir():
                shutil.copytree(item, dest_path / item.name, dirs_exist_ok=True)
    
    async def _generate_python_library(self, project_path: Path, integration_result: IntegrationResult) -> ProjectStructure:
        """Generate Python library project structure."""
        
        # Create standard library structure
        lib_name = project_path.name.replace('-', '_')
        src_dir = project_path / lib_name
        src_dir.mkdir(exist_ok=True)
        
        # Move source files to library directory
        src_path = project_path / "src"
        if src_path.exists():
            for item in src_path.iterdir():
                if item.is_file():
                    shutil.move(str(item), str(src_dir / item.name))
            src_path.rmdir()
        
        # Generate setup.py
        setup_content = f'''from setuptools import setup, find_packages

setup(
    name="{project_path.name}",
    version="0.1.0",
    description="Auto-generated library from AutoBot Assembly System",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        # Dependencies will be populated from requirements.txt
    ],
    author="AutoBot Assembly System",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
'''
        
        with open(project_path / "setup.py", 'w') as f:
            f.write(setup_content)
        
        # Generate __init__.py for the library
        init_content = f'"""Auto-generated library: {project_path.name}"""\n\n__version__ = "0.1.0"\n'
        with open(src_dir / "__init__.py", 'w') as f:
            f.write(init_content)
        
        # Create tests directory
        tests_dir = project_path / "tests"
        tests_dir.mkdir(exist_ok=True)
        with open(tests_dir / "__init__.py", 'w') as f:
            f.write("")
        
        return ProjectStructure(
            project_type=ProjectType.LIBRARY,
            entry_points=[f"{lib_name}/__init__.py"],
            source_directories=[lib_name],
            config_files=["setup.py", "requirements.txt"],
            documentation_files=["README.md"],
            test_directories=["tests"],
            build_files=["setup.py"]
        )
    
    async def _generate_python_application(self, project_path: Path, integration_result: IntegrationResult) -> ProjectStructure:
        """Generate Python application project structure."""
        
        # Ensure main.py exists
        main_file = project_path / "main.py"
        if not main_file.exists():
            main_content = '''#!/usr/bin/env python3
"""
Auto-generated application entry point
"""

def main():
    print("Application started successfully!")
    # TODO: Add your application logic here

if __name__ == "__main__":
    main()
'''
            with open(main_file, 'w') as f:
                f.write(main_content)
        
        return ProjectStructure(
            project_type=ProjectType.APPLICATION,
            entry_points=["main.py"],
            source_directories=["src"],
            config_files=["requirements.txt"],
            documentation_files=["README.md"],
            test_directories=["tests"],
            build_files=[]
        )
    
    async def _generate_python_web_service(self, project_path: Path, integration_result: IntegrationResult) -> ProjectStructure:
        """Generate Python web service project structure."""
        
        # Generate app.py if it doesn't exist
        app_file = project_path / "app.py"
        if not app_file.exists():
            app_content = '''#!/usr/bin/env python3
"""
Auto-generated web service
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return {"message": "Web service is running!", "status": "success"}

@app.route('/health')
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
'''
            with open(app_file, 'w') as f:
                f.write(app_content)
        
        # Generate Dockerfile
        dockerfile_content = '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
'''
        
        with open(project_path / "Dockerfile", 'w') as f:
            f.write(dockerfile_content)
        
        return ProjectStructure(
            project_type=ProjectType.WEB_SERVICE,
            entry_points=["app.py"],
            source_directories=["src"],
            config_files=["requirements.txt", "Dockerfile"],
            documentation_files=["README.md"],
            test_directories=["tests"],
            build_files=["Dockerfile"]
        )
    
    async def _generate_python_cli_tool(self, project_path: Path, integration_result: IntegrationResult) -> ProjectStructure:
        """Generate Python CLI tool project structure."""
        
        # Generate CLI entry point
        cli_file = project_path / "cli.py"
        if not cli_file.exists():
            cli_content = '''#!/usr/bin/env python3
"""
Auto-generated CLI tool
"""

import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Auto-generated CLI tool")
    parser.add_argument("--version", action="version", version="0.1.0")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        print("CLI tool started in verbose mode")
    
    print("CLI tool executed successfully!")
    # TODO: Add your CLI logic here

if __name__ == "__main__":
    main()
'''
            with open(cli_file, 'w') as f:
                f.write(cli_content)
        
        return ProjectStructure(
            project_type=ProjectType.CLI_TOOL,
            entry_points=["cli.py"],
            source_directories=["src"],
            config_files=["requirements.txt"],
            documentation_files=["README.md"],
            test_directories=["tests"],
            build_files=[]
        )
    
    async def _generate_javascript_library(self, project_path: Path, integration_result: IntegrationResult) -> ProjectStructure:
        """Generate JavaScript library project structure."""
        
        # Generate package.json if it doesn't exist
        package_json = project_path / "package.json"
        if not package_json.exists():
            package_data = {
                "name": project_path.name,
                "version": "0.1.0",
                "description": "Auto-generated library from AutoBot Assembly System",
                "main": "index.js",
                "scripts": {
                    "test": "jest",
                    "build": "webpack",
                    "start": "node index.js"
                },
                "keywords": ["autobot", "assembly"],
                "author": "AutoBot Assembly System",
                "license": "MIT"
            }
            
            with open(package_json, 'w') as f:
                json.dump(package_data, f, indent=2)
        
        return ProjectStructure(
            project_type=ProjectType.LIBRARY,
            entry_points=["index.js"],
            source_directories=["src"],
            config_files=["package.json"],
            documentation_files=["README.md"],
            test_directories=["tests"],
            build_files=["package.json"]
        )
    
    async def _generate_javascript_application(self, project_path: Path, integration_result: IntegrationResult) -> ProjectStructure:
        """Generate JavaScript application project structure."""
        
        return await self._generate_javascript_library(project_path, integration_result)
    
    async def _generate_javascript_web_service(self, project_path: Path, integration_result: IntegrationResult) -> ProjectStructure:
        """Generate JavaScript web service project structure."""
        
        # Generate Express.js server if needed
        server_file = project_path / "server.js"
        if not server_file.exists():
            server_content = '''const express = require('express');
const app = express();
const port = process.env.PORT || 3000;

app.use(express.json());

app.get('/', (req, res) => {
    res.json({ message: 'Web service is running!', status: 'success' });
});

app.get('/health', (req, res) => {
    res.json({ status: 'healthy' });
});

app.listen(port, () => {
    console.log(`Server running on port ${port}`);
});
'''
            with open(server_file, 'w') as f:
                f.write(server_content)
        
        return ProjectStructure(
            project_type=ProjectType.WEB_SERVICE,
            entry_points=["server.js"],
            source_directories=["src"],
            config_files=["package.json"],
            documentation_files=["README.md"],
            test_directories=["tests"],
            build_files=["package.json"]
        )
    
    async def _generate_java_library(self, project_path: Path, integration_result: IntegrationResult) -> ProjectStructure:
        """Generate Java library project structure."""
        
        # Generate pom.xml for Maven
        pom_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <groupId>com.autobot.assembly</groupId>
    <artifactId>{project_path.name}</artifactId>
    <version>0.1.0</version>
    <packaging>jar</packaging>
    
    <name>{project_path.name}</name>
    <description>Auto-generated library from AutoBot Assembly System</description>
    
    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>
    
    <dependencies>
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
'''
        
        with open(project_path / "pom.xml", 'w') as f:
            f.write(pom_content)
        
        return ProjectStructure(
            project_type=ProjectType.LIBRARY,
            entry_points=["src/main/java"],
            source_directories=["src/main/java"],
            config_files=["pom.xml"],
            documentation_files=["README.md"],
            test_directories=["src/test/java"],
            build_files=["pom.xml"]
        )
    
    async def _generate_java_application(self, project_path: Path, integration_result: IntegrationResult) -> ProjectStructure:
        """Generate Java application project structure."""
        
        return await self._generate_java_library(project_path, integration_result)
    
    async def _generate_java_web_service(self, project_path: Path, integration_result: IntegrationResult) -> ProjectStructure:
        """Generate Java web service project structure."""
        
        return await self._generate_java_library(project_path, integration_result)
    
    async def _generate_generic_project(self, project_path: Path, integration_result: IntegrationResult) -> ProjectStructure:
        """Generate generic project structure."""
        
        return ProjectStructure(
            project_type=ProjectType.GENERIC,
            entry_points=["main"],
            source_directories=["src"],
            config_files=[],
            documentation_files=["README.md"],
            test_directories=["tests"],
            build_files=[]
        )
    
    async def _extract_dependencies(self, project_path: Path, language: str) -> List[str]:
        """Extract dependencies from project files."""
        
        dependencies = []
        
        if language.lower() == 'python':
            # Check requirements.txt
            req_file = project_path / "requirements.txt"
            if req_file.exists():
                with open(req_file, 'r') as f:
                    dependencies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        elif language.lower() == 'javascript':
            # Check package.json
            package_file = project_path / "package.json"
            if package_file.exists():
                with open(package_file, 'r') as f:
                    package_data = json.load(f)
                    deps = package_data.get('dependencies', {})
                    dependencies = [f"{name}@{version}" for name, version in deps.items()]
        
        elif language.lower() == 'java':
            # Check pom.xml (simplified)
            pom_file = project_path / "pom.xml"
            if pom_file.exists():
                dependencies = ["Maven dependencies (see pom.xml)"]
        
        return dependencies
    
    def _generate_build_commands(self, language: str, project_type: ProjectType) -> List[str]:
        """Generate build commands for the project."""
        
        commands = []
        
        if language.lower() == 'python':
            if project_type == ProjectType.LIBRARY:
                commands = ["python setup.py build", "python setup.py sdist bdist_wheel"]
            else:
                commands = ["pip install -r requirements.txt"]
        
        elif language.lower() == 'javascript':
            commands = ["npm install", "npm run build"]
        
        elif language.lower() == 'java':
            commands = ["mvn compile", "mvn package"]
        
        return commands
    
    def _generate_run_commands(self, language: str, project_type: ProjectType, project_name: str) -> List[str]:
        """Generate run commands for the project."""
        
        commands = []
        
        if language.lower() == 'python':
            if project_type == ProjectType.WEB_SERVICE:
                commands = ["python app.py"]
            elif project_type == ProjectType.CLI_TOOL:
                commands = ["python cli.py"]
            else:
                commands = ["python main.py"]
        
        elif language.lower() == 'javascript':
            if project_type == ProjectType.WEB_SERVICE:
                commands = ["node server.js"]
            else:
                commands = ["node index.js"]
        
        elif language.lower() == 'java':
            commands = [f"java -jar target/{project_name}-0.1.0.jar"]
        
        return commands
    
    def _generate_test_commands(self, language: str, project_type: ProjectType) -> List[str]:
        """Generate test commands for the project."""
        
        commands = []
        
        if language.lower() == 'python':
            commands = ["python -m pytest tests/", "python -m unittest discover tests"]
        
        elif language.lower() == 'javascript':
            commands = ["npm test", "jest"]
        
        elif language.lower() == 'java':
            commands = ["mvn test"]
        
        return commands
    
    async def _generate_project_metadata(self, project_path: Path, project_name: str, 
                                       language: str, project_type: ProjectType, 
                                       dependencies: List[str]):
        """Generate project metadata file."""
        
        metadata = {
            "name": project_name,
            "language": language,
            "project_type": project_type.value,
            "generated_by": "AutoBot Assembly System",
            "version": "0.1.0",
            "dependencies": dependencies,
            "structure": {
                "entry_points": ["main.py" if language == "python" else "index.js"],
                "source_directories": ["src"],
                "test_directories": ["tests"]
            }
        }
        
        with open(project_path / ".autobot-metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
    
    async def _generate_cicd_config(self, project_path: Path, language: str, project_type: ProjectType):
        """Generate CI/CD configuration files."""
        
        # Generate GitHub Actions workflow
        github_dir = project_path / ".github" / "workflows"
        github_dir.mkdir(parents=True, exist_ok=True)
        
        if language.lower() == 'python':
            workflow_content = '''name: Python CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
'''
        
        elif language.lower() == 'javascript':
            workflow_content = '''name: Node.js CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [16.x, 18.x, 20.x]

    steps:
    - uses: actions/checkout@v3
    
    - name: Use Node.js ${{ matrix.node-version }}
      uses: actions/setup-node@v3
      with:
        node-version: ${{ matrix.node-version }}
        cache: 'npm'
    
    - run: npm ci
    - run: npm run build --if-present
    - run: npm test
'''
        
        else:
            workflow_content = '''name: Generic CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    - name: Run tests
      run: echo "Add your test commands here"
'''
        
        with open(github_dir / "ci.yml", 'w') as f:
            f.write(workflow_content)


# Example usage
async def main():
    from .repository_cloner import RepositoryCloner
    from .file_extractor import FileExtractor
    from .code_integrator import CodeIntegrator
    from ..search.tier1_packages import PackageResult
    from datetime import datetime
    
    # Test complete workflow
    cloner = RepositoryCloner()
    extractor = FileExtractor()
    integrator = CodeIntegrator()
    generator = ProjectGenerator()
    
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
    
    print("Testing complete project generation workflow...")
    
    # Clone repositories
    clone_results = await cloner.clone_repositories(test_repos)
    
    # Extract files
    extraction_results = await extractor.extract_files(
        clone_results, 
        language="python",
        extraction_criteria={'max_files_per_repo': 5}
    )
    
    # Integrate components
    integration_result = await integrator.integrate_components(
        extraction_results, 
        language="python",
        project_name="test_integration"
    )
    
    # Generate final project
    generated_project = await generator.generate_project(
        integration_result,
        project_name="my_generated_project",
        language="python",
        project_type=ProjectType.APPLICATION
    )
    
    # Print results
    print(f"\nGenerated Project:")
    print(f"  Name: {generated_project.project_name}")
    print(f"  Type: {generated_project.project_type.value}")
    print(f"  Language: {generated_project.language}")
    print(f"  Path: {generated_project.project_path}")
    print(f"  Dependencies: {len(generated_project.dependencies)}")
    print(f"  Build commands: {generated_project.build_commands}")
    print(f"  Run commands: {generated_project.run_commands}")
    print(f"  Test commands: {generated_project.test_commands}")
    
    # Cleanup
    await cloner.cleanup_clones(clone_results)
    print("Workflow completed successfully!")


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())