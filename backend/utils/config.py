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
    
    def find_project_root() -> Path:
        """动态查找项目根目录（通过寻找.git文件夹）"""
        current_path = Path(__file__).resolve()  # 当前文件的绝对路径
        # 向上级目录循环查找，直到找到.git文件夹或到达系统根目录
        while current_path != current_path.parent:
            if (current_path / ".git").exists():
                return current_path
        current_path = current_path.parent
    # 如果没找到标志性文件，可根据需求抛错或返回默认路径
        raise FileNotFoundError("未找到项目根目录（未发现.git文件夹）")
    
    # 基础配置
    PROJECT_ROOT = find_project_root()
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
    
    # 数据库配置
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "interview_db")
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    
    # JWT配置
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-keep-it-secret")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # API配置
    API_V1_PREFIX = "/api"
    PROJECT_NAME = "AI面试系统"
    VERSION = "1.0.0"
    BACKEND_CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    
    # 上传配置
    UPLOAD_DIR = PROJECT_ROOT / "uploads"
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """验证配置"""
        errors = []
        warnings = []
        
        # 检查必需的API密钥
        if not cls.DEEPSEEK_API_KEY:
            errors.append("DEEPSEEK_API_KEY未设置")
        
        # 检查数据库配置
        if not cls.DB_PASSWORD:
            warnings.append("数据库密码未设置，请确保在生产环境中设置安全的数据库密码")
        
        # 检查JWT配置
        if cls.SECRET_KEY == "your-secret-key-keep-it-secret":
            warnings.append("正在使用默认的SECRET_KEY，请在生产环境中更改为安全的密钥")
        
        # 检查目录
        required_dirs = [cls.DATA_DIR, cls.CHAT_HISTORY_DIR, cls.UPLOAD_DIR]
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
