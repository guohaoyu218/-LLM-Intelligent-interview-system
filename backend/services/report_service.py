"""
报告生成服务模块
提供面试报告的生成、格式化和导出功能
"""

from typing import Dict, List, Any, Optional
import json
from datetime import datetime
from pathlib import Path

from backend.utils.logger import get_logger


class ReportService:
    """报告服务类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)
        
        # 报告模板
        self.report_templates = {
            "markdown": self._get_markdown_template(),
            "text": self._get_text_template(),
            "html": self._get_html_template()
        }
    
    def generate_interview_report(self, session_data: Dict[str, Any], 
                                evaluation_result: Dict[str, Any],
                                format_type: str = "markdown") -> Dict[str, Any]:
        """生成面试报告"""
        try:
            # 准备报告数据
            report_data = self._prepare_report_data(session_data, evaluation_result)
            
            # 根据格式生成报告
            if format_type == "markdown":
                report_content = self._generate_markdown_report(report_data)
            elif format_type == "text":
                report_content = self._generate_text_report(report_data)
            elif format_type == "html":
                report_content = self._generate_html_report(report_data)
            else:
                report_content = self._generate_markdown_report(report_data)
            
            # 保存报告
            report_file_path = self._save_report(report_data["session_id"], report_content, format_type)
            
            self.logger.info(f"面试报告生成完成: {report_data['session_id']}")
            
            return {
                "status": "success",
                "report_content": report_content,
                "report_file_path": str(report_file_path),
                "session_id": report_data["session_id"],
                "format": format_type
            }
            
        except Exception as e:
            self.logger.error(f"报告生成失败: {e}")
            return {
                "status": "error",
                "message": f"报告生成失败: {str(e)}"
            }
    
    def _prepare_report_data(self, session_data: Dict[str, Any], 
                           evaluation_result: Dict[str, Any]) -> Dict[str, Any]:
        """准备报告数据"""
        
        # 计算面试时长
        start_time = datetime.fromisoformat(session_data.get("start_time", datetime.now().isoformat()))
        end_time = datetime.fromisoformat(session_data.get("end_time", datetime.now().isoformat()))
        duration_minutes = int((end_time - start_time).total_seconds() / 60)
        
        # 统计对话数据
        conversation_history = session_data.get("conversation_history", [])
        user_messages = [msg for msg in conversation_history if msg["role"] == "user"]
        question_count = len(user_messages)
        
        report_data = {
            "session_id": session_data.get("session_id", "unknown"),
            "interview_mode": session_data.get("mode", "basic"),
            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_minutes": duration_minutes,
            "question_count": question_count,
            "overall_score": evaluation_result.get("overall_score", 0),
            "evaluation_level": evaluation_result.get("evaluation_level", "一般"),
            "dimension_scores": evaluation_result.get("dimension_scores", {}),
            "comprehensive_feedback": evaluation_result.get("comprehensive_feedback", ""),
            "strengths": evaluation_result.get("strengths", []),
            "weaknesses": evaluation_result.get("weaknesses", []),
            "improvement_suggestions": evaluation_result.get("improvement_suggestions", []),
            "conversation_summary": self._summarize_conversation(conversation_history),
            "metadata": session_data.get("metadata", {})
        }
        
        return report_data
    
    def _summarize_conversation(self, conversation_history: List[Dict]) -> List[Dict[str, str]]:
        """总结对话内容"""
        summary = []
        current_qa = {}
        
        for msg in conversation_history:
            if msg["role"] == "assistant" and not current_qa:
                # 面试官问题
                current_qa["question"] = msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
            elif msg["role"] == "user" and "question" in current_qa:
                # 候选人回答
                current_qa["answer"] = msg["content"][:300] + "..." if len(msg["content"]) > 300 else msg["content"]
                summary.append(current_qa.copy())
                current_qa = {}
        
        return summary
    
    def _generate_markdown_report(self, report_data: Dict[str, Any]) -> str:
        """生成Markdown格式报告"""
        
        # 维度得分表格
        dimension_table = ""
        if report_data["dimension_scores"]:
            dimension_names = {
                "technical_accuracy": "技术准确性",
                "communication": "沟通表达", 
                "problem_solving": "问题解决",
                "experience_depth": "经验深度",
                "learning_ability": "学习能力"
            }
            
            dimension_table = "| 评估维度 | 得分 |\n|---------|------|\n"
            for dimension, score in report_data["dimension_scores"].items():
                name = dimension_names.get(dimension, dimension)
                dimension_table += f"| {name} | {score:.1f}/10.0 |\n"
        
        # 对话摘要
        qa_summary = ""
        for i, qa in enumerate(report_data["conversation_summary"], 1):
            qa_summary += f"""
