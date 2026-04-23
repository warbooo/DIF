from __future__ import annotations

from typing import Any, Literal, Optional, List, Dict

from pydantic import BaseModel, Field


class RepairResponse(BaseModel):
    task_id: str
    ocr_text: str
    filled_text: str
    repaired_image_base64: str
    mild_image_base64: str
    strong_image_base64: str
    # 方便前端下载/展示
    repaired_image_mime: str = "image/png"
    # 元数据
    meta: Optional[Dict[str, Any]] = None


class RepairZipItem(BaseModel):
    filename: str
    task_id: str
    ocr_text: str
    filled_text: str
    repaired_image_base64: str
    repaired_image_mime: str = "image/png"


class RepairZipResponse(BaseModel):
    items: List[RepairZipItem]


class RepairHistoryResponse(BaseModel):
    task_id: str
    original_filename: str
    doc_type: str
    status: str
    created_at: str
    updated_at: str


class UserSatisfactionRatingRequest(BaseModel):
    """用户满意度评价请求"""
    task_id: str
    visual_quality: int = Field(..., ge=1, le=5, description="视觉清晰度 (1-5)")
    text_readability: int = Field(..., ge=1, le=5, description="文字可读性 (1-5)")
    stain_removal: int = Field(..., ge=1, le=5, description="污渍去除效果 (1-5)")
    color_restoration: int = Field(..., ge=1, le=5, description="色彩还原度 (1-5)")
    overall_satisfaction: int = Field(..., ge=1, le=5, description="整体满意度 (1-5)")
    comments: Optional[str] = Field(None, description="用户评论")


class UserSatisfactionRatingResponse(BaseModel):
    """用户满意度评价响应"""
    id: int
    task_id: str
    visual_quality: int
    text_readability: int
    stain_removal: int
    color_restoration: int
    overall_satisfaction: int
    comments: Optional[str]
    created_at: str


class EvaluationReportResponse(BaseModel):
    """评估报告响应"""
    image_quality: dict
    ocr_accuracy: Optional[dict] = None
    overall_score: dict
    interpretations: dict

