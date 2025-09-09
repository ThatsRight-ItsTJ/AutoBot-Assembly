import logging
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.reporting.ai_integrated_reporter import AIIntegratedReporter
from src.cli.config_manager import ConfigManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ai_reporter():
    """Test the AI Integrated Reporter with different configurations."""
    
    print("🧪 Testing AI Integrated Reporter with flexible API key configuration")
    print("=" * 70)
    
    # Test 1: With ConfigManager
    print("\n1️⃣ Testing with ConfigManager...")
    try:
        config_manager = ConfigManager()
        reporter = AIIntegratedReporter(config_manager=config_manager)
        
        # Test API resolution
        api_config = reporter._resolve_api_config()
        print(f"   ✅ API config resolved: {api_config}")
        
        # Test fallback behavior
        fallback_config = reporter._resolve_api_config('openai')
        print(f"   ✅ Fallback config resolved: {fallback_config}")
        
    except Exception as e:
        print(f"   ❌ ConfigManager test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Without ConfigManager (legacy mode)
    print("\n2️⃣ Testing without ConfigManager (legacy mode)...")
    try:
        reporter = AIIntegratedReporter(config_manager=None)
        
        # Test API resolution
        api_config = reporter._resolve_api_config()
        print(f"   ✅ Legacy API config resolved: {api_config}")
        
        # Verify no hardcoded key
        if api_config.get('api_key') is None:
            print("   ✅ No hardcoded API key found (good!)")
        else:
            print(f"   ⚠️  API key found: {api_config.get('api_key')[:10]}...")
            
    except Exception as e:
        print(f"   ❌ Legacy mode test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Test with mock project data
    print("\n3️⃣ Testing AI analysis with mock data...")
    try:
        # Create minimal project data
        project_data = {
            'name': 'Test Project',
            'language': 'Python',
            'description': 'A test web application',
            'files': ['app.py', 'config.py', 'README.md'],
            'size': 10240
        }
        
        repositories = [
            {
                'name': 'requests',
                'url': 'https://github.com/psf/requests',
                'purpose': 'HTTP requests',
                'license': 'Apache-2.0',
                'files_copied': ['requests/__init__.py']
            }
        ]
        
        # Test with ConfigManager
        config_manager = ConfigManager()
        reporter = AIIntegratedReporter(config_manager=config_manager)
        
        # Test executive summary generation
        summary = await reporter._generate_executive_summary(project_data, repositories)
        print(f"   ✅ Executive summary generated ({len(summary)} chars)")
        
        # Test AI analysis
        analysis = await reporter._get_ai_analysis(
            "Test project analysis",
            "executive_summary"
        )
        print(f"   ✅ AI analysis generated ({len(analysis)} chars)")
        
    except Exception as e:
        print(f"   ❌ Mock data test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("🎉 AI Integrated Reporter test completed!")

if __name__ == "__main__":
    asyncio.run(test_ai_reporter())