from diskcache import Cache
import os
from pathlib import Path
from tempfile import gettempdir

def get_cache():
    # Priority order for cache directories
    possible_dirs = [
        os.getenv('OTP_CACHE_DIR'),  # 1. Jenkins-specific
        os.getenv('CACHE_DIR'),      # 2. General cache dir
        os.path.join(gettempdir(), 'otp_cache'),            # 3. System temp
        str(Path.home() / '.cache/otp')  # 4. User cache
    ]
    
    for cache_dir in possible_dirs:
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
        except OSError:
            continue
    
    # Final fallback that should always work
    return Cache(':memory:')

cache = get_cache()
