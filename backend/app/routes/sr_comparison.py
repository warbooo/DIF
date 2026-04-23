"""
超分对比 API
提供直接对比原图和修复图的功能
"""
from __future__ import annotations

import base64
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..db.models import User
from ..deps import get_optional_user
from ..services.ocr_subprocess import get_ocr_service
from ..services.evaluation import calculate_image_quality_metrics
from ..services.super_resolution_comparison import compare_sr_ocr_improvement

router = APIRouter(prefix="/api/sr-comparison", tags=["超分对比"])


@router.post("/direct-compare")
async def direct_compare_images(
    original_file: UploadFile = File(...),
    repaired_file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_optional_user),
) -> Dict[str, Any]:
    """
    直接对比原图和修复图，不重新执行超分
    
    Args:
        original_file: 原始图片
        repaired_file: 修复后的图片
    
    Returns:
        对比结果和评估指标
    """
    import time
    start_time = time.time()
    print("="*60)
    print("开始直接图片对比")
    print("="*60)
    
    # 读取两个文件
    step1_start = time.time()
    original_contents = await original_file.read()
    repaired_contents = await repaired_file.read()
    print(f"[耗时] 文件读取：{(time.time() - step1_start)*1000:.0f}ms")
    print(f"[INFO] 原图大小：{len(original_contents)/1024:.2f}KB, 修复图大小：{len(repaired_contents)/1024:.2f}KB")
    
    if not original_contents or not repaired_contents:
        raise HTTPException(status_code=400, detail="文件为空")
    
    # 对原始图像进行 OCR 识别（与 OCR 识别模块一致）
    print(f"\n[步骤 1] 对原始图像进行 OCR 识别...")
    try:
        # 直接使用原始图像进行 OCR 识别，与 OCR 识别模块一致
        ocr_start = time.time()
        print("[OCR] 开始 OCR 识别...")
        from ..services.ocr_subprocess import get_ocr_service
        ocr_service = get_ocr_service()
        
        # 不启用拼写纠错，与 OCR 模块的原始识别结果一致
        recognize_start = time.time()
        original_ocr = ocr_service.recognize(original_contents, enable_spell_correction=False)
        print(f"[耗时] OCR 识别：{(time.time() - recognize_start)*1000:.0f}ms")
        
        # 不启用拼写纠错，与用户初衷一致
        original_text = original_ocr.get('text', '')
        original_confidences = original_ocr.get('confidences', [])
        
        # 保存原始图像数据用于 SSIM 计算
        original_processed_contents = original_contents
        
        print(f"OK 原图 OCR 完成：{len(original_text.split(chr(10)))} 行文字")
        print(f"[DEBUG] 原图 OCR 文字：{original_text[:100]}...")
        print(f"[DEBUG] 原图 OCR 完整文字：{original_text}")
        print(f"[耗时] 原图处理总耗时：{(time.time() - ocr_start)*1000:.0f}ms")
    except Exception as e:
        print(f"WARNING 原图 OCR 异常：{e}")
        import traceback
        traceback.print_exc()
        original_text = ""
        original_confidences = []
        original_processed_contents = original_contents
    
    # 对修复后图像进行 OCR 识别（与 OCR 识别模块一致）
    print(f"\n[步骤 2] 对修复后图像进行 OCR 识别...")
    try:
        # 直接使用原始图像进行 OCR 识别，与 OCR 识别模块一致
        ocr_start = time.time()
        print("[OCR] 开始 OCR 识别...")
        from ..services.ocr_subprocess import get_ocr_service
        ocr_service = get_ocr_service()
        
        # 不启用拼写纠错，与 OCR 模块的原始识别结果一致
        recognize_start = time.time()
        repaired_ocr = ocr_service.recognize(repaired_contents, enable_spell_correction=False)
        print(f"[耗时] OCR 识别：{(time.time() - recognize_start)*1000:.0f}ms")
        
        # 不启用拼写纠错，与用户初衷一致
        repaired_text = repaired_ocr.get('text', '')
        repaired_confidences = repaired_ocr.get('confidences', [])
        
        # 保存原始图像数据用于 SSIM 计算
        repaired_processed_contents = repaired_contents
        
        print(f"OK 修复图 OCR 完成：{len(repaired_text.split(chr(10)))} 行文字")
        print(f"[DEBUG] 修复图 OCR 文字：{repaired_text[:100]}...")
        print(f"[DEBUG] 修复图 OCR 完整文字：{repaired_text}")
        print(f"[耗时] 修复图处理总耗时：{(time.time() - ocr_start)*1000:.0f}ms")
    except Exception as e:
        print(f"WARNING 修复图 OCR 异常：{e}")
        import traceback
        traceback.print_exc()
        repaired_text = ""
        repaired_confidences = []
        repaired_processed_contents = repaired_contents
    
    # 使用 OCR 结果中的置信度
    # 确保置信度列表不为空
    original_confidences = original_ocr.get('confidences', []) if 'original_ocr' in locals() else []
    repaired_confidences = repaired_ocr.get('confidences', []) if 'repaired_ocr' in locals() else []
    
    # 对比文本
    print(f"\n[步骤 3] 对比文本...")
    step3_start = time.time()
    comparison_result = compare_sr_ocr_improvement(
        original_text,
        original_confidences,
        repaired_text,
        repaired_confidences
    )
    print(f"[耗时] 文本对比：{(time.time() - step3_start)*1000:.0f}ms")
    
    # 计算平均置信度（无论指标计算是否成功都返回）
    original_avg_confidence = sum(original_confidences) / len(original_confidences) if original_confidences else 0
    repaired_avg_confidence = sum(repaired_confidences) / len(repaired_confidences) if repaired_confidences else 0
    print(f"\n[步骤 4] 原图平均置信度：{original_avg_confidence:.2%}, 修复后平均置信度：{repaired_avg_confidence:.2%}")
    
    # 计算评估指标
    print(f"\n[步骤 5] 计算评估指标...")
    step5_start = time.time()
    metrics = None
    
    try:
        # 开发环境下重新导入模块，避免缓存问题
        import importlib
        import sys
        
        # 重新导入 ocr_evaluation 模块
        if 'app.services.ocr_evaluation' in sys.modules:
            ocr_eval_module = importlib.reload(sys.modules['app.services.ocr_evaluation'])
        else:
            from ..services import ocr_evaluation as ocr_eval_module
        
        # 使用 OCRAnalyzer
        analyzer = ocr_eval_module.get_analyzer()
        
        # 使用修复后的文本作为基准
        ocr_metrics_start = time.time()
        ocr_metrics = analyzer.evaluate(original_text, repaired_text)
        print(f"[耗时] OCR 评估计算：{(time.time() - ocr_metrics_start)*1000:.0f}ms")
        
        # 计算图片质量指标
        base64_start = time.time()
        # 使用处理后的图像数据计算 SSIM，确保比较的是相同处理流程的图像
        original_b64 = base64.b64encode(original_processed_contents).decode('utf-8')
        repaired_b64 = base64.b64encode(repaired_processed_contents).decode('utf-8')
        print(f"[耗时] Base64 编码：{(time.time() - base64_start)*1000:.0f}ms")
        
        image_quality_start = time.time()
        image_metrics = calculate_image_quality_metrics(original_b64, repaired_b64)
        print(f"[耗时] 图片质量计算：{(time.time() - image_quality_start)*1000:.0f}ms")
        print(f"[步骤 5] 图片质量指标：{image_metrics}")
        
        # 只要有图片指标就返回（OCR 评估是可选的）
        if image_metrics:
            metrics = {
                "psnr": image_metrics.get("psnr", 0),
                "ssim": image_metrics.get("ssim", 0),
                # OCR 置信度指标
                "original_confidence": original_avg_confidence,
                "repaired_confidence": repaired_avg_confidence,
                "confidence_improvement": repaired_avg_confidence - original_avg_confidence,
            }
            
            print(f"OK 评估指标计算完成：{metrics}")
            print(f"OK OCR 置信度改善：{original_avg_confidence:.4f} -> {repaired_avg_confidence:.4f} (提升：{repaired_avg_confidence - original_avg_confidence:.4f})")
        else:
            print(f"WARNING 评估指标计算失败")
            metrics = None
        print(f"[耗时] 评估指标总耗时：{(time.time() - step5_start)*1000:.0f}ms")
    except Exception as e:
        print(f"WARNING 评估指标计算异常：{e}")
        import traceback
        traceback.print_exc()
        metrics = None
    
    total_time = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"TIME  总耗时：{total_time*1000:.0f}ms ({total_time:.2f}秒)")
    print(f"{'='*60}")
    print("直接对比完成")
    print("="*60)
    
    return {
        "success": True,
        "comparison": comparison_result,
        "metrics": metrics,
        "ocr_data": {
            "original": {
                "text": original_text,
                "confidence": original_avg_confidence,
                "line_count": len(original_text.split(chr(10))) if original_text else 0,
                "char_count": len(original_text.replace(' ', '').replace(chr(10), '')) if original_text else 0,
            },
            "repaired": {
                "text": repaired_text,
                "confidence": repaired_avg_confidence,
                "line_count": len(repaired_text.split(chr(10))) if repaired_text else 0,
                "char_count": len(repaired_text.replace(' ', '').replace(chr(10), '')) if repaired_text else 0,
            }
        },
        "metadata": {
            "original_size": len(original_contents),
            "repaired_size": len(repaired_contents),
            "processing_time_ms": int(total_time * 1000),
        }
    }
