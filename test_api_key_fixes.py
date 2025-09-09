#!/usr/bin/env python3
"""
Test script to verify API key loading fixes.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_environment_loading():
    """Test environment variable loading."""
    print("🔍 Testing Environment Variable Loading...")
    
    # Test dotenv loading (if available)
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ dotenv loaded successfully")
    except ImportError:
        print("⚠️  dotenv not available, using system environment")
    
    # Check for common environment variables
    env_vars = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY', 'ZAI_API_KEY']
    found_vars = []
    
    for var in env_vars:
        if os.getenv(var):
            found_vars.append(var)
            print(f"✅ Found {var} in environment")
        else:
            print(f"❌ {var} not found in environment")
    
    return len(found_vars) > 0

def test_config_manager():
    """Test ConfigManager initialization and API key resolution."""
    print("\n🔧 Testing ConfigManager...")
    
    try:
        from src.cli.config_manager import ConfigManager
        
        # Initialize ConfigManager
        config_manager = ConfigManager()
        print("✅ ConfigManager initialized successfully")
        
        # Test API key resolution
        api_keys = config_manager.get_api_keys()
        print(f"✅ API keys resolved: {list(api_keys.keys())}")
        
        # Test function-specific API key resolution
        function_config = config_manager.get_function_api_key('project_analyzer')
        print(f"✅ Function API config resolved: provider={function_config['provider']}")
        
        # Test API status
        api_status = config_manager.get_api_status('project_analyzer')
        available_providers = [p for p, s in api_status.items() if s.get('available', False)]
        print(f"✅ Available API providers: {available_providers}")
        
        return True
        
    except Exception as e:
        print(f"❌ ConfigManager test failed: {e}")
        return False

def test_ai_reporter():
    """Test AIIntegratedReporter initialization."""
    print("\n📊 Testing AIIntegratedReporter...")
    
    try:
        from src.reporting.ai_integrated_reporter import AIIntegratedReporter
        from src.cli.config_manager import ConfigManager
        
        # Test with ConfigManager
        config_manager = ConfigManager()
        reporter = AIIntegratedReporter(config_manager=config_manager)
        print("✅ AIIntegratedReporter initialized with ConfigManager")
        
        # Test without ConfigManager
        reporter_fallback = AIIntegratedReporter()
        print("✅ AIIntegratedReporter initialized without ConfigManager (fallback)")
        
        return True
        
    except Exception as e:
        print(f"❌ AIIntegratedReporter test failed: {e}")
        return False

def test_project_analyzer():
    """Test ProjectAnalyzer initialization."""
    print("\n🔬 Testing ProjectAnalyzer...")
    
    try:
        from src.orchestration.project_analyzer import ProjectAnalyzer
        from src.cli.config_manager import ConfigManager
        
        # Test with ConfigManager
        config_manager = ConfigManager()
        analyzer = ProjectAnalyzer(config_manager=config_manager)
        print("✅ ProjectAnalyzer initialized with ConfigManager")
        
        # Test without ConfigManager
        analyzer_fallback = ProjectAnalyzer()
        print("✅ ProjectAnalyzer initialized without ConfigManager (fallback)")
        
        return True
        
    except Exception as e:
        print(f"❌ ProjectAnalyzer test failed: {e}")
        return False

async def test_ai_integration():
    """Test AI integration with fallback behavior."""
    print("\n🤖 Testing AI Integration...")
    
    try:
        from src.orchestration.project_analyzer import ProjectAnalyzer
        from src.reporting.ai_integrated_reporter import AIIntegratedReporter
        from src.cli.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        
        # Test ProjectAnalyzer AI analysis
        analyzer = ProjectAnalyzer(config_manager=config_manager)
        analysis = await analyzer.analyze_project_prompt("Create a web scraper for news")
        print(f"✅ ProjectAnalyzer analysis completed: {analysis.name}")
        
        # Test AIIntegratedReporter AI analysis
        reporter = AIIntegratedReporter(config_manager=config_manager)
        project_data = {
            'name': 'Test Project',
            'files': ['main.py', 'requirements.txt'],
            'size': 1024,
            'language': 'python'
        }
        
        # Test a simple AI analysis call
        ai_result = await reporter._get_ai_analysis("Test project analysis", "executive_summary")
        print(f"✅ AIIntegratedReporter AI analysis completed: {len(ai_result)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ AI integration test failed: {e}")
        return False

def test_cli_initialization():
    """Test CLI initialization with ConfigManager."""
    print("\n🖥️  Testing CLI Initialization...")
    
    try:
        from src.cli.autobot_cli import AutoBotCLI
        
        # Initialize CLI
        cli = AutoBotCLI()
        print("✅ AutoBotCLI initialized successfully")
        
        # Check if ConfigManager is available
        if cli.config_manager:
            print("✅ CLI has ConfigManager available")
        else:
            print("⚠️  CLI using fallback behavior (no ConfigManager)")
        
        # Check if reporter has ConfigManager
        if cli.reporter.config_manager:
            print("✅ AIIntegratedReporter has ConfigManager")
        else:
            print("⚠️  AIIntegratedReporter using fallback behavior")
        
        return True
        
    except Exception as e:
        print(f"❌ CLI initialization test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 AutoBot Assembly System - API Key Loading Tests")
    print("=" * 60)
    
    test_results = []
    
    # Run tests
    test_results.append(("Environment Loading", test_environment_loading()))
    test_results.append(("ConfigManager", test_config_manager()))
    test_results.append(("AIIntegratedReporter", test_ai_reporter()))
    test_results.append(("ProjectAnalyzer", test_project_analyzer()))
    test_results.append(("CLI Initialization", test_cli_initialization()))
    test_results.append(("AI Integration", await test_ai_integration()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📋 Test Results Summary:")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
        if result:
            passed += 1
    
    print("=" * 60)
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! API key loading fixes are working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)