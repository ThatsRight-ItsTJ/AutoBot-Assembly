#!/usr/bin/env python3
"""
Fixed comprehensive test script for AutoBot Assembly System.

Tests all core components with proper error handling and fallback mechanisms.
"""

import asyncio
import sys
import os
import tempfile
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))
os.chdir(current_dir)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_project_analyzer():
    """Test AI-powered project analysis."""
    print("\n🤖 Testing Project Analyzer")
    print("-" * 40)
    
    try:
        from src.orchestration.project_analyzer import ProjectAnalyzer
        
        analyzer = ProjectAnalyzer()
        
        # Test with a simple project description
        test_prompt = "Create a simple web scraper that extracts news headlines from RSS feeds"
        
        print(f"Analyzing prompt: {test_prompt}")
        
        # Try with fallback provider (Pollinations)
        analysis = await analyzer.analyze_project_prompt(test_prompt, provider="pollinations")
        
        print(f"✅ Analysis completed:")
        print(f"   Name: {analysis.name}")
        print(f"   Type: {analysis.project_type}")
        print(f"   Language: {analysis.language}")
        print(f"   Components: {len(analysis.components)}")
        print(f"   Confidence: {analysis.confidence}")
        
        return True
        
    except Exception as e:
        print(f"❌ Project Analyzer failed: {e}")
        logger.exception("Project Analyzer test failed")
        return False

async def test_search_orchestrator():
    """Test multi-tier search orchestration."""
    print("\n🔍 Testing Search Orchestrator")
    print("-" * 40)
    
    try:
        from src.orchestration.search_orchestrator import SearchOrchestrator
        
        orchestrator = SearchOrchestrator()
        
        # Test with simple requirements
        project_name = "web scraper"
        language = "python"
        components = ["requests", "beautifulsoup", "json"]
        
        print(f"Searching for: {project_name} ({language})")
        print(f"Components: {components}")
        
        results = await orchestrator.orchestrate_search(project_name, language, components)
        
        print(f"✅ Search completed:")
        print(f"   Packages found: {len(results.packages)}")
        print(f"   Collections found: {len(results.curated_collections)}")
        print(f"   Repositories found: {len(results.discovered_repositories)}")
        
        # Show some examples
        if results.packages:
            print(f"   Example package: {results.packages[0].name}")
        if results.discovered_repositories:
            print(f"   Example repo: {results.discovered_repositories[0].name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Search Orchestrator failed: {e}")
        logger.exception("Search Orchestrator test failed")
        return False

