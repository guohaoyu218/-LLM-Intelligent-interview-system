"""
pytest配置文件
"""

import pytest
import sys
import os
from pathlib import Path

# 添加项目路径到sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 测试数据目录
TEST_DATA_DIR = Path(__file__).parent / "data"
TEST_DATA_DIR.mkdir(exist_ok=True)


@pytest.fixture
def mock_config():
    """模拟配置数据"""
    return {
        "deepseek": {
            "api_key": "test-api-key",
            "base_url": "https://api.deepseek.com",
            "model": "deepseek-chat"
        },
        "bge": {
            "model_name": "BAAI/bge-small-zh-v1.5",
            "model_path": None,
            "dimension": 512
        },
        "qdrant": {
            "host": "localhost",
            "port": 6333,
            "api_key": None
        },
        "paths": {
            "project_root": str(project_root),
            "data_dir": str(project_root / "data"),
            "chat_history_dir": str(project_root / "chat_history")
        }
    }


@pytest.fixture
def sample_session_data():
    """示例会话数据"""
    return {
        "session_id": "test-session-123",
        "mode": "basic",
        "start_time": "2023-01-01T10:00:00",
        "end_time": "2023-01-01T10:30:00",
        "status": "completed",
        "conversation_history": [
            {
                "role": "assistant",
                "content": "你好，欢迎参加面试！请先简单介绍一下自己。",
                "timestamp": "2023-01-01T10:00:00"
            },
            {
                "role": "user", 
                "content": "你好，我是张三，有3年Python开发经验。",
                "timestamp": "2023-01-01T10:01:00"
            },
            {
                "role": "assistant",
                "content": "很好！请介绍一下你最近做过的一个项目。",
                "timestamp": "2023-01-01T10:02:00"
            },
            {
                "role": "user",
                "content": "我最近开发了一个基于Flask的Web应用，使用了Redis缓存和MySQL数据库。",
                "timestamp": "2023-01-01T10:03:00"
            }
        ],
        "metadata": {
            "resume_content": "",
            "jd_content": "",
            "question_count": 2
        }
    }


@pytest.fixture
def sample_evaluation_result():
    """示例评估结果"""
    return {
        "session_id": "test-session-123",
        "evaluation_time": "2023-01-01T10:30:00",
        "overall_score": 7.5,
        "dimension_scores": {
            "technical_accuracy": 8.0,
            "communication": 7.5,
            "problem_solving": 7.0,
            "experience_depth": 8.0,
            "learning_ability": 7.0
        },
        "evaluation_level": "良好",
        "comprehensive_feedback": "候选人表现良好，技术基础扎实，表达清晰。",
        "strengths": ["技术基础扎实", "项目经验丰富", "表达清晰"],
        "weaknesses": ["问题解决思路需要改进"],
        "improvement_suggestions": [
            "技术准确性：继续保持当前的优秀表现",
            "问题解决：培养系统性的问题分析方法"
        ]
    }


# 测试环境设置
def pytest_configure(config):
    """pytest配置"""
    # 设置测试环境变量
    os.environ["TESTING"] = "true"
    os.environ["DEEPSEEK_API_KEY"] = "test-key"


def pytest_unconfigure(config):
    """清理测试环境"""
    if "TESTING" in os.environ:
        del os.environ["TESTING"]
