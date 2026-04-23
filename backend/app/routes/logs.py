from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..deps import get_current_user
from ..db.session import get_db
from ..db.models import User, SystemLog

router = APIRouter(prefix="/api/logs", tags=["logs"])


class LogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    username: Optional[str] = None
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    ip_address: Optional[str]
    status: str
    duration: Optional[int]
    message: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[LogResponse])
async def get_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    action: Optional[str] = None,
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[LogResponse]:
    """获取系统日志列表"""
    query = db.query(SystemLog)
    
    # 过滤条件
    if action:
        query = query.filter(SystemLog.action == action)
    if status:
        query = query.filter(SystemLog.status == status)
    if user_id:
        query = query.filter(SystemLog.user_id == user_id)
    if start_date:
        query = query.filter(SystemLog.created_at >= start_date)
    if end_date:
        query = query.filter(SystemLog.created_at <= end_date)
    
    # 排序和分页
    logs = query.order_by(SystemLog.created_at.desc()).offset(skip).limit(limit).all()
    
    # 构建响应
    response = []
    for log in logs:
        log_dict = {
            "id": log.id,
            "user_id": log.user_id,
            "username": log.user.username if log.user else None,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "ip_address": log.ip_address,
            "status": log.status,
            "duration": log.duration,
            "message": log.message,
            "created_at": log.created_at.isoformat() if log.created_at else ""
        }
        response.append(LogResponse(**log_dict))
    
    return response


@router.get("/user", response_model=List[LogResponse])
async def get_user_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    action: Optional[str] = None,
    status: Optional[str] = None,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[LogResponse]:
    """获取当前用户的日志"""
    query = db.query(SystemLog).filter(SystemLog.user_id == current_user.id)
    
    # 过滤条件
    if action:
        query = query.filter(SystemLog.action == action)
    if status:
        query = query.filter(SystemLog.status == status)
    
    # 排序和分页
    logs = query.order_by(SystemLog.created_at.desc()).offset(skip).limit(limit).all()
    
    # 构建响应
    response = []
    for log in logs:
        log_dict = {
            "id": log.id,
            "user_id": log.user_id,
            "username": log.user.username if log.user else None,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "ip_address": log.ip_address,
            "status": log.status,
            "duration": log.duration,
            "message": log.message,
            "created_at": log.created_at.isoformat() if log.created_at else ""
        }
        response.append(LogResponse(**log_dict))
    
    return response


@router.get("/{log_id}", response_model=LogResponse)
async def get_log_detail(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> LogResponse:
    """获取日志详情"""
    log = db.query(SystemLog).filter(SystemLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    # 检查权限：只能查看自己的日志或管理员查看所有
    if log.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    log_dict = {
        "id": log.id,
        "user_id": log.user_id,
        "username": log.user.username if log.user else None,
        "action": log.action,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id,
        "ip_address": log.ip_address,
        "status": log.status,
        "duration": log.duration,
        "message": log.message,
        "created_at": log.created_at.isoformat() if log.created_at else ""
    }
    
    return LogResponse(**log_dict)


@router.get("/stats/summary")
async def get_log_stats(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """获取日志统计信息"""
    # 获取用户的日志统计
    total_logs = db.query(SystemLog).filter(SystemLog.user_id == current_user.id).count()
    success_logs = db.query(SystemLog).filter(
        SystemLog.user_id == current_user.id,
        SystemLog.status == "success"
    ).count()
    error_logs = db.query(SystemLog).filter(
        SystemLog.user_id == current_user.id,
        SystemLog.status == "error"
    ).count()
    
    # 获取最近的操作
    recent_logs = db.query(SystemLog).filter(
        SystemLog.user_id == current_user.id
    ).order_by(SystemLog.created_at.desc()).limit(5).all()
    
    recent_activities = []
    for log in recent_logs:
        recent_activities.append({
            "action": log.action,
            "status": log.status,
            "duration": log.duration,
            "created_at": log.created_at.isoformat() if log.created_at else ""
        })
    
    return {
        "total_logs": total_logs,
        "success_logs": success_logs,
        "error_logs": error_logs,
        "success_rate": round((success_logs / total_logs * 100) if total_logs > 0 else 0, 2),
        "recent_activities": recent_activities
    }
