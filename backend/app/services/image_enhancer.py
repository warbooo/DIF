"""
图片美化服务
提供亮度、对比度、饱和度、锐化等参数调节功能
"""
import io
from PIL import Image, ImageEnhance, ImageFilter
from typing import Dict, Tuple, Optional
import numpy as np


class ImageEnhancer:
    """图片增强器"""
    
    # 默认参数
    DEFAULT_PARAMS = {
        'brightness': 1.0,      # 亮度 (0.0-2.0)
        'contrast': 1.0,        # 对比度 (0.0-2.0)
        'saturation': 1.0,      # 饱和度 (0.0-2.0)
        'sharpness': 1.0,       # 锐化 (0.0-2.0)
        'warmth': 0,            # 色温 (-100 到 100)
        'exposure': 0,          # 曝光 (-100 到 100)
        'highlights': 0,        # 高光 (-100 到 100)
        'shadows': 0,           # 阴影 (-100 到 100)
    }
    
    def enhance(
        self,
        image_bytes: bytes,
        params: Optional[Dict] = None
    ) -> Tuple[bytes, Dict]:
        """
        增强图片
        
        Args:
            image_bytes: 图片字节流
            params: 增强参数字典
        
        Returns:
            (增强后的图片字节流，元数据)
        """
        # 使用默认参数或传入参数
        if params is None:
            params = self.DEFAULT_PARAMS.copy()
        else:
            # 合并参数，未提供的使用默认值
            for key, default_value in self.DEFAULT_PARAMS.items():
                if key not in params:
                    params[key] = default_value
        
        # 打开图片
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        original_size = image.size
        
        # 应用增强
        enhanced = self._apply_enhancements(image, params)
        
        # 保存结果
        output = io.BytesIO()
        enhanced.save(output, format="PNG")
        result_bytes = output.getvalue()
        
        # 元数据
        meta = {
            "original_size": f"{original_size[0]}x{original_size[1]}",
            "enhanced_size": f"{enhanced.size[0]}x{enhanced.size[1]}",
            "params": params,
            "method": "PIL Enhancement"
        }
        
        return result_bytes, meta
    
    def _apply_enhancements(self, image: Image.Image, params: Dict) -> Image.Image:
        """应用所有增强效果"""
        result = image
        
        # 1. 亮度
        if params.get('brightness', 1.0) != 1.0:
            enhancer = ImageEnhance.Brightness(result)
            result = enhancer.enhance(params['brightness'])
        
        # 2. 对比度
        if params.get('contrast', 1.0) != 1.0:
            enhancer = ImageEnhance.Contrast(result)
            result = enhancer.enhance(params['contrast'])
        
        # 3. 饱和度
        if params.get('saturation', 1.0) != 1.0:
            enhancer = ImageEnhance.Color(result)
            result = enhancer.enhance(params['saturation'])
        
        # 4. 锐化
        if params.get('sharpness', 1.0) != 1.0:
            enhancer = ImageEnhance.Sharpness(result)
            result = enhancer.enhance(params['sharpness'])
        
        # 5. 色温（暖色调/冷色调）
        warmth = params.get('warmth', 0)
        if warmth != 0:
            result = self._adjust_warmth(result, warmth)
        
        # 6. 曝光
        exposure = params.get('exposure', 0)
        if exposure != 0:
            result = self._adjust_exposure(result, exposure)
        
        # 7. 高光
        highlights = params.get('highlights', 0)
        if highlights != 0:
            result = self._adjust_highlights(result, highlights)
        
        # 8. 阴影
        shadows = params.get('shadows', 0)
        if shadows != 0:
            result = self._adjust_shadows(result, shadows)
        
        return result
    
    def _adjust_warmth(self, image: Image.Image, warmth: int) -> Image.Image:
        """调整色温"""
        img_array = np.array(image, dtype=np.float32) / 255.0
        
        # 暖色调：增加红色和黄色
        # 冷色调：增加蓝色
        if warmth > 0:
            # 暖色调
            img_array[:, :, 0] = np.clip(img_array[:, :, 0] * (1 + warmth / 200), 0, 1)  # R
            img_array[:, :, 1] = np.clip(img_array[:, :, 1] * (1 + warmth / 400), 0, 1)  # G
        else:
            # 冷色调
            img_array[:, :, 2] = np.clip(img_array[:, :, 2] * (1 - warmth / 200), 0, 1)  # B
        
        result_array = np.clip(img_array * 255, 0, 255).astype(np.uint8)
        return Image.fromarray(result_array)
    
    def _adjust_exposure(self, image: Image.Image, exposure: int) -> Image.Image:
        """调整曝光"""
        img_array = np.array(image, dtype=np.float32) / 255.0
        
        # 曝光调整
        adjustment = exposure / 100.0
        img_array = np.clip(img_array * (1 + adjustment), 0, 1)
        
        result_array = np.clip(img_array * 255, 0, 255).astype(np.uint8)
        return Image.fromarray(result_array)
    
    def _adjust_highlights(self, image: Image.Image, highlights: int) -> Image.Image:
        """调整高光"""
        img_array = np.array(image, dtype=np.float32) / 255.0
        
        # 只调整亮部区域
        mask = img_array.mean(axis=2) > 0.5
        adjustment = highlights / 100.0
        
        for i in range(3):  # RGB 三个通道
            channel = img_array[:, :, i]
            channel[mask] = np.clip(channel[mask] * (1 + adjustment), 0, 1)
        
        result_array = np.clip(img_array * 255, 0, 255).astype(np.uint8)
        return Image.fromarray(result_array)
    
    def _adjust_shadows(self, image: Image.Image, shadows: int) -> Image.Image:
        """调整阴影"""
        img_array = np.array(image, dtype=np.float32) / 255.0
        
        # 只调整暗部区域
        mask = img_array.mean(axis=2) < 0.5
        adjustment = shadows / 100.0
        
        for i in range(3):  # RGB 三个通道
            channel = img_array[:, :, i]
            channel[mask] = np.clip(channel[mask] * (1 + adjustment), 0, 1)
        
        result_array = np.clip(img_array * 255, 0, 255).astype(np.uint8)
        return Image.fromarray(result_array)
    
    def recommend_params(self, image_bytes: bytes) -> Dict:
        """
        智能推荐美化参数
        
        Args:
            image_bytes: 图片字节流
        
        Returns:
            推荐的参数配置
        """
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_array = np.array(image, dtype=np.float32) / 255.0
        
        # 分析图片特征
        brightness = np.mean(img_array)
        contrast = np.std(img_array)
        saturation = self._calculate_saturation(img_array)
        
        # 根据特征推荐参数
        recommended = self.DEFAULT_PARAMS.copy()
        
        # 1. 亮度推荐
        if brightness < 0.4:
            recommended['brightness'] = 1.1 + (0.4 - brightness) * 0.5
        elif brightness > 0.7:
            recommended['brightness'] = 0.95
        
        # 2. 对比度推荐
        if contrast < 0.15:
            recommended['contrast'] = 1.2
        elif contrast > 0.3:
            recommended['contrast'] = 1.05
        
        # 3. 饱和度推荐
        if saturation < 0.2:
            recommended['saturation'] = 1.3
        elif saturation > 0.5:
            recommended['saturation'] = 1.05
        
        # 4. 锐化推荐（默认轻微锐化）
        recommended['sharpness'] = 1.1
        
        # 限制参数范围
        for key in ['brightness', 'contrast', 'saturation', 'sharpness']:
            recommended[key] = max(0.5, min(1.5, recommended[key]))
        
        # 置信度
        confidence = 0.75
        
        return {
            'recommended_params': recommended,
            'confidence': confidence,
            'image_analysis': {
                'brightness': float(round(brightness, 3)),
                'contrast': float(round(contrast, 3)),
                'saturation': float(round(saturation, 3))
            },
            'recommendation_reason': self._generate_reason(recommended, brightness, contrast, saturation)
        }
    
    def _calculate_saturation(self, img_array: np.ndarray) -> float:
        """计算图片饱和度"""
        # 转换为 HSV 色彩空间
        r, g, b = img_array[:, :, 0], img_array[:, :, 1], img_array[:, :, 2]
        max_c = np.maximum(np.maximum(r, g), b)
        min_c = np.minimum(np.minimum(r, g), b)
        diff = max_c - min_c
        
        # 计算饱和度
        saturation = np.where(max_c != 0, diff / max_c, 0)
        return float(np.mean(saturation))
    
    def _generate_reason(
        self,
        params: Dict,
        brightness: float,
        contrast: float,
        saturation: float
    ) -> str:
        """生成推荐理由"""
        reasons = []
        
        if brightness < 0.4:
            reasons.append("图片偏暗，已适当提高亮度")
        elif brightness > 0.7:
            reasons.append("图片较亮，已轻微降低亮度")
        
        if contrast < 0.15:
            reasons.append("对比度较低，已增强对比")
        
        if saturation < 0.2:
            reasons.append("色彩较淡，已提升饱和度")
        
        if not reasons:
            reasons.append("图片质量良好，进行轻微优化")
        
        reasons.append("锐化增强细节")
        
        return "；".join(reasons)


