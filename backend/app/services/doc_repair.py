"""
文档修复服务
提供文档图像修复、OCR 识别、文字补全等功能
"""
from __future__ import annotations

import base64
import io
import time
from typing import Any, Dict, Optional

from PIL import Image, ImageEnhance, ImageFilter

from ..core.settings import settings
from .performance_monitor import get_timer, format_duration

# 导入 OCR 服务
# from .ocr_paddle_ocr import None

# 导入超分服务
from .swin2sr_service import get_sr_service, enhance_image


def _read_image_bytes_as_pil(data: bytes) -> Image.Image:
    """将图像字节数据转换为 PIL Image"""
    try:
        img = Image.open(io.BytesIO(data))
        return img.convert("RGB")
    except Exception as e:
        raise ValueError("Invalid image bytes") from e


def preprocess_image(image: Image.Image) -> Image.Image:
    """
    预处理 - 轻微对比度调整
    
    Args:
        image: PIL Image 对象
    
    Returns:
        处理后的 PIL Image 对象
    """
    from PIL import ImageEnhance
    
    print("[预处理] 开始文档图像预处理...")
    
    # 仅做轻微对比度调整，避免过度锐化
    print("[预处理] 轻微对比度调整...")
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.05)  # 仅 5% 对比度提升
    print("[预处理] 预处理完成")
    return image


def postprocess_image(image: Image.Image) -> Image.Image:
    """
    后处理 - 轻微锐化和对比度调整
    
    Args:
        image: PIL Image 对象
    
    Returns:
        处理后的 PIL Image 对象
    """
    print("[后处理] 开始后处理...")
    
    # 1. 轻微锐化
    print("[后处理] 轻微锐化...")
    from PIL import ImageFilter
    image = image.filter(ImageFilter.UnsharpMask(radius=0.5, percent=80, threshold=3))
    
    # 2. 对比度调整
    print("[后处理] 对比度调整...")
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.08)  # 8% 对比度提升
    # 3. 亮度微调
    print("[后处理] 亮度微调...")
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1.02)  # 2% 亮度提升
    
    print("[后处理] 后处理完成")
    return image


def repair_image(data: bytes) -> bytes:
    """
    修复图像 - 预处理 + 超分 + OCR
    
    Args:
        data: 图像字节数据
    
    Returns:
        修复后的图像字节数据
    """
    print("="*50)
    print("[文档修复] 开始修复文档图像")
    print("="*50)
    
    # 1. 读取图像
    image = _read_image_bytes_as_pil(data)
    print(f"[INFO] 原始尺寸：{image.width}x{image.height}")
    
    # 2. 预处理
    print("\n[STEP 1] 预处理...")
    processed = preprocess_image(image)
    print("预处理完成")
    
    # 3. OCR 识别
    print("\n[STEP 2] OCR 识别...")
    try:
        from .ocr_subprocess import get_ocr_service
        ocr_service = get_ocr_service()
        ocr_result = ocr_service.recognize(data)
        if ocr_result.get('success'):
            print(f"识别到 OCR 文字：{len(ocr_result.get('text', '').split(chr(10)))} 行")
        else:
            print(f"OCR 失败：{ocr_result.get('message')}")
    except Exception as e:
        print(f"OCR 异常：{e}")
    
    # 4. 保存结果
    print("\n[STEP 3] 保存结果...")
    output = io.BytesIO()
    processed.save(output, format="PNG")
    result_bytes = output.getvalue()
    print(f"输出尺寸：{processed.width}x{processed.height}")
    print("="*50)
    
    return result_bytes


