"""
Gradio前端应用主文件
基于DeepSeek的AI智能面试官系统
"""

import gradio as gr
import os
import sys
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backend.utils.config import load_config
from backend.utils.logger import get_logger, InterviewLogger
from backend.models.deepseek_model import DeepSeekLLM
from backend.models.bge_embedding import BGEEmbedding

class InterviewSession:
    """面试会话管理类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session_id = str(uuid.uuid4())
        self.logger = InterviewLogger(self.session_id)
        
        # 初始化模型
        self.llm = DeepSeekLLM(config)
        self.embedding = BGEEmbedding(config)
        
        # 会话状态
        self.mode = "basic"
        self.difficulty = "medium"
        self.chat_history = []
        self.interview_data = {
            "start_time": None,
            "end_time": None,
            "questions_count": 0,
            "user_profile": {},
            "performance_scores": []
        }
        
        # 面试阶段
        self.current_phase = "greeting"  # greeting, technical, experience, closing
        self.phase_questions = {
            "greeting": ["请先简单介绍一下自己", "说说你的技术背景和工作经验"],
            "technical": ["基础技术问题", "深度技术讨论"],
            "experience": ["项目经验", "实际应用场景"],
            "closing": ["职业规划", "问题答疑"]
        }
    
    def start_interview(self, mode: str, resume_text: str = "", jd_text: str = "") -> str:
        """开始面试"""
        try:
            self.mode = mode
            self.interview_data["start_time"] = datetime.now()
            self.interview_data["mode"] = mode
            
            # 处理简历和JD
            if resume_text:
                self.interview_data["user_profile"]["resume"] = resume_text
            if jd_text:
                self.interview_data["user_profile"]["jd"] = jd_text
            
            # 生成开场白
            system_prompt = self._get_interviewer_system_prompt()
            greeting_prompt = f"""
            你是一位专业的面试官，现在开始进行{mode}面试。
            
            面试信息：
            - 面试模式：{mode}
            - 简历信息：{resume_text[:200] if resume_text else '未提供'}
            - 职位要求：{jd_text[:200] if jd_text else '未提供'}
            
            请用友好专业的语气开始面试，简短介绍面试流程，然后提出第一个问题。
            """
            
            response = self.llm.invoke(greeting_prompt, system_prompt=system_prompt)
            welcome_message = response.content
            
            # 记录日志
            self.logger.log_session_start(mode, {
                "has_resume": bool(resume_text),
                "has_jd": bool(jd_text)
            })
            
            return welcome_message
            
        except Exception as e:
            self.logger.log_error(e, "面试启动")
            return f"面试启动失败：{str(e)}"
    
    def process_user_input(self, user_input: str) -> str:
        """处理用户输入"""
        try:
            # 分析用户回答
            answer_analysis = self._analyze_answer(user_input)
            
            # 生成下一个问题
            next_question = self._generate_next_question(user_input, answer_analysis)
            
            # 更新会话状态
            self.interview_data["questions_count"] += 1
            self.interview_data["performance_scores"].append(answer_analysis)
            
            # 记录日志
            self.logger.log_answer(user_input, answer_analysis)
            self.logger.log_question(next_question, self.difficulty, self.mode)
            
            return next_question
            
        except Exception as e:
            self.logger.log_error(e, "处理用户输入")
            return "抱歉，系统出现问题，让我们继续讨论其他话题。"
    
    def end_interview(self) -> Dict[str, Any]:
        """结束面试并生成报告"""
        try:
            self.interview_data["end_time"] = datetime.now()
            
            # 生成面试报告
            report = self._generate_interview_report()
            
            # 保存会话数据
            self._save_session_data()
            
            # 记录日志
            self.logger.log_session_end(report)
            
            return report
            
        except Exception as e:
            self.logger.log_error(e, "结束面试")
            return {"error": f"报告生成失败：{str(e)}"}
    
    def _get_interviewer_system_prompt(self) -> str:
        """获取面试官系统提示"""
        return f"""
        你是一位经验丰富的技术面试官，正在进行{self.mode}模式的面试。
        
        面试要求：
        1. 保持专业、友好、鼓励的态度
        2. 问题要有层次性，从基础到进阶
        3. 根据候选人回答调整问题难度
        4. 适时进行追问和深入讨论
        5. 当前难度级别：{self.difficulty}
        
        面试流程：
        - 开场问候和自我介绍（2-3分钟）
        - 基础技能评估（10-15分钟）
        - 深度技术讨论（15-20分钟）
        - 项目经验挖掘（10-15分钟）
        - 结束总结和答疑（5分钟）
        
        注意事项：
        - 每次只问一个问题
        - 给出适当的反馈和鼓励
        - 问题要具体可回答，避免过于宽泛
        - 根据回答质量动态调整难度
        """
    
    def _analyze_answer(self, answer: str) -> Dict[str, Any]:
        """分析回答质量"""
        prompt = f"""
        请分析以下面试回答的质量，从多个维度进行客观评分：
        
        回答内容：{answer}
        
        评分维度（1-10分）：
        1. 技术准确性：回答是否技术正确
        2. 表达清晰度：是否表达清楚易懂
        3. 深度理解：是否展现深入理解
        4. 实践经验：是否体现实际经验
        5. 逻辑结构：回答是否有逻辑性
        
        请以JSON格式返回，包含：
        - scores: 各维度得分字典
        - overall_score: 综合得分（1-10）
        - strengths: 优点列表
        - improvements: 改进建议列表
        - keywords: 提到的关键技术点
        """
        
        try:
            response = self.llm.invoke(prompt)
            result = json.loads(response.content)
            return result
        except:
            return {
                "scores": {"accuracy": 5, "clarity": 5, "depth": 5, "experience": 5, "logic": 5},
                "overall_score": 5.0,
                "strengths": [],
                "improvements": ["请提供更详细的回答"],
                "keywords": []
            }
    
    def _generate_next_question(self, previous_answer: str, analysis: Dict[str, Any]) -> str:
        """生成下一个问题"""
        # 根据回答质量调整难度
        score = analysis.get("overall_score", 5.0)
        if score > 7.5:
            self.difficulty = "hard"
        elif score < 4.0:
            self.difficulty = "easy"
        else:
            self.difficulty = "medium"
        
        prompt = f"""
        基于候选人的回答，生成下一个合适的面试问题。
        
        候选人回答：{previous_answer}
        回答分析：{analysis}
        当前难度：{self.difficulty}
        面试模式：{self.mode}
        已提问数量：{self.interview_data["questions_count"]}
        
        要求：
        1. 问题要有针对性和连贯性
        2. 难度要匹配候选人水平
        3. 可以是追问、扩展或新话题
        4. 控制在1-2个问题内
        5. 问题要具体可回答
        
        请直接返回问题，不要其他说明。
        """
        
        response = self.llm.invoke(prompt)
        return response.content.strip()
    
    def _generate_interview_report(self) -> Dict[str, Any]:
        """生成面试报告"""
        if not self.interview_data["performance_scores"]:
            return {"error": "没有足够的数据生成报告"}
        
        # 计算总体表现
        scores = self.interview_data["performance_scores"]
        overall_scores = [s.get("overall_score", 0) for s in scores]
        avg_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0
        
        # 计算各维度平均分
        dimensions = ["accuracy", "clarity", "depth", "experience", "logic"]
        dim_scores = {}
        for dim in dimensions:
            dim_values = []
            for score in scores:
                if "scores" in score and dim in score["scores"]:
                    dim_values.append(score["scores"][dim])
            dim_scores[dim] = sum(dim_values) / len(dim_values) if dim_values else 0
        
        # 收集优点和建议
        all_strengths = []
        all_improvements = []
        for score in scores:
            all_strengths.extend(score.get("strengths", []))
            all_improvements.extend(score.get("improvements", []))
        
        # 生成文字总结
        duration = (self.interview_data["end_time"] - self.interview_data["start_time"]).total_seconds() / 60
        
        return {
            "session_id": self.session_id,
            "interview_info": {
                "mode": self.mode,
                "duration_minutes": round(duration, 1),
                "questions_count": self.interview_data["questions_count"],
                "date": self.interview_data["start_time"].strftime("%Y-%m-%d %H:%M")
            },
            "performance": {
                "overall_score": round(avg_score, 2),
                "dimension_scores": {k: round(v, 2) for k, v in dim_scores.items()},
                "score_trend": [round(s, 2) for s in overall_scores]
            },
            "feedback": {
                "strengths": list(set(all_strengths)),
                "improvements": list(set(all_improvements))
            }
        }
    
    def _save_session_data(self):
        """保存会话数据"""
        try:
            from backend.utils.config import config
            
            # 创建会话目录
            session_dir = config.CHAT_HISTORY_DIR / self.session_id
            session_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存会话数据
            session_file = session_dir / "session_data.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                # 序列化datetime对象
                data = self.interview_data.copy()
                for key in ["start_time", "end_time"]:
                    if data.get(key):
                        data[key] = data[key].isoformat()
                
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 保存聊天记录
            chat_file = session_dir / "chat_history.txt"
            with open(chat_file, 'w', encoding='utf-8') as f:
                for msg in self.chat_history:
                    f.write(f"{msg}\n")
                    
        except Exception as e:
            self.logger.log_error(e, "保存会话数据")

class GradioInterviewApp:
    """Gradio面试应用主类"""
    
    def __init__(self):
        # 加载配置
        self.config = load_config()
        self.logger = get_logger(__name__)
        
        # 当前会话
        self.current_session: Optional[InterviewSession] = None
        
        # 验证配置
        self._validate_setup()
    
    def _validate_setup(self):
        """验证系统配置"""
        try:
            # 测试DeepSeek连接
            llm = DeepSeekLLM(self.config)
            if not llm.validate_connection():
                raise Exception("DeepSeek API连接失败")
            
            # 测试BGE模型
            embedding = BGEEmbedding(self.config)
            if not embedding.validate_model():
                raise Exception("BGE模型加载失败")
            
            self.logger.info("系统配置验证通过")
            
        except Exception as e:
            self.logger.error(f"系统配置验证失败: {e}")
            raise
    
    def start_interview(self, mode: str, resume_file, jd_file) -> Tuple[str, List]:
        """启动面试"""
        try:
            # 创建新会话
            self.current_session = InterviewSession(self.config)
            
            # 处理上传文件
            resume_text = ""
            jd_text = ""
            
            if resume_file:
                resume_text = self._process_uploaded_file(resume_file)
            
            if jd_file:
                jd_text = self._process_uploaded_file(jd_file)
            
            # 开始面试
            welcome_message = self.current_session.start_interview(mode, resume_text, jd_text)
            
            # 初始化聊天历史 (使用OpenAI格式)
            chat_history = [{"role": "assistant", "content": welcome_message}]
            
            return welcome_message, chat_history
            
        except Exception as e:
            error_msg = f"面试启动失败：{str(e)}"
            self.logger.error(error_msg)
            return error_msg, []
    
    def chat_response(self, message: str, history: List) -> Tuple[str, List]:
        """处理聊天响应"""
        if not self.current_session:
            return "", history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": "请先开始面试"}
            ]
        
        try:
            # 获取AI响应
            ai_response = self.current_session.process_user_input(message)
            
            # 更新聊天历史 (使用OpenAI格式)
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": ai_response})
            
            return "", history
            
        except Exception as e:
            error_msg = f"系统错误：{str(e)}"
            self.logger.error(error_msg)
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": error_msg})
            return "", history
    
    def end_interview_session(self) -> str:
        """结束面试会话"""
        if not self.current_session:
            return "没有进行中的面试"
        
        try:
            # 生成报告
            report = self.current_session.end_interview()
            
            # 格式化报告
            formatted_report = self._format_report(report)
            
            # 清理会话
            self.current_session = None
            
            return formatted_report
            
        except Exception as e:
            error_msg = f"面试结束失败：{str(e)}"
            self.logger.error(error_msg)
            return error_msg
    
    def _process_uploaded_file(self, file) -> str:
        """处理上传文件"""
        if not file:
            return ""
        
        try:
            # 读取文件内容
            if hasattr(file, 'name'):
                file_path = file.name
            else:
                file_path = str(file)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return content[:2000]  # 限制长度
            
        except Exception as e:
            self.logger.error(f"文件处理失败: {e}")
            return ""
    
    def _format_report(self, report: Dict[str, Any]) -> str:
        """格式化面试报告"""
        if "error" in report:
            return report["error"]
        
        try:
            formatted = f"""
