#!/usr/bin/env python3
"""
AutoBot CLI

Command-line interface for the AutoBot Assembly System.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestration.search_orchestrator import SearchOrchestrator
from assembly.project_generator import ProjectGenerator
from reporting.ai_integrated_reporter import AIIntegratedReporter


class AutoBotCLI:
    """Command-line interface for AutoBot Assembly System."""
    
    def __init__(self):
        self.orchestrator = SearchOrchestrator()
        self.generator = ProjectGenerator()
        self.reporter = AIIntegratedReporter()
        self.logger = logging.getLogger(__name__)
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            description="AutoBot Assembly System - Automated project generation",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python -m src.cli.autobot_cli batch "Create a Python web scraper"
  python -m src.cli.autobot_cli interactive
  python -m src.cli.autobot_cli wizard --type web_service --language python
            """
        )
        
        # Mode selection
        parser.add_argument(
            'mode',
            choices=['interactive', 'wizard', 'batch'],
            help='Operation mode: interactive (step-by-step), wizard (guided), or batch (single command)'
        )
        
        # Prompt for batch mode
        parser.add_argument(
            'prompt',
            nargs='?',
            help='Project description prompt (required for batch mode)'
        )
        
        # Optional arguments
        parser.add_argument(
            '--output', '-o',
            default='./generated_project',
            help='Output directory for generated project (default: ./generated_project)'
        )
        
        parser.add_argument(
            '--type', '-t',
            choices=['application', 'library', 'web_service', 'cli_tool'],
            help='Project type'
        )
        
        parser.add_argument(
            '--language', '-l',
            choices=['python', 'javascript', 'java'],
            default='python',
            help='Programming language (default: python)'
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
            help='Maximum number of repositories to analyze (default: 10)'
        )
        
        parser.add_argument(
            '--timeout',
            type=int,
            default=300,
            help='Timeout in seconds for operations (default: 300)'
        )
        
        return parser
    
    async def run_batch_mode(self, prompt: str, args: argparse.Namespace) -> None:
        """Run in batch mode with a single prompt."""
        print(f"🚀 Starting AutoBot Assembly System in batch mode...")
        print(f"📝 Prompt: {prompt}")
        print(f"🎯 Language: {args.language}")
        print(f"📁 Output: {args.output}")
        print()
        
        try:
            # Step 1: Search and analyze components
            print("🔍 Searching for relevant components...")
            search_results = await self.orchestrator.orchestrate_comprehensive_search(
                prompt, 
                args.language,
                max_repositories=args.max_repos
            )
            
            if not search_results.tier1_packages and not search_results.tier2_curated and not search_results.tier3_discovered:
                print("❌ No suitable components found. Try a different prompt.")
                return
            
            print(f"✅ Found {len(search_results.tier1_packages)} packages, "
                  f"{len(search_results.tier2_curated)} curated repos, "
                  f"{len(search_results.tier3_discovered)} discovered repos")
            
            # Step 2: Generate project
            print("\n🏗️ Generating project structure...")
            project_spec = {
                'name': self._extract_project_name(prompt),
                'description': prompt,
                'language': args.language,
                'type': args.type or 'application',
                'components': search_results,
                'include_tests': not args.skip_tests,
                'include_docs': not args.skip_docs,
                'output_dir': args.output
            }
            
            generated_project = await self.generator.generate_complete_project(project_spec)
            
            print(f"✅ Project generated successfully!")
            print(f"📁 Location: {generated_project.project_path}")
            print(f"📄 Files created: {len(generated_project.files)}")
            
            # Step 3: Generate report
            print("\n📊 Generating analysis report...")
            report = await self.reporter.generate_comprehensive_report(
                search_results, 
                args.language,
                project_context={'name': project_spec['name'], 'description': prompt}
            )
            
            # Save report
            report_path = Path(args.output) / "analysis_report.md"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(report.markdown_report)
            
            print(f"✅ Analysis report saved: {report_path}")
            
            # Summary
            print(f"\n🎉 AutoBot Assembly Complete!")
            print(f"📁 Project: {generated_project.project_path}")
            print(f"📊 Report: {report_path}")
            print(f"⭐ Quality Score: {report.overall_quality_score:.2f}")
            
        except Exception as e:
            print(f"❌ Error during project generation: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    async def run_interactive_mode(self, args: argparse.Namespace) -> None:
        """Run in interactive mode."""
        print("🤖 Welcome to AutoBot Assembly System - Interactive Mode")
        print("Type 'quit' or 'exit' to stop\n")
        
        while True:
            try:
                prompt = input("📝 Enter your project description: ").strip()
                
                if prompt.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not prompt:
                    print("Please enter a project description.")
                    continue
                
                # Use batch mode logic for processing
                await self.run_batch_mode(prompt, args)
                
                print("\n" + "="*50 + "\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                if args.verbose:
                    import traceback
                    traceback.print_exc()
    
    async def run_wizard_mode(self, args: argparse.Namespace) -> None:
        """Run in wizard mode with guided prompts."""
        print("🧙 AutoBot Assembly Wizard")
        print("I'll help you create a project step by step.\n")
        
        # Collect project details
        project_type = args.type or self._ask_choice(
            "What type of project do you want to create?",
            ['application', 'library', 'web_service', 'cli_tool']
        )
        
        language = args.language or self._ask_choice(
            "Which programming language?",
            ['python', 'javascript', 'java']
        )
        
        description = input("📝 Describe your project in detail: ").strip()
        
        if not description:
            print("❌ Project description is required.")
            return
        
        # Update args with wizard selections
        args.type = project_type
        args.language = language
        
        # Run batch mode with collected info
        await self.run_batch_mode(description, args)
    
    def _ask_choice(self, question: str, choices: list) -> str:
        """Ask user to choose from a list of options."""
        print(f"\n{question}")
        for i, choice in enumerate(choices, 1):
            print(f"  {i}. {choice}")
        
        while True:
            try:
                choice_num = int(input("Enter your choice (number): "))
                if 1 <= choice_num <= len(choices):
                    return choices[choice_num - 1]
                else:
                    print(f"Please enter a number between 1 and {len(choices)}")
            except ValueError:
                print("Please enter a valid number")
    
    def _extract_project_name(self, prompt: str) -> str:
        """Extract a project name from the prompt."""
        # Simple heuristic to create a project name
        words = prompt.lower().split()
        
        # Remove common words
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'that', 'create', 'build', 'make', 'develop'}
        meaningful_words = [w for w in words if w not in stop_words and w.isalpha()]
        
        # Take first few meaningful words
        name_words = meaningful_words[:3]
        
        if not name_words:
            return "autobot_project"
        
        return "_".join(name_words).replace("-", "_")


async def main():
    """Main entry point."""
    cli = AutoBotCLI()
    parser = cli.create_parser()
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Validate arguments
    if args.mode == 'batch' and not args.prompt:
        parser.error("batch mode requires a prompt argument")
    
    # Run the appropriate mode
    try:
        if args.mode == 'batch':
            await cli.run_batch_mode(args.prompt, args)
        elif args.mode == 'interactive':
            await cli.run_interactive_mode(args)
        elif args.mode == 'wizard':
            await cli.run_wizard_mode(args)
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())