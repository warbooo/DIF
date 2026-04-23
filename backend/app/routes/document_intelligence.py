"""
文档智能分析路由
整合文档分类、表格提取、多语言识别等创新功能
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import io
import time
from PIL import Image

router = APIRouter(prefix="/api/intelligence", tags=["document_intelligence"])


class DocumentAnalysisResponse(BaseModel):
    """文档分析响应"""
    success: bool
    message: str
    processing_time: float
    document_type: Optional[str] = None
    type_confidence: Optional[float] = None
    features: Optional[Dict] = None
    recommendations: Optional[List[str]] = None
    optimal_params: Optional[Dict] = None


class TableExtractionResponse(BaseModel):
    """表格提取响应"""
    success: bool
    message: str
    processing_time: float
    table_count: int
    tables: Optional[List[Dict]] = None
    markdown_output: Optional[str] = None
    html_output: Optional[str] = None


class DocumentQualityResponse(BaseModel):
    """文档质量评估响应"""
    success: bool
    message: str
    overall_score: float
    dimensions: Optional[Dict[str, float]] = None
    issues: Optional[List[str]] = None
    suggestions: Optional[List[str]] = None


@router.post("/classify", response_model=DocumentAnalysisResponse)
async def classify_document(
    file: UploadFile = File(...),
    ocr_text: str = Form("")
):
    """
    智能文档分类
    自动识别文档类型并提供最优处理参数
    """
    start_time = time.time()
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    
    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # 读取图像
        image = Image.open(io.BytesIO(contents)).convert('RGB')
        
        # 文档分类
        from ..services.document_classifier import classify_document
        doc_type, info = classify_document(image, ocr_text)
        
        processing_time = time.time() - start_time
        
        return DocumentAnalysisResponse(
            success=True,
            message=f"文档分类完成，识别为: {doc_type.value}",
            processing_time=processing_time,
            document_type=info["type"],
            type_confidence=info["confidence"],
            features=info["features"],
            recommendations=info["recommendations"],
            optimal_params=info["optimal_params"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@router.post("/extract-tables", response_model=TableExtractionResponse)
async def extract_tables(
    file: UploadFile = File(...),
    export_format: str = Form("json")  # json, excel, csv, markdown, html
):
    """
    智能表格提取
    从文档中提取表格结构并导出为多种格式
    """
    start_time = time.time()
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    
    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # 读取图像
        image = Image.open(io.BytesIO(contents)).convert('RGB')
        
        # 先进行OCR识别
        from ..services.ocr_subprocess import get_ocr_service
        ocr_service = get_ocr_service()
        ocr_result = ocr_service.recognize(contents)
        
        # 提取表格
        from ..services.table_extractor import extract_tables, TableExporter
        tables = extract_tables(image, ocr_result)
        
        # 生成输出
        markdown_output = None
        html_output = None
        
        if tables:
            # 生成Markdown
            markdown_lines = []
            for i, table in enumerate(tables):
                markdown_lines.append(f"### Table {i+1}\n")
                markdown_lines.append(table.to_markdown())
                markdown_lines.append("")
            markdown_output = "\n".join(markdown_lines)
            
            # 生成HTML
            html_parts = ["<div class='tables-container'>"]
            for i, table in enumerate(tables):
                html_parts.append(f"<h3>Table {i+1}</h3>")
                html_parts.append(table.to_html())
            html_parts.append("</div>")
            html_output = "\n".join(html_parts)
        
        processing_time = time.time() - start_time
        
        return TableExtractionResponse(
            success=True,
            message=f"提取到 {len(tables)} 个表格",
            processing_time=processing_time,
            table_count=len(tables),
            tables=[table.to_dict() for table in tables],
            markdown_output=markdown_output,
            html_output=html_output
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Table extraction failed: {str(e)}")


@router.post("/quality-assessment", response_model=DocumentQualityResponse)
async def assess_quality(
    file: UploadFile = File(...)
):
    """
    文档质量评估
    多维度评估文档质量并提供修复建议
    """
    start_time = time.time()
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    
    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # 读取图像
        image = Image.open(io.BytesIO(contents)).convert('RGB')
        
        # 质量评估
        from ..services.doc_repair import evaluate_image_quality
        quality_metrics = evaluate_image_quality(image, image)  # 对比原图
        
        # 计算综合得分
        dimensions = {
            "sharpness": min(quality_metrics.get("original_sharpness", 0) / 100, 1.0),
            "contrast": min(quality_metrics.get("original_contrast", 0) / 50, 1.0),
            "resolution": min(image.width * image.height / 1000000, 1.0),  # 以1MP为满分
        }
        
        overall_score = sum(dimensions.values()) / len(dimensions)
        
        # 生成问题和建议
        issues = []
        suggestions = []
        
        if dimensions["sharpness"] < 0.5:
            issues.append("图像清晰度较低")
            suggestions.append("建议使用超分辨率增强")
        
        if dimensions["contrast"] < 0.5:
            issues.append("图像对比度不足")
            suggestions.append("建议增强对比度")
        
        if dimensions["resolution"] < 0.3:
            issues.append("图像分辨率较低")
            suggestions.append("建议使用更高的扫描分辨率")
        
        processing_time = time.time() - start_time
        
        return DocumentQualityResponse(
            success=True,
            message="质量评估完成",
            overall_score=round(overall_score * 100, 2),
            dimensions={k: round(v * 100, 2) for k, v in dimensions.items()},
            issues=issues,
            suggestions=suggestions
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quality assessment failed: {str(e)}")


@router.post("/full-analysis")
async def full_document_analysis(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    完整文档智能分析
    整合分类、OCR、表格提取、质量评估等所有功能
    """
    start_time = time.time()
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    
    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # 读取图像
        image = Image.open(io.BytesIO(contents)).convert('RGB')
        
        # 1. 文档分类
        from ..services.document_classifier import classify_document
        doc_type, type_info = classify_document(image, "")
        
        # 2. OCR识别
        from ..services.ocr_subprocess import get_ocr_service
        ocr_service = get_ocr_service()
        ocr_result = ocr_service.recognize(contents)
        
        # 3. 重新分类（使用OCR文本）
        doc_type, type_info = classify_document(image, ocr_result.get("text", ""))
        
        # 4. 表格提取
        from ..services.table_extractor import extract_tables
        tables = extract_tables(image, ocr_result)
        
        # 5. 质量评估
        from ..services.doc_repair import evaluate_image_quality
        quality_metrics = evaluate_image_quality(image, image)
        
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "message": "完整分析完成",
            "processing_time": processing_time,
            "document_classification": {
                "type": type_info["type"],
                "confidence": type_info["confidence"],
                "recommendations": type_info["recommendations"]
            },
            "ocr_result": {
                "text": ocr_result.get("text", ""),
                "processed_text": ocr_result.get("processed_text", ""),
                "confidence": ocr_result.get("avg_confidence", 0),
                "post_processing_applied": ocr_result.get("post_processing_applied", [])
            },
            "tables": {
                "count": len(tables),
                "data": [table.to_dict() for table in tables]
            },
            "quality": {
                "sharpness": round(quality_metrics.get("original_sharpness", 0), 2),
                "contrast": round(quality_metrics.get("original_contrast", 0), 2)
            },
            "optimal_processing_params": type_info["optimal_params"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Full analysis failed: {str(e)}")


@router.get("/document-types")
async def get_document_types():
    """获取支持的文档类型列表"""
    from ..services.document_classifier import DocumentType
    
    types = []
    for doc_type in DocumentType:
        descriptions = {
            DocumentType.PRINTED: "印刷体文档，如打印的论文、报告",
            DocumentType.HANDWRITTEN: "手写文档，如手写笔记、信件",
            DocumentType.TABLE: "包含表格的文档，如财务报表",
            DocumentType.INVOICE: "发票、收据等票据类文档",
            DocumentType.ID_CARD: "身份证、名片等证件类文档",
            DocumentType.CONTRACT: "合同、协议等法律文档",
            DocumentType.BOOK: "书籍、教材等出版物",
            DocumentType.NEWSPAPER: "报纸、杂志等新闻类文档",
            DocumentType.UNKNOWN: "未知类型文档"
        }
        types.append({
            "type": doc_type.value,
            "description": descriptions.get(doc_type, "未知类型")
        })
    
    return {"document_types": types}
