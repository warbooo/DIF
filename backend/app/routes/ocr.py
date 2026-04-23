from __future__ import annotations

import time
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from sqlalchemy.orm import Session

from ..deps import get_current_user
from ..db.session import get_db
from ..db.models import User
from ..services.ocr_subprocess import get_ocr_service
from ..services.ocr_postprocessing import get_post_processor

router = APIRouter(prefix="/api/ocr", tags=["ocr"])


@router.post("/recognize")
async def ocr_recognize(
    file: UploadFile = File(...),
    enable_spell_correction: str = Form("true"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    OCR 识别与后处理
    
    Args:
        file: 上传的图片文件
        enable_spell_correction: 是否启用拼写纠错 ("true"/"false")
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        OCR 识别结果
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")
    
    # 转换字符串为布尔值
    enable_spell = enable_spell_correction.lower() == "true"
    
    print(f"\n[OCR API] 收到请求，enable_spell_correction={enable_spell_correction}, 转换后={enable_spell}")
    
    start_time = time.time()
    
    try:
        # 1. OCR 识别
        ocr_start = time.time()
        ocr_service = get_ocr_service()
        ocr_result = ocr_service.recognize(contents)
        ocr_time = time.time() - ocr_start
        
        if not ocr_result.get("success", False):
            raise HTTPException(
                status_code=500, 
                detail=ocr_result.get("message", "OCR 识别失败")
            )
        
        raw_text = ocr_result.get("text", "")
        
        # 2. 后处理（拼写纠错）
        corrected_text = ""
        correction_time = 0.0
        
        if enable_spell:
            print(f"[OCR API] 开始拼写纠错...")
            correction_start = time.time()
            post_processor = get_post_processor()
            post_result = post_processor.process(
                ocr_result, 
                enable_spell_correction=True
            )
            corrected_text = post_result.get("processed_text", raw_text)
            correction_time = time.time() - correction_start
            print(f"[OCR API] 纠错完成，耗时 {correction_time:.3f}s")
        else:
            print(f"[OCR API] 未启用拼写纠错")
            corrected_text = raw_text
        
        total_time = time.time() - start_time
        
        # 计算字符数
        char_count = len(corrected_text) if corrected_text else len(raw_text)
        
        return {
            "raw_text": raw_text,
            "corrected_text": corrected_text if enable_spell else None,
            "ocr_time": round(ocr_time, 3),
            "correction_time": round(correction_time, 3) if enable_spell else 0,
            "total_time": round(total_time, 3),
            "char_count": char_count,
            "confidence": ocr_result.get("confidence", 0.0),
            "confidences": ocr_result.get("confidences", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OCR处理失败: {str(e)}"
        )
