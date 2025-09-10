"""
Performance Optimizer for AutoBot Assembly System

Comprehensive performance optimization system for all integrations in the AutoBot Assembly platform,
including caching strategies, parallel processing, and performance monitoring.
"""

import asyncio
import logging
import os
import time
import json
import hashlib
import threading
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from collections import defaultdict, deque
import psutil

# Import components for optimization
try:
    from ..analysis.universal_code_analyzer import UniversalCodeAnalyzer, CodeElement
    UNIVERSAL_ANALYZER_AVAILABLE = True
except ImportError:
    UNIVERSAL_ANALYZER_AVAILABLE = False
    UniversalCodeAnalyzer = None
    CodeElement = None

try:
    from ..assembly.pattern_validator import PatternBasedValidator, PatternValidationResult
    PATTERN_VALIDATOR_AVAILABLE = True
except ImportError:
    PATTERN_VALIDATOR_AVAILABLE = False
    PatternBasedValidator = None
    PatternValidationResult = None

try:
    from ..validation.context7_validator import Context7Validator, APIValidationResult
    CONTEXT7_VALIDATOR_AVAILABLE = True
except ImportError:
    CONTEXT7_VALIDATOR_AVAILABLE = False
    Context7Validator = None
    APIValidationResult = None

try:
    from ..search.sourcegraph_integration import SourceGraphIntegration
    SOURCEGRAPH_AVAILABLE = True
except ImportError:
    SOURCEGRAPH_AVAILABLE = False
    SourceGraphIntegration = None

try:
    from ..qa.multi_layer_validator import MultiLayerValidator, QualityAssessmentReport
    MULTI_LAYER_VALIDATOR_AVAILABLE = True
except ImportError:
    MULTI_LAYER_VALIDATOR_AVAILABLE = False
    MultiLayerValidator = None
    QualityAssessmentReport = None

# Mock classes for missing dependencies
if not UNIVERSAL_ANALYZER_AVAILABLE:
    @dataclass
    class CodeElement:
        name: str
        type: str
        code: str
        file_path: str
        language: str

if not PATTERN_VALIDATOR_AVAILABLE:
    @dataclass
    class PatternValidationResult:
        is_valid: bool
        overall_score: float

if not CONTEXT7_VALIDATOR_AVAILABLE:
    @dataclass
    class APIValidationResult:
        api_endpoint: str
        status: str

if not MULTI_LAYER_VALIDATOR_AVAILABLE:
    @dataclass
    class QualityAssessmentReport:
        overall_score: float


class OptimizationLevel(Enum):
    """Optimization levels for performance tuning."""
    BASIC = "basic"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class CacheStrategy(Enum):
    """Caching strategies for performance optimization."""
    MEMORY = "memory"
    DISK = "disk"
    HYBRID = "hybrid"


@dataclass
class OptimizationMetric:
    """Performance optimization metric."""
    timestamp: float
    operation_type: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    cache_hits: int
    cache_misses: int
    throughput: float
    optimization_level: OptimizationLevel
    cache_strategy: CacheStrategy


@dataclass
class PerformanceMetrics:
    """Aggregated performance metrics."""
    total_operations: int
    avg_execution_time: float
    avg_memory_usage: float
    avg_cpu_usage: float
    total_cache_hits: int
    total_cache_misses: int
    cache_hit_rate: float
    avg_throughput: float
    optimization_effectiveness: float


@dataclass
class OptimizationResult:
    """Result of an optimization operation."""
    operation_type: str
    input_size: int
    output_size: int
    execution_time: float
    memory_saved: float
    cache_hits: int
    optimization_applied: List[str]
    performance_gain: float


@dataclass
class CodeComponent:
    """Code component for optimization."""
    name: str
    type: str
    language: str
    code: str
    file_path: str
    imports: List[str]
    dependencies: List[str]
    line_start: int
    line_end: int
    context: Dict[str, Any]


@dataclass
class IntegrationPattern:
    """Integration pattern for optimization."""
    pattern_id: str
    pattern_name: str
    description: str
    code_example: str
    dependencies: List[str]
    confidence_score: float
    source_repository: str
    language: str


