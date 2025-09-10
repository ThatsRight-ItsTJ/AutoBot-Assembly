"""
Project Analyzer with Tree-sitter Integration

AI-powered project analysis engine that interprets user requirements
and generates comprehensive project specifications enhanced with Tree-sitter
structural analysis via UniversalCodeAnalyzer.
"""

import asyncio
import json
import logging
import os
from dataclasses import asdict, dataclass
from enum import Enum
from typing import List, Dict, Optional, Any

# Import AI providers
try:
    import aiohttp
except ImportError:
    aiohttp = None

# Import ConfigManager
try:
    from src.cli.config_manager import ConfigManager
except ImportError:
    ConfigManager = None

# Import UniversalCodeAnalyzer for Tree-sitter integration
try:
    from src.analysis.universal_code_analyzer import UniversalCodeAnalyzer
    UNIVERSAL_ANALYZER_AVAILABLE = True
except ImportError:
    UNIVERSAL_ANALYZER_AVAILABLE = False
    UniversalCodeAnalyzer = None

# Import Context7 integration
try:
    from src.analysis.context7_integration import Context7Analyzer, Context7AnalysisResult
    CONTEXT7_AVAILABLE = True
except ImportError:
    CONTEXT7_AVAILABLE = False
    Context7Analyzer = None
    Context7AnalysisResult = None


class ProjectType(Enum):
    """Types of projects that can be analyzed."""
    WEB_APPLICATION = "web_application"
    API_SERVICE = "api_service"
    DATA_PIPELINE = "data_pipeline"
    MOBILE_APP = "mobile_app"
    DESKTOP_APP = "desktop_app"
    MACHINE_LEARNING = "machine_learning"
    AUTOMATION_SCRIPT = "automation_script"
    LIBRARY = "library"


@dataclass
class ProjectAnalysis:
    """Result of project analysis."""
    name: str
    description: str
    project_type: ProjectType
    language: str
    components: List[str]
    dependencies: List[str]
    confidence: float
    estimated_complexity: str
    recommended_architecture: str


