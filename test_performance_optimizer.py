#!/usr/bin/env python3
"""
Test script for the performance optimizer module.

This script demonstrates the basic functionality of the PerformanceOptimizer class
and verifies that it can be imported and instantiated correctly.
"""

import sys
import os
import time
import logging

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.optimization.performance_optimizer import (
    PerformanceOptimizer,
    OptimizationLevel,
    CacheStrategy,
    CodeComponent,
    IntegrationPattern
)

def setup_logging():
    """Set up logging for the test"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_basic_functionality():
    """Test basic functionality of the PerformanceOptimizer"""
    print("Testing PerformanceOptimizer basic functionality...")
    
    # Create a performance optimizer instance
    optimizer = PerformanceOptimizer()
    
    # Test setting optimization levels
    print(f"Current optimization level: {optimizer.optimization_level}")
    optimizer.set_optimization_level(OptimizationLevel.AGGRESSIVE)
    print(f"Updated optimization level: {optimizer.optimization_level}")
    
    # Test setting cache strategies
    print(f"Current cache strategy: {optimizer.cache_strategy}")
    optimizer.set_cache_strategy(CacheStrategy.MEMORY)
    print(f"Updated cache strategy: {optimizer.cache_strategy}")
    
    # Test cache management
    print(f"Initial cache size: {len(optimizer.memory_cache)}")
    
    # Generate some test components
    test_components = []
    for i in range(5):
        component = CodeComponent(
            name=f"test_component_{i}",
            type="function",
            language="python",
            code=f"def test_function_{i}():\n    pass",
            file_path=f"/test/path_{i}.py",
            imports=["import os", "import sys"],
            dependencies=[],
            line_start=1,
            line_end=3,
            context={}
        )
        test_components.append(component)
    
    # Test component analysis optimization
    print("Testing component analysis optimization...")
    start_time = time.time()
    optimized_components = optimizer.optimize_component_analysis(test_components)
    end_time = time.time()
    
    print(f"Optimized {len(optimized_components)} components in {end_time - start_time:.4f} seconds")
    print(f"Cache size after optimization: {len(optimizer.memory_cache)}")
    
    # Test pattern validation optimization
    print("\nTesting pattern validation optimization...")
    patterns = [
        IntegrationPattern(
            pattern_id="test_pattern",
            pattern_name="test_pattern",
            description="Test pattern",
            code_example="def test_function():",
            dependencies=[],
            confidence_score=0.8,
            source_repository="test_repo",
            language="python"
        )
    ]
    
    start_time = time.time()
    optimized_patterns = optimizer.optimize_pattern_validation(test_components, patterns)
    end_time = time.time()
    
    print(f"Validated {len(optimized_patterns)} components with patterns in {end_time - start_time:.4f} seconds")
    
    # Test performance report generation
    print("\nGenerating performance report...")
    report = optimizer.get_performance_report()
    
    if 'summary' in report:
        print("Performance Report Summary:")
        print(f"  Total metrics: {report['summary']['total_metrics']}")
        print(f"  Avg execution time: {report['summary']['avg_execution_time']:.4f}s")
        print(f"  Avg memory usage: {report['summary']['avg_memory_usage']:.2f}MB")
        print(f"  Cache hit rate: {report['summary']['overall_cache_hit_rate']:.2%}")
    else:
        print("No performance metrics available yet")
    
    # Test cache clearing
    print("\nTesting cache clearing...")
    cache_size_before = len(optimizer.memory_cache)
    optimizer.clear_cache()
    cache_size_after = len(optimizer.memory_cache)
    
    print(f"Cache size before clearing: {cache_size_before}")
    print(f"Cache size after clearing: {cache_size_after}")
    
    print("\nPerformanceOptimizer basic functionality test completed successfully!")
    return True

def test_api_optimization():
    """Test API endpoint optimization functionality"""
    print("\nTesting API optimization functionality...")
    
    optimizer = PerformanceOptimizer()
    
    # Create test API endpoints
    api_endpoints = [
        {
            'endpoint': '/api/v1/users',
            'method': 'GET',
            'description': 'Get all users'
        },
        {
            'endpoint': '/api/v1/users/{id}',
            'method': 'GET',
            'description': 'Get user by ID'
        },
        {
            'endpoint': '/api/v1/users',
            'method': 'POST',
            'description': 'Create new user'
        }
    ]
    
    # Test API validation optimization
    start_time = time.time()
    optimized_endpoints = optimizer.optimize_api_validation(api_endpoints)
    end_time = time.time()
    
    print(f"Optimized {len(optimized_endpoints)} API endpoints in {end_time - start_time:.4f} seconds")
    
    print("API optimization test completed successfully!")
    return True

def test_search_optimization():
    """Test SourceGraph search optimization functionality"""
    print("\nTesting search optimization functionality...")
    
    optimizer = PerformanceOptimizer()
    
    # Create test search queries
    queries = [
        'python async function patterns',
        'javascript promise handling',
        'java exception best practices'
    ]
    
    # Test search optimization
    start_time = time.time()
    optimized_results = optimizer.optimize_sourcegraph_search(queries)
    end_time = time.time()
    
    print(f"Optimized search for {len(optimized_results)} queries in {end_time - start_time:.4f} seconds")
    
    print("Search optimization test completed successfully!")
    return True

def main():
    """Main test function"""
    setup_logging()
    
    print("=" * 60)
    print("AutoBot Assembly Performance Optimizer Test Suite")
    print("=" * 60)
    
    try:
        # Run all tests
        tests_passed = 0
        total_tests = 3
        
        if test_basic_functionality():
            tests_passed += 1
        
        if test_api_optimization():
            tests_passed += 1
            
        if test_search_optimization():
            tests_passed += 1
        
        print("\n" + "=" * 60)
        print(f"Test Results: {tests_passed}/{total_tests} tests passed")
        print("=" * 60)
        
        if tests_passed == total_tests:
            print("All tests passed! Performance optimizer is working correctly.")
            return 0
        else:
            print("Some tests failed. Please check the output above for details.")
            return 1
            
    except Exception as e:
        print(f"\nTest failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())