from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel


class OcrResultItem(BaseModel):
    text: str
    confidence: Optional[float] = None


class CompletionLogItem(BaseModel):
    input_text: str
    completed_text: str
    completion_type: str
    tokens_used: int
    duration: float
    status: str


class HistoryItem(BaseModel):
    id: int  # 数据库主键（整数），用于 API 调用
    task_id: str  # UUID 字符串，用于显示
    original_filename: str
    status: str
    created_at: str
    input_text: Optional[str] = None
    ocr_results: Optional[List[OcrResultItem]] = None
    completion_log: Optional[CompletionLogItem] = None
    sr_model_type: Optional[str] = None  # 超分模型类型
    sr_scale: Optional[int] = None  # 超分倍数

