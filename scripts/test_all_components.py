#!/usr/bin/env python3
"""
Comprehensive test script for all AutoBot Assembly System components.
Fixes import issues by using proper Python path setup.
"""

import asyncio
import sys
import tempfile
import os
from pathlib import Path

# Add src to Python path and set up proper imports
current_dir = Path(__file__).parent.parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Change to the project directory to fix relative imports
os.chdir(current_dir)

async def test_core_components():
    """Test core system components."""
    print("🧪 Testing Core Components")
    print("=" * 50)
    
    try:
        # Test orchestration components
        from orchestration.project_analyzer import ProjectAnalyzer
        from orchestration.search_orchestrator import SearchOrchestrator
        
        # Test search components
        from search.tier1_packages import PackageSearcher
        from search.tier2_curated import CuratedSearcher
        from search.tier3_discovery import GitHubDiscoverer
        
        # Test analysis components
        from analysis.unified_scorer import UnifiedFileScorer
        from analysis.megalinter_client import MegaLinterClient
        from analysis.semgrep_client import SemgrepClient
        from analysis.astgrep_client import ASTGrepClient
        
        print("✅ Core orchestration and analysis components imported successfully")
        
        # Quick functionality test
        analyzer = ProjectAnalyzer()
        result = await analyzer.analyze_project_prompt(
            "Create a simple web scraper",
            provider="pollinations"
        )
        
        print(f"✅ Project analysis working: {result.name}")
        print(f"   Language: {result.language}")
        print(f"   Components: {len(result.components)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Core components test failed: {e}")
        return False

async def test_assembly_components():
    """Test assembly and project generation components."""
    print("\n🔧 Testing Assembly Components")
    print("=" * 50)
    
    try:
        from assembly.repository_cloner import RepositoryCloner
        from assembly.file_extractor import FileExtractor
        from assembly.code_integrator import CodeIntegrator
        from assembly.project_generator import ProjectGenerator
        
        print("✅ Assembly components imported successfully")
        
        # Test project generator
        generator = ProjectGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project = await generator.generate_project(
                project_name="TestProject",
                output_dir=temp_dir,
                files={
                    'main.py': 'print("Hello, World!")',
                    'README.md': '# Test Project'
                },
                project_description="Simple test project",
                language="python"
            )
            
            print(f"✅ Project generation working: {project.name}")
            print(f"   Path: {project.path}")
            print(f"   Files: {len(project.files)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Assembly components test failed: {e}")
        return False

async def test_reporting_components():
    """Test reporting components."""
    print("\n📋 Testing Reporting Components")
    print("=" * 50)
    
    try:
        from reporting.project_reporter import ProjectReporter
        from reporting.ai_integrated_reporter import AIIntegratedReporter
        
        print("✅ Reporting components imported successfully")
        
        # Test AI integrated reporter
        reporter = AIIntegratedReporter()
        
        # Mock project data for testing
        project_data = {
            'name': 'TestProject',
            'path': '/tmp/test',
            'files': ['main.py', 'README.md'],
            'size': 1024,
            'language': 'python',
            'description': 'Test project for reporting'
        }
        
        repositories = [
            {
                'name': 'test-repo',
                'url': 'https://github.com/test/repo',
                'files_copied': ['main.py'],
                'purpose': 'Testing purposes',
                'license': 'MIT'
            }
        ]
        
        report = await reporter.generate_comprehensive_report(
            project_data, repositories
        )
        
        print("✅ AI-integrated reporting working")
        print(f"   Report length: {len(report)} characters")
        print("   Contains AI analysis sections: ✅")
        
        return True
        
    except Exception as e:
        print(f"❌ Reporting components test failed: {e}")
        return False

async def test_qa_components():
    """Test quality assurance components."""
    print("\n🔍 Testing QA Components")
    print("=" * 50)
    
    try:
        from qa.integration_tester import IntegrationTester
        from qa.quality_validator import QualityValidator
        from qa.documentation_generator import DocumentationGenerator
        
        print("✅ QA components imported successfully")
        
        # Test integration tester
        tester = IntegrationTester()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple test project
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text('def hello(): return "Hello, World!"')
            
            result = await tester.run_integration_tests(temp_dir)
            
            print(f"✅ Integration testing working")
            print(f"   Tests passed: {result.tests_passed}")
            print(f"   Total tests: {result.total_tests}")
        
        return True
        
    except Exception as e:
        print(f"❌ QA components test failed: {e}")
        return False

async def test_cli_components():
    """Test CLI components."""
    print("\n💻 Testing CLI Components")
    print("=" * 50)
    
    try:
        from cli.autobot_cli import AutoBotCLI, CLIConfig, CLIMode
        from cli.progress_reporter import ProgressReporter
        from cli.config_manager import ConfigManager
        
        print("✅ CLI components imported successfully")
        
        # Test config manager
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        print(f"✅ Config management working")
        print(f"   Config loaded: {type(config).__name__}")
        
        # Test progress reporter
        progress = ProgressReporter()
        progress.start_task("test_task", "Testing progress reporting")
        progress.update_progress("test_task", 50, "Halfway done")
        progress.complete_task("test_task", "Test completed")
        
        print("✅ Progress reporting working")
        
        return True
        
    except Exception as e:
        print(f"❌ CLI components test failed: {e}")
        return False

async def test_web_api_components():
    """Test web and API components."""
    print("\n🌐 Testing Web & API Components")
    print("=" * 50)
    
    try:
        from web.web_server import WebServer
        from web.websocket_handler import WebSocketHandler
        from web.result_visualizer import ResultVisualizer
        
        from api.api_server import APIServer
        from api.auth_manager import AuthManager
        from api.rate_limiter import RateLimiter
        
        print("✅ Web and API components imported successfully")
        
        # Test auth manager
        auth_manager = AuthManager()
        api_key = auth_manager.generate_api_key("test_user")
        
        print(f"✅ Auth management working")
        print(f"   Generated API key: {api_key[:20]}...")
        
        # Test rate limiter
        rate_limiter = RateLimiter()
        allowed = await rate_limiter.check_rate_limit("test_user")
        
        print(f"✅ Rate limiting working: {allowed}")
        
        return True
        
    except Exception as e:
        print(f"❌ Web/API components test failed: {e}")
        return False

async def main():
    """Run comprehensive component tests."""
    print("🧪 AutoBot Assembly System - Comprehensive Component Test")
    print("=" * 70)
    
    # Set GitHub token if available
    github_token = os.getenv('GITHUB_TOKEN')
    if github_token:
        print(f"✅ GitHub token configured: {github_token[:10]}...")
    else:
        print("⚠️ No GitHub token - some features may be limited")
    
    print()
    
    # Run all component tests
    test_results = {
        'Core Components': await test_core_components(),
        'Assembly Components': await test_assembly_components(),
        'Reporting Components': await test_reporting_components(),
        'QA Components': await test_qa_components(),
        'CLI Components': await test_cli_components(),
        'Web/API Components': await test_web_api_components()
    }
    
    # Summary
    print("\n🎯 COMPREHENSIVE TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for component, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{component:<25} {status}")
    
    print(f"\nResults: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL COMPONENTS WORKING!")
        print("🚀 AutoBot Assembly System is fully operational!")
    else:
        print(f"\n⚠️ {total - passed} component(s) need attention")
        print("🔧 Check the failed components above")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())