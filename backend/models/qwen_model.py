"""
通义千问模型封装
用于评估和报告生成
"""

from typing import Dict, Any, Optional
import json
import requests
from time import sleep
from backend.utils.logger import get_logger

class QwenModel:
    """Qwen API封装，专注于评估报告生成"""
    
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get("QWEN_API_KEY")
        self.api_base = config.get("QWEN_API_BASE", "https://api.qwen.ai/v1")
        self.model = config.get("QWEN_MODEL", "qwen-max")
        self.logger = get_logger(__name__)
        
        if not self.api_key:
            raise ValueError("Qwen API key not found in config")
    
    def generate(self, 
                prompt: str, 
                system_prompt: Optional[str] = None,
                temperature: float = 0.7,
                max_tokens: int = 1000,
                retry_count: int = 3,
                retry_delay: int = 2) -> Dict[str, Any]:
        """生成文本"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        for attempt in range(retry_count):
            try:
                response = requests.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
                
                return {
                    "content": result["choices"][0]["message"]["content"],
                    "usage": result.get("usage", {}),
                    "model": self.model
                }
                
            except Exception as e:
                self.logger.error(f"Qwen API调用失败 (尝试 {attempt + 1}/{retry_count}): {str(e)}")
                if attempt < retry_count - 1:
                    sleep(retry_delay)
                else:
                    raise
    
    def analyze_interview(self, 
                         conversation_history: list,
                         resume_data: Optional[Dict] = None) -> Dict[str, Any]:
        """分析面试内容并生成评估"""
        try:
            # 构建分析提示词
            conversation_text = "\n".join([
                f"{'面试官' if msg['role'] == 'assistant' else '候选人'}: {msg['content']}"
                for msg in conversation_history
            ])
            
            prompt = f"""请分析以下面试对话，生成详细的评估报告。

面试记录：
{conversation_text}

{f'候选人简历信息：{json.dumps(resume_data, ensure_ascii=False)}' if resume_data else ''}

请从以下维度进行评估：
1. 技术深度（技术理解准确性、知识广度、实践经验）
2. 逻辑思维（问题分析能力、解决方案设计、思路清晰度）
3. 沟通表达（表达清晰度、专业术语使用、回答完整性）
4. 综合素质（学习能力、创新思维、职业规划）

输出格式要求：
1. 各维度得分（0-10分）和详细分析
2. 优势和亮点总结
3. 改进建议
4. 是否推荐进入下轮面试
5. 总体评价和建议

请以JSON格式返回，包含所有评估维度和详细说明。"""

            # 设置系统提示词引导输出格式
            system_prompt = """你是一位经验丰富的技术面试评估专家。
请基于面试对话内容，给出客观、专业、结构化的评估报告。
评估要有理有据，结合具体对话内容，避免主观臆测。
输出必须是格式良好的JSON。"""

            # 生成评估报告
            result = self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=2000
            )
            
            # 解析结果
            try:
                report = json.loads(result["content"])
                return report
            except json.JSONDecodeError:
                self.logger.error("评估报告解析失败，返回原始内容")
                return {
                    "error": "结果解析失败",
                    "raw_content": result["content"]
                }
                
        except Exception as e:
            self.logger.error(f"面试分析失败: {str(e)}")
            raise
    
    def generate_report(self,
                       evaluation_result: Dict[str, Any],
                       report_format: str = "markdown") -> str:
        """基于评估结果生成格式化报告"""
        try:
            # 构建报告生成提示词
            prompt = f"""请基于以下评估结果生成一份正式的面试评估报告。

评估数据：
{json.dumps(evaluation_result, ensure_ascii=False, indent=2)}

要求：
1. 报告格式为{report_format}
2. 结构清晰，层次分明
3. 语言专业、客观
4. 包含数据支撑
5. 提供具体的改进建议

请生成一份完整的报告。"""

            system_prompt = f"""你是一位专业的技术评估报告撰写专家。
请基于评估数据生成一份结构化的报告。
输出格式为{report_format}。
注重数据的可读性和专业性。"""

            # 生成报告
            result = self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=2000
            )
            
            return result["content"]
            
        except Exception as e:
            self.logger.error(f"报告生成失败: {str(e)}")
            raise
    
    def validate_connection(self) -> bool:
        """验证API连接"""
        try:
            result = self.generate(
                "测试连接",
                max_tokens=10
            )
            return bool(result.get("content"))
        except:
            return False
