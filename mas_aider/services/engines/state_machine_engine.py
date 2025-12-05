"""
状态机执行引擎 - 基于配置的工作流执行器
"""

import time
from typing import Dict, Any, List, Optional
from ..evaluators.condition_evaluator import ConditionEvaluator
from ...workflows.workspace_interaction_guide import COLLABORATION_GUIDE

# 导入异常类和日志
try:
    from .exceptions import ExecutionError, AgentError, ConditionError, TimeoutError
    from .logging import get_logger
except ImportError:
    # 脚本模式下的简化异常类和日志
    class ExecutionError(Exception):
        def __init__(self, message, **kwargs):
            super().__init__(message)
            self.error_code = "EXECUTION_ERROR"
            for k, v in kwargs.items():
                setattr(self, k, v)

    class AgentError(Exception):
        def __init__(self, message, **kwargs):
            super().__init__(message)
            self.error_code = "AGENT_ERROR"
            for k, v in kwargs.items():
                setattr(self, k, v)

    class ConditionError(Exception):
        def __init__(self, message, **kwargs):
            super().__init__(message)
            self.error_code = "CONDITION_ERROR"
            for k, v in kwargs.items():
                setattr(self, k, v)

    class TimeoutError(Exception):
        def __init__(self, message, **kwargs):
            super().__init__(message)
            self.error_code = "TIMEOUT_ERROR"
            for k, v in kwargs.items():
                setattr(self, k, v)

    def get_logger():
        return None  # 简化模式下不使用日志


