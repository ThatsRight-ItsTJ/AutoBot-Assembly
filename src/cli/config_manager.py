"""
Configuration Manager

User settings and preferences management for AutoBot CLI.
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import logging


@dataclass
class UserConfig:
    """User configuration settings."""
    
    # Default settings
    default_output_dir: str = "./autobot_output"
    default_language: Optional[str] = None
    default_project_type: Optional[str] = None
    
    # Behavior settings
    verbose: bool = False
    skip_tests: bool = False
    skip_docs: bool = False
    auto_confirm: bool = False
    
    # Performance settings
    max_repos: int = 10
    timeout: int = 300
    concurrent_clones: int = 3
    
    # API settings - Support for multiple providers
    api_provider: str = "pollinations"  # pollinations, openai, anthropic, google, zai
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    pollinations_api_key: Optional[str] = None  # Optional, free tier available
    zai_api_key: Optional[str] = None  # Z.ai/Bigmodel provider
    github_token: Optional[str] = None
    
    # New: Per-Function API Key Configuration
    function_api_keys: Optional[Dict[str, Dict[str, Any]]] = None
    
    # UI preferences
    use_rich: bool = True
    color_theme: str = "auto"  # auto, dark, light
    show_progress: bool = True
    
    # History settings
    save_history: bool = True
    max_history_items: int = 50
    
    # Advanced settings
    enable_caching: bool = True
    cache_duration_hours: int = 24
    debug_mode: bool = False


class ConfigManager:
    """Manages user configuration and settings."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Configuration paths
        self.config_dir = Path.home() / ".autobot"
        self.config_file = self.config_dir / "config.json"
        self.history_file = self.config_dir / "history.json"
        self.cache_dir = self.config_dir / "cache"
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Load configuration
        self._config = self.load_config()
    
    def load_config(self) -> UserConfig:
        """Load user configuration from file."""
        
        if not self.config_file.exists():
            # Create default configuration
            config = UserConfig()
            self.save_config(config)
            return config
        
        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
            
            # Create UserConfig from loaded data
            config = UserConfig(**config_data)
            return config
            
        except Exception as e:
            self.logger.warning(f"Failed to load config: {e}. Using defaults.")
            return UserConfig()
    
    def save_config(self, config: UserConfig):
        """Save user configuration to file."""
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(asdict(config), f, indent=2)
            
            self._config = config
            self.logger.info("Configuration saved successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
    
    def get_config(self) -> UserConfig:
        """Get current configuration."""
        return self._config
    
    def update_config(self, **kwargs):
        """Update configuration with new values."""
        
        config_dict = asdict(self._config)
        config_dict.update(kwargs)
        
        try:
            new_config = UserConfig(**config_dict)
            self.save_config(new_config)
            return True
        except Exception as e:
            self.logger.error(f"Failed to update config: {e}")
            return False
    
    def reset_config(self):
        """Reset configuration to defaults."""
        
        default_config = UserConfig()
        self.save_config(default_config)
        return default_config
    
    def get_api_keys(self) -> Dict[str, Optional[str]]:
        """Get API keys from configuration and environment variables."""
        
        # Priority: User config > Environment variables
        api_keys = {
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
        
        return api_keys
    
    def get_preferred_api_provider(self, function_name: str = None) -> str:
        """Get the preferred API provider based on configuration and available keys."""
        
        api_keys = self.get_api_keys()
        preferred = self._config.api_provider.lower()
        
        # If function-specific config is requested, check function preferences first
        if function_name and self._config.function_api_keys:
            function_config = self._config.function_api_keys.get(function_name, {})
            function_provider = function_config.get('provider')
            if function_provider:
                preferred = function_provider.lower()
        
        # Check if preferred provider has API key (except Pollinations which is free)
        if preferred == "pollinations":
            return "pollinations"
        elif preferred == "openai" and api_keys['openai_api_key']:
            return "openai"
        elif preferred == "anthropic" and api_keys['anthropic_api_key']:
            return "anthropic"
        elif preferred == "google" and api_keys['google_api_key']:
            return "google"
        elif preferred == "zai" and api_keys['zai_api_key']:
            return "zai"
        
        # Fallback logic: use any available API key
        if api_keys['openai_api_key']:
            return "openai"
        elif api_keys['anthropic_api_key']:
            return "anthropic"
        elif api_keys['google_api_key']:
            return "google"
        elif api_keys['zai_api_key']:
            return "zai"
        else:
            # Default to Pollinations (free)
            return "pollinations"
    
    def set_api_key(self, provider: str, api_key: str):
        """Set API key for a specific provider."""
        
        provider = provider.lower()
        
        if provider == 'openai':
            self.update_config(openai_api_key=api_key)
        elif provider == 'anthropic':
            self.update_config(anthropic_api_key=api_key)
        elif provider == 'google':
            self.update_config(google_api_key=api_key)
        elif provider == 'pollinations':
            self.update_config(pollinations_api_key=api_key)
        elif provider == 'zai':
            self.update_config(zai_api_key=api_key)
        elif provider == 'github':
            self.update_config(github_token=api_key)
        else:
            self.logger.warning(f"Unknown API provider: {provider}")
    
    def set_api_provider(self, provider: str):
        """Set preferred API provider."""
        
        valid_providers = ['pollinations', 'openai', 'anthropic', 'google', 'zai']
        provider = provider.lower()
        
        if provider in valid_providers:
            self.update_config(api_provider=provider)
            self.logger.info(f"API provider set to: {provider}")
        else:
            self.logger.error(f"Invalid API provider: {provider}. Valid options: {valid_providers}")
    
    def get_api_status(self, function_name: str = None) -> Dict[str, Dict[str, Any]]:
        """Get status of all API providers."""
        
        api_keys = self.get_api_keys()
        status = {}
        
        providers = {
            'pollinations': {
                'name': 'Pollinations AI',
                'free_tier': True,
                'requires_key': False
            },
            'openai': {
                'name': 'OpenAI GPT',
                'free_tier': False,
                'requires_key': True
            },
            'anthropic': {
                'name': 'Anthropic Claude',
                'free_tier': False,
                'requires_key': True
            },
            'google': {
                'name': 'Google Gemini',
                'free_tier': True,
                'requires_key': True
            },
            'zai': {
                'name': 'Z.ai/Bigmodel',
                'free_tier': False,
                'requires_key': True
            }
        }
        
        for provider_id, provider_info in providers.items():
            key_name = f"{provider_id}_api_key"
            has_key = bool(api_keys.get(key_name))
            
            if provider_id == 'pollinations':
                # Pollinations is always available (free tier)
                available = True
                status_msg = "Available (Free Tier)"
            else:
                available = has_key
                if has_key:
                    status_msg = "Available"
                else:
                    status_msg = "API Key Required"
            
            status[provider_id] = {
                'name': provider_info['name'],
                'available': available,
                'has_key': has_key,
                'free_tier': provider_info['free_tier'],
                'requires_key': provider_info['requires_key'],
                'status': status_msg
            }
        
        # Add function-specific status if requested
        if function_name:
            function_config = self.get_function_config(function_name)
            status['function_config'] = {
                'function_name': function_name,
                'preferred_provider': function_config.get('provider', self._config.api_provider),
                'fallback_providers': function_config.get('fallback_providers', []),
                'timeout': function_config.get('timeout', 30),
                'retry_count': function_config.get('retry_count', 3)
            }
        
        return status
    
    def get_function_api_key(self, function_name: str, provider: str = None) -> Dict[str, Any]:
        """
        Get API key configuration for a specific function.
        
        Args:
            function_name: Name of the function (project_analyzer, ai_reporter, etc.)
            provider: Optional specific provider to use
            
        Returns:
            Dictionary with resolved configuration
        """
        # Initialize function_api_keys if not present
        if not self._config.function_api_keys:
            self._config.function_api_keys = self._get_default_function_keys()
            self.save_config(self._config)
        
        # Get function-specific config
        function_config = self._config.function_api_keys.get(function_name, {})
        
        # Determine provider to use
        if provider:
            target_provider = provider
        else:
            target_provider = function_config.get('provider') or self._config.api_provider
        
        # Priority order for API key resolution:
        # 1. Function-specific API key
        # 2. Global API key
        # 3. Environment variable for function-specific key
        # 4. Environment variable for global key
        # 5. Environment variable for any available API key (fallback)
        
        # Check function-specific key first
        function_key = function_config.get(f'{target_provider}_api_key')
        
        if function_key:
            self.logger.debug(f"Found function-specific API key for {target_provider} in {function_name}")
            return {
                'provider': target_provider,
                'api_key': function_key,
                'timeout': function_config.get('timeout', 30),
                'retry_count': function_config.get('retry_count', 3)
            }
        
        # Fall back to global key
        global_key = getattr(self._config, f'{target_provider}_api_key', None)
        
        if global_key:
            self.logger.debug(f"Found global API key for {target_provider}")
            return {
                'provider': target_provider,
                'api_key': global_key,
                'timeout': function_config.get('timeout', 30),
                'retry_count': function_config.get('retry_count', 3)
            }
        
        # Check environment variables in priority order
        env_var_names = [
            f'{function_name.upper()}_{target_provider.upper()}_API_KEY',  # Function-specific
            f'{target_provider.upper()}_API_KEY',  # Global
            f'{target_provider.upper()}_KEY'  # Alternative naming
        ]
        
        for env_var in env_var_names:
            env_key = os.getenv(env_var)
            if env_key:
                self.logger.debug(f"Found API key in environment variable: {env_var}")
                return {
                    'provider': target_provider,
                    'api_key': env_key,
                    'timeout': function_config.get('timeout', 30),
                    'retry_count': function_config.get('retry_count', 3)
                }
        
        # Final fallback: check for any available API key
        api_keys = self.get_api_keys()
        for provider_name, key_value in api_keys.items():
            if key_value and provider_name != 'github_token':
                self.logger.debug(f"Found fallback API key for {provider_name}")
                return {
                    'provider': provider_name.replace('_api_key', ''),
                    'api_key': key_value,
                    'timeout': function_config.get('timeout', 30),
                    'retry_count': function_config.get('retry_count', 3)
                }
        
        # No key available - Pollinations doesn't require a key for free tier
        if target_provider == 'pollinations':
            self.logger.debug("Using Pollinations (no API key required for free tier)")
            return {
                'provider': target_provider,
                'api_key': None,
                'timeout': function_config.get('timeout', 30),
                'retry_count': function_config.get('retry_count', 3)
            }
        
        self.logger.warning(f"No API key available for {target_provider}")
        return {
            'provider': target_provider,
            'api_key': None,
            'timeout': function_config.get('timeout', 30),
            'retry_count': function_config.get('retry_count', 3)
        }
    
    def set_function_api_key(self, function_name: str, provider: str, api_key: str):
        """Set API key for a specific function."""
        
        # Initialize function_api_keys if not present
        if not self._config.function_api_keys:
            self._config.function_api_keys = self._get_default_function_keys()
        
        # Ensure function exists in config
        if function_name not in self._config.function_api_keys:
            self._config.function_api_keys[function_name] = self._get_default_function_config()
        
        # Set the function-specific API key
        self._config.function_api_keys[function_name][f'{provider}_api_key'] = api_key
        self.save_config(self._config)
        self.logger.info(f"Set {provider} API key for {function_name}")
    
    def get_function_config(self, function_name: str) -> Dict[str, Any]:
        """Get configuration for a specific function."""
        
        # Initialize function_api_keys if not present
        if not self._config.function_api_keys:
            self._config.function_api_keys = self._get_default_function_keys()
            self.save_config(self._config)
        
        return self._config.function_api_keys.get(function_name, self._get_default_function_config())
    
    def _get_default_function_keys(self) -> Dict[str, Dict[str, Any]]:
        """Get default function API key configuration."""
        return {
            'project_analyzer': self._get_default_function_config(),
            'ai_reporter': self._get_default_function_config(),
            'search_orchestrator': self._get_default_function_config()
        }
    
    def _get_default_function_config(self) -> Dict[str, Any]:
        """Get default configuration for a function."""
        return {
            'provider': self._config.api_provider,
            'fallback_providers': ['openai', 'anthropic', 'google', 'zai'],
            'timeout': 30,
            'retry_count': 3
        }
    
    def migrate_legacy_config(self):
        """Migrate legacy configuration to new format."""
        
        # Initialize function_api_keys if not present
        if not self._config.function_api_keys:
            self._config.function_api_keys = self._get_default_function_keys()
            
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
        self.logger.info("Configuration migrated to new format")
    
    def add_to_history(self, entry: Dict[str, Any]):
        """Add entry to command history."""
        
        if not self._config.save_history:
            return
        
        try:
            # Load existing history
            history = self.load_history()
            
            # Add new entry with timestamp
            import time
            entry['timestamp'] = time.time()
            history.append(entry)
            
            # Limit history size
            if len(history) > self._config.max_history_items:
                history = history[-self._config.max_history_items:]
            
            # Save updated history
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save history: {e}")
    
    def load_history(self) -> List[Dict[str, Any]]:
        """Load command history."""
        
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load history: {e}")
            return []
    
    def clear_history(self):
        """Clear command history."""
        
        try:
            if self.history_file.exists():
                self.history_file.unlink()
            self.logger.info("History cleared")
        except Exception as e:
            self.logger.error(f"Failed to clear history: {e}")
    
    def get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for a given key."""
        
        # Create safe filename from cache key
        safe_key = "".join(c for c in cache_key if c.isalnum() or c in ('-', '_')).rstrip()
        return self.cache_dir / f"{safe_key}.json"
    
    def get_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached data if it exists and is not expired."""
        
        if not self._config.enable_caching:
            return None
        
        cache_file = self.get_cache_path(cache_key)
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            
            # Check if cache is expired
            import time
            cache_time = cached_data.get('timestamp', 0)
            max_age = self._config.cache_duration_hours * 3600
            
            if time.time() - cache_time > max_age:
                # Cache expired, remove it
                cache_file.unlink()
                return None
            
            return cached_data.get('data')
            
        except Exception as e:
            self.logger.error(f"Failed to load cache {cache_key}: {e}")
            return None
    
    def set_cached_data(self, cache_key: str, data: Dict[str, Any]):
        """Cache data with timestamp."""
        
        if not self._config.enable_caching:
            return
        
        cache_file = self.get_cache_path(cache_key)
        
        try:
            import time
            cached_data = {
                'timestamp': time.time(),
                'data': data
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cached_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to cache data {cache_key}: {e}")
    
    def clear_cache(self):
        """Clear all cached data."""
        
        try:
            import shutil
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(exist_ok=True)
            self.logger.info("Cache cleared")
        except Exception as e:
            self.logger.error(f"Failed to clear cache: {e}")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration."""
        
        config_dict = asdict(self._config)
        
        # Hide sensitive information
        if config_dict.get('openai_api_key'):
            config_dict['openai_api_key'] = '***hidden***'
        if config_dict.get('anthropic_api_key'):
            config_dict['anthropic_api_key'] = '***hidden***'
        if config_dict.get('google_api_key'):
            config_dict['google_api_key'] = '***hidden***'
        if config_dict.get('pollinations_api_key'):
            config_dict['pollinations_api_key'] = '***hidden***'
        if config_dict.get('zai_api_key'):
            config_dict['zai_api_key'] = '***hidden***'
        if config_dict.get('github_token'):
            config_dict['github_token'] = '***hidden***'
        
        return config_dict
    
    def export_config(self, export_path: str):
        """Export configuration to a file."""
        
        try:
            config_dict = asdict(self._config)
            
            # Remove sensitive data from export
            config_dict.pop('openai_api_key', None)
            config_dict.pop('anthropic_api_key', None)
            config_dict.pop('google_api_key', None)
            config_dict.pop('pollinations_api_key', None)
            config_dict.pop('zai_api_key', None)
            config_dict.pop('github_token', None)
            
            with open(export_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            self.logger.info(f"Configuration exported to {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export config: {e}")
            return False
    
    def import_config(self, import_path: str):
        """Import configuration from a file."""
        
        try:
            with open(import_path, 'r') as f:
                config_data = json.load(f)
            
            # Merge with current config (preserve API keys)
            current_config = asdict(self._config)
            current_config.update(config_data)
            
            new_config = UserConfig(**current_config)
            self.save_config(new_config)
            
            self.logger.info(f"Configuration imported from {import_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import config: {e}")
            return False
    
    def validate_config(self) -> List[str]:
        """Validate current configuration and return any issues."""
        
        issues = []
        
        # Check required directories
        if not Path(self._config.default_output_dir).parent.exists():
            issues.append(f"Output directory parent does not exist: {self._config.default_output_dir}")
        
        # Check numeric values
        if self._config.max_repos <= 0:
            issues.append("max_repos must be greater than 0")
        
        if self._config.timeout <= 0:
            issues.append("timeout must be greater than 0")
        
        if self._config.concurrent_clones <= 0:
            issues.append("concurrent_clones must be greater than 0")
        
        # Check API keys (warn if missing)
        api_keys = self.get_api_keys()
        if not api_keys['github_token']:
            issues.append("GitHub token not configured (may hit rate limits)")
        
        return issues


# Example usage and testing
def main():
    """Test the configuration manager."""
    
    config_manager = ConfigManager()
    
    # Print current configuration
    print("Current Configuration:")
    config = config_manager.get_config()
    for key, value in asdict(config).items():
        if 'token' in key or 'key' in key:
            value = '***hidden***' if value else None
        print(f"  {key}: {value}")
    
    # Test API status
    print("\nAPI Status:")
    api_status = config_manager.get_api_status()
    for provider, status in api_status.items():
        available = "✅" if status['available'] else "❌"
        print(f"  {provider}: {available} {status['status']}")
    
    # Test validation
    print("\nValidation Issues:")
    issues = config_manager.validate_config()
    if issues:
        for issue in issues:
            print(f"  ⚠️ {issue}")
    else:
        print("  ✅ No issues found")
    
    # Test history
    print("\nAdding test history entry...")
    config_manager.add_to_history({
        'prompt': 'Create a web scraper',
        'output_dir': './test_project',
        'success': True
    })
    
    history = config_manager.load_history()
    print(f"History entries: {len(history)}")


if __name__ == "__main__":
    main()