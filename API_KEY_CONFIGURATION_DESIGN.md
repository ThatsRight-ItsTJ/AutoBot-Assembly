# Flexible API Key Configuration System Design

## Executive Summary

This document provides a comprehensive design for a flexible API key configuration system for the AutoBot-Assembly project. The design enables:

1. **Z.ai/Bigmodel API Integration** - Adding a new AI provider option
2. **Per-Function API Keys** - Separate API keys for different components
3. **Backward Compatibility** - Existing functionality continues to work
4. **Security Best Practices** - Secure handling of sensitive credentials

## Current System Analysis

### Existing Architecture
- **Configuration Management**: `src/cli/config_manager.py` with `UserConfig` dataclass
- **Current Providers**: pollinations, openai, anthropic, google
- **Hardcoded Issues**: Pollinations API key hardcoded in `project_analyzer.py` and `ai_integrated_reporter.py`
- **Environment Support**: Environment variables override configuration file values
- **Provider Priority**: Configured provider → fallback to available keys

### Current Problems
1. **Hardcoded API Keys**: `self.pollinations_api_key = "D6ivBlSgXRsU1F7r"` in multiple files
2. **Single Key per Provider**: One key shared across all functions
3. **No Z.ai/Bigmodel Support**: Missing provider integration
4. **Limited Configuration**: No per-function key separation

## New Configuration Architecture

### 1. Enhanced UserConfig Structure

```python
@dataclass
class UserConfig:
    # Default settings (unchanged)
    default_output_dir: str = "./autobot_output"
    default_language: Optional[str] = None
    default_project_type: Optional[str] = None
    
    # Behavior settings (unchanged)
    verbose: bool = False
    skip_tests: bool = False
    skip_docs: bool = False
    auto_confirm: bool = False
    
    # Performance settings (unchanged)
    max_repos: int = 10
    timeout: int = 300
    concurrent_clones: int = 3
    
    # API Provider Settings
    api_provider: str = "pollinations"  # pollinations, openai, anthropic, google, zai
    
    # Global API Keys (for backward compatibility)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    pollinations_api_key: Optional[str] = None
    zai_api_key: Optional[str] = None  # New Z.ai/Bigmodel provider
    github_token: Optional[str] = None
    
    # New: Per-Function API Key Configuration
    function_api_keys: Dict[str, Dict[str, str]] = None
    
    # UI preferences (unchanged)
    use_rich: bool = True
    color_theme: str = "auto"
    show_progress: bool = True
    
    # History settings (unchanged)
    save_history: bool = True
    max_history_items: int = 50
    
    # Advanced settings (unchanged)
    enable_caching: bool = True
    cache_duration_hours: int = 24
    debug_mode: bool = False
```

### 2. Per-Function API Key Structure

```python
# Default function API key configuration
DEFAULT_FUNCTION_KEYS = {
    'project_analyzer': {
        'provider': 'pollinations',  # Default provider
        'api_key': None,  # Will use global key if not set
        'fallback_providers': ['openai', 'anthropic', 'google', 'zai'],
        'timeout': 30,
        'retry_count': 3
    },
    'ai_reporter': {
        'provider': 'pollinations',  # Can be different from analyzer
        'api_key': None,
        'fallback_providers': ['openai', 'anthropic', 'google', 'zai'],
        'timeout': 60,
        'retry_count': 2
    },
    'search_orchestrator': {
        'provider': 'pollinations',
        'api_key': None,
        'fallback_providers': ['openai', 'anthropic', 'google', 'zai'],
        'timeout': 45,
        'retry_count': 2
    }
}
```

### 3. Z.ai/Bigmodel Provider Integration

```python
# Z.ai/Bigmodel API Configuration
ZAI_CONFIG = {
    'name': 'Z.ai/Bigmodel',
    'base_url': 'https://open.bigmodel.cn/api/paas/v4',
    'models': {
        'glm-4': 'glm-4',
        'glm-4v': 'glm-4v',
        'glm-3-turbo': 'glm-3-turbo'
    },
    'endpoints': {
        'chat': '/chat/completions',
        'models': '/models'
    },
    'headers': {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
}
```

