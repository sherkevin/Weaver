"""
数据验证装饰器

提供输入输出数据验证功能。
"""

from functools import wraps
from typing import Callable, Any, Type, Union
from ..diagnostics.exceptions import ValidationError


def validate_input(*validators) -> Callable:
    """输入验证装饰器

    验证方法输入参数是否符合要求。
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 跳过self参数
            actual_args = args[1:] if args else ()

            # 验证位置参数
            for i, arg in enumerate(actual_args):
                if i < len(validators) and validators[i]:
                    validator_func = validators[i]
                    if not validator_func(arg):
                        raise ValidationError(
                            f"Input validation failed for argument {i} in {func.__name__}: {arg}"
                        )

            # 验证关键字参数
            for key, value in kwargs.items():
                # 这里可以扩展为支持关键字参数验证
                pass

            return func(*args, **kwargs)

        return wrapper
    return decorator


def validate_output(validator: Callable[[Any], bool]) -> Callable:
    """输出验证装饰器

    验证方法返回值是否符合要求。
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            result = func(*args, **kwargs)

            if not validator(result):
                raise ValidationError(
                    f"Output validation failed for {func.__name__}: {result}"
                )

            return result

        return wrapper
    return decorator


# 常用验证器
def not_none(value: Any) -> bool:
    """验证值不为None"""
    return value is not None


def not_empty(value: Union[str, list, dict, tuple]) -> bool:
    """验证值不为空"""
    try:
        return len(value) > 0
    except TypeError:
        return False


def positive_number(value: Union[int, float]) -> bool:
    """验证为正数"""
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def in_range(min_val: Union[int, float], max_val: Union[int, float]) -> Callable:
    """创建范围验证器"""
    def validator(value: Union[int, float]) -> bool:
        try:
            return min_val <= float(value) <= max_val
        except (TypeError, ValueError):
            return False
    return validator


def of_type(expected_type: Type) -> Callable:
    """创建类型验证器"""
    def validator(value: Any) -> bool:
        return isinstance(value, expected_type)
    return validator


def matches_pattern(pattern: str) -> Callable:
    """创建正则表达式验证器"""
    import re
    compiled_pattern = re.compile(pattern)

    def validator(value: str) -> bool:
        try:
            return bool(compiled_pattern.match(str(value)))
        except (TypeError, AttributeError):
            return False

    return validator


# 组合验证器
def all_validators(*validators) -> Callable:
    """组合多个验证器（必须全部通过）"""
    def combined_validator(value: Any) -> bool:
        return all(validator(value) for validator in validators)
    return combined_validator


def any_validator(*validators) -> Callable:
    """组合多个验证器（只需一个通过）"""
    def combined_validator(value: Any) -> bool:
        return any(validator(value) for validator in validators)
    return combined_validator
