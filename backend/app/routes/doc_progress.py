from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ..services.progress_manager import progress_manager

router = APIRouter(prefix="/api/doc/progress", tags=["progress"])


@router.get("/{task_id}")
async def get_task_progress(task_id: str) -> Dict[str, Any]:
    """
    查询任务进度
    
    Args:
        task_id: 任务ID
    
    Returns:
        任务进度信息
    """
    progress = progress_manager.get_progress(task_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "success": True,
        "task_id": task_id,
        "progress": progress
    }


@router.get("/")
async def list_active_tasks() -> Dict[str, Any]:
    """
    列出所有活动任务
    
    Returns:
        活动任务列表
    """
    # 这里可以返回所有正在进行的任务
    # 简化实现，返回空列表
    return {
        "success": True,
        "tasks": []
    }
