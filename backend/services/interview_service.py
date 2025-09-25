"""
面试服务模块
提供面试流程管理和问题生成功能
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import uuid
from pathlib import Path

from backend.utils.logger import get_logger
from backend.models.deepseek_model import DeepSeekLLM
from backend.models.bge_embedding import BGEEmbedding


class InterviewService:
    """面试服务类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)
        
        # 初始化模型
        self.llm = DeepSeekLLM(config)
        self.embedding = BGEEmbedding(config)
        
        # 面试模板
        self.interview_templates = {
            "basic": self._get_basic_template(),
            "jd_based": self._get_jd_template(), 
            "resume_based": self._get_resume_template()
        }
        
    def _get_basic_template(self) -> str:
        """获取基础面试模板"""
        return """你是一位专业的AI面试官，负责进行技术面试。请遵循以下原则：

1. **面试风格**：
   - 保持专业、友好、客观的态度
   - 循序渐进，从基础到深入
   - 根据候选人回答调整问题难度

2. **问题类型**：
   - 基础技术概念（30%）
   - 实际项目经验（40%）
   - 问题解决能力（20%）
   - 职业发展规划（10%）

3. **评估维度**：
   - 技术准确性：概念理解是否正确
   - 表达清晰度：表达是否清晰有条理
   - 深度理解：是否有深入思考
   - 实践经验：是否有实际项目经验
   - 逻辑思维：思路是否清晰合理

4. **面试流程**：
   - 开场：简短自我介绍和面试说明
   - 技术提问：3-5个递进式问题
   - 经验探讨：项目经验深入了解
   - 结尾：职业规划和问题答疑

请开始面试，先进行简短的开场白。"""

    def _get_jd_template(self) -> str:
        """获取基于JD的面试模板"""
        return """你是一位专业的AI面试官，将根据以下职位描述进行针对性面试：

{jd_content}

**面试重点**：
1. 针对JD中的技能要求进行深入考察
2. 了解候选人在相关技术栈的实际经验
3. 评估候选人与岗位的匹配度
4. 探讨候选人对该岗位的理解和兴趣

**面试策略**：
- 优先考察JD中明确要求的核心技能
- 根据岗位级别调整问题难度
- 关注候选人的学习能力和成长潜力
- 了解候选人对公司和行业的认知

请开始面试，结合职位要求进行开场。"""

    def _get_resume_template(self) -> str:
        """获取基于简历的面试模板"""
        return """你是一位专业的AI面试官，将基于候选人的简历进行个性化面试：

{resume_content}

**面试重点**：
1. 深入了解简历中提到的项目经验
2. 验证技能声明的真实性和深度
3. 探讨职业发展轨迹和选择理由
4. 了解候选人的优势和成长空间

**提问策略**：
- 针对简历中的具体项目深入提问
- 验证技术技能的实际掌握程度
- 了解工作经历中的成果和挑战
- 探讨未来职业规划的合理性

请开始面试，基于候选人简历进行个性化开场。"""

    def start_interview(self, mode: str, resume_content: str = "", jd_content: str = "") -> Dict[str, Any]:
        """开始面试"""
        try:
            session_id = str(uuid.uuid4())
            
            # 选择面试模板
            template = self.interview_templates.get(mode, self.interview_templates["basic"])
            
            # 根据模式填充模板
            if mode == "jd_based" and jd_content:
                system_prompt = template.format(jd_content=jd_content)
            elif mode == "resume_based" and resume_content:
                system_prompt = template.format(resume_content=resume_content)
            else:
                system_prompt = template
            
            # 生成开场白
            welcome_response = self.llm.invoke(
                "请生成面试开场白，介绍面试流程并开始第一个问题。",
                system_prompt=system_prompt,
                temperature=0.8,
                max_tokens=500
            )
            
            # 创建面试会话
            interview_session = {
                "session_id": session_id,
                "mode": mode,
                "start_time": datetime.now().isoformat(),
                "status": "active",
                "system_prompt": system_prompt,
                "conversation_history": [
                    {
                        "role": "assistant",
                        "content": welcome_response.content,
                        "timestamp": datetime.now().isoformat()
                    }
                ],
                "metadata": {
                    "resume_content": resume_content,
                    "jd_content": jd_content,
                    "question_count": 1,
                    "scores": []
                }
            }
            
            self.logger.info(f"面试会话已创建: {session_id}")
            
            return {
                "session_id": session_id,
                "welcome_message": welcome_response.content,
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"面试启动失败: {e}")
            return {
                "status": "error",
                "message": f"面试启动失败: {str(e)}"
            }
    
    def continue_interview(self, session_id: str, user_response: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """继续面试对话"""
        try:
            # 更新对话历史
            session_data["conversation_history"].append({
                "role": "user",
                "content": user_response,
                "timestamp": datetime.now().isoformat()
            })
            
            # 构建对话上下文
            conversation_context = self._build_conversation_context(session_data["conversation_history"])
            
            # 生成面试官回应
            interviewer_response = self.llm.invoke(
                f"候选人回答：{user_response}\n\n请给出专业的面试官回应，包括对答案的简短评价和下一个问题。",
                system_prompt=session_data["system_prompt"] + f"\n\n对话历史：\n{conversation_context}",
                temperature=0.7,
                max_tokens=600
            )
            
            # 更新会话数据
            session_data["conversation_history"].append({
                "role": "assistant", 
                "content": interviewer_response.content,
                "timestamp": datetime.now().isoformat()
            })
            session_data["metadata"]["question_count"] += 1
            
            # 检查是否应该结束面试
            should_end = self._should_end_interview(session_data)
            
            if should_end:
                session_data["status"] = "completed"
                session_data["end_time"] = datetime.now().isoformat()
            
            self.logger.info(f"面试对话继续: {session_id}, 问题数: {session_data['metadata']['question_count']}")
            
            return {
                "session_id": session_id,
                "interviewer_response": interviewer_response.content,
                "should_end": should_end,
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"面试对话失败: {e}")
            return {
                "status": "error",
                "message": f"面试对话失败: {str(e)}"
            }
    
    def _build_conversation_context(self, conversation_history: List[Dict]) -> str:
        """构建对话上下文"""
        context_lines = []
        for msg in conversation_history[-6:]:  # 只保留最近6轮对话
            role = "面试官" if msg["role"] == "assistant" else "候选人"
            context_lines.append(f"{role}: {msg['content']}")
        return "\n".join(context_lines)
    
    def _should_end_interview(self, session_data: Dict[str, Any]) -> bool:
        """判断是否应该结束面试"""
        max_questions = self.config.get("interview", {}).get("max_questions", 8)
        current_questions = session_data["metadata"]["question_count"]
        
        # 基于问题数量判断
        if current_questions >= max_questions:
            return True
        
        # 基于时间判断（可选）
        start_time = datetime.fromisoformat(session_data["start_time"])
        duration_minutes = (datetime.now() - start_time).total_seconds() / 60
        max_duration = self.config.get("interview", {}).get("max_duration_minutes", 30)
        
        if duration_minutes >= max_duration:
            return True
            
        return False
    
    def get_interview_summary(self, session_data: Dict[str, Any]) -> str:
        """生成面试总结"""
        try:
            conversation_context = self._build_conversation_context(session_data["conversation_history"])
            
            summary_prompt = f"""基于以下面试对话，生成面试总结：

对话内容：
{conversation_context}

请生成包含以下内容的总结：
1. 候选人整体表现概述
2. 主要优势和亮点
3. 需要改进的地方
4. 对该候选人的初步评价

总结应客观、专业、建设性。"""

            summary_response = self.llm.invoke(
                summary_prompt,
                temperature=0.6,
                max_tokens=800
            )
            
            return summary_response.content
            
        except Exception as e:
            self.logger.error(f"生成面试总结失败: {e}")
            return "面试总结生成失败"
