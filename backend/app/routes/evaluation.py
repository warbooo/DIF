"""
评估指标 API
提供图片修复和文字修复的客观评估指标
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime

from ..deps import get_current_user, get_db
from ..db.models import User
from ..services.evaluation import (
    calculate_image_quality_metrics,
    calculate_character_error_rate,
    get_metric_explanation
)

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


@router.post("/submit-rating")
async def submit_task_rating(
    task_id: int,
    rating: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    提交任务评价（1-5 星）
    
    Args:
        task_id: 任务 ID
        rating: 评分（1-5）
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        提交结果
    """
    print(f"[Rating] 收到评价提交请求：task_id={task_id}, rating={rating}, user_id={current_user.id}")
    
    # 验证评分范围
    if rating < 1 or rating > 5:
        print(f"[Rating] 评分无效：{rating}")
        raise HTTPException(status_code=400, detail="评分必须在 1-5 星之间")
    
    try:
        # 导入任务模型
        from ..db.models import TaskRating
        
        # 检查是否已有评价
        existing_rating = db.query(TaskRating).filter(
            TaskRating.task_id == task_id,
            TaskRating.user_id == current_user.id
        ).first()
        
        if existing_rating:
            # 更新已有评价
            print(f"[Rating] 更新已有评价：id={existing_rating.id}, old_rating={existing_rating.rating}")
            existing_rating.rating = rating
            existing_rating.updated_at = datetime.utcnow()
        else:
            # 创建新评价
            print(f"[Rating] 创建新评价")
            new_rating = TaskRating(
                task_id=task_id,
                user_id=current_user.id,
                rating=rating,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(new_rating)
        
        db.commit()
        print(f"[Rating] 评价提交成功")
        
        return {
            "success": True,
            "message": "评价已提交",
            "rating": rating
        }
    except Exception as e:
        db.rollback()
        print(f"[Rating] 评价提交失败：{e}")
        raise HTTPException(status_code=500, detail=f"提交失败：{str(e)}")


@router.get("/get-rating/{task_id}")
async def get_task_rating(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取用户对任务的评价
    
    Args:
        task_id: 任务 ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        用户评价（如果有）
    """
    try:
        # 导入任务模型
        from ..db.models import TaskRating
        
        # 查询评价
        rating = db.query(TaskRating).filter(
            TaskRating.task_id == task_id,
            TaskRating.user_id == current_user.id
        ).first()
        
        if rating:
            return {
                "success": True,
                "rating": rating.rating,
                "created_at": rating.created_at.isoformat() if rating.created_at else None,
                "updated_at": rating.updated_at.isoformat() if rating.updated_at else None
            }
        else:
            return {
                "success": True,
                "rating": None
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@router.get("/list-ratings")
async def list_all_ratings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取当前用户的所有评价记录
    
    Args:
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        评价列表
    """
    try:
        # 导入任务模型
        from ..db.models import TaskRating
        
        # 查询当前用户的所有评价
        ratings = db.query(TaskRating).filter(
            TaskRating.user_id == current_user.id
        ).order_by(TaskRating.created_at.desc()).all()
        
        rating_list = []
        for r in ratings:
            rating_list.append({
                "id": r.id,
                "task_id": r.task_id,
                "rating": r.rating,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None
            })
        
        return {
            "success": True,
            "count": len(rating_list),
            "ratings": rating_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@router.post("/image-quality")
async def evaluate_image_quality(
    original_image: UploadFile = File(...),
    repaired_image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    评估图片修复质量
    
    Args:
        original_image: 原图
        repaired_image: 修复后图片
        
    Returns:
        PSNR、SSIM、LPIPS等评估指标
    """
    try:
        import base64
        
        # 读取图片并转换为base64
        original_contents = await original_image.read()
        repaired_contents = await repaired_image.read()
        
        original_b64 = base64.b64encode(original_contents).decode('utf-8')
        repaired_b64 = base64.b64encode(repaired_contents).decode('utf-8')
        
        # 计算评估指标
        metrics = calculate_image_quality_metrics(original_b64, repaired_b64)
        
        return {
            "success": True,
            "metrics": metrics,
            "explanation": get_metric_explanation()['image_metrics']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"评估失败: {str(e)}")


@router.post("/text-quality")
async def evaluate_text_quality(
    original_text: str = Form(...),
    repaired_text: str = Form(...),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    评估文字修复质量
    
    Args:
        original_text: 原图OCR文本
        repaired_text: 修复后OCR文本
        
    Returns:
        CER等评估指标
    """
    try:
        # 计算评估指标
        metrics = calculate_character_error_rate(original_text, repaired_text)
        
        return {
            "success": True,
            "metrics": metrics,
            "explanation": get_metric_explanation()['text_metrics']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"评估失败: {str(e)}")


@router.get("/explanation")
async def get_evaluation_explanation() -> Dict[str, Any]:
    """
    获取评估指标说明
    """
    return {
        "success": True,
        "explanation": get_metric_explanation()
    }