## Detailed Technical Specification

### 1. ConfigManager Enhancements

#### New Methods:
- `get_function_api_key(function_name: str, provider: str = None) -> Dict[str, Any]`
- `set_function_api_key(function_name: str, provider: str, api_key: str)`
- `get_function_config(function_name: str) -> Dict[str, Any]`
- `migrate_legacy_config()` - Handle backward compatibility

#### Enhanced Methods:
- `get_api_keys()` - Support per-function keys
- `get_preferred_api_provider()` - Consider function-specific preferences
- `get_api_status()` - Show per-function API status

### 2. AI Provider Interface

```python
class AIProvider:
    """Base interface for AI providers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.timeout = config.get('timeout', 30)
        self.retry_count = config.get('retry_count', 3)
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate AI response."""
        raise NotImplementedError
    
    def is_available(self) -> bool:
        """Check if provider is available."""
        raise NotImplementedError

class ZaiProvider(AIProvider):
    """Z.ai/Bigmodel API provider."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'https://open.bigmodel.cn/api/paas/v4')
        self.model = config.get('model', 'glm-4')
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using Z.ai API."""
        import aiohttp
        
        headers = {
            **ZAI_CONFIG['headers'],
            'Authorization': f'Bearer {self.api_key}'
        }
        
        payload = {
            'model': self.model,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': kwargs.get('temperature', 0.7),
            'max_tokens': kwargs.get('max_tokens', 2000)
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}{ZAI_CONFIG['endpoints']['chat']}",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['choices'][0]['message']['content']
                else:
                    raise Exception(f"Z.ai API error: {response.status}")
    
    def is_available(self) -> bool:
        """Check if Z.ai provider is available."""
        return bool(self.api_key)
```

### 3. Function-Specific API Key Resolution

```python
def resolve_api_key_for_function(self, function_name: str, provider: str = None) -> Dict[str, Any]:
    """
    Resolve API key for a specific function.
    
    Args:
        function_name: Name of the function (project_analyzer, ai_reporter, etc.)
        provider: Optional specific provider to use
        
    Returns:
        Dictionary with resolved configuration
    """
    # Get function-specific config
    function_config = self._get_function_config(function_name)
    
    # Determine provider to use
    if provider:
        target_provider = provider
    else:
        target_provider = function_config.get('provider') or self._config.api_provider
    
    # Check function-specific key first
    function_key = function_config.get(f'{target_provider}_api_key')
    
    if function_key:
        return {
            'provider': target_provider,
            'api_key': function_key,
            'timeout': function_config.get('timeout', 30),
            'retry_count': function_config.get('retry_count', 3)
        }
    
    # Fall back to global key
    global_key = getattr(self._config, f'{target_provider}_api_key', None)
    
    if global_key:
        return {
            'provider': target_provider,
            'api_key': global_key,
            'timeout': function_config.get('timeout', 30),
            'retry_count': function_config.get('retry_count', 3)
        }
    
    # No key available
    return {
        'provider': target_provider,
        'api_key': None,
        'timeout': function_config.get('timeout', 30),
        'retry_count': function_config.get('retry_count', 3)
    }
```

## Implementation Plan

### Phase 1: Core Configuration Changes

#### File: `src/cli/config_manager.py`
1. **Enhanced UserConfig**: Add `function_api_keys` field
2. **New Methods**: Add function-specific API key methods
3. **Enhanced get_api_keys()**: Support per-function resolution
4. **Migration Logic**: Add `migrate_legacy_config()` method

#### File: `src/orchestration/project_analyzer.py`
1. **Remove Hardcoded Key**: Remove `self.pollinations_api_key = "D6ivBlSgXRsU1F7r"`
2. **Add Config Integration**: Use ConfigManager for API key resolution
3. **Enhanced Provider Support**: Support multiple providers with fallback