# 📋 面试评估报告

## 📊 基本信息
- **面试编号**: {report['session_id'][:8]}
- **面试日期**: {report['interview_info']['date']}
- **面试模式**: {report['interview_info']['mode']}
- **面试时长**: {report['interview_info']['duration_minutes']} 分钟
- **问题数量**: {report['interview_info']['questions_count']} 个

## 🎯 综合评估
**总体得分**: {report['performance']['overall_score']}/10.0

### 各维度得分
"""
            
            # 添加维度得分
            dimension_names = {
                "accuracy": "技术准确性",
                "clarity": "表达清晰度", 
                "depth": "深度理解",
                "experience": "实践经验",
                "logic": "逻辑结构"
            }
            
            for dim, score in report['performance']['dimension_scores'].items():
                name = dimension_names.get(dim, dim)
                formatted += f"- **{name}**: {score}/10.0\n"
            
            # 添加优点和建议
            formatted += f"""
## ✅ 表现优点
"""
            for strength in report['feedback']['strengths'][:5]:  # 限制数量
                formatted += f"- {strength}\n"
            
            formatted += f"""
## 📈 改进建议
"""
            for improvement in report['feedback']['improvements'][:5]:
                formatted += f"- {improvement}\n"
            
            # 添加得分趋势
            if len(report['performance']['score_trend']) > 1:
                formatted += f"""
