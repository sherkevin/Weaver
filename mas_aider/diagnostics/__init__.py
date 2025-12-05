"""
诊断功能模块

提供系统诊断相关的功能，包括异常处理和日志记录。
"""

from .exceptions import (
    WorkflowException,
    ConfigurationError,
    ValidationError,
    ExecutionError,
    AgentError,
    ConditionError,
    FileSystemError,
    TimeoutError,
    config_error,
    validation_error,
    execution_error,
    agent_error,
    condition_error,
    filesystem_error,
    timeout_error
)

from .logging import (
    WorkflowLogger,
    get_logger,
    log_info,
    log_error,
    log_warning,
    log_debug
)

__all__ = [
    # 异常类
    'WorkflowException',
    'ConfigurationError',
    'ValidationError',
    'ExecutionError',
    'AgentError',
    'ConditionError',
    'FileSystemError',
    'TimeoutError',

    # 异常构造器
    'config_error',
    'validation_error',
    'execution_error',
    'agent_error',
    'condition_error',
    'filesystem_error',
    'timeout_error',

    # 日志功能
    'WorkflowLogger',
    'get_logger',
    'log_info',
    'log_error',
    'log_warning',
    'log_debug'
]
