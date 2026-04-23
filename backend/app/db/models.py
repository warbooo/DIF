from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tasks = relationship("RepairTask", back_populates="user", cascade="all, delete-orphan")


class RepairTask(Base):
    __tablename__ = "repair_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_key = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String(256), nullable=False)
    status = Column(String(16), default="pending")  # pending, processing, done, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # OCR & Completion results
    ocr_text = Column(Text, default="")
    filled_text = Column(Text, default="")
    original_relpath = Column(String(512), nullable=True)  # 原始图片路径（可能是裁剪后的）
    repaired_relpath = Column(String(512), nullable=True)  # 修复后图片路径
    meta = Column(JSON, default=dict)

    # Relationships
    user = relationship("User", back_populates="tasks")


# 新增：用户满意度评价模型
class UserSatisfactionRating(Base):
    __tablename__ = "user_satisfaction_ratings"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("repair_tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 评分项
    visual_quality = Column(Integer, default=0)  # 视觉质量 1-5
    text_readability = Column(Integer, default=0)  # 文字可读性 1-5
    stain_removal = Column(Integer, default=0)  # 污渍去除 1-5
    color_restoration = Column(Integer, default=0)  # 色彩还原 1-5
    overall_satisfaction = Column(Integer, default=0)  # 综合满意度 1-5
    
    comments = Column(Text, default="")  # 评价备注
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    task = relationship("RepairTask")


# 任务快速评价模型（1-5 星）
class TaskRating(Base):
    __tablename__ = "task_ratings"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("repair_tasks.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 评分（1-5 星）
    rating = Column(Integer, nullable=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    task = relationship("RepairTask")

    __table_args__ = (
        UniqueConstraint('task_id', 'user_id', name='uix_task_user_rating'),
    )
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint('task_id', 'user_id', name='uix_task_user_rating'),
    )


# 新增：系统日志模型
class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(64), nullable=False)  # 操作类型
    resource_type = Column(String(64), nullable=True)  # 资源类型
    resource_id = Column(String(128), nullable=True)  # 资源ID
    ip_address = Column(String(64), nullable=True)  # IP地址
    status = Column(String(16), default="success")  # success, error
    duration = Column(Integer, nullable=True)  # 耗时(ms)
    message = Column(Text, nullable=True)  # 详细信息
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")


# 新增：OCR识别结果详情表
class OcrResult(Base):
    __tablename__ = "ocr_results"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("repair_tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # OCR识别详情
    language = Column(String(16), default="ch")  # 识别语言
    confidence = Column(Float, default=0.0)  # 整体置信度
    word_count = Column(Integer, default=0)  # 识别字数
    line_count = Column(Integer, default=0)  # 识别行数
    
    # 识别结果结构化存储
    raw_text = Column(Text, default="")  # 原始文本
    structured_data = Column(JSON, default=list)  # 结构化识别结果（包含位置、置信度等）
    
    # 处理信息
    processing_time = Column(Float, default=0.0)  # 处理耗时(秒)
    model_version = Column(String(64), default="")  # OCR模型版本
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    task = relationship("RepairTask")
    user = relationship("User")


# 新增：文本补全操作日志表
class CompletionLog(Base):
    __tablename__ = "completion_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("repair_tasks.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 补全类型
    completion_type = Column(String(32), default="nlp_based")  # nlp_based, llm
    is_llm_enabled = Column(Boolean, default=False)
    
    # 输入输出
    original_text = Column(Text, default="")
    completed_text = Column(Text, default="")
    
    # 处理信息
    success = Column(Boolean, default=True)
    error_message = Column(Text, default="")
    processing_time = Column(Float, default=0.0)
    
    # LLM相关
    llm_provider = Column(String(32), default="")
    tokens_used = Column(Integer, default=0)
    model_name = Column(String(64), default="")
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    task = relationship("RepairTask")
    user = relationship("User")


# 新增：模型使用统计表
class ModelUsageStat(Base):
    __tablename__ = "model_usage_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 模型信息
    model_type = Column(String(32), nullable=False)  # classical, compressed, realworld
    model_name = Column(String(64), nullable=False)
    
    # 使用统计
    usage_count = Column(Integer, default=0)
    total_processing_time = Column(Float, default=0.0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    
    # 性能指标
    avg_confidence = Column(Float, default=0.0)
    avg_image_size = Column(String(32), default="")
    
    last_used_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint('user_id', 'model_type', name='uix_user_model_usage'),
    )


# 新增：用户个性化设置表
class UserSetting(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # UI设置
    theme = Column(String(32), default="light")  # light, dark
    language = Column(String(16), default="zh-CN")
    
    # 默认处理设置
    default_model = Column(String(32), default="classical")
    default_language = Column(String(16), default="ch")
    auto_ocr = Column(Boolean, default=True)
    auto_completion = Column(Boolean, default=False)
    llm_enabled = Column(Boolean, default=False)
    
    # 高级设置
    enable_tiling = Column(Boolean, default=True)
    use_fp16 = Column(Boolean, default=True)
    tile_size = Column(Integer, default=256)
    
    # 通知设置
    email_notifications = Column(Boolean, default=False)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")



