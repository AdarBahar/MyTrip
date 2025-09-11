"""
Rate Limiting Utilities

Simple in-memory rate limiting for API endpoints.
"""

import time
from typing import Dict, Tuple
from collections import defaultdict, deque


class RateLimiter:
    """Simple sliding window rate limiter"""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
    
    def allow_request(self, key: str) -> bool:
        """Check if request is allowed for the given key"""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        request_times = self.requests[key]
        while request_times and request_times[0] < window_start:
            request_times.popleft()
        
        # Check if under limit
        if len(request_times) < self.max_requests:
            request_times.append(now)
            return True
        
        return False
    
    def get_remaining(self, key: str) -> int:
        """Get remaining requests for the key"""
        now = time.time()
        window_start = now - self.window_seconds
        
        request_times = self.requests[key]
        # Count requests in current window
        current_requests = sum(1 for t in request_times if t >= window_start)
        
        return max(0, self.max_requests - current_requests)
    
    def get_reset_time(self, key: str) -> int:
        """Get timestamp when the rate limit resets"""
        request_times = self.requests[key]
        if not request_times:
            return int(time.time())
        
        # Reset time is when the oldest request expires
        return int(request_times[0] + self.window_seconds)
