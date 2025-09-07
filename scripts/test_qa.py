#!/usr/bin/env python3
"""
Test script for Phase 5: Quality Assurance

Tests integration testing, quality validation, and documentation generation.
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from qa.integration_tester import IntegrationTester
from qa.quality_validator import QualityValidator
from qa.documentation_generator import DocumentationGenerator, DocType
from assembly.project_generator import ProjectGenerator, ProjectType, GeneratedProject, ProjectStructure


async def create_test_project():
    """Create a test project for QA testing."""
    
    # Create a temporary test project
    test_project_path = Path(tempfile.mkdtemp(prefix="autobot_qa_test_"))
    
    # Create basic project structure
    src_dir = test_project_path / "src"
    src_dir.mkdir()
    
    tests_dir = test_project_path / "tests"
    tests_dir.mkdir()
    
    # Create main.py
    main_content = '''#!/usr/bin/env python3
"""
Test project main module
"""

def hello_world():
    """Return a greeting message."""
    return "Hello, World!"

def calculate_sum(a, b):
    """Calculate sum of two numbers."""
    return a + b

class Calculator:
    """Simple calculator class."""
    
    def add(self, a, b):
        """Add two numbers."""
        return a + b
    
    def multiply(self, a, b):
        """Multiply two numbers."""
        return a * b

def main():
    """Main entry point."""
    print(hello_world())
    calc = Calculator()
    result = calc.add(5, 3)
    print(f"5 + 3 = {result}")

if __name__ == "__main__":
    main()
'''
    
    with open(test_project_path / "main.py", 'w') as f:
        f.write(main_content)
    
    # Create src module
    src_module_content = '''"""
Source module for testing
"""

import os
import json

def process_data(data):
    """Process input data."""
    if not data:
        return None
    
    return {
        'processed': True,
        'length': len(str(data)),
        'type': type(data).__name__
    }

class DataProcessor:
    """Data processing class."""
    
    def __init__(self):
        self.processed_count = 0
    
    def process(self, item):
        """Process a single item."""
        self.processed_count += 1
        return f"Processed: {item}"
'''
    
    with open(src_dir / "processor.py", 'w') as f:
        f.write(src_module_content)
    
    # Create __init__.py files
    with open(src_dir / "__init__.py", 'w') as f:
        f.write('"""Source package"""')
    
    with open(tests_dir / "__init__.py", 'w') as f:
        f.write('"""Tests package"""')
    
    # Create a test file
    test_content = '''"""
