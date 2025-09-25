"""
测试工具服务模块
"""

import unittest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.services.evaluation_service import EvaluationService


class TestEvaluationService(unittest.TestCase):
    """评估服务测试类"""
    
    def setUp(self):
        """测试设置"""
        self.mock_config = {
            "deepseek": {
                "api_key": "test-key",
                "base_url": "https://api.deepseek.com", 
                "model": "deepseek-chat"
            }
        }
    
    def test_calculate_overall_score(self):
        """测试总体得分计算"""
        service = EvaluationService(self.mock_config)
        
        dimension_scores = {
            "technical_accuracy": 8.0,
            "communication": 7.0,
            "problem_solving": 6.0,
            "experience_depth": 7.5,
            "learning_ability": 8.5
        }
        
        overall_score = service._calculate_overall_score(dimension_scores)
        
        # 验证得分在合理范围内
        self.assertGreaterEqual(overall_score, 1.0)
        self.assertLessEqual(overall_score, 10.0)
        self.assertIsInstance(overall_score, float)
    
    def test_get_evaluation_level(self):
        """测试评估等级获取"""
        service = EvaluationService(self.mock_config)
        
        test_cases = [
            (9.5, "优秀"),
            (8.5, "良好"), 
            (7.5, "中等"),
            (6.5, "一般"),
            (5.0, "需要改进")
        ]
        
        for score, expected_level in test_cases:
            with self.subTest(score=score):
                level = service._get_evaluation_level(score)
                self.assertEqual(level, expected_level)
    
    def test_parse_evaluation_response(self):
        """测试评估响应解析"""
        service = EvaluationService(self.mock_config)
        
        # 测试正常格式
        response_content = "评分：8.5分\n理由：候选人表现优秀，技术理解深入。"
        score, feedback = service._parse_evaluation_response(response_content)
        
        self.assertEqual(score, 8.5)
        self.assertIn("技术理解深入", feedback)
        
        # 测试异常格式
        response_content = "这是一个没有标准格式的回复"
        score, feedback = service._parse_evaluation_response(response_content)
        
        self.assertEqual(score, 6.0)  # 默认分数
        self.assertEqual(feedback, "这是一个没有标准格式的回复")


if __name__ == "__main__":
    unittest.main()
