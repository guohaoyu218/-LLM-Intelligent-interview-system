"""
数据库初始化脚本
"""
from backend.core.database import engine
from backend.models import user, interview

def init_db():
    """
    初始化数据库
    """
    # 创建所有表
    user.Base.metadata.create_all(bind=engine)
    interview.Base.metadata.create_all(bind=engine)
