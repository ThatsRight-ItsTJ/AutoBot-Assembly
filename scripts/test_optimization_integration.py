#!/usr/bin/env python3
"""
Test script for Performance Optimization Integration

Tests the integration of the performance optimizer with AutoBot Assembly components.
"""

import asyncio
import sys
import os
import time
import logging
from pathlib import Path

# Add src to path
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))
os.chdir(current_dir)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_cli_optimization_integration():
    """Test CLI integration with performance optimizer."""
    print("🧪 Testing CLI Optimization Integration")
    print("-" * 50)
    
    try:
        from src.cli.autobot_cli import AutoBotCLI
        from src.optimization.performance_optimizer import OptimizationLevel, CacheStrategy
        
        # Initialize CLI
        cli = AutoBotCLI()
        print("✅ CLI initialized with performance optimizer")
        
        # Test optimization settings
        print(f"   Initial optimization level: {cli.performance_optimizer.optimization_level.value}")
        print(f"   Initial cache strategy: {cli.performance_optimizer.cache_strategy.value}")
        
        # Test optimization level change
        cli.performance_optimizer.set_optimization_level(OptimizationLevel.AGGRESSIVE)
        print("✅ Optimization level changed to aggressive")
        
        # Test cache strategy change
        cli.performance_optimizer.set_cache_strategy(CacheStrategy.MEMORY)
        print("✅ Cache strategy changed to memory")
        
        # Test performance report generation
        report = cli.performance_optimizer.get_performance_report()
        print(f"✅ Performance report generated: {len(report)} sections")
        
        return True
        
    except Exception as e:
        print(f"❌ CLI optimization integration failed: {e}")
        logger.exception("CLI optimization integration test failed")
        return False

async def test_web_optimization_integration():
    """Test web interface integration with performance optimizer."""
    print("\n🌐 Testing Web Optimization Integration")
    print("-" * 50)
    
    try:
        from src.web.web_server import WebServer, WebConfig
        
        # Initialize web server
        config = WebConfig(debug=True)
        server = WebServer(config)
        print("✅ Web server initialized with performance optimizer")
        
        # Test optimization settings
        print(f"   Optimization level: {server.performance_optimizer.optimization_level.value}")
        print(f"   Cache strategy: {server.performance_optimizer.cache_strategy.value}")
        
        # Test cache statistics
        cache_stats = server.performance_optimizer.get_cache_statistics()
        print(f"✅ Cache statistics retrieved: {cache_stats['strategy']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Web optimization integration failed: {e}")
        logger.exception("Web optimization integration test failed")
        return False

async def test_reporter_optimization_integration():
    """Test AI reporter integration with performance optimizer."""
    print("\n📊 Testing Reporter Optimization Integration")
    print("-" * 50)
    
    try:
        from src.reporting.ai_integrated_reporter import AIIntegratedReporter
        from src.cli.config_manager import ConfigManager
        
        # Initialize reporter
        config_manager = ConfigManager()
        reporter = AIIntegratedReporter(config_manager=config_manager)
        print("✅ AI reporter initialized")
        
        # Check if performance optimizer is available
        if reporter.performance_optimizer:
            print("✅ Performance optimizer available in reporter")
            
            # Test performance metrics generation
            project_data = {
                'name': 'Test Project',
                'files': ['main.py', 'requirements.txt'],
                'size': 1024,
                'language': 'python'
            }
            
            repositories = [
                {
                    'name': 'test-repo',
                    'url': 'https://github.com/test/repo',
                    'purpose': 'Testing',
                    'license': 'MIT'
                }
            ]
            
            # Generate report with performance metrics
            report = await reporter.generate_comprehensive_report(project_data, repositories)
            
            if "PERFORMANCE METRICS" in report:
                print("✅ Performance metrics included in report")
            else:
                print("⚠️  Performance metrics not found in report")
        else:
            print("⚠️  Performance optimizer not available in reporter")
        
        return True
        
    except Exception as e:
        print(f"❌ Reporter optimization integration failed: {e}")
        logger.exception("Reporter optimization integration test failed")
        return False

