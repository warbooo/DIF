"""
图片美化 API 路由
"""
import io
import base64
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from typing import Optional, Dict
from PIL import Image

from ..deps import get_optional_user
from ..db.models import User
from ..services.image_enhancer import enhance_image, recommend_enhance_params

router = APIRouter(prefix="/api/image/enhance", tags=["image-enhancement"])


@router.post("/")
async def enhance_image_endpoint(
    file: UploadFile = File(...),
    brightness: float = Form(1.0),
    contrast: float = Form(1.0),
    saturation: float = Form(1.0),
    sharpness: float = Form(1.0),
    warmth: int = Form(0),
    exposure: int = Form(0),
    highlights: int = Form(0),
    shadows: int = Form(0),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    美化图片
    
    支持多种参数调节：
    - brightness: 亮度 (0.0-2.0, 默认 1.0)
    - contrast: 对比度 (0.0-2.0, 默认 1.0)
    - saturation: 饱和度 (0.0-2.0, 默认 1.0)
    - sharpness: 锐化 (0.0-2.0, 默认 1.0)
    - warmth: 色温 (-100 到 100, 默认 0)
    - exposure: 曝光 (-100 到 100, 默认 0)
    - highlights: 高光 (-100 到 100, 默认 0)
    - shadows: 阴影 (-100 到 100, 默认 0)
    
    Args:
        file: 上传的图片文件
        brightness: 亮度
        contrast: 对比度
        saturation: 饱和度
        sharpness: 锐化
        warmth: 色温
        exposure: 曝光
        highlights: 高光
        shadows: 阴影
        current_user: 当前用户（可选）
    
    Returns:
        美化后的图片和元数据
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
        # 收集参数
        params = {
            'brightness': brightness,
            'contrast': contrast,
            'saturation': saturation,
            'sharpness': sharpness,
            'warmth': warmth,
            'exposure': exposure,
            'highlights': highlights,
            'shadows': shadows
        }
        
        # 执行美化
        result_bytes, meta = enhance_image(contents, params)
        
        # 转换为 base64
        result_base64 = base64.b64encode(result_bytes).decode('ascii')
        
        return {
            "success": True,
            "image_base64": result_base64,
            "meta": meta
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Enhancement failed: {str(e)}")


@router.post("/recommend")
async def recommend_params_endpoint(
    file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    智能推荐美化参数
    
    根据图片特征自动推荐最优的美化参数
    
    Args:
        file: 上传的图片文件
        current_user: 当前用户（可选）
    
    Returns:
        推荐的参数配置
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
        # 获取推荐参数
        recommendation = recommend_enhance_params(contents)
        
        return {
            "success": True,
            "recommendation": recommendation
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")


@router.get("/presets")
async def get_presets():
    """获取预设的美化方案"""
    return {
        "presets": [
            {
                "id": "default",
                "name": "默认",
                "description": "无调整",
                "params": {
                    'brightness': 1.0,
                    'contrast': 1.0,
                    'saturation': 1.0,
                    'sharpness': 1.0,
                    'warmth': 0,
                    'exposure': 0,
                    'highlights': 0,
                    'shadows': 0
                }
            },
            {
                "id": "bright",
                "name": "明亮",
                "description": "提高亮度，适合暗图",
                "params": {
                    'brightness': 1.2,
                    'contrast': 1.1,
                    'saturation': 1.1,
                    'sharpness': 1.0,
                    'warmth': 10,
                    'exposure': 10,
                    'highlights': -10,
                    'shadows': 20
                }
            },
            {
                "id": "vivid",
                "name": "鲜艳",
                "description": "增强色彩，适合风景",
                "params": {
                    'brightness': 1.05,
                    'contrast': 1.15,
                    'saturation': 1.4,
                    'sharpness': 1.1,
                    'warmth': 5,
                    'exposure': 0,
                    'highlights': -5,
                    'shadows': 10
                }
            },
            {
                "id": "cool",
                "name": "冷色调",
                "description": "冷色风格",
                "params": {
                    'brightness': 1.0,
                    'contrast': 1.2,
                    'saturation': 1.1,
                    'sharpness': 1.1,
                    'warmth': -30,
                    'exposure': 0,
                    'highlights': -10,
                    'shadows': 0
                }
            },
            {
                "id": "warm",
                "name": "暖色调",
                "description": "暖色风格",
                "params": {
                    'brightness': 1.0,
                    'contrast': 1.1,
                    'saturation': 1.2,
                    'sharpness': 1.0,
                    'warmth': 30,
                    'exposure': 5,
                    'highlights': -5,
                    'shadows': 10
                }
            },
            {
                "id": "dramatic",
                "name": "戏剧化",
                "description": "高对比度，强烈风格",
                "params": {
                    'brightness': 0.95,
                    'contrast': 1.4,
                    'saturation': 1.3,
                    'sharpness': 1.2,
                    'warmth': 0,
                    'exposure': -5,
                    'highlights': -20,
                    'shadows': 15
                }
            }
        ]
    }
