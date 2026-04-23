"""
图片分析工具
分析图片特征，为智能推荐提供依据
"""
import io
from PIL import Image
import numpy as np
from typing import Dict, Tuple
from enum import Enum


class ImageType(Enum):
    """图片类型"""
    DOCUMENT = "document"  # 文档/文字
    COMPRESSED = "compressed"  # 压缩图像
    PHOTO = "photo"  # 真实照片
    UNKNOWN = "unknown"  # 未知


class ImageQuality(Enum):
    """图片质量"""
    EXCELLENT = "excellent"  # 优秀
    GOOD = "good"  # 良好
    FAIR = "fair"  # 一般
    POOR = "poor"  # 较差


def analyze_image(image_bytes: bytes) -> Dict:
    """
    分析图片特征
    
    Args:
        image_bytes: 图片字节流
    
    Returns:
        分析结果字典
    """
    # 打开图片
    image = Image.open(io.BytesIO(image_bytes))
    
    # 获取基本信息
    width, height = image.size
    mode = image.mode
    
    # 转换为 RGB 进行分析
    if mode != 'RGB':
        image_rgb = image.convert('RGB')
    else:
        image_rgb = image
    
    # 转换为 numpy 数组
    img_array = np.array(image_rgb)
    
    # 分析特征
    image_type = detect_image_type(img_array, width, height, len(image_bytes))
    quality = estimate_quality(img_array)
    recommended_scale = recommend_scale(width, height)
    
    analysis = {
        'width': width,
        'height': height,
        'resolution': f"{width}x{height}",
        'megapixels': round((width * height) / 1_000_000, 2),
        'aspect_ratio': round(width / height, 2),
        'image_type': image_type,
        'quality': quality,
        'is_low_resolution': is_low_resolution(width, height),
        'recommended_scale': recommended_scale,
        'recommended_model': recommend_model(img_array, image_type, width, height, len(image_bytes)),
        'confidence': calculate_confidence(img_array, image_type, quality, recommended_scale)
    }
    
    return analysis


