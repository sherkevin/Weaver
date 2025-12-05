"""
重试机制装饰器

提供自动重试功能，提高系统容错性。
"""

import time
import random
from functools import wraps
from typing import Callable, Any, Type


def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,)
) -> Callable:
    """失败重试装饰器

    在指定异常发生时自动重试，采用指数退避策略。

    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 退避倍数
        jitter: 是否添加随机抖动
        exceptions: 需要重试的异常类型

    使用示例:
        @retry_on_failure(max_attempts=5, delay=0.1)
        def unstable_operation():
            # 可能失败的操作
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_attempts - 1:  # 不是最后一次尝试
                        # 计算延迟时间
                        actual_delay = current_delay
                        if jitter:
                            # 添加随机抖动，避免惊群效应
                            actual_delay *= (0.5 + random.random() * 0.5)

                        time.sleep(actual_delay)
                        current_delay *= backoff

            # 所有重试都失败了
            raise last_exception

        return wrapper
    return decorator


def exponential_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> Callable:
    """指数退避重试装饰器

    使用指数退避策略，避免服务过载。
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_attempts - 1:
                        # 计算指数退避延迟
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        if jitter:
                            delay *= (0.5 + random.random() * 0.5)

                        time.sleep(delay)

            # 重新抛出最后一个异常
            raise

        return wrapper
    return decorator


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exceptions: tuple = (Exception,)
) -> Callable:
    """熔断器装饰器

    当失败次数超过阈值时，打开熔断器一段时间，避免继续调用失败的服务。
    """
    def decorator(func: Callable) -> Callable:
        # 熔断器状态
        failures = 0
        last_failure_time = 0
        state = "closed"  # closed, open, half_open

        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            nonlocal failures, last_failure_time, state

            current_time = time.time()

            # 检查是否需要从打开状态转换到半开状态
            if state == "open" and current_time - last_failure_time > recovery_timeout:
                state = "half_open"

            # 熔断器打开状态，直接抛出异常
            if state == "open":
                raise Exception("Circuit breaker is OPEN")

            try:
                result = func(*args, **kwargs)

                # 成功调用，重置失败计数
                if state == "half_open":
                    state = "closed"
                failures = 0

                return result

            except expected_exceptions as e:
                failures += 1
                last_failure_time = current_time

                # 检查是否需要打开熔断器
                if failures >= failure_threshold:
                    state = "open"

                raise e

        return wrapper
    return decorator