class ProjectAnalyzer:
    """AI-powered project analysis engine with Tree-sitter structural analysis."""
    
    def __init__(self, config_manager=None, enable_tree_sitter: bool = True, enable_context7: bool = True):
        self.logger = logging.getLogger(__name__)
        
        # Initialize configuration manager with error handling
        if config_manager:
            self.config_manager = config_manager
        elif ConfigManager:
            try:
                self.config_manager = ConfigManager()
                self.logger.info("ConfigManager initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize ConfigManager: {e}")
                self.config_manager = None
        else:
            self.logger.warning("ConfigManager not available, using fallback behavior")
            self.config_manager = None
        
        # Initialize Tree-sitter analyzer if enabled and available
        self.enable_tree_sitter = enable_tree_sitter and UNIVERSAL_ANALYZER_AVAILABLE
        self.tree_sitter_analyzer = None
        if self.enable_tree_sitter:
            try:
                self.tree_sitter_analyzer = UniversalCodeAnalyzer()
                self.logger.info("UniversalCodeAnalyzer initialized for Tree-sitter structural analysis")
            except Exception as e:
                self.logger.warning(f"Failed to initialize UniversalCodeAnalyzer: {e}")
                self.tree_sitter_analyzer = None
                self.enable_tree_sitter = False
        
        # Initialize Context7 analyzer if enabled and available
        self.enable_context7 = enable_context7 and CONTEXT7_AVAILABLE
        self.context7_analyzer = None
        if self.enable_context7:
            try:
                self.context7_analyzer = Context7Analyzer(enable_fallback=True)
                self.logger.info("Context7Analyzer initialized for enhanced code analysis")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Context7Analyzer: {e}")
                self.context7_analyzer = None
                self.enable_context7 = False
        
        # Initialize AI provider configurations
        self.ai_providers = {}
        self._initialize_providers()
        
        # Function name for API key resolution
        self.function_name = 'project_analyzer'
        
        # Context7 analysis configuration
        self.context7_analysis_types = ['structure', 'api', 'security', 'performance']
        
        # Project analysis patterns
        self.analysis_patterns = {
            'web_scraping': {
                'type': ProjectType.WEB_APPLICATION,
                'language': 'python',
                'components': ['web_scraper', 'data_parser', 'storage', 'scheduler'],
                'dependencies': ['requests', 'beautifulsoup4', 'scrapy', 'selenium']
            },
            'news_aggregator': {
                'type': ProjectType.WEB_APPLICATION,
                'language': 'python',
                'components': ['rss_parser', 'sentiment_analysis', 'web_dashboard', 'database'],
                'dependencies': ['feedparser', 'fastapi', 'pandas', 'nltk']
            },
            'api_service': {
                'type': ProjectType.API_SERVICE,
                'language': 'python',
                'components': ['api_endpoints', 'authentication', 'database', 'documentation'],
                'dependencies': ['fastapi', 'uvicorn', 'pydantic', 'sqlalchemy']
            },
            'data_analysis': {
                'type': ProjectType.DATA_PIPELINE,
                'language': 'python',
                'components': ['data_ingestion', 'processing', 'visualization', 'reporting'],
                'dependencies': ['pandas', 'numpy', 'matplotlib', 'jupyter']
            }
        }
    
    def _initialize_providers(self):
        """Initialize AI provider configurations."""
        
        # Initialize Pollinations provider (always available)
        if aiohttp is not None:
            self.ai_providers['pollinations'] = {
                'url': 'https://text.pollinations.ai/',
                'available': True,
                'api_key': None  # Pollinations doesn't require API key for free tier
            }
        
        # If ConfigManager is not available, only use Pollinations
        if not self.config_manager:
            self.logger.warning("ConfigManager not available, only Pollinations AI will be available")
            return
        
        try:
            # Get global API keys for other providers
            api_keys = self.config_manager.get_api_keys()
            
            # Initialize OpenAI provider
            if api_keys.get('openai_api_key'):
                self.ai_providers['openai'] = {
                    'url': 'https://api.openai.com/v1/chat/completions',
                    'available': True,
                    'api_key': api_keys['openai_api_key']
                }
            
            # Initialize Anthropic provider
            if api_keys.get('anthropic_api_key'):
                self.ai_providers['anthropic'] = {
                    'url': 'https://api.anthropic.com/v1/messages',
                    'available': True,
                    'api_key': api_keys['anthropic_api_key']
                }
            
            # Initialize Google provider
            if api_keys.get('google_api_key'):
                self.ai_providers['google'] = {
                    'url': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent',
                    'available': True,
                    'api_key': api_keys['google_api_key']
                }
            
            # Initialize Z.ai provider
            if api_keys.get('zai_api_key'):
                self.ai_providers['zai'] = {
                    'url': 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
                    'available': True,
                    'api_key': api_keys['zai_api_key']
                }
        except Exception as e:
            self.logger.error(f"Failed to initialize AI providers: {e}")
    
    async def analyze_project_prompt(self, prompt: str, provider: str = None,
                                   source_files: Optional[List[str]] = None) -> ProjectAnalysis:
        """
        Analyze a project prompt and generate comprehensive project specifications.
        
        Args:
            prompt: User's project description/requirements
            provider: AI provider to use for analysis (None for function's preferred provider)
            source_files: Optional list of source files for Tree-sitter structural analysis
            
        Returns:
            ProjectAnalysis: Comprehensive analysis of the project requirements
        """
        self.logger.info(f"Analyzing project prompt: {prompt[:100]}...")
        
        # Try AI analysis first
        ai_analysis = await self._get_ai_analysis(prompt, provider)
        
        if ai_analysis:
            # Enhance AI analysis with Tree-sitter structural data if source files provided
            if source_files and self.enable_tree_sitter:
                enhanced_analysis = await self._enhance_with_structural_analysis(ai_analysis, source_files)
                return enhanced_analysis
            
            # Enhance with Context7 insights if available
            if source_files and self.enable_context7:
                context7_analysis = await self._enhance_with_context7_analysis(ai_analysis, source_files)
                if context7_analysis:
                    return context7_analysis
            
            return ai_analysis
        
        # Fallback to pattern-based analysis with optional Tree-sitter and Context7 enhancement
        pattern_analysis = self._pattern_based_analysis(prompt)
        
        if source_files and self.enable_tree_sitter:
            enhanced_analysis = await self._enhance_with_structural_analysis(pattern_analysis, source_files)
            pattern_analysis = enhanced_analysis
        
        if source_files and self.enable_context7:
            context7_analysis = await self._enhance_with_context7_analysis(pattern_analysis, source_files)
            if context7_analysis:
                pattern_analysis = context7_analysis
        
        return pattern_analysis
    
    async def _enhance_with_structural_analysis(self, analysis: ProjectAnalysis,
                                             source_files: List[str]) -> ProjectAnalysis:
        """
        Enhance project analysis with Tree-sitter structural data from source files.
        
        Args:
            analysis: Existing project analysis
            source_files: List of source files to analyze
            
        Returns:
            Enhanced ProjectAnalysis with structural metrics
        """
        try:
            # Analyze source files for structural information
            structural_metrics = await self._analyze_source_files_structure(source_files)
            
            # Enhance components with structural insights
            if structural_metrics['complexity_score'] > 0.7:
                analysis.estimated_complexity = 'high'
            elif structural_metrics['complexity_score'] > 0.4:
                analysis.estimated_complexity = 'medium'
            else:
                analysis.estimated_complexity = 'low'
            
            # Add structural insights to components
            enhanced_components = analysis.components.copy()
            
            if structural_metrics['classes_count'] > 10:
                enhanced_components.append('large_class_architecture')
            elif structural_metrics['classes_count'] > 5:
                enhanced_components.append('modular_class_structure')
            
            if structural_metrics['functions_count'] > 20:
                enhanced_components.append('function_decomposition_needed')
            elif structural_metrics['functions_count'] > 10:
                enhanced_components.append('modular_function_structure')
            
            if structural_metrics.get('has_tests', False):
                enhanced_components.append('test_suite_present')
            else:
                enhanced_components.append('test_suite_required')
            
            if structural_metrics.get('has_docs', False):
                enhanced_components.append('documentation_present')
            else:
                enhanced_components.append('documentation_required')
            
            # Update analysis with enhanced components
            analysis.components = enhanced_components
            
            # Adjust confidence based on structural analysis quality
            analysis.confidence = min(0.95, analysis.confidence + 0.1)
            
            self.logger.info(f"Enhanced analysis with structural metrics: {structural_metrics}")
            
            return analysis
            
        except Exception as e:
            self.logger.warning(f"Failed to enhance analysis with structural data: {e}")
            return analysis
    
    async def _enhance_with_context7_analysis(self, analysis: ProjectAnalysis,
                                            source_files: List[str]) -> Optional[ProjectAnalysis]:
        """
        Enhance project analysis with Context7 insights and API validation.
        
        Args:
            analysis: Existing project analysis
            source_files: List of source files for Context7 analysis
            
        Returns:
            Enhanced ProjectAnalysis with Context7 insights, or None if analysis fails
        """
        if not self.context7_analyzer:
            return None
        
        try:
            self.logger.info("Enhancing analysis with Context7 insights...")
            
            # Perform Context7 analysis on source files
            context7_results = []
            total_confidence_boost = 0.0
            context7_insights = []
            api_validations = []
            code_issues = []
            
            for file_path in source_files[:5]:  # Limit to first 5 files for performance
                try:
                    # Skip non-existent files
                    if not os.path.exists(file_path):
                        continue
                    
                    # Analyze file with Context7
                    result = await self.context7_analyzer.analyze_file(
                        file_path,
                        self._detect_language(file_path),
                        self.context7_analysis_types
                    )
                    
                    if result and result.success:
                        context7_results.append(result)
                        total_confidence_boost += result.confidence_score
                        
                        # Collect insights
                        if result.insights:
                            context7_insights.extend(
                                f"{file_path}: {key} = {value}"
                                for key, value in result.insights.items()
                            )
                        
                        # Collect API validations
                        api_validations.extend(result.api_validations)
                        
                        # Collect code issues
                        code_issues.extend(result.code_issues)
                        
                except Exception as e:
                    self.logger.warning(f"Context7 analysis failed for {file_path}: {e}")
                    continue
            
            # Enhance analysis with Context7 insights
            if context7_results:
                # Boost confidence based on Context7 analysis quality
                avg_confidence_boost = total_confidence_boost / len(context7_results)
                analysis.confidence = min(0.98, analysis.confidence + (avg_confidence_boost * 0.1))
                
                # Add Context7 insights to components
                enhanced_components = analysis.components.copy()
                
                # Add components based on API validations
                if api_validations:
                    enhanced_components.append('api_validation_performed')
                    if any(v.validation_status == 'warning' for v in api_validations):
                        enhanced_components.append('api_security_review_needed')
                
                # Add components based on code issues
                if code_issues:
                    issue_types = set(issue['type'] for issue in code_issues)
                    if 'high_complexity' in issue_types:
                        enhanced_components.append('complexity_refactoring_needed')
                    if 'missing_tests' in issue_types:
                        enhanced_components.append('test_implementation_required')
                
                # Add Context7-specific insights
                if context7_insights:
                    enhanced_components.append('context7_analysis_performed')
                    
                    # Check for performance insights
                    performance_insights = [
                        insight for insight in context7_insights
                        if 'performance' in insight.lower() or 'complexity' in insight.lower()
                    ]
                    if performance_insights:
                        enhanced_components.append('performance_optimization_opportunities')
                
                analysis.components = enhanced_components
                
                # Update estimated complexity based on Context7 analysis
                complexity_scores = [
                    result.insights.get('complexity_score', 0.5)
                    for result in context7_results
                    if result.insights
                ]
                
                if complexity_scores:
                    avg_complexity = sum(complexity_scores) / len(complexity_scores)
                    if avg_complexity > 0.7:
                        analysis.estimated_complexity = 'high'
                    elif avg_complexity > 0.4:
                        analysis.estimated_complexity = 'medium'
                    else:
                        analysis.estimated_complexity = 'low'
                
                self.logger.info(f"Enhanced analysis with {len(context7_results)} Context7 results")
                
                return analysis
            
        except Exception as e:
            self.logger.warning(f"Failed to enhance analysis with Context7 data: {e}")
        
        return None
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file path."""
        extension = os.path.splitext(file_path)[1].lower().lstrip('.')
        
        language_map = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'java': 'java',
            'go': 'go',
            'rs': 'rust',
            'php': 'php',
            'rb': 'ruby',
            'c': 'c',
            'cpp': 'cpp',
            'cs': 'csharp',
            'swift': 'swift',
            'kt': 'kotlin'
        }
        
        return language_map.get(extension, 'python')  # Default to Python
    
    async def _analyze_source_files_structure(self, source_files: List[str]) -> Dict[str, Any]:
        """
        Analyze source files structure using Tree-sitter.
        
        Args:
            source_files: List of source file paths
            
        Returns:
            Dictionary containing structural metrics
        """
        if not self.tree_sitter_analyzer:
            return {}
        
        structural_metrics = {
            'complexity_score': 0.0,
            'classes_count': 0,
            'functions_count': 0,
            'has_tests': False,
            'has_docs': False,
            'average_file_size': 0,
            'total_files_analyzed': 0
        }
        
        total_files = 0
        total_complexity = 0.0
        total_classes = 0
        total_functions = 0
        
        try:
            for file_path in source_files:
                try:
                    # Skip non-existent files
                    if not os.path.exists(file_path):
                        continue
                    
                    # Analyze file with Tree-sitter
                    file_result = self.tree_sitter_analyzer.analyze_file(file_path)
                    
                    if file_result and file_result.get('success'):
                        total_files += 1
                        
                        # Extract metrics
                        metrics = file_result.get('metrics', {})
                        structure = file_result.get('structure', {})
                        
                        total_complexity += float(metrics.get('complexity_score', 0.0))
                        total_classes += int(metrics.get('classes_count', 0))
                        total_functions += int(metrics.get('functions_count', 0))
                        
                        # Check for tests and documentation
                        if structure.get('has_tests', False):
                            structural_metrics['has_tests'] = True
                        if structure.get('has_docs', False):
                            structural_metrics['has_docs'] = True
                        
                except Exception as e:
                    self.logger.warning(f"Error analyzing {file_path}: {e}")
                    continue
            
            # Calculate averages
            if total_files > 0:
                structural_metrics['complexity_score'] = total_complexity / total_files
                structural_metrics['classes_count'] = total_classes
                structural_metrics['functions_count'] = total_functions
                structural_metrics['total_files_analyzed'] = total_files
            
        except Exception as e:
            self.logger.error(f"Error in structural analysis: {e}")
        
        return structural_metrics
    
    async def _get_ai_analysis(self, prompt: str, provider: str = None) -> Optional[ProjectAnalysis]:
        """Get AI-powered project analysis."""
        
        # If ConfigManager is not available, use Pollinations as fallback
        if not self.config_manager:
            self.logger.warning("ConfigManager not available, using Pollinations fallback")
            if 'pollinations' in self.ai_providers and self.ai_providers['pollinations']['available']:
                timeout = aiohttp.ClientTimeout(total=15)
                return await self._call_ai_provider('pollinations', prompt, timeout)
            return None
        
        try:
            # Get function API configuration
            api_config = self.config_manager.get_function_api_key(self.function_name, provider)
            timeout = aiohttp.ClientTimeout(total=api_config.get('timeout', 15))
            
            # Use resolved provider from config
            resolved_provider = api_config['provider']
            
            # Try function-specific providers first
            if resolved_provider in self.ai_providers and self.ai_providers[resolved_provider]['available']:
                return await self._call_ai_provider(resolved_provider, prompt, timeout)
            
            # Try fallback providers
            fallback_providers = ['openai', 'anthropic', 'google', 'zai', 'pollinations']
            for fallback_provider in fallback_providers:
                if fallback_provider in self.ai_providers and self.ai_providers[fallback_provider]['available']:
                    return await self._call_ai_provider(fallback_provider, prompt, timeout)
            
            # No available providers
            self.logger.warning(f"No available AI providers for project analysis")
            return None
        except Exception as e:
            self.logger.error(f"Error getting AI analysis: {e}")
            # Try Pollinations as final fallback
            if 'pollinations' in self.ai_providers and self.ai_providers['pollinations']['available']:
                timeout = aiohttp.ClientTimeout(total=15)
                return await self._call_ai_provider('pollinations', prompt, timeout)
            return None
    
    async def _call_ai_provider(self, provider: str, prompt: str, timeout: aiohttp.ClientTimeout) -> Optional[ProjectAnalysis]:
        """Call a specific AI provider."""
        
        provider_config = self.ai_providers[provider]
        url = provider_config['url']
        api_key = provider_config['api_key']
        
        try:
            # Simplified prompt for better AI response
            analysis_prompt = f"Analyze this project: {prompt}. Respond with project name, type (web_application/api_service/data_pipeline), language (python/javascript), 4 key components, and 4 main dependencies."
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'AutoBot-Assembly/1.0'
            }
            
            # Add authorization header if needed
            if provider != 'pollinations' and api_key:
                headers['Authorization'] = f"Bearer {api_key}"
            
            # Prepare payload based on provider
            if provider == 'pollinations':
                payload = {
                    'messages': [
                        {
                            'role': 'user',
                            'content': f"You are a software architect. Analyze this project requirement: {analysis_prompt}"
                        }
                    ],
                    'model': 'gpt-4'
                }
            else:
                payload = {
                    'messages': [
                        {
                            'role': 'user',
                            'content': f"You are a software architect. Analyze this project requirement: {analysis_prompt}"
                        }
                    ],
                    'model': 'gpt-4' if provider == 'openai' else 'claude-3-sonnet-20240229' if provider == 'anthropic' else 'gemini-pro'
                }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=timeout) as response:
                    if response.status == 200:
                        result = await response.text()
                        self.logger.info(f"AI analysis successful with {provider}: {len(result)} characters")
                        return self._parse_ai_response(result, prompt)
                    else:
                        response_text = await response.text()
                        self.logger.warning(f"{provider} API returned status {response.status}: {response_text}")
        
        except Exception as e:
            self.logger.warning(f"AI analysis failed with {provider}: {e}")
        
        return None
    
    def _parse_ai_response(self, ai_response: str, original_prompt: str) -> ProjectAnalysis:
        """Parse AI response into ProjectAnalysis object."""
        
        try:
            # Try to extract meaningful information from any response format
            response_lower = ai_response.lower()
            
            # Extract project name from response or generate from prompt
            project_name = self._generate_project_name(original_prompt)
            
            # Determine project type from response or prompt
            project_type = ProjectType.WEB_APPLICATION
            if 'api' in response_lower or 'api' in original_prompt.lower():
                project_type = ProjectType.API_SERVICE
            elif 'data' in response_lower or 'analysis' in response_lower:
                project_type = ProjectType.DATA_PIPELINE
            
            # Use pattern-based components as fallback with AI enhancement
            pattern_analysis = self._pattern_based_analysis(original_prompt)
            
            return ProjectAnalysis(
                name=project_name,
                description=original_prompt,
                project_type=project_type,
                language='python',  # Default to Python
                components=pattern_analysis.components,
                dependencies=pattern_analysis.dependencies,
                confidence=0.85,  # Higher confidence for AI-assisted analysis
                estimated_complexity='medium',
                recommended_architecture='layered'
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to parse AI response: {e}")
        
        # Fallback to pattern-based analysis if parsing fails
        return self._pattern_based_analysis(original_prompt)
    
    def _pattern_based_analysis(self, prompt: str) -> ProjectAnalysis:
        """Analyze project using pattern matching as fallback."""
        
        prompt_lower = prompt.lower()
        
        # Determine project pattern
        selected_pattern = None
        for pattern_name, pattern_config in self.analysis_patterns.items():
            if any(keyword in prompt_lower for keyword in pattern_name.split('_')):
                selected_pattern = pattern_config
                break
        
        # Default to web application if no pattern matches
        if not selected_pattern:
            selected_pattern = self.analysis_patterns['api_service']
        
        # Generate project name from prompt
        project_name = self._generate_project_name(prompt)
        
        return ProjectAnalysis(
            name=project_name,
            description=prompt,
            project_type=selected_pattern['type'],
            language=selected_pattern['language'],
            components=selected_pattern['components'].copy(),
            dependencies=selected_pattern['dependencies'].copy(),
            confidence=0.75,  # Medium confidence for pattern-based analysis
            estimated_complexity='medium',
            recommended_architecture='layered'
        )
    
    def _generate_project_name(self, prompt: str) -> str:
        """Generate a project name from the prompt."""
        
        # Extract key words from prompt
        words = prompt.lower().split()
        
        # Filter out common words
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'create', 'build', 'make', 'develop'}
        key_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Take first 2-3 meaningful words and capitalize
        if len(key_words) >= 2:
            name_parts = key_words[:3]
        else:
            name_parts = key_words[:1] + ['System']
        
        # Capitalize and join
        project_name = ''.join(word.capitalize() for word in name_parts)
        
        return project_name if project_name else 'AutoGeneratedProject'
    
    async def get_analysis_summary(self, analysis: ProjectAnalysis) -> Dict[str, Any]:
        """Generate a summary of the project analysis."""
        
        summary = {
            'project_name': analysis.name,
            'project_type': analysis.project_type.value,
            'primary_language': analysis.language,
            'component_count': len(analysis.components),
            'dependency_count': len(analysis.dependencies),
            'confidence_score': analysis.confidence,
            'complexity_level': analysis.estimated_complexity,
            'architecture_pattern': analysis.recommended_architecture,
            'top_components': analysis.components[:5],
            'key_dependencies': analysis.dependencies[:5]
        }
        
        # Add Tree-sitter analysis information if available
        if self.enable_tree_sitter:
            summary['tree_sitter_enabled'] = True
            summary['structural_analysis_available'] = self.tree_sitter_analyzer is not None
            summary['supported_languages'] = self.tree_sitter_analyzer.get_supported_languages() if self.tree_sitter_analyzer else []
        else:
            summary['tree_sitter_enabled'] = False
            summary['structural_analysis_available'] = False
        
        # Add Context7 analysis information if available
        if self.enable_context7:
            summary['context7_enabled'] = True
            summary['context7_analysis_available'] = self.context7_analyzer is not None
            if self.context7_analyzer:
                context7_status = self.context7_analyzer.get_context7_status()
                summary['context7_status'] = context7_status
                summary['supported_languages'] = context7_status.get('supported_languages', [])
        else:
            summary['context7_enabled'] = False
            summary['context7_analysis_available'] = False
        
        return summary
    
    def get_tree_sitter_status(self) -> Dict[str, Any]:
        """Get status of Tree-sitter integration."""
        return {
            'enabled': self.enable_tree_sitter,
            'analyzer_available': self.tree_sitter_analyzer is not None,
            'supported_languages': self.tree_sitter_analyzer.get_supported_languages() if self.tree_sitter_analyzer else [],
            'cache_info': self.tree_sitter_analyzer.get_cache_info() if self.tree_sitter_analyzer else None
        }
    
    def get_context7_status(self) -> Dict[str, Any]:
        """Get status of Context7 integration."""
        if not self.context7_analyzer:
            return {
                'enabled': self.enable_context7,
                'analyzer_available': False,
                'context7_available': False,
                'fallback_available': False,
                'supported_languages': [],
                'config': {}
            }
        
        return self.context7_analyzer.get_context7_status()
    
    async def validate_project_apis(self, source_files: List[str]) -> List[Dict[str, Any]]:
        """
        Validate API endpoints and patterns across the project using Context7.
        
        Args:
            source_files: List of source files to validate
            
        Returns:
            List of API validation results
        """
        if not self.context7_analyzer:
            return []
        
        try:
            self.logger.info("Validating project APIs with Context7...")
            
            api_validations = []
            validated_files = 0
            
            for file_path in source_files[:10]:  # Limit to first 10 files for performance
                try:
                    if not os.path.exists(file_path):
                        continue
                    
                    language = self._detect_language(file_path)
                    file_validations = await self.context7_analyzer.validate_apis(file_path, language)
                    
                    api_validations.extend([
                        {
                            'file': file_path,
                            'language': language,
                            'validation': asdict(validation) if hasattr(validation, '__dict__') else validation
                        }
                        for validation in file_validations
                    ])
                    
                    validated_files += 1
                    
                except Exception as e:
                    self.logger.warning(f"API validation failed for {file_path}: {e}")
                    continue
            
            self.logger.info(f"API validation completed for {validated_files} files")
            return api_validations
            
        except Exception as e:
            self.logger.error(f"Project API validation failed: {e}")
            return []
    
    async def real_time_project_analysis(self, source_files: List[str]) -> Dict[str, Any]:
        """
        Perform real-time analysis of the project using Context7.
        
        Args:
            source_files: List of source files to analyze
            
        Returns:
            Dictionary containing real-time analysis results
        """
        if not self.context7_analyzer:
            return {'error': 'Context7 analyzer not available'}
        
        try:
            self.logger.info("Performing real-time project analysis...")
            
            analysis_results = []
            analyzed_files = 0
            
            for file_path in source_files[:5]:  # Limit to first 5 files for performance
                try:
                    if not os.path.exists(file_path):
                        continue
                    
                    language = self._detect_language(file_path)
                    result = await self.context7_analyzer.real_time_analysis(file_path, language)
                    
                    if result and result.success:
                        analysis_results.append({
                            'file': file_path,
                            'language': language,
                            'insights': result.insights,
                            'api_validations': [
                                asdict(validation) if hasattr(validation, '__dict__') else validation
                                for validation in result.api_validations
                            ],
                            'code_issues': result.code_issues,
                            'recommendations': result.recommendations,
                            'confidence': result.confidence_score
                        })
                    
                    analyzed_files += 1
                    
                except Exception as e:
                    self.logger.warning(f"Real-time analysis failed for {file_path}: {e}")
                    continue
            
            return {
                'success': True,
                'analyzed_files': analyzed_files,
                'total_files': len(source_files),
                'analysis_results': analysis_results,
                'timestamp': self.context7_analyzer._get_timestamp() if hasattr(self.context7_analyzer, '_get_timestamp') else None
            }
            
        except Exception as e:
            self.logger.error(f"Real-time project analysis failed: {e}")
            return {'error': str(e)}