def detect_image_type(img_array: np.ndarray, width: int = 0, height: int = 0, file_size: int = 0) -> str:
    """
    检测图片类型
    
    基于三个模型的定位设计判断逻辑：
    - ClassicalSR: 理想图片 - 高质量扫描件（本身质量很高，需要强力锐化）
    - CompressedSR: 网络压缩图 - 有损压缩图片（JPEG 压缩、网络传图、小尺寸图）
    - RealWorldSR: 绝大部分情况通用 - 复杂退化（真实照片、模糊文本、老照片、监控截图）
    
    判断依据：
    1. 颜色熵：衡量颜色丰富程度（文档低，照片高）
    2. 边缘强度：衡量线条清晰度（文档/动漫高，照片中等）
    3. 高频成分：衡量压缩噪点（压缩图高）
    4. 尺寸和文件大小：辅助判断（小图多为压缩图）
    
    优化：大图会先缩小到 512x512 再分析，提升速度
    """
    # 优化：如果图片太大，先缩小到 512x512 再分析
    # 理由：特征分析不需要全分辨率，512x512 足够捕捉统计特征
    # 速度提升：1000x1000 → 快 4 倍，2000x2000 → 快 16 倍
    original_shape = img_array.shape
    if img_array.shape[0] > 512 or img_array.shape[1] > 512:
        from PIL import Image
        # 转换为 PIL Image
        if len(img_array.shape) == 3:
            pil_image = Image.fromarray(img_array.astype(np.uint8))
        else:
            pil_image = Image.fromarray(img_array.astype(np.uint8), mode='L')
        
        # 缩小到 512x512
        pil_image = pil_image.resize((512, 512), Image.Resampling.LANCZOS)
        
        # 转回 numpy 数组
        img_array = np.array(pil_image)
        
        # 如果是灰度图，记录一下
        if len(img_array.shape) == 2:
            img_array = img_array[:, :, np.newaxis]
    
    # 转换为灰度图
    if len(img_array.shape) == 3:
        gray = np.mean(img_array, axis=2)
    else:
        gray = img_array
    
    # 1. 计算颜色熵（衡量颜色丰富程度）
    hist = np.histogram(gray.flatten(), bins=256, range=(0, 256))[0]
    hist_norm = hist / hist.sum()
    color_entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-10))
    
    # 2. 计算边缘强度（Sobel 算子）
    from scipy import ndimage
    sobel_x = ndimage.sobel(gray, axis=0)
    sobel_y = ndimage.sobel(gray, axis=1)
    edge_magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
    edge_strength = np.mean(edge_magnitude)
    
    # 3. 计算高频成分比例（傅里叶变换）
    f_transform = np.fft.fft2(gray)
    f_shift = np.fft.fftshift(f_transform)
    magnitude_spectrum = np.abs(f_shift)
    
    h, w = magnitude_spectrum.shape
    center_h, center_w = h // 2, w // 2
    low_freq = magnitude_spectrum[center_h-20:center_h+20, center_w-20:center_w+20]
    high_freq = magnitude_spectrum.copy()
    high_freq[center_h-20:center_h+20, center_w-20:center_w+20] = 0
    high_freq_ratio = np.sum(high_freq) / (np.sum(low_freq) + np.sum(high_freq))
    
    # 调试日志
    print(f"\n[图片类型检测] 特征分析:")
    print(f"  - 颜色熵：{color_entropy:.3f} (低<6.5, 中 6.5-7.5, 高>7.5)")
    print(f"  - 边缘强度：{edge_strength:.3f} (低<30, 中 30-60, 高>60)")
    print(f"  - 高频成分：{high_freq_ratio:.3f} (低<0.7, 高>0.7)")
    if file_size > 0:
        print(f"  - 文件大小：{file_size} bytes")
    if width > 0 and height > 0:
        print(f"  - 图片尺寸：{width}x{height}")
    
    # ========== 第一步：判断是否为文档（优先判断） ==========
    # 文档特征：低颜色熵（颜色单调）
    # 关键：文档的颜色熵通常很低（< 6.5），因为主要是黑白文字
    
    # 先检查是否是文档（最优先）
    if color_entropy < 6.5:
        # 颜色单调，很可能是文档/表格/文字
        print(f"  → 识别结果：DOCUMENT (文档/表格/文字)")
        return ImageType.DOCUMENT.value
    
    # ========== 第二步：判断是否为压缩图（小尺寸网络图） ==========
    # 特征：小尺寸 + 小文件 + 低颜色熵 + 高边缘强度
    # 注意：这一步已经在上面被文档判断拦截了，不会误判文档
    if width > 0 and height > 0 and file_size > 0:
        is_small = (width < 300 and height < 300) or file_size < 100000
        low_color = color_entropy < 6.0
        high_edge = edge_strength > 50
        
        print(f"  [压缩图检测] is_small={is_small} (size={width}x{height}, file={file_size})")
        print(f"  [压缩图检测] low_color={low_color} (entropy={color_entropy:.3f})")
        print(f"  [压缩图检测] high_edge={high_edge} (edge={edge_strength:.3f})")
        
        if is_small and low_color and high_edge:
            print(f"  → 识别结果：COMPRESSED (小尺寸网络图/表情包)")
            return ImageType.COMPRESSED.value
        else:
            print(f"  [压缩图检测] 不满足条件，继续判断")
    
    # ========== 第四步：判断是否为压缩图（大尺寸） ==========
    # 压缩图特征：高高频成分 + 中等颜色熵 + 中等边缘强度
    # 关键：压缩图的边缘强度不会太低（文字仍然清晰）
    if high_freq_ratio > 0.7 and 5.5 < color_entropy < 7.5:
        # 额外检查：压缩图的边缘强度应该 > 20
        if edge_strength > 20:
            print(f"  → 识别结果：COMPRESSED (压缩图像)")
            return ImageType.COMPRESSED.value
        else:
            # 边缘强度太低，应该是模糊文档
            print(f"  → 识别结果：DOCUMENT (模糊文档，边缘强度过低)")
            return ImageType.DOCUMENT.value
    
    # ========== 默认：未知类型 ==========
    # 默认当作照片处理（RealWorldSR 更通用）
    print(f"  → 识别结果：PHOTO (默认)")
    return ImageType.PHOTO.value


def estimate_quality(img_array: np.ndarray) -> str:
    """
    估计图片质量
    
    基于以下特征：
    1. 对比度
    2. 亮度
    3. 清晰度（梯度方差）
    4. 噪点水平
    """
    # 转换为灰度图
    if len(img_array.shape) == 3:
        gray = np.mean(img_array, axis=2)
    else:
        gray = img_array
    
    # 1. 对比度（标准差）
    contrast = np.std(gray)
    
    # 2. 亮度（均值）
    brightness = np.mean(gray)
    
    # 3. 清晰度（梯度方差）
    from scipy import ndimage
    gradient_x = ndimage.sobel(gray, axis=0)
    gradient_y = ndimage.sobel(gray, axis=1)
    gradient_magnitude = np.sqrt(gradient_x**2 + gradient_y**2)
    sharpness = np.var(gradient_magnitude)
    
    # 4. 噪点水平（平滑区域的方差）
    # 使用高斯模糊后与原图的差异
    blurred = ndimage.gaussian_filter(gray, sigma=2)
    noise_level = np.mean((gray - blurred) ** 2)
    
    # 综合评分
    score = 0
    
    # 对比度评分（理想：50-150）
    if 50 < contrast < 150:
        score += 30
    elif 30 < contrast < 200:
        score += 20
    else:
        score += 10
    
    # 亮度评分（理想：100-200）
    if 100 < brightness < 200:
        score += 30
    elif 50 < brightness < 220:
        score += 20
    else:
        score += 10
    
    # 清晰度评分
    if sharpness > 1000:
        score += 30
    elif sharpness > 500:
        score += 20
    else:
        score += 10
    
    # 噪点评分（越低越好）
    if noise_level < 50:
        score += 10
    elif noise_level < 100:
        score += 5
    
    # 根据评分判断质量
    if score >= 80:
        return ImageQuality.EXCELLENT.value
    elif score >= 60:
        return ImageQuality.GOOD.value
    elif score >= 40:
        return ImageQuality.FAIR.value
    else:
        return ImageQuality.POOR.value


