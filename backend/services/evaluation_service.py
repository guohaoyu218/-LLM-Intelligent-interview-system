"""
评估服务模块
提供面试评分和分析功能
"""

from typing import Dict, List, Any, Optional
import json
import re
from datetime import datetime

from backend.utils.logger import get_logger
from backend.models.deepseek_model import DeepSeekLLM


class EvaluationService:
    """评估服务类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)
        self.llm = DeepSeekLLM(config)
        
        # 评分维度和权重
        self.evaluation_dimensions = {
            "technical_accuracy": {"weight": 0.25, "name": "技术准确性"},
            "communication": {"weight": 0.20, "name": "沟通表达"},
            "problem_solving": {"weight": 0.20, "name": "问题解决"},
            "experience_depth": {"weight": 0.20, "name": "经验深度"},
            "learning_ability": {"weight": 0.15, "name": "学习能力"}
        }
    
    def evaluate_interview(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """评估整个面试"""
        try:
            # 提取对话内容
            conversation_history = session_data.get("conversation_history", [])
            
            # 分别评估每个维度
            dimension_scores = {}
            detailed_feedback = {}
            
            for dimension, config in self.evaluation_dimensions.items():
                score, feedback = self._evaluate_dimension(conversation_history, dimension)
                dimension_scores[dimension] = score
                detailed_feedback[dimension] = feedback
            
            # 计算总体得分
            overall_score = self._calculate_overall_score(dimension_scores)
            
            # 生成综合评价
            comprehensive_feedback = self._generate_comprehensive_feedback(
                conversation_history, dimension_scores, overall_score
            )
            
            # 生成改进建议
            improvement_suggestions = self._generate_improvement_suggestions(
                dimension_scores, detailed_feedback
            )
            
            evaluation_result = {
                "session_id": session_data.get("session_id"),
                "evaluation_time": datetime.now().isoformat(),
                "overall_score": overall_score,
                "dimension_scores": dimension_scores,
                "detailed_feedback": detailed_feedback,
                "comprehensive_feedback": comprehensive_feedback,
                "improvement_suggestions": improvement_suggestions,
                "evaluation_level": self._get_evaluation_level(overall_score),
                "strengths": self._extract_strengths(detailed_feedback),
                "weaknesses": self._extract_weaknesses(detailed_feedback)
            }
            
            self.logger.info(f"面试评估完成: {session_data.get('session_id')}, 总分: {overall_score}")
            
            return evaluation_result
            
        except Exception as e:
            self.logger.error(f"面试评估失败: {e}")
            return {
                "status": "error",
                "message": f"评估失败: {str(e)}"
            }
    
    def _evaluate_dimension(self, conversation_history: List[Dict], dimension: str) -> tuple[float, str]:
        """评估单个维度"""
        try:
            # 构建对话上下文
            context = self._build_evaluation_context(conversation_history)
            
            # 根据维度生成评估提示
            evaluation_prompt = self._get_dimension_prompt(dimension, context)
            
            # 调用LLM进行评估
            response = self.llm.invoke(
                evaluation_prompt,
                temperature=0.3,
                max_tokens=400
            )
            
            # 解析评分和反馈
            score, feedback = self._parse_evaluation_response(response.content)
            
            return score, feedback
            
        except Exception as e:
            self.logger.error(f"维度评估失败 {dimension}: {e}")
            return 6.0, f"评估失败: {str(e)}"
    
    def _get_dimension_prompt(self, dimension: str, context: str) -> str:
        """获取维度评估提示"""
        prompts = {
            "technical_accuracy": f"""
请基于以下面试对话，评估候选人的技术准确性：

{context}

评估标准：
- 10-9分：技术概念理解准确，回答专业深入
- 8-7分：技术理解基本正确，有少量小错误
- 6-5分：技术理解一般，有一些明显错误
- 4-3分：技术理解较差，错误较多
- 2-1分：技术概念基本不理解

请按以下格式回答：
评分：X.X分
理由：具体的评估理由和依据
            """,
            
            "communication": f"""
请基于以下面试对话，评估候选人的沟通表达能力：

{context}