### Q{i}: {qa.get('question', '无问题记录')}

**候选人回答：**
{qa.get('answer', '无回答记录')}

---
"""
        
        markdown_content = f"""# 面试评估报告

## 📋 基本信息

- **面试编号**: {report_data['session_id'][:8]}...
- **面试模式**: {report_data['interview_mode']}  
- **面试时间**: {report_data['start_time']} ~ {report_data['end_time']}
- **面试时长**: {report_data['duration_minutes']} 分钟
- **问题数量**: {report_data['question_count']} 个

## 🎯 综合评估

### 总体得分
**{report_data['overall_score']:.1f}/10.0** - {report_data['evaluation_level']}

### 各维度得分
{dimension_table}

## 📊 详细反馈

### 综合评价
{report_data['comprehensive_feedback']}

### ✅ 主要优势
{chr(10).join([f"- {strength}" for strength in report_data['strengths']])}

### 📈 改进建议  
{chr(10).join([f"- {suggestion}" for suggestion in report_data['improvement_suggestions']])}

## 💬 面试问答摘要
{qa_summary}

---
*报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
        
        return markdown_content
    
    def _generate_text_report(self, report_data: Dict[str, Any]) -> str:
        """生成纯文本格式报告"""
        
        text_content = f"""
========================================
          面试评估报告
========================================

基本信息：
- 面试编号：{report_data['session_id'][:8]}...
- 面试模式：{report_data['interview_mode']}
- 面试时间：{report_data['start_time']} ~ {report_data['end_time']}
- 面试时长：{report_data['duration_minutes']} 分钟
- 问题数量：{report_data['question_count']} 个

综合评估：
- 总体得分：{report_data['overall_score']:.1f}/10.0 ({report_data['evaluation_level']})

各维度得分："""

        # 添加维度得分
        dimension_names = {
            "technical_accuracy": "技术准确性",
            "communication": "沟通表达",
            "problem_solving": "问题解决", 
            "experience_depth": "经验深度",
            "learning_ability": "学习能力"
        }
        
        for dimension, score in report_data["dimension_scores"].items():
            name = dimension_names.get(dimension, dimension)
            text_content += f"\n- {name}：{score:.1f}/10.0"
        
        text_content += f"""

详细反馈：

综合评价：
{report_data['comprehensive_feedback']}

主要优势：
{chr(10).join([f"• {strength}" for strength in report_data['strengths']])}

改进建议：
{chr(10).join([f"• {suggestion}" for suggestion in report_data['improvement_suggestions']])}

面试问答摘要："""

        # 添加问答摘要
        for i, qa in enumerate(report_data["conversation_summary"], 1):
            text_content += f"""

Q{i}: {qa.get('question', '无问题记录')}
A{i}: {qa.get('answer', '无回答记录')}
"""
        
        text_content += f"\n\n报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return text_content
    
    def _generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """生成HTML格式报告"""
        
        # 维度得分图表数据（简化版）
        dimension_chart = ""
        if report_data["dimension_scores"]:
            dimension_names = {
                "technical_accuracy": "技术准确性",
                "communication": "沟通表达",
                "problem_solving": "问题解决", 
                "experience_depth": "经验深度",
                "learning_ability": "学习能力"
            }
            
            for dimension, score in report_data["dimension_scores"].items():
                name = dimension_names.get(dimension, dimension)
                percentage = (score / 10.0) * 100
                color = "success" if score >= 8 else "warning" if score >= 6 else "danger"
                dimension_chart += f"""
                <div class="mb-3">
                    <div class="d-flex justify-content-between">
                        <span>{name}</span>
                        <span>{score:.1f}/10.0</span>
                    </div>
                    <div class="progress">
                        <div class="progress-bar bg-{color}" style="width: {percentage}%"></div>
                    </div>
                </div>"""
        
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>面试评估报告</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ font-family: 'Microsoft YaHei', sans-serif; }}
        .report-header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
        .score-circle {{ width: 120px; height: 120px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold; }}
        .score-excellent {{ background-color: #28a745; }}
        .score-good {{ background-color: #17a2b8; }}
        .score-average {{ background-color: #ffc107; }}
        .score-poor {{ background-color: #dc3545; }}
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="report-header p-4 mb-4">
            <h1 class="text-center">🎯 面试评估报告</h1>
            <p class="text-center mb-0">基于AI智能分析的专业面试评估</p>
        </div>
        
        <div class="container">
            <!-- 基本信息 -->
            <div class="row mb-4">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header"><h5>📋 基本信息</h5></div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <p><strong>面试编号：</strong>{report_data['session_id'][:8]}...</p>
                                    <p><strong>面试模式：</strong>{report_data['interview_mode']}</p>
                                    <p><strong>面试时长：</strong>{report_data['duration_minutes']} 分钟</p>
                                </div>
                                <div class="col-md-6">
                                    <p><strong>开始时间：</strong>{report_data['start_time']}</p>
                                    <p><strong>结束时间：</strong>{report_data['end_time']}</p>
                                    <p><strong>问题数量：</strong>{report_data['question_count']} 个</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card text-center">
                        <div class="card-header"><h5>🎯 总体得分</h5></div>
                        <div class="card-body">
                            <div class="score-circle score-{'excellent' if report_data['overall_score'] >= 8 else 'good' if report_data['overall_score'] >= 6 else 'average' if report_data['overall_score'] >= 4 else 'poor'} mx-auto text-white">
                                {report_data['overall_score']:.1f}
                            </div>
                            <p class="mt-3 mb-0"><strong>{report_data['evaluation_level']}</strong></p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 维度得分 -->
            <div class="row mb-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header"><h5>📊 各维度得分</h5></div>
                        <div class="card-body">
                            {dimension_chart}
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 详细反馈 -->
            <div class="row mb-4">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header"><h5>💬 综合评价</h5></div>
                        <div class="card-body">
                            <p>{report_data['comprehensive_feedback']}</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-success text-white"><h5>✅ 主要优势</h5></div>
                        <div class="card-body">
                            <ul>
                                {chr(10).join([f"<li>{strength}</li>" for strength in report_data['strengths']])}
                            </ul>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-info text-white"><h5>📈 改进建议</h5></div>
                        <div class="card-body">
                            <ul>
                                {chr(10).join([f"<li>{suggestion}</li>" for suggestion in report_data['improvement_suggestions']])}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="text-center text-muted mb-4">
                <small>报告生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</small>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""
        
        return html_content
    
    def _save_report(self, session_id: str, content: str, format_type: str) -> Path:
        """保存报告到文件"""
        try:
            # 创建报告目录
            reports_dir = Path(self.config.get("paths", {}).get("project_root", ".")) / "reports"
            reports_dir.mkdir(exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = {"markdown": ".md", "text": ".txt", "html": ".html"}.get(format_type, ".txt")
            filename = f"interview_report_{session_id[:8]}_{timestamp}{file_extension}"
            
            # 保存文件
            file_path = reports_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"报告已保存: {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"保存报告失败: {e}")
            raise
    
    def _get_markdown_template(self) -> str:
        """获取Markdown模板"""
        return "markdown_template"  # 占位符
    
    def _get_text_template(self) -> str:
        """获取文本模板"""
        return "text_template"  # 占位符
    
    def _get_html_template(self) -> str:
        """获取HTML模板"""
        return "html_template"  # 占位符
    
    def export_report_data(self, session_data: Dict[str, Any], 
                          evaluation_result: Dict[str, Any]) -> Dict[str, Any]:
        """导出报告数据为JSON格式"""
        try:
            report_data = self._prepare_report_data(session_data, evaluation_result)
            
            # 添加原始数据
            export_data = {
                "report_info": report_data,
                "raw_session_data": session_data,
                "raw_evaluation_result": evaluation_result,
                "export_time": datetime.now().isoformat()
            }
            
            # 保存JSON文件
            reports_dir = Path(self.config.get("paths", {}).get("project_root", ".")) / "reports"
            reports_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = f"interview_data_{report_data['session_id'][:8]}_{timestamp}.json"
            json_file_path = reports_dir / json_filename
            
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"报告数据已导出: {json_file_path}")
            
            return {
                "status": "success",
                "export_path": str(json_file_path),
                "data": export_data
            }
            
        except Exception as e:
            self.logger.error(f"导出报告数据失败: {e}")
            return {
                "status": "error",
                "message": f"导出失败: {str(e)}"
            }
