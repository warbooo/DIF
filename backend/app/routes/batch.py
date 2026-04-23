"""批量处理与任务管理接口"""

import os
import zipfile
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..db.models import User
from ..deps import get_current_user

router = APIRouter(prefix="/api/batch", tags=["batch"])


@router.post("/upload")
async def batch_upload_and_process(
    files: List[UploadFile] = File(...),
    use_super_resolution: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    批量上传并处理图片
    
    支持：
    - 多张图片直接上传
    - 压缩包文件（zip），自动解压后处理
    - 文件夹上传（前端 webkitdirectory 支持）
    """
    if not files:
        raise HTTPException(status_code=400, detail="没有上传任何文件")
    
    results = []
    temp_dir = None
    
    try:
        # 处理每个上传的文件
        for file in files:
            # 检查是否是压缩包
            if file.filename and file.filename.endswith('.zip'):
                # 创建临时目录解压
                temp_dir = Path(f"./temp/batch_{current_user.id}")
                temp_dir.mkdir(parents=True, exist_ok=True)
                
                # 保存并解压压缩包
                zip_path = temp_dir / file.filename
                with open(zip_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                try:
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                except Exception as e:
                    results.append({
                        "filename": file.filename,
                        "status": "failed",
                        "error": f"解压失败：{str(e)}"
                    })
                    continue
                
                # 处理解压后的图片
                for img_path in temp_dir.glob("**/*"):
                    if img_path.is_file() and img_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp']:
                        # 读取图片
                        with open(img_path, 'rb') as f:
                            img_data = f.read()
                        
                        # 这里简化处理，实际应该调用修复服务
                        results.append({
                            "filename": img_path.name,
                            "status": "pending",
                            "message": "已添加到处理队列"
                        })
                
                # 清理临时文件
                shutil.rmtree(temp_dir)
                temp_dir = None
                
            elif file.content_type and file.content_type.startswith('image/'):
                # 直接处理图片（简化处理）
                results.append({
                    "filename": file.filename,
                    "status": "pending",
                    "message": "已添加到处理队列"
                })
        
        return {
            "total": len(files),
            "success": len([r for r in results if r["status"] != "failed"]),
            "failed": len([r for r in results if r["status"] == "failed"]),
            "results": results
        }
        
    except Exception as e:
        # 清理临时文件
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir)
        raise HTTPException(status_code=500, detail=f"批量处理失败：{str(e)}")
