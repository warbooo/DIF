"""
异步任务API路由
提供后台任务的提交、查询、取消等功能
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional

from ..deps import get_current_user, get_db
from ..db.models import User, RepairTask
from ..services.async_task_queue import (
    get_task_queue,
    TaskStatus,
    Task
)
from ..services.doc_repair import repair_document
from ..services.storage import save_upload_bytes, save_result_image_bytes, new_task_id
from ..services.pdf_processor import is_pdf_file, process_pdf
import base64

router = APIRouter(prefix="/api/async-tasks", tags=["async-tasks"])


def _b64_to_bytes(b64: str) -> bytes:
    """Base64转字节"""
    return base64.b64decode(b64)


def _task_to_dict(task: Task) -> Dict[str, Any]:
    """将Task对象转换为字典"""
    return {
        "task_id": task.task_id,
        "status": task.status.value,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "progress": task.progress,
        "progress_message": task.progress_message,
        "metadata": task.metadata,
        "error": task.error,
        "has_result": task.result is not None
    }


@router.post("/repair")
async def submit_async_repair(
    file: UploadFile = File(...),
    doc_type: str = Form("document"),
    pdf_page: int = Form(1),
    use_super_resolution: str = Form("true"),
    sr_model_type: str = Form("auto"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    提交异步文档修复任务
    
    任务会在后台执行，不会阻塞请求
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")
    
    task_queue = get_task_queue()
    use_super_resolution_flag = use_super_resolution.lower() == "true"
    
    # 处理内容
    processed_contents = contents
    processing_info = {}
    
    # 检查是否为PDF文件
    if is_pdf_file(file.filename):
        try:
            processed_contents, processing_info = process_pdf(contents, file.filename, page=pdf_page)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"PDF处理失败: {str(e)}")
    
    # 生成任务key
    task_key = new_task_id()
    
    # 保存上传文件
    upload_path = save_upload_bytes(contents, file.filename, user_id=current_user.id)
    
    # 定义后台执行函数
    def background_task(task_id: str):
        try:
            # 更新进度
            task_queue.update_progress(task_id, 10, "正在读取图像...")
            
            # 执行文档修复
            task_queue.update_progress(task_id, 20, "正在预处理图像...")
            
            result = repair_document(
                processed_contents,
                filename=file.filename,
                doc_type=doc_type,
                use_super_resolution=use_super_resolution_flag,
                sr_model_type=sr_model_type,
                task_id=task_id
            )
            
            task_queue.update_progress(task_id, 80, "正在保存结果...")
            
            # 保存结果
            repaired_b64 = result["repaired_image_base64"]
            repaired_bytes = _b64_to_bytes(repaired_b64)
            save_result_image_bytes(
                repaired_bytes,
                task_id=task_key,
                user_id=current_user.id,
                filename="repaired.png"
            )
            
            task_queue.update_progress(task_id, 90, "正在更新数据库...")
            
            # 保存到数据库
            meta = result.get("meta", {})
            if processing_info:
                meta["pdf_processing"] = processing_info
            
            task = RepairTask(
                task_key=task_key,
                user_id=current_user.id,
                original_filename=file.filename,
                doc_type=doc_type,
                status="done",
                ocr_text=result.get("ocr_text", "") or "",
                filled_text=result.get("filled_text", "") or "",
                repaired_relpath=f"{task_key}_repaired.png",
                meta=meta,
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            
            task_queue.update_progress(task_id, 100, "处理完成")
            
            return {
                "success": True,
                "task_key": task_key,
                "result": result
            }
            
        except Exception as e:
            # 保存失败状态
            task = RepairTask(
                task_key=task_key,
                user_id=current_user.id,
                original_filename=file.filename,
                status="failed",
                ocr_text="",
                filled_text="",
                repaired_relpath=None,
                meta={"error": "repair_failed"} if not processing_info else {"error": "repair_failed", "pdf_processing": processing_info},
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            raise
    
    # 提交异步任务
    async_task_id = task_queue.submit_task(
        background_task,
        metadata={
            "filename": file.filename,
            "doc_type": doc_type,
            "user_id": current_user.id,
            "task_key": task_key
        }
    )
    
    return {
        "success": True,
        "async_task_id": async_task_id,
        "task_key": task_key,
        "message": "任务已提交，正在后台处理中"
    }


@router.get("/{task_id}")
async def get_task_status(task_id: str, current_user: User = Depends(get_current_user)):
    """
    获取异步任务状态
    """
    task_queue = get_task_queue()
    task = task_queue.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task_dict = _task_to_dict(task)
    
    # 如果任务完成，包含结果
    if task.status == TaskStatus.COMPLETED and task.result:
        task_dict["result"] = task.result
    
    return {
        "success": True,
        "task": task_dict
    }


@router.get("/")
async def list_tasks(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    列出所有异步任务
    """
    task_queue = get_task_queue()
    
    status_enum = None
    if status:
        try:
            status_enum = TaskStatus(status)
        except ValueError:
            pass
    
    tasks = task_queue.list_tasks(status=status_enum)
    
    # 过滤出当前用户的任务
    user_tasks = []
    for task in tasks:
        if task.metadata.get("user_id") == current_user.id:
            user_tasks.append(_task_to_dict(task))
    
    return {
        "success": True,
        "count": len(user_tasks),
        "tasks": user_tasks
    }


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str, current_user: User = Depends(get_current_user)):
    """
    取消异步任务
    """
    task_queue = get_task_queue()
    task = task_queue.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 验证任务归属
    if task.metadata.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此任务")
    
    success = task_queue.cancel_task(task_id)
    
    return {
        "success": success,
        "message": "任务已取消" if success else "任务无法取消"
    }


@router.delete("/cleanup")
async def cleanup_old_tasks(
    older_than_hours: int = 24,
    current_user: User = Depends(get_current_user)
):
    """
    清理旧任务（仅管理员）
    """
    # 这里可以添加管理员权限检查
    task_queue = get_task_queue()
    task_queue.cleanup_completed_tasks(older_than_hours=older_than_hours)
    
    return {
        "success": True,
        "message": f"已清理{older_than_hours}小时前的已完成任务"
    }
