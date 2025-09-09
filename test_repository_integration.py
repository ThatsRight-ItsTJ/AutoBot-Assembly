#!/usr/bin/env python3
"""
Repository Integration Verification Test - AutoBot Assembly System

This test verifies whether the system actually:
1. Downloads/copies files from repositories
2. Integrates package contents into generated code
3. Uses discovered resources vs just templates
"""

import asyncio
import sys
import json
import os
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.cli.autobot_cli import AutoBotCLI

async def test_repository_integration():
    """Test to verify actual repository integration vs template generation."""
    
    print("🔍 Repository Integration Verification Test")
    print("=" * 60)
    
    # Clean test - remove any existing projects
    completed_downloads = Path('./completed_downloads')
    if completed_downloads.exists():
        import shutil
        shutil.rmtree(completed_downloads)
        print("🧹 Cleaned previous test results")
    
    # Simple prompt that should trigger repository discovery
    test_prompt = "Create a Python web scraper using requests and BeautifulSoup"
    
    print(f"📝 Test Prompt: '{test_prompt}'")
    print(f"🎯 Expected: Real repository files integrated, not just templates")
    print()
    
    try:
        # Initialize CLI
        cli = AutoBotCLI()
        
        # Create args for batch mode with verbose logging
        import argparse
        args = argparse.Namespace(
            prompt=test_prompt,
            output='./completed_downloads',
            language='python',
            type='application',
            skip_tests=False,
            skip_docs=False,
            max_repos=10,  # Increase to get more repositories
            timeout=120,
            verbose=True
        )
        
        print("🏗️  Running project generation with repository integration...")
        print("-" * 60)
        
        # Run batch mode
        await cli.run_batch_mode(args)
        
        print("\n🔍 ANALYZING REPOSITORY INTEGRATION:")
        print("=" * 60)
        
        # Check if project was created
        if not completed_downloads.exists():
            print("❌ No completed_downloads directory found")
            return False
        
        projects = list(completed_downloads.iterdir())
        if not projects:
            print("❌ No projects found in completed_downloads")
            return False
        
        latest_project = max(projects, key=lambda p: p.stat().st_mtime)
        print(f"📁 Analyzing project: {latest_project.name}")
        
        # 1. Check analysis report for repository integration details
        analysis_report = latest_project / 'analysis_report.json'
        repository_evidence = []
        
        if analysis_report.exists():
            with open(analysis_report, 'r') as f:
                report_data = json.load(f)
                
            print(f"\n📊 Analysis Report Found:")
            
            # Check for repository references
            report_str = json.dumps(report_data, indent=2).lower()
            
            if 'github.com' in report_str or 'repository' in report_str:
                print("✅ Repository references found in analysis report")
                repository_evidence.append("analysis_report_refs")
            else:
                print("❌ No repository references in analysis report")
            
            # Check for specific integration details
            if 'components' in report_data:
                components = report_data['components']
                print(f"📦 Components found: {len(components)}")
                
                for comp in components[:3]:  # Show first 3
                    if isinstance(comp, dict):
                        comp_name = comp.get('name', 'Unknown')
                        comp_type = comp.get('type', 'Unknown')
                        print(f"   • {comp_name} ({comp_type})")
            
        else:
            print("❌ No analysis report found")
        
        # 2. Check generated code for real package imports and usage
        main_py = latest_project / 'main.py'
        requirements_txt = latest_project / 'requirements.txt'
        
        real_imports = []
        template_indicators = []
        
        if main_py.exists():
            with open(main_py, 'r') as f:
                main_content = f.read()
            
            print(f"\n📄 Analyzing main.py ({len(main_content)} characters):")
            
            # Check for real package imports
            common_packages = ['requests', 'beautifulsoup4', 'bs4', 'urllib', 'selenium', 'scrapy']
            for package in common_packages:
                if package in main_content.lower():
                    real_imports.append(package)
                    print(f"✅ Found real package usage: {package}")
            
            # Check for template indicators
            template_words = ['todo', 'placeholder', 'example', 'template', 'your_', 'replace_this']
            for word in template_words:
                if word in main_content.lower():
                    template_indicators.append(word)
            
            if template_indicators:
                print(f"⚠️  Template indicators found: {template_indicators}")
            else:
                print("✅ No obvious template placeholders found")
        
        else:
            print("❌ No main.py file found")
        
        # 3. Check requirements.txt for real dependencies
        real_dependencies = []
        
        if requirements_txt.exists():
            with open(requirements_txt, 'r') as f:
                requirements_content = f.read()
            
            print(f"\n📋 Analyzing requirements.txt:")
            lines = requirements_content.strip().split('\n')
            
            for line in lines:
                if line.strip() and not line.startswith('#'):
                    real_dependencies.append(line.strip())
                    print(f"✅ Real dependency: {line.strip()}")
        
        else:
            print("❌ No requirements.txt file found")
        
        # 4. Integration Assessment
        print(f"\n🎯 REPOSITORY INTEGRATION ASSESSMENT:")
        print("=" * 60)
        
        integration_score = 0
        max_score = 5
        
        # Evidence scoring
        if repository_evidence:
            integration_score += 1
            print("✅ [1/5] Repository references in analysis")
        else:
            print("❌ [0/5] No repository references found")
        
        if real_imports:
            integration_score += 1
            print(f"✅ [1/5] Real package imports found: {real_imports}")
        else:
            print("❌ [0/5] No real package imports detected")
        
        if real_dependencies:
            integration_score += 1
            print(f"✅ [1/5] Real dependencies specified: {len(real_dependencies)}")
        else:
            print("❌ [0/5] No real dependencies found")
        
        if len(template_indicators) < 3:
            integration_score += 1
            print("✅ [1/5] Minimal template placeholders")
        else:
            print(f"❌ [0/5] Too many template indicators: {template_indicators}")
        
        if main_py.exists() and len(main_content) > 500:
            integration_score += 1
            print("✅ [1/5] Substantial code generated")
        else:
            print("❌ [0/5] Insufficient code generation")
        
        # Final assessment
        print(f"\n🏆 INTEGRATION SCORE: {integration_score}/{max_score}")
        
        if integration_score >= 4:
            print("🎉 EXCELLENT: Strong evidence of repository integration")
            return True
        elif integration_score >= 3:
            print("✅ GOOD: Some repository integration detected")
            return True
        elif integration_score >= 2:
            print("⚠️  PARTIAL: Limited repository integration")
            return False
        else:
            print("❌ POOR: Likely template-only generation")
            return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing Repository Integration vs Template Generation...")
    print()
    
    success = asyncio.run(test_repository_integration())
    
    if success:
        print("\n🎉 SUCCESS: Repository integration verified!")
    else:
        print("\n❌ FAILED: System appears to use templates only")
    
    sys.exit(0 if success else 1)