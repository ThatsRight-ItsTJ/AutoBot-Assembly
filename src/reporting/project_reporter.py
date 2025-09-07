#!/usr/bin/env python3
"""
Project Reporter

Generates comprehensive reports for assembled projects including:
- File structure outline
- Repository files analysis
- File purposes and descriptions
- Development plan recommendations
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class FileInfo:
    """Information about a single file in the project."""
    path: str
    size: int
    purpose: str
    source_repo: Optional[str] = None
    language: Optional[str] = None
    description: Optional[str] = None


@dataclass
class RepositoryInfo:
    """Information about a source repository."""
    name: str
    url: str
    files_copied: List[str]
    purpose: str
    license: Optional[str] = None


@dataclass
class ProjectReport:
    """Complete project assembly report."""
    project_name: str
    generated_at: str
    total_files: int
    total_size: int
    file_structure: Dict[str, Any]
    files: List[FileInfo]
    repositories: List[RepositoryInfo]
    development_plan: List[str]
    next_steps: List[str]
    technologies: List[str]


class ProjectReporter:
    """Generates comprehensive project reports."""
    
    def __init__(self):
        self.language_extensions = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'React JSX',
            '.tsx': 'React TSX',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.json': 'JSON',
            '.md': 'Markdown',
            '.yml': 'YAML',
            '.yaml': 'YAML',
            '.toml': 'TOML',
            '.ini': 'INI',
            '.env': 'Environment',
            '.sh': 'Shell Script',
            '.bat': 'Batch Script',
            '.dockerfile': 'Docker',
            '.go': 'Go',
            '.rs': 'Rust',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.swift': 'Swift',
            '.kt': 'Kotlin'
        }
        
        self.file_purposes = {
            'main.py': 'Main application entry point',
            'app.py': 'Flask/FastAPI application entry point',
            'server.js': 'Node.js server entry point',
            'index.js': 'JavaScript application entry point',
            'index.html': 'Main HTML page',
            'package.json': 'Node.js dependencies and scripts',
            'requirements.txt': 'Python dependencies',
            'Dockerfile': 'Docker container configuration',
            'docker-compose.yml': 'Docker multi-container setup',
            'README.md': 'Project documentation',
            'LICENSE': 'Project license',
            '.gitignore': 'Git ignore patterns',
            'config.py': 'Application configuration',
            'settings.py': 'Django settings',
            'manage.py': 'Django management script',
            'webpack.config.js': 'Webpack build configuration',
            'tsconfig.json': 'TypeScript configuration',
            'babel.config.js': 'Babel transpiler configuration',
            '.env': 'Environment variables',
            'Makefile': 'Build automation',
            'setup.py': 'Python package setup',
            'pyproject.toml': 'Python project configuration'
        }
    
    def analyze_project(self, project_path: str, repositories: List[Dict] = None) -> ProjectReport:
        """Analyze a project directory and generate a comprehensive report."""
        project_path = Path(project_path)
        project_name = project_path.name
        
        # Analyze file structure
        file_structure = self._build_file_structure(project_path)
        files = self._analyze_files(project_path)
        
        # Process repository information
        repo_info = self._process_repositories(repositories or [])
        
        # Generate development recommendations
        technologies = self._identify_technologies(files)
        development_plan = self._generate_development_plan(files, technologies)
        next_steps = self._generate_next_steps(files, technologies)
        
        # Calculate totals
        total_files = len(files)
        total_size = sum(f.size for f in files)
        
        return ProjectReport(
            project_name=project_name,
            generated_at=datetime.now().isoformat(),
            total_files=total_files,
            total_size=total_size,
            file_structure=file_structure,
            files=files,
            repositories=repo_info,
            development_plan=development_plan,
            next_steps=next_steps,
            technologies=technologies
        )
    
    def _build_file_structure(self, project_path: Path) -> Dict[str, Any]:
        """Build a hierarchical file structure representation."""
        def build_tree(path: Path) -> Dict[str, Any]:
            if path.is_file():
                return {
                    'type': 'file',
                    'size': path.stat().st_size,
                    'extension': path.suffix
                }
            elif path.is_dir():
                children = {}
                try:
                    for child in sorted(path.iterdir()):
                        if not child.name.startswith('.') or child.name in ['.env', '.gitignore']:
                            children[child.name] = build_tree(child)
                except PermissionError:
                    pass
                return {
                    'type': 'directory',
                    'children': children
                }
            return {}
        
        return build_tree(project_path)
    
    def _analyze_files(self, project_path: Path) -> List[FileInfo]:
        """Analyze all files in the project."""
        files = []
        
        for file_path in project_path.rglob('*'):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                relative_path = file_path.relative_to(project_path)
                size = file_path.stat().st_size
                language = self._detect_language(file_path)
                purpose = self._determine_purpose(file_path)
                description = self._generate_description(file_path, language)
                
                files.append(FileInfo(
                    path=str(relative_path),
                    size=size,
                    purpose=purpose,
                    language=language,
                    description=description
                ))
        
        return files
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored in the report."""
        ignore_patterns = [
            '__pycache__',
            '.pyc',
            'node_modules',
            '.git',
            '.DS_Store',
            'Thumbs.db'
        ]
        
        path_str = str(file_path)
        return any(pattern in path_str for pattern in ignore_patterns)
    
    def _detect_language(self, file_path: Path) -> Optional[str]:
        """Detect programming language from file extension."""
        return self.language_extensions.get(file_path.suffix.lower())
    
    def _determine_purpose(self, file_path: Path) -> str:
        """Determine the purpose of a file based on its name and location."""
        filename = file_path.name.lower()
        
        # Check exact filename matches
        if filename in self.file_purposes:
            return self.file_purposes[filename]
        
        # Check by directory and extension
        parent_dir = file_path.parent.name.lower()
        extension = file_path.suffix.lower()
        
        # Directory-based purposes
        if parent_dir == 'tests' or 'test' in filename:
            return 'Test file'
        elif parent_dir == 'docs':
            return 'Documentation'
        elif parent_dir == 'static':
            return 'Static asset'
        elif parent_dir == 'templates':
            return 'Template file'
        elif parent_dir == 'migrations':
            return 'Database migration'
        elif parent_dir == 'components':
            return 'UI component'
        elif parent_dir == 'utils' or parent_dir == 'helpers':
            return 'Utility function'
        elif parent_dir == 'models':
            return 'Data model'
        elif parent_dir == 'views':
            return 'View/Controller'
        elif parent_dir == 'api':
            return 'API endpoint'
        
        # Extension-based purposes
        if extension == '.md':
            return 'Documentation'
        elif extension in ['.css', '.scss']:
            return 'Stylesheet'
        elif extension in ['.js', '.ts']:
            return 'JavaScript module'
        elif extension == '.py':
            return 'Python module'
        elif extension in ['.html', '.htm']:
            return 'HTML template'
        elif extension in ['.json', '.yml', '.yaml']:
            return 'Configuration file'
        
        return 'Source file'
    
    def _generate_description(self, file_path: Path, language: Optional[str]) -> Optional[str]:
        """Generate a description for a file based on its content and context."""
        try:
            if file_path.stat().st_size > 10000:  # Skip large files
                return f"Large {language or 'file'} ({file_path.stat().st_size} bytes)"
            
            # Try to read first few lines for context
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_lines = [f.readline().strip() for _ in range(3)]
                    first_lines = [line for line in first_lines if line]
                    
                    if first_lines:
                        first_line = first_lines[0]
                        
                        # Look for docstrings or comments
                        if first_line.startswith('"""') or first_line.startswith("'''"):
                            return f"Python module with docstring: {first_line[:50]}..."
                        elif first_line.startswith('//') or first_line.startswith('/*'):
                            return f"JavaScript module with comment: {first_line[:50]}..."
                        elif first_line.startswith('#'):
                            return f"Script with comment: {first_line[:50]}..."
                        elif 'import' in first_line or 'from' in first_line:
                            return f"Module with imports: {first_line[:50]}..."
                        elif 'function' in first_line or 'def' in first_line:
                            return f"Function definition: {first_line[:50]}..."
                        elif 'class' in first_line:
                            return f"Class definition: {first_line[:50]}..."
            except (UnicodeDecodeError, PermissionError):
                pass
                
        except (OSError, PermissionError):
            pass
        
        return None
    
    def _process_repositories(self, repositories: List[Dict]) -> List[RepositoryInfo]:
        """Process repository information."""
        repo_info = []
        
        for repo in repositories:
            repo_info.append(RepositoryInfo(
                name=repo.get('name', 'Unknown'),
                url=repo.get('url', ''),
                files_copied=repo.get('files_copied', []),
                purpose=repo.get('purpose', 'Source repository'),
                license=repo.get('license')
            ))
        
        return repo_info
    
    def _identify_technologies(self, files: List[FileInfo]) -> List[str]:
        """Identify technologies used in the project."""
        technologies = set()
        
        for file in files:
            # Language-based technologies
            if file.language:
                technologies.add(file.language)
            
            # Framework detection
            filename = file.path.lower()
            if 'package.json' in filename:
                technologies.add('Node.js')
            elif 'requirements.txt' in filename:
                technologies.add('Python')
            elif 'dockerfile' in filename:
                technologies.add('Docker')
            elif 'docker-compose' in filename:
                technologies.add('Docker Compose')
            elif filename.endswith('.jsx') or filename.endswith('.tsx'):
                technologies.add('React')
            elif 'webpack' in filename:
                technologies.add('Webpack')
            elif 'babel' in filename:
                technologies.add('Babel')
            elif 'tsconfig' in filename:
                technologies.add('TypeScript')
            elif 'manage.py' in filename:
                technologies.add('Django')
            elif 'app.py' in filename or 'flask' in filename:
                technologies.add('Flask')
            elif 'fastapi' in filename:
                technologies.add('FastAPI')
        
        return sorted(list(technologies))
    
    def _generate_development_plan(self, files: List[FileInfo], technologies: List[str]) -> List[str]:
        """Generate development plan recommendations."""
        plan = []
        
        # Basic setup steps
        plan.append("1. **Environment Setup**")
        if 'Python' in technologies:
            plan.append("   - Set up Python virtual environment")
            plan.append("   - Install dependencies: `pip install -r requirements.txt`")
        if 'Node.js' in technologies:
            plan.append("   - Install Node.js dependencies: `npm install`")
        if 'Docker' in technologies:
            plan.append("   - Build Docker images: `docker-compose build`")
        
        # Configuration steps
        plan.append("2. **Configuration**")
        env_files = [f for f in files if '.env' in f.path]
        if env_files:
            plan.append("   - Configure environment variables in .env file")
        
        config_files = [f for f in files if 'config' in f.path.lower()]
        if config_files:
            plan.append("   - Review and update configuration files")
        
        # Database setup
        if any('model' in f.path.lower() or 'migration' in f.path.lower() for f in files):
            plan.append("3. **Database Setup**")
            plan.append("   - Set up database connection")
            plan.append("   - Run migrations if applicable")
        
        # Testing
        test_files = [f for f in files if 'test' in f.path.lower()]
        if test_files:
            plan.append("4. **Testing**")
            plan.append("   - Run existing tests to verify setup")
            plan.append("   - Add additional test coverage as needed")
        
        # Deployment
        plan.append("5. **Deployment Preparation**")
        if 'Docker' in technologies:
            plan.append("   - Test Docker container deployment")
        plan.append("   - Set up production environment variables")
        plan.append("   - Configure logging and monitoring")
        
        return plan
    
    def _generate_next_steps(self, files: List[FileInfo], technologies: List[str]) -> List[str]:
        """Generate next steps recommendations."""
        steps = []
        
        # Missing essential files
        essential_files = ['README.md', 'LICENSE', '.gitignore']
        existing_files = [f.path for f in files]
        
        missing_files = [f for f in essential_files if not any(f in path for path in existing_files)]
        if missing_files:
            steps.append(f"**Add missing essential files**: {', '.join(missing_files)}")
        
        # Security considerations
        if any('.env' in f.path for f in files):
            steps.append("**Security**: Ensure .env file is in .gitignore and not committed to version control")
        
        # Documentation
        if not any('README' in f.path for f in files):
            steps.append("**Documentation**: Create comprehensive README with setup and usage instructions")
        
        # Testing
        test_files = [f for f in files if 'test' in f.path.lower()]
        if not test_files:
            steps.append("**Testing**: Add unit tests and integration tests")
        
        # CI/CD
        ci_files = [f for f in files if any(ci in f.path for ci in ['.github', '.gitlab', 'jenkins', 'travis'])]
        if not ci_files:
            steps.append("**CI/CD**: Set up continuous integration and deployment pipeline")
        
        # Monitoring
        steps.append("**Monitoring**: Add logging, error tracking, and performance monitoring")
        
        # Code quality
        steps.append("**Code Quality**: Set up linting, formatting, and code quality checks")
        
        return steps
    
    def generate_markdown_report(self, report: ProjectReport) -> str:
        """Generate a markdown report from the project analysis."""
        md = []
        
        # Header
        md.append(f"# {report.project_name} - Project Assembly Report")
        md.append("")
        md.append(f"**Generated:** {report.generated_at}")
        md.append(f"**Total Files:** {report.total_files}")
        md.append(f"**Total Size:** {self._format_size(report.total_size)}")
        md.append("")
        
        # Technologies
        if report.technologies:
            md.append("## 🛠️ Technologies Used")
            md.append("")
            for tech in report.technologies:
                md.append(f"- {tech}")
            md.append("")
        
        # File Structure
        md.append("## 📁 File Structure")
        md.append("")
        md.append("```")
        md.append(self._format_file_structure(report.file_structure, report.project_name))
        md.append("```")
        md.append("")
        
        # Repository Sources
        if report.repositories:
            md.append("## 📦 Source Repositories")
            md.append("")
            for repo in report.repositories:
                md.append(f"### {repo.name}")
                md.append(f"- **URL:** {repo.url}")
                md.append(f"- **Purpose:** {repo.purpose}")
                if repo.license:
                    md.append(f"- **License:** {repo.license}")
                if repo.files_copied:
                    md.append("- **Files Copied:**")
                    for file in repo.files_copied:
                        md.append(f"  - {file}")
                md.append("")
        
        # File Analysis
        md.append("## 📄 File Analysis")
        md.append("")
        md.append("| File | Size | Language | Purpose |")
        md.append("|------|------|----------|---------|")
        
        for file in sorted(report.files, key=lambda x: x.path):
            size = self._format_size(file.size)
            language = file.language or "N/A"
            purpose = file.purpose
            md.append(f"| {file.path} | {size} | {language} | {purpose} |")
        
        md.append("")
        
        # Development Plan
        if report.development_plan:
            md.append("## 🚀 Development Plan")
            md.append("")
            for step in report.development_plan:
                md.append(step)
            md.append("")
        
        # Next Steps
        if report.next_steps:
            md.append("## ✅ Next Steps")
            md.append("")
            for i, step in enumerate(report.next_steps, 1):
                md.append(f"{i}. {step}")
            md.append("")
        
        # Footer
        md.append("---")
        md.append("*Report generated by AutoBot Assembly System*")
        
        return "\n".join(md)
    
    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def _format_file_structure(self, structure: Dict[str, Any], name: str, indent: int = 0) -> str:
        """Format file structure as a tree."""
        lines = []
        prefix = "  " * indent
        
        if indent == 0:
            lines.append(f"{name}/")
            indent += 1
            prefix = "  " * indent
        
        if structure.get('type') == 'directory':
            children = structure.get('children', {})
            for child_name, child_data in sorted(children.items()):
                if child_data.get('type') == 'directory':
                    lines.append(f"{prefix}{child_name}/")
                    lines.append(self._format_file_structure(child_data, child_name, indent + 1))
                else:
                    size = self._format_size(child_data.get('size', 0))
                    lines.append(f"{prefix}{child_name} ({size})")
        
        return "\n".join(filter(None, lines))
    
    def save_report(self, report: ProjectReport, output_path: str, format: str = 'markdown') -> None:
        """Save the report to a file."""
        output_path = Path(output_path)
        
        if format == 'markdown':
            content = self.generate_markdown_report(report)
            output_path = output_path.with_suffix('.md')
        elif format == 'json':
            content = json.dumps(asdict(report), indent=2, default=str)
            output_path = output_path.with_suffix('.json')
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)