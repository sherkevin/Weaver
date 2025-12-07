"""
条件评估器测试 - 测试 AST 解析和表达式评估
"""

import unittest
import sys
from pathlib import Path

# 添加父目录到路径，以便导入模块
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.services.evaluators.condition_evaluator import UnifiedConditionEvaluator


class TestConditionEvaluator(unittest.TestCase):
    """条件评估器测试类"""
    
    def setUp(self):
        """设置测试环境"""
        self.evaluator = UnifiedConditionEvaluator(max_turns=10)
    
    def _evaluate(self, condition_expr: str, agent_response: dict = None, condition_state: dict = None, system_state: dict = None):
        """辅助方法：简化测试调用"""
        agent_response = agent_response or {"decisions": {}}
        condition_state = condition_state or {}
        system_state = system_state or {}
        return self.evaluator.evaluate(condition_expr, agent_response, condition_state, system_state)
    
    def test_system_conditions(self):
        """测试系统预定义条件"""
        # true
        self.assertTrue(self._evaluate("true"))
        
        # false
        self.assertFalse(self._evaluate("false"))
        
        # always
        self.assertTrue(self._evaluate("always"))
        
        # never
        self.assertFalse(self._evaluate("never"))
        
        # max_turns_exceeded（需要从 system_state 获取 total_turns）
        system_state = {"total_turns": 10}
        self.assertTrue(self._evaluate("max_turns_exceeded", system_state=system_state))
        
        system_state = {"total_turns": 5}
        self.assertFalse(self._evaluate("max_turns_exceeded", system_state=system_state))
        
        # error_occurred（需要从 system_state 获取 error）
        system_state = {"error": "Some error"}
        self.assertTrue(self._evaluate("error_occurred", system_state=system_state))
        
        system_state = {}
        self.assertFalse(self._evaluate("error_occurred", system_state=system_state))
    
    def test_agent_decisions(self):
        """测试 Agent 决策条件"""
        agent_response = {
            "decisions": {
                "design_confirmed": True,
                "ready_to_build": False,
                "quality_score": 8,
                "confidence": 0.9
            }
        }
        
        # 布尔值
        self.assertTrue(self._evaluate("design_confirmed", agent_response=agent_response))
        self.assertFalse(self._evaluate("ready_to_build", agent_response=agent_response))
        
        # 数值
        self.assertTrue(self._evaluate("quality_score", agent_response=agent_response))
    
    def test_comparison_operators(self):
        """测试比较运算符"""
        # 系统状态变量（细粒度 turn_count）
        agent_response = {"decisions": {}}
        condition_state = {"turn_count_client_supplier_clarify": 5}
        
        # 大于
        self.assertTrue(self.evaluator.evaluate("turn_count_client_supplier_clarify > 3", agent_response, condition_state))
        self.assertFalse(self.evaluator.evaluate("turn_count_client_supplier_clarify > 10", agent_response, condition_state))
        
        # 大于等于
        self.assertTrue(self.evaluator.evaluate("turn_count_client_supplier_clarify >= 5", agent_response, condition_state))
        self.assertFalse(self.evaluator.evaluate("turn_count_client_supplier_clarify >= 10", agent_response, condition_state))
        
        # 小于
        self.assertTrue(self.evaluator.evaluate("turn_count_client_supplier_clarify < 10", agent_response, condition_state))
        self.assertFalse(self.evaluator.evaluate("turn_count_client_supplier_clarify < 3", agent_response, condition_state))
        
        # 小于等于
        self.assertTrue(self.evaluator.evaluate("turn_count_client_supplier_clarify <= 5", agent_response, condition_state))
        self.assertFalse(self.evaluator.evaluate("turn_count_client_supplier_clarify <= 3", agent_response, condition_state))
        
        # 等于
        self.assertTrue(self.evaluator.evaluate("turn_count_client_supplier_clarify == 5", agent_response, condition_state))
        self.assertFalse(self.evaluator.evaluate("turn_count_client_supplier_clarify == 10", agent_response, condition_state))
        
        # 不等于
        self.assertTrue(self.evaluator.evaluate("turn_count_client_supplier_clarify != 10", agent_response, condition_state))
        self.assertFalse(self.evaluator.evaluate("turn_count_client_supplier_clarify != 5", agent_response, condition_state))
        
        # 业务决策变量（从 decisions 中读取）
        agent_response = {"decisions": {"quality_score": 8}}
        condition_state = {}
        self.assertTrue(self.evaluator.evaluate("quality_score >= 8", agent_response, condition_state))
        self.assertFalse(self.evaluator.evaluate("quality_score >= 9", agent_response, condition_state))
    
    def test_not_operator(self):
        """测试 NOT 运算符"""
        agent_response = {
            "decisions": {
                "design_confirmed": True,
                "ready_to_build": False
            }
        }
        # NOT True
        self.assertFalse(self._evaluate("NOT design_confirmed", agent_response=agent_response))
        
        # NOT False
        self.assertTrue(self._evaluate("NOT ready_to_build", agent_response=agent_response))
        
        # NOT (比较表达式)
        self.assertFalse(self._evaluate("NOT (design_confirmed == True)", agent_response=agent_response))
        self.assertTrue(self._evaluate("NOT (design_confirmed == False)", agent_response=agent_response))
    
    def test_and_operator(self):
        """测试 AND 运算符"""
        agent_response = {
            "decisions": {
                "design_confirmed": True,
                "ready_to_build": False,
                "quality_score": 8
            }
        }
        global_state = {}
        
        # True AND True
        self.assertTrue(self.evaluator.evaluate("design_confirmed AND design_confirmed", agent_response, global_state))
        
        # True AND False
        self.assertFalse(self.evaluator.evaluate("design_confirmed AND ready_to_build", agent_response, global_state))
        
        # False AND False
        self.assertFalse(self.evaluator.evaluate("ready_to_build AND ready_to_build", agent_response, global_state))
        
        # 链式 AND
        self.assertTrue(self.evaluator.evaluate("design_confirmed AND design_confirmed AND design_confirmed", agent_response, global_state))
        
        # 与比较表达式组合
        self.assertTrue(self.evaluator.evaluate("design_confirmed AND quality_score >= 8", agent_response, global_state))
        self.assertFalse(self.evaluator.evaluate("design_confirmed AND quality_score >= 9", agent_response, global_state))
    
    def test_or_operator(self):
        """测试 OR 运算符"""
        agent_response = {
            "decisions": {
                "design_confirmed": True,
                "ready_to_build": False
            }
        }
        global_state = {}
        
        # True OR False
        self.assertTrue(self.evaluator.evaluate("design_confirmed OR ready_to_build", agent_response, global_state))
        
        # False OR True
        self.assertTrue(self.evaluator.evaluate("ready_to_build OR design_confirmed", agent_response, global_state))
        
        # False OR False
        self.assertFalse(self.evaluator.evaluate("ready_to_build OR ready_to_build", agent_response, global_state))
        
        # 链式 OR
        self.assertTrue(self.evaluator.evaluate("design_confirmed OR ready_to_build OR design_confirmed", agent_response, global_state))
    
    def test_compound_conditions(self):
        """测试复合条件（NOT + AND + OR）"""
        agent_response = {
            "decisions": {
                "design_confirmed": True,
                "ready_to_build": False
            }
        }
        global_state = {}
        
        # NOT A AND NOT B
        # NOT True AND NOT False = False AND True = False
        self.assertFalse(self.evaluator.evaluate("NOT design_confirmed AND NOT ready_to_build", agent_response, global_state))
        
        # A OR B
        # True OR False = True
        self.assertTrue(self.evaluator.evaluate("design_confirmed OR ready_to_build", agent_response, global_state))
        
        # NOT A OR B
        # NOT True OR False = False OR False = False
        self.assertFalse(self.evaluator.evaluate("NOT design_confirmed OR ready_to_build", agent_response, global_state))
        
        # A AND NOT B
        # True AND NOT False = True AND True = True
        self.assertTrue(self.evaluator.evaluate("design_confirmed AND NOT ready_to_build", agent_response, global_state))
    
    def test_operator_precedence(self):
        """测试运算符优先级"""
        agent_response = {
            "decisions": {
                "a": True,
                "b": False,
                "c": True
            }
        }
        global_state = {}
        
        # AND 优先级高于 OR
        # True OR False AND True = True OR (False AND True) = True OR False = True
        self.assertTrue(self.evaluator.evaluate("a OR b AND c", agent_response, global_state))
        
        # NOT 优先级高于 AND
        # NOT False AND True = (NOT False) AND True = True AND True = True
        self.assertTrue(self.evaluator.evaluate("NOT b AND c", agent_response, global_state))
        
        # NOT 优先级高于 OR
        # NOT False OR False = (NOT False) OR False = True OR False = True
        self.assertTrue(self.evaluator.evaluate("NOT b OR b", agent_response, global_state))
    
    def test_parentheses(self):
        """测试括号优先级"""
        agent_response = {
            "decisions": {
                "a": True,
                "b": False,
                "c": True
            }
        }
        global_state = {}
        
        # (A OR B) AND C
        # (True OR False) AND True = True AND True = True
        self.assertTrue(self.evaluator.evaluate("(a OR b) AND c", agent_response, global_state))
        
        # A OR (B AND C)
        # True OR (False AND True) = True OR False = True
        self.assertTrue(self.evaluator.evaluate("a OR (b AND c)", agent_response, global_state))
        
        # NOT (A AND B)
        # NOT (True AND False) = NOT False = True
        self.assertTrue(self.evaluator.evaluate("NOT (a AND b)", agent_response, global_state))
        
        # (NOT A) AND B
        # (NOT True) AND False = False AND False = False
        self.assertFalse(self.evaluator.evaluate("(NOT a) AND b", agent_response, global_state))
    
    def test_chained_comparisons(self):
        """测试链式比较"""
        agent_response = {"decisions": {}}
        global_state = {"turn_count": 5}
        
        # 5 < 10 < 20
        self.assertTrue(self.evaluator.evaluate("turn_count < 10 < 20", agent_response, global_state))
        
        # 5 >= 5 <= 10
        self.assertTrue(self.evaluator.evaluate("turn_count >= 5 <= 10", agent_response, global_state))
        
        # 5 > 10 < 20 (False)
        self.assertFalse(self.evaluator.evaluate("turn_count > 10 < 20", agent_response, global_state))
    
    def test_string_values(self):
        """测试字符串值"""
        agent_response = {
            "decisions": {
                "status": "completed",
                "phase": "testing"
            }
        }
        global_state = {}
        
        # 字符串比较
        self.assertTrue(self.evaluator.evaluate("status == 'completed'", agent_response, global_state))
        self.assertFalse(self.evaluator.evaluate("status == 'pending'", agent_response, global_state))
        
        # 字符串比较（双引号）
        self.assertTrue(self.evaluator.evaluate('status == "completed"', agent_response, global_state))
    
    def test_string_to_bool_conversion(self):
        """测试字符串到布尔值的转换"""
        agent_response = {
            "decisions": {
                "flag1": "true",
                "flag2": "True",
                "flag3": "false",
                "flag4": "False",
                "flag5": "1",
                "flag6": "0",
                "flag7": "yes",
                "flag8": "no"
            }
        }
        global_state = {}
        
        # "true"/"True" -> True
        self.assertTrue(self.evaluator.evaluate("flag1", agent_response, global_state))
        self.assertTrue(self.evaluator.evaluate("flag2", agent_response, global_state))
        
        # "false"/"False" -> False
        self.assertFalse(self.evaluator.evaluate("flag3", agent_response, global_state))
        self.assertFalse(self.evaluator.evaluate("flag4", agent_response, global_state))
        
        # "1" -> True
        self.assertTrue(self.evaluator.evaluate("flag5", agent_response, global_state))
        
        # "0" -> False
        self.assertFalse(self.evaluator.evaluate("flag6", agent_response, global_state))
        
        # "yes" -> True
        self.assertTrue(self.evaluator.evaluate("flag7", agent_response, global_state))
        
        # "no" -> False
        self.assertFalse(self.evaluator.evaluate("flag8", agent_response, global_state))
    
    def test_variable_priority(self):
        """测试变量优先级（decisions 优先于 global_state）"""
        agent_response = {
            "decisions": {
                "turn_count": 100  # 覆盖 global_state 中的值
            }
        }
        global_state = {"turn_count": 5}
        
        # decisions 中的值应该优先
        self.assertTrue(self.evaluator.evaluate("turn_count == 100", agent_response, global_state))
        self.assertFalse(self.evaluator.evaluate("turn_count == 5", agent_response, global_state))
    
    def test_empty_expression(self):
        """测试空表达式"""
        agent_response = {"decisions": {}}
        global_state = {}
        
        # 空表达式应该返回 True
        self.assertTrue(self.evaluator.evaluate("", agent_response, global_state))
        self.assertTrue(self.evaluator.evaluate("   ", agent_response, global_state))
    
    def test_real_world_scenarios(self):
        """测试真实场景"""
        # 场景1：hulatang workflow 的条件
        agent_response = {
            "decisions": {
                "design_confirmed": True,
                "ready_to_build": False
            }
        }
        global_state = {}
        
        # NOT design_confirmed AND NOT ready_to_build
        # NOT True AND NOT False = False AND True = False
        self.assertFalse(self.evaluator.evaluate("NOT design_confirmed AND NOT ready_to_build", agent_response, global_state))
        
        # design_confirmed OR ready_to_build
        # True OR False = True
        self.assertTrue(self.evaluator.evaluate("design_confirmed OR ready_to_build", agent_response, global_state))
        
        # 场景2：质量检查
        agent_response = {
            "decisions": {
                "quality_score": 8,
                "confidence": 0.9,
                "review_passed": True
            }
        }
        global_state = {"turn_count": 3}
        
        # quality_score >= 8 AND confidence > 0.8
        self.assertTrue(self.evaluator.evaluate("quality_score >= 8 AND confidence > 0.8", agent_response, global_state))
        
        # review_passed AND turn_count < 5
        self.assertTrue(self.evaluator.evaluate("review_passed AND turn_count < 5", agent_response, global_state))
        
        # (quality_score >= 8 OR review_passed) AND turn_count < 10
        self.assertTrue(self.evaluator.evaluate("(quality_score >= 8 OR review_passed) AND turn_count < 10", agent_response, global_state))
    
    def test_undefined_variable(self):
        """测试未定义变量"""
        agent_response = {"decisions": {}}
        global_state = {}
        
        # 未定义的变量在 AST 解析失败时会回退到 legacy 模式，返回 False
        # 这是为了向后兼容
        self.assertFalse(self.evaluator.evaluate("undefined_var", agent_response, global_state))
        
        # 但 True/False/None 应该可以正常使用
        self.assertTrue(self.evaluator.evaluate("True", agent_response, global_state))
        self.assertFalse(self.evaluator.evaluate("False", agent_response, global_state))
        
        # 测试在复合表达式中使用未定义变量
        # 如果 AST 解析失败，会回退到 legacy 模式，返回 False
        # 如果 AST 解析成功但变量未定义，会抛出异常并被捕获，回退到 legacy 模式
        self.assertFalse(self.evaluator.evaluate("undefined_var == True", agent_response, global_state))


if __name__ == "__main__":
    unittest.main()

