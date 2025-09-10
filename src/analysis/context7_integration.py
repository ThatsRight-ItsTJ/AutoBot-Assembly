"""
Context7 Integration for Enhanced Code Analysis

Provides Context7-powered code analysis, API validation, and real-time insights
with fallback mechanisms when Context7 is unavailable.
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path

# Import MCP client for Context7 integration
try:
    import mcp
    from mcp.client.session import ClientSession
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    mcp = None
    ClientSession = None
    stdio_client = None

# Import configuration management
try:
    from src.cli.config_manager import ConfigManager
except ImportError:
    ConfigManager = None

# Import UniversalCodeAnalyzer for fallback
try:
    from .universal_code_analyzer import UniversalCodeAnalyzer
    UNIVERSAL_ANALYZER_AVAILABLE = True
except ImportError:
    UNIVERSAL_ANALYZER_AVAILABLE = False
    UniversalCodeAnalyzer = None


@dataclass
class Context7AnalysisResult:
    """Result of Context7 analysis."""
    success: bool
    file_path: str
    language: str
    insights: Dict[str, Any]
    api_validations: List[Dict[str, Any]]
    code_issues: List[Dict[str, Any]]
    recommendations: List[str]
    confidence_score: float
    analysis_timestamp: str


@dataclass
class Context7APIValidation:
    """API validation result from Context7."""
    api_name: str
    endpoint: str
    validation_status: str  # 'valid', 'invalid', 'warning'
    issues: List[str]
    suggestions: List[str]
    security_score: float


class Context7Analyzer:
    """Context7-powered code analysis with MCP integration."""
    
    def __init__(self, enable_fallback: bool = True):
        self.logger = logging.getLogger(__name__)
        self.enable_fallback = enable_fallback and UNIVERSAL_ANALYZER_AVAILABLE
        
        # Initialize Context7 MCP client
        self.context7_client = None
        self.context7_available = False
        
        # Initialize fallback analyzer
        self.fallback_analyzer = None
        if self.enable_fallback:
            try:
                self.fallback_analyzer = UniversalCodeAnalyzer()
                self.logger.info("UniversalCodeAnalyzer initialized as fallback")
            except Exception as e:
                self.logger.warning(f"Failed to initialize fallback analyzer: {e}")
                self.fallback_analyzer = None
        
        # Initialize configuration
        self.config_manager = None
        if ConfigManager:
            try:
                self.config_manager = ConfigManager()
            except Exception as e:
                self.logger.warning(f"Failed to initialize ConfigManager: {e}")
        
        # Load Context7 configuration
        self.context7_config = self._load_context7_config()
        
        # Initialize Context7 client
        self._initialize_context7_client()
        
        # Supported languages for Context7 analysis
        self.supported_languages = [
            'python', 'javascript', 'typescript', 'java', 'go', 'rust',
            'php', 'ruby', 'c', 'cpp', 'csharp', 'swift', 'kotlin'
        ]
    
    def _load_context7_config(self) -> Dict[str, Any]:
        """Load Context7 configuration from environment and config files."""
        config = {
            'enabled': os.getenv('CONTEXT7_ENABLED', 'true').lower() == 'true',
            'max_tokens': int(os.getenv('CONTEXT7_MAX_TOKENS', '10000')),
            'timeout': 30,
            'retry_attempts': 3,
            'mcp_config_path': 'mcp_config.json'
        }
        
        # Override with function-specific configuration if available
        if self.config_manager:
            try:
                func_config = self.config_manager.get_function_api_key('context7_analyzer')
                if func_config:
                    config.update({
                        'enabled': func_config.get('enabled', config['enabled']),
                        'max_tokens': func_config.get('max_tokens', config['max_tokens']),
                        'timeout': func_config.get('timeout', config['timeout'])
                    })
            except Exception as e:
                self.logger.warning(f"Failed to load function-specific config: {e}")
        
        return config
    
    def _initialize_context7_client(self):
        """Initialize Context7 MCP client."""
        if not self.context7_config['enabled']:
            self.logger.info("Context7 integration disabled by configuration")
            return
        
        if not MCP_AVAILABLE:
            self.logger.warning("MCP client not available, Context7 integration disabled")
            return
        
        try:
            # Load MCP configuration
            mcp_config_path = Path(self.context7_config['mcp_config_path'])
            if not mcp_config_path.exists():
                self.logger.warning(f"MCP config file not found: {mcp_config_path}")
                return
            
            with open(mcp_config_path, 'r') as f:
                mcp_config = json.load(f)
            
            # Initialize Context7 server configuration
            context7_server_config = mcp_config.get('mcpServers', {}).get('context7')
            if not context7_server_config:
                self.logger.warning("Context7 server configuration not found in MCP config")
                return
            
            # Initialize MCP client
            self.context7_client = stdio_client(
                command=context7_server_config['command'],
                args=context7_server_config.get('args', []),
                env=context7_server_config.get('env', {})
            )
            
            # Test connection
            asyncio.run(self._test_context7_connection())
            self.context7_available = True
            self.logger.info("Context7 MCP client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Context7 client: {e}")
            self.context7_available = False
    
    async def _test_context7_connection(self) -> bool:
        """Test Context7 connection with a simple analysis request."""
        if not self.context7_client:
            return False
        
        try:
            # Create a test session
            async with self.context7_client as streams:
                async with ClientSession(*streams) as session:
                    # Test with a simple code snippet
                    test_code = "def hello():\n    print('Hello, World!')"
                    test_request = {
                        'code': test_code,
                        'language': 'python',
                        'analysis_type': 'structure'
                    }
                    
                    # Send test request (adjust based on actual Context7 API)
                    await session.initialize()
                    result = await session.call_tool('analyze', test_request)
                    
                    return result is not None
                    
        except Exception as e:
            self.logger.warning(f"Context7 connection test failed: {e}")
            return False
    
    async def analyze_file(self, file_path: str, language: str, 
                          analysis_types: List[str] = None) -> Context7AnalysisResult:
        """
        Analyze a file using Context7 with fallback to Tree-sitter.
        
        Args:
            file_path: Path to the file to analyze
            language: Programming language
            analysis_types: Types of analysis to perform (structure, api, security, etc.)
            
        Returns:
            Context7AnalysisResult with analysis results
        """
        if not os.path.exists(file_path):
            return Context7AnalysisResult(
                success=False,
                file_path=file_path,
                language=language,
                insights={},
                api_validations=[],
                code_issues=[],
                recommendations=[f"File not found: {file_path}"],
                confidence_score=0.0,
                analysis_timestamp=self._get_timestamp()
            )
        
        # Set default analysis types
        if analysis_types is None:
            analysis_types = ['structure', 'api', 'security']
        
        # Try Context7 analysis first
        if self.context7_available and language in self.supported_languages:
            try:
                result = await self._analyze_with_context7(file_path, language, analysis_types)
                if result and result.success:
                    return result
            except Exception as e:
                self.logger.warning(f"Context7 analysis failed for {file_path}: {e}")
        
        # Fallback to Tree-sitter analysis
        if self.fallback_analyzer:
            try:
                return await self._analyze_with_fallback(file_path, language, analysis_types)
            except Exception as e:
                self.logger.error(f"Fallback analysis failed for {file_path}: {e}")
        
        # Return empty result if both methods fail
        return Context7AnalysisResult(
            success=False,
            file_path=file_path,
            language=language,
            insights={},
            api_validations=[],
            code_issues=[f"Analysis failed for file: {file_path}"],
            recommendations=["Manual review required"],
            confidence_score=0.0,
            analysis_timestamp=self._get_timestamp()
        )
    
    async def _analyze_with_context7(self, file_path: str, language: str, 
                                   analysis_types: List[str]) -> Context7AnalysisResult:
        """Analyze file using Context7 MCP client."""
        try:
            async with self.context7_client as streams:
                async with ClientSession(*streams) as session:
                    await session.initialize()
                    
                    # Read file content
                    with open(file_path, 'r', encoding='utf-8') as f:
                        code_content = f.read()
                    
                    # Prepare analysis request
                    analysis_request = {
                        'code': code_content,
                        'language': language,
                        'analysis_types': analysis_types,
                        'max_tokens': self.context7_config['max_tokens']
                    }
                    
                    # Call Context7 analysis tool
                    result = await session.call_tool('analyze', analysis_request)
                    
                    if result:
                        return self._parse_context7_response(result, file_path, language)
                    else:
                        raise Exception("Context7 returned empty result")
                        
        except Exception as e:
            self.logger.error(f"Context7 analysis error: {e}")
            raise
    
    def _parse_context7_response(self, response: Any, file_path: str, 
                                language: str) -> Context7AnalysisResult:
        """Parse Context7 response into structured result."""
        try:
            # Convert response to dict if it's not already
            if hasattr(response, '__dict__'):
                response_data = response.__dict__
            else:
                response_data = response
            
            # Extract analysis results
            insights = response_data.get('insights', {})
            api_validations = response_data.get('api_validations', [])
            code_issues = response_data.get('code_issues', [])
            recommendations = response_data.get('recommendations', [])
            confidence_score = float(response_data.get('confidence_score', 0.5))
            
            return Context7AnalysisResult(
                success=True,
                file_path=file_path,
                language=language,
                insights=insights,
                api_validations=api_validations,
                code_issues=code_issues,
                recommendations=recommendations,
                confidence_score=confidence_score,
                analysis_timestamp=self._get_timestamp()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse Context7 response: {e}")
            raise
    
    async def _analyze_with_fallback(self, file_path: str, language: str, 
                                   analysis_types: List[str]) -> Context7AnalysisResult:
        """Analyze file using fallback Tree-sitter analyzer."""
        try:
            # Use UniversalCodeAnalyzer for comprehensive analysis
            tree_sitter_result = self.fallback_analyzer.analyze_file(file_path, language)
            
            if not tree_sitter_result or not tree_sitter_result.get('success'):
                raise Exception("Tree-sitter analysis failed")
            
            # Convert Tree-sitter result to Context7 format
            return self._convert_tree_sitter_to_context7_format(
                tree_sitter_result, file_path, language
            )
            
        except Exception as e:
            self.logger.error(f"Fallback analysis error: {e}")
            raise
    
    def _convert_tree_sitter_to_context7_format(self, tree_sitter_result: Dict[str, Any], 
                                              file_path: str, language: str) -> Context7AnalysisResult:
        """Convert Tree-sitter analysis result to Context7 format."""
        
        metrics = tree_sitter_result.get('metrics', {})
        structure = tree_sitter_result.get('structure', {})
        
        # Extract insights from Tree-sitter analysis
        insights = {
            'complexity_score': float(metrics.get('complexity_score', 0.0)),
            'maintainability_index': float(metrics.get('maintainability_index', 0.5)),
            'cyclomatic_complexity': int(metrics.get('cyclomatic_complexity', 1)),
            'lines_of_code': int(metrics.get('lines_of_code', 0)),
            'comment_ratio': float(metrics.get('comment_ratio', 0.0))
        }
        
        # Extract API-like patterns (simplified detection)
        api_validations = self._detect_api_patterns(structure, language)
        
        # Extract code issues
        code_issues = self._detect_code_issues(metrics, structure)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(insights, code_issues)
        
        # Calculate confidence score
        confidence_score = min(0.8, float(metrics.get('confidence_score', 0.5)))
        
        return Context7AnalysisResult(
            success=True,
            file_path=file_path,
            language=language,
            insights=insights,
            api_validations=api_validations,
            code_issues=code_issues,
            recommendations=recommendations,
            confidence_score=confidence_score,
            analysis_timestamp=self._get_timestamp()
        )
    
    def _detect_api_patterns(self, structure: Dict[str, Any], language: str) -> List[Context7APIValidation]:
        """Detect API-like patterns in code structure."""
        api_validations = []
        
        # Check for common API patterns based on language
        if language.lower() == 'python':
            # FastAPI/Flask patterns
            if any(pattern in str(structure).lower() for pattern in ['@app.', 'fastapi', 'flask']):
                api_validations.append(Context7APIValidation(
                    api_name='web_framework',
                    endpoint='auto-detected',
                    validation_status='valid',
                    issues=[],
                    suggestions=['Consider using OpenAPI documentation'],
                    security_score=0.8
                ))
        
        elif language.lower() == 'javascript':
            # Express.js patterns
            if any(pattern in str(structure).lower() for pattern in ['express()', 'app.get', 'app.post']):
                api_validations.append(Context7APIValidation(
                    api_name='express_api',
                    endpoint='auto-detected',
                    validation_status='valid',
                    issues=[],
                    suggestions=['Consider adding rate limiting'],
                    security_score=0.7
                ))
        
        return api_validations
    
    def _detect_code_issues(self, metrics: Dict[str, Any], structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect common code issues from metrics and structure."""
        issues = []
        
        # Check complexity issues
        complexity_score = float(metrics.get('complexity_score', 0.0))
        if complexity_score > 0.8:
            issues.append({
                'type': 'high_complexity',
                'severity': 'warning',
                'message': f'High complexity score: {complexity_score:.2f}',
                'suggestion': 'Consider breaking down complex functions'
            })
        
        # Check maintainability issues
        maintainability_index = float(metrics.get('maintainability_index', 0.0))
        if maintainability_index < 0.5:
            issues.append({
                'type': 'low_maintainability',
                'severity': 'warning',
                'message': f'Low maintainability index: {maintainability_index:.2f}',
                'suggestion': 'Improve code structure and documentation'
            })
        
        # Check for test coverage
        if not structure.get('has_tests', False):
            issues.append({
                'type': 'missing_tests',
                'severity': 'info',
                'message': 'No test files detected',
                'suggestion': 'Add unit tests for better code quality'
            })
        
        return issues
    
    def _generate_recommendations(self, insights: Dict[str, Any], 
                                code_issues: List[Dict[str, Any]]) -> List[str]:
        """Generate improvement recommendations based on analysis."""
        recommendations = []
        
        # Complexity-based recommendations
        complexity_score = insights.get('complexity_score', 0.0)
        if complexity_score > 0.7:
            recommendations.append("Consider refactoring complex functions")
        
        # Maintainability-based recommendations
        maintainability_index = insights.get('maintainability_index', 0.0)
        if maintainability_index < 0.6:
            recommendations.append("Improve code documentation and structure")
        
        # Test coverage recommendations
        test_issues = [issue for issue in code_issues if issue['type'] == 'missing_tests']
        if test_issues:
            recommendations.append("Add comprehensive test coverage")
        
        # Security recommendations
        if insights.get('lines_of_code', 0) > 1000:
            recommendations.append("Consider security audit for large codebase")
        
        return recommendations
    
    async def validate_apis(self, file_path: str, language: str) -> List[Context7APIValidation]:
        """
        Validate API endpoints and patterns in the code.
        
        Args:
            file_path: Path to file to validate
            language: Programming language
            
        Returns:
            List of API validation results
        """
        # Perform analysis focused on API validation
        analysis_result = await self.analyze_file(
            file_path, language, ['api', 'structure']
        )
        
        return analysis_result.api_validations
    
    async def real_time_analysis(self, file_path: str, language: str, 
                               debounce_ms: int = 1000) -> Context7AnalysisResult:
        """
        Perform real-time analysis with debouncing.
        
        Args:
            file_path: Path to file to analyze
            language: Programming language
            debounce_ms: Debounce delay in milliseconds
            
        Returns:
            Latest analysis result
        """
        try:
            # Simple implementation with asyncio.sleep for debouncing
            await asyncio.sleep(debounce_ms / 1000.0)
            
            return await self.analyze_file(file_path, language)
            
        except Exception as e:
            self.logger.error(f"Real-time analysis failed: {e}")
            return Context7AnalysisResult(
                success=False,
                file_path=file_path,
                language=language,
                insights={},
                api_validations=[],
                code_issues=[f"Real-time analysis failed: {e}"],
                recommendations=["Manual review required"],
                confidence_score=0.0,
                analysis_timestamp=self._get_timestamp()
            )
    
    def get_context7_status(self) -> Dict[str, Any]:
        """Get Context7 integration status."""
        return {
            'context7_available': self.context7_available,
            'fallback_available': self.fallback_analyzer is not None,
            'supported_languages': self.supported_languages,
            'config': self.context7_config,
            'mcp_available': MCP_AVAILABLE
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for analysis."""
        from datetime import datetime
        return datetime.now().isoformat()


# Example usage
async def main():
    """Example usage of Context7Analyzer."""
    analyzer = Context7Analyzer(enable_fallback=True)
    
    # Test with a Python file
    test_file = "src/orchestration/project_analyzer.py"
    if Path(test_file).exists():
        print(f"Analyzing {test_file} with Context7...")
        
        # Perform comprehensive analysis
        result = await analyzer.analyze_file(test_file, "python")
        
        print(f"\nContext7 Analysis Results:")
        print(f"  Success: {result.success}")
        print(f"  Language: {result.language}")
        print(f"  Confidence: {result.confidence_score:.2f}")
        print(f"  Insights: {len(result.insights)} items")
        print(f"  API Validations: {len(result.api_validations)} items")
        print(f"  Code Issues: {len(result.code_issues)} items")
        print(f"  Recommendations: {len(result.recommendations)} items")
        
        # Show status
        status = analyzer.get_context7_status()
        print(f"\nContext7 Status:")
        print(f"  Context7 Available: {status['context7_available']}")
        print(f"  Fallback Available: {status['fallback_available']}")
        print(f"  Supported Languages: {len(status['supported_languages'])}")
        
    else:
        print(f"Test file {test_file} not found")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())