# 全局实例
enhancer = ImageEnhancer()


def enhance_image(image_bytes: bytes, params: Optional[Dict] = None) -> Tuple[bytes, Dict]:
    """便捷函数：增强图片"""
    return enhancer.enhance(image_bytes, params)


def recommend_enhance_params(image_bytes: bytes) -> Dict:
    """便捷函数：推荐美化参数"""
    return enhancer.recommend_params(image_bytes)


def optimize_for_text(image_bytes: bytes) -> bytes:
    """
    针对文字图像进行优化处理（老照片文档增强版本）
    智能判断：根据对比度自动决定是否使用 CLAHE
    
    专门针对：泛黄老照片、褪色文档、红色/深色文字
    
    处理步骤：
    1. 色彩校正（去除泛黄）
    2. 智能对比度增强（根据图像对比度决定是否使用 CLAHE）
    3. 提升整体亮度
    4. 锐化边缘
    
    Args:
        image_bytes: 原始图片字节流
    
    Returns:
        优化后的图片字节流
    """
    # 打开图片
    img = Image.open(io.BytesIO(image_bytes))
    
    # 转换为 RGB（如果必要）
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # 转换为 numpy 数组
    img_array = np.array(img).astype(np.float32) / 255.0
    
    # 计算图像对比度（使用标准差）
    gray = np.mean(img_array, axis=2)  # 转为灰度
    contrast = np.std(gray)  # 标准差作为对比度指标
    
    # 智能判断是否需要 CLAHE 增强
    # 对比度阈值：0.15（低于此值认为是低对比度图像）
    USE_CLAHE = contrast < 0.15
    
    print(f"[Text Optimization] 图像对比度：{contrast:.4f}，{'使用' if USE_CLAHE else '跳过'} CLAHE 增强")
    
    from skimage import color, exposure, restoration
    
    try:
        # 1. 转换到 LAB 色彩空间
        lab = color.rgb2lab(img_array)
        
        # 2. 色彩校正 - 去除泛黄（调整 b 通道）
        # 泛黄图片的 b 通道（黄 - 蓝）偏高，需要降低
        lab[:, :, 2] = lab[:, :, 2] * 0.85  # 轻微减少黄色
        
        # 3. 智能对比度增强 - 根据对比度决定是否使用 CLAHE
        if USE_CLAHE:
            # 低对比度图像：使用 CLAHE 增强
            # clip_limit 根据对比度动态调整（对比度越低，增强越强）
            clip_limit = 0.03 * (0.15 / max(contrast, 0.05))  # 降低基础强度
            clip_limit = min(clip_limit, 0.05)  # 限制最大增强强度（从 0.08 降到 0.05）
            print(f"[Text Optimization] CLAHE clip_limit: {clip_limit:.4f}")
            
            L_channel = exposure.equalize_adapthist(lab[:, :, 0], clip_limit=clip_limit, nbins=256)
            lab[:, :, 0] = L_channel
        
        # 4. 转回 RGB
        img_array = color.lab2rgb(lab)
        
        # 5. 提升整体亮度（Gamma 校正）
        # gamma < 1 提升亮度
        gamma = 0.8  # 更温和的提亮，避免过度提亮影响 OCR 识别
        img_array = np.power(img_array, 1/gamma)
        
    except Exception as e:
        print(f"[WARN] LAB 色彩空间处理失败：{e}，使用基础处理")
        # 回退到基础 gamma 校正
        gamma = 0.8  # 更温和的提亮
        img_array = np.power(img_array, 1/gamma)
    
    # 5. 锐化增强文字边缘（使用更温和的滤波器）
    from scipy import ndimage
    # 降低锐化强度，避免引入过多高频噪点
    sharpen_filter = np.array([
        [0, -0.3, 0],
        [-0.3, 2.2, -0.3],
        [0, -0.3, 0]
    ])
    
    # 对每个通道应用锐化
    for i in range(3):
        img_array[:, :, i] = ndimage.convolve(img_array[:, :, i], sharpen_filter, mode='reflect')
    
    # 限制数值范围
    img_array = np.clip(img_array, 0, 1)
    
    # 6. 轻微去噪（保持边缘）
    # 降低去噪强度，避免模糊文字边缘
    for i in range(3):
        img_array[:, :, i] = ndimage.gaussian_filter(img_array[:, :, i], sigma=0.15)
    
    # 限制数值范围
    img_array = np.clip(img_array, 0, 1)
    
    # 转回 0-255 范围
    img_array = (img_array * 255).astype(np.uint8)
    
    # 转回图片
    result_img = Image.fromarray(img_array, mode='RGB')
    
    # 保存为字节流
    output = io.BytesIO()
    result_img.save(output, format='PNG', quality=95)
    output.seek(0)
    
    return output.getvalue()
