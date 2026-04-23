"""
文本补全接口 - 基于上下文的语义补全
针对普通 PDF 文档的缺字补全
"""
import time
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.orm import Session

from ..services.text_completion import completion_service, quick_complete, detect_missing
from ..db.session import get_db
from ..db.models import CompletionLog, ModelUsageStat, User
from ..deps import get_current_user

router = APIRouter(prefix="/api/text", tags=["text-completion"])


class CompletionRequest(BaseModel):
    """文本补全请求"""
    text: str = Field(..., description="需要补全的文本")
    use_llm: bool = Field(False, description="是否使用大语言模型（默认使用规则）")
    enable_spell_correction: bool = Field(False, description="是否先进行拼写纠错（MacBERT）")


class CompletionResponse(BaseModel):
    """文本补全响应"""
    success: bool
    message: str
    original_text: str
    corrected_text: Optional[str] = Field(None, description="拼写纠错后的文本（如果启用了纠错）")
    completed_text: str
    missing_count: int
    completion_positions: List[dict]
    method: str
    steps: List[str] = Field(default_factory=list, description="执行步骤")


class BatchCompletionRequest(BaseModel):
    """批量文本补全请求"""
    texts: List[str]
    use_llm: bool = False


class BatchCompletionResponse(BaseModel):
    """批量文本补全响应"""
    success: bool
    message: str
    results: List[dict]


@router.post("/complete", response_model=CompletionResponse)
async def complete_text(
    request: CompletionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> CompletionResponse:
    """
    单条文本补全
    
    检测文本中的缺失字符，并进行语义补全
    
    - **text**: 需要补全的文本，缺失处可用 □、_、? 等标记
    - **use_llm**: 是否使用大语言模型（需要配置 API Key）
    - **enable_spell_correction**: 是否先进行拼写纠错（MacBERT）
    """
    import time
    start_time = time.time()
    try:
        result = completion_service.semantic_completion(
            request.text, 
            use_llm=request.use_llm,
            enable_spell_correction=request.enable_spell_correction
        )
        
        processing_time = time.time() - start_time
        
        # 保存 CompletionLog
        completion_type = "llm" if request.use_llm else "nlp_based"
        db_completion = CompletionLog(
            user_id=current_user.id,
            completion_type=completion_type,
            is_llm_enabled=request.use_llm,
            original_text=request.text,
            completed_text=result['completed_text'],
            success=True,
            processing_time=processing_time,
            tokens_used=0,
            model_name=""
        )
        
        # 如果使用了 LLM，记录 LLM 信息
        if request.use_llm and result.get('method') == 'llm':
            db_completion.llm_provider = "Qwen"
            db_completion.model_name = completion_service.model
            db_completion.tokens_used = len(request.text) + len(result['completed_text'])
        
        db.add(db_completion)
        
        # 保存 ModelUsageStat
        model_stat = ModelUsageStat(
            model_type="llm" if request.use_llm else "nlp",
            model_name=completion_service.model if request.use_llm else "nlp_completion",
            usage_count=1,
            success_count=1,
            total_processing_time=processing_time
        )
        db.add(model_stat)
        
        # 如果启用了拼写纠错，单独统计 MacBERT 模型使用
        if request.enable_spell_correction and 'spell_correction' in result.get('steps', []):
            macbert_stat = ModelUsageStat(
                model_type="nlp",
                model_name="macbert_corrector",
                usage_count=1,
                success_count=1,
                total_processing_time=processing_time * 0.3  # 估计纠错耗时占30%
            )
            db.add(macbert_stat)
        
        db.commit()
        
        # 构建消息
        steps_desc = []
        if 'spell_correction' in result.get('steps', []):
            steps_desc.append('拼写纠错')
        if 'llm_completion' in result.get('steps', []):
            steps_desc.append('LLM 补全')
        elif 'rule_completion' in result.get('steps', []):
            steps_desc.append('NLP 补全')
        
        message = f"补全完成，共补全 {result['missing_count']} 处缺失"
        if steps_desc:
            message += f"（步骤：{' → '.join(steps_desc)}）"
        
        return CompletionResponse(
            success=True,
            message=message,
            original_text=result['original_text'],
            corrected_text=result.get('corrected_text'),
            completed_text=result['completed_text'],
            missing_count=result['missing_count'],
            completion_positions=result['completion_positions'],
            method=result['method'],
            steps=result.get('steps', [])
        )
    except Exception as e:
        return CompletionResponse(
            success=False,
            message=f"补全失败: {str(e)}",
            original_text=request.text,
            corrected_text=None,
            completed_text=request.text,
            missing_count=0,
            completion_positions=[],
            method="error",
            steps=[]
        )


@router.post("/complete/batch", response_model=BatchCompletionResponse)
async def complete_text_batch(request: BatchCompletionRequest) -> BatchCompletionResponse:
    """
    批量文本补全
    
    对多条文本进行批量补全
    """
    try:
        results = completion_service.batch_completion(
            request.texts,
            use_llm=request.use_llm
        )
        
        total_missing = sum(r['missing_count'] for r in results)
        
        return BatchCompletionResponse(
            success=True,
            message=f"批量补全完成，共处理 {len(results)} 条文本，补全 {total_missing} 处缺失",
            results=results
        )
    except Exception as e:
        return BatchCompletionResponse(
            success=False,
            message=f"批量补全失败: {str(e)}",
            results=[]
        )


@router.post("/detect-missing")
async def detect_missing_chars(request: CompletionRequest):
    """
    检测文本中的缺失字符位置
    
    返回所有缺失字符的位置和上下文信息
    """
    try:
        positions = detect_missing(request.text)
        
        return {
            "success": True,
            "message": f"检测到 {len(positions)} 处缺失",
            "missing_count": len(positions),
            "positions": positions
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"检测失败: {str(e)}",
            "missing_count": 0,
            "positions": []
        }


@router.get("/completion-info")
async def get_completion_info():
    """获取文本补全功能说明和配置状态"""
    from ..services.text_completion import completion_service
    
    return {
        "功能说明": "基于上下文的语义补全，针对PDF扫描文档OCR识别中的缺字问题",
        "大模型状态": "已配置" if completion_service.enable_llm else "未配置",
        "支持方法": {
            "rule_based": "基于规则的快速补全，适用于常见固定搭配",
            "llm_based": "基于大语言模型的语义补全（需要配置 LLM_API_KEY）",
            "rule_fallback": "大模型调用失败时自动回退到规则补全"
        },
        "支持的缺失标记": completion_service.missing_marks,
        "使用场景": [
            "PDF扫描文档OCR识别后的缺字补全",
            "文档数字化过程中的文字修复",
            "批量文档的自动补全处理"
        ],
        "配置说明": {
            "LLM_API_KEY": "大模型 API 密钥",
            "LLM_API_BASE": "API 基础地址（默认：https://api.openai.com/v1）",
            "LLM_MODEL": "模型名称（默认：gpt-3.5-turbo）"
        },
        "示例": {
            "输入": "这是一_测试文档，请_系相关人员_生。",
            "输出": "这是一个测试文档，请联系相关人员学生。"
        }
    }
