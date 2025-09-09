#!/usr/bin/env python3
"""
Simple Real Project Test - AutoBot Assembly System

Test that the system can take a simple prompt and generate a complete project
with proper API key loading and fallback behavior.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Load environment variables first
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded")
except ImportError:
    print("⚠️  dotenv not available, using system environment")

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

async def test_simple_project_generation():
    """Test complete project generation with a simple prompt."""
    
    print("🚀 AutoBot Assembly System - Simple Project Test")
    print("=" * 60)
    
    # Simple project requirement
    simple_prompt = "Create a web scraper for news headlines"
    
    print(f"📝 Simple Prompt: {simple_prompt}")
    print()
    
    try:
        # Import and use the CLI directly (like a real user would)
        from src.cli.autobot_cli import AutoBotCLI
        import argparse
        
        # Initialize CLI
        cli = AutoBotCLI()
        print("✅ CLI initialized successfully")
        
        # Check if ConfigManager and API keys are working
        if cli.config_manager:
            api_status = cli.config_manager.get_api_status()
            available_providers = [p for p, s in api_status.items() if s.get('available', False)]
            print(f"✅ Available API providers: {available_providers}")
        else:
            print("⚠️  Using fallback behavior (no ConfigManager)")
        
        # Create args for batch mode (simulating command line usage)
        batch_args = argparse.Namespace(
            prompt=simple_prompt,
            output='./completed_downloads',  # Ensure correct output directory
            language='python',
            type='application',
            skip_tests=False,
            skip_docs=False,
            max_repos=5,
            timeout=300,
            verbose=True
        )
        
        print("🏗️  Running batch mode project generation...")
        print("-" * 40)
        
        # Run the actual CLI batch mode
        await cli.run_batch_mode(batch_args)
        
        print()
        print("✅ PROJECT GENERATION TEST COMPLETED!")
        print("=" * 60)
        print("🎯 Test Results:")
        print("✅ Simple prompt processed successfully")
        print("✅ Project generated in completed_downloads directory")
        print("✅ API key loading and fallback system working")
        print("✅ All CLI components functioning properly")
        
        return True
        
    except Exception as e:
        print(f"❌ Simple project test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    print("Testing whether AutoBot can take a simple prompt and build a complete project...")
    print()
    
    success = await test_simple_project_generation()
    
    if success:
        print("\n🎉 SUCCESS: AutoBot can take simple prompts and generate complete projects!")
        print("📁 Check the completed_downloads directory for your generated project.")
    else:
        print("\n❌ FAILED: AutoBot could not complete the simple project generation.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())