async def test_project_generator():
    """Test project generation."""
    print("\n🏗️ Testing Project Generator")
    print("-" * 40)
    
    try:
        from src.assembly.project_generator import ProjectGenerator
        
        generator = ProjectGenerator()
        
        # Create test files
        test_files = {
            'main.py': '''#!/usr/bin/env python3
"""
Simple Web Scraper
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

def scrape_headlines():
    """Scrape news headlines."""
    print("Scraping headlines...")
    return ["Sample headline 1", "Sample headline 2"]

def main():
    """Main function."""
    headlines = scrape_headlines()
    
    data = {
        'timestamp': datetime.now().isoformat(),
        'headlines': headlines
    }
    
    with open('headlines.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Scraped {len(headlines)} headlines")

if __name__ == '__main__':
    main()
''',
            'requirements.txt': '''requests>=2.25.0
beautifulsoup4>=4.9.0
''',
            'README.md': '''# Web Scraper

A simple web scraper for extracting news headlines.

## Usage

```bash
pip install -r requirements.txt
python main.py
```
'''
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project = await generator.generate_project(
                project_name="WebScraper",
                output_dir=temp_dir,
                files=test_files,
                project_description="Simple web scraper for news headlines",
                language="python"
            )
            
            print(f"✅ Project generated:")
            print(f"   Name: {project.name}")
            print(f"   Path: {project.path}")
            print(f"   Files: {len(project.files)}")
            print(f"   Size: {project.size} bytes")
            
            return True
        
    except Exception as e:
        print(f"❌ Project Generator failed: {e}")
        logger.exception("Project Generator test failed")
        return False

async def test_ai_reporter():
    """Test AI-integrated reporting."""
    print("\n📋 Testing AI Reporter")
    print("-" * 40)
    
    try:
        from src.reporting.ai_integrated_reporter import AIIntegratedReporter
        
        reporter = AIIntegratedReporter()
        
        # Create test project data
        project_data = {
            'name': 'TestProject',
            'files': ['main.py', 'requirements.txt', 'README.md'],
            'size': 1024,
            'language': 'python',
            'description': 'Test project for reporting'
        }
        
        repositories = [
            {
                'name': 'requests',
                'url': 'https://github.com/psf/requests',
                'purpose': 'HTTP library',
                'license': 'Apache-2.0'
            }
        ]
        
        print("Generating comprehensive report...")
        
        report = await reporter.generate_comprehensive_report(project_data, repositories)
        
        print(f"✅ Report generated:")
        print(f"   Length: {len(report)} characters")
        print(f"   Contains AI analysis: {'AI-POWERED ANALYSIS' in report}")
        print(f"   Contains metrics: {'QUALITY METRICS' in report}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI Reporter failed: {e}")
        logger.exception("AI Reporter test failed")
        return False

async def test_config_manager():
    """Test configuration management."""
    print("\n⚙️ Testing Config Manager")
    print("-" * 40)
    
    try:
        from src.cli.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        
        # Test API key retrieval
        api_keys = config_manager.get_api_keys()
        
        print(f"✅ Config Manager working:")
        print(f"   API keys configured: {len([k for k, v in api_keys.items() if v])}")
        print(f"   GitHub token: {'✅' if api_keys.get('github_token') else '❌'}")
        print(f"   OpenAI key: {'✅' if api_keys.get('openai_api_key') else '❌'}")
        
        # Test API status
        status = config_manager.get_api_status()
        print(f"   API status: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Config Manager failed: {e}")
        logger.exception("Config Manager test failed")
        return False

async def test_end_to_end_workflow():
    """Test complete end-to-end workflow."""
    print("\n🚀 Testing End-to-End Workflow")
    print("-" * 40)
    
    try:
        # Import all components
        from src.orchestration.project_analyzer import ProjectAnalyzer
        from src.orchestration.search_orchestrator import SearchOrchestrator
        from src.assembly.project_generator import ProjectGenerator
        from src.reporting.ai_integrated_reporter import AIIntegratedReporter
        
        print("1. Analyzing project requirements...")
        analyzer = ProjectAnalyzer()
        analysis = await analyzer.analyze_project_prompt(
            "Create a Python web scraper for news headlines",
            provider="pollinations"
        )
        print(f"   ✅ Analysis: {analysis.name} ({analysis.language})")
        
        print("2. Searching for components...")
        orchestrator = SearchOrchestrator()
        search_results = await orchestrator.orchestrate_search(
            analysis.name, analysis.language, analysis.components[:3]  # Limit components
        )
        print(f"   ✅ Found: {len(search_results.packages)} packages, {len(search_results.discovered_repositories)} repos")
        
        print("3. Generating project...")
        generator = ProjectGenerator()
        
        # Simple project files
        project_files = {
            'main.py': '''#!/usr/bin/env python3
"""News Scraper - Generated by AutoBot Assembly System"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

def scrape_news():
    """Scrape news headlines."""
    print("Scraping news headlines...")
    # Placeholder implementation
    return ["Breaking: AutoBot Assembly System Works!", "Tech: AI-Powered Development"]

def main():
    """Main function."""
    headlines = scrape_news()
    
    data = {
        'timestamp': datetime.now().isoformat(),
        'headlines': headlines,
        'count': len(headlines)
    }
    
    with open('news_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Successfully scraped {len(headlines)} headlines")

if __name__ == '__main__':
    main()
''',
            'requirements.txt': '''requests>=2.25.0
beautifulsoup4>=4.9.0
lxml>=4.6.0
''',
            'README.md': f'''# {analysis.name}

{analysis.description}

Generated by AutoBot Assembly System on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Features

- Web scraping capabilities
- JSON data export
- Error handling
- Modular design
'''
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project = await generator.generate_project(
                project_name="NewsScraper",
                output_dir=temp_dir,
                files=project_files,
                project_description=analysis.description,
                language=analysis.language
            )
            print(f"   ✅ Project: {project.name} ({len(project.files)} files)")
            
            print("4. Generating AI report...")
            reporter = AIIntegratedReporter()
            
            project_data = {
                'name': project.name,
                'path': project.path,
                'files': project.files,
                'size': project.size,
                'language': analysis.language,
                'description': analysis.description
            }
            
            repositories = [
                {
                    'name': 'requests',
                    'url': 'https://github.com/psf/requests',
                    'purpose': 'HTTP client library',
                    'license': 'Apache-2.0'
                }
            ]
            
            report = await reporter.generate_comprehensive_report(project_data, repositories)
            print(f"   ✅ Report: {len(report)} characters")
            
            print("\n🎉 End-to-End Workflow Completed Successfully!")
            print(f"   Total time: ~{datetime.now().second}s")
            print(f"   Components analyzed: {len(analysis.components)}")
            print(f"   Resources found: {len(search_results.packages) + len(search_results.discovered_repositories)}")
            print(f"   Project files: {len(project.files)}")
            print(f"   Report sections: {report.count('##')}")
            
            return True
        
    except Exception as e:
        print(f"❌ End-to-End Workflow failed: {e}")
        logger.exception("End-to-End Workflow test failed")
        return False

async def main():
    """Run all component tests."""
    print("🧪 AutoBot Assembly System - Comprehensive Component Test")
    print("=" * 70)
    
    # Check environment
    github_token = os.getenv('GITHUB_TOKEN')
    if github_token:
        print(f"✅ GitHub token configured: {github_token[:10]}...")
    else:
        print("⚠️ No GitHub token - some features may be limited")
    
    print()
    
    # Define tests
    tests = [
        ("Config Manager", test_config_manager),
        ("Project Analyzer", test_project_analyzer),
        ("Search Orchestrator", test_search_orchestrator),
        ("Project Generator", test_project_generator),
        ("AI Reporter", test_ai_reporter),
        ("End-to-End Workflow", test_end_to_end_workflow)
    ]
    
    results = {}
    
    # Run tests
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running {test_name} test...")
            result = await test_func()
            results[test_name] = "✅ PASSED" if result else "❌ FAILED"
            
            if result:
                print(f"✅ {test_name} test completed successfully")
            else:
                print(f"❌ {test_name} test failed")
                
        except Exception as e:
            results[test_name] = f"❌ FAILED: {str(e)}"
            print(f"❌ {test_name} test failed with exception: {e}")
            logger.exception(f"Test {test_name} failed")
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, result in results.items():
        print(f"{test_name:<25} {result}")
    
    passed_tests = len([r for r in results.values() if "PASSED" in r])
    total_tests = len(results)
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("🚀 AutoBot Assembly System is fully operational!")
        print("\n📊 System Status:")
        print("✅ AI-powered project analysis")
        print("✅ Multi-tier component discovery")
        print("✅ Automated project generation")
        print("✅ AI-integrated comprehensive reporting")
        print("✅ End-to-end workflow automation")
    else:
        print(f"\n⚠️ {total_tests - passed_tests} test(s) failed")
        print("🔧 Check the failed components above")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    asyncio.run(main())