评估标准：
- 10-9分：表达清晰准确，逻辑性强，用词得当
- 8-7分：表达较清晰，逻辑基本合理
- 6-5分：表达一般，逻辑有些混乱
- 4-3分：表达不够清晰，逻辑性差
- 2-1分：表达混乱，难以理解

请按以下格式回答：
评分：X.X分  
理由：具体的评估理由和依据
            """,
            
            "problem_solving": f"""
请基于以下面试对话，评估候选人的问题解决能力：

{context}

评估标准：
- 10-9分：思路清晰，能系统性分析和解决问题
- 8-7分：有一定的问题分析能力
- 6-5分：问题解决思路一般
- 4-3分：问题分析能力较弱
- 2-1分：缺乏系统的问题解决思维

请按以下格式回答：
评分：X.X分
理由：具体的评估理由和依据
            """,
            
            "experience_depth": f"""
请基于以下面试对话，评估候选人的经验深度：

{context}

评估标准：
- 10-9分：有丰富的实践经验，能深入分享项目细节
- 8-7分：有一定的实践经验
- 6-5分：经验一般，缺乏深度
- 4-3分：实践经验较少
- 2-1分：几乎没有相关经验

请按以下格式回答：
评分：X.X分
理由：具体的评估理由和依据
            """,
            
            "learning_ability": f"""
请基于以下面试对话，评估候选人的学习能力：

{context}

评估标准：
- 10-9分：展现出强烈的学习意愿和快速学习能力
- 8-7分：有一定的学习能力和成长意识
- 6-5分：学习能力一般
- 4-3分：学习意愿不强
- 2-1分：缺乏学习能力和成长意识

请按以下格式回答：
评分：X.X分
理由：具体的评估理由和依据
            """
        }
        
        return prompts.get(dimension, prompts["technical_accuracy"])
    
    def _build_evaluation_context(self, conversation_history: List[Dict]) -> str:
        """构建评估上下文"""
        context_lines = []
        for msg in conversation_history:
            if msg["role"] == "user":
                context_lines.append(f"候选人: {msg['content']}")
            elif msg["role"] == "assistant":
                context_lines.append(f"面试官: {msg['content']}")
        
        return "\n".join(context_lines)
    
    def _parse_evaluation_response(self, response_content: str) -> tuple[float, str]:
        """解析评估响应"""
        try:
            # 尝试提取评分
            score_match = re.search(r'评分[：:]\s*(\d+(?:\.\d+)?)', response_content)
            if score_match:
                score = float(score_match.group(1))
                score = max(1.0, min(10.0, score))  # 限制在1-10分范围内
            else:
                score = 6.0  # 默认分数
            
            # 提取理由
            reason_match = re.search(r'理由[：:]\s*(.+)', response_content, re.DOTALL)
            if reason_match:
                feedback = reason_match.group(1).strip()
            else:
                feedback = response_content.strip()
            
            return score, feedback
            
        except Exception as e:
            self.logger.error(f"解析评估响应失败: {e}")
            return 6.0, response_content.strip()
    
    def _calculate_overall_score(self, dimension_scores: Dict[str, float]) -> float:
        """计算总体得分"""
        total_weighted_score = 0
        total_weight = 0
        
        for dimension, score in dimension_scores.items():
            if dimension in self.evaluation_dimensions:
                weight = self.evaluation_dimensions[dimension]["weight"]
                total_weighted_score += score * weight
                total_weight += weight
        
        if total_weight > 0:
            overall_score = total_weighted_score / total_weight
        else:
            overall_score = 6.0
        
        return round(overall_score, 1)
    
    def _generate_comprehensive_feedback(self, conversation_history: List[Dict], 
                                       dimension_scores: Dict[str, float], 
                                       overall_score: float) -> str:
        """生成综合评价"""
        try:
            context = self._build_evaluation_context(conversation_history)
            
            feedback_prompt = f"""
基于以下面试对话和各维度评分，生成综合评价：

面试对话：
{context}

各维度得分：
{json.dumps(dimension_scores, ensure_ascii=False, indent=2)}

总体得分：{overall_score}分

请生成一个客观、专业、建设性的综合评价，包括：
1. 候选人的整体表现概述
2. 主要优势和亮点
3. 需要改进的地方
4. 总体印象和建议

