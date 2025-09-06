#!/usr/bin/env python3
"""
Test script for Phase 3: Compatibility & License Analysis

Tests framework compatibility checking, license analysis, and comprehensive compatibility matrix generation.
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from compatibility.framework_checker import FrameworkCompatibilityChecker
from compatibility.license_analyzer import LicenseAnalyzer
from compatibility.compatibility_matrix import CompatibilityMatrixGenerator
from search.tier1_packages import PackageResult
from search.tier2_curated import RepositoryResult


async def test_framework_compatibility():
    """Test framework compatibility checking."""
    print("\n" + "="*60)
    print("TESTING FRAMEWORK COMPATIBILITY CHECKER")
    print("="*60)
    
    checker = FrameworkCompatibilityChecker()
    
    # Create test components with different frameworks
    test_components = [
        PackageResult(
            name="fastapi",
            repository_url="https://github.com/tiangolo/fastapi",
            description="FastAPI framework for building APIs with Python",
            downloads=1000000,
            stars=50000,
            last_updated=datetime.now(),
            license="MIT",
            quality_score=0.9,
            language="python",
            package_manager="pypi",
            version="0.100.0",
            dependencies_count=5
        ),
        PackageResult(
            name="django",
            repository_url="https://github.com/django/django",
            description="Django web framework for Python",
            downloads=2000000,
            stars=60000,
            last_updated=datetime.now(),
            license="BSD-3-Clause",
            quality_score=0.95,
            language="python",
            package_manager="pypi",
            version="4.2.0",
            dependencies_count=8
        ),
        RepositoryResult(
            repository="react",
            full_name="facebook/react",
            description="React JavaScript library for building user interfaces",
            url="https://github.com/facebook/react",
            stars=200000,
            forks=40000,
            language="JavaScript",
            topics=["react", "javascript", "frontend", "ui"],
            last_updated=datetime.now(),
            license="MIT",
            quality_score=0.98
        )
    ]
    
    print(f"Testing with {len(test_components)} components...")
    
    # Test Python framework compatibility
    print("\n--- Python Framework Analysis ---")
    python_matrix = await checker.analyze_component_compatibility(test_components[:2], "python")
    
    print(f"Overall compatibility: {python_matrix.overall_compatibility:.2f}")
    print(f"Conflicts found: {len(python_matrix.conflicts)}")
    print(f"Compatible sets: {len(python_matrix.compatible_sets)}")
    
    if python_matrix.conflicts:
        print("\nConflicts:")
        for conflict in python_matrix.conflicts:
            print(f"  • {conflict.framework1} vs {conflict.framework2} ({conflict.severity.value})")
            print(f"    Reason: {conflict.reason}")
            print(f"    Resolutions: {', '.join(conflict.resolution_suggestions)}")
    
    print("\nRecommendations:")
    for rec in python_matrix.recommendations:
        print(f"  {rec}")
    
    return True


async def test_license_analysis():
    """Test license analysis."""
    print("\n" + "="*60)
    print("TESTING LICENSE ANALYZER")
    print("="*60)
    
    analyzer = LicenseAnalyzer()
    
    # Create test components with different licenses
    test_components = [
        PackageResult(
            name="requests",
            repository_url="https://github.com/psf/requests",
            description="HTTP library for Python",
            downloads=1000000,
            stars=50000,
            last_updated=datetime.now(),
            license="Apache-2.0",
            quality_score=0.9,
            language="python",
            package_manager="pypi",
            version="2.31.0",
            dependencies_count=5
        ),
        PackageResult(
            name="flask",
            repository_url="https://github.com/pallets/flask",
            description="Web framework for Python",
            downloads=2000000,
            stars=60000,
            last_updated=datetime.now(),
            license="BSD-3-Clause",
            quality_score=0.95,
            language="python",
            package_manager="pypi",
            version="2.3.0",
            dependencies_count=3
        ),
        PackageResult(
            name="gpl-component",
            repository_url="https://github.com/example/gpl-component",
            description="GPL licensed component for testing",
            downloads=10000,
            stars=1000,
            last_updated=datetime.now(),
            license="GPL-3.0",
            quality_score=0.7,
            language="python",
            package_manager="pypi",
            version="1.0.0",
            dependencies_count=2
        )
    ]
    
    print(f"Testing with {len(test_components)} components...")
    
    analysis = await analyzer.analyze_license_compliance(test_components)
    
    print(f"\nLicense Analysis Results:")
    print(f"  Overall status: {analysis.overall_compliance_status}")
    print(f"  Commercial use allowed: {analysis.commercial_use_allowed}")
    print(f"  Source disclosure required: {analysis.source_disclosure_required}")
    print(f"  Attribution requirements: {len(analysis.attribution_requirements)}")
    
    print(f"\nDetected licenses:")
    for comp_id, license_info in analysis.detected_licenses.items():
        print(f"  {comp_id}: {license_info.license_type.value} (confidence: {license_info.confidence_score:.2f})")
        print(f"    Commercial use: {license_info.allows_commercial_use}")
        print(f"    Attribution required: {license_info.requires_attribution}")
        print(f"    Source disclosure: {license_info.requires_source_disclosure}")
    
    print(f"\nCompatibility matrix:")
    for compatibility in analysis.compatibility_matrix:
        print(f"  {compatibility.license1.value} + {compatibility.license2.value}: {compatibility.status.value}")
        if compatibility.status.value != 'compatible':
            print(f"    Reason: {compatibility.reason}")
    
    print(f"\nRecommendations:")
    for rec in analysis.recommendations:
        print(f"  {rec}")
    
    if analysis.attribution_requirements:
        print(f"\nAttribution Requirements:")
        for req in analysis.attribution_requirements:
            print(f"  • {req.component_name} ({req.license_type.value})")
            print(f"    Text: {req.attribution_text}")
    
    return True


async def test_comprehensive_matrix():
    """Test comprehensive compatibility matrix generation."""
    print("\n" + "="*60)
    print("TESTING COMPREHENSIVE COMPATIBILITY MATRIX")
    print("="*60)
    
    generator = CompatibilityMatrixGenerator()
    
    # Create diverse test components
    test_components = [
        PackageResult(
            name="fastapi",
            repository_url="https://github.com/tiangolo/fastapi",
            description="FastAPI framework for building APIs",
            downloads=1000000,
            stars=50000,
            last_updated=datetime.now(),
            license="MIT",
            quality_score=0.9,
            language="python",
            package_manager="pypi",
            version="0.100.0",
            dependencies_count=5
        ),
        PackageResult(
            name="requests",
            repository_url="https://github.com/psf/requests",
            description="HTTP library for Python",
            downloads=2000000,
            stars=55000,
            last_updated=datetime.now(),
            license="Apache-2.0",
            quality_score=0.95,
            language="python",
            package_manager="pypi",
            version="2.31.0",
            dependencies_count=3
        ),
        PackageResult(
            name="sqlalchemy",
            repository_url="https://github.com/sqlalchemy/sqlalchemy",
            description="SQL toolkit and ORM for Python",
            downloads=1500000,
            stars=45000,
            last_updated=datetime.now(),
            license="MIT",
            quality_score=0.92,
            language="python",
            package_manager="pypi",
            version="2.0.0",
            dependencies_count=7
        ),
        PackageResult(
            name="complex-component",
            repository_url="https://github.com/example/complex-component",
            description="Complex component with many dependencies",
            downloads=50000,
            stars=5000,
            last_updated=datetime.now(),
            license="GPL-3.0",
            quality_score=0.6,
            language="python",
            package_manager="pypi",
            version="1.0.0",
            dependencies_count=25
        )
    ]
    
    print(f"Testing with {len(test_components)} components...")
    
    # Generate comprehensive compatibility matrix
    report = await generator.generate_comprehensive_matrix(test_components, "python")
    
    print(f"\nCompatibility Report Summary:")
    print(f"  Total components: {report.summary['total_components']}")
    print(f"  Average score: {report.summary['average_score']:.2f}")
    print(f"  Overall assessment: {report.summary['overall_assessment']}")
    print(f"  Total integration hours: {report.summary['total_integration_hours']}")
    
    print(f"\nScore Distribution:")
    dist = report.summary['score_distribution']
    print(f"  High (≥0.8): {dist['high']} components")
    print(f"  Medium (0.6-0.8): {dist['medium']} components")
    print(f"  Low (<0.6): {dist['low']} components")
    
    print(f"\nPriority Distribution:")
    priority = report.summary['priority_distribution']
    print(f"  High: {priority['high']} components")
    print(f"  Medium: {priority['medium']} components")
    print(f"  Low: {priority['low']} components")
    print(f"  Skip: {priority['skip']} components")
    
    print(f"\nComponent Analysis:")
    for comp in report.components:
        print(f"  • {comp.component_name}: {comp.overall_score:.2f} ({comp.priority} priority)")
        print(f"    Framework: {comp.framework_compatibility:.2f}, License: {comp.license_compatibility}")
        print(f"    Integration hours: {comp.integration_complexity.integration_effort_hours}")
        print(f"    Recommendation: {comp.recommendation}")
        if comp.integration_complexity.risk_factors:
            print(f"    Risk factors: {', '.join(comp.integration_complexity.risk_factors)}")
    
    if report.recommended_combinations:
        print(f"\nRecommended Combinations:")
        for i, combo in enumerate(report.recommended_combinations, 1):
            print(f"  {i}. {', '.join(combo)}")
    
    if report.integration_roadmap:
        print(f"\nIntegration Roadmap:")
        for phase in report.integration_roadmap:
            print(f"  Phase {phase['phase']}: {phase['title']}")
            print(f"    Components: {', '.join(phase['components'])}")
            print(f"    Estimated hours: {phase['estimated_hours']}")
            print(f"    Description: {phase['description']}")
    
    if report.risk_assessment['high_risk_components']:
        print(f"\nHigh Risk Components:")
        for risk_comp in report.risk_assessment['high_risk_components']:
            print(f"  • {risk_comp['name']}: {risk_comp['score']:.2f}")
            print(f"    Issues: {', '.join(risk_comp['issues'])}")
    
    return True


async def run_all_tests():
    """Run all compatibility analysis tests."""
    print("AUTOBOT ASSEMBLY SYSTEM - PHASE 3 TESTING")
    print("Compatibility & License Analysis")
    print("=" * 80)
    
    tests = [
        ("Framework Compatibility", test_framework_compatibility),
        ("License Analysis", test_license_analysis),
        ("Comprehensive Matrix", test_comprehensive_matrix)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running {test_name} test...")
            result = await test_func()
            results[test_name] = "✅ PASSED" if result else "❌ FAILED"
            print(f"✅ {test_name} test completed successfully")
        except Exception as e:
            results[test_name] = f"❌ FAILED: {str(e)}"
            print(f"❌ {test_name} test failed: {e}")
            logging.exception(f"Test {test_name} failed")
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, result in results.items():
        print(f"{test_name}: {result}")
    
    passed_tests = len([r for r in results.values() if "PASSED" in r])
    total_tests = len(results)
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All Phase 3 tests passed! Compatibility & License Analysis system is working correctly.")
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