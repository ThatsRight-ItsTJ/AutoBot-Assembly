#!/usr/bin/env python3
"""
Comprehensive test suite for the Performance Optimizer module.
"""

import asyncio
import unittest
import tempfile
import time
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.optimization.performance_optimizer import (
    PerformanceOptimizer,
    OptimizationLevel,
    CacheStrategy,
    CodeComponent,
    IntegrationPattern,
    OptimizationMetric,
    PerformanceMetrics,
    OptimizationResult
)


class TestPerformanceOptimizer(unittest.TestCase):
    """Test cases for PerformanceOptimizer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.optimizer = PerformanceOptimizer()
        
        # Create test components
        self.test_components = [
            CodeComponent(
                name=f"test_component_{i}",
                type="function",
                language="python",
                code=f"def test_function_{i}():\n    return {i}",
                file_path=f"/test/path_{i}.py",
                imports=["import os", "import sys"],
                dependencies=[],
                line_start=1,
                line_end=3,
                context={}
            )
            for i in range(10)
        ]
        
        # Create test patterns
        self.test_patterns = [
            IntegrationPattern(
                pattern_id=f"pattern_{i}",
                pattern_name=f"Test Pattern {i}",
                description=f"Test pattern {i}",
                code_example=f"def pattern_function_{i}():\n    pass",
                dependencies=[],
                confidence_score=0.8,
                source_repository=f"test_repo_{i}",
                language="python"
            )
            for i in range(3)
        ]
    
    def test_initialization(self):
        """Test optimizer initialization."""
        self.assertIsInstance(self.optimizer.optimization_level, OptimizationLevel)
        self.assertIsInstance(self.optimizer.cache_strategy, CacheStrategy)
        self.assertIsInstance(self.optimizer.max_workers, int)
        self.assertGreater(self.optimizer.max_workers, 0)
    
    def test_optimization_level_setting(self):
        """Test setting optimization levels."""
        # Test basic level
        self.optimizer.set_optimization_level(OptimizationLevel.BASIC)
        self.assertEqual(self.optimizer.optimization_level, OptimizationLevel.BASIC)
        
        # Test aggressive level
        self.optimizer.set_optimization_level(OptimizationLevel.AGGRESSIVE)
        self.assertEqual(self.optimizer.optimization_level, OptimizationLevel.AGGRESSIVE)
    
    def test_cache_strategy_setting(self):
        """Test setting cache strategies."""
        # Test memory strategy
        self.optimizer.set_cache_strategy(CacheStrategy.MEMORY)
        self.assertEqual(self.optimizer.cache_strategy, CacheStrategy.MEMORY)
        
        # Test hybrid strategy
        self.optimizer.set_cache_strategy(CacheStrategy.HYBRID)
        self.assertEqual(self.optimizer.cache_strategy, CacheStrategy.HYBRID)
    
    def test_component_analysis_optimization(self):
        """Test component analysis optimization."""
        # Test with empty list
        result = self.optimizer.optimize_component_analysis([])
        self.assertEqual(len(result), 0)
        
        # Test with components
        result = self.optimizer.optimize_component_analysis(self.test_components)
        self.assertEqual(len(result), len(self.test_components))
        
        # Test caching (second call should be faster)
        start_time = time.time()
        result2 = self.optimizer.optimize_component_analysis(self.test_components)
        end_time = time.time()
        
        self.assertEqual(len(result2), len(self.test_components))
        # Second call should be very fast due to caching
        self.assertLess(end_time - start_time, 0.1)
    
    def test_pattern_validation_optimization(self):
        """Test pattern validation optimization."""
        # Test with empty lists
        result = self.optimizer.optimize_pattern_validation([], [])
        self.assertEqual(len(result), 0)
        
        # Test with components and patterns
        result = self.optimizer.optimize_pattern_validation(self.test_components, self.test_patterns)
        self.assertEqual(len(result), len(self.test_components))
    
    def test_api_validation_optimization(self):
        """Test API validation optimization."""
        test_endpoints = [
            {
                'endpoint': '/api/v1/test',
                'method': 'GET',
                'description': 'Test endpoint'
            },
            {
                'endpoint': '/api/v1/users',
                'method': 'POST',
                'description': 'Create user'
            }
        ]
        
        # Test with empty list
        result = self.optimizer.optimize_api_validation([])
        self.assertEqual(len(result), 0)
        
        # Test with endpoints
        result = self.optimizer.optimize_api_validation(test_endpoints)
        self.assertEqual(len(result), len(test_endpoints))
    
    def test_sourcegraph_search_optimization(self):
        """Test SourceGraph search optimization."""
        test_queries = [
            'python async function patterns',
            'javascript promise handling',
            'java exception best practices'
        ]
        
        # Test with empty list
        result = self.optimizer.optimize_sourcegraph_search([])
        self.assertEqual(len(result), 0)
        
        # Test with queries
        result = self.optimizer.optimize_sourcegraph_search(test_queries)
        self.assertIsInstance(result, list)
    
    def test_cache_operations(self):
        """Test cache operations."""
        # Test cache key generation
        key1 = self.optimizer._generate_cache_key('test', 'arg1', 'arg2')
        key2 = self.optimizer._generate_cache_key('test', 'arg1', 'arg2')
        key3 = self.optimizer._generate_cache_key('test', 'arg1', 'arg3')
        
        self.assertEqual(key1, key2)  # Same args should generate same key
        self.assertNotEqual(key1, key3)  # Different args should generate different keys
        
        # Test cache storage and retrieval
        test_data = {'test': 'data'}
        self.optimizer._store_in_cache('test_key', test_data)
        
        retrieved_data = self.optimizer._get_from_cache('test_key')
        self.assertEqual(retrieved_data, test_data)
        
        # Test cache miss
        missing_data = self.optimizer._get_from_cache('nonexistent_key')
        self.assertIsNone(missing_data)
    
    def test_performance_metrics(self):
        """Test performance metrics recording."""
        # Record some test metrics
        self.optimizer._record_metric('test_operation', 1.5, 10, 5)
        self.optimizer._record_metric('test_operation', 2.0, 15, 8)
        
        # Get performance report
        report = self.optimizer.get_performance_report()
        
        self.assertIn('summary', report)
        self.assertIn('metrics', report)
        self.assertIn('operation_breakdown', report)
        
        summary = report['summary']
        self.assertGreater(summary['total_metrics'], 0)
        self.assertGreater(summary['avg_execution_time'], 0)
    
    def test_optimization_recommendations(self):
        """Test optimization recommendations."""
        # Record some metrics first
        self.optimizer._record_metric('test_operation', 1.0, 10, 5)
        
        recommendations = self.optimizer.get_optimization_recommendations()
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
    
    def test_scenario_optimization(self):
        """Test scenario-based optimization."""
        scenarios = [
            'large_repository_analysis',
            'real_time_validation',
            'batch_processing',
            'api_heavy_workload'
        ]
        
        for scenario in scenarios:
            result = self.optimizer.optimize_for_scenario(scenario)
            self.assertIsInstance(result, OptimizationResult)
            self.assertEqual(result.operation_type, 'scenario_optimization')
            self.assertGreater(len(result.optimization_applied), 0)
    
    def test_cache_statistics(self):
        """Test cache statistics."""
        # Add some items to cache
        for i in range(5):
            self.optimizer._store_in_cache(f'test_key_{i}', f'test_data_{i}')
        
        stats = self.optimizer.get_cache_statistics()
        
        self.assertIn('memory_cache', stats)
        self.assertIn('disk_cache', stats)
        self.assertIn('strategy', stats)
        
        self.assertGreater(stats['memory_cache']['size'], 0)
    
    def test_cache_clearing(self):
        """Test cache clearing."""
        # Add items to cache
        self.optimizer._store_in_cache('test_key', 'test_data')
        self.assertIsNotNone(self.optimizer._get_from_cache('test_key'))
        
        # Clear cache
        self.optimizer.clear_cache()
        self.assertIsNone(self.optimizer._get_from_cache('test_key'))
    
    def test_benchmark_operation(self):
        """Test operation benchmarking."""
        def test_operation(x, y):
            time.sleep(0.01)  # Simulate work
            return x + y
        
        benchmark_result = self.optimizer.benchmark_operation(test_operation, 5, 3)
        
        self.assertIn('success', benchmark_result)
        self.assertIn('execution_time', benchmark_result)
        self.assertIn('result', benchmark_result)
        
        self.assertTrue(benchmark_result['success'])
        self.assertEqual(benchmark_result['result'], 8)
        self.assertGreater(benchmark_result['execution_time'], 0.01)


class TestAsyncOptimization(unittest.IsolatedAsyncioTestCase):
    """Test async optimization functionality."""
    
    async def asyncSetUp(self):
        """Set up async test fixtures."""
        self.optimizer = PerformanceOptimizer()
    
    async def test_async_request_throttling(self):
        """Test async request throttling."""
        # Enable throttling with low limit for testing
        self.optimizer.request_throttling = True
        self.optimizer.max_requests_per_second = 2
        
        start_time = time.time()
        
        # Make multiple requests
        for _ in range(3):
            await self.optimizer._apply_request_throttling()
        
        end_time = time.time()
        
        # Should take at least 1 second due to throttling
        self.assertGreater(end_time - start_time, 0.5)


def run_integration_tests():
    """Run integration tests with actual AutoBot components."""
    print("Running integration tests...")
    
    optimizer = PerformanceOptimizer()
    
    # Test with actual file analysis if UniversalCodeAnalyzer is available
    try:
        from src.analysis.universal_code_analyzer import UniversalCodeAnalyzer
        
        analyzer = UniversalCodeAnalyzer()
        test_file = "src/optimization/performance_optimizer.py"
        
        if Path(test_file).exists():
            print(f"Testing with real file: {test_file}")
            
            # Benchmark the analysis
            start_time = time.time()
            result = analyzer.analyze_file(test_file, "python")
            end_time = time.time()
            
            print(f"File analysis took {end_time - start_time:.4f} seconds")
            print(f"Analysis successful: {result.get('success', False) if result else False}")
        
    except ImportError:
        print("UniversalCodeAnalyzer not available for integration test")
    
    print("Integration tests completed")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Performance Optimizer Test Suite")
    print("=" * 60)
    
    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run integration tests
    print("\n" + "=" * 60)
    run_integration_tests()
    
    print("\n" + "=" * 60)
    print("All tests completed!")


if __name__ == "__main__":
    main()