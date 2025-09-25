"""
DeepSeek模型封装
"""
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.language_models.llms import LLM
from backend.utils.logger import get_logger

class DeepSeekLLM:
    """DeepSeek大语言模型封装"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)
        
        # 初始化ChatOpenAI客户端
        self.client = ChatOpenAI(
            model=config["deepseek"]["model"],
            api_key=config["deepseek"]["api_key"],
            base_url=config["deepseek"]["base_url"],
            temperature=0.7,
            max_tokens=2000,
            timeout=30,
            max_retries=3
        )
        
        # 模型参数
        self.default_params = {
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.95,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1
        }
    
    def invoke(self, 
               prompt: str, 
               system_prompt: Optional[str] = None,
               **kwargs) -> AIMessage:
        """调用模型生成响应"""
        
        try:
            # 构建消息
            messages = []
            
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            
            messages.append(HumanMessage(content=prompt))
            
            # 更新参数
            params = self.default_params.copy()
            params.update(kwargs)
            
            # 调用模型
            response = self.client.invoke(
                messages,
                **params
            )
            
            self.logger.debug(f"模型调用成功: {prompt[:50]}...")
            return response
            
        except Exception as e:
            self.logger.error(f"模型调用失败: {e}")
            raise
    
    def stream_invoke(self, 
                     prompt: str,
                     system_prompt: Optional[str] = None,
                     **kwargs):
        """流式调用模型"""
        
        try:
            # 构建消息
            messages = []
            
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            
            messages.append(HumanMessage(content=prompt))
            
            # 更新参数
            params = self.default_params.copy()
            params.update(kwargs)
            
            # 流式调用
            for chunk in self.client.stream(messages, **params):
                yield chunk
                
        except Exception as e:
            self.logger.error(f"流式调用失败: {e}")
            raise
    
    def batch_invoke(self, 
                    prompts: List[str],
                    system_prompt: Optional[str] = None,
                    **kwargs) -> List[AIMessage]:
        """批量调用模型"""
        
        try:
            # 构建批量消息
            batch_messages = []
            
            for prompt in prompts:
                messages = []
                if system_prompt:
                    messages.append(SystemMessage(content=system_prompt))
                messages.append(HumanMessage(content=prompt))
                batch_messages.append(messages)
            
            # 更新参数
            params = self.default_params.copy()
            params.update(kwargs)
            
            # 批量调用
            responses = self.client.batch(batch_messages, **params)
            
            self.logger.debug(f"批量调用成功: {len(prompts)}个请求")
            return responses
            
        except Exception as e:
            self.logger.error(f"批量调用失败: {e}")
            raise
    
    def validate_connection(self) -> bool:
        """验证连接"""
        try:
            test_response = self.invoke("Hello", max_tokens=10)
            return bool(test_response.content)
        except Exception as e:
            self.logger.error(f"连接验证失败: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "model_name": self.config["deepseek"]["model"],
            "base_url": self.config["deepseek"]["base_url"],
            "default_params": self.default_params,
            "is_connected": self.validate_connection()
        }

