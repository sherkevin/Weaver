"""
LangGraph执行引擎 - 基于LangGraph的工作流编排引擎

替代原有的StateMachineEngine，使用LangGraph提供的图结构和流式执行能力。
"""

import time
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

from ..core.workflow_state import WorkflowState, create_initial_state, extract_agent_context
from ..services.evaluators.condition_evaluator import UnifiedConditionEvaluator
from ..diagnostics.logging import get_logger
from ..workflows.guide import COLLABORATION_GUIDE


class LangGraphEngine:
    """
    LangGraph工作流执行引擎
    
    核心职责：
    - 从YAML配置构建LangGraph
    - 管理Agent节点和状态转移
    - 使用UnifiedConditionEvaluator进行条件路由
    - 支持workflow router的热拔插
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        agent_service,
        env_service,
        condition_evaluator: UnifiedConditionEvaluator
    ):
        """
        初始化LangGraph引擎
        
        Args:
            config: Workflow配置（YAML解析后的字典）
            agent_service: Agent服务
            env_service: 环境服务
            condition_evaluator: 统一条件评估器（已注入router）
        """
        self.config = config
        self.agent_service = agent_service
        self.env_service = env_service
        self.condition_evaluator = condition_evaluator
        self.logger = get_logger()
        
        # 解析配置
        self.states = config.get("states", [])
        self.exit_conditions = config.get("exit_conditions", [])
        self.max_turns = config.get("max_turns", 10)
        
        # 构建状态映射
        self.state_map = {state["name"]: state for state in self.states}
        
        # 构建LangGraph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> Any:
        """
        从YAML配置构建LangGraph
        
        Returns:
            编译后的LangGraph
        """
        # 创建StateGraph
        graph = StateGraph(WorkflowState)
        
        # 1. 添加Agent节点（每个state对应一个节点）
        for state_config in self.states:
            state_name = state_config["name"]
            node_func = self._create_agent_node(state_config)
            graph.add_node(state_name, node_func)
        
        # 2. 设置入口点
        start_state = self._get_start_state()
        if not start_state:
            raise ValueError("No start state found in workflow configuration")
        graph.set_entry_point(start_state)
        
        # 3. 添加条件边（transitions）
        for state_config in self.states:
            state_name = state_config["name"]
            transitions = state_config.get("transitions", [])
            
            if transitions:
                # 使用条件路由
                router_func = self._create_router_function(transitions)
                path_map = self._create_path_map(transitions)
                
                graph.add_conditional_edges(
                    state_name,
                    router_func,
                    path_map
                )
            else:
                # 默认转到END
                graph.add_edge(state_name, END)
        
        # 编译图（LangGraph会自动处理递归限制，我们通过全局退出条件控制）
        return graph.compile()
    
    def _get_start_state(self) -> Optional[str]:
        """获取起始状态"""
        for state in self.states:
            if state.get("start", False):
                return state["name"]
        
        # 默认第一个状态
        if self.states:
            return self.states[0]["name"]
        
        return None
    
    def _create_agent_node(self, state_config: Dict[str, Any]) -> Callable:
        """
        创建Agent执行节点
        
        Args:
            state_config: 状态配置
            
        Returns:
            节点执行函数
        """
        agent_name = state_config["agent"]
        state_name = state_config["name"]
        prompt_template = state_config.get("prompt", "")
        
        def agent_node(state: WorkflowState) -> WorkflowState:
            """Agent节点执行函数"""
            try:
                # 1. 渲染prompt
                prompt = self._render_prompt(prompt_template, state)
                
                # 2. 获取Agent实例
                from ..core.workflow_base import WorkflowContext
                
                # 从state构建context（简化版）
                context = type('obj', (object,), {
                    'workflow_name': state["workflow_name"],
                    'metadata': {
                        'workspace_info': state["workspace_info"]
                    }
                })()
                
                agent = self.agent_service.get_agent_for_workflow(agent_name, context)
                
                # 3. 执行Agent
                self.logger.info(f"🤖 Executing {agent_name} in state '{state_name}'")
                response = agent.run(prompt)
                
                # 4. 解析响应
                parsed_response = self._parse_agent_response(response, agent_name, state_name)
                
                # 5. 更新状态
                state["last_agent"] = agent_name
                state["last_content"] = parsed_response.get("content", response)
                state["decisions"] = parsed_response.get("decisions", {})
                
                # 5.1 更新总交互次数（系统内部）
                state["total_turns"] = state.get("total_turns", 0) + 1
                
                # 5.2 更新细粒度 turn_count（用于 condition 评估）
                # 注意：这里需要知道下一个状态，但此时还不知道，所以需要在路由时更新
                # 暂时先不在这里更新，在路由函数中更新
                
                # 6. 记录执行历史
                state["execution_history"].append({
                    "state": state_name,
                    "agent": agent_name,
                    "decisions": state["decisions"],
                    "total_turns": state["total_turns"]
                })
                
                # 7. 记录完整响应（可选）
                if "agent_responses" not in state or state["agent_responses"] is None:
                    state["agent_responses"] = []
                
                state["agent_responses"].append({
                    "state": state_name,
                    "agent": agent_name,
                    "response": parsed_response,
                    "timestamp": time.time()
                })
                
                # 8. 添加消息到历史
                state["messages"].append(HumanMessage(content=prompt))
                state["messages"].append(AIMessage(content=response))
                
                return state
                
            except Exception as e:
                self.logger.error(f"❌ Error in state '{state_name}': {e}")
                state["error"] = str(e)
                state["error_state"] = state_name
                return state
        
        return agent_node
    
    def _create_router_function(self, transitions: List[Dict[str, Any]]) -> Callable:
        """
        创建LangGraph路由函数
        
        Args:
            transitions: 转移配置列表
            
        Returns:
            路由函数
        """
        def router(state: WorkflowState) -> str:
            """
            路由函数：根据条件决定下一个状态
            
            Args:
                state: 当前workflow状态
                
            Returns:
                下一个状态名称（必须在path_map中）
            """
            # 优先检查全局退出条件（在评估转移条件之前）
            if self._check_global_exit_conditions(state):
                self.logger.info("🏁 Global exit condition met, routing to END")
                return "END"
            
            # 提取Agent上下文
            context = extract_agent_context(state)
            agent_response = context["agent_response"]
            condition_state = context["condition_state"]
            system_state = context["system_state"]
            
            # 评估每个转移条件
            for transition in transitions:
                condition = transition.get("condition", "true")
                target = transition.get("to", "END")
                
                try:
                    if self.condition_evaluator.evaluate(condition, agent_response, condition_state, system_state):
                        # 更新细粒度 turn_count（在确定转移目标后）
                        from_agent = state.get("last_agent", "")
                        if from_agent and target != "END":
                            turn_count_key = f"turn_count_{from_agent}_{target}"
                            state[turn_count_key] = state.get(turn_count_key, 0) + 1
                            self.logger.debug(f"📊 Updated {turn_count_key} = {state[turn_count_key]}")
                        
                        self.logger.info(f"✅ Condition '{condition}' met, transitioning to '{target}'")
                        return target
                except Exception as e:
                    self.logger.warning(f"⚠️  Failed to evaluate condition '{condition}': {e}")
                    continue
            
            # 默认转到END
            self.logger.info("📍 No condition met, ending workflow")
            return "END"
        
        return router
    
    def _create_path_map(self, transitions: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        创建路径映射（LangGraph要求）
        
        Args:
            transitions: 转移配置列表
            
        Returns:
            路径映射字典 {key: target_state}
        """
        path_map = {}
        for transition in transitions:
            target = transition.get("to", "END")
            path_map[target] = target
        
        # 确保END总是存在
        path_map["END"] = END
        
        return path_map
    
    def _render_prompt(self, template: str, state: WorkflowState) -> str:
        """
        渲染prompt模板，支持条件语法 {% if %}
        
        Args:
            template: Prompt模板
            state: 当前状态
            
        Returns:
            渲染后的prompt
        """
        import re
        
        prompt = template
        
        # 基础变量替换
        prompt = prompt.replace("{{initial_message}}", state.get("initial_message", ""))
        # 注意：{{turn_count}} 模板变量已废弃，应该使用细粒度 turn_count
        # 为了向后兼容，暂时保留，但建议使用具体的 turn_count_{agent}_{state}
        prompt = prompt.replace("{{turn_count}}", str(state.get("total_turns", 0)))
        
        # 协作规范替换
        prompt = prompt.replace("{{COLLABORATION_GUIDE}}", COLLABORATION_GUIDE.strip())
        
        # 传递上一轮的增量信息
        agent_responses = state.get("agent_responses", [])
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
            last_agent_name = ""  # 用于条件判断
        
        # ✅ 处理条件语法 {% if %}...{% else %}...{% endif %}
        # 匹配模式：{% if last_agent_name == "supplier" %}...{% else %}...{% endif %}
        pattern = r'\{%\s*if\s+last_agent_name\s*==\s*["\'](\w+)["\']\s*%\}(.*?)\{%\s*else\s*%\}(.*?)\{%\s*endif\s*%\}'
        
        def replace_conditional(match):
            condition_value = match.group(1)  # "supplier"
            if_block = match.group(2)  # if 块内容
            else_block = match.group(3)  # else 块内容
            
            # 判断条件是否满足
            if last_agent_name == condition_value:
                return if_block  # 使用 if 块
            else:
                return else_block  # 使用 else 块
        
        # 替换所有条件块
        prompt = re.sub(pattern, replace_conditional, prompt, flags=re.DOTALL)
        
        return prompt
    
    def _parse_agent_response(self, response: str, agent_name: str = "unknown", state_name: str = "unknown") -> Dict[str, Any]:
        """
        解析Agent响应，必须包含JSON格式的decisions字段
        
        Args:
            response: Agent原始响应字符串
            agent_name: Agent名称（用于错误信息）
            state_name: 状态名称（用于错误信息）
            
        Returns:
            Dict[str, Any]: 解析后的响应，包含content和decisions
            
        Raises:
            AgentError: 如果响应不包含JSON格式或缺少decisions字段
        """
        import json
        import re
        from ..diagnostics.exceptions import AgentError
        
        # 尝试提取JSON部分
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if not json_match:
            # 如果没有找到JSON，报错退出
            raise AgentError(
                f"Agent响应未包含JSON格式。Agent '{agent_name}' 在状态 '{state_name}' 中的响应必须包含JSON对象，包含'content'和'decisions'字段。",
                agent_name=agent_name,
                prompt=f"响应内容（前500字符）: {response[:500]}..."
            )

        try:
            parsed = json.loads(json_match.group())
        except json.JSONDecodeError as e:
            # JSON格式错误
            raise AgentError(
                f"Agent响应的JSON格式无效: {e}。Agent '{agent_name}' 在状态 '{state_name}' 中的响应必须包含有效的JSON对象。",
                agent_name=agent_name,
                prompt=f"JSON部分（前200字符）: {json_match.group()[:200]}..."
            )

        # 验证必需字段
        if "decisions" not in parsed:
            raise AgentError(
                f"Agent响应缺少必需的'decisions'字段。Agent '{agent_name}' 在状态 '{state_name}' 中必须输出decisions字段用于条件评估。",
                agent_name=agent_name,
                prompt=f"解析的JSON: {parsed}"
            )

        # 确保包含content字段（如果没有，使用整个响应）
        if "content" not in parsed:
            parsed["content"] = response.replace(json_match.group(), "").strip()
        # 如果替换后为空，使用整个响应
        if not parsed["content"]:
            parsed["content"] = response

        return parsed
    
    def _check_global_exit_conditions(self, state: WorkflowState) -> bool:
        """检查全局退出条件"""
        context = extract_agent_context(state)
        condition_state = context["condition_state"]
        system_state = context["system_state"]
        
        # 检查 max_turns（系统级退出条件）
        if system_state.get("total_turns", 0) >= self.max_turns:
            self.logger.info(f"🏁 Max turns exceeded: {system_state.get('total_turns')} >= {self.max_turns}")
            return True
        
        # 检查 YAML 中定义的退出条件
        for exit_condition in self.exit_conditions:
            condition = exit_condition.get("condition", "")
            if condition:
                try:
                    if self.condition_evaluator.evaluate(condition, {}, condition_state, system_state):
                        self.logger.info(f"🏁 Global exit condition met: {condition}")
                        return True
                except Exception as e:
                    self.logger.warning(f"⚠️  Failed to evaluate exit condition '{condition}': {e}")
        
        return False
    
    def execute(self, context, initial_state_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行工作流
        
        Args:
            context: 工作流上下文
            initial_state_data: 初始状态数据
            
        Returns:
            执行结果
        """
        # 创建初始状态
        initial_state = create_initial_state(
            workflow_name=context.workflow_name,
            initial_message=context.initial_message,
            workspace_info=initial_state_data.get("workspace_info") if initial_state_data else {}
        )
        
        try:
            # 设置 LangGraph 配置，包括递归限制
            # recursion_limit 应该大于 max_turns，给足够的执行空间
            recursion_limit = self.max_turns * 3
            config = {"recursion_limit": recursion_limit}
            
            # 执行LangGraph
            final_state = self.graph.invoke(initial_state, config=config)
            
            # 构建结果
            return self._build_result(final_state)
            
        except Exception as e:
            self.logger.error(f"❌ Workflow execution failed: {e}")
            return {
                "success": False,
                "final_content": "",
                "total_turns": initial_state.get("total_turns", 0),
                "agents_used": [],
                "metadata": {
                    "error": str(e),
                    "execution_history": initial_state.get("execution_history", [])
                }
            }
    
    def _build_result(self, final_state: WorkflowState) -> Dict[str, Any]:
        """构建执行结果"""
        return {
            "success": final_state.get("error") is None,
            "final_content": self._get_final_content(final_state),
            "total_turns": final_state.get("total_turns", 0),
            "agents_used": self._get_agents_used(final_state),
            "metadata": {
                "execution_history": final_state.get("execution_history", []),
                "error": final_state.get("error"),
                "error_state": final_state.get("error_state"),
                "total_time": time.time() - final_state.get("start_time", time.time())
            }
        }
    
    def _get_final_content(self, final_state: WorkflowState) -> str:
        """获取最终内容 - 从collab目录获取所有文件内容"""
        try:
            workspace_info = final_state.get("workspace_info", {})
            if not workspace_info:
                return ""
            
            collab_dir = workspace_info.get("collab_dir")
            if not collab_dir:
                return ""
            
            collab_dir = Path(collab_dir)
            all_files_content = []
            
            # 收集collab目录下所有文件的内容
            for file_path in collab_dir.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        relative_path = file_path.relative_to(collab_dir)
                        all_files_content.append(f"=== {relative_path} ===\n{content}")
                    except Exception as e:
                        all_files_content.append(f"=== {file_path.name} ===\n[无法读取文件: {e}]")
            
            return "\n\n".join(all_files_content) if all_files_content else "collab目录为空"
        except Exception as e:
            return f"无法读取collab目录内容: {e}"
    
    def _get_agents_used(self, final_state: WorkflowState) -> List[str]:
        """获取使用的Agent列表"""
        history = final_state.get("execution_history", [])
        return list(set(item["agent"] for item in history if "agent" in item))
