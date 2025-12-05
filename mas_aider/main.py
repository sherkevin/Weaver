"""
多Agent系统主入口 - 支持Keep-Alive会话

支持会话保持 (Keep-Alive) 和单次运行两种模式
"""

import time
from pathlib import Path
from typing import Optional, Dict, Any

# 导入架构组件
from .config import AppConfig
from .services import EnvironmentService, AgentService
from .core import WorkflowFactory, WorkflowContext
from .diagnostics.logging import get_logger


class MasAiderSession:
    """
    持久化会话管理器
    保持 Service 和 Agent 在内存中存活，允许连续运行多个工作流
    """

    def __init__(self, auto_cleanup: bool = True):
        """
        初始化持久化会话

        Args:
            auto_cleanup: 是否在会话结束时自动清理Agent缓存
        """
        # 1. 加载配置
        self.config = AppConfig.load()
        self.logger = get_logger()
        self.auto_cleanup = auto_cleanup
        self.start_time = time.time()

        # 2. 初始化服务 (只初始化一次，这就是 Keep-Alive 的关键)
        self.env_service = EnvironmentService(self.config)
        self.agent_service = AgentService(self.config)

        # 3. 跟踪活跃的工作流
        self.active_workflows: set[str] = set()

        self.logger.info("🚀 MasAider Session Initialized (Agents are alive)")
        self.logger.info(f"📊 Session ID: {id(self)}")

    def run_workflow(self, workflow_name: str = "collaboration", custom_config_path: Optional[str] = None) -> Any:
        """
        在当前会话中运行工作流

        Args:
            workflow_name: 工作流名称
            custom_config_path: 可选的自定义配置文件路径

        Returns:
            工作流执行结果
        """
        self.active_workflows.add(workflow_name)

        try:
            # 动态注册工作流（如果需要）
            self._ensure_workflows_registered()

            # 3. 创建工作流上下文
            initial_message = WorkflowFactory.get_workflow_initial_message(workflow_name)

            context = WorkflowContext(
                workflow_name=workflow_name,
                config=self.config,
                initial_message=initial_message,
                metadata={
                    "env_service": self.env_service,
                    "agent_service": self.agent_service
                }
            )

            # 4. 创建工作流
            workflow = WorkflowFactory.create(workflow_name, context)

            # 支持自定义配置文件路径
            if custom_config_path and hasattr(workflow, 'config_path'):
                workflow.config_path = custom_config_path
                # 重新加载配置（如果支持）
                if hasattr(workflow, '_load_config'):
                    workflow.config = workflow._load_config()

            # 5. 执行工作流
            self.logger.log_execution_start(workflow_name)
            result = workflow.execute()

            # 6. 输出结果
            self._print_results(result)
            return result

        except Exception as e:
            self.logger.error(f"❌ Workflow '{workflow_name}' failed: {e}")
            raise

    def _ensure_workflows_registered(self):
        """确保工作流已注册"""
        # 这里保留原本的动态加载逻辑，或者是简单的预注册
        # 为了简化，这里假设 Factory 已经能处理或在外部处理了
        pass

    def _print_results(self, result) -> None:
        """输出执行结果"""
        self.logger.info("="*60)
        self.logger.info("📊 WORKFLOW EXECUTION RESULTS")
        self.logger.info("="*60)

        if hasattr(result, 'success') and result.success:
            self.logger.info("✅ Status: SUCCESS")
            if hasattr(result, 'total_turns'):
                self.logger.info(f"🔄 Total Turns: {result.total_turns}")
            if hasattr(result, 'agents_used'):
                self.logger.info(f"🤖 Agents Used: {', '.join(result.agents_used)}")

            if hasattr(result, 'final_content') and result.final_content.strip():
                self.logger.info("📄 Final content generated successfully")
            else:
                self.logger.warning("⚠️ No content generated in shared file")
        else:
            self.logger.error("❌ Status: FAILED")
            if hasattr(result, 'error_message') and result.error_message:
                self.logger.error(f"💥 Error: {result.error_message}")

        # 显示额外元数据
        if hasattr(result, 'metadata') and result.metadata:
            self.logger.info("📋 Additional metadata available")

        self.logger.info("="*60)

    def cleanup_workflow(self, workflow_name: str):
        """
        显式清理特定工作流的Agent缓存

        Args:
            workflow_name: 工作流名称
        """
        if workflow_name in self.active_workflows:
            self.agent_service.clear_agents_for_workflow(workflow_name)
            self.active_workflows.discard(workflow_name)
            self.logger.info(f"🧹 Cleaned up workflow '{workflow_name}'")

    def get_session_info(self) -> Dict[str, Any]:
        """
        获取会话状态信息

        Returns:
            会话统计信息
        """
        cache_stats = self.agent_service.get_cache_stats()

        return {
            "session_id": id(self),
            "active_workflows": list(self.active_workflows),
            "session_uptime": time.time() - self.start_time,
            "cached_agents": cache_stats,
            "auto_cleanup": self.auto_cleanup
        }

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口，自动清理"""
        if self.auto_cleanup:
            for workflow in list(self.active_workflows):
                self.cleanup_workflow(workflow)
            self.logger.info("🧹 Session cleanup completed")


# --- 为了兼容旧的 main 函数调用方式 ---


def main(workflow_name: str = "collaboration"):
    """
    单次运行入口 (兼容旧代码)

    注意：这种方式运行结束后，Agent 依然会被销毁。
    如果要 Keep-Alive，请在外部脚本使用 MasAiderSession 类。

    Args:
        workflow_name: 工作流名称
    """
    session = MasAiderSession()
    session.run_workflow(workflow_name)


def list_available_workflows() -> None:
    """列出所有可用的工作流"""
    from .core import WorkflowFactory
    from .diagnostics.logging import get_logger
    logger = get_logger()

    logger.info("Available workflows:")
    workflows = WorkflowFactory.get_available_workflows()
    if not workflows:
        logger.info("  No workflows registered. Ensure workflow YAMLs or Python classes are correctly defined.")
    for name, cls in workflows.items():
        logger.info(f"  - {name}: {cls.__name__}")


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 当作为脚本运行时，确保可以导入相对模块
    sys.path.insert(0, str(Path(__file__).parent))

    if len(sys.argv) > 1:
        if sys.argv[1] == "--list":
            list_available_workflows()
        elif sys.argv[1] == "--run" and len(sys.argv) > 2:
            workflow_name = sys.argv[2]
            main(workflow_name)
        else:
            print("Usage: python -m mas_aider.main [--list | --run <workflow_name>]")
            print("Available workflow types: collaboration, hulatang")
    else:
        main("collaboration")  # 默认运行 collaboration