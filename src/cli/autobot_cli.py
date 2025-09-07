"""
AutoBot CLI

Interactive command-line interface for the AutoBot Assembly System.
"""

import asyncio
import logging
import sys
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import argparse
import json
import time

# Rich for beautiful CLI output
try:
    from rich.console import Console
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.tree import Tree
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None

from ..orchestration.project_analyzer import ProjectAnalyzer
from ..orchestration.search_orchestrator import SearchOrchestrator
from ..analysis.unified_scorer import UnifiedScorer
from ..compatibility.compatibility_matrix import CompatibilityMatrix
from ..assembly.repository_cloner import RepositoryCloner
from ..assembly.file_extractor import FileExtractor
from ..assembly.code_integrator import CodeIntegrator
from ..assembly.project_generator import ProjectGenerator, ProjectType
from ..qa.integration_tester import IntegrationTester
from ..qa.quality_validator import QualityValidator
from ..qa.documentation_generator import DocumentationGenerator, DocType
from .progress_reporter import ProgressReporter, ProgressStage
from .config_manager import ConfigManager


class CLIMode(str, Enum):
    INTERACTIVE = "interactive"
    BATCH = "batch"
    WIZARD = "wizard"


@dataclass
class CLIConfig:
    mode: CLIMode = CLIMode.INTERACTIVE
    output_dir: str = "./autobot_output"
    verbose: bool = False
    skip_tests: bool = False
    skip_docs: bool = False
    project_type: Optional[str] = None
    language: Optional[str] = None
    max_repos: int = 10
    timeout: int = 300