#### File: `src/reporting/ai_integrated_reporter.py`
1. **Remove Hardcoded Key**: Remove hardcoded API key
2. **Add Config Integration**: Use ConfigManager for API key resolution
3. **Enhanced Provider Support**: Support multiple providers with fallback

### Phase 2: Z.ai/Bigmodel Integration

#### File: `src/api/zai_provider.py` (New)
1. **ZaiProvider Class**: Implement Z.ai API provider
2. **Authentication**: Handle Z.ai API authentication
3. **Error Handling**: Implement proper error handling
4. **Rate Limiting**: Implement rate limiting logic

#### File: `src/cli/config_manager.py`
1. **Add Z.ai Support**: Add `zai_api_key` field
2. **Provider Status**: Update `get_api_status()` to include Z.ai
3. **Provider Priority**: Update priority logic to include Z.ai

### Phase 3: Enhanced CLI Integration

#### File: `src/cli/autobot_cli.py`
1. **API Key Commands**: Add commands for managing per-function API keys
2. **Provider Selection**: Add provider selection for specific functions
3. **Status Display**: Enhanced API status display

## Backward Compatibility Strategy

### 1. Configuration Migration
```python
def migrate_legacy_config(self):
    """Migrate legacy configuration to new format."""
    
    # Initialize function_api_keys if not present
    if not self._config.function_api_keys:
        self._config.function_api_keys = DEFAULT_FUNCTION_KEYS.copy()
        
        # Migrate existing global keys to function defaults
        for function_name, function_config in self._config.function_api_keys.items():
            provider = function_config.get('provider')
            if provider and hasattr(self._config, f'{provider}_api_key'):
                api_key = getattr(self._config, f'{provider}_api_key')
                if api_key:
                    function_config[f'{provider}_api_key'] = api_key
    
    # Set default Z.ai provider if not configured
    if not hasattr(self._config, 'zai_api_key'):
        self._config.zai_api_key = None
    
    # Save migrated configuration
    self.save_config(self._config)
```

### 2. API Key Resolution Fallback
```python
def get_api_keys(self) -> Dict[str, Optional[str]]:
    """Get API keys with backward compatibility."""
    
    # Priority: Function-specific keys > Global keys > Environment variables
    api_keys = {}
    
    # First, get global keys (existing behavior)
    global_keys = {
        'openai_api_key': (
            self._config.openai_api_key or 
            os.getenv('OPENAI_API_KEY')
        ),
        'anthropic_api_key': (
            self._config.anthropic_api_key or 
            os.getenv('ANTHROPIC_API_KEY')
        ),
        'google_api_key': (
            self._config.google_api_key or 
            os.getenv('GOOGLE_API_KEY')
        ),
        'pollinations_api_key': (
            self._config.pollinations_api_key or 
            os.getenv('POLLINATIONS_API_KEY')
        ),
        'zai_api_key': (
            self._config.zai_api_key or 
            os.getenv('ZAI_API_KEY')
        ),
        'github_token': (
            self._config.github_token or 
            os.getenv('GITHUB_TOKEN')
        )
    }
    
    # If function-specific keys are configured, use them
    if self._config.function_api_keys:
        for function_name, function_config in self._config.function_api_keys.items():
            for provider in ['pollinations', 'openai', 'anthropic', 'google', 'zai']:
                key_name = f'{provider}_api_key'
                if key_name in function_config:
                    # Function-specific key takes precedence
                    api_keys[f'{function_name}_{key_name}'] = function_config[key_name]
        
        # Also include global keys as fallback
        api_keys.update(global_keys)
    else:
        # No function-specific keys, use global keys
        api_keys.update(global_keys)
    
    return api_keys
```

## Security Considerations

### 1. API Key Storage
- **Configuration File**: API keys stored in `~/.autobot/config.json` with encryption option
- **Environment Variables**: Support for environment variable overrides
- **Memory Management**: API keys cleared from memory after use when possible
- **Access Control**: File permissions restricted to user only