class StateMachineEngine:
    """
    状态机执行引擎

    负责：
    - 管理工作流状态转移
    - 执行Agent任务
    - 评估转移条件
    - 处理全局退出条件
    """

    def __init__(self, config: Dict[str, Any], agent_service, env_service):
        """
        初始化状态机引擎

        Args:
            config: 工作流配置
            agent_service: Agent服务
            env_service: 环境服务
        """
        self.config = config
        self.agent_service = agent_service
        self.env_service = env_service

        # 解析配置
        self.states = config.get("states", [])
        self.exit_conditions = config.get("exit_conditions", [])
        self.max_turns = config.get("max_turns", 10)

        # 初始化组件
        self.condition_evaluator = ConditionEvaluator(self.max_turns)
        self.state_map = {state["name"]: state for state in self.states}

    def execute(self, context, initial_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行工作流

        Args:
            context: 工作流上下文
            initial_state: 初始状态

        Returns:
            Dict[str, Any]: 执行结果
        """
        # 初始化全局状态
        global_state = initial_state or {}
        global_state.update({
            "turn_count": 0,
            "start_time": time.time(),
            "current_state": "start",
            "execution_history": [],
            "agent_responses": []
        })

        # 获取起始状态
        current_state_name = self._get_start_state()

        while current_state_name and current_state_name != "END":
            try:
                # 1. 检查全局退出条件
                if self._check_global_exit_conditions(global_state):
                    if get_logger():
                        get_logger().info("🏁 Global exit condition met, ending workflow")
                    break

                # 2. 获取当前状态配置
                current_state = self.state_map.get(current_state_name)
                if not current_state:
                    if get_logger():
                        get_logger().warning(f"State '{current_state_name}' not found, ending workflow")
                    break

                if get_logger():
                    get_logger().info(f"🔄 Executing state: {current_state_name}")

                # 3. 执行Agent任务
                agent_response = self._execute_agent_task(current_state, context, global_state)

                # 4. 更新全局状态
                global_state["agent_responses"].append({
                    "state": current_state_name,
                    "agent": current_state["agent"],
                    "response": agent_response,
                    "timestamp": time.time()
                })

                # 5. 合并Agent决策到全局状态
                decisions = agent_response.get("decisions", {})
                global_state.update(decisions)

                # 6. 记录执行历史
                global_state["execution_history"].append({
                    "state": current_state_name,
                    "agent": current_state["agent"],
                    "decisions": decisions,
                    "turn_count": global_state["turn_count"]
                })

                # 7. 评估状态转移条件
                next_state = self._evaluate_transitions(
                    current_state.get("transitions", []),
                    agent_response,
                    global_state
                )

                if get_logger():
                    get_logger().log_state_transition(current_state_name, next_state)

                # 8. 更新状态
                global_state["current_state"] = next_state
                global_state["turn_count"] += 1
                current_state_name = next_state

            except Exception as e:
                error_msg = f"Error in state '{current_state_name}': {e}"
                raise ExecutionError(error_msg, workflow_name=context.workflow_name, state_name=current_state_name) from e

        # 返回执行结果
        return self._build_result(global_state)

    def _get_start_state(self) -> Optional[str]:
        """获取起始状态"""
        # 查找标记为start的状态
        for state in self.states:
            if state.get("start", False):
                return state["name"]

        # 默认第一个状态
        if self.states:
            return self.states[0]["name"]

        return None

    def _execute_agent_task(self, state_config: Dict[str, Any], context, global_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行Agent任务

        Args:
            state_config: 状态配置
            context: 工作流上下文
            global_state: 全局状态

        Returns:
            Dict[str, Any]: Agent响应
        """
        agent_name = state_config["agent"]
        prompt_template = state_config.get("prompt", "")

        # 渲染prompt模板
        prompt = self._render_prompt(prompt_template, context, global_state)

        # 获取Agent实例 (这里需要从agent_service获取)
        # 注意：这里需要根据实际的Agent服务接口调整
        try:
            # 获取Agent实例
            agent = self.agent_service.get_agent_for_workflow(agent_name, context)
            response = agent.run(prompt)

            # 解析Agent响应
            return self._parse_agent_response(response)

        except Exception as e:
            error_msg = f"Failed to execute agent task for {agent_name}: {e}"
            raise AgentError(error_msg, agent_name=agent_name, prompt=prompt[:100]) from e

    def _render_prompt(self, template: str, context, global_state: Dict[str, Any]) -> str:
        """
        渲染prompt模板，支持Agent响应传递
        
        设计原则：
        - 只传递增量信息（接力棒），不传递完整历史
        - 详细历史由 Aider 自动管理（cur_messages + done_messages）
        - 文件变化由 Aider 自动感知（通过 fnames 和 RepoMap）
        """
        prompt = template

        # 基础变量替换
        prompt = prompt.replace("{{initial_message}}", context.initial_message or "")
        prompt = prompt.replace("{{turn_count}}", str(global_state.get("turn_count", 0)))

        # 协作规范替换
        prompt = prompt.replace("{{COLLABORATION_GUIDE}}", COLLABORATION_GUIDE.strip())

        # 传递上一轮的增量信息（接力棒）
        # 注意：这不是历史摘要，而是"上一轮对方刚刚说的那一句话"
        # Aider 会自动管理详细历史，我们只需要传递增量信息
        agent_responses = global_state.get("agent_responses", [])
        if agent_responses:
            last_response = agent_responses[-1]
            last_agent_name = last_response.get("agent", "")
            last_content = last_response.get("response", {}).get("content", "")
            last_decisions = last_response.get("response", {}).get("decisions", {})

            prompt = prompt.replace("{{last_agent_name}}", last_agent_name)
            prompt = prompt.replace("{{last_agent_content}}", last_content)
            prompt = prompt.replace("{{last_agent_decisions}}", str(last_decisions))
        else:
            # 第一轮，没有上一轮信息
            prompt = prompt.replace("{{last_agent_name}}", "")
            prompt = prompt.replace("{{last_agent_content}}", "")
            prompt = prompt.replace("{{last_agent_decisions}}", "{}")

        return prompt

    def _parse_agent_response(self, response: str) -> Dict[str, Any]:
        """解析Agent响应，支持JSON格式"""
        import json
        import re

        # 尝试提取JSON部分
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                return parsed
            except json.JSONDecodeError:
                pass

        # 如果不是JSON格式，返回纯文本响应
        return {
            "content": response,
            "decisions": {}
        }

    def _evaluate_transitions(self, transitions: List[Dict[str, Any]], agent_response: Dict[str, Any], global_state: Dict[str, Any]) -> str:
        """
        评估状态转移条件

        Args:
            transitions: 转移配置列表
            agent_response: Agent响应
            global_state: 全局状态

        Returns:
            str: 下一个状态名
        """
        for transition in transitions:
            condition = transition.get("condition", "true")
            target = transition.get("to", "END")

            if self.condition_evaluator.evaluate(condition, agent_response, global_state):
                return target

        # 默认转移到END
        return "END"

    def _check_global_exit_conditions(self, global_state: Dict[str, Any]) -> bool:
        """检查全局退出条件"""
        for exit_condition in self.exit_conditions:
            condition = exit_condition.get("condition", "")
            if self.condition_evaluator.evaluate(condition, {}, global_state):
                return True
        return False

    def _build_result(self, global_state: Dict[str, Any]) -> Dict[str, Any]:
        """构建执行结果"""
        return {
            "success": global_state.get("error") is None,
            "final_content": self._get_final_content(global_state),
            "total_turns": global_state.get("turn_count", 0),
            "agents_used": self._get_agents_used(global_state),
            "metadata": {
                "execution_history": global_state.get("execution_history", []),
                "error": global_state.get("error"),
                "error_state": global_state.get("error_state"),
                "total_time": time.time() - global_state.get("start_time", time.time())
            }
        }

    def _get_final_content(self, global_state: Dict[str, Any]) -> str:
        """获取最终内容 - 从collab目录获取所有文件内容"""
        try:
            workspace_info = self.env_service.get_workspace_info()
            collab_dir = workspace_info.collab_dir
            all_files_content = []

            # 收集collab目录下所有文件的内容
            for file_path in collab_dir.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith('.'):  # 跳过隐藏文件
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        relative_path = file_path.relative_to(collab_dir)
                        all_files_content.append(f"=== {relative_path} ===\n{content}")
                    except Exception as e:
                        all_files_content.append(f"=== {file_path.name} ===\n[无法读取文件: {e}]")

            return "\n\n".join(all_files_content) if all_files_content else "collab目录为空"
        except Exception as e:
            return f"无法读取collab目录内容: {e}"

    def _get_agents_used(self, global_state: Dict[str, Any]) -> List[str]:
        """获取使用的Agent列表"""
        history = global_state.get("execution_history", [])
        return list(set(item["agent"] for item in history))
