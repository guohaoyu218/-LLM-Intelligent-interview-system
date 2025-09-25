"""
日志管理模块
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""
    
    # 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # 添加颜色
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        
        return super().format(record)

def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[Path] = None,
    console_output: bool = True
) -> logging.Logger:
    """设置日志记录器"""
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 日志格式
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    colored_formatter = ColoredFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(colored_formatter)
        logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        # 确保日志目录存在
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(
            log_file,
            mode='a',
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """获取日志记录器"""
    from .config import config
    
    return setup_logger(
        name=name,
        level=config.LOG_LEVEL,
        log_file=config.LOG_FILE,
        console_output=True
    )

class InterviewLogger:
    """面试专用日志记录器"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.logger = get_logger(f"interview.{session_id}")
        
        # 创建面试专用日志文件
        from .config import config
        session_log_file = config.CHAT_HISTORY_DIR / f"{session_id}" / "session.log"
        session_log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(
            session_log_file,
            mode='w',
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(file_handler)
    
    def log_question(self, question: str, difficulty: str, mode: str):
        """记录面试问题"""
        self.logger.info(f"[问题生成] 难度:{difficulty} 模式:{mode} 问题:{question}")
    
    def log_answer(self, answer: str, analysis: dict):
        """记录回答分析"""
        self.logger.info(f"[回答分析] 回答:{answer[:100]}... 得分:{analysis.get('overall_score', 0)}")
    
    def log_session_start(self, mode: str, config: dict):
        """记录会话开始"""
        self.logger.info(f"[会话开始] 模式:{mode} 配置:{config}")
    
    def log_session_end(self, report: dict):
        """记录会话结束"""
        self.logger.info(f"[会话结束] 总分:{report.get('overall_score', 0)} 问题数:{report.get('question_count', 0)}")
    
    def log_error(self, error: Exception, context: str = ""):
        """记录错误"""
        self.logger.error(f"[错误] {context}: {str(error)}", exc_info=True)