评价应该具体、有针对性，避免空泛的表述。
            """
            
            response = self.llm.invoke(
                feedback_prompt,
                temperature=0.6,
                max_tokens=600
            )
            
            return response.content.strip()
            
        except Exception as e:
            self.logger.error(f"生成综合评价失败: {e}")
            return f"候选人总体得分为{overall_score}分，表现一般，建议继续努力提升。"
    
    def _generate_improvement_suggestions(self, dimension_scores: Dict[str, float], 
                                        detailed_feedback: Dict[str, str]) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # 找出得分较低的维度
        low_score_dimensions = []
        for dimension, score in dimension_scores.items():
            if score < 7.0:  # 低于7分的维度
                dimension_name = self.evaluation_dimensions[dimension]["name"]
                low_score_dimensions.append((dimension, dimension_name, score))
        
        # 为低分维度生成建议
        for dimension, name, score in sorted(low_score_dimensions, key=lambda x: x[2]):
            suggestion = self._get_improvement_suggestion(dimension, score)
            suggestions.append(f"{name}：{suggestion}")
        
        # 如果没有低分维度，给出通用建议
        if not suggestions:
            suggestions = [
                "继续保持当前的优秀表现",
                "可以进一步拓展技术广度和深度",
                "多参与实际项目提升经验"
            ]
        
        return suggestions[:5]  # 最多返回5个建议
    
    def _get_improvement_suggestion(self, dimension: str, score: float) -> str:
        """获取特定维度的改进建议"""
        suggestions = {
            "technical_accuracy": [
                "加强基础技术概念的学习和理解",
                "多阅读技术文档和最佳实践",
                "通过实际项目验证和加深技术理解"
            ],
            "communication": [
                "练习技术概念的清晰表达",
                "培养逻辑性思维和表达习惯",
                "多参与技术分享和讨论"
            ],
            "problem_solving": [
                "培养系统性的问题分析方法",
                "多练习算法和数据结构题目",
                "学习设计模式和架构思维"
            ],
            "experience_depth": [
                "积极参与更多实际项目",
                "深入了解项目的技术细节和业务背景",
                "总结和分享项目经验"
            ],
            "learning_ability": [
                "培养持续学习的习惯",
                "关注技术发展趋势",
                "建立自己的知识管理体系"
            ]
        }
        
        dimension_suggestions = suggestions.get(dimension, ["继续努力提升"])
        
        if score < 4.0:
            return f"{dimension_suggestions[0]}，建议从基础开始系统性学习"
        elif score < 6.0:
            return f"{dimension_suggestions[1] if len(dimension_suggestions) > 1 else dimension_suggestions[0]}"
        else:
            return f"{dimension_suggestions[-1] if len(dimension_suggestions) > 2 else dimension_suggestions[0]}"
    
    def _get_evaluation_level(self, overall_score: float) -> str:
        """获取评估等级"""
        if overall_score >= 9.0:
            return "优秀"
        elif overall_score >= 8.0:
            return "良好"
        elif overall_score >= 7.0:
            return "中等"
        elif overall_score >= 6.0:
            return "一般"
        else:
            return "需要改进"
    
    def _extract_strengths(self, detailed_feedback: Dict[str, str]) -> List[str]:
        """提取优势点"""
        strengths = []
        
        # 简化版的优势提取，实际可以使用NLP技术
        for dimension, feedback in detailed_feedback.items():
            if any(word in feedback for word in ["优秀", "突出", "很好", "准确", "清晰"]):
                dimension_name = self.evaluation_dimensions[dimension]["name"]
                strengths.append(f"{dimension_name}表现突出")
        
        if not strengths:
            strengths = ["具备基本的技术能力"]
            
        return strengths[:3]  # 最多返回3个优势
    
    def _extract_weaknesses(self, detailed_feedback: Dict[str, str]) -> List[str]:
        """提取弱点"""
        weaknesses = []
        
        # 简化版的弱点提取
        for dimension, feedback in detailed_feedback.items():
            if any(word in feedback for word in ["不足", "缺乏", "较差", "需要", "改进"]):
                dimension_name = self.evaluation_dimensions[dimension]["name"]
                weaknesses.append(f"{dimension_name}有待提升")
        
        return weaknesses[:3]  # 最多返回3个弱点