class AutoBotCLI:
    """Interactive command-line interface for AutoBot Assembly System."""
    
    def __init__(self, config: Optional[CLIConfig] = None):
        self.config = config or CLIConfig()
        self.console = Console() if RICH_AVAILABLE else None
        self.progress_reporter = ProgressReporter(self.console)
        self.config_manager = ConfigManager()
        self.logger = logging.getLogger(__name__)
        
        # Initialize core components
        self.project_analyzer = ProjectAnalyzer()
        self.search_orchestrator = SearchOrchestrator()
        self.unified_scorer = UnifiedScorer()
        self.compatibility_matrix = CompatibilityMatrix()
        self.repository_cloner = RepositoryCloner()
        self.file_extractor = FileExtractor()
        self.code_integrator = CodeIntegrator()
        self.project_generator = ProjectGenerator()
        self.integration_tester = IntegrationTester()
        self.quality_validator = QualityValidator()
        self.documentation_generator = DocumentationGenerator()
        
        # CLI state
        self.current_session = None
        self.last_results = {}
    
    def print(self, message: str, style: Optional[str] = None):
        """Print message with optional styling."""
        if self.console and RICH_AVAILABLE:
            self.console.print(message, style=style)
        else:
            print(message)
    
    def print_panel(self, content: str, title: Optional[str] = None, style: str = "blue"):
        """Print content in a panel."""
        if self.console and RICH_AVAILABLE:
            self.console.print(Panel(content, title=title, border_style=style))
        else:
            if title:
                print(f"\n=== {title} ===")
            print(content)
            print("=" * (len(title) + 8) if title else "")
    
    def prompt(self, message: str, default: Optional[str] = None) -> str:
        """Prompt user for input."""
        if self.console and RICH_AVAILABLE:
            return Prompt.ask(message, default=default)
        else:
            prompt_text = f"{message}"
            if default:
                prompt_text += f" [{default}]"
            prompt_text += ": "
            
            response = input(prompt_text).strip()
            return response if response else (default or "")
    
    def confirm(self, message: str, default: bool = True) -> bool:
        """Ask for confirmation."""
        if self.console and RICH_AVAILABLE:
            return Confirm.ask(message, default=default)
        else:
            default_text = "Y/n" if default else "y/N"
            response = input(f"{message} [{default_text}]: ").strip().lower()
            
            if not response:
                return default
            return response.startswith('y')
    
    async def run(self, prompt_text: Optional[str] = None):
        """Main CLI entry point."""
        
        # Print welcome banner
        self.print_welcome()
        
        # Load user configuration
        user_config = self.config_manager.load_config()
        
        try:
            if self.config.mode == CLIMode.INTERACTIVE:
                await self.run_interactive_mode(prompt_text)
            elif self.config.mode == CLIMode.WIZARD:
                await self.run_wizard_mode()
            elif self.config.mode == CLIMode.BATCH:
                await self.run_batch_mode(prompt_text)
            else:
                self.print("Unknown CLI mode", style="red")
                return False
                
        except KeyboardInterrupt:
            self.print("\n\n👋 Goodbye! Thanks for using AutoBot Assembly System!", style="yellow")
            return False
        except Exception as e:
            self.print(f"\n❌ An error occurred: {e}", style="red")
            if self.config.verbose:
                import traceback
                self.print(traceback.format_exc(), style="dim red")
            return False
        
        return True
    
    def print_welcome(self):
        """Print welcome banner."""
        
        welcome_text = """
🤖 AutoBot Assembly System - CLI Interface

Transform your ideas into working code with AI-powered repository assembly!

Features:
• 🔍 Intelligent component discovery across multiple ecosystems
• 🔧 Automated code integration and project generation  
• 🧪 Comprehensive quality assurance and testing
• 📚 Professional documentation generation
• 🚀 Production-ready output with CI/CD pipelines

Ready to build something amazing? Let's get started!
"""
        
        self.print_panel(welcome_text.strip(), title="Welcome to AutoBot", style="green")
    
    async def run_interactive_mode(self, initial_prompt: Optional[str] = None):
        """Run interactive mode with continuous prompts."""
        
        self.print("\n🎯 Interactive Mode - Enter your project ideas and I'll build them for you!")
        self.print("Type 'help' for commands, 'quit' to exit\n")
        
        while True:
            try:
                if initial_prompt:
                    prompt_text = initial_prompt
                    initial_prompt = None  # Only use initial prompt once
                else:
                    prompt_text = self.prompt("\n💡 What would you like to build?")
                
                if not prompt_text:
                    continue
                
                # Handle special commands
                if prompt_text.lower() in ['quit', 'exit', 'q']:
                    break
                elif prompt_text.lower() in ['help', 'h']:
                    self.print_help()
                    continue
                elif prompt_text.lower() in ['config', 'settings']:
                    await self.configure_settings()
                    continue
                elif prompt_text.lower() in ['status', 'last']:
                    self.print_last_results()
                    continue
                
                # Process the prompt
                await self.process_prompt(prompt_text)
                
            except KeyboardInterrupt:
                if self.confirm("\n\nDo you want to exit AutoBot?", default=False):
                    break
                else:
                    continue
    
    async def run_wizard_mode(self):
        """Run guided wizard mode."""
        
        self.print_panel("🧙 Wizard Mode - I'll guide you through creating your project step by step!", 
                        title="Project Creation Wizard", style="magenta")
        
        # Step 1: Project Description
        self.print("\n📝 Step 1: Project Description")
        prompt_text = self.prompt("Describe what you want to build")
        
        if not prompt_text:
            self.print("❌ Project description is required", style="red")
            return
        
        # Step 2: Project Type
        self.print("\n🏗️ Step 2: Project Type")
        project_types = [
            ("1", "Application - Standalone executable program"),
            ("2", "Library - Reusable code package"),
            ("3", "Web Service - HTTP API or web server"),
            ("4", "CLI Tool - Command-line utility"),
            ("5", "Auto-detect - Let AutoBot decide")
        ]
        
        for option, description in project_types:
            self.print(f"  {option}. {description}")
        
        type_choice = self.prompt("Choose project type", default="5")
        
        # Step 3: Programming Language
        self.print("\n💻 Step 3: Programming Language")
        languages = [
            ("1", "Python - Versatile and beginner-friendly"),
            ("2", "JavaScript - Web and Node.js development"),
            ("3", "Java - Enterprise and cross-platform"),
            ("4", "Auto-detect - Let AutoBot decide")
        ]
        
        for option, description in languages:
            self.print(f"  {option}. {description}")
        
        lang_choice = self.prompt("Choose programming language", default="4")
        
        # Step 4: Output Directory
        self.print("\n📁 Step 4: Output Location")
        output_dir = self.prompt("Where should I create your project?", default="./my_autobot_project")
        
        # Step 5: Additional Options
        self.print("\n⚙️ Step 5: Additional Options")
        skip_tests = not self.confirm("Include automated testing?", default=True)
        skip_docs = not self.confirm("Generate documentation?", default=True)
        
        # Update configuration
        self.config.output_dir = output_dir
        self.config.skip_tests = skip_tests
        self.config.skip_docs = skip_docs
        
        if type_choice != "5":
            type_mapping = {"1": "application", "2": "library", "3": "web_service", "4": "cli_tool"}
            self.config.project_type = type_mapping.get(type_choice)
        
        if lang_choice != "4":
            lang_mapping = {"1": "python", "2": "javascript", "3": "java"}
            self.config.language = lang_mapping.get(lang_choice)
        
        # Confirmation
        self.print("\n✅ Configuration Summary:")
        self.print(f"  Project: {prompt_text}")
        self.print(f"  Type: {self.config.project_type or 'Auto-detect'}")
        self.print(f"  Language: {self.config.language or 'Auto-detect'}")
        self.print(f"  Output: {self.config.output_dir}")
        self.print(f"  Testing: {'Yes' if not self.config.skip_tests else 'No'}")
        self.print(f"  Documentation: {'Yes' if not self.config.skip_docs else 'No'}")
        
        if self.confirm("\nProceed with project creation?", default=True):
            await self.process_prompt(prompt_text)
        else:
            self.print("❌ Project creation cancelled", style="yellow")
    
    async def run_batch_mode(self, prompt_text: Optional[str]):
        """Run batch mode for automated processing."""
        
        if not prompt_text:
            self.print("❌ Batch mode requires a prompt text", style="red")
            return
        
        self.print_panel(f"🔄 Batch Mode - Processing: {prompt_text}", 
                        title="Automated Processing", style="blue")
        
        await self.process_prompt(prompt_text)
    
    async def process_prompt(self, prompt_text: str):
        """Process a user prompt and generate project."""
        
        session_id = f"cli_{int(time.time())}"
        self.current_session = session_id
        
        try:
            # Create output directory
            output_path = Path(self.config.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Start progress tracking
            await self.progress_reporter.start_session(session_id, "AutoBot Assembly")
            
            # Phase 1: Analyze prompt
            await self.progress_reporter.update_stage(ProgressStage.ANALYZING)
            self.print("\n🔍 Phase 1: Analyzing your requirements...")
            
            analysis_result = await self.project_analyzer.analyze_prompt(prompt_text)
            
            if self.config.verbose:
                self.print_analysis_results(analysis_result)
            
            # Phase 2: Search for components
            await self.progress_reporter.update_stage(ProgressStage.SEARCHING)
            self.print("\n🔎 Phase 2: Searching for components...")
            
            search_results = await self.search_orchestrator.orchestrate_search(
                analysis_result, max_results_per_tier=self.config.max_repos
            )
            
            if self.config.verbose:
                self.print_search_results(search_results)
            
            # Phase 3: Analyze and score components
            await self.progress_reporter.update_stage(ProgressStage.ANALYZING)
            self.print("\n📊 Phase 3: Analyzing component quality...")
            
            # For CLI, we'll use a simplified analysis approach
            scored_results = []
            for result in search_results.all_results[:self.config.max_repos]:
                # Simple scoring based on available data
                score = min(result.quality_score * 1.2, 1.0) if hasattr(result, 'quality_score') else 0.7
                scored_results.append((result, score))
            
            # Phase 4: Check compatibility
            await self.progress_reporter.update_stage(ProgressStage.COMPATIBILITY)
            self.print("\n🔗 Phase 4: Checking compatibility...")
            
            # Simplified compatibility check for CLI
            compatible_results = [r for r, s in scored_results if s > 0.5]
            
            if not compatible_results:
                self.print("❌ No compatible components found", style="red")
                return
            
            # Phase 5: Assemble project
            await self.progress_reporter.update_stage(ProgressStage.ASSEMBLING)
            self.print("\n🔧 Phase 5: Assembling your project...")
            
            # Clone repositories
            cloner = RepositoryCloner()
            clone_results = await cloner.clone_repositories(compatible_results[:5])
            
            # Extract files
            extractor = FileExtractor()
            extraction_results = await extractor.extract_files(
                clone_results,
                language=self.config.language or analysis_result.recommended_language,
                extraction_criteria={'max_files_per_repo': 20}
            )
            
            # Integrate code
            integrator = CodeIntegrator()
            integration_result = await integrator.integrate_components(
                extraction_results,
                language=self.config.language or analysis_result.recommended_language,
                project_name=analysis_result.project_name or "autobot_project"
            )
            
            # Generate project
            generator = ProjectGenerator()
            project_type = ProjectType.APPLICATION
            if self.config.project_type:
                project_type = ProjectType(self.config.project_type)
            
            generated_project = await generator.generate_project(
                integration_result,
                project_name=analysis_result.project_name or "autobot_project",
                language=self.config.language or analysis_result.recommended_language,
                project_type=project_type
            )
            
            # Move to output directory
            final_project_path = output_path / generated_project.project_name
            if Path(generated_project.project_path) != final_project_path:
                import shutil
                if final_project_path.exists():
                    shutil.rmtree(final_project_path)
                shutil.move(generated_project.project_path, final_project_path)
                generated_project.project_path = str(final_project_path)
            
            # Phase 6: Quality Assurance
            if not self.config.skip_tests:
                await self.progress_reporter.update_stage(ProgressStage.TESTING)
                self.print("\n🧪 Phase 6: Running quality assurance...")
                
                # Integration testing
                tester = IntegrationTester()
                test_suite = await tester.test_project(generated_project)
                
                # Quality validation
                validator = QualityValidator()
                validation_result = await validator.validate_project(generated_project, test_suite)
                
                # Documentation generation
                if not self.config.skip_docs:
                    doc_generator = DocumentationGenerator()
                    doc_result = await doc_generator.generate_documentation(
                        generated_project, validation_result,
                        [DocType.README, DocType.USER_GUIDE, DocType.DEVELOPER_GUIDE]
                    )
                
                # Store results for later reference
                self.last_results = {
                    'generated_project': generated_project,
                    'test_suite': test_suite,
                    'validation_result': validation_result,
                    'doc_result': doc_result if not self.config.skip_docs else None
                }
            
            # Cleanup
            await cloner.cleanup_clones(clone_results)
            
            # Phase 7: Complete
            await self.progress_reporter.update_stage(ProgressStage.COMPLETE)
            
            # Print success message
            self.print_success_results(generated_project)
            
        except Exception as e:
            await self.progress_reporter.update_stage(ProgressStage.ERROR, str(e))
            self.print(f"\n❌ Error during processing: {e}", style="red")
            if self.config.verbose:
                import traceback
                self.print(traceback.format_exc(), style="dim red")
        
        finally:
            await self.progress_reporter.end_session()
    
    def print_analysis_results(self, analysis_result):
        """Print analysis results."""
        
        self.print("\n📋 Analysis Results:", style="bold blue")
        self.print(f"  Project Name: {analysis_result.project_name}")
        self.print(f"  Project Type: {analysis_result.project_type}")
        self.print(f"  Language: {analysis_result.recommended_language}")
        self.print(f"  Components: {len(analysis_result.required_components)}")
        
        if analysis_result.required_components:
            self.print("  Required Components:")
            for component in analysis_result.required_components[:5]:
                self.print(f"    • {component}")
    
    def print_search_results(self, search_results):
        """Print search results."""
        
        self.print("\n🔍 Search Results:", style="bold blue")
        self.print(f"  Total Results: {len(search_results.all_results)}")
        self.print(f"  Tier 1 (Packages): {len(search_results.tier1_results)}")
        self.print(f"  Tier 2 (Curated): {len(search_results.tier2_results)}")
        self.print(f"  Tier 3 (Discovery): {len(search_results.tier3_results)}")
        
        if search_results.all_results:
            self.print("  Top Results:")
            for result in search_results.all_results[:5]:
                stars = getattr(result, 'stars', 0)
                self.print(f"    • {result.name} - {result.description[:60]}... ({stars} stars)")
    
    def print_success_results(self, generated_project):
        """Print success results."""
        
        success_text = f"""
🎉 Project Successfully Generated!

📁 Project Location: {generated_project.project_path}
🏗️ Project Type: {generated_project.project_type.value.title()}
💻 Language: {generated_project.language.title()}
📦 Dependencies: {len(generated_project.dependencies)}

🚀 Next Steps:
1. Navigate to your project: cd {generated_project.project_path}
"""
        
        if generated_project.build_commands:
            success_text += f"2. Install dependencies: {generated_project.build_commands[0]}\n"
        
        if generated_project.run_commands:
            success_text += f"3. Run your project: {generated_project.run_commands[0]}\n"
        
        success_text += """
📚 Check the README.md file for detailed instructions!

Happy coding! 🚀
"""
        
        self.print_panel(success_text.strip(), title="Success!", style="green")
        
        # Show quality results if available
        if 'validation_result' in self.last_results:
            validation = self.last_results['validation_result']
            quality_text = f"""
Quality Score: {validation.overall_score:.2f}/1.0 ({validation.overall_quality_level.value.title()})

Strengths: {len(validation.strengths)}
Recommendations: {len(validation.recommendations)}
"""
            self.print_panel(quality_text.strip(), title="Quality Assessment", style="blue")
    
    def print_last_results(self):
        """Print last results."""
        
        if not self.last_results:
            self.print("❌ No previous results available", style="yellow")
            return
        
        if 'generated_project' in self.last_results:
            project = self.last_results['generated_project']
            self.print(f"\n📁 Last Generated Project: {project.project_name}")
            self.print(f"   Location: {project.project_path}")
            self.print(f"   Type: {project.project_type.value}")
            self.print(f"   Language: {project.language}")
        
        if 'validation_result' in self.last_results:
            validation = self.last_results['validation_result']
            self.print(f"\n📊 Quality Score: {validation.overall_score:.2f}/1.0")
            self.print(f"   Level: {validation.overall_quality_level.value.title()}")
            
            if validation.recommendations:
                self.print("   Top Recommendations:")
                for rec in validation.recommendations[:3]:
                    self.print(f"     • {rec}")
    
    def print_help(self):
        """Print help information."""
        
        help_text = """
🤖 AutoBot Assembly System - Commands

Basic Commands:
  help, h          - Show this help message
  quit, exit, q    - Exit AutoBot
  config, settings - Configure AutoBot settings
  status, last     - Show last project results

Usage:
  Simply describe what you want to build in natural language!

Examples:
  "Create a web scraper for news articles"
  "Build a REST API for a todo app"
  "Make a CLI tool for file processing"
  "Generate a machine learning classifier"

Tips:
  • Be specific about your requirements
  • Mention preferred technologies if you have any
  • Describe the main functionality you need

AutoBot will automatically:
  ✅ Find relevant components
  ✅ Check compatibility and licenses
  ✅ Generate working code
  ✅ Add tests and documentation
  ✅ Set up build systems
"""
        
        self.print_panel(help_text.strip(), title="Help", style="cyan")
    
    async def configure_settings(self):
        """Configure AutoBot settings."""
        
        self.print_panel("⚙️ AutoBot Configuration", title="Settings", style="yellow")
        
        # Output directory
        current_output = self.config.output_dir
        new_output = self.prompt(f"Output directory", default=current_output)
        if new_output != current_output:
            self.config.output_dir = new_output
        
        # Verbosity
        self.config.verbose = self.confirm("Enable verbose output?", default=self.config.verbose)
        
        # Testing
        self.config.skip_tests = not self.confirm("Run quality tests?", default=not self.config.skip_tests)
        
        # Documentation
        self.config.skip_docs = not self.confirm("Generate documentation?", default=not self.config.skip_docs)
        
        # Max repositories
        max_repos = self.prompt(f"Maximum repositories to analyze", default=str(self.config.max_repos))
        try:
            self.config.max_repos = int(max_repos)
        except ValueError:
            pass
        
        self.print("✅ Settings updated!", style="green")


def create_cli_parser():
    """Create command-line argument parser."""
    
    parser = argparse.ArgumentParser(
        description="AutoBot Assembly System - AI-powered repository assembly",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  autobot                                    # Interactive mode
  autobot "Create a web scraper"             # Direct prompt
  autobot --wizard                           # Guided wizard mode
  autobot --batch "Build a REST API" -o ./my_api  # Batch mode
        """
    )
    
    parser.add_argument(
        'prompt', 
        nargs='?', 
        help='Project description (what you want to build)'
    )
    
    parser.add_argument(
        '--mode', '-m',
        choices=['interactive', 'wizard', 'batch'],
        default='interactive',
        help='CLI mode (default: interactive)'
    )
    
    parser.add_argument(
        '--wizard', '-w',
        action='store_true',
        help='Run in guided wizard mode'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='./autobot_output',
        help='Output directory (default: ./autobot_output)'
    )
    
    parser.add_argument(
        '--type', '-t',
        choices=['application', 'library', 'web_service', 'cli_tool'],
        help='Project type (auto-detected if not specified)'
    )
    
    parser.add_argument(
        '--language', '-l',
        choices=['python', 'javascript', 'java'],
        help='Programming language (auto-detected if not specified)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--skip-tests',
        action='store_true',
        help='Skip quality testing'
    )
    
    parser.add_argument(
        '--skip-docs',
        action='store_true',
        help='Skip documentation generation'
    )
    
    parser.add_argument(
        '--max-repos',
        type=int,
        default=10,
        help='Maximum repositories to analyze (default: 10)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=300,
        help='Timeout in seconds (default: 300)'
    )
    
    return parser


async def main():
    """Main CLI entry point."""
    
    # Set up logging
    logging.basicConfig(
        level=logging.WARNING,  # Quiet by default
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Parse arguments
    parser = create_cli_parser()
    args = parser.parse_args()
    
    # Create configuration
    config = CLIConfig(
        mode=CLIMode.WIZARD if args.wizard else CLIMode(args.mode),
        output_dir=args.output,
        verbose=args.verbose,
        skip_tests=args.skip_tests,
        skip_docs=args.skip_docs,
        project_type=args.type,
        language=args.language,
        max_repos=args.max_repos,
        timeout=args.timeout
    )
    
    # Set logging level based on verbosity
    if config.verbose:
        logging.getLogger().setLevel(logging.INFO)
    
    # Handle batch mode
    if args.prompt and not args.wizard:
        config.mode = CLIMode.BATCH
    
    # Create and run CLI
    cli = AutoBotCLI(config)
    success = await cli.run(args.prompt)
    
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)