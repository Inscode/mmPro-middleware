from diskcache import Cache
import os
from pathlib import Path  # Better path handling

# Simple cache initialization with smart fallbacks
def get_cache():
    # 1. Try configured directory first
    cache_dir = os.getenv('DISKCACHE_DIR', '/app/otp_cache')
    
    # 2. Try workspace directory in CI (like Jenkins)
    if not os.access(cache_dir, os.W_OK) and 'WORKSPACE' in os.environ:
        cache_dir = os.path.join(os.environ['WORKSPACE'], 'otp_cache')
    
    # 3. Final fallback to temp directory
    if not os.access(cache_dir, os.W_OK):
        cache_dir = '/tmp/otp_cache'
    
    # Ensure directory exists
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    
    return Cache(cache_dir)

# Single global cache instance
cache = get_cache()