def is_low_resolution(width: int, height: int) -> bool:
    """判断是否为低分辨率图片"""
    # 短边小于 512 像素认为是低分辨率
    return min(width, height) < 512


def recommend_scale(width: int, height: int) -> int:
    """
    推荐超分倍数
    
    基于图片尺寸：
    - 超小图（<256）：推荐 X8 或 X16
    - 小图（256-512）：推荐 X4 或 X8
    - 中图（512-1024）：推荐 X2 或 X4
    - 大图（>1024）：推荐 X2 或不超分
    """
    min_dim = min(width, height)
    max_dim = max(width, height)
    
    if min_dim < 256:
        # 超小图，可以大幅度放大
        return 8 if max_dim < 512 else 4
    elif min_dim < 512:
        # 小图
        return 4 if max_dim < 1024 else 2
    elif min_dim < 1024:
        # 中图
        return 2 if max_dim < 2048 else 1
    else:
        # 大图，不建议超分或只轻微超分
        return 1


def recommend_model(img_array: np.ndarray, image_type: str = None, width: int = 0, height: int = 0, file_size: int = 0) -> str:
    """
    推荐模型权重
    
    基于图片类型：
    - ClassicalSR: 理想图片 - 高质量扫描件（本身质量很高，需要强力锐化）
    - CompressedSR: 网络压缩图 - 有损压缩图片（JPEG 压缩、网络传图、小尺寸图）
    - RealWorldSR: 绝大部分情况通用 - 复杂退化（真实照片、模糊文本、老照片、监控截图）
    
    特殊规则：
    - 小尺寸 + 低颜色熵 + 高边缘强度 → CompressedSR（表情包/网络小图）
    - 文档类图片 → RealWorldSR（更温和，减少伪影）
    """
    # 如果已经提供了 image_type，直接使用
    if image_type is None:
        image_type = detect_image_type(img_array, width, height, file_size)
    
    if image_type == ImageType.DOCUMENT.value:
        # 文档类图片使用 RealWorldSR，避免 ClassicalSR 引入过多伪影
        # RealWorldSR 更温和，适合文字识别
        return "realworld"
    elif image_type == ImageType.COMPRESSED.value:
        return "compressed"
    elif image_type == ImageType.PHOTO.value:
        return "realworld"
    else:
        # 未知类型：默认使用 RealWorldSR
        # 理由：模糊老照片、低质量照片等，RealWorldSR 的柔和特性更适合
        return "realworld"


def calculate_confidence(
    img_array: np.ndarray,
    image_type: str,
    quality: str,
    scale: int
) -> float:
    """
    计算推荐置信度
    
    综合考虑：
    - 图片类型识别的确定性
    - 图片质量评估
    - 超分倍数的合理性
    
    返回 0-1 之间的值，越高表示推荐越可靠
    """
    # 基础置信度（基于图片类型识别）
    if len(img_array.shape) == 3:
        gray = np.mean(img_array, axis=2)
    else:
        gray = img_array
    
    # 计算颜色熵
    hist = np.histogram(gray.flatten(), bins=256, range=(0, 256))[0]
    hist_norm = hist / hist.sum()
    color_entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-10))
    
    # 类型识别置信度（0.6-0.95）
    type_confidence = 0.75  # 基础置信度
    if color_entropy < 5.5:
        # 低熵：很可能是文档
        if image_type == "document":
            type_confidence = 0.9
        else:
            type_confidence = 0.65
    elif color_entropy > 6.8:
        # 高熵：很可能是照片
        if image_type == "photo":
            type_confidence = 0.85
        else:
            type_confidence = 0.7
    else:
        # 中等熵：特征不明显
        type_confidence = 0.6
    
    # 质量调整（质量越好，置信度越高）
    quality_bonus = {
        "excellent": 0.15,
        "good": 0.10,
        "fair": 0.05,
        "poor": 0.0
    }.get(quality, 0.05)
    
    # 倍数合理性调整
    height, width = img_array.shape[:2]
    megapixels = (height * width) / 1_000_000
    
    scale_bonus = 0.0  # 默认
    if scale >= 8:
        # 高倍数超分
        if megapixels < 0.3:
            # 图片太小，不推荐高倍数 - 惩罚
            scale_bonus = -0.15
        elif megapixels < 0.5:
            # 图片较小，谨慎推荐
            scale_bonus = -0.05
        else:
            # 图片足够大，可以高倍数
            scale_bonus = 0.10
    elif scale == 4:
        # 标准倍数
        scale_bonus = 0.05
    elif scale <= 2:
        # 低倍数超分
        if megapixels > 2.0:
            # 图片已经很大，低倍数合理
            scale_bonus = 0.10
        else:
            scale_bonus = 0.0
    
    # 综合置信度 = 基础 + 质量奖励 + 倍数奖励
    confidence = type_confidence + quality_bonus + scale_bonus
    
    # 限制在 0.5-0.95 之间
    confidence = max(0.5, min(0.95, confidence))
    
    return round(confidence, 2)
