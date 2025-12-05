"""
工作流异常层次结构 - 统一的错误处理机制
"""

from typing import Optional, Dict, Any


class WorkflowException(Exception):
    """工作流基础异常"""

    def __init__(self, message: str, error_code: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.context = context or {}

    def __str__(self):
        if self.error_code != "UNKNOWN_ERROR":
            return f"[{self.error_code}] {super().__str__()}"
        return super().__str__()


class ConfigurationError(WorkflowException):
    """配置相关错误"""

    def __init__(self, message: str, config_path: Optional[str] = None, field: Optional[str] = None):
        super().__init__(
            message,
            "CONFIG_ERROR",
            {"config_path": config_path, "field": field}
        )


class ValidationError(WorkflowException):
    """验证相关错误"""

    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        super().__init__(
            message,
            "VALIDATION_ERROR",
            {"field": field, "value": value}
        )


class ExecutionError(WorkflowException):
    """执行相关错误"""

    def __init__(self, message: str, workflow_name: Optional[str] = None, state_name: Optional[str] = None, agent_name: Optional[str] = None):
        super().__init__(
            message,
            "EXECUTION_ERROR",
            {"workflow_name": workflow_name, "state_name": state_name, "agent_name": agent_name}
        )


class AgentError(WorkflowException):
    """Agent相关错误"""

    def __init__(self, message: str, agent_name: Optional[str] = None, prompt: Optional[str] = None):
        super().__init__(
            message,
            "AGENT_ERROR",
            {"agent_name": agent_name, "prompt": prompt}
        )


class ConditionError(WorkflowException):
    """条件评估相关错误"""

    def __init__(self, message: str, condition: Optional[str] = None, state: Optional[Dict[str, Any]] = None):
        super().__init__(
            message,
            "CONDITION_ERROR",
            {"condition": condition, "state": state}
        )


class FileSystemError(WorkflowException):
    """文件系统相关错误"""

    def __init__(self, message: str, path: Optional[str] = None, operation: Optional[str] = None):
        super().__init__(
            message,
            "FILESYSTEM_ERROR",
            {"path": path, "operation": operation}
        )


class TimeoutError(WorkflowException):
    """超时错误"""

    def __init__(self, message: str, timeout_seconds: Optional[int] = None, operation: Optional[str] = None):
        super().__init__(
            message,
            "TIMEOUT_ERROR",
            {"timeout_seconds": timeout_seconds, "operation": operation}
        )


# 便捷异常创建函数
def config_error(message: str, **context) -> ConfigurationError:
    """创建配置错误"""
    return ConfigurationError(message, **context)


def validation_error(message: str, **context) -> ValidationError:
    """创建验证错误"""
    return ValidationError(message, **context)


def execution_error(message: str, **context) -> ExecutionError:
    """创建执行错误"""
    return ExecutionError(message, **context)


def agent_error(message: str, **context) -> AgentError:
    """创建Agent错误"""
    return AgentError(message, **context)


def condition_error(message: str, **context) -> ConditionError:
    """创建条件错误"""
    return ConditionError(message, **context)


def filesystem_error(message: str, **context) -> FileSystemError:
    """创建文件系统错误"""
    return FileSystemError(message, **context)


def timeout_error(message: str, **context) -> TimeoutError:
    """创建超时错误"""
    return TimeoutError(message, **context)


# 异常处理装饰器已移至 decorators 包
# 如需使用，请从 mas_aider.decorators 导入
