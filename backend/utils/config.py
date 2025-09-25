"""
配置管理模块
"""
import os
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """系统配置类"""
    
    # 基础配置
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    CHAT_HISTORY_DIR = PROJECT_ROOT / "chat_history"
    
    # API配置
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    
    # BGE模型配置
    BGE_MODEL_NAME = os.getenv("BGE_MODEL_NAME", "BAAI/bge-small-zh-v1.5")
    _bge_path = os.getenv("BGE_MODEL_PATH")
    BGE_MODEL_PATH = Path(_bge_path) if _bge_path else None
    EMBEDDING_DIMENSION = 512
    
    # Qdrant配置
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    
    # 面试配置
    MAX_CONVERSATION_TURNS = 20
    DEFAULT_DIFFICULTY = "medium"
    SUPPORTED_LANGUAGES = ["zh-CN", "en-US"]
    
    # 性能配置
    MAX_CONCURRENT_SESSIONS = 10
    REQUEST_TIMEOUT = 30
    RETRY_ATTEMPTS = 3
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = PROJECT_ROOT / "logs" / "app.log"
    
    # 安全配置
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".md"}
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """验证配置"""
        errors = []
        warnings = []
        
        # 检查必需的API密钥
        if not cls.DEEPSEEK_API_KEY:
            errors.append("DEEPSEEK_API_KEY未设置")
        
        # 检查目录
        required_dirs = [cls.DATA_DIR, cls.CHAT_HISTORY_DIR]
        for dir_path in required_dirs:
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    warnings.append(f"已创建目录: {dir_path}")
                except Exception as e:
                    errors.append(f"无法创建目录 {dir_path}: {e}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """获取配置字典"""
        return {
            "deepseek": {
                "api_key": cls.DEEPSEEK_API_KEY,
                "base_url": cls.DEEPSEEK_BASE_URL,
                "model": cls.DEEPSEEK_MODEL
            },
            "bge": {
                "model_name": cls.BGE_MODEL_NAME,
                "model_path": cls.BGE_MODEL_PATH,
                "dimension": cls.EMBEDDING_DIMENSION
            },
            "qdrant": {
                "host": cls.QDRANT_HOST,
                "port": cls.QDRANT_PORT,
                "api_key": cls.QDRANT_API_KEY
            },
            "paths": {
                "project_root": str(cls.PROJECT_ROOT),
                "data_dir": str(cls.DATA_DIR),
                "chat_history_dir": str(cls.CHAT_HISTORY_DIR)
            }
        }

def load_config() -> Dict[str, Any]:
    """加载配置"""
    config_dict = Config.get_config_dict()
    
    # 验证配置
    validation = Config.validate_config()
    if not validation["valid"]:
        raise ValueError(f"配置验证失败: {validation['errors']}")
    
    if validation["warnings"]:
        print(f"配置警告: {validation['warnings']}")
    
    return config_dict

# 导出配置实例
config = Config()
