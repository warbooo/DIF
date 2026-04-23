from __future__ import annotations

import base64
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional

from ..deps import get_current_user, bearer_scheme, get_optional_user
from ..core.security import decode_token
from ..core.settings import storage_root
from ..db.session import get_db
from ..db.models import RepairTask, User, OcrResult, CompletionLog
from ..schemas.history import HistoryItem, OcrResultItem, CompletionLogItem

router = APIRouter(prefix="/api/history", tags=["history"])


def utc_to_local(utc_dt) -> datetime:
    """将 UTC 时间转换为本地时间"""
    if utc_dt is None:
        return None
    if isinstance(utc_dt, str):
        try:
            if ' ' in utc_dt:
                utc_dt = utc_dt.replace(' ', 'T')
            utc_dt = datetime.fromisoformat(utc_dt)
        except Exception as e:
            print(f"[History] 解析时间字符串失败：{e}")
            return datetime.now()
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone()


@router.get("", response_model=List[HistoryItem])
def list_history(
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> List[HistoryItem]:
    """
    获取历史记录（已优化批量查询）
    """
    print("[History] 开始获取历史记录")
    
    # 确定用户 ID
    if current_user:
        user_id = current_user.id
        print(f"[History] 已登录用户 ID: {user_id}")
    else:
        test_user = db.query(User).filter(User.id == 3).first()
        if test_user:
            user_id = test_user.id
            print(f"[History] 未登录，使用测试用户 ID: {user_id}")
        else:
            last_user = db.query(User).order_by(User.id.desc()).first()
            if last_user:
                user_id = last_user.id
                print(f"[History] 未登录，使用最后一个用户 ID: {user_id}")
            else:
                print("[History] 数据库中没有用户")
                return []
    
    # 查询任务列表（只加载最近 10 条）
    print(f"[History] 查询用户 ID {user_id} 的任务（最近 10 条）")
    tasks = (
        db.query(RepairTask)
        .filter(RepairTask.user_id == user_id)
        .order_by(RepairTask.id.desc())
        .limit(10)
        .all()
    )
    print(f"[History] 找到 {len(tasks)} 个任务")
    
    # 批量查询 OCR 结果和补全日志（关键优化）
    if tasks:
        task_ids = [task.id for task in tasks]
        
        # 一次性查询所有 OCR 结果（1 次查询替代 50 次）
        print(f"[History] 批量查询 OCR 结果...")
        ocr_results_map = {
            ocr.task_id: ocr 
            for ocr in db.query(OcrResult).filter(OcrResult.task_id.in_(task_ids)).all()
        }
        
        # 一次性查询所有补全日志（1 次查询替代 50 次）
        print(f"[History] 批量查询补全日志...")
        completion_logs_map = {
            comp.task_id: comp 
            for comp in db.query(CompletionLog).filter(CompletionLog.task_id.in_(task_ids)).all()
        }
    else:
        ocr_results_map = {}
        completion_logs_map = {}
    
    # 构建返回结果
    history_items = []
    for task in tasks:
        try:
            # 从批量查询结果中获取数据
            ocr_data = ocr_results_map.get(task.id)
            ocr_results = []
            if ocr_data:
                ocr_results.append(OcrResultItem(
                    text=ocr_data.raw_text,
                    confidence=ocr_data.confidence
                ))
            
            completion_data = completion_logs_map.get(task.id)
            completion = None
            if completion_data:
                completion = CompletionLogItem(
                    input_text=completion_data.original_text,
                    completed_text=completion_data.completed_text,
                    completion_type=completion_data.completion_type,
                    tokens_used=completion_data.word_count if hasattr(completion_data, 'word_count') else 0,
                    duration=completion_data.processing_time,
                    status="success" if completion_data.success else "failed"
                )
            
            local_time = utc_to_local(task.created_at)
            
            # 从 meta 中提取超分信息
            sr_model_type = task.meta.get("sr_model_type") if task.meta else None
            sr_scale = task.meta.get("sr_scale") if task.meta else None
            
            history_item = HistoryItem(
                id=task.id,  # 添加数据库主键 ID
                task_id=task.task_key,
                original_filename=task.original_filename,
                status=task.status,
                created_at=local_time.isoformat(),
                input_text=ocr_data.raw_text if ocr_data else task.ocr_text,
                ocr_results=ocr_results if ocr_results else None,
                completion_log=completion,
                sr_model_type=sr_model_type,
                sr_scale=sr_scale
            )
            
            history_items.append(history_item)
        except Exception as e:
            print(f"[History] 处理任务 {task.task_key} 时出错：{e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"[History] 总共添加了 {len(history_items)} 个任务到历史记录")
    return history_items


@router.get("/{task_id}", response_model=HistoryItem)
def get_task(
    task_id: str, 
    current_user: Optional[User] = Depends(get_optional_user), 
    db: Session = Depends(get_db)
) -> HistoryItem:
    """获取单个任务详情"""
    if current_user:
        user_id = current_user.id
    else:
        test_user = db.query(User).filter(User.id == 3).first()
        if test_user:
            user_id = test_user.id
        else:
            last_user = db.query(User).order_by(User.id.desc()).first()
            if last_user:
                user_id = last_user.id
            else:
                raise HTTPException(status_code=404, detail="Task not found")
    
    task = db.query(RepairTask).filter(
        RepairTask.task_key == task_id, 
        RepairTask.user_id == user_id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return HistoryItem(
        task_id=task.task_key,
        original_filename=task.original_filename,
        status=task.status,
        created_at=utc_to_local(task.created_at).isoformat(),
    )


@router.get("/{task_id}/detail")
def get_task_detail(
    task_id: str, 
    current_user: Optional[User] = Depends(get_optional_user), 
    db: Session = Depends(get_db)
):
    """获取任务的完整详情"""
    if current_user:
        user_id = current_user.id
    else:
        test_user = db.query(User).filter(User.id == 3).first()
        if test_user:
            user_id = test_user.id
        else:
            last_user = db.query(User).order_by(User.id.desc()).first()
            if last_user:
                user_id = last_user.id
            else:
                raise HTTPException(status_code=404, detail="Task not found")
    
    task = db.query(RepairTask).filter(
        RepairTask.task_key == task_id, 
        RepairTask.user_id == user_id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 读取修复后的图片
    repaired_image_base64 = None
    original_image_base64 = None
    
    if task.repaired_relpath:
        try:
            root = storage_root()
            img_path = root / task.repaired_relpath
            
            if not img_path.exists() and task.repaired_relpath and '/' not in task.repaired_relpath:
                user_subdir = root / "results" / str(task.user_id)
                old_path = user_subdir / task.repaired_relpath
                if old_path.exists():
                    img_path = old_path
            
            if img_path.exists():
                with open(img_path, "rb") as f:
                    img_data = f.read()
                    repaired_image_base64 = base64.b64encode(img_data).decode("utf-8")
        except Exception as e:
            print(f"读取图片失败：{e}")
    
    if task.original_relpath:
        try:
            root = storage_root()
            original_img_path = root / task.original_relpath
            
            if not original_img_path.exists() and task.original_relpath and '/' not in task.original_relpath:
                user_subdir = root / "results" / str(task.user_id)
                old_path = user_subdir / task.original_relpath
                if old_path.exists():
                    original_img_path = old_path
            
            if original_img_path.exists():
                with open(original_img_path, "rb") as f:
                    img_data = f.read()
                    original_image_base64 = base64.b64encode(img_data).decode("utf-8")
        except Exception as e:
            print(f"读取原图失败：{e}")
    
    return {
        "task_id": task.task_key,
        "original_filename": task.original_filename,
        "status": task.status,
        "created_at": utc_to_local(task.created_at).isoformat(),
        "ocr_text": task.ocr_text,
        "filled_text": task.filled_text,
        "original_relpath": task.original_relpath,
        "repaired_relpath": task.repaired_relpath,
        "original_image_base64": original_image_base64,
        "repaired_image_base64": repaired_image_base64,
        "meta": task.meta,
    }