## 📈 表现趋势
得分变化: {' → '.join(map(str, report['performance']['score_trend']))}
"""
            
            return formatted
            
        except Exception as e:
            self.logger.error(f"报告格式化失败: {e}")
            return "报告生成失败"

def create_interview_interface():
    """创建Gradio界面"""
    
    app = GradioInterviewApp()
    
    # 自定义CSS
    custom_css = """
    .main-header {
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .interview-panel {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .chat-container {
        min-height: 500px;
        max-height: 600px;
        border: 2px solid #e9ecef;
        border-radius: 10px;
    }
    
    .status-indicator {
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 0.5rem 0;
    }
    
    .status-ready { background: #d4edda; color: #155724; }
    .status-active { background: #cce5ff; color: #004085; }
    .status-ended { background: #f8d7da; color: #721c24; }
    """
    
    with gr.Blocks(
        theme=gr.themes.Soft(),
        title="AI智能面试官",
        css=custom_css
    ) as interface:
        
        # 状态管理
        session_state = gr.State(value={"status": "ready", "session_id": None})
        
        # 主标题
        gr.HTML("""
        <div class="main-header">
            <h1>🤖 AI智能面试官系统</h1>
            <p>基于DeepSeek大模型 + BGE嵌入 + LangChain Agent架构</p>
            <p><strong>专业 | 智能 | 客观 | 高效</strong></p>
        </div>
        """)
        
        with gr.Tab("🚀 面试设置", elem_id="setup-tab"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.HTML('<div class="interview-panel">')
                    
                    mode_radio = gr.Radio(
                        choices=[
                            ("基础面试", "basic"),
                            ("JD定向面试", "jd_based"), 
                            ("简历匹配面试", "resume_based")
                        ],
                        value="basic",
                        label="📋 面试模式",
                        info="选择适合的面试类型"
                    )
                    
                    with gr.Group():
                        resume_file = gr.File(
                            label="📄 上传简历 (可选)",
                            file_types=[".txt", ".md", ".pdf"],
                            visible=False
                        )
                        
                        jd_file = gr.File(
                            label="📋 上传职位描述 (可选)",
                            file_types=[".txt", ".md", ".pdf"],
                            visible=False
                        )
                    
                    start_button = gr.Button(
                        "🎯 开始面试",
                        variant="primary",
                        size="lg"
                    )
                    
                    gr.HTML('</div>')
                
                with gr.Column(scale=2):
                    status_display = gr.HTML(
                        '<div class="status-indicator status-ready">系统就绪，等待开始面试</div>'
                    )
                    
                    setup_info = gr.Textbox(
                        label="📢 系统消息",
                        lines=8,
                        interactive=False,
                        placeholder="面试开始后，这里将显示面试官的开场白..."
                    )
            
            # 根据模式更新文件上传组件显示
            def update_file_uploads(mode):
                return {
                    resume_file: gr.update(visible=mode == "resume_based"),
                    jd_file: gr.update(visible=mode == "jd_based")
                }
            
            mode_radio.change(
                update_file_uploads,
                inputs=[mode_radio],
                outputs=[resume_file, jd_file]
            )
        
        with gr.Tab("💬 面试进行", elem_id="interview-tab"):
            with gr.Row():
                with gr.Column():
                    chatbot = gr.Chatbot(
                        label="🎙️ 面试对话",
                        elem_classes=["chat-container"],
                        bubble_full_width=False,
                        show_copy_button=True,
                        avatar_images=["👤", "🤖"],
                        type="messages"
                    )
                    
                    with gr.Row():
                        user_input = gr.Textbox(
                            placeholder="💭 输入您的回答... (支持Shift+Enter换行)",
                            lines=3,
                            scale=5,
                            show_label=False
                        )
                        
                        with gr.Column(scale=1):
                            send_button = gr.Button("📤 发送", variant="primary")
                            clear_button = gr.Button("🧹 清空")
                    
                    with gr.Row():
                        end_button = gr.Button(
                            "🏁 结束面试", 
                            variant="stop",
                            size="lg"
                        )
                        
                        interview_tips = gr.HTML("""
                        <div style="padding: 1rem; background: #e7f3ff; border-radius: 8px; font-size: 0.9em;">
                            💡 <strong>面试小贴士：</strong><br>
                            • 回答要具体、有逻辑<br>
                            • 可以举例说明实际经验<br>
                            • 不懂的问题可以诚实表达
                        </div>
                        """)
        
        with gr.Tab("📊 面试报告", elem_id="report-tab"):
            with gr.Row():
                with gr.Column():
                    report_display = gr.Markdown(
                        value="📋 面试结束后，详细的评估报告将在此显示...",
                        label="面试评估报告"
                    )
                    
                    with gr.Row():
                        refresh_report = gr.Button("🔄 刷新报告")
                        download_report = gr.Button("💾 导出报告", visible=False)
        
        # 事件处理函数
        def start_interview_handler(mode, resume, jd):
            try:
                message, history = app.start_interview(mode, resume, jd)
                status = '<div class="status-indicator status-active">面试进行中...</div>'
                return message, history, status
            except Exception as e:
                error_msg = f"启动失败：{str(e)}"
                status = '<div class="status-indicator status-ended">启动失败</div>'
                return error_msg, [], status
        
        def send_message_handler(message, history):
            if not message.strip():
                return "", history
            return app.chat_response(message, history)
        
        def end_interview_handler():
            try:
                report = app.end_interview_session()
                status = '<div class="status-indicator status-ended">面试已结束</div>'
                return report, status, []
            except Exception as e:
                return f"结束失败：{str(e)}", status_display.value, []
        
        # 绑定事件
        start_button.click(
            start_interview_handler,
            inputs=[mode_radio, resume_file, jd_file],
            outputs=[setup_info, chatbot, status_display]
        )
        
        send_button.click(
            send_message_handler,
            inputs=[user_input, chatbot],
            outputs=[user_input, chatbot]
        )
        
        user_input.submit(
            send_message_handler,
            inputs=[user_input, chatbot],
            outputs=[user_input, chatbot]
        )
        
        end_button.click(
            end_interview_handler,
            outputs=[report_display, status_display, chatbot]
        )
        
        clear_button.click(
            lambda: ([], ""),
            outputs=[chatbot, user_input]
        )
    
    return interface

if __name__ == "__main__":
    try:
        # 创建界面
        interface = create_interview_interface()
        
        # 启动应用
        interface.launch(
            server_name="127.0.0.1",
            server_port=7860,
            share=False,
            show_error=True,
            favicon_path=None,
            auth=None
        )
        
    except Exception as e:
        print(f"应用启动失败: {e}")
        sys.exit(1)
