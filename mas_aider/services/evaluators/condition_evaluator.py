"""
条件评估引擎 - 支持多种条件类型的评估

这是业务逻辑服务，负责复杂的条件判断逻辑。
"""

import re
import operator
from typing import Dict, Any, Callable


class ConditionEvaluator:
    """
    强大的条件评估引擎

    支持的条件类型：
    - 系统条件: "always", "never", "max_turns_exceeded"
    - Agent决策: "needs_implementation" (从decisions字段读取)
    - 状态表达式: "turn_count > 5", "quality_score >= 8"
    - 复合条件: "quality_score >= 8 AND confidence > 0.8"
    - 自定义函数: "check_complex_logic"
    """

    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns

        # 系统预定义条件
        self.system_conditions: Dict[str, Callable] = {
            "always": lambda agent_response, state: True,
            "never": lambda agent_response, state: False,
            "max_turns_exceeded": lambda agent_response, state: state.get("turn_count", 0) >= self.max_turns,
            "error_occurred": lambda agent_response, state: state.get("error") is not None,
        }

    def evaluate(self, condition_expr: str, agent_response: Dict[str, Any], global_state: Dict[str, Any]) -> bool:
        """
        评估条件表达式

        Args:
            condition_expr: 条件表达式
            agent_response: Agent的完整响应
            global_state: 全局状态

        Returns:
            bool: 条件是否满足
        """
        if not condition_expr or condition_expr.strip() == "":
            return True

        condition_expr = condition_expr.strip()

        # 1. 系统预定义条件
        if condition_expr in self.system_conditions:
            return self.system_conditions[condition_expr](agent_response, global_state)

        # 2. Agent决策条件 (从decisions字段读取)
        decisions = agent_response.get("decisions", {})
        if condition_expr in decisions:
            return bool(decisions[condition_expr])

        # 3. 状态表达式条件 (turn_count > 5)
        if self._is_state_expression(condition_expr):
            return self._evaluate_state_expression(condition_expr, global_state)

        # 4. 复合条件 (AND/OR/NOT)
        if any(op in condition_expr.upper() for op in [" AND ", " OR ", " NOT "]):
            return self._evaluate_compound_condition(condition_expr, agent_response, global_state)

        # 5. 自定义条件函数
        if hasattr(self, f"check_{condition_expr}"):
            return getattr(self, f"check_{condition_expr}")(agent_response, global_state)

        # 6. 默认处理 - 尝试从全局状态获取
        return bool(global_state.get(condition_expr, False))

    def _is_state_expression(self, expr: str) -> bool:
        """检查是否是状态表达式 (包含比较运算符)"""
        return any(op in expr for op in [">=", "<=", "!=", "==", ">", "<", "="])

    def _evaluate_state_expression(self, expr: str, state: Dict[str, Any]) -> bool:
        """评估状态表达式"""
        try:
            # 简单的表达式评估 (turn_count > 5)
            expr = expr.replace("=", "==")  # 统一等于号

            # 提取变量名和值
            var_match = re.match(r'(\w+)\s*([><=!]+)\s*(.+)', expr)
            if var_match:
                var_name, op, value_str = var_match.groups()

                # 获取变量值
                var_value = state.get(var_name)
                if var_value is None:
                    return False

                # 转换比较值
                try:
                    if "." in value_str or "e" in value_str.lower():
                        compare_value = float(value_str)
                    else:
                        compare_value = int(value_str)
                except ValueError:
                    compare_value = value_str.strip('"\'')  # 字符串值

                # 执行比较
                if op == "==":
                    return var_value == compare_value
                elif op == "!=":
                    return var_value != compare_value
                elif op == ">":
                    return var_value > compare_value
                elif op == ">=":
                    return var_value >= compare_value
                elif op == "<":
                    return var_value < compare_value
                elif op == "<=":
                    return var_value <= compare_value

            return False

        except Exception as e:
            print(f"Warning: Failed to evaluate expression '{expr}': {e}")
            return False

    def _evaluate_compound_condition(self, expr: str, agent_response: Dict[str, Any], global_state: Dict[str, Any]) -> bool:
        """评估复合条件 (AND/OR/NOT)"""
        try:
            # 递归处理复合条件
            expr_upper = expr.upper()

            # 处理NOT
            if expr_upper.startswith("NOT "):
                sub_expr = expr[4:].strip()
                return not self.evaluate(sub_expr, agent_response, global_state)

            # 处理AND
            if " AND " in expr_upper:
                parts = self._split_by_operator(expr, "AND")
                return all(self.evaluate(part.strip(), agent_response, global_state) for part in parts)

            # 处理OR
            if " OR " in expr_upper:
                parts = self._split_by_operator(expr, "OR")
                return any(self.evaluate(part.strip(), agent_response, global_state) for part in parts)

            return False

        except Exception as e:
            print(f"Warning: Failed to evaluate compound condition '{expr}': {e}")
            return False

    def _split_by_operator(self, expr: str, operator: str) -> list:
        """按运算符分割表达式，处理括号"""
        parts = []
        current_part = ""
        paren_depth = 0

        i = 0
        while i < len(expr):
            char = expr[i]

            if char == "(":
                paren_depth += 1
                current_part += char
            elif char == ")":
                paren_depth -= 1
                current_part += char
            elif paren_depth == 0:
                # 检查是否匹配运算符
                if expr[i:i+len(operator)+2].upper() == f" {operator} ":
                    parts.append(current_part.strip())
                    current_part = ""
                    i += len(operator) + 1  # 跳过" AND "
                    continue
                else:
                    current_part += char
            else:
                current_part += char

            i += 1

        if current_part.strip():
            parts.append(current_part.strip())

        return parts

    # 自定义条件检查函数
    def check_complex_logic(self, agent_response: Dict[str, Any], global_state: Dict[str, Any]) -> bool:
        """自定义条件检查示例"""
        decisions = agent_response.get("decisions", {})
        quality = decisions.get("quality_score", 0)
        confidence = decisions.get("confidence", 0)

        return quality >= 7 and confidence > 0.7

    def check_high_quality(self, agent_response: Dict[str, Any], global_state: Dict[str, Any]) -> bool:
        """高质量检查"""
        decisions = agent_response.get("decisions", {})
        return decisions.get("quality_score", 0) >= 9