### 2. Secure Transmission
- **HTTPS**: All API calls use HTTPS
- **Header Security**: No API keys in URL parameters
- **Rate Limiting**: Implement rate limiting to prevent abuse
- **Input Validation**: Validate all API inputs

### 3. Audit and Monitoring
- **Usage Logging**: Log API key usage without storing sensitive data
- **Error Handling**: Secure error messages that don't expose keys
- **Access Tracking**: Track which functions use which providers

## Configuration Examples

### 1. Basic Configuration (Backward Compatible)
```json
{
  "api_provider": "pollinations",
  "pollinations_api_key": "your-pollinations-key",
  "openai_api_key": "your-openai-key",
  "function_api_keys": {
    "project_analyzer": {
      "provider": "pollinations",
      "fallback_providers": ["openai", "anthropic"]
    },
    "ai_reporter": {
      "provider": "openai",
      "fallback_providers": ["anthropic", "google"]
    }
  }
}
```

### 2. Advanced Per-Function Configuration
```json
{
  "api_provider": "zai",
  "zai_api_key": "your-zai-key",
  "function_api_keys": {
    "project_analyzer": {
      "provider": "zai",
      "zai_api_key": "analyzer-specific-zai-key",
      "timeout": 45,
      "retry_count": 3,
      "fallback_providers": ["openai", "anthropic"]
    },
    "ai_reporter": {
      "provider": "openai",
      "openai_api_key": "reporter-specific-openai-key",
      "timeout": 60,
      "retry_count": 2,
      "fallback_providers": ["anthropic", "google"]
    },
    "search_orchestrator": {
      "provider": "pollinations",
      "timeout": 30,
      "retry_count": 2,
      "fallback_providers": ["google", "zai"]
    }
  }
}
```

### 3. Environment Variable Configuration
```bash
# Global API keys
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export ZAI_API_KEY="your-zai-key"

# Function-specific API keys
export PROJECT_ANALYZER_ZAI_API_KEY="analyzer-specific-zai-key"
export AI_REPORTER_OPENAI_API_KEY="reporter-specific-openai-key"
```

## Migration Guide

### Step 1: Backup Existing Configuration
```bash
cp ~/.autobot/config.json ~/.autobot/config.json.backup
```

### Step 2: Update Configuration
The system will automatically migrate existing configuration to the new format. The migration will:
1. Preserve existing global API keys
2. Initialize function-specific configurations with default values
3. Set existing global keys as defaults for all functions
4. Add Z.ai provider support

### Step 3: Test Migration
```bash
python -m src.cli.config_manager --validate
```

### Step 4: Update Environment Variables (Optional)
If using environment variables, ensure they follow the new naming convention:
- `OPENAI_API_KEY` → remains the same
- `PROJECT_ANALYZER_OPENAI_API_KEY` → function-specific key

## Testing Strategy

### 1. Unit Tests
- Test configuration loading and saving
- Test API key resolution logic
- Test provider availability checking
- Test migration logic

### 2. Integration Tests
- Test per-function API key usage
- Test provider fallback mechanisms
- Test Z.ai API integration
- Test backward compatibility

### 3. End-to-End Tests
- Test complete workflows with different configurations
- Test error handling and edge cases
- Test performance with different providers

## Performance Considerations

### 1. Caching
- Cache API key resolution results
- Cache provider availability checks
- Cache configuration data

### 2. Async Operations
- All API calls should be asynchronous
- Implement proper connection pooling
- Handle timeouts and retries properly

### 3. Memory Management
- Clear sensitive data from memory when possible
- Use efficient data structures for configuration
- Implement lazy loading of configuration data

## Conclusion

This flexible API key configuration system provides a comprehensive solution for managing multiple AI providers with per-function API key support. The design maintains backward compatibility while enabling advanced configuration options for different use cases.

The implementation plan provides a clear roadmap for phased development, ensuring that the system can be deployed incrementally with minimal disruption to existing functionality.

The security considerations and best practices ensure that sensitive API keys are handled securely throughout the system.

The configuration examples and migration guide provide clear guidance for users transitioning to the new system.