Test module
"""

import unittest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from processor import process_data, DataProcessor

class TestProcessor(unittest.TestCase):
    """Test the processor module."""
    
    def test_process_data(self):
        """Test process_data function."""
        result = process_data("test")
        self.assertIsNotNone(result)
        self.assertTrue(result['processed'])
    
    def test_data_processor(self):
        """Test DataProcessor class."""
        processor = DataProcessor()
        result = processor.process("item")
        self.assertEqual(processor.processed_count, 1)

if __name__ == "__main__":
    unittest.main()
'''
    
    with open(tests_dir / "test_processor.py", 'w') as f:
        f.write(test_content)
    
    # Create requirements.txt
    requirements_content = '''requests>=2.25.0
flask>=2.0.0
pytest>=6.0.0
'''
    
    with open(test_project_path / "requirements.txt", 'w') as f:
        f.write(requirements_content)
    
    # Create basic README
    readme_content = '''# Test Project

This is a test project for AutoBot Assembly System QA testing.
'''
    
    with open(test_project_path / "README.md", 'w') as f:
        f.write(readme_content)
    
    return test_project_path


async def test_integration_tester():
    """Test integration testing functionality."""
    print("\n" + "="*60)
    print("TESTING INTEGRATION TESTER")
    print("="*60)
    
    # Create test project
    test_project_path = await create_test_project()
    
    try:
        # Create GeneratedProject object
        generated_project = GeneratedProject(
            project_name="qa_test_project",
            project_path=str(test_project_path),
            project_type=ProjectType.APPLICATION,
            structure=ProjectStructure(
                project_type=ProjectType.APPLICATION,
                entry_points=["main.py"],
                source_directories=["src"],
                config_files=["requirements.txt"],
                documentation_files=["README.md"],
                test_directories=["tests"],
                build_files=[]
            ),
            language="python",
            dependencies=["requests>=2.25.0", "flask>=2.0.0", "pytest>=6.0.0"],
            build_commands=["pip install -r requirements.txt"],
            run_commands=["python main.py"],
            test_commands=["python -m pytest tests/"]
        )
        
        # Test integration tester
        tester = IntegrationTester(test_timeout=60)
        
        print(f"Testing integration for project at: {test_project_path}")
        
        test_suite = await tester.test_project(generated_project)
        
        print(f"\nIntegration Test Results:")
        print(f"  Project: {test_suite.project_name}")
        print(f"  Language: {test_suite.language}")
        print(f"  Project Type: {test_suite.project_type}")
        print(f"  Overall Status: {test_suite.overall_status.value}")
        print(f"  Total Tests: {test_suite.total_tests}")
        print(f"  Passed: {test_suite.passed_tests}")
        print(f"  Failed: {test_suite.failed_tests}")
        print(f"  Skipped: {test_suite.skipped_tests}")
        print(f"  Duration: {test_suite.total_duration:.2f}s")
        
        print(f"\nDetailed Test Results:")
        for result in test_suite.test_results:
            status_icon = {"passed": "✅", "failed": "❌", "skipped": "⏭️", "error": "🔥"}.get(result.status.value, "❓")
            print(f"  {status_icon} {result.test_name}: {result.status.value} ({result.duration_seconds:.2f}s)")
            if result.error_message:
                print(f"    Error: {result.error_message}")
            if result.output and len(result.output) < 100:
                print(f"    Output: {result.output}")
        
        return test_suite
        
    finally:
        # Cleanup
        if test_project_path.exists():
            shutil.rmtree(test_project_path)


async def test_quality_validator(test_suite=None):
    """Test quality validation functionality."""
    print("\n" + "="*60)
    print("TESTING QUALITY VALIDATOR")
    print("="*60)
    
    # Create test project
    test_project_path = await create_test_project()
    
    try:
        # Create GeneratedProject object
        generated_project = GeneratedProject(
            project_name="qa_test_project",
            project_path=str(test_project_path),
            project_type=ProjectType.APPLICATION,
            structure=ProjectStructure(
                project_type=ProjectType.APPLICATION,
                entry_points=["main.py"],
                source_directories=["src"],
                config_files=["requirements.txt"],
                documentation_files=["README.md"],
                test_directories=["tests"],
                build_files=[]
            ),
            language="python",
            dependencies=["requests>=2.25.0", "flask>=2.0.0", "pytest>=6.0.0"],
            build_commands=["pip install -r requirements.txt"],
            run_commands=["python main.py"],
            test_commands=["python -m pytest tests/"]
        )
        
        # Test quality validator
        validator = QualityValidator()
        
        print(f"Testing quality validation for project at: {test_project_path}")
        
        validation_result = await validator.validate_project(generated_project, test_suite)
        
        print(f"\nQuality Validation Results:")
        print(f"  Project: {validation_result.project_name}")
        print(f"  Overall Score: {validation_result.overall_score:.3f}/1.0")
        print(f"  Quality Level: {validation_result.overall_quality_level.value.title()}")
        print(f"  Validation Duration: {validation_result.validation_duration:.2f}s")
        
        print(f"\nQuality Metrics:")
        metrics = validation_result.quality_metrics
        print(f"  Complexity Score: {metrics.complexity_score:.3f}")
        print(f"  Maintainability Index: {metrics.maintainability_index:.3f}")
        print(f"  Technical Debt Ratio: {metrics.technical_debt_ratio:.3f}")
        print(f"  Security Score: {metrics.security_score:.3f}")
        print(f"  Performance Score: {metrics.performance_score:.3f}")
        print(f"  Documentation Completeness: {metrics.documentation_completeness:.3f}")
        if metrics.code_coverage:
            print(f"  Code Coverage: {metrics.code_coverage:.3f}")
        
        if validation_result.strengths:
            print(f"\nStrengths:")
            for strength in validation_result.strengths:
                print(f"  ✅ {strength}")
        
        if validation_result.weaknesses:
            print(f"\nWeaknesses:")
            for weakness in validation_result.weaknesses:
                print(f"  ⚠️ {weakness}")
        
        if validation_result.recommendations:
            print(f"\nRecommendations:")
            for rec in validation_result.recommendations[:5]:
                print(f"  💡 {rec}")
        
        if validation_result.benchmark_comparisons:
            print(f"\nBenchmark Comparisons:")
            for metric, comparison in validation_result.benchmark_comparisons.items():
                print(f"  {metric}: {comparison['comparison']} ({comparison['value']:.3f})")
        
        return validation_result
        
    finally:
        # Cleanup
        if test_project_path.exists():
            shutil.rmtree(test_project_path)


async def test_documentation_generator(validation_result=None):
    """Test documentation generation functionality."""
    print("\n" + "="*60)
    print("TESTING DOCUMENTATION GENERATOR")
    print("="*60)
    
    # Create test project
    test_project_path = await create_test_project()
    
    try:
        # Create GeneratedProject object
        generated_project = GeneratedProject(
            project_name="qa_test_project",
            project_path=str(test_project_path),
            project_type=ProjectType.APPLICATION,
            structure=ProjectStructure(
                project_type=ProjectType.APPLICATION,
                entry_points=["main.py"],
                source_directories=["src"],
                config_files=["requirements.txt"],
                documentation_files=["README.md"],
                test_directories=["tests"],
                build_files=[]
            ),
            language="python",
            dependencies=["requests>=2.25.0", "flask>=2.0.0", "pytest>=6.0.0"],
            build_commands=["pip install -r requirements.txt"],
            run_commands=["python main.py"],
            test_commands=["python -m pytest tests/"]
        )
        
        # Test documentation generator
        doc_generator = DocumentationGenerator()
        
        print(f"Testing documentation generation for project at: {test_project_path}")
        
        # Generate different types of documentation
        doc_types = [DocType.README, DocType.USER_GUIDE, DocType.DEVELOPER_GUIDE, DocType.CHANGELOG, DocType.API_DOCS]
        
        doc_result = await doc_generator.generate_documentation(
            generated_project, 
            validation_result, 
            doc_types
        )
        
        print(f"\nDocumentation Generation Results:")
        print(f"  Project: {doc_result.project_name}")
        print(f"  Documentation Coverage: {doc_result.documentation_coverage:.1%}")
        print(f"  Generation Duration: {doc_result.generation_duration:.2f}s")
        print(f"  Generated Documents: {len(doc_result.generated_documents)}")
        
        for doc_type, content in doc_result.generated_documents.items():
            print(f"  📄 {doc_type.value}: {len(content)} characters")
            
            # Show first few lines of each document
            lines = content.split('\n')[:3]
            for line in lines:
                if line.strip():
                    print(f"    {line[:80]}{'...' if len(line) > 80 else ''}")
            print()
        
        if doc_result.warnings:
            print(f"Warnings:")
            for warning in doc_result.warnings:
                print(f"  ⚠️ {warning}")
        
        # Check if files were actually created
        print(f"Generated Files:")
        doc_files = {
            DocType.README: "README.md",
            DocType.USER_GUIDE: "docs/USER_GUIDE.md",
            DocType.DEVELOPER_GUIDE: "docs/DEVELOPER_GUIDE.md",
            DocType.CHANGELOG: "CHANGELOG.md",
            DocType.API_DOCS: "docs/API.md"
        }
        
        for doc_type, filename in doc_files.items():
            file_path = test_project_path / filename
            if file_path.exists():
                size = file_path.stat().st_size
                print(f"  ✅ {filename}: {size} bytes")
            else:
                print(f"  ❌ {filename}: not found")
        
        return doc_result
        
    finally:
        # Cleanup
        if test_project_path.exists():
            shutil.rmtree(test_project_path)


async def test_complete_qa_workflow():
    """Test complete QA workflow."""
    print("\n" + "="*60)
    print("TESTING COMPLETE QA WORKFLOW")
    print("="*60)
    
    # Create test project
    test_project_path = await create_test_project()
    
    try:
        # Create GeneratedProject object
        generated_project = GeneratedProject(
            project_name="complete_qa_test",
            project_path=str(test_project_path),
            project_type=ProjectType.APPLICATION,
            structure=ProjectStructure(
                project_type=ProjectType.APPLICATION,
                entry_points=["main.py"],
                source_directories=["src"],
                config_files=["requirements.txt"],
                documentation_files=["README.md"],
                test_directories=["tests"],
                build_files=[]
            ),
            language="python",
            dependencies=["requests>=2.25.0", "flask>=2.0.0", "pytest>=6.0.0"],
            build_commands=["pip install -r requirements.txt"],
            run_commands=["python main.py"],
            test_commands=["python -m pytest tests/"]
        )
        
        print("Testing complete QA workflow...")
        
        # Step 1: Integration Testing
        print("\n1. Running Integration Tests...")
        tester = IntegrationTester(test_timeout=60)
        test_suite = await tester.test_project(generated_project)
        print(f"   Integration: {test_suite.overall_status.value} ({test_suite.passed_tests}/{test_suite.total_tests} passed)")
        
        # Step 2: Quality Validation
        print("\n2. Running Quality Validation...")
        validator = QualityValidator()
        validation_result = await validator.validate_project(generated_project, test_suite)
        print(f"   Quality: {validation_result.overall_quality_level.value} ({validation_result.overall_score:.3f}/1.0)")
        
        # Step 3: Documentation Generation
        print("\n3. Generating Documentation...")
        doc_generator = DocumentationGenerator()
        doc_result = await doc_generator.generate_documentation(
            generated_project, 
            validation_result,
            [DocType.README, DocType.USER_GUIDE, DocType.DEVELOPER_GUIDE]
        )
        print(f"   Documentation: {doc_result.documentation_coverage:.1%} coverage ({len(doc_result.generated_documents)} docs)")
        
        # Summary
        print(f"\n✅ Complete QA Workflow Results:")
        print(f"  Integration Tests: {test_suite.passed_tests}/{test_suite.total_tests} passed")
        print(f"  Quality Score: {validation_result.overall_score:.3f}/1.0 ({validation_result.overall_quality_level.value})")
        print(f"  Documentation: {len(doc_result.generated_documents)} documents generated")
        print(f"  Total QA Time: {test_suite.total_duration + validation_result.validation_duration + doc_result.generation_duration:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Complete QA workflow failed: {e}")
        return False
        
    finally:
        # Cleanup
        if test_project_path.exists():
            shutil.rmtree(test_project_path)


async def run_all_tests():
    """Run all QA system tests."""
    print("AUTOBOT ASSEMBLY SYSTEM - PHASE 5 TESTING")
    print("Quality Assurance (Integration Tester, Quality Validator, Documentation Generator)")
    print("=" * 100)
    
    tests = [
        ("Integration Testing", test_integration_tester),
        ("Quality Validation", test_quality_validator),
        ("Documentation Generation", test_documentation_generator),
        ("Complete QA Workflow", test_complete_qa_workflow)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running {test_name} test...")
            
            if test_name == "Quality Validation":
                # Run with integration test results
                test_suite = await test_integration_tester()
                result = await test_func(test_suite)
                results["Integration Testing"] = "✅ PASSED"
                results[test_name] = "✅ PASSED" if result else "❌ FAILED"
            elif test_name == "Documentation Generation":
                # Run with validation results
                validation_result = await test_quality_validator()
                result = await test_func(validation_result)
                results["Quality Validation"] = "✅ PASSED" if validation_result else "❌ FAILED"
                results[test_name] = "✅ PASSED" if result else "❌ FAILED"
            else:
                result = await test_func()
                results[test_name] = "✅ PASSED" if result else "❌ FAILED"
            
            print(f"✅ {test_name} test completed successfully")
            
        except Exception as e:
            results[test_name] = f"❌ FAILED: {str(e)}"
            print(f"❌ {test_name} test failed: {e}")
            logging.exception(f"Test {test_name} failed")
    
    # Print summary
    print("\n" + "="*100)
    print("TEST SUMMARY")
    print("="*100)
    
    for test_name, result in results.items():
        print(f"{test_name}: {result}")
    
    passed_tests = len([r for r in results.values() if "PASSED" in r])
    total_tests = len(results)
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All Phase 5 tests passed! Quality Assurance system is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the error messages above.")
        return False


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)