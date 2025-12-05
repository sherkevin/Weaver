"""
性能监控和日志装饰器

提供方法执行时间监控、调用日志记录等功能。
"""

import time
import logging
from functools import wraps
from typing import Callable, Any
from ..diagnostics.logging import get_logger


def time_execution(func: Callable) -> Callable:
    """执行时间监控装饰器

    记录方法执行时间，便于性能分析。
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        logger = get_logger()
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            logger.debug(f"{func.__name__} executed in {execution_time:.3f}s")
            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
            raise

    return wrapper


def log_method_calls(level: str = "DEBUG") -> Callable:
    """方法调用日志装饰器

    记录方法的调用情况，包括参数和返回值。
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = get_logger()

            # 记录方法调用
            if logger.isEnabledFor(getattr(logging, level)):
                args_str = ", ".join(repr(arg) for arg in args[1:])  # 跳过self
                kwargs_str = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())
                params = ", ".join(filter(None, [args_str, kwargs_str]))

                getattr(logger, level.lower())(f"Calling {func.__name__}({params})")

            # 执行方法
            result = func(*args, **kwargs)

            # 记录返回值
            if logger.isEnabledFor(getattr(logging, level)):
                getattr(logger, level.lower())(f"{func.__name__} returned: {repr(result)}")

            return result

        return wrapper
    return decorator


def count_calls(func: Callable) -> Callable:
    """方法调用计数装饰器

    统计方法被调用的次数。
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        wrapper.call_count += 1
        return func(*args, **kwargs)

    wrapper.call_count = 0
    return wrapper


def profile_memory(func: Callable) -> Callable:
    """内存使用监控装饰器

    监控方法执行时的内存使用情况。
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            mem_before = process.memory_info().rss / 1024 / 1024  # MB

            result = func(*args, **kwargs)

            mem_after = process.memory_info().rss / 1024 / 1024  # MB
            mem_delta = mem_after - mem_before

            logger = get_logger()
            logger.debug(f"Memory usage: {mem_before:.2f}MB -> {mem_after:.2f}MB (Δ{mem_delta:+.2f}MB)")
            return result

        except ImportError:
            # 如果没有psutil，直接执行
            return func(*args, **kwargs)

    return wrapper


def trace_execution(depth: int = 1) -> Callable:
    """执行追踪装饰器

    记录方法执行的调用栈信息。
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            import inspect

            logger = get_logger()

            # 获取调用栈信息
            frame = inspect.currentframe()
            try:
                # 向上查找调用者
                for _ in range(depth + 1):
                    frame = frame.f_back
                    if frame is None:
                        break

                if frame:
                    caller_info = f"{frame.f_code.co_name} in {frame.f_code.co_filename}:{frame.f_lineno}"
                    logger.debug(f"{func.__name__} called from: {caller_info}")
            finally:
                del frame

            return func(*args, **kwargs)

        return wrapper
    return decorator
