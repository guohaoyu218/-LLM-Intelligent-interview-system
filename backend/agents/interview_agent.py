"""
面试官智能体
基于DeepSeek模型，负责面试互动和问题生成
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from backend.utils.logger import get_logger
from backend.models.deepseek_model import DeepSeekLLM

class InterviewAgent:
    """面试官智能体"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)
        self.model = DeepSeekLLM(config)
        
        # 面试阶段
        self.interview_phases = {
            "greeting": {
                "name": "开场与自我介绍",
                "duration": 5,  # 分钟
                "questions": ["请简单介绍一下自己", "谈谈你的技术背景"]
            },
            "technical": {
                "name": "技术能力评估",
                "duration": 20,
                "questions": []  # 动态生成技术问题
            },
            "project": {
                "name": "项目经验讨论",
                "duration": 15,
                "questions": ["描述一个你最有挑战的项目", "在项目中遇到过什么技术难题"]
            },
            "scenario": {
                "name": "场景设计",
                "duration": 10,
                "questions": []  # 动态生成场景题
            },
            "closing": {
                "name": "总结与答疑",
                "duration": 5,
                "questions": ["你有什么想问我的吗", "谈谈你对这个职位的看法"]
            }
        }
        
        # 面试配置
        self.interview_config = {
            "max_questions": 15,
            "min_questions": 8,
            "follow_up_threshold": 0.7,  # 触发追问的阈值
            "difficulty_levels": ["easy", "medium", "hard"]
        }
        
        # 当前状态
        self.current_phase = "greeting"
        self.current_difficulty = "medium"
        self.questions_asked = 0
        self.phase_history = []
    
    def start_interview(self, mode: str, resume_text: str = "", jd_text: str = "") -> Dict[str, Any]:
        """开始面试会话"""
        try:
            # 构建系统提示词
            system_prompt = self._build_system_prompt(mode, resume_text, jd_text)
            
            # 生成开场白
            prompt = """请生成一个专业、友好的面试开场白，包括：
1. 简短的自我介绍
2. 面试流程说明
3. 第一个问题

注意：
- 保持专业性和友好度
- 说明面试预计时长
- 从简单问题开始"""

            response = self.model.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7
            )
            
            # 初始化面试状态
            self.current_phase = "greeting"
            self.questions_asked = 1
            self.phase_history = ["greeting"]
            
            return {
                "status": "success",
                "welcome_message": response["content"],
                "current_phase": self.current_phase,
                "current_difficulty": self.current_difficulty
            }
            
        except Exception as e:
            self.logger.error(f"面试启动失败: {str(e)}")
            raise
    
    def process_answer(self, 
                      answer: str, 
                      conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """处理候选人的回答并生成下一个问题"""
        try:
            # 分析回答
            analysis = self._analyze_answer(answer, conversation_history)
            
            # 更新难度
            self._adjust_difficulty(analysis["score"])
            
            # 决定是否需要追问
            if self._should_follow_up(analysis):
                next_question = self._generate_follow_up(answer, analysis)
            else:
                # 检查是否需要切换阶段
                if self._should_change_phase(analysis):
                    self._move_to_next_phase()
                next_question = self._generate_next_question(conversation_history)
            
            self.questions_asked += 1
            
            return {
                "status": "success",
                "next_question": next_question,
                "analysis": analysis,
                "current_phase": self.current_phase,
                "current_difficulty": self.current_difficulty,
                "should_end": self._should_end_interview()
            }
            
        except Exception as e:
            self.logger.error(f"回答处理失败: {str(e)}")
            raise
    
    def _build_system_prompt(self, mode: str, resume_text: str = "", jd_text: str = "") -> str:
        """构建系统提示词"""
        base_prompt = """你是一位经验丰富的技术面试官，需要：
1. 保持专业、友好的态度
2. 根据候选人水平调整问题难度
3. 对重要知识点进行追问
4. 注意考察实践经验
5. 关注问题解决能力

面试原则：
- 每次只问一个问题
- 给出适当的反馈
- 问题要具体且有引导性
- 循序渐进，由浅入深
"""
        
        if mode == "jd_based" and jd_text:
            base_prompt += f"\n职位要求：\n{jd_text}\n请基于职位要求设计问题。"
        
        if mode == "resume_based" and resume_text:
            base_prompt += f"\n候选人简历：\n{resume_text}\n请基于简历内容进行提问。"
        
        return base_prompt
    
    def _analyze_answer(self, 
                       answer: str, 
                       conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析回答质量"""
        try:
            prompt = f"""请分析以下面试回答：

问题背景：{conversation_history[-2]['content'] if len(conversation_history) >= 2 else ''}
候选人回答：{answer}

请评估：
1. 回答质量（0-10分）
2. 技术理解程度
3. 是否需要追问
4. 下一步建议

返回JSON格式，包含：
- score: 分数
- understanding: 理解程度描述
- needs_follow_up: 是否需要追问
- reasoning: 分析理由
- next_step: 建议的下一步"""

            result = self.model.generate(prompt)
            return json.loads(result["content"])
            
        except Exception as e:
            self.logger.error(f"回答分析失败: {str(e)}")
            return {
                "score": 5,
                "understanding": "无法评估",
                "needs_follow_up": False,
                "reasoning": "分析过程出错",
                "next_step": "继续下一个问题"
            }
    
    def _adjust_difficulty(self, score: float):
        """根据回答评分调整难度"""
        if score >= 8.0:
            self.current_difficulty = "hard"
        elif score <= 4.0:
            self.current_difficulty = "easy"
        else:
            self.current_difficulty = "medium"
    
    def _should_follow_up(self, analysis: Dict[str, Any]) -> bool:
        """判断是否需要追问"""
        return (
            analysis.get("needs_follow_up", False) and
            analysis.get("score", 0) >= self.interview_config["follow_up_threshold"] and
            self.questions_asked < self.interview_config["max_questions"]
        )
    
    def _generate_follow_up(self, answer: str, analysis: Dict[str, Any]) -> str:
        """生成追问"""
        prompt = f"""基于候选人的回答，生成一个深入的追问：

原始回答：{answer}
分析结果：{json.dumps(analysis, ensure_ascii=False)}

要求：
1. 追问要有针对性
2. 考察更深层的理解
3. 关注技术原理
4. 联系实际场景

请直接返回追问问题，不需要其他说明。"""

        response = self.model.generate(prompt)
        return response["content"].strip()
    
    def _should_change_phase(self, analysis: Dict[str, Any]) -> bool:
        """判断是否需要切换面试阶段"""
        current_phase = self.interview_phases[self.current_phase]
        phase_questions = len([p for p in self.phase_history if p == self.current_phase])
        
        return (
            phase_questions >= 3 or  # 当前阶段问题数达到上限
            (analysis.get("score", 0) >= 8 and phase_questions >= 2) or  # 表现优秀可以提前切换
            (analysis.get("score", 0) <= 4 and phase_questions >= 2)  # 表现欠佳也考虑切换
        )
    
    def _move_to_next_phase(self):
        """移动到下一个面试阶段"""
        phase_order = list(self.interview_phases.keys())
        current_index = phase_order.index(self.current_phase)
        
        if current_index < len(phase_order) - 1:
            self.current_phase = phase_order[current_index + 1]
            self.phase_history.append(self.current_phase)
    
    def _generate_next_question(self, conversation_history: List[Dict[str, Any]]) -> str:
        """生成下一个问题"""
        current_phase = self.interview_phases[self.current_phase]
        
        prompt = f"""请生成下一个面试问题：

当前阶段：{current_phase['name']}
当前难度：{self.current_difficulty}
已问问题数：{self.questions_asked}

最近的对话：
{self._format_recent_conversation(conversation_history)}

要求：
1. 问题要符合当前阶段
2. 难度要适中
3. 有针对性和延续性
4. 注重实践和原理结合

请直接返回问题，不需要其他说明。"""

        response = self.model.generate(prompt)
        return response["content"].strip()
    
    def _format_recent_conversation(self, conversation_history: List[Dict[str, Any]], limit: int = 4) -> str:
        """格式化最近的对话记录"""
        recent = conversation_history[-limit:] if len(conversation_history) > limit else conversation_history
        return "\n".join([
            f"{'面试官' if msg['role'] == 'assistant' else '候选人'}: {msg['content']}"
            for msg in recent
        ])
    
    def _should_end_interview(self) -> bool:
        """判断是否应该结束面试"""
        return (
            self.questions_asked >= self.interview_config["max_questions"] or
            (self.questions_asked >= self.interview_config["min_questions"] and 
             self.current_phase == "closing")
        )
