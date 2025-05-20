from diskcache import Cache
import os

cache_dir = os.getenv('DISKCACHE_DIR', '/app/otp_cache')

try:
    os.makedirs(cache_dir, exist_ok=True)
    # Try to set permissions, but don't fail if we can't
    try:
        os.chmod(cache_dir, 0o755)
    except PermissionError:
        pass  # Continue with default permissions
        
    cache = Cache(cache_dir)
except Exception as e:
    print(f"Error initializing cache: {e}")
    # Fallback to temporary directory if needed
    cache = Cache('/tmp/otp_cache')