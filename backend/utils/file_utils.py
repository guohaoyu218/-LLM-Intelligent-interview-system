"""
工具函数模块
整合原utils_enhanced.py的功能到backend结构中
"""


import json
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.messages import AIMessage, HumanMessage


def save_chat_history(chat_history: List, session_id: str) -> str:
    """
    保存聊天记录
    
    Args:
        chat_history: 聊天记录列表
        session_id: 会话ID
        
    Returns:
        保存的文件路径
    """
    try:
        # 使用项目根目录的chat_history文件夹
        project_root = Path(__file__).parent.parent.parent
        chat_dir = project_root / "chat_history" / session_id
        chat_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = chat_dir / "chat_history.txt"
        
        with open(file_path, "w", encoding="utf-8") as file:
            for message in chat_history:
                if isinstance(message, AIMessage):
                    speaker = "面试官"
                elif isinstance(message, HumanMessage):
                    speaker = "应聘者"
                else:
                    continue
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                file.write(f"[{timestamp}] {speaker}: {message.content}\n\n")
        
        return str(file_path)
    except Exception as e:
        print(f"保存聊天记录失败：{e}")
        return ""


def parse_jd_to_json(llm, jd_content: str) -> Dict[str, Any]:
    """
    解析职位描述为JSON格式
    
    Args:
        llm: 语言模型实例
        jd_content: 职位描述文本
        
    Returns:
        解析后的JSON数据
    """
    try:
        template = """
基于JD文本，按照约束，生成以下格式的 JSON 数据：
{{
    "职位名称": "string",
    "公司名称": "string", 
    "工作地点": "string",
    "薪资范围": "string",
    "工作经验": "string",
    "学历要求": "string",
    "职位描述": "string",
    "职责要求": ["requirement1", "requirement2"],
    "技能要求": ["skill1", "skill2"],
    "福利待遇": ["benefit1", "benefit2"]
}}

JD文本：
{jd_content}

约束：
1、严格按照上述JSON格式输出
2、如果某项信息未提及，设为空字符串或空数组
3、确保输出是有效的JSON格式

JSON：
"""
        
        parser = JsonOutputParser()
        prompt = PromptTemplate(
            template=template,
            input_variables=["jd_content"]
        )
        
        chain = prompt | llm | parser
        result = chain.invoke({"jd_content": jd_content})
        
        return result
        
    except Exception as e:
        print(f"解析JD失败: {e}")
        return {}


def parse_resume_to_md(llm, resume_content: str) -> str:
    """
    解析简历为Markdown格式
    
    Args:
        llm: 语言模型实例
        resume_content: 简历文本
        
    Returns:
        Markdown格式的简历
    """
    try:
        template = """
基于简历文本，转换成标准的Markdown格式：

简历文本：
{resume_content}

约束：
1、使用标准的Markdown格式
2、只使用一级标题(#)和二级标题(##)
3、一级标题包括：个人信息、教育经历、工作经历、项目经历、职业技能、获奖情况、自我评价
4、内容要完整保留，格式要清晰

Markdown：
"""
        
        parser = StrOutputParser()
        prompt = PromptTemplate(
            template=template,
            input_variables=["resume_content"]
        )
        
        chain = prompt | llm | parser
        result = chain.invoke({"resume_content": resume_content})
        
        return result.strip("```markdown").strip("```").strip()
        
    except Exception as e:
        print(f"解析简历失败: {e}")
        return ""


def read_json_file(file_path: str) -> Dict[str, Any]:
    """读取JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"读取JSON文件失败 {file_path}: {e}")
        return {}


def save_json_file(data: Dict[str, Any], file_path: str) -> bool:
    """保存JSON文件"""
    try:
        # 确保目录存在
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            #将 Python 数据结构（如字典、列表）序列化为 JSON 格式，并写入指定文件中，同时设置 “不转义非 ASCII 字符” 和 “2 个空格缩进”
        return True
    except Exception as e:
        print(f"保存JSON文件失败 {file_path}: {e}")
        return False
