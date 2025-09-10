"""
Pattern Validator with Enhanced SourceGraph Integration

Validates generated code against real-world patterns discovered from SourceGraph.
Ensures code follows best practices and avoids common anti-patterns.
Enhanced with SourceGraph pattern discovery, similarity scoring, and pattern-based validation.
"""

import asyncio
import logging
import re
import os
import time
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

import aiohttp
from difflib import SequenceMatcher


@dataclass
class ValidationIssue:
    """Validation issue found in generated code."""
    issue_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    suggestion: str
    line_number: Optional[int] = None
    confidence: float = 0.0


@dataclass
class PatternValidationResult:
    """Result of pattern validation."""
    is_valid: bool
    overall_score: float
    issues: List[ValidationIssue]
    similar_patterns: List[Dict]
    common_patterns: List[str]
    recommendations: List[str]
    sourcegraph_insights: Dict[str, Any] = field(default_factory=dict)
    pattern_discovery_recommendations: List[str] = field(default_factory=list)
    sourcegraph_validation_score: float = 0.0
    pattern_similarity_analysis: Dict[str, Any] = field(default_factory=dict)


class PatternValidator:
    """Validates generated code against real-world patterns."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Common anti-patterns to check for
        self.anti_patterns = {
            'hardcoded_values': [
                r'localhost[:\d+]',
                r'127\.0\.0\.1[:\d+]',
                r'password\s*=\s*[\'"][^\'"]*[\'"]',
                r'token\s*=\s*[\'"][^\'"]*[\'"]',
                r'api_key\s*=\s*[\'"][^\'"]*[\'"]'
            ],
            'missing_error_handling': [
                r'requests\.(get|post|put|delete)\(',
                r'sql\.',
                r'open\(',
                r'subprocess\.',
                r'os\.system'
            ],
            'security_issues': [
                r'eval\(',
                r'exec\(',
                r'subprocess\.run\(.*shell=True',
                r'pickle\.loads',
                r'marshal\.loads'
            ],
            'performance_issues': [
                r'for\s+\w+\s+in\s+range\(.*len\(',
                r'\.iteritems\(\)',
                r'import\s+*\*',
                r'global\s+\w+'
            ]
        }
        
        # Best practices patterns
        self.best_practices = {
            'proper_error_handling': [
                r'try:',
                r'except\s+',
                r'finally:',
                r'raise\s+'
            ],
            'logging': [
                r'import\s+logging',
                r'logger\.',
                r'logging\.'
            ],
            'type_hints': [
                r'def\s+\w+\s*\([^)]*:\s*\w+',
                r':\s*\w+\s*=\s*',
                r'->\s*\w+'
            ],
            'async_patterns': [
                r'async\s+def\s+',
                r'await\s+',
                r'async\s+with\s+'
            ]
        }
        
        # Common library patterns
        self.library_patterns = {
            'requests': {
                'proper_usage': [
                    r'requests\.(get|post|put|delete)\([^)]*\)',
                    r'session\s*=\s*requests\.Session\(\)',
                    r'response\s*=\s*requests\.',
                    r'json\(\)'
                ],
                'common_issues': [
                    r'requests\.(get|post|put|delete)\([^)]*\)\.text',
                    r'requests\.(get|post|put|delete)\([^)]*\)\.json\(\)',
                    r'missing\s+timeout'
                ]
            },
            'flask': {
                'proper_usage': [
                    r'@app\.(route|get|post)',
                    r'Flask\(\)',
                    r'request\.',
                    r'render_template'
                ],
                'common_issues': [
                    r'@app\.route\([^)]*\)\s*def\s+\w+\s*\([^)]*\):\s*return\s+',
                    r'missing\s+debug\s+mode'
                ]
            },
            'pandas': {
                'proper_usage': [
                    r'pd\.read_csv',
                    r'pd\.DataFrame',
                    r'df\.',
                    r'groupby\(',
                    r'merge\('
                ],
                'common_issues': [
                    r'df\[.*\]\s*=',
                    r'iterrows\(\)',
                    r'chain\.index'
                ]
            }
        }
    
    async def validate_against_production_patterns(self, generated_code: str, libraries: List[str]) -> PatternValidationResult:
        """Validate generated code against real-world patterns with enhanced SourceGraph integration."""
        self.logger.info(f"Validating code against production patterns for libraries: {libraries}")
        
        issues = []
        
        # Check for anti-patterns
        anti_pattern_issues = self._check_anti_patterns(generated_code)
        issues.extend(anti_pattern_issues)
        
        # Check for best practices
        best_practice_issues = self._check_best_practices(generated_code)
        issues.extend(best_practice_issues)
        
        # Check library-specific patterns
        library_issues = await self._check_library_patterns(generated_code, libraries)
        issues.extend(library_issues)
        
        # Enhanced code structure validation
        if self.enable_comprehensive_validation:
            structure_issues = self._check_code_structure(generated_code)
            issues.extend(structure_issues)
            
            quality_issues = self._check_code_quality(generated_code)
            issues.extend(quality_issues)
            
            error_handling_issues = self._check_error_handling_patterns(generated_code)
            issues.extend(error_handling_issues)
        
        # Find similar implementations
        similar_patterns = await self.find_similar_implementations(generated_code, libraries)
        
        # Analyze common patterns
        pattern_analysis = self.analyze_common_patterns(similar_patterns)
        
        # Compare with patterns
        comparison_result = self.compare_with_patterns(generated_code, pattern_analysis)
        
        # Enhanced SourceGraph validation if enabled
        sourcegraph_insights = {}
        sourcegraph_validation_score = 0.0
        pattern_discovery_recommendations = []
        
        if self.sourcegraph_validation_enabled:
            try:
                sourcegraph_result = await self._validate_with_sourcegraph(generated_code, libraries)
                sourcegraph_insights = sourcegraph_result.get('insights', {})
                sourcegraph_validation_score = sourcegraph_result.get('validation_score', 0.0)
                pattern_discovery_recommendations = sourcegraph_result.get('recommendations', [])
                
                # Add SourceGraph validation issues
                sourcegraph_issues = sourcegraph_result.get('issues', [])
                issues.extend(sourcegraph_issues)
                
            except Exception as e:
                self.logger.warning(f"SourceGraph validation failed: {e}")
        
        # Calculate overall score with SourceGraph contribution
        overall_score = self._calculate_validation_score(issues, pattern_analysis, sourcegraph_validation_score)
        
        # Generate recommendations with SourceGraph insights
        recommendations = self._generate_recommendations(issues, pattern_analysis)
        recommendations.extend(pattern_discovery_recommendations)
        
        # Perform pattern similarity analysis
        pattern_similarity_analysis = self._analyze_pattern_similarity(generated_code, similar_patterns)
        
        result = PatternValidationResult(
            is_valid=len(issues) == 0 and overall_score > 0.8,
            overall_score=overall_score,
            issues=issues,
            similar_patterns=similar_patterns,
            common_patterns=pattern_analysis.get('common_patterns', []),
            recommendations=recommendations,
            sourcegraph_insights=sourcegraph_insights,
            pattern_discovery_recommendations=pattern_discovery_recommendations,
            sourcegraph_validation_score=sourcegraph_validation_score,
            pattern_similarity_analysis=pattern_similarity_analysis
        )
        
        self.logger.info(f"Validation completed. Score: {overall_score:.2f}, Issues: {len(issues)}")
        return result
    
    def _check_anti_patterns(self, code: str) -> List[ValidationIssue]:
        """Check for common anti-patterns in the code."""
        issues = []
        
        for anti_pattern_type, patterns in self.anti_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, code, re.IGNORECASE)
                
                for match in matches:
                    issue = self._create_anti_pattern_issue(anti_pattern_type, match)
                    issues.append(issue)
        
        return issues
    
    def _create_anti_pattern_issue(self, anti_pattern_type: str, match) -> ValidationIssue:
        """Create a validation issue for an anti-pattern."""
        
        issue_descriptions = {
            'hardcoded_values': 'Hardcoded values detected',
            'missing_error_handling': 'Missing error handling for potentially risky operations',
            'security_issues': 'Potential security vulnerability detected',
            'performance_issues': 'Potential performance issue detected'
        }
        
        suggestions = {
            'hardcoded_values': 'Use environment variables or configuration files',
            'missing_error_handling': 'Add try/except blocks for error handling',
            'security_issues': 'Follow security best practices and validate inputs',
            'performance_issues': 'Consider more efficient alternatives'
        }
        
        severity_map = {
            'hardcoded_values': 'medium',
            'missing_error_handling': 'high',
            'security_issues': 'critical',
            'performance_issues': 'medium'
        }
        
        # Extract line number (approximate)
        line_number = code[:match.start()].count('\n') + 1
        
        return ValidationIssue(
            issue_type=anti_pattern_type,
            severity=severity_map.get(anti_pattern_type, 'medium'),
            description=issue_descriptions.get(anti_pattern_type, 'Anti-pattern detected'),
            suggestion=suggestions.get(anti_pattern_type, 'Review and refactor'),
            line_number=line_number,
            confidence=0.8
        )
    
    def _check_best_practices(self, code: str) -> List[ValidationIssue]:
        """Check for best practices in the code."""
        issues = []
        
        for practice_type, patterns in self.best_practices.items():
            found_patterns = []
            
            for pattern in patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    found_patterns.append(pattern)
            
            # If best practice is missing, add issue
            if not found_patterns and practice_type != 'async_patterns':  # async is optional
                issue = self._create_missing_practice_issue(practice_type)
                issues.append(issue)
        
        return issues
    
    def _create_missing_practice_issue(self, practice_type: str) -> ValidationIssue:
        """Create a validation issue for missing best practices."""
        
        issue_descriptions = {
            'proper_error_handling': 'Missing proper error handling',
            'logging': 'Missing logging implementation',
            'type_hints': 'Missing type hints',
            'async_patterns': 'Consider using async patterns for better performance'
        }
        
        suggestions = {
            'proper_error_handling': 'Add try/except blocks with proper exception handling',
            'logging': 'Add logging statements for debugging and monitoring',
            'type_hints': 'Add type hints for better code maintainability',
            'async_patterns': 'Consider using async/await for I/O operations'
        }
        
        severity_map = {
            'proper_error_handling': 'high',
            'logging': 'medium',
            'type_hints': 'low',
            'async_patterns': 'low'
        }
        
        return ValidationIssue(
            issue_type='missing_best_practice',
            severity=severity_map.get(practice_type, 'medium'),
            description=issue_descriptions.get(practice_type, 'Best practice not followed'),
            suggestion=suggestions.get(practice_type, 'Consider implementing this best practice'),
            line_number=None,
            confidence=0.6
        )
    
    async def _check_library_patterns(self, code: str, libraries: List[str]) -> List[ValidationIssue]:
        """Check for library-specific patterns and issues."""
        issues = []
        
        for library in libraries:
            if library in self.library_patterns:
                library_issues = self._analyze_library_code(code, library)
                issues.extend(library_issues)
        
        return issues
    
    def _analyze_library_code(self, code: str, library: str) -> List[ValidationIssue]:
        """Analyze code for specific library patterns."""
        issues = []
        patterns = self.library_patterns[library]
        
        # Check for proper usage patterns
        for pattern in patterns['proper_usage']:
            if not re.search(pattern, code, re.IGNORECASE):
                issue = self._create_missing_library_pattern_issue(library, 'proper_usage')
                issues.append(issue)
                break  # Only add one issue per missing pattern type
        
        # Check for common issues
        for pattern in patterns['common_issues']:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                issue = self._create_library_issue_issue(library, match)
                issues.append(issue)
        
        return issues
    
    def _create_missing_library_pattern_issue(self, library: str, pattern_type: str) -> ValidationIssue:
        """Create an issue for missing library patterns."""
        suggestions = {
            'requests': 'Use proper requests patterns with sessions and error handling',
            'flask': 'Follow Flask best practices for route definitions and error handling',
            'pandas': 'Use pandas idioms for efficient data manipulation'
        }
        
        return ValidationIssue(
            issue_type=f'missing_{library}_pattern',
            severity='medium',
            description=f'Missing proper {library} usage patterns',
            suggestion=suggestions.get(library, 'Review library documentation for best practices'),
            line_number=None,
            confidence=0.5
        )
    
    def _create_library_issue_issue(self, library: str, match) -> ValidationIssue:
        """Create an issue for library-specific problems."""
        line_number = match.string[:match.start()].count('\n') + 1
        
        library_specific_issues = {
            'requests': {
                'requests\\.get\\([^)]*\\)\\.text': 'Use response.json() for JSON data instead of text',
                'requests\\.get\\([^)]*\\)\\.json\\(\\)': 'Check response status before accessing JSON',
                'missing\\s+timeout': 'Add timeout parameter to prevent hanging requests'
            },
            'flask': {
                '@app\\.route\\([^)]*\\)\\s*def\\s+\\w+\\s*\\([^)]*\\):\\s*return\\s+': 'Consider returning proper response objects',
                'missing\\s+debug\\s+mode': 'Consider setting debug mode for development'
            },
            'pandas': {
                'df\\[.*\\]\\s*=': 'Use .loc[] or .iloc[] for assignment',
                'iterrows\\(\\)': 'Use .itertuples() or vectorized operations instead',
                'chain\\.index': 'Use .reset_index() instead of chain.index'
            }
        }
        
        issue_key = None
        for key, description in library_specific_issues.get(library, {}).items():
            if re.search(key, match.group(0), re.IGNORECASE):
                issue_key = key
                break
        
        description = library_specific_issues.get(library, {}).get(issue_key, 'Common library issue detected')
        
        return ValidationIssue(
            issue_type=f'{library}_issue',
            severity='medium',
            description=description,
            suggestion='Review library documentation for proper usage',
            line_number=line_number,
            confidence=0.7
        )
    
    async def find_similar_implementations(self, generated_code: str, libraries: List[str]) -> List[Dict]:
        """Find similar implementations in SourceGraph with enhanced pattern matching."""
        if not self.sourcegraph_enabled:
            # Fallback to mock implementations
            return self._generate_mock_similar_implementations(generated_code, libraries)
        
        try:
            # Check cache first
            cache_key = self._generate_cache_key(generated_code, libraries)
            if self.pattern_cache_enabled and cache_key in self.pattern_cache:
                cached_result, timestamp = self.pattern_cache[cache_key]
                if time.time() - timestamp < self.pattern_cache_ttl:
                    self.logger.info("Returning cached similar implementations")
                    return cached_result
            
            # Import SourceGraph integration
            from .sourcegraph_integration import SourceGraphDiscovery
            
            similar = []
            
            async with SourceGraphDiscovery() as discovery:
                for library in libraries:
                    try:
                        # Discover patterns for this library
                        patterns = await discovery.discover_integration_patterns([library], "general")
                        
                        # Find similar patterns
                        for pattern in patterns[:self.max_pattern_discovery_results]:
                            similarity_score = self._calculate_code_similarity(generated_code, pattern)
                            
                            if similarity_score >= self.min_pattern_similarity:
                                similar_implementation = {
                                    'library': library,
                                    'similarity_score': similarity_score,
                                    'pattern_id': pattern.pattern_id,
                                    'repositories': [example.repository for example in pattern.code_examples],
                                    'paths': [example.path for example in pattern.code_examples],
                                    'key_differences': self._identify_key_differences(generated_code, pattern),
                                    'common_features': self._identify_common_features(generated_code, pattern),
                                    'confidence_score': pattern.confidence_score,
                                    'pattern_features': pattern.pattern_features,
                                    'best_practices': pattern.best_practices,
                                    'common_issues': pattern.common_issues
                                }
                                similar.append(similar_implementation)
                                
                    except Exception as e:
                        self.logger.warning(f"Failed to find similar implementations for {library}: {e}")
                        continue
            
            # Sort by similarity score
            similar.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # Cache results
            if self.pattern_cache_enabled:
                self.pattern_cache[cache_key] = (similar, time.time())
            
            return similar
            
        except ImportError:
            self.logger.warning("SourceGraph integration not available")
            return self._generate_mock_similar_implementations(generated_code, libraries)
        except Exception as e:
            self.logger.error(f"Similar implementation search failed: {e}")
            return self._generate_mock_similar_implementations(generated_code, libraries)
    
    def _generate_mock_similar_implementations(self, generated_code: str, libraries: List[str]) -> List[Dict]:
        """Generate mock similar implementations when SourceGraph is unavailable."""
        similar = []
        
        # Generate mock similar implementations based on libraries
        for library in libraries[:2]:  # Limit to top 2 libraries
            similar.append({
                'library': library,
                'similarity_score': 0.75,
                'repository': f'example/{library}-implementation',
                'path': f'examples/{library}_usage.py',
                'key_differences': [
                    'Uses different error handling approach',
                    'Implements additional validation'
                ],
                'common_features': [
                    f'Uses {library} for primary functionality',
                    'Follows similar code structure'
                ],
                'confidence_score': 0.7,
                'pattern_features': {},
                'best_practices': [],
                'common_issues': []
            })
        
        return similar
    
    def analyze_common_patterns(self, patterns: List[Dict]) -> Dict:
        """Analyze common patterns from similar implementations."""
        if not patterns:
            return {}
        
        # Extract common features across patterns
        all_features = []
        for pattern in patterns:
            all_features.extend(pattern.get('common_features', []))
        
        # Count frequency of each feature
        feature_counts = {}
        for feature in all_features:
            feature_counts[feature] = feature_counts.get(feature, 0) + 1
        
        # Get most common features
        common_patterns = [
            feature for feature, count in feature_counts.items() 
            if count >= len(patterns) * 0.5  # Present in at least 50% of patterns
        ]
        
        return {
            'common_patterns': common_patterns,
            'total_patterns_analyzed': len(patterns),
            'feature_diversity': len(set(all_features))
        }
    
    def compare_with_patterns(self, generated_code: str, pattern_analysis: Dict) -> Dict:
        """Compare generated code with discovered patterns."""
        if not pattern_analysis:
            return {'alignment_score': 0.0, 'missing_patterns': []}
        
        common_patterns = pattern_analysis.get('common_patterns', [])
        alignment_score = 0.0
        
        # Check how many common patterns are present in generated code
        patterns_found = 0
        missing_patterns = []
        
        for pattern in common_patterns:
            if pattern.lower() in generated_code.lower():
                patterns_found += 1
                alignment_score += 1.0 / len(common_patterns)
            else:
                missing_patterns.append(pattern)
        
        # Normalize alignment score
        if common_patterns:
            alignment_score = patterns_found / len(common_patterns)
        
        return {
            'alignment_score': alignment_score,
            'patterns_found': patterns_found,
            'total_patterns': len(common_patterns),
            'missing_patterns': missing_patterns
        }
    
    def _calculate_validation_score(self, issues: List[ValidationIssue], pattern_analysis: Dict) -> float:
        """Calculate overall validation score."""
        if not issues and pattern_analysis:
            return 1.0
        
        # Start with a base score
        score = 1.0
        
        # Deduct points for issues
        for issue in issues:
            if issue.severity == 'critical':
                score -= 0.3
            elif issue.severity == 'high':
                score -= 0.2
            elif issue.severity == 'medium':
                score -= 0.1
            else:  # low
                score -= 0.05
        
        # Consider pattern alignment
        alignment_score = pattern_analysis.get('alignment_score', 0.0)
        score = (score + alignment_score) / 2
        
        # Ensure score is within valid range
        return max(0.0, min(1.0, score))
    
    def _generate_recommendations(self, issues: List[ValidationIssue], pattern_analysis: Dict) -> List[str]:
        """Generate improvement recommendations based on validation results."""
        recommendations = []
        
        # Group issues by severity
        critical_issues = [issue for issue in issues if issue.severity == 'critical']
        high_issues = [issue for issue in issues if issue.severity == 'high']
        medium_issues = [issue for issue in issues if issue.severity == 'medium']
        
        if critical_issues:
            recommendations.append("Address critical security and error handling issues immediately")
        
        if high_issues:
            recommendations.append("Fix high-priority issues to improve code reliability")
        
        if medium_issues:
            recommendations.append("Consider addressing medium-priority issues for better maintainability")
        
        # Add pattern-based recommendations
        missing_patterns = pattern_analysis.get('missing_patterns', [])
        if missing_patterns:
            recommendations.append(f"Consider implementing common patterns: {', '.join(missing_patterns[:3])}")
        
        if not issues:
            recommendations.append("Code follows good practices and common patterns")
        
        return recommendations