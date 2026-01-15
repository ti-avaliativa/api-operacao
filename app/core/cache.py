"""
Sistema de cache com TTL
"""
import hashlib
import json
import time
from functools import wraps
from cachetools import TTLCache
from app.core.config import CACHE_CONFIG

# Dicionário global de caches
caches = {}

def create_cache_key(*args, **kwargs):
    """Cria uma chave de cache única baseada nos argumentos da função."""
    key = {
        'args': args,
        'kwargs': kwargs
    }
    return hashlib.md5(json.dumps(key, sort_keys=True).encode()).hexdigest()

def cached(ttl_seconds=None, maxsize=None):
    """
    Decorator para cache de funções assíncronas
    
    Args:
        ttl_seconds: Tempo de vida do cache em segundos (default: CACHE_CONFIG['default_ttl'])
        maxsize: Tamanho máximo do cache (default: CACHE_CONFIG['default_maxsize'])
    """
    if ttl_seconds is None:
        ttl_seconds = CACHE_CONFIG['default_ttl']
    if maxsize is None:
        maxsize = CACHE_CONFIG['default_maxsize']
    
    def decorator(func):
        cache_key = f"{func.__module__}.{func.__name__}"
        if cache_key not in caches:
            caches[cache_key] = TTLCache(maxsize=maxsize, ttl=ttl_seconds)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = caches[cache_key]
            key = create_cache_key(*args, **kwargs)
            current_time = time.time()
            
            if key in cache and cache[key][1] > current_time:
                return cache[key][0]
            
            result = await func(*args, **kwargs)
            cache[key] = (result, current_time + ttl_seconds)
            return result
        
        return wrapper
    return decorator

