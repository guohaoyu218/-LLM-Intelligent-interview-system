"""
面试相关数据库模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship
from backend.core.database import Base

class Interview(Base):
    """面试记录模型"""
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_id = Column(String(36), nullable=False, unique=True)
    interview_type = Column(String(50))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(20))
    score = Column(Numeric(5, 2), nullable=True)
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    user = relationship("User", back_populates="interviews")
