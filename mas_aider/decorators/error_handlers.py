"""
错误处理装饰器

提供统一的异常处理机制，避免在业务逻辑中出现try-catch的额外缩进。
"""

from functools import wraps
from ..diagnostics.exceptions import ConfigurationError, WorkflowException, ExecutionError


def config_load_error_handler(func):
    """配置加载错误处理装饰器

    自动捕获配置加载过程中的异常并转换为ConfigurationError，
    避免在主函数中出现try-catch的额外缩进。

    使用示例:
        @classmethod
        @config_load_error_handler
        def load(cls) -> 'AppConfig':
            # 主要逻辑，无try-catch缩进！
            return do_something()
    """
    @wraps(func)
    def wrapper(cls, *args, **kwargs):
        try:
            return func(cls, *args, **kwargs)
        except ConfigurationError:
            # 已是我们自定义的异常，直接重新抛出
            raise
        except Exception as e:
            # 捕获其他异常，转换为ConfigurationError
            config_path = cls._get_config_path()
            raise ConfigurationError(f"Failed to load config from {config_path}: {e}")
    return wrapper


def workflow_execution_error_handler(func):
    """工作流执行错误处理装饰器

    处理工作流执行过程中的异常，转换为WorkflowException。
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except WorkflowException:
            raise
        except Exception as e:
            raise WorkflowException(f"Workflow execution failed: {e}")
    return wrapper


def agent_operation_error_handler(func):
    """Agent操作错误处理装饰器

    处理Agent执行过程中的异常，提供统一的错误处理。
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except ExecutionError:
            raise
        except Exception as e:
            raise ExecutionError(f"Agent operation failed: {e}")
    return wrapper
