"""
PDF处理路由
提供PDF转图像、多页处理、信息读取等功能
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import io
from PIL import Image

router = APIRouter(prefix="/api/pdf", tags=["pdf"])


class PDFInfoResponse(BaseModel):
    """PDF信息响应"""
    success: bool
    message: str
    page_count: int
    has_text: bool
    metadata: Optional[Dict[str, str]] = None


class PDFToImageResponse(BaseModel):
    """PDF转图像响应"""
    success: bool
    message: str
    page_count: int
    current_page: int
    image_base64: Optional[str] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    dpi: int


@router.post("/info", response_model=PDFInfoResponse)
async def get_pdf_info(
    file: UploadFile = File(...)
):
    """
    获取PDF文件信息
    
    包括页数、是否包含文本、元数据等
    """
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Please upload a PDF file")
    
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")
    
    try:
        from ..services.pdf_processor import get_pdf_processor
        processor = get_pdf_processor()
        
        info = processor.get_pdf_info(contents)
        
        return PDFInfoResponse(
            success=True,
            message="PDF信息获取成功",
            page_count=info.get('page_count', 0),
            has_text=info.get('has_text', False),
            metadata=info.get('metadata', {})
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get PDF info: {str(e)}")


@router.post("/to-image", response_model=PDFToImageResponse)
async def pdf_to_image(
    file: UploadFile = File(...),
    page: int = Form(1),
    dpi: int = Form(300)
):
    """
    将PDF转换为图像
    
    Args:
        file: PDF文件
        page: 页码（从1开始）
        dpi: 分辨率（DPI）
    
    Returns:
        图像的base64编码
    """
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Please upload a PDF file")
    
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")
    
    try:
        from ..services.pdf_processor import get_pdf_processor
        processor = get_pdf_processor()
        
        # 获取PDF信息
        info = processor.get_pdf_info(contents)
        total_pages = info.get('page_count', 1)
        
        # 验证页码
        if page < 1 or page > total_pages:
            raise HTTPException(status_code=400, detail=f"Page {page} is out of range. PDF has {total_pages} pages.")
        
        # 转换为图像
        image = processor.pdf_to_single_image(contents, dpi=dpi, page=page)
        
        if image is None:
            raise HTTPException(status_code=500, detail="Failed to convert PDF to image")
        
        # 转换为base64
        image_base64 = processor.image_to_base64(image)
        
        return PDFToImageResponse(
            success=True,
            message=f"PDF converted to image successfully (Page {page} of {total_pages})",
            page_count=total_pages,
            current_page=page,
            image_base64=image_base64,
            image_width=image.width,
            image_height=image.height,
            dpi=dpi
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to convert PDF: {str(e)}")


@router.post("/to-all-images")
async def pdf_to_all_images(
    file: UploadFile = File(...),
    dpi: int = Form(200)
):
    """
    将PDF的所有页转换为图像
    
    Args:
        file: PDF文件
        dpi: 分辨率（DPI）
    
    Returns:
        所有页的图像base64编码列表
    """
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Please upload a PDF file")
    
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")
    
    try:
        from ..services.pdf_processor import get_pdf_processor
        processor = get_pdf_processor()
        
        # 获取PDF信息
        info = processor.get_pdf_info(contents)
        total_pages = info.get('page_count', 1)
        
        # 转换所有页
        images = processor.pdf_to_images(contents, dpi=dpi)
        
        # 转换为base64列表
        images_base64 = [processor.image_to_base64(img) for img in images]
        
        return {
            "success": True,
            "message": f"All {total_pages} pages converted successfully",
            "page_count": total_pages,
            "dpi": dpi,
            "images": images_base64,
            "image_sizes": [{"width": img.width, "height": img.height} for img in images]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to convert PDF: {str(e)}")


@router.post("/process-page")
async def process_pdf_page(
    file: UploadFile = File(...),
    page: int = Form(1),
    dpi: int = Form(300),
    use_super_resolution: bool = Form(True)
):
    """
    处理PDF的指定页面
    
    将PDF转换为图像，然后进行文档修复和OCR识别
    
    Args:
        file: PDF文件
        page: 页码
        dpi: 转换分辨率
        use_super_resolution: 是否使用超分辨率
    
    Returns:
        处理结果（图像+OCR文本）
    """
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Please upload a PDF file")
    
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")
    
    try:
        from ..services.pdf_processor import get_pdf_processor
        from ..services.doc_repair import repair_document
        processor = get_pdf_processor()
        
        # 获取PDF信息
        info = processor.get_pdf_info(contents)
        total_pages = info.get('page_count', 1)
        
        # 验证页码
        if page < 1 or page > total_pages:
            raise HTTPException(status_code=400, detail=f"Page {page} is out of range. PDF has {total_pages} pages.")
        
        # 转换为图像
        image = processor.pdf_to_single_image(contents, dpi=dpi, page=page)
        
        if image is None:
            raise HTTPException(status_code=500, detail="Failed to convert PDF to image")
        
        # 转换为字节
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        
        # 文档修复
        result = repair_document(
            image_bytes,
            filename=f"{file.filename}_page{page}.png",
            doc_type="document",
            use_super_resolution=use_super_resolution
        )
        
        return {
            "success": True,
            "message": f"PDF page {page} processed successfully",
            "page_count": total_pages,
            "current_page": page,
            "dpi": dpi,
            "original_image_size": {"width": image.width, "height": image.height},
            "repaired_image_base64": result.get("repaired_image_base64"),
            "mild_image_base64": result.get("mild_image_base64", result.get("repaired_image_base64")),
            "strong_image_base64": result.get("strong_image_base64", result.get("repaired_image_base64")),
            "ocr_text": result.get("ocr_text", ""),
            "filled_text": result.get("filled_text", ""),
            "meta": result.get("meta", {})
        }
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")
