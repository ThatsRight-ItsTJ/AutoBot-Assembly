"""
Performance optimization module for AutoBot Assembly.

This module provides a comprehensive performance optimization system for all integrations
in the AutoBot Assembly platform, including caching strategies, parallel processing,
and performance monitoring.
"""

from .performance_optimizer import (
    PerformanceOptimizer,
    OptimizationLevel,
    CacheStrategy,
    OptimizationMetric,
    PerformanceMetrics,
    OptimizationResult
)

__all__ = [
    'PerformanceOptimizer',
    'OptimizationLevel',
    'CacheStrategy',
    'OptimizationMetric',
    'PerformanceMetrics',
    'OptimizationResult'
]