def evaluate_image_quality(original: Image.Image, repaired: Image.Image) -> Dict[str, Any]:
    """评估图像质量"""
    # 导入 OpenCV
    import cv2
    import numpy as np
    
    original_cv = cv2.cvtColor(np.array(original), cv2.COLOR_RGB2BGR)
    repaired_cv = cv2.cvtColor(np.array(repaired), cv2.COLOR_RGB2BGR)
    
    # 计算清晰度（拉普拉斯方差）
    original_lap = cv2.Laplacian(cv2.cvtColor(original_cv, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
    repaired_lap = cv2.Laplacian(cv2.cvtColor(repaired_cv, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
    
    # 计算对比度
    original_contrast = np.std(cv2.cvtColor(original_cv, cv2.COLOR_BGR2GRAY))
    repaired_contrast = np.std(cv2.cvtColor(repaired_cv, cv2.COLOR_BGR2GRAY))
    
    return {
        "original_sharpness": round(original_lap, 2),
        "repaired_sharpness": round(repaired_lap, 2),
        "sharpness_improvement": round((repaired_lap - original_lap) / original_lap * 100, 2) if original_lap > 0 else 0,
        "original_contrast": round(original_contrast, 2),
        "repaired_contrast": round(repaired_contrast, 2),
        "contrast_improvement": round((repaired_contrast - original_contrast) / original_contrast * 100, 2) if original_contrast > 0 else 0,
    }


def repair_document(data: bytes, filename: str = "image.png", doc_type: str = "document", 
                   use_super_resolution: bool = True, sr_model_type: str = "classical", sr_scale: int = 4,
                   enable_text_optimization: bool = False, enable_ocr: bool = True, enable_spell_correction: bool = False, task_id: str = None) -> Dict[str, Any]:
    """
    修复文档图像 - 完整流程
    Args:
        data: 图像字节数据
        filename: 文件名
        doc_type: 文档类型
        use_super_resolution: 是否使用超分
        sr_model_type: 超分模型类型 (auto, compressed, classical, realworld)
        sr_scale: 超分倍数 (2, 4, 8, 16)
        enable_ocr: 是否进行 OCR 识别（图片修复应该设为 False）
        enable_spell_correction: 是否启用拼写纠错
        task_id: 任务 ID

    Returns:
        修复结果字典
    """
    timer = get_timer()
    timer.start_task(filename)

    print("="*50)
    print("[文档修复] 开始修复文档")
    print("="*50)

    # 1. 读取图像
    with timer.time_stage("读取图像"):
        image = _read_image_bytes_as_pil(data)
        print(f"[INFO] 原始尺寸：{image.width}x{image.height}")

    # 2. 预处理
    with timer.time_stage("预处理"):
        print("\n[STEP 1] 预处理...")
        processed = preprocess_image(image)
        print("预处理完成")

    # 3. 超分处理
    sr_image = processed
    model_name = "No Super Resolution"
    sr_meta = {}

    if use_super_resolution:
        with timer.time_stage("超分处理"):
            print("\n[STEP 2] 超分处理...")
            print(f"[DEBUG] use_super_resolution={use_super_resolution}, sr_model_type={sr_model_type}")
            try:
                # 更新任务进度
                if task_id:
                    from .async_task_queue import get_task_queue
                    task_queue = get_task_queue()
                    task_queue.update_progress(task_id, 30, "正在初始化超分模型...")
                    print(f"[DEBUG] 进度 30%")
                
                # 保存预处理后的图像到字节
                processed_bytes = io.BytesIO()
                processed.save(processed_bytes, format="PNG")
                processed_bytes_value = processed_bytes.getvalue()
                
                # 使用基础 Swin2SR 超分，使用预处理后的图像
                from .swin2sr_service import enhance_image
                print("[DEBUG] 执行超分处理...")
                sr_bytes, sr_meta = enhance_image(processed_bytes_value, sr_model_type=sr_model_type, target_scale=sr_scale, enable_text_optimization=enable_text_optimization)
                print(f"[DEBUG] 超分完成...")
                sr_image = Image.open(io.BytesIO(sr_bytes)).convert("RGB")
                model_name = f"Swin2SR ({sr_meta.get('method', 'unknown')})"
                print(f"超分结果：{sr_meta.get('original_size')} -> {sr_meta.get('enhanced_size')}")
                print(f"  耗时：{sr_meta.get('process_time', 0):.3f}s")
                if sr_meta.get('text_optimized'):
                    print(f"  ✓ 文字优化已启用")
                
                # 后处理
                print("\n[STEP 2.5] 后处理...")
                sr_image = postprocess_image(sr_image)
                
                if task_id:
                    task_queue.update_progress(task_id, 50, "正在执行超分...")
                    print(f"[DEBUG] 进度 50%")
            except Exception as e:
                print(f"超分失败：{e}")
                import traceback
                traceback.print_exc()
                sr_image = processed
                model_name = "Fallback (No SR)"
                if task_id:
                    from .async_task_queue import get_task_queue
                    task_queue = get_task_queue()
                    task_queue.update_progress(task_id, 70, "超分失败，使用原图...")

    # 4. OCR 识别（可选）
    ocr_text = ""
    ocr_raw_result = {}  # 包含 OCR 完整结果（包括 confidences 等）
    
    if enable_ocr:
        with timer.time_stage("OCR 识别"):
            print("\n[STEP 3] OCR 识别...")
            try:
                from .ocr_subprocess import get_ocr_service
                ocr_service = get_ocr_service()
                # 对超分后的图像进行 OCR
                processed_bytes = io.BytesIO()
                sr_image.save(processed_bytes, format="PNG")
                ocr_result = ocr_service.recognize(processed_bytes.getvalue(), enable_spell_correction=enable_spell_correction)
                if ocr_result.get('success'):
                    ocr_text = ocr_result.get('text', '')
                    ocr_raw_result = ocr_result  # 保存完整 OCR 结果
                    print(f"识别到 OCR 文字：{len(ocr_text.split(chr(10)))} 行")
                    
                    # 对比模块中无需进行文本补全
                else:
                    print(f"OCR 失败：{ocr_result.get('message')}")
            except Exception as e:
                print(f"OCR 异常：{e}")
    else:
        print("\n[STEP 3] 跳过 OCR 识别（图片修复模式）")

    # 5. 保存为 base64
    with timer.time_stage("保存结果"):
        print("\n[STEP 4] 保存结果...")
        buffer = io.BytesIO()
        sr_image.save(buffer, format="PNG")
        result_base64 = base64.b64encode(buffer.getvalue()).decode('ascii')
        print(f"输出尺寸：{sr_image.width}x{sr_image.height}")

    # 性能统计
    timer.end_task()
    performance_report = timer.get_breakdown()

    # 打印性能报告
    print("\n" + "="*50)
    print("性能统计")
    print("="*50)
    total_time = performance_report.get("total_processing_time", 0)
    print(f"总耗时：{format_duration(total_time)}")
    print("\n各阶段:")

    stats = performance_report.get("statistics", {})
    for stage_name, stage_stats in stats.items():
        if stage_stats:
            print(f"  {stage_name}: {format_duration(stage_stats['avg'])}")

    print("="*50)

    return {
        "repaired_image_base64": result_base64,
        "mild_image_base64": result_base64,
        "strong_image_base64": result_base64,
        "ocr_text": ocr_text,
        "ocr_raw_result": ocr_raw_result,  # 保存完整 OCR 结果
        "filled_text": "",
        "meta": {
            "input_size": f"{image.width}x{image.height}",
            "output_size": f"{sr_image.width}x{sr_image.height}",
            "model": model_name,
            "super_resolution": sr_meta,
            "performance": performance_report
        }
    }


def fill_missing_text(ocr_text: str, enable_spell_correction: bool = True) -> str:
    """
    补全 OCR 识别缺失的文字
    
    Args:
        ocr_text: OCR 识别的文本
        enable_spell_correction: 是否启用 MacBERT 拼写纠错
    
    Returns:
        补全后的文本
    """
    if not ocr_text or not enable_spell_correction:
        return ocr_text
    
    try:
        from app.services.text_completion import completion_service
        
        # 使用 MacBERT 进行语义补全和拼写纠错
        result = completion_service.semantic_completion(
            ocr_text,
            use_llm=False,  # 不使用 LLM
            enable_spell_correction=True  # 启用 MacBERT 纠错
        )
        
        completed_text = result.get('completed_text', ocr_text)
        steps = result.get('steps', [])
        
        if steps:
            print(f"[DocRepair] 语义补全完成：{repr(ocr_text)} → {repr(completed_text)}")
            print(f"[DocRepair] 使用的方法：{steps}")
        
        return completed_text
        
    except Exception as e:
        print(f"[DocRepair] 语义补全失败：{e}")
        return ocr_text
