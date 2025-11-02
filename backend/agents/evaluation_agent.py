"""
面试评估智能体
基于Qwen模型，负责面试评估和报告生成
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from backend.utils.logger import get_logger
from backend.models.qwen_model import QwenModel

class EvaluationAgent:
    """面试评估智能体"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)
        self.model = QwenModel(config)
        
        # 评估维度配置
        self.evaluation_dimensions = {
            "technical_depth": {
                "weight": 0.3,
                "metrics": ["knowledge_breadth", "knowledge_depth", "practical_experience"]
            },
            "logical_thinking": {
                "weight": 0.3,
                "metrics": ["problem_solving", "analytical_skills", "structured_thinking"]
            },
            "communication": {
                "weight": 0.2,
                "metrics": ["clarity", "conciseness", "engagement"]
            },
            "innovation": {
                "weight": 0.2,
                "metrics": ["creativity", "solution_design", "learning_ability"]
            }
        }
    
    def evaluate_interview(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """评估整场面试"""
        try:
            # 获取面试记录
            conversation_history = session_data.get("conversation_history", [])
            if not conversation_history:
                raise ValueError("面试记录为空")
            
            # 获取简历数据（如果有）
            resume_data = session_data.get("metadata", {}).get("resume_content")
            
            # 生成评估
            evaluation = self.model.analyze_interview(
                conversation_history=conversation_history,
                resume_data=resume_data
            )
            
            # 添加元数据
            evaluation["metadata"] = {
                "session_id": session_data.get("session_id"),
                "interview_duration": self._calculate_duration(session_data),
                "questions_count": len([msg for msg in conversation_history if msg["role"] == "assistant"]),
                "evaluation_time": datetime.now().isoformat()
            }
            
            return evaluation
            
        except Exception as e:
            self.logger.error(f"面试评估失败: {str(e)}")
            raise
    
    def generate_report(self, 
                       session_data: Dict[str, Any],
                       evaluation_result: Dict[str, Any],
                       format: str = "markdown") -> str:
        """生成评估报告"""
        try:
            # 生成报告
            report = self.model.generate_report(
                evaluation_result=evaluation_result,
                report_format=format
            )
            
            return report
            
        except Exception as e:
            self.logger.error(f"报告生成失败: {str(e)}")
            raise
    
    def analyze_answer(self, answer: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """实时分析单个回答"""
        try:
            prompt = f"""请分析以下面试回答的质量：

回答内容：{answer}

{f'相关上下文：{json.dumps(context, ensure_ascii=False)}' if context else ''}

请从以下维度评分（0-10分）并说明理由：
1. 技术准确性
2. 表达清晰度
3. 理解深度
4. 实践经验
5. 逻辑性

输出格式要求：JSON，包含scores（各维度分数）、overall_score（总分）、strengths（优点）和improvements（建议）字段。"""

            result = self.model.generate(prompt)
            
            try:
                return json.loads(result["content"])
            except json.JSONDecodeError:
                return {
                    "scores": {"accuracy": 5, "clarity": 5, "depth": 5, "experience": 5, "logic": 5},
                    "overall_score": 5.0,
                    "strengths": [],
                    "improvements": ["无法解析评估结果"]
                }
                
        except Exception as e:
            self.logger.error(f"回答分析失败: {str(e)}")
            return {
                "scores": {"accuracy": 5, "clarity": 5, "depth": 5, "experience": 5, "logic": 5},
                "overall_score": 5.0,
                "strengths": [],
                "improvements": ["评估过程出错"]
            }
    
    def _calculate_duration(self, session_data: Dict[str, Any]) -> int:
        """计算面试时长（分钟）"""
        try:
            start_time = datetime.fromisoformat(session_data["start_time"])
            end_time = datetime.fromisoformat(session_data.get("end_time", datetime.now().isoformat()))
            duration_seconds = (end_time - start_time).total_seconds()
            return int(duration_seconds / 60)
        except:
            return 0
