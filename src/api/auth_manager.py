"""
Authentication Manager

API key and token management for AutoBot API server.
"""

import hashlib
import secrets
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import json
import os


@dataclass
class APIKey:
    """API key information."""
    
    key_id: str
    key_hash: str
    name: str
    created_at: float
    last_used: Optional[float] = None
    usage_count: int = 0
    rate_limit: int = 100  # requests per hour
    is_active: bool = True
    permissions: List[str] = None
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = ['generate', 'status', 'download']


class AuthManager:
    """Manages API authentication and authorization."""
    
    def __init__(self, keys_file: str = "./api_keys.json"):
        self.logger = logging.getLogger(__name__)
        self.keys_file = Path(keys_file)
        self.api_keys: Dict[str, APIKey] = {}
        
        # Load existing keys
        self._load_api_keys()
        
        # Create default key if none exist
        if not self.api_keys:
            self._create_default_key()
    
    def _load_api_keys(self):
        """Load API keys from file."""
        
        if not self.keys_file.exists():
            return
        
        try:
            with open(self.keys_file, 'r') as f:
                keys_data = json.load(f)
            
            for key_id, key_data in keys_data.items():
                self.api_keys[key_id] = APIKey(**key_data)
            
            self.logger.info(f"Loaded {len(self.api_keys)} API keys")
            
        except Exception as e:
            self.logger.error(f"Failed to load API keys: {e}")
    
    def _save_api_keys(self):
        """Save API keys to file."""
        
        try:
            keys_data = {}
            for key_id, api_key in self.api_keys.items():
                keys_data[key_id] = {
                    'key_id': api_key.key_id,
                    'key_hash': api_key.key_hash,
                    'name': api_key.name,
                    'created_at': api_key.created_at,
                    'last_used': api_key.last_used,
                    'usage_count': api_key.usage_count,
                    'rate_limit': api_key.rate_limit,
                    'is_active': api_key.is_active,
                    'permissions': api_key.permissions
                }
            
            with open(self.keys_file, 'w') as f:
                json.dump(keys_data, f, indent=2)
            
            self.logger.info("API keys saved successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to save API keys: {e}")
    
    def _create_default_key(self):
        """Create a default API key."""
        
        key = self.create_api_key("default", permissions=['generate', 'status', 'download', 'admin'])
        self.logger.info(f"Created default API key: {key}")
    
    def _hash_key(self, key: str) -> str:
        """Hash an API key."""
        return hashlib.sha256(key.encode()).hexdigest()
    
    def create_api_key(self, name: str, rate_limit: int = 100, permissions: List[str] = None) -> str:
        """Create a new API key."""
        
        # Generate random key
        raw_key = secrets.token_urlsafe(32)
        key_id = secrets.token_hex(8)
        key_hash = self._hash_key(raw_key)
        
        # Create API key object
        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            created_at=time.time(),
            rate_limit=rate_limit,
            permissions=permissions or ['generate', 'status', 'download']
        )
        
        # Store key
        self.api_keys[key_id] = api_key
        self._save_api_keys()
        
        self.logger.info(f"Created API key '{name}' with ID {key_id}")
        
        # Return the raw key (only time it's available)
        return f"autobot_{key_id}_{raw_key}"
    
    async def verify_token(self, token: str) -> Optional[APIKey]:
        """Verify an API token and return the associated key."""
        
        if not token or not token.startswith('autobot_'):
            return None
        
        try:
            # Parse token format: autobot_{key_id}_{raw_key}
            parts = token.split('_', 2)
            if len(parts) != 3:
                return None
            
            key_id = parts[1]
            raw_key = parts[2]
            
            # Find API key
            if key_id not in self.api_keys:
                return None
            
            api_key = self.api_keys[key_id]
            
            # Verify key is active
            if not api_key.is_active:
                return None
            
            # Verify hash
            if api_key.key_hash != self._hash_key(raw_key):
                return None
            
            # Update usage
            api_key.last_used = time.time()
            api_key.usage_count += 1
            self._save_api_keys()
            
            return api_key
            
        except Exception as e:
            self.logger.error(f"Token verification failed: {e}")
            return None
    
    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        
        if key_id not in self.api_keys:
            return False
        
        self.api_keys[key_id].is_active = False
        self._save_api_keys()
        
        self.logger.info(f"Revoked API key {key_id}")
        return True
    
    def list_api_keys(self) -> List[Dict[str, Any]]:
        """List all API keys (without sensitive data)."""
        
        keys_info = []
        for api_key in self.api_keys.values():
            keys_info.append({
                'key_id': api_key.key_id,
                'name': api_key.name,
                'created_at': api_key.created_at,
                'last_used': api_key.last_used,
                'usage_count': api_key.usage_count,
                'rate_limit': api_key.rate_limit,
                'is_active': api_key.is_active,
                'permissions': api_key.permissions
            })
        
        return keys_info
    
    def get_key_usage_stats(self, key_id: str) -> Optional[Dict[str, Any]]:
        """Get usage statistics for a specific key."""
        
        if key_id not in self.api_keys:
            return None
        
        api_key = self.api_keys[key_id]
        
        return {
            'key_id': key_id,
            'name': api_key.name,
            'usage_count': api_key.usage_count,
            'last_used': api_key.last_used,
            'rate_limit': api_key.rate_limit,
            'is_active': api_key.is_active
        }
    
    def check_permission(self, api_key: APIKey, permission: str) -> bool:
        """Check if an API key has a specific permission."""
        
        return permission in api_key.permissions or 'admin' in api_key.permissions
    
    def update_key_permissions(self, key_id: str, permissions: List[str]) -> bool:
        """Update permissions for an API key."""
        
        if key_id not in self.api_keys:
            return False
        
        self.api_keys[key_id].permissions = permissions
        self._save_api_keys()
        
        self.logger.info(f"Updated permissions for key {key_id}")
        return True
    
    def cleanup_inactive_keys(self, inactive_days: int = 90) -> int:
        """Remove API keys that haven't been used for a specified number of days."""
        
        cutoff_time = time.time() - (inactive_days * 24 * 3600)
        removed_count = 0
        
        keys_to_remove = []
        for key_id, api_key in self.api_keys.items():
            if (api_key.last_used and api_key.last_used < cutoff_time) or \
               (not api_key.last_used and api_key.created_at < cutoff_time):
                keys_to_remove.append(key_id)
        
        for key_id in keys_to_remove:
            if self.api_keys[key_id].name != 'default':  # Don't remove default key
                del self.api_keys[key_id]
                removed_count += 1
        
        if removed_count > 0:
            self._save_api_keys()
            self.logger.info(f"Cleaned up {removed_count} inactive API keys")
        
        return removed_count


# Example usage
def main():
    """Test the authentication manager."""
    
    auth_manager = AuthManager("test_api_keys.json")
    
    # Create test keys
    key1 = auth_manager.create_api_key("test_key_1", rate_limit=50)
    key2 = auth_manager.create_api_key("test_key_2", permissions=['generate', 'status'])
    
    print(f"Created keys:")
    print(f"Key 1: {key1}")
    print(f"Key 2: {key2}")
    
    # List keys
    print("\nAPI Keys:")
    for key_info in auth_manager.list_api_keys():
        print(f"  {key_info['name']} ({key_info['key_id']}): {key_info['permissions']}")
    
    # Test verification
    import asyncio
    
    async def test_verification():
        result = await auth_manager.verify_token(key1)
        print(f"\nVerification result: {result.name if result else 'Failed'}")
    
    asyncio.run(test_verification())


if __name__ == "__main__":
    main()