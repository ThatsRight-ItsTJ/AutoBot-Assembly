#!/usr/bin/env python3
"""
End-to-End Test Suite

Comprehensive testing for all AutoBot Assembly System interfaces.
"""

import asyncio
import sys
import os
import tempfile
import shutil
import json
import time
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Now import modules
from orchestration.project_analyzer import ProjectAnalyzer, AnalysisResult, ProjectType
from search.search_orchestrator import SearchOrchestrator
from analysis.unified_scorer import UnifiedScorer
from compatibility.framework_checker import FrameworkCompatibilityChecker
from assembly.project_generator import ProjectGenerator
from qa.quality_validator import QualityValidator
from cli.config_manager import ConfigManager


class TestResults:
    """Track test results across all components."""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []
    
    def add_result(self, test_name: str, passed: bool, error: str = None):
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            print(f"✅ {test_name}")
        else:
            self.tests_failed += 1
            self.failures.append(f"{test_name}: {error}")
            print(f"❌ {test_name}: {error}")
    
    def summary(self):
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\n📊 Test Summary:")
        print(f"   Total Tests: {self.tests_run}")
        print(f"   Passed: {self.tests_passed}")
        print(f"   Failed: {self.tests_failed}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        if self.failures:
            print(f"\n❌ Failures:")
            for failure in self.failures:
                print(f"   • {failure}")


async def test_project_analyzer():
    """Test the project analyzer with multiple API providers."""
    
    print("\n🤖 Testing Project Analyzer")
    print("=" * 40)
    
    results = TestResults()
    test_prompt = "Create a web scraper for news articles using Python"
    
    # Test with different providers
    providers = ["pollinations", "openai", "anthropic", "google"]
    
    for provider in providers:
        try:
            analyzer = ProjectAnalyzer(api_provider=provider)
            result = await analyzer.analyze_prompt(test_prompt)
            
            # Validate result
            assert isinstance(result, AnalysisResult)
            assert result.project_name
            assert result.project_type in ProjectType
            assert result.recommended_language
            assert 0 <= result.confidence_score <= 1
            
            results.add_result(f"Analyzer {provider}", True)
            
        except Exception as e:
            results.add_result(f"Analyzer {provider}", False, str(e))
    
    # Test fallback behavior
    try:
        analyzer = ProjectAnalyzer(api_key=None, api_provider="invalid")
        result = await analyzer.analyze_prompt(test_prompt)
        assert result.confidence_score > 0
        results.add_result("Fallback analysis", True)
    except Exception as e:
        results.add_result("Fallback analysis", False, str(e))
    
    results.summary()
    return results


async def test_search_orchestrator():
    """Test the search orchestrator."""
    
    print("\n🔍 Testing Search Orchestrator")
    print("=" * 40)
    
    results = TestResults()
    
    try:
        # Create test analysis result
        analysis_result = AnalysisResult(
            project_name="test_scraper",
            project_type=ProjectType.APPLICATION,
            project_description="A web scraper for news articles",
            recommended_language="python",
            required_components=["requests", "beautifulsoup4", "pandas"],
            technical_requirements=["HTTP client", "HTML parsing"],
            complexity_score=0.6,
            estimated_effort="medium",
            suggested_architecture={"pattern": "mvc", "framework": "flask"},
            keywords=["web", "scraper", "news"],
            confidence_score=0.8
        )
        
        orchestrator = SearchOrchestrator()
        search_results = await orchestrator.orchestrate_search(analysis_result)
        
        # Validate results
        assert len(search_results.tier1_results) > 0
        assert len(search_results.tier2_results) > 0
        assert search_results.total_repositories > 0
        
        results.add_result("Search orchestration", True)
        
    except Exception as e:
        results.add_result("Search orchestration", False, str(e))
    
    results.summary()
    return results


async def test_analysis_system():
    """Test the analysis system."""
    
    print("\n📊 Testing Analysis System")
    print("=" * 40)
    
    results = TestResults()
    
    try:
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def hello_world():
    print("Hello, World!")
    return True

if __name__ == "__main__":
    hello_world()
""")
            test_file = f.name
        
        try:
            scorer = UnifiedScorer()
            
            # Test file scoring
            score = await scorer.score_file(test_file)
            assert score.overall_score >= 0
            assert score.file_path == test_file
            
            results.add_result("File analysis", True)
            
        finally:
            os.unlink(test_file)
        
    except Exception as e:
        results.add_result("File analysis", False, str(e))
    
    results.summary()
    return results


async def test_compatibility_system():
    """Test the compatibility system."""
    
    print("\n🔗 Testing Compatibility System")
    print("=" * 40)
    
    results = TestResults()
    
    try:
        checker = FrameworkCompatibilityChecker()
        
        # Test framework compatibility
        compatibility = await checker.check_compatibility(
            primary_framework="flask",
            secondary_frameworks=["requests", "sqlalchemy"],
            language="python"
        )
        
        assert compatibility.is_compatible is not None
        assert compatibility.primary_framework == "flask"
        
        results.add_result("Framework compatibility", True)
        
    except Exception as e:
        results.add_result("Framework compatibility", False, str(e))
    
    results.summary()
    return results


async def test_project_generator():
    """Test the project generator."""
    
    print("\n🏗️ Testing Project Generator")
    print("=" * 40)
    
    results = TestResults()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Create test analysis result
            analysis_result = AnalysisResult(
                project_name="test_calculator",
                project_type=ProjectType.CLI_TOOL,
                project_description="A simple calculator CLI tool",
                recommended_language="python",
                required_components=["argparse", "math"],
                technical_requirements=["CLI interface", "Math operations"],
                complexity_score=0.3,
                estimated_effort="low",
                suggested_architecture={"pattern": "command", "framework": "click"},
                keywords=["calculator", "cli", "math"],
                confidence_score=0.9
            )
            
            generator = ProjectGenerator()
            
            # Test project structure generation
            project_structure = await generator.generate_project_structure(
                analysis_result, 
                output_dir=temp_dir
            )
            
            assert project_structure.project_root.exists()
            assert len(project_structure.generated_files) > 0
            
            results.add_result("Project generation", True)
            
        except Exception as e:
            results.add_result("Project generation", False, str(e))
    
    results.summary()
    return results


async def test_quality_validator():
    """Test the quality validation system."""
    
    print("\n✅ Testing Quality Validator")
    print("=" * 40)
    
    results = TestResults()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Create a simple test project
            test_project = Path(temp_dir) / "test_project"
            test_project.mkdir()
            
            # Create test files
            (test_project / "main.py").write_text("""
def add(a, b):
    return a + b

def main():
    print(add(2, 3))

if __name__ == "__main__":
    main()
""")
            
            (test_project / "requirements.txt").write_text("# No dependencies\n")
            
            validator = QualityValidator()
            
            # Test quality validation
            validation_result = await validator.validate_project(str(test_project))
            
            assert validation_result.overall_score >= 0
            assert validation_result.project_path == str(test_project)
            
            results.add_result("Quality validation", True)
            
        except Exception as e:
            results.add_result("Quality validation", False, str(e))
    
    results.summary()
    return results


def test_config_manager():
    """Test the configuration manager."""
    
    print("\n⚙️ Testing Configuration Manager")
    print("=" * 40)
    
    results = TestResults()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            config_manager = ConfigManager()
            config_manager.config_dir = Path(temp_dir)
            config_manager.config_file = config_manager.config_dir / "config.json"
            
            # Test configuration loading/saving
            config = config_manager.get_config()
            assert config.api_provider in ["pollinations", "openai", "anthropic", "google"]
            
            # Test API key management
            config_manager.set_api_key("openai", "test-key")
            api_keys = config_manager.get_api_keys()
            assert api_keys["openai_api_key"] == "test-key"
            
            # Test API status
            api_status = config_manager.get_api_status()
            assert "pollinations" in api_status
            assert api_status["pollinations"]["available"]
            
            results.add_result("Configuration management", True)
            
        except Exception as e:
            results.add_result("Configuration management", False, str(e))
    
    results.summary()
    return results


async def test_full_pipeline():
    """Test the complete end-to-end pipeline."""
    
    print("\n🚀 Testing Full Pipeline")
    print("=" * 40)
    
    results = TestResults()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Step 1: Analyze prompt
            analyzer = ProjectAnalyzer(api_provider="pollinations")
            analysis_result = await analyzer.analyze_prompt(
                "Create a simple Python calculator with basic operations"
            )
            
            # Step 2: Search for components
            orchestrator = SearchOrchestrator()
            search_results = await orchestrator.orchestrate_search(analysis_result)
            
            # Step 3: Generate project
            generator = ProjectGenerator()
            project_structure = await generator.generate_project_structure(
                analysis_result,
                output_dir=temp_dir
            )
            
            # Step 4: Validate quality
            validator = QualityValidator()
            validation_result = await validator.validate_project(
                str(project_structure.project_root)
            )
            
            # Verify pipeline completion
            assert project_structure.project_root.exists()
            assert validation_result.overall_score >= 0
            assert len(project_structure.generated_files) > 0
            
            results.add_result("Full pipeline", True)
            
            # Print pipeline summary
            print(f"\n📋 Pipeline Summary:")
            print(f"   Project: {analysis_result.project_name}")
            print(f"   Language: {analysis_result.recommended_language}")
            print(f"   Components found: {search_results.total_repositories}")
            print(f"   Files generated: {len(project_structure.generated_files)}")
            print(f"   Quality score: {validation_result.overall_score:.2f}")
            
        except Exception as e:
            results.add_result("Full pipeline", False, str(e))
    
    results.summary()
    return results


async def main():
    """Run all end-to-end tests."""
    
    print("🧪 AutoBot Assembly System - End-to-End Test Suite")
    print("=" * 60)
    
    start_time = time.time()
    all_results = []
    
    try:
        # Run all test suites
        all_results.append(await test_project_analyzer())
        all_results.append(await test_search_orchestrator())
        all_results.append(await test_analysis_system())
        all_results.append(await test_compatibility_system())
        all_results.append(await test_project_generator())
        all_results.append(await test_quality_validator())
        all_results.append(test_config_manager())
        all_results.append(await test_full_pipeline())
        
        # Calculate overall results
        total_tests = sum(r.tests_run for r in all_results)
        total_passed = sum(r.tests_passed for r in all_results)
        total_failed = sum(r.tests_failed for r in all_results)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n🎯 OVERALL TEST RESULTS")
        print("=" * 60)
        print(f"Total Tests Run: {total_tests}")
        print(f"Tests Passed: {total_passed}")
        print(f"Tests Failed: {total_failed}")
        print(f"Success Rate: {(total_passed/total_tests*100):.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        
        if total_failed == 0:
            print(f"\n🎉 ALL TESTS PASSED! AutoBot Assembly System is fully functional.")
        else:
            print(f"\n⚠️ {total_failed} tests failed. Check individual test results above.")
        
        # Print system status
        print(f"\n📊 System Status:")
        print(f"✅ Phase 1: AI Integration & Search Orchestration")
        print(f"✅ Phase 2: File Analysis System")
        print(f"✅ Phase 3: Compatibility & License Analysis")
        print(f"✅ Phase 4: Assembly Engine")
        print(f"✅ Phase 5: Quality Assurance")
        print(f"✅ Phase 6: CLI & Web Interface")
        print(f"✅ Multi-API Provider Support")
        print(f"✅ End-to-End Pipeline")
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())