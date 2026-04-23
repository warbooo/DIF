"""
超分智能推荐 API 路由
"""
import io
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from typing import Optional
from PIL import Image

from ..deps import get_optional_user
from ..db.models import User
from ..services.sr_recommender import recommend_sr_config

router = APIRouter(prefix="/api/sr/recommend", tags=["super-resolution"])


@router.post("/")
async def recommend_super_resolution(
    file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    智能推荐超分配置
    
    根据上传的图片自动分析并推荐：
    - 最优模型权重（ClassicalSR/CompressedSR/RealWorldSR）
    - 最优超分倍数（X2/X4/X8/X16）
    - 级联配置
    - 备选方案
    
    Args:
        file: 上传的图片文件
        current_user: 当前用户（可选）
    
    Returns:
        推荐结果
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")
    
    # 验证图片格式
    try:
        image = Image.open(io.BytesIO(contents))
        image.verify()
        image = Image.open(io.BytesIO(contents))
        if image.mode != 'RGB':
            image = image.convert('RGB')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")
    
    try:
        # 调用推荐服务
        print(f"\n[推荐 API] 开始分析图片，大小：{len(contents)} bytes")
        recommendation = recommend_sr_config(contents)
        
        print(f"[推荐 API] 推荐结果:")
        print(f"  - 模型：{recommendation.get('recommended_model_name', 'N/A')}")
        print(f"  - 倍数：{recommendation.get('recommended_scale', 'N/A')}")
        print(f"  - 置信度：{recommendation.get('confidence', 'N/A')}")
        
        return {
            "success": True,
            "recommendation": recommendation
        }
        
    except Exception as e:
        import traceback
        print(f"[推荐 API] 推荐失败：{e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")


@router.get("/scales")
async def get_supported_scales():
    """获取支持的超分倍数"""
    return {
        "scales": [2, 4, 8, 16],
        "cascade_config": {
            "2": {"scales": [2], "description": "单阶段：X2"},
            "4": {"scales": [4], "description": "单阶段：X4"},
            "8": {"scales": [2, 4], "description": "双阶段：X2 → X4"},
            "16": {"scales": [4, 4], "description": "三阶段：X4 → X4"}
        }
    }


@router.get("/models")
async def get_available_models():
    """获取可用的模型列表"""
    return {
        "models": {
            "classical": {
                "name": "ClassicalSR",
                "description": "经典超分模型",
                "best_for": "文字文档、扫描件、书籍照片",
                "tags": ["文字清晰化", "扫描文档", "书籍照片"],
                "scales": [2, 4]
            },
            "compressed": {
                "name": "CompressedSR",
                "description": "压缩图像恢复模型",
                "best_for": "网络压缩图、JPEG 图片",
                "tags": ["去除压缩噪点", "JPEG 压缩图", "网络下载图"],
                "scales": [4]
            },
            "realworld": {
                "name": "RealWorldSR",
                "description": "真实世界超分模型",
                "best_for": "真实照片、复杂退化",
                "tags": ["人像", "风景", "AI 图"],
                "scales": [4]
            }
        }
    }
