#!/usr/bin/env python3
"""
AutoBot CLI Interface

Command-line interface for the AutoBot Assembly System.
"""

import argparse
import asyncio
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import json
import os

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Now import with absolute imports
from src.orchestration.search_orchestrator import SearchOrchestrator
from src.assembly.project_generator import ProjectGenerator
from src.reporting.ai_integrated_reporter import AIIntegratedReporter


class AutoBotCLI:
    """Command-line interface for AutoBot Assembly System."""
    
    def __init__(self):
        self.orchestrator = SearchOrchestrator()
        self.generator = ProjectGenerator()
        self.reporter = AIIntegratedReporter()
        
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            description="AutoBot Assembly System - Automated project generation",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python -m src.cli.autobot_cli batch "Create a web scraper"
  python -m src.cli.autobot_cli interactive
  python -m src.cli.autobot_cli wizard --type web_service
            """
        )
        
        # Mode selection - make this a positional argument
        parser.add_argument(
            'mode',
            choices=['interactive', 'wizard', 'batch'],
            help='Operation mode'
        )
        
        # Prompt for batch mode
        parser.add_argument(
            'prompt',
            nargs='?',
            help='Project description (required for batch mode)'
        )
        
        # Optional arguments
        parser.add_argument(
            '--output', '-o',
            type=str,
            default='./generated_project',
            help='Output directory for generated project'
        )
        
        parser.add_argument(
            '--type', '-t',
            choices=['application', 'library', 'web_service', 'cli_tool'],
            default='application',
            help='Project type'
        )
        
        parser.add_argument(
            '--language', '-l',
            choices=['python', 'javascript', 'java'],
            default='python',
            help='Programming language'
        )
        
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose output'
        )
        
        parser.add_argument(
            '--skip-tests',
            action='store_true',
            help='Skip test generation'
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
            help='Maximum repositories to analyze'
        )
        
        parser.add_argument(
            '--timeout',
            type=int,
            default=300,
            help='Timeout in seconds'
        )
        
        return parser
    
    async def run_batch_mode(self, args: argparse.Namespace) -> None:
        """Run in batch mode with the provided prompt."""
        if not args.prompt:
            print("Error: Prompt is required for batch mode")
            print("Usage: python -m src.cli.autobot_cli batch \"Your project description\"")
            sys.exit(1)
        
        print(f"🚀 AutoBot Assembly System - Batch Mode")
        print(f"📝 Project: {args.prompt}")
        print(f"🔧 Language: {args.language}")
        print(f"📁 Output: {args.output}")
        print("-" * 50)
        
        try:
            # Step 1: Search for components
            print("🔍 Searching for components...")
            search_results = await self.orchestrator.orchestrate_search(
                query=args.prompt,
                language=args.language,
                project_type=args.type,
                max_results=args.max_repos
            )
            
            print(f"✅ Found {len(search_results.all_results)} components")
            
            # Step 2: Generate project
            print("🏗️ Generating project...")
            project_config = {
                'name': self._extract_project_name(args.prompt),
                'description': args.prompt,
                'language': args.language,
                'type': args.type,
                'include_tests': not args.skip_tests,
                'include_docs': not args.skip_docs,
            }
            
            generated_project = await self.generator.generate_complete_project(
                search_results=search_results,
                project_config=project_config,
                output_path=args.output
            )
            
            print(f"✅ Project generated: {generated_project.project_path}")
            
            # Step 3: Generate report
            print("📊 Generating analysis report...")
            report = await self.reporter.generate_comprehensive_report(
                search_results=search_results,
                generated_project=generated_project,
                analysis_config={'include_ai_analysis': True}
            )
            
            # Save report
            report_path = Path(args.output) / "analysis_report.json"
            with open(report_path, 'w') as f:
                json.dump(report.to_dict(), f, indent=2, default=str)
            
            print(f"✅ Report saved: {report_path}")
            
            # Summary
            print("\n🎉 Project Generation Complete!")
            print(f"📁 Project Location: {generated_project.project_path}")
            print(f"📊 Components Used: {len(search_results.all_results)}")
            print(f"📄 Files Generated: {len(generated_project.generated_files)}")
            print(f"📋 Report: {report_path}")
            
            # Show key files
            if hasattr(generated_project, 'generated_files') and generated_project.generated_files:
                print("\n📄 Key Files Generated:")
                for file_path in sorted(generated_project.generated_files)[:10]:
                    print(f"  • {file_path}")
                if len(generated_project.generated_files) > 10:
                    print(f"  ... and {len(generated_project.generated_files) - 10} more files")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    async def run_interactive_mode(self, args: argparse.Namespace) -> None:
        """Run in interactive mode."""
        print("🚀 AutoBot Assembly System - Interactive Mode")
        print("Type 'help' for commands, 'quit' to exit")
        
        while True:
            try:
                user_input = input("\nAutoBot> ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                elif user_input.lower() == 'help':
                    self._show_help()
                elif user_input.startswith('generate '):
                    prompt = user_input[9:].strip()
                    if prompt:
                        # Create a temporary args object for batch processing
                        batch_args = argparse.Namespace(
                            prompt=prompt,
                            output=args.output,
                            language=args.language,
                            type=args.type,
                            skip_tests=args.skip_tests,
                            skip_docs=args.skip_docs,
                            max_repos=args.max_repos,
                            timeout=args.timeout,
                            verbose=args.verbose
                        )
                        await self.run_batch_mode(batch_args)
                    else:
                        print("Please provide a project description")
                else:
                    print("Unknown command. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {str(e)}")
    
    async def run_wizard_mode(self, args: argparse.Namespace) -> None:
        """Run in wizard mode with guided prompts."""
        print("🧙 AutoBot Assembly System - Wizard Mode")
        print("Let's create your project step by step...\n")
        
        # Collect project details
        project_type = input(f"Project type [{args.type}]: ").strip() or args.type
        language = input(f"Programming language [{args.language}]: ").strip() or args.language
        
        print("\nDescribe your project:")
        description = input("Project description: ").strip()
        
        if not description:
            print("Project description is required!")
            return
        
        output_dir = input(f"Output directory [{args.output}]: ").strip() or args.output
        
        # Confirm settings
        print(f"\n📋 Project Configuration:")
        print(f"  Type: {project_type}")
        print(f"  Language: {language}")
        print(f"  Description: {description}")
        print(f"  Output: {output_dir}")
        
        confirm = input("\nProceed with generation? [Y/n]: ").strip().lower()
        if confirm and confirm != 'y' and confirm != 'yes':
            print("Cancelled.")
            return
        
        # Create args for batch processing
        batch_args = argparse.Namespace(
            prompt=description,
            output=output_dir,
            language=language,
            type=project_type,
            skip_tests=args.skip_tests,
            skip_docs=args.skip_docs,
            max_repos=args.max_repos,
            timeout=args.timeout,
            verbose=args.verbose
        )
        
        await self.run_batch_mode(batch_args)
    
    def _show_help(self) -> None:
        """Show interactive mode help."""
        print("""
Available commands:
  generate <description>  - Generate a project from description
  help                   - Show this help message
  quit/exit/q           - Exit the program

Examples:
  generate Create a web scraper for news sites
  generate Build a REST API with FastAPI
  generate Make a CLI tool for file processing
        """)
    
    def _extract_project_name(self, prompt: str) -> str:
        """Extract a project name from the prompt."""
        # Simple extraction - take first few words and clean them
        words = prompt.lower().split()[:3]
        name = '_'.join(word.strip('.,!?') for word in words if word.isalnum())
        return name or 'autobot_project'
    
    async def run(self) -> None:
        """Main entry point."""
        parser = self.create_parser()
        args = parser.parse_args()
        
        # Set up logging
        log_level = logging.DEBUG if args.verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Run the appropriate mode
        try:
            if args.mode == 'batch':
                await self.run_batch_mode(args)
            elif args.mode == 'interactive':
                await self.run_interactive_mode(args)
            elif args.mode == 'wizard':
                await self.run_wizard_mode(args)
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            sys.exit(1)
        except Exception as e:
            print(f"Fatal error: {str(e)}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)


def main():
    """Entry point for the CLI."""
    cli = AutoBotCLI()
    asyncio.run(cli.run())


if __name__ == '__main__':
    main()