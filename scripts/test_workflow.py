#!/usr/bin/env python3
"""
Test script for AutoBot Assembly System workflow.
Tests the complete pipeline from prompt analysis to search orchestration.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from orchestration.project_analyzer import ProjectAnalyzer
from orchestration.search_orchestrator import SearchOrchestrator


async def test_project_analysis():
    """Test the AI prompt analysis functionality."""
    print("🧠 Testing Project Analysis...")
    
    analyzer = ProjectAnalyzer()
    
    test_cases = [
        ("Create a Python FastAPI application with JWT authentication and PostgreSQL database", "python"),
        ("Build a React dashboard with user management and charts", "javascript"),
        ("Make a CLI tool for file processing and data conversion", "python"),
        ("Develop a Java Spring Boot microservice with Redis caching", "java")
    ]
    
    for prompt, language in test_cases:
        print(f"\n  📝 Prompt: {prompt}")
        try:
            result = await analyzer.analyze_prompt(prompt, language)
            print(f"     Type: {result.project_type}")
            print(f"     Components: {result.core_components}")
            print(f"     Keywords: {result.search_keywords}")
            print(f"     Complexity: {result.complexity_level}")
            print(f"     ✅ Analysis successful")
        except Exception as e:
            print(f"     ❌ Analysis failed: {e}")
    
    print("\n✅ Project Analysis test complete")


async def test_search_orchestration():
    """Test the search orchestration functionality."""
    print("\n🔍 Testing Search Orchestration...")
    
    # Check for GitHub token
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("⚠️  GITHUB_TOKEN not found in environment. Search functionality will be limited.")
    
    try:
        orchestrator = SearchOrchestrator(github_token)
        analyzer = ProjectAnalyzer()
        
        # Test with a simple project
        test_prompt = "Create a Python web scraper with proxy rotation"
        print(f"  📝 Test prompt: {test_prompt}")
        
        # Analyze project
        project_structure = await analyzer.analyze_prompt(test_prompt, "python")
        print(f"     Components identified: {project_structure.core_components}")
        
        # Execute search (with limited results for testing)
        print("     Executing tiered search...")
        search_results = await orchestrator.execute_tiered_search(project_structure, max_results_per_tier=5)
        
        print(f"     Results summary:")
        for tier, count in search_results.search_summary.items():
            print(f"       {tier}: {count}")
        
        # Show top results
        top_results = orchestrator.get_top_results(search_results, top_n=3)
        print(f"     Top 3 results:")
        for i, result in enumerate(top_results, 1):
            name = getattr(result, 'full_name', getattr(result, 'name', 'Unknown'))
            score = getattr(result, 'quality_score', getattr(result, 'discovery_score', 0.0))
            print(f"       {i}. {name} (Score: {score:.2f})")
        
        print("     ✅ Search orchestration successful")
        
    except Exception as e:
        print(f"     ❌ Search orchestration failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Search Orchestration test complete")


async def test_api_connectivity():
    """Test API connectivity."""
    print("\n🌐 Testing API Connectivity...")
    
    # Test Pollinations AI
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://text.pollinations.ai/openai",
                json={
                    "model": "openai",
                    "messages": [{"role": "user", "content": "Hello"}],
                    "jsonMode": False
                },
                timeout=10
            ) as response:
                if response.status == 200:
                    print("     ✅ Pollinations AI API accessible")
                else:
                    print(f"     ⚠️  Pollinations AI API returned status {response.status}")
    except Exception as e:
        print(f"     ❌ Pollinations AI API test failed: {e}")
    
    # Test GitHub API
    github_token = os.getenv('GITHUB_TOKEN')
    if github_token:
        try:
            from github import Github
            g = Github(github_token)
            user = g.get_user()
            print(f"     ✅ GitHub API accessible (User: {user.login})")
        except Exception as e:
            print(f"     ❌ GitHub API test failed: {e}")
    else:
        print("     ⚠️  GitHub token not provided, skipping GitHub API test")
    
    print("\n✅ API Connectivity test complete")


def test_dependencies():
    """Test that all required dependencies are installed."""
    print("📦 Testing Dependencies...")
    
    required_packages = [
        'aiohttp', 'asyncio', 'github', 'docker', 'redis', 
        'pydantic', 'requests', 'logging'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"     ✅ {package}")
        except ImportError:
            print(f"     ❌ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All Python dependencies installed")
        return True


def test_external_tools():
    """Test external tools availability."""
    print("\n🔧 Testing External Tools...")
    
    import subprocess
    
    tools = {
        'docker': ['docker', '--version'],
        'ruby': ['ruby', '--version'],
        'cargo': ['cargo', '--version'],
        'ast-grep': ['ast-grep', '--version']
    }
    
    for tool_name, command in tools.items():
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                print(f"     ✅ {tool_name}: {version}")
            else:
                print(f"     ❌ {tool_name}: Command failed")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"     ❌ {tool_name}: Not found")
    
    print("\n✅ External tools test complete")


async def main():
    """Run all tests."""
    print("🤖 AutoBot Assembly System - Workflow Test")
    print("==========================================")
    
    # Setup logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise during testing
    
    # Test dependencies first
    if not test_dependencies():
        print("\n❌ Dependency test failed. Please install missing packages.")
        return
    
    # Test external tools
    test_external_tools()
    
    # Test API connectivity
    await test_api_connectivity()
    
    # Test core functionality
    await test_project_analysis()
    await test_search_orchestration()
    
    print("\n🎉 All tests completed!")
    print("\nNext steps:")
    print("1. Review any warnings or errors above")
    print("2. Set up your .env file with API keys if not done already")
    print("3. Try running a full workflow with your own prompts")


if __name__ == "__main__":
    asyncio.run(main())