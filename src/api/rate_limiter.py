"""
Rate Limiter

Request throttling and quota management for AutoBot API.
"""

import time
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque
import json
from pathlib import Path


@dataclass
class RateLimit:
    """Rate limit configuration."""
    
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10  # Max requests in burst
    burst_window: int = 60  # Burst window in seconds


@dataclass
class ClientStats:
    """Client request statistics."""
    
    client_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    blocked_requests: int = 0
    first_request: Optional[float] = None
    last_request: Optional[float] = None
    current_minute_requests: int = 0
    current_hour_requests: int = 0
    current_day_requests: int = 0


class RateLimiter:
    """Advanced rate limiting with multiple time windows and burst protection."""
    
    def __init__(self, default_limits: Optional[RateLimit] = None):
        self.logger = logging.getLogger(__name__)
        
        # Default rate limits
        self.default_limits = default_limits or RateLimit()
        
        # Client-specific limits
        self.client_limits: Dict[str, RateLimit] = {}
        
        # Request tracking
        self.client_stats: Dict[str, ClientStats] = {}
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Time windows for cleanup
        self.minute_requests: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.hour_requests: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.day_requests: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        
        # Blocked clients (temporary bans)
        self.blocked_clients: Dict[str, float] = {}  # client_id -> unblock_time
        
        # Background cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background cleanup task."""
        
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(60)  # Cleanup every minute
                    await self._cleanup_old_requests()
                except Exception as e:
                    self.logger.error(f"Cleanup task error: {e}")
        
        self._cleanup_task = asyncio.create_task(cleanup_loop())
    
    async def _cleanup_old_requests(self):
        """Clean up old request records."""
        
        current_time = time.time()
        
        # Clean up minute windows (keep last 1 minute)
        minute_cutoff = current_time - 60
        for client_id, requests in self.minute_requests.items():
            while requests and requests[0] < minute_cutoff:
                requests.popleft()
        
        # Clean up hour windows (keep last 1 hour)
        hour_cutoff = current_time - 3600
        for client_id, requests in self.hour_requests.items():
            while requests and requests[0] < hour_cutoff:
                requests.popleft()
        
        # Clean up day windows (keep last 24 hours)
        day_cutoff = current_time - 86400
        for client_id, requests in self.day_requests.items():
            while requests and requests[0] < day_cutoff:
                requests.popleft()
        
        # Remove expired blocks
        expired_blocks = [
            client_id for client_id, unblock_time in self.blocked_clients.items()
            if current_time > unblock_time
        ]
        for client_id in expired_blocks:
            del self.blocked_clients[client_id]
            self.logger.info(f"Unblocked client: {client_id}")
    
    def set_client_limits(self, client_id: str, limits: RateLimit):
        """Set custom rate limits for a specific client."""
        
        self.client_limits[client_id] = limits
        self.logger.info(f"Set custom limits for client {client_id}")
    
    def get_client_limits(self, client_id: str) -> RateLimit:
        """Get rate limits for a client."""
        
        return self.client_limits.get(client_id, self.default_limits)
    
    async def check_rate_limit(self, client_id: str, endpoint: str = "default") -> bool:
        """
        Check if a request should be allowed based on rate limits.
        
        Args:
            client_id: Unique identifier for the client (IP, API key, etc.)
            endpoint: API endpoint being accessed
            
        Returns:
            True if request is allowed, False if rate limited
        """
        
        current_time = time.time()
        
        # Check if client is temporarily blocked
        if client_id in self.blocked_clients:
            if current_time < self.blocked_clients[client_id]:
                await self._record_blocked_request(client_id)
                return False
            else:
                # Block expired, remove it
                del self.blocked_clients[client_id]
        
        # Get client limits
        limits = self.get_client_limits(client_id)
        
        # Initialize client stats if needed
        if client_id not in self.client_stats:
            self.client_stats[client_id] = ClientStats(
                client_id=client_id,
                first_request=current_time
            )
        
        stats = self.client_stats[client_id]
        
        # Check burst limit (requests in last burst_window seconds)
        burst_cutoff = current_time - limits.burst_window
        recent_requests = [
            req_time for req_time in self.request_history[client_id]
            if req_time > burst_cutoff
        ]
        
        if len(recent_requests) >= limits.burst_limit:
            await self._record_blocked_request(client_id)
            # Temporary block for burst violation (5 minutes)
            self.blocked_clients[client_id] = current_time + 300
            self.logger.warning(f"Client {client_id} blocked for burst limit violation")
            return False
        
        # Check minute limit
        minute_requests = len(self.minute_requests[client_id])
        if minute_requests >= limits.requests_per_minute:
            await self._record_blocked_request(client_id)
            return False
        
        # Check hour limit
        hour_requests = len(self.hour_requests[client_id])
        if hour_requests >= limits.requests_per_hour:
            await self._record_blocked_request(client_id)
            return False
        
        # Check day limit
        day_requests = len(self.day_requests[client_id])
        if day_requests >= limits.requests_per_day:
            await self._record_blocked_request(client_id)
            # Longer block for daily limit (1 hour)
            self.blocked_clients[client_id] = current_time + 3600
            self.logger.warning(f"Client {client_id} blocked for daily limit violation")
            return False
        
        # Request is allowed, record it
        await self._record_allowed_request(client_id, current_time)
        return True
    
    async def _record_allowed_request(self, client_id: str, request_time: float):
        """Record an allowed request."""
        
        # Add to time windows
        self.minute_requests[client_id].append(request_time)
        self.hour_requests[client_id].append(request_time)
        self.day_requests[client_id].append(request_time)
        self.request_history[client_id].append(request_time)
        
        # Update stats
        stats = self.client_stats[client_id]
        stats.total_requests += 1
        stats.successful_requests += 1
        stats.last_request = request_time
    
    async def _record_blocked_request(self, client_id: str):
        """Record a blocked request."""
        
        if client_id in self.client_stats:
            stats = self.client_stats[client_id]
            stats.total_requests += 1
            stats.blocked_requests += 1
            stats.last_request = time.time()
    
    async def record_failed_request(self, client_id: str):
        """Record a failed request (for statistics)."""
        
        if client_id in self.client_stats:
            self.client_stats[client_id].failed_requests += 1
    
    def get_client_stats(self, client_id: str) -> Optional[ClientStats]:
        """Get statistics for a specific client."""
        
        return self.client_stats.get(client_id)
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get overall rate limiting statistics."""
        
        total_clients = len(self.client_stats)
        total_requests = sum(stats.total_requests for stats in self.client_stats.values())
        total_blocked = sum(stats.blocked_requests for stats in self.client_stats.values())
        total_failed = sum(stats.failed_requests for stats in self.client_stats.values())
        
        return {
            'total_clients': total_clients,
            'total_requests': total_requests,
            'total_blocked': total_blocked,
            'total_failed': total_failed,
            'blocked_clients': len(self.blocked_clients),
            'success_rate': (total_requests - total_blocked - total_failed) / max(total_requests, 1)
        }
    
    def get_rate_limit_info(self, client_id: str) -> Dict[str, Any]:
        """Get current rate limit status for a client."""
        
        current_time = time.time()
        limits = self.get_client_limits(client_id)
        
        # Count current usage
        minute_usage = len(self.minute_requests[client_id])
        hour_usage = len(self.hour_requests[client_id])
        day_usage = len(self.day_requests[client_id])
        
        # Calculate reset times
        minute_reset = 60 - (current_time % 60)
        hour_reset = 3600 - (current_time % 3600)
        day_reset = 86400 - (current_time % 86400)
        
        # Check if blocked
        is_blocked = client_id in self.blocked_clients
        block_expires = self.blocked_clients.get(client_id, 0)
        
        return {
            'client_id': client_id,
            'limits': {
                'requests_per_minute': limits.requests_per_minute,
                'requests_per_hour': limits.requests_per_hour,
                'requests_per_day': limits.requests_per_day,
                'burst_limit': limits.burst_limit
            },
            'usage': {
                'minute': minute_usage,
                'hour': hour_usage,
                'day': day_usage
            },
            'remaining': {
                'minute': max(0, limits.requests_per_minute - minute_usage),
                'hour': max(0, limits.requests_per_hour - hour_usage),
                'day': max(0, limits.requests_per_day - day_usage)
            },
            'reset_times': {
                'minute': minute_reset,
                'hour': hour_reset,
                'day': day_reset
            },
            'is_blocked': is_blocked,
            'block_expires': block_expires if is_blocked else None
        }
    
    def block_client(self, client_id: str, duration_seconds: int):
        """Manually block a client for a specified duration."""
        
        block_until = time.time() + duration_seconds
        self.blocked_clients[client_id] = block_until
        
        self.logger.warning(f"Manually blocked client {client_id} for {duration_seconds} seconds")
    
    def unblock_client(self, client_id: str):
        """Manually unblock a client."""
        
        if client_id in self.blocked_clients:
            del self.blocked_clients[client_id]
            self.logger.info(f"Manually unblocked client {client_id}")
    
    def reset_client_limits(self, client_id: str):
        """Reset rate limit counters for a client."""
        
        # Clear all request records
        if client_id in self.minute_requests:
            self.minute_requests[client_id].clear()
        if client_id in self.hour_requests:
            self.hour_requests[client_id].clear()
        if client_id in self.day_requests:
            self.day_requests[client_id].clear()
        if client_id in self.request_history:
            self.request_history[client_id].clear()
        
        # Unblock if blocked
        self.unblock_client(client_id)
        
        self.logger.info(f"Reset rate limits for client {client_id}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive rate limiting statistics."""
        
        return {
            'overall': self.get_all_stats(),
            'active_clients': len(self.client_stats),
            'blocked_clients': len(self.blocked_clients),
            'default_limits': {
                'requests_per_minute': self.default_limits.requests_per_minute,
                'requests_per_hour': self.default_limits.requests_per_hour,
                'requests_per_day': self.default_limits.requests_per_day,
                'burst_limit': self.default_limits.burst_limit
            }
        }
    
    def export_stats(self, filepath: str):
        """Export statistics to a JSON file."""
        
        stats_data = {
            'timestamp': time.time(),
            'overall_stats': self.get_all_stats(),
            'client_stats': {
                client_id: {
                    'total_requests': stats.total_requests,
                    'successful_requests': stats.successful_requests,
                    'failed_requests': stats.failed_requests,
                    'blocked_requests': stats.blocked_requests,
                    'first_request': stats.first_request,
                    'last_request': stats.last_request
                }
                for client_id, stats in self.client_stats.items()
            },
            'blocked_clients': self.blocked_clients
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(stats_data, f, indent=2)
            
            self.logger.info(f"Exported rate limiting stats to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to export stats: {e}")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()


# Example usage and testing
async def test_rate_limiter():
    """Test the rate limiter."""
    
    # Create rate limiter with low limits for testing
    limits = RateLimit(
        requests_per_minute=5,
        requests_per_hour=20,
        requests_per_day=100,
        burst_limit=3,
        burst_window=10
    )
    
    rate_limiter = RateLimiter(limits)
    
    client_id = "test_client"
    
    print("Testing rate limiter...")
    
    # Test normal requests
    for i in range(10):
        allowed = await rate_limiter.check_rate_limit(client_id)
        print(f"Request {i+1}: {'Allowed' if allowed else 'Blocked'}")
        
        if i == 2:  # Check status after a few requests
            info = rate_limiter.get_rate_limit_info(client_id)
            print(f"Rate limit info: {info}")
        
        await asyncio.sleep(0.1)
    
    # Get final stats
    stats = await rate_limiter.get_stats()
    print(f"\nFinal stats: {stats}")


if __name__ == "__main__":
    asyncio.run(test_rate_limiter())