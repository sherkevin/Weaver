"""
缓存装饰器

提供方法结果缓存功能，避免重复计算。
"""

from functools import wraps, lru_cache
import hashlib
import pickle
from pathlib import Path
from typing import Any, Callable


def memoize(func: Callable) -> Callable:
    """简单的内存缓存装饰器

    使用LRU缓存方法结果，避免重复计算相同输入。
    """
    @wraps(func)
    @lru_cache(maxsize=128)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


def cached_property(func: Callable) -> property:
    """缓存属性装饰器

    将方法转换为缓存的属性，只计算一次后缓存结果。
    """
    @wraps(func)
    def wrapper(self):
        cache_key = f"_cached_{func.__name__}"
        if not hasattr(self, cache_key):
            setattr(self, cache_key, func(self))
        return getattr(self, cache_key)
    return property(wrapper)


def file_cache(cache_dir: str = ".cache", max_age: int = 3600):
    """文件缓存装饰器

    将函数结果缓存到文件系统，避免重复计算。
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key_data = pickle.dumps((func.__name__, args, kwargs))
            cache_key = hashlib.md5(key_data).hexdigest()
            cache_file = Path(cache_dir) / f"{cache_key}.pkl"

            # 检查缓存是否存在且未过期
            if cache_file.exists():
                import time
                file_age = time.time() - cache_file.stat().st_mtime
                if file_age < max_age:
                    try:
                        with open(cache_file, 'rb') as f:
                            return pickle.load(f)
                    except Exception:
                        pass  # 缓存文件损坏，重新计算

            # 计算结果并缓存
            result = func(*args, **kwargs)
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump(result, f)
            except Exception:
                pass  # 缓存失败不影响正常执行

            return result
        return wrapper
    return decorator
