"""
工作流日志管理 - 统一的日志系统
"""

import logging
import sys
from typing import Optional
from pathlib import Path


class WorkflowLogger:
    """工作流日志管理器"""

    _instance: Optional['WorkflowLogger'] = None

    def __init__(self, name: str = "mas_aider", level: str = "INFO"):
        """
        初始化日志器

        Args:
            name: 日志器名称
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger(name)

        # 设置日志级别
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        self.logger.setLevel(level_map.get(level.upper(), logging.INFO))

        # 避免重复添加handler
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        """设置日志处理器"""
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)

        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)

        # 可选：文件处理器
        # try:
        #     file_handler = logging.FileHandler("workflow.log")
        #     file_handler.setLevel(logging.DEBUG)
        #     file_handler.setFormatter(formatter)
        #     self.logger.addHandler(file_handler)
        # except Exception:
        #     pass  # 文件日志失败时跳过

        self.logger.addHandler(console_handler)

    @classmethod
    def get_instance(cls, level: str = "INFO") -> 'WorkflowLogger':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls(level=level)
        return cls._instance

    def info(self, message: str, **kwargs):
        """记录信息日志"""
        self.logger.info(message, extra=kwargs)

    def error(self, message: str, exc_info: bool = False, **kwargs):
        """记录错误日志"""
        self.logger.error(message, exc_info=exc_info, extra=kwargs)

    def warning(self, message: str, **kwargs):
        """记录警告日志"""
        self.logger.warning(message, extra=kwargs)

    def debug(self, message: str, **kwargs):
        """记录调试日志"""
        self.logger.debug(message, extra=kwargs)

    def critical(self, message: str, **kwargs):
        """记录严重错误日志"""
        self.logger.critical(message, extra=kwargs)

    # 便捷方法
    def log_execution_start(self, workflow_name: str, **kwargs):
        """记录工作流执行开始"""
        self.info(f"🚀 Starting workflow execution: {workflow_name}", **kwargs)

    def log_execution_end(self, workflow_name: str, success: bool, duration: float, **kwargs):
        """记录工作流执行结束"""
        status = "✅ SUCCESS" if success else "❌ FAILED"
        self.info(f"{status} Workflow completed: {workflow_name} (duration: {duration:.2f}s)", **kwargs)

    def log_state_transition(self, from_state: str, to_state: str, condition: str = "", **kwargs):
        """记录状态转移"""
        if condition:
            self.debug(f"➡️ State transition: {from_state} -> {to_state} (condition: {condition})", **kwargs)
        else:
            self.debug(f"➡️ State transition: {from_state} -> {to_state}", **kwargs)

    def log_agent_call(self, agent_name: str, prompt_length: int, **kwargs):
        """记录Agent调用"""
        self.debug(f"🤖 Agent call: {agent_name} (prompt length: {prompt_length})", **kwargs)

    def log_config_loaded(self, config_path: str, **kwargs):
        """记录配置加载"""
        self.info(f"⚙️ Config loaded: {config_path}", **kwargs)

    def log_workflow_registered(self, workflow_name: str, **kwargs):
        """记录工作流注册"""
        self.info(f"📝 Workflow registered: {workflow_name}", **kwargs)


# 全局便捷函数
def get_logger(level: str = "INFO") -> WorkflowLogger:
    """获取日志器实例"""
    return WorkflowLogger.get_instance(level)


# 兼容性函数（用于替换print语句）
def log_info(message: str, **kwargs):
    """兼容性函数，替换print信息"""
    get_logger().info(message, **kwargs)


def log_error(message: str, exc_info: bool = False, **kwargs):
    """兼容性函数，替换print错误"""
    get_logger().error(message, exc_info=exc_info, **kwargs)


def log_warning(message: str, **kwargs):
    """兼容性函数，替换print警告"""
    get_logger().warning(message, **kwargs)


def log_debug(message: str, **kwargs):
    """兼容性函数，替换print调试"""
    get_logger().debug(message, **kwargs)
