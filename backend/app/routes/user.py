from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..deps import get_current_user
from ..db.session import get_db
from ..db.models import User, RepairTask
from ..core.security import hash_password, verify_password, decode_token

# 创建 bearer scheme
bearer_scheme = HTTPBearer(auto_error=False)

router = APIRouter(prefix="/api/user", tags=["user"])


class UserProfileResponse(BaseModel):
    id: int
    username: str
    created_at: str

    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    pass


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=8, max_length=256)


class HistoryRecordResponse(BaseModel):
    task_key: str
    original_filename: str
    status: str
    created_at: str
    updated_at: str
    ocr_text: str
    filled_text: str

    class Config:
        from_attributes = True


class UserFileResponse(BaseModel):
    task_key: str
    filename: str
    status: str
    created_at: str
    has_result: bool

    class Config:
        from_attributes = True


@router.get("/profile", response_model=UserProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserProfileResponse:
    """获取用户个人信息"""
    return UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        created_at=current_user.created_at.isoformat() if current_user.created_at else ""
    )

@router.put("/profile", response_model=UserProfileResponse)
def update_profile(
    req: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserProfileResponse:
    """更新用户个人信息（当前无实际更新内容，保留接口以备扩展）"""
    db.commit()
    db.refresh(current_user)
    
    return UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        created_at=current_user.created_at.isoformat() if current_user.created_at else ""
    )

@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """修改密码"""
    if not verify_password(req.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="原密码错误")
    
    current_user.hashed_password = hash_password(req.new_password)
    db.commit()
    
    return {"success": True, "message": "密码修改成功"}


@router.get("/history", response_model=List[HistoryRecordResponse])
def get_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[HistoryRecordResponse]:
    """获取用户历史处理记录"""
    # 先获取任务，然后在 Python 中过滤和排序
    tasks = db.query(RepairTask).filter(
        RepairTask.user_id == current_user.id,
        RepairTask.task_key != None
    ).limit(limit * 2).all()
    
    # 在 Python 中过滤和排序
    valid_tasks = [t for t in tasks if t.task_key and t.created_at]
    valid_tasks.sort(key=lambda t: t.created_at, reverse=True)
    tasks = valid_tasks[skip:skip + limit]
    
    result = []
    for task in tasks:
        try:
            # 处理字符串类型的时间
            def format_time(time_val):
                if not time_val:
                    return ""
                if isinstance(time_val, str):
                    return time_val
                try:
                    return time_val.isoformat()
                except Exception:
                    return str(time_val)
            
            result.append(HistoryRecordResponse(
                task_key=task.task_key,
                original_filename=task.original_filename,
                status=task.status,
                created_at=format_time(task.created_at),
                updated_at=format_time(task.updated_at),
                ocr_text=task.ocr_text or "",
                filled_text=task.filled_text or ""
            ))
        except Exception as e:
            print(f"[User] 处理历史记录 {getattr(task, 'original_filename', 'unknown')} 时出错：{e}")
            import traceback
            traceback.print_exc()
            continue
    
    return result


@router.get("/history/count")
def get_history_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """获取用户历史记录总数"""
    count = db.query(RepairTask).filter(RepairTask.user_id == current_user.id).count()
    return {"total": count}


@router.get("/files", response_model=List[UserFileResponse])
def get_user_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[UserFileResponse]:
    """获取用户个人文件库"""
    tasks = db.query(RepairTask).filter(
        RepairTask.user_id == current_user.id
    ).order_by(
        RepairTask.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    result = []
    for task in tasks:
        try:
            if not task.task_key:
                continue
            
            # 处理字符串类型的时间
            def format_time(time_val):
                if not time_val:
                    return ""
                if isinstance(time_val, str):
                    return time_val
                try:
                    return time_val.isoformat()
                except Exception:
                    return str(time_val)
            
            result.append(UserFileResponse(
                task_key=task.task_key,
                filename=task.original_filename,
                status=task.status,
                created_at=format_time(task.created_at),
                has_result=task.repaired_relpath is not None and task.status == "done"
            ))
        except Exception as e:
            print(f"[User] 处理文件 {getattr(task, 'original_filename', 'unknown')} 时出错：{e}")
            import traceback
            traceback.print_exc()
            continue
    
    return result


@router.delete("/files/{task_key}")
def delete_user_file(
    task_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """删除用户文件"""
    task = db.query(RepairTask).filter(
        RepairTask.task_key == task_key,
        RepairTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    db.delete(task)
    db.commit()
    
    return {"success": True, "message": "文件删除成功"}
