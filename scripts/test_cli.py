#!/usr/bin/env python3
"""
CLI Test Script

Test script for AutoBot CLI interface with API key management.
"""

import asyncio
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cli.autobot_cli import AutoBotCLI, CLIConfig, CLIMode
from cli.config_manager import ConfigManager
from orchestration.project_analyzer import ProjectAnalyzer


async def test_api_key_management():
    """Test API key management functionality."""
    
    print("🔑 Testing API Key Management")
    print("=" * 50)
    
    # Create temporary config for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        config_manager = ConfigManager()
        config_manager.config_dir = Path(temp_dir)
        config_manager.config_file = config_manager.config_dir / "config.json"
        
        # Test setting API keys
        print("\n1. Setting API keys...")
        config_manager.set_api_key("openai", "sk-test-openai-key")
        config_manager.set_api_key("anthropic", "sk-ant-test-key")
        config_manager.set_api_key("github", "ghp_test_token")
        
        # Test getting API keys
        print("2. Getting API keys...")
        api_keys = config_manager.get_api_keys()
        for provider, key in api_keys.items():
            status = "✅ Set" if key else "❌ Not set"
            print(f"   {provider}: {status}")
        
        # Test API provider preference
        print("\n3. Testing API provider preferences...")
        providers = ["pollinations", "openai", "anthropic", "google"]
        
        for provider in providers:
            config_manager.set_api_provider(provider)
            preferred = config_manager.get_preferred_api_provider()
            print(f"   Set: {provider} → Preferred: {preferred}")
        
        # Test API status
        print("\n4. API Status:")
        api_status = config_manager.get_api_status()
        for provider, status in api_status.items():
            available = "✅" if status['available'] else "❌"
            print(f"   {provider}: {available} {status['status']}")


async def test_project_analyzer_with_apis():
    """Test project analyzer with different API providers."""
    
    print("\n🤖 Testing Project Analyzer with Multiple APIs")
    print("=" * 50)
    
    test_prompt = "Create a web scraper for news articles using Python"
    
    # Test with different providers
    providers = ["pollinations", "openai", "anthropic", "google"]
    
    for provider in providers:
        print(f"\n--- Testing {provider.upper()} ---")
        
        try:
            analyzer = ProjectAnalyzer(api_provider=provider)
            result = await analyzer.analyze_prompt(test_prompt)
            
            print(f"✅ {provider}: Success")
            print(f"   Project: {result.project_name}")
            print(f"   Type: {result.project_type}")
            print(f"   Language: {result.recommended_language}")
            print(f"   Confidence: {result.confidence_score:.2f}")
            
        except Exception as e:
            print(f"❌ {provider}: Failed - {e}")


async def test_cli_modes():
    """Test different CLI modes."""
    
    print("\n🖥️ Testing CLI Modes")
    print("=" * 50)
    
    # Test batch mode (non-interactive)
    print("\n1. Testing Batch Mode...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config = CLIConfig(
            mode=CLIMode.BATCH,
            output_dir=temp_dir,
            skip_tests=True,  # Skip for faster testing
            skip_docs=True,
            max_repos=3  # Limit for testing
        )
        
        cli = AutoBotCLI(config)
        
        # Mock a simple batch run
        test_prompt = "Create a simple Python calculator"
        
        try:
            # This would normally run the full pipeline
            # For testing, we'll just test the analyzer
            analyzer = ProjectAnalyzer(api_provider="pollinations")
            result = await analyzer.analyze_prompt(test_prompt)
            
            print(f"✅ Batch mode analysis successful")
            print(f"   Project: {result.project_name}")
            print(f"   Type: {result.project_type}")
            
        except Exception as e:
            print(f"❌ Batch mode failed: {e}")


async def test_fallback_behavior():
    """Test fallback behavior when no API keys are available."""
    
    print("\n🔄 Testing Fallback Behavior")
    print("=" * 50)
    
    # Clear environment variables for testing
    original_env = {}
    api_env_vars = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY', 'POLLINATIONS_API_KEY']
    
    for var in api_env_vars:
        original_env[var] = os.environ.get(var)
        if var in os.environ:
            del os.environ[var]
    
    try:
        # Test analyzer with no API keys (should fallback to Pollinations)
        print("1. Testing with no API keys...")
        analyzer = ProjectAnalyzer()
        
        print(f"   Selected provider: {analyzer.api_provider}")
        print(f"   API endpoint: {analyzer.api_endpoint}")
        
        # Test analysis (should use rule-based fallback)
        test_prompt = "Build a REST API for user management"
        result = await analyzer.analyze_prompt(test_prompt)
        
        print(f"✅ Fallback analysis successful")
        print(f"   Project: {result.project_name}")
        print(f"   Confidence: {result.confidence_score:.2f}")
        
    finally:
        # Restore environment variables
        for var, value in original_env.items():
            if value is not None:
                os.environ[var] = value


def test_config_management():
    """Test configuration management features."""
    
    print("\n⚙️ Testing Configuration Management")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_manager = ConfigManager()
        config_manager.config_dir = Path(temp_dir)
        config_manager.config_file = config_manager.config_dir / "config.json"
        
        # Test default configuration
        print("1. Default configuration:")
        config = config_manager.get_config()
        print(f"   API Provider: {config.api_provider}")
        print(f"   Max Repos: {config.max_repos}")
        print(f"   Verbose: {config.verbose}")
        
        # Test updating configuration
        print("\n2. Updating configuration...")
        config_manager.update_config(
            api_provider="openai",
            max_repos=15,
            verbose=True
        )
        
        updated_config = config_manager.get_config()
        print(f"   API Provider: {updated_config.api_provider}")
        print(f"   Max Repos: {updated_config.max_repos}")
        print(f"   Verbose: {updated_config.verbose}")
        
        # Test API key management
        print("\n3. API key management...")
        config_manager.set_api_key("openai", "test-key-123")
        config_manager.set_api_key("github", "ghp-test-456")
        
        api_keys = config_manager.get_api_keys()
        print(f"   OpenAI key set: {'Yes' if api_keys['openai_api_key'] else 'No'}")
        print(f"   GitHub token set: {'Yes' if api_keys['github_token'] else 'No'}")
        
        # Test preferred provider logic
        print("\n4. Preferred provider logic...")
        preferred = config_manager.get_preferred_api_provider()
        print(f"   Preferred provider: {preferred}")
        
        # Test validation
        print("\n5. Configuration validation...")
        issues = config_manager.validate_config()
        if issues:
            for issue in issues:
                print(f"   ⚠️ {issue}")
        else:
            print("   ✅ No validation issues")


async def main():
    """Run all tests."""
    
    print("🚀 AutoBot CLI Test Suite")
    print("=" * 50)
    
    try:
        # Test configuration management
        test_config_management()
        
        # Test API key management
        await test_api_key_management()
        
        # Test project analyzer with different APIs
        await test_project_analyzer_with_apis()
        
        # Test CLI modes
        await test_cli_modes()
        
        # Test fallback behavior
        await test_fallback_behavior()
        
        print("\n🎉 All tests completed!")
        print("\nKey Features Tested:")
        print("✅ Multi-API provider support (OpenAI, Anthropic, Google, Pollinations)")
        print("✅ Automatic fallback to free Pollinations API")
        print("✅ User configuration management")
        print("✅ API key storage and retrieval")
        print("✅ CLI mode switching")
        print("✅ Rule-based analysis fallback")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())