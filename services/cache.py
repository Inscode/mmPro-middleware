from diskcache import Cache
import os
from pathlib import Path

def get_cache():
    # Try possible cache locations in order of preference
    for cache_dir in [
        os.getenv('DISKCACHE_DIR'),               # 1. Custom configured directory
        str(Path(os.getenv('WORKSPACE', '.')) / '.cache',  # 2. Jenkins workspace
        '/tmp/your_app_cache'                     # 3. System temp directory
    ]:
        if not cache_dir:
            continue
            
        try:
            path = Path(cache_dir)
            path.mkdir(parents=True, exist_ok=True)
            
            # Test write permissions
            test_file = path / '.permission_test'
            test_file.touch()
            test_file.unlink()
            
            return Cache(str(path))
            
        except (OSError, PermissionError) as e:
            continue
    
    # Final fallback that should always work
    return Cache('/tmp/fallback_cache')

# Initialize cache instance
cache = get_cache()