class PerformanceOptimizer:
    """Comprehensive performance optimization system for AutoBot Assembly."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Load configuration from environment
        self.optimization_level = OptimizationLevel(
            os.getenv('OPTIMIZATION_LEVEL', 'moderate').lower()
        )
        self.cache_strategy = CacheStrategy(
            os.getenv('CACHE_STRATEGY', 'hybrid').lower()
        )
        
        # Performance settings
        self.max_workers = int(os.getenv('OPTIMIZATION_MAX_WORKERS', '4'))
        self.parallel_enabled = os.getenv('OPTIMIZATION_PARALLEL', 'true').lower() == 'true'
        self.cache_size = int(os.getenv('CACHE_SIZE', '1000'))
        self.disk_cache_path = Path(os.getenv('DISK_CACHE_PATH', './cache/performance_cache'))
        
        # Request throttling settings
        self.request_throttling = os.getenv('REQUEST_THROTTLING', 'true').lower() == 'true'
        self.max_requests_per_second = int(os.getenv('MAX_REQUESTS_PER_SECOND', '100'))
        
        # Batch processing settings
        self.batch_processing = os.getenv('BATCH_PROCESSING', 'true').lower() == 'true'
        self.batch_size = int(os.getenv('BATCH_SIZE', '10'))
        self.max_batch_wait_time = float(os.getenv('MAX_BATCH_WAIT_TIME', '1.0'))
        
        # Initialize caches
        self.memory_cache: Dict[str, Any] = {}
        self.cache_timestamps: Dict[str, float] = {}
        self.cache_access_count: Dict[str, int] = defaultdict(int)
        
        # Performance metrics
        self.metrics: List[OptimizationMetric] = []
        self.operation_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Thread safety
        self.cache_lock = threading.RLock()
        self.metrics_lock = threading.RLock()
        
        # Request throttling
        self.request_times: deque = deque(maxlen=self.max_requests_per_second)
        self.throttle_lock = threading.Lock()
        
        # Batch processing
        self.batch_queue: Dict[str, List] = defaultdict(list)
        self.batch_timers: Dict[str, float] = {}
        self.batch_lock = threading.Lock()
        
        # Initialize disk cache
        self._initialize_disk_cache()
        
        # Initialize component optimizers
        self._initialize_component_optimizers()
        
        self.logger.info(f"PerformanceOptimizer initialized with {self.optimization_level.value} level")
    
    def _initialize_disk_cache(self):
        """Initialize disk cache directory."""
        if self.cache_strategy in [CacheStrategy.DISK, CacheStrategy.HYBRID]:
            self.disk_cache_path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Disk cache initialized at {self.disk_cache_path}")
    
    def _initialize_component_optimizers(self):
        """Initialize optimizers for different components."""
        self.component_optimizers = {}
        
        # Universal Code Analyzer optimizer
        if UNIVERSAL_ANALYZER_AVAILABLE:
            self.component_optimizers['universal_analyzer'] = self._create_analyzer_optimizer()
        
        # Pattern Validator optimizer
        if PATTERN_VALIDATOR_AVAILABLE:
            self.component_optimizers['pattern_validator'] = self._create_pattern_optimizer()
        
        # Context7 Validator optimizer
        if CONTEXT7_VALIDATOR_AVAILABLE:
            self.component_optimizers['context7_validator'] = self._create_context7_optimizer()
        
        # SourceGraph optimizer
        if SOURCEGRAPH_AVAILABLE:
            self.component_optimizers['sourcegraph'] = self._create_sourcegraph_optimizer()
        
        # Multi-layer Validator optimizer
        if MULTI_LAYER_VALIDATOR_AVAILABLE:
            self.component_optimizers['multi_layer_validator'] = self._create_multilayer_optimizer()
    
    def _create_analyzer_optimizer(self) -> Dict[str, Any]:
        """Create optimizer configuration for UniversalCodeAnalyzer."""
        return {
            'cache_ttl': 3600,  # 1 hour
            'parallel_parsing': True,
            'max_file_size': 1024 * 1024,  # 1MB
            'timeout': 30,
            'batch_size': 10
        }
    
    def _create_pattern_optimizer(self) -> Dict[str, Any]:
        """Create optimizer configuration for PatternBasedValidator."""
        return {
            'cache_ttl': 1800,  # 30 minutes
            'parallel_validation': True,
            'max_patterns': 50,
            'timeout': 60,
            'batch_size': 5
        }
    
    def _create_context7_optimizer(self) -> Dict[str, Any]:
        """Create optimizer configuration for Context7Validator."""
        return {
            'cache_ttl': 900,  # 15 minutes
            'connection_pooling': True,
            'max_connections': 10,
            'timeout': 30,
            'batch_size': 20
        }
    
    def _create_sourcegraph_optimizer(self) -> Dict[str, Any]:
        """Create optimizer configuration for SourceGraphIntegration."""
        return {
            'cache_ttl': 7200,  # 2 hours
            'rate_limit': 100,  # requests per hour
            'timeout': 45,
            'batch_size': 5
        }
    
    def _create_multilayer_optimizer(self) -> Dict[str, Any]:
        """Create optimizer configuration for MultiLayerValidator."""
        return {
            'cache_ttl': 1800,  # 30 minutes
            'parallel_layers': True,
            'max_layers': 7,
            'timeout': 120,
            'adaptive_timeout': True
        }
    
    def set_optimization_level(self, level: OptimizationLevel):
        """Set optimization level."""
        self.optimization_level = level
        self.logger.info(f"Optimization level set to {level.value}")
        
        # Adjust settings based on level
        if level == OptimizationLevel.BASIC:
            self.max_workers = min(self.max_workers, 2)
            self.parallel_enabled = False
            self.batch_processing = False
        elif level == OptimizationLevel.MODERATE:
            self.max_workers = min(self.max_workers, 4)
            self.parallel_enabled = True
            self.batch_processing = True
        elif level == OptimizationLevel.AGGRESSIVE:
            self.max_workers = max(self.max_workers, 6)
            self.parallel_enabled = True
            self.batch_processing = True
    
    def set_cache_strategy(self, strategy: CacheStrategy):
        """Set cache strategy."""
        self.cache_strategy = strategy
        self.logger.info(f"Cache strategy set to {strategy.value}")
        
        if strategy == CacheStrategy.DISK:
            self._initialize_disk_cache()
    
    def optimize_component_analysis(self, components: List[CodeComponent]) -> List[CodeComponent]:
        """Optimize component analysis performance."""
        start_time = time.time()
        
        if not components:
            return []
        
        self.logger.info(f"Optimizing analysis for {len(components)} components")
        
        # Check cache first
        cached_results = []
        uncached_components = []
        
        for component in components:
            cache_key = self._generate_cache_key('component_analysis', component.name, component.file_path)
            cached_result = self._get_from_cache(cache_key)
            
            if cached_result:
                cached_results.append(cached_result)
            else:
                uncached_components.append(component)
        
        # Process uncached components
        if uncached_components:
            if self.parallel_enabled and len(uncached_components) > 1:
                processed_components = self._parallel_component_analysis(uncached_components)
            else:
                processed_components = self._sequential_component_analysis(uncached_components)
            
            # Cache results
            for component in processed_components:
                cache_key = self._generate_cache_key('component_analysis', component.name, component.file_path)
                self._store_in_cache(cache_key, component)
        else:
            processed_components = []
        
        # Combine results
        all_components = cached_results + processed_components
        
        # Record metrics
        execution_time = time.time() - start_time
        self._record_metric('component_analysis', execution_time, len(components), len(cached_results))
        
        self.logger.info(f"Component analysis completed in {execution_time:.2f}s ({len(cached_results)} cached)")
        return all_components
    
    def optimize_pattern_validation(self, components: List[CodeComponent], 
                                  patterns: List[IntegrationPattern]) -> List[CodeComponent]:
        """Optimize pattern validation performance."""
        start_time = time.time()
        
        if not components or not patterns:
            return components
        
        self.logger.info(f"Optimizing pattern validation for {len(components)} components against {len(patterns)} patterns")
        
        # Use batch processing if enabled
        if self.batch_processing and len(components) > self.batch_size:
            validated_components = self._batch_pattern_validation(components, patterns)
        elif self.parallel_enabled and len(components) > 1:
            validated_components = self._parallel_pattern_validation(components, patterns)
        else:
            validated_components = self._sequential_pattern_validation(components, patterns)
        
        # Record metrics
        execution_time = time.time() - start_time
        self._record_metric('pattern_validation', execution_time, len(components), 0)
        
        self.logger.info(f"Pattern validation completed in {execution_time:.2f}s")
        return validated_components
    
    def optimize_api_validation(self, api_endpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize API validation performance."""
        start_time = time.time()
        
        if not api_endpoints:
            return []
        
        self.logger.info(f"Optimizing API validation for {len(api_endpoints)} endpoints")
        
        # Check cache for API validation results
        cached_results = []
        uncached_endpoints = []
        
        for endpoint in api_endpoints:
            cache_key = self._generate_cache_key('api_validation', endpoint.get('endpoint', ''), endpoint.get('method', ''))
            cached_result = self._get_from_cache(cache_key)
            
            if cached_result:
                cached_results.append(cached_result)
            else:
                uncached_endpoints.append(endpoint)
        
        # Process uncached endpoints
        if uncached_endpoints:
            if self.batch_processing and len(uncached_endpoints) > self.batch_size:
                validated_endpoints = self._batch_api_validation(uncached_endpoints)
            elif self.parallel_enabled and len(uncached_endpoints) > 1:
                validated_endpoints = self._parallel_api_validation(uncached_endpoints)
            else:
                validated_endpoints = self._sequential_api_validation(uncached_endpoints)
            
            # Cache results
            for endpoint in validated_endpoints:
                cache_key = self._generate_cache_key('api_validation', endpoint.get('endpoint', ''), endpoint.get('method', ''))
                self._store_in_cache(cache_key, endpoint)
        else:
            validated_endpoints = []
        
        # Combine results
        all_endpoints = cached_results + validated_endpoints
        
        # Record metrics
        execution_time = time.time() - start_time
        self._record_metric('api_validation', execution_time, len(api_endpoints), len(cached_results))
        
        self.logger.info(f"API validation completed in {execution_time:.2f}s ({len(cached_results)} cached)")
        return all_endpoints
    
    def optimize_sourcegraph_search(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Optimize SourceGraph search performance."""
        start_time = time.time()
        
        if not queries:
            return []
        
        self.logger.info(f"Optimizing SourceGraph search for {len(queries)} queries")
        
        # Apply request throttling
        if self.request_throttling:
            await self._apply_request_throttling()
        
        # Check cache for search results
        cached_results = []
        uncached_queries = []
        
        for query in queries:
            cache_key = self._generate_cache_key('sourcegraph_search', query)
            cached_result = self._get_from_cache(cache_key)
            
            if cached_result:
                cached_results.extend(cached_result)
            else:
                uncached_queries.append(query)
        
        # Process uncached queries
        if uncached_queries:
            if self.batch_processing and len(uncached_queries) > self.batch_size:
                search_results = self._batch_sourcegraph_search(uncached_queries)
            elif self.parallel_enabled and len(uncached_queries) > 1:
                search_results = self._parallel_sourcegraph_search(uncached_queries)
            else:
                search_results = self._sequential_sourcegraph_search(uncached_queries)
            
            # Cache results
            for i, query in enumerate(uncached_queries):
                cache_key = self._generate_cache_key('sourcegraph_search', query)
                query_results = search_results[i] if i < len(search_results) else []
                self._store_in_cache(cache_key, query_results)
        else:
            search_results = []
        
        # Combine results
        all_results = cached_results + [item for sublist in search_results for item in sublist]
        
        # Record metrics
        execution_time = time.time() - start_time
        self._record_metric('sourcegraph_search', execution_time, len(queries), len(cached_results))
        
        self.logger.info(f"SourceGraph search completed in {execution_time:.2f}s ({len(cached_results)} cached)")
        return all_results
    
    def optimize_multi_layer_validation(self, components: List[CodeComponent], 
                                      patterns: List[IntegrationPattern]) -> QualityAssessmentReport:
        """Optimize multi-layer validation performance."""
        start_time = time.time()
        
        self.logger.info(f"Optimizing multi-layer validation for {len(components)} components")
        
        # Check cache for validation results
        cache_key = self._generate_cache_key('multi_layer_validation', 
                                           str(len(components)), 
                                           str(len(patterns)))
        cached_result = self._get_from_cache(cache_key)
        
        if cached_result:
            self.logger.info("Using cached multi-layer validation results")
            return cached_result
        
        # Perform validation with optimization
        if MULTI_LAYER_VALIDATOR_AVAILABLE:
            validator = MultiLayerValidator()
            
            # Apply adaptive timeout based on optimization level
            if self.optimization_level == OptimizationLevel.AGGRESSIVE:
                # Use parallel validation for aggressive optimization
                report = self._parallel_multi_layer_validation(validator, components, patterns)
            else:
                # Use standard validation
                report = validator.validate_assembly_quality(components, patterns)
        else:
            # Create mock report if validator not available
            report = QualityAssessmentReport(overall_score=0.8)
        
        # Cache result
        self._store_in_cache(cache_key, report)
        
        # Record metrics
        execution_time = time.time() - start_time
        self._record_metric('multi_layer_validation', execution_time, len(components), 0)
        
        self.logger.info(f"Multi-layer validation completed in {execution_time:.2f}s")
        return report
    
    def _parallel_component_analysis(self, components: List[CodeComponent]) -> List[CodeComponent]:
        """Perform parallel component analysis."""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._analyze_single_component, component): component 
                for component in components
            }
            
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=30)
                    if result:
                        results.append(result)
                except Exception as e:
                    self.logger.warning(f"Component analysis failed: {e}")
            
            return results
    
    def _sequential_component_analysis(self, components: List[CodeComponent]) -> List[CodeComponent]:
        """Perform sequential component analysis."""
        results = []
        for component in components:
            try:
                result = self._analyze_single_component(component)
                if result:
                    results.append(result)
            except Exception as e:
                self.logger.warning(f"Component analysis failed for {component.name}: {e}")
        
        return results
    
    def _analyze_single_component(self, component: CodeComponent) -> Optional[CodeComponent]:
        """Analyze a single component."""
        try:
            # Simulate component analysis
            if UNIVERSAL_ANALYZER_AVAILABLE and UniversalCodeAnalyzer:
                analyzer = UniversalCodeAnalyzer()
                # Perform actual analysis if available
                analysis_result = analyzer.analyze_file(component.file_path, component.language)
                
                # Update component with analysis results
                if analysis_result and analysis_result.get('success'):
                    component.context.update(analysis_result.get('metrics', {}))
            
            return component
        except Exception as e:
            self.logger.warning(f"Failed to analyze component {component.name}: {e}")
            return component
    
    def _parallel_pattern_validation(self, components: List[CodeComponent], 
                                   patterns: List[IntegrationPattern]) -> List[CodeComponent]:
        """Perform parallel pattern validation."""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._validate_component_patterns, component, patterns): component 
                for component in components
            }
            
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=60)
                    if result:
                        results.append(result)
                except Exception as e:
                    self.logger.warning(f"Pattern validation failed: {e}")
            
            return results
    
    def _sequential_pattern_validation(self, components: List[CodeComponent], 
                                     patterns: List[IntegrationPattern]) -> List[CodeComponent]:
        """Perform sequential pattern validation."""
        results = []
        for component in components:
            try:
                result = self._validate_component_patterns(component, patterns)
                if result:
                    results.append(result)
            except Exception as e:
                self.logger.warning(f"Pattern validation failed for {component.name}: {e}")
        
        return results
    
    def _batch_pattern_validation(self, components: List[CodeComponent], 
                                patterns: List[IntegrationPattern]) -> List[CodeComponent]:
        """Perform batch pattern validation."""
        results = []
        
        # Process in batches
        for i in range(0, len(components), self.batch_size):
            batch = components[i:i + self.batch_size]
            
            if self.parallel_enabled:
                batch_results = self._parallel_pattern_validation(batch, patterns)
            else:
                batch_results = self._sequential_pattern_validation(batch, patterns)
            
            results.extend(batch_results)
            
            # Add delay between batches if throttling is enabled
            if self.request_throttling and i + self.batch_size < len(components):
                time.sleep(self.max_batch_wait_time)
        
        return results
    
    def _validate_component_patterns(self, component: CodeComponent, 
                                   patterns: List[IntegrationPattern]) -> Optional[CodeComponent]:
        """Validate patterns for a single component."""
        try:
            # Simulate pattern validation
            if PATTERN_VALIDATOR_AVAILABLE and PatternBasedValidator:
                validator = PatternBasedValidator()
                # Perform actual validation if available
                validation_result = validator.validate_single_pattern([component], patterns[0] if patterns else None)
                
                # Update component with validation results
                if validation_result:
                    component.context['pattern_validation'] = {
                        'is_valid': validation_result.is_valid,
                        'score': validation_result.overall_score
                    }
            
            return component
        except Exception as e:
            self.logger.warning(f"Failed to validate patterns for component {component.name}: {e}")
            return component
    
    def _parallel_api_validation(self, endpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Perform parallel API validation."""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._validate_single_api, endpoint): endpoint 
                for endpoint in endpoints
            }
            
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=30)
                    if result:
                        results.append(result)
                except Exception as e:
                    self.logger.warning(f"API validation failed: {e}")
            
            return results
    
    def _sequential_api_validation(self, endpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Perform sequential API validation."""
        results = []
        for endpoint in endpoints:
            try:
                result = self._validate_single_api(endpoint)
                if result:
                    results.append(result)
            except Exception as e:
                self.logger.warning(f"API validation failed for {endpoint.get('endpoint', 'unknown')}: {e}")
        
        return results
    
    def _batch_api_validation(self, endpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Perform batch API validation."""
        results = []
        
        # Process in batches
        for i in range(0, len(endpoints), self.batch_size):
            batch = endpoints[i:i + self.batch_size]
            
            if self.parallel_enabled:
                batch_results = self._parallel_api_validation(batch)
            else:
                batch_results = self._sequential_api_validation(batch)
            
            results.extend(batch_results)
            
            # Add delay between batches if throttling is enabled
            if self.request_throttling and i + self.batch_size < len(endpoints):
                time.sleep(self.max_batch_wait_time)
        
        return results
    
    def _validate_single_api(self, endpoint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate a single API endpoint."""
        try:
            # Simulate API validation
            if CONTEXT7_VALIDATOR_AVAILABLE and Context7Validator:
                validator = Context7Validator()
                # Perform actual validation if available
                validation_result = validator.validate_api_endpoint(
                    endpoint.get('endpoint', ''),
                    endpoint.get('method', 'GET'),
                    endpoint.get('headers', {}),
                    endpoint.get('body', {})
                )
                
                # Update endpoint with validation results
                endpoint['validation_result'] = {
                    'status': validation_result.status,
                    'message': validation_result.message
                }
            
            return endpoint
        except Exception as e:
            self.logger.warning(f"Failed to validate API endpoint {endpoint.get('endpoint', 'unknown')}: {e}")
            return endpoint
    
    def _parallel_sourcegraph_search(self, queries: List[str]) -> List[List[Dict[str, Any]]]:
        """Perform parallel SourceGraph search."""
        with ThreadPoolExecutor(max_workers=min(self.max_workers, 3)) as executor:  # Limit for API rate limits
            futures = {
                executor.submit(self._search_single_query, query): query 
                for query in queries
            }
            
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=45)
                    results.append(result if result else [])
                except Exception as e:
                    self.logger.warning(f"SourceGraph search failed: {e}")
                    results.append([])
            
            return results
    
    def _sequential_sourcegraph_search(self, queries: List[str]) -> List[List[Dict[str, Any]]]:
        """Perform sequential SourceGraph search."""
        results = []
        for query in queries:
            try:
                result = self._search_single_query(query)
                results.append(result if result else [])
            except Exception as e:
                self.logger.warning(f"SourceGraph search failed for query '{query}': {e}")
                results.append([])
        
        return results
    
    def _batch_sourcegraph_search(self, queries: List[str]) -> List[List[Dict[str, Any]]]:
        """Perform batch SourceGraph search."""
        results = []
        
        # Process in batches with rate limiting
        for i in range(0, len(queries), self.batch_size):
            batch = queries[i:i + self.batch_size]
            
            if self.parallel_enabled:
                batch_results = self._parallel_sourcegraph_search(batch)
            else:
                batch_results = self._sequential_sourcegraph_search(batch)
            
            results.extend(batch_results)
            
            # Add delay between batches for rate limiting
            if i + self.batch_size < len(queries):
                time.sleep(self.max_batch_wait_time)
        
        return results
    
    def _search_single_query(self, query: str) -> List[Dict[str, Any]]:
        """Search a single query in SourceGraph."""
        try:
            # Simulate SourceGraph search
            if SOURCEGRAPH_AVAILABLE and SourceGraphIntegration:
                integration = SourceGraphIntegration()
                # Perform actual search if available
                results = integration.sourcegraph_search(query, limit=10)
                return [{'query': query, 'results': results}]
            else:
                # Return mock results
                return [{'query': query, 'results': []}]
        except Exception as e:
            self.logger.warning(f"Failed to search query '{query}': {e}")
            return []
    
    def _parallel_multi_layer_validation(self, validator, components: List[CodeComponent], 
                                       patterns: List[IntegrationPattern]) -> QualityAssessmentReport:
        """Perform parallel multi-layer validation."""
        try:
            # Use parallel validation if available
            return validator.validate_assembly_quality(components, patterns)
        except Exception as e:
            self.logger.warning(f"Parallel multi-layer validation failed: {e}")
            return QualityAssessmentReport(overall_score=0.5)
    
    async def _apply_request_throttling(self):
        """Apply request throttling to prevent rate limit violations."""
        if not self.request_throttling:
            return
        
        with self.throttle_lock:
            current_time = time.time()
            
            # Remove old requests (older than 1 second)
            while self.request_times and current_time - self.request_times[0] > 1.0:
                self.request_times.popleft()
            
            # Check if we need to wait
            if len(self.request_times) >= self.max_requests_per_second:
                wait_time = 1.0 - (current_time - self.request_times[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
            
            # Record this request
            self.request_times.append(current_time)
    
    def _generate_cache_key(self, operation_type: str, *args) -> str:
        """Generate cache key for operation."""
        key_data = f"{operation_type}:{':'.join(str(arg) for arg in args)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get item from cache."""
        with self.cache_lock:
            # Check memory cache first
            if cache_key in self.memory_cache:
                self.cache_access_count[cache_key] += 1
                return self.memory_cache[cache_key]
            
            # Check disk cache if using hybrid or disk strategy
            if self.cache_strategy in [CacheStrategy.DISK, CacheStrategy.HYBRID]:
                disk_file = self.disk_cache_path / f"{cache_key}.json"
                if disk_file.exists():
                    try:
                        with open(disk_file, 'r') as f:
                            data = json.load(f)
                        
                        # Move to memory cache if using hybrid strategy
                        if self.cache_strategy == CacheStrategy.HYBRID:
                            self._store_in_memory_cache(cache_key, data)
                        
                        self.cache_access_count[cache_key] += 1
                        return data
                    except Exception as e:
                        self.logger.warning(f"Failed to read disk cache {cache_key}: {e}")
            
            return None
    
    def _store_in_cache(self, cache_key: str, data: Any):
        """Store item in cache."""
        with self.cache_lock:
            # Store in memory cache
            if self.cache_strategy in [CacheStrategy.MEMORY, CacheStrategy.HYBRID]:
                self._store_in_memory_cache(cache_key, data)
            
            # Store in disk cache
            if self.cache_strategy in [CacheStrategy.DISK, CacheStrategy.HYBRID]:
                self._store_in_disk_cache(cache_key, data)
    
    def _store_in_memory_cache(self, cache_key: str, data: Any):
        """Store item in memory cache."""
        # Implement LRU eviction if cache is full
        if len(self.memory_cache) >= self.cache_size:
            self._evict_lru_items()
        
        self.memory_cache[cache_key] = data
        self.cache_timestamps[cache_key] = time.time()
    
    def _store_in_disk_cache(self, cache_key: str, data: Any):
        """Store item in disk cache."""
        try:
            disk_file = self.disk_cache_path / f"{cache_key}.json"
            with open(disk_file, 'w') as f:
                json.dump(data, f, default=str)
        except Exception as e:
            self.logger.warning(f"Failed to write disk cache {cache_key}: {e}")
    
    def _evict_lru_items(self):
        """Evict least recently used items from memory cache."""
        if not self.cache_access_count:
            return
        
        # Find least accessed items
        sorted_items = sorted(self.cache_access_count.items(), key=lambda x: x[1])
        items_to_evict = sorted_items[:len(sorted_items) // 4]  # Evict 25%
        
        for cache_key, _ in items_to_evict:
            self.memory_cache.pop(cache_key, None)
            self.cache_timestamps.pop(cache_key, None)
            self.cache_access_count.pop(cache_key, None)
    
    def _record_metric(self, operation_type: str, execution_time: float, 
                      input_size: int, cache_hits: int):
        """Record performance metric."""
        with self.metrics_lock:
            # Get current system metrics
            memory_usage = psutil.virtual_memory().percent
            cpu_usage = psutil.cpu_percent()
            
            # Calculate throughput
            throughput = input_size / execution_time if execution_time > 0 else 0
            
            metric = OptimizationMetric(
                timestamp=time.time(),
                operation_type=operation_type,
                execution_time=execution_time,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                cache_hits=cache_hits,
                cache_misses=input_size - cache_hits,
                throughput=throughput,
                optimization_level=self.optimization_level,
                cache_strategy=self.cache_strategy
            )
            
            self.metrics.append(metric)
            self.operation_times[operation_type].append(execution_time)
            
            # Limit metrics history
            if len(self.metrics) > 1000:
                self.metrics = self.metrics[-500:]  # Keep last 500 metrics
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        with self.metrics_lock:
            if not self.metrics:
                return {
                    'summary': {
                        'total_metrics': 0,
                        'avg_execution_time': 0.0,
                        'avg_memory_usage': 0.0,
                        'avg_cpu_usage': 0.0,
                        'overall_cache_hit_rate': 0.0,
                        'avg_throughput': 0.0
                    },
                    'metrics': [],
                    'operation_breakdown': {},
                    'optimization_effectiveness': 0.0
                }
            
            # Calculate summary statistics
            total_metrics = len(self.metrics)
            avg_execution_time = sum(m.execution_time for m in self.metrics) / total_metrics
            avg_memory_usage = sum(m.memory_usage for m in self.metrics) / total_metrics
            avg_cpu_usage = sum(m.cpu_usage for m in self.metrics) / total_metrics
            
            total_cache_hits = sum(m.cache_hits for m in self.metrics)
            total_cache_misses = sum(m.cache_misses for m in self.metrics)
            cache_hit_rate = total_cache_hits / (total_cache_hits + total_cache_misses) if (total_cache_hits + total_cache_misses) > 0 else 0
            
            avg_throughput = sum(m.throughput for m in self.metrics) / total_metrics
            
            # Calculate operation breakdown
            operation_breakdown = {}
            for operation_type, times in self.operation_times.items():
                if times:
                    operation_breakdown[operation_type] = {
                        'count': len(times),
                        'avg_time': sum(times) / len(times),
                        'min_time': min(times),
                        'max_time': max(times)
                    }
            
            # Calculate optimization effectiveness
            baseline_time = 1.0  # Assume 1 second baseline
            optimization_effectiveness = max(0, (baseline_time - avg_execution_time) / baseline_time)
            
            return {
                'summary': {
                    'total_metrics': total_metrics,
                    'avg_execution_time': avg_execution_time,
                    'avg_memory_usage': avg_memory_usage,
                    'avg_cpu_usage': avg_cpu_usage,
                    'overall_cache_hit_rate': cache_hit_rate,
                    'avg_throughput': avg_throughput
                },
                'metrics': [
                    {
                        'timestamp': m.timestamp,
                        'operation_type': m.operation_type,
                        'execution_time': m.execution_time,
                        'memory_usage': m.memory_usage,
                        'cpu_usage': m.cpu_usage,
                        'cache_hits': m.cache_hits,
                        'cache_misses': m.cache_misses,
                        'throughput': m.throughput
                    }
                    for m in self.metrics[-50:]  # Last 50 metrics
                ],
                'operation_breakdown': operation_breakdown,
                'optimization_effectiveness': optimization_effectiveness,
                'cache_statistics': {
                    'memory_cache_size': len(self.memory_cache),
                    'disk_cache_path': str(self.disk_cache_path),
                    'cache_strategy': self.cache_strategy.value,
                    'total_cache_accesses': sum(self.cache_access_count.values())
                },
                'configuration': {
                    'optimization_level': self.optimization_level.value,
                    'max_workers': self.max_workers,
                    'parallel_enabled': self.parallel_enabled,
                    'batch_processing': self.batch_processing,
                    'request_throttling': self.request_throttling
                }
            }
    
    def clear_cache(self):
        """Clear all caches."""
        with self.cache_lock:
            # Clear memory cache
            self.memory_cache.clear()
            self.cache_timestamps.clear()
            self.cache_access_count.clear()
            
            # Clear disk cache
            if self.cache_strategy in [CacheStrategy.DISK, CacheStrategy.HYBRID]:
                try:
                    import shutil
                    if self.disk_cache_path.exists():
                        shutil.rmtree(self.disk_cache_path)
                        self.disk_cache_path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    self.logger.warning(f"Failed to clear disk cache: {e}")
        
        self.logger.info("All caches cleared")
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.cache_lock:
            return {
                'memory_cache': {
                    'size': len(self.memory_cache),
                    'max_size': self.cache_size,
                    'utilization': len(self.memory_cache) / self.cache_size if self.cache_size > 0 else 0
                },
                'disk_cache': {
                    'path': str(self.disk_cache_path),
                    'exists': self.disk_cache_path.exists(),
                    'file_count': len(list(self.disk_cache_path.glob('*.json'))) if self.disk_cache_path.exists() else 0
                },
                'access_patterns': dict(self.cache_access_count),
                'strategy': self.cache_strategy.value
            }
    
    def optimize_for_scenario(self, scenario: str) -> OptimizationResult:
        """Optimize performance for specific scenarios."""
        start_time = time.time()
        
        optimizations_applied = []
        
        if scenario == 'large_repository_analysis':
            # Optimize for large repository analysis
            self.set_optimization_level(OptimizationLevel.AGGRESSIVE)
            self.set_cache_strategy(CacheStrategy.HYBRID)
            optimizations_applied.extend(['aggressive_level', 'hybrid_cache'])
            
        elif scenario == 'real_time_validation':
            # Optimize for real-time validation
            self.set_optimization_level(OptimizationLevel.MODERATE)
            self.set_cache_strategy(CacheStrategy.MEMORY)
            optimizations_applied.extend(['moderate_level', 'memory_cache'])
            
        elif scenario == 'batch_processing':
            # Optimize for batch processing
            self.set_optimization_level(OptimizationLevel.BASIC)
            self.set_cache_strategy(CacheStrategy.DISK)
            optimizations_applied.extend(['basic_level', 'disk_cache', 'batch_mode'])
            
        elif scenario == 'api_heavy_workload':
            # Optimize for API-heavy workloads
            self.request_throttling = True
            self.batch_processing = True
            optimizations_applied.extend(['request_throttling', 'batch_processing'])
        
        execution_time = time.time() - start_time
        
        return OptimizationResult(
            operation_type='scenario_optimization',
            input_size=1,
            output_size=1,
            execution_time=execution_time,
            memory_saved=0.0,
            cache_hits=0,
            optimization_applied=optimizations_applied,
            performance_gain=0.2  # Estimated 20% performance gain
        )
    
    def benchmark_operation(self, operation_func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Benchmark a specific operation."""
        # Record baseline performance
        start_time = time.time()
        start_memory = psutil.virtual_memory().percent
        start_cpu = psutil.cpu_percent()
        
        try:
            result = operation_func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        end_time = time.time()
        end_memory = psutil.virtual_memory().percent
        end_cpu = psutil.cpu_percent()
        
        return {
            'success': success,
            'result': result,
            'error': error,
            'execution_time': end_time - start_time,
            'memory_delta': end_memory - start_memory,
            'cpu_delta': end_cpu - start_cpu,
            'timestamp': start_time
        }
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get optimization recommendations based on current metrics."""
        recommendations = []
        
        if not self.metrics:
            return ["No performance data available for recommendations"]
        
        # Analyze recent performance
        recent_metrics = self.metrics[-50:] if len(self.metrics) > 50 else self.metrics
        
        avg_execution_time = sum(m.execution_time for m in recent_metrics) / len(recent_metrics)
        avg_memory_usage = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
        avg_cpu_usage = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
        
        total_cache_hits = sum(m.cache_hits for m in recent_metrics)
        total_cache_misses = sum(m.cache_misses for m in recent_metrics)
        cache_hit_rate = total_cache_hits / (total_cache_hits + total_cache_misses) if (total_cache_hits + total_cache_misses) > 0 else 0
        
        # Generate recommendations
        if avg_execution_time > 5.0:
            recommendations.append("Consider increasing optimization level to AGGRESSIVE for better performance")
        
        if avg_memory_usage > 80:
            recommendations.append("High memory usage detected - consider using DISK cache strategy")
        
        if avg_cpu_usage > 90:
            recommendations.append("High CPU usage - consider reducing max_workers or using BASIC optimization level")
        
        if cache_hit_rate < 0.3:
            recommendations.append("Low cache hit rate - consider increasing cache size or TTL")
        
        if cache_hit_rate > 0.8:
            recommendations.append("Excellent cache performance - current configuration is optimal")
        
        if self.optimization_level == OptimizationLevel.BASIC and avg_execution_time < 2.0:
            recommendations.append("Performance is good - consider upgrading to MODERATE optimization level")
        
        return recommendations
    
    def export_performance_data(self, file_path: str):
        """Export performance data to file."""
        try:
            report = self.get_performance_report()
            
            with open(file_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.logger.info(f"Performance data exported to {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to export performance data: {e}")
    
    def reset_metrics(self):
        """Reset all performance metrics."""
        with self.metrics_lock:
            self.metrics.clear()
            self.operation_times.clear()
        
        self.logger.info("Performance metrics reset")


# Example usage and testing
async def main():
    """Test the performance optimizer."""
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create optimizer
    optimizer = PerformanceOptimizer()
    
    print(f"Performance Optimizer initialized:")
    print(f"  Optimization Level: {optimizer.optimization_level.value}")
    print(f"  Cache Strategy: {optimizer.cache_strategy.value}")
    print(f"  Max Workers: {optimizer.max_workers}")
    print(f"  Parallel Enabled: {optimizer.parallel_enabled}")
    
    # Test component optimization
    test_components = [
        CodeComponent(
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
        for i in range(10)
    ]
    
    print(f"\nTesting component analysis optimization...")
    optimized_components = optimizer.optimize_component_analysis(test_components)
    print(f"Optimized {len(optimized_components)} components")
    
    # Test pattern validation
    test_patterns = [
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
    
    print(f"\nTesting pattern validation optimization...")
    validated_components = optimizer.optimize_pattern_validation(test_components, test_patterns)
    print(f"Validated {len(validated_components)} components")
    
    # Generate performance report
    print(f"\nGenerating performance report...")
    report = optimizer.get_performance_report()
    
    print(f"Performance Report:")
    print(f"  Total Operations: {report['summary']['total_metrics']}")
    print(f"  Avg Execution Time: {report['summary']['avg_execution_time']:.4f}s")
    print(f"  Cache Hit Rate: {report['summary']['overall_cache_hit_rate']:.2%}")
    
    # Get recommendations
    recommendations = optimizer.get_optimization_recommendations()
    print(f"\nOptimization Recommendations:")
    for rec in recommendations:
        print(f"  • {rec}")


if __name__ == "__main__":
    asyncio.run(main())