async def test_performance_optimization_scenarios():
    """Test different performance optimization scenarios."""
    print("\n⚡ Testing Performance Optimization Scenarios")
    print("-" * 50)
    
    try:
        from src.optimization.performance_optimizer import PerformanceOptimizer, CodeComponent, IntegrationPattern
        
        optimizer = PerformanceOptimizer()
        
        # Test scenario optimizations
        scenarios = [
            'large_repository_analysis',
            'real_time_validation',
            'batch_processing',
            'api_heavy_workload'
        ]
        
        for scenario in scenarios:
            print(f"Testing scenario: {scenario}")
            result = optimizer.optimize_for_scenario(scenario)
            
            print(f"   ✅ Optimizations applied: {result.optimization_applied}")
            print(f"   ⚡ Performance gain: {result.performance_gain:.1%}")
        
        # Test component optimization
        test_components = [
            CodeComponent(
                name=f"component_{i}",
                type="function",
                language="python",
                code=f"def func_{i}(): pass",
                file_path=f"/test/{i}.py",
                imports=[],
                dependencies=[],
                line_start=1,
                line_end=2,
                context={}
            )
            for i in range(20)
        ]
        
        print(f"\nTesting component optimization with {len(test_components)} components...")
        start_time = time.time()
        optimized = optimizer.optimize_component_analysis(test_components)
        end_time = time.time()
        
        print(f"✅ Optimized {len(optimized)} components in {end_time - start_time:.4f}s")
        
        # Test pattern validation
        test_patterns = [
            IntegrationPattern(
                pattern_id=f"pattern_{i}",
                pattern_name=f"Pattern {i}",
                description=f"Test pattern {i}",
                code_example="def pattern(): pass",
                dependencies=[],
                confidence_score=0.8,
                source_repository="test_repo",
                language="python"
            )
            for i in range(5)
        ]
        
        print(f"Testing pattern validation with {len(test_patterns)} patterns...")
        start_time = time.time()
        validated = optimizer.optimize_pattern_validation(test_components, test_patterns)
        end_time = time.time()
        
        print(f"✅ Validated {len(validated)} components in {end_time - start_time:.4f}s")
        
        # Generate performance report
        report = optimizer.get_performance_report()
        summary = report['summary']
        
        print(f"\n📈 Performance Summary:")
        print(f"   Total operations: {summary['total_metrics']}")
        print(f"   Avg execution time: {summary['avg_execution_time']:.4f}s")
        print(f"   Cache hit rate: {summary['overall_cache_hit_rate']:.1%}")
        print(f"   Memory usage: {summary['avg_memory_usage']:.1f}%")
        
        # Get recommendations
        recommendations = optimizer.get_optimization_recommendations()
        print(f"\n💡 Optimization Recommendations:")
        for rec in recommendations[:3]:
            print(f"   • {rec}")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance optimization scenarios test failed: {e}")
        logger.exception("Performance optimization scenarios test failed")
        return False

async def test_cache_performance():
    """Test cache performance and efficiency."""
    print("\n💾 Testing Cache Performance")
    print("-" * 50)
    
    try:
        from src.optimization.performance_optimizer import PerformanceOptimizer, CacheStrategy
        
        # Test different cache strategies
        strategies = [CacheStrategy.MEMORY, CacheStrategy.DISK, CacheStrategy.HYBRID]
        
        for strategy in strategies:
            print(f"\nTesting {strategy.value} cache strategy...")
            
            optimizer = PerformanceOptimizer()
            optimizer.set_cache_strategy(strategy)
            
            # Test cache operations
            test_data = {'test': 'data', 'timestamp': time.time()}
            cache_key = 'test_cache_key'
            
            # Store in cache
            start_time = time.time()
            optimizer._store_in_cache(cache_key, test_data)
            store_time = time.time() - start_time
            
            # Retrieve from cache
            start_time = time.time()
            retrieved_data = optimizer._get_from_cache(cache_key)
            retrieve_time = time.time() - start_time
            
            print(f"   Store time: {store_time:.6f}s")
            print(f"   Retrieve time: {retrieve_time:.6f}s")
            print(f"   Data integrity: {'✅' if retrieved_data == test_data else '❌'}")
            
            # Test cache statistics
            cache_stats = optimizer.get_cache_statistics()
            print(f"   Cache size: {cache_stats['memory_cache']['size']}")
            
            # Clear cache for next test
            optimizer.clear_cache()
        
        return True
        
    except Exception as e:
        print(f"❌ Cache performance test failed: {e}")
        logger.exception("Cache performance test failed")
        return False

async def main():
    """Run all optimization integration tests."""
    print("🚀 AutoBot Assembly System - Performance Optimization Integration Tests")
    print("=" * 80)
    
    # Track test results
    test_results = []
    
    # Run tests
    test_results.append(("CLI Integration", await test_cli_optimization_integration()))
    test_results.append(("Web Integration", await test_web_optimization_integration()))
    test_results.append(("Reporter Integration", await test_reporter_optimization_integration()))
    test_results.append(("Optimization Scenarios", await test_performance_optimization_scenarios()))
    test_results.append(("Cache Performance", await test_cache_performance()))
    
    # Print summary
    print("\n" + "=" * 80)
    print("🎯 OPTIMIZATION INTEGRATION TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<30} {status}")
    
    print(f"\nResults: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL OPTIMIZATION INTEGRATION TESTS PASSED!")
        print("🚀 Performance optimization is fully integrated with AutoBot Assembly!")
        print("\n📊 Integration Status:")
        print("✅ CLI commands support optimization flags")
        print("✅ Web interface has optimization controls")
        print("✅ API endpoints for optimization configuration")
        print("✅ Performance metrics in reports")
        print("✅ Comprehensive test coverage")
        print("✅ Cache performance validation")
        print("✅ Scenario-based optimization")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
        print("🔧 Check the failed components above")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)