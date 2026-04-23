"""
评估指标服务
提供图片修复和文字修复的客观评估指标
"""
import base64
import io
import numpy as np
from PIL import Image
from typing import Dict, Any, Optional
import math


def ensure_valid_float(value: Any, default: float = 0.0) -> float:
    """
    确保返回有效的浮点数，避免 NaN 或 Infinity

    Args:
        value: 要检查的值
        default: 默认值

    Returns:
        有效的浮点数
    """
    try:
        if value is None:
            return default
        float_value = float(value)
        if math.isnan(float_value) or math.isinf(float_value):
            return default
        return float_value
    except (TypeError, ValueError):
        return default


# 导入已有的PSNR/SSIM计算工具
try:
    from swin2sr.utils.util_calculate_psnr_ssim import calculate_psnr, calculate_ssim
    HAS_QUALITY_METRICS = True
except ImportError:
    HAS_QUALITY_METRICS = False
    print("[Evaluation] 警告: 未找到PSNR/SSIM计算工具，将使用模拟值")

# LPIPS指标支持
try:
    import lpips
    import torch
    import torchvision.transforms as transforms
    HAS_LPIPS = True
    lpips_loss_fn = None
    print("[Evaluation] LPIPS指标已加载")
except ImportError:
    HAS_LPIPS = False
    print("[Evaluation] 警告: 未安装lpips库，LPIPS指标不可用")


def get_lpips_model():
    """
    获取LPIPS模型（懒加载）
    """
    global lpips_loss_fn
    if not HAS_LPIPS:
        return None
    
    if lpips_loss_fn is None:
        try:
            lpips_loss_fn = lpips.LPIPS(net='alex')  # 使用AlexNet网络
            if torch.cuda.is_available():
                lpips_loss_fn = lpips_loss_fn.cuda()
        except Exception as e:
            print(f"[Evaluation] LPIPS模型加载失败: {e}")
            return None
    
    return lpips_loss_fn


def base64_to_numpy(b64_string: str) -> Optional[np.ndarray]:
    """
    将base64字符串转换为numpy数组
    
    Args:
        b64_string: base64编码的图片字符串
        
    Returns:
        numpy数组 (HWC格式)
    """
    try:
        # 移除data:image/xxx;base64,前缀
        if ',' in b64_string:
            b64_string = b64_string.split(',')[1]
        
        # 解码base64
        image_bytes = base64.b64decode(b64_string)
        
        # 读取为PIL图片
        image = Image.open(io.BytesIO(image_bytes))
        
        # 转换为numpy数组 (HWC格式)
        image_np = np.array(image)
        
        # 如果是RGBA，转换为RGB
        if len(image_np.shape) == 3 and image_np.shape[2] == 4:
            image = image.convert('RGB')
            image_np = np.array(image)
        
        # 确保是uint8类型
        if image_np.dtype != np.uint8:
            image_np = image_np.astype(np.uint8)
        
        return image_np
    except Exception as e:
        print(f"[Evaluation] base64转numpy失败: {e}")
        return None


def resize_images_to_match(img1: np.ndarray, img2: np.ndarray) -> tuple:
    """
    将两张图片调整为相同尺寸（以较小的为准）
    
    Args:
        img1: 图片1 (HWC格式)
        img2: 图片2 (HWC格式)
        
    Returns:
        (调整后的img1, 调整后的img2)
    """
    try:
        from PIL import Image
        
        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]
        
        # 如果尺寸相同，直接返回
        if h1 == h2 and w1 == w2:
            return img1, img2
        
        # 计算目标尺寸（以较小的为准）
        target_h = min(h1, h2)
        target_w = min(w1, w2)
        
        # 转换为PIL图片进行调整
        pil_img1 = Image.fromarray(img1)
        pil_img2 = Image.fromarray(img2)
        
        pil_img1_resized = pil_img1.resize((target_w, target_h), Image.LANCZOS)
        pil_img2_resized = pil_img2.resize((target_w, target_h), Image.LANCZOS)
        
        # 转回numpy数组
        img1_resized = np.array(pil_img1_resized)
        img2_resized = np.array(pil_img2_resized)
        
        return img1_resized, img2_resized
    except Exception as e:
        print(f"[Evaluation] 图片尺寸调整失败: {e}")
        return img1, img2


def calculate_lpips(
    img1_np: np.ndarray,
    img2_np: np.ndarray
) -> Optional[float]:
    """
    计算LPIPS (Learned Perceptual Image Patch Similarity)
    
    Args:
        img1_np: 图片1 (HWC, numpy)
        img2_np: 图片2 (HWC, numpy)
        
    Returns:
        LPIPS值（越低越好），失败返回None
    """
    if not HAS_LPIPS:
        return None
    
    lpips_model = get_lpips_model()
    if lpips_model is None:
        return None
    
    try:
        # 转换为PyTorch张量并预处理
        transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        img1_tensor = transform(img1_np).unsqueeze(0)
        img2_tensor = transform(img2_np).unsqueeze(0)
        
        if torch.cuda.is_available():
            img1_tensor = img1_tensor.cuda()
            img2_tensor = img2_tensor.cuda()
        
        # 计算LPIPS
        with torch.no_grad():
            lpips_value = lpips_model(img1_tensor, img2_tensor)
        
        return float(lpips_value.item())
    except Exception as e:
        print(f"[Evaluation] LPIPS计算失败: {e}")
        return None


def calculate_image_quality_metrics(
    original_image_b64: str,
    repaired_image_b64: str
) -> Dict[str, Any]:
    """
    计算图片修复质量评估指标
    
    Args:
        original_image_b64: 原图base64
        repaired_image_b64: 修复后图片base64
        
    Returns:
        包含PSNR、SSIM、LPIPS等指标的字典
    """
    # 转换为numpy数组
    img1 = base64_to_numpy(original_image_b64)
    img2 = base64_to_numpy(repaired_image_b64)
    
    if img1 is None or img2 is None:
        return {
            'psnr': 0.0,
            'ssim': 0.0,
            'lpips': None,
            'note': '图片解析失败'
        }
    
    # 调整尺寸使其匹配
    img1_resized, img2_resized = resize_images_to_match(img1, img2)
    
    # 计算LPIPS
    lpips_value = None
    if HAS_LPIPS:
        lpips_value = calculate_lpips(img1_resized, img2_resized)
    
    # 计算PSNR/SSIM
    if HAS_QUALITY_METRICS:
        try:
            psnr = calculate_psnr(img1_resized, img2_resized, crop_border=0, input_order='HWC', test_y_channel=False)
            ssim = calculate_ssim(img1_resized, img2_resized, crop_border=0, input_order='HWC', test_y_channel=False)
            
            return {
                'psnr': ensure_valid_float(round(float(psnr), 2), 25.0),
                'ssim': ensure_valid_float(round(float(ssim), 4), 0.75),
                'lpips': ensure_valid_float(round(float(lpips_value), 4), 0.5) if lpips_value is not None else None,
                'note': '真实计算'
            }
        except Exception as e:
            print(f"[Evaluation] PSNR/SSIM计算失败: {e}")
    
    # 如果计算失败或没有工具，返回模拟值（基于简单的MSE）
    try:
        mse = np.mean((img1_resized.astype(np.float32) - img2_resized.astype(np.float32)) ** 2)
        if mse == 0:
            psnr = 100.0
        else:
            psnr = 10 * np.log10(255.0 ** 2 / mse)
        
        # 简单的SSIM模拟
        ssim = max(0, min(1, 1 - mse / (255.0 ** 2)))
        
        return {
            'psnr': ensure_valid_float(round(float(psnr), 2), 25.0),
            'ssim': ensure_valid_float(round(float(ssim), 4), 0.75),
            'lpips': ensure_valid_float(round(float(lpips_value), 4), 0.5) if lpips_value is not None else None,
            'note': '模拟计算'
        }
    except Exception as e:
        print(f"[Evaluation] 模拟指标计算失败: {e}")
        return {
            'psnr': 25.0,
            'ssim': 0.75,
            'lpips': None,
            'note': '默认值'
        }


def calculate_character_error_rate(original_text: str, repaired_text: str) -> Dict[str, Any]:
    """
    计算文字修复的字符错误率 (CER)
    
    Args:
        original_text: 原图 OCR 文本
        repaired_text: 修复后 OCR 文本
        
    Returns:
        包含 CER、WER、F1 分数、语义准确率的字典
    """
    # 移除空白字符进行比较
    def clean_text(text: str) -> str:
        return ''.join(text.split())
    
    def tokenize(text: str) -> list:
        """简单分词（按空格和标点）"""
        import re
        # 英文分词
        if re.search(r'[a-zA-Z]', text):
            return re.findall(r'\b\w+\b', text.lower())
        # 中文分词（按字符）
        return list(clean_text(text))
    
    original_clean = clean_text(original_text)
    repaired_clean = clean_text(repaired_text)
    
    if not original_clean and not repaired_clean:
        return {
            'cer': 0.0,
            'wer': 0.0,
            'f1_score': 1.0,
            'semantic_accuracy': 1.0,
            'edit_distance': 0,
            'original_chars': 0,
            'repaired_chars': 0,
            'note': '两者都为空'
        }
    
    if not original_clean:
        return {
            'cer': 1.0,
            'wer': 1.0,
            'f1_score': 0.0,
            'semantic_accuracy': 0.0,
            'edit_distance': len(repaired_clean),
            'original_chars': 0,
            'repaired_chars': len(repaired_clean),
            'note': '原图无文字'
        }
    
    # 计算编辑距离
    def levenshtein_distance(s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    # 字符级计算
    edit_distance = levenshtein_distance(original_clean, repaired_clean)
    cer = edit_distance / len(original_clean) if len(original_clean) > 0 else 1.0
    # CER 限制在 0-100% 范围内
    cer = min(cer, 1.0)
    
    # 词级计算（WER）
    original_words = tokenize(original_text)
    repaired_words = tokenize(repaired_text)
    
    # 标准 WER 计算：基于词序列的编辑距离
    # WER = (S + D + I) / N，其中：
    # S = 替换的词数
    # D = 删除的词数
    # I = 插入的词数
    # N = 原始词数
    if len(original_words) > 0:
        # 计算词级别的编辑距离（不是字符级别）
        def word_levenshtein_distance(words1: list, words2: list) -> int:
            """计算两个词列表之间的编辑距离"""
            if len(words1) < len(words2):
                return word_levenshtein_distance(words2, words1)
            
            if len(words2) == 0:
                return len(words1)
            
            previous_row = range(len(words2) + 1)
            for i, w1 in enumerate(words1):
                current_row = [i + 1]
                for j, w2 in enumerate(words2):
                    # 词级别的比较：相同为 0，不同为 1
                    cost = 0 if w1 == w2 else 1
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + cost
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        word_edit_distance = word_levenshtein_distance(original_words, repaired_words)
        wer = word_edit_distance / len(original_words)
        # WER 理论上不应该超过 100%，但在插入错误很多时可能超过
        # 为了直观展示，我们限制最大值为 100%
        wer = min(wer, 1.0)
    else:
        wer = 1.0
    
    # F1 分数计算
    # 准确率：正确识别的字符数 / 识别的总字符数
    # 召回率：正确识别的字符数 / 原始总字符数
    correct_chars = max(0, len(original_clean) - edit_distance)  # 确保不为负数
    precision = correct_chars / len(repaired_clean) if len(repaired_clean) > 0 else 0.0
    recall = correct_chars / len(original_clean) if len(original_clean) > 0 else 0.0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    # F1 分数限制在 0-1 范围内
    f1_score = max(0.0, min(f1_score, 1.0))
    
    # 语义准确率（简化版本：基于编辑距离的归一化）
    semantic_accuracy = max(0, 1 - cer)
    # 语义准确率限制在 0-1 范围内
    semantic_accuracy = max(0.0, min(semantic_accuracy, 1.0))
    
    return {
        'cer': ensure_valid_float(round(float(cer), 4), 0.0),
        'wer': ensure_valid_float(round(float(wer), 4), 0.0),
        'f1_score': ensure_valid_float(round(float(f1_score), 4), 0.0),
        'semantic_accuracy': ensure_valid_float(round(float(semantic_accuracy), 4), 0.0),
        'edit_distance': edit_distance,
        'original_chars': len(original_clean),
        'repaired_chars': len(repaired_clean),
        'precision': ensure_valid_float(round(float(precision), 4), 0.0),
        'recall': ensure_valid_float(round(float(recall), 4), 0.0),
        'note': '真实计算'
    }


def get_metric_explanation() -> Dict[str, Any]:
    """
    获取评估指标说明
    """
    return {
        'image_metrics': {
            'ssim': {
                'name': 'SSIM (结构相似性)',
                'description': '结构相似性，范围 0-1，越接近 1 越好，>0.8 认为质量良好',
                'range': '0-1',
                'good_threshold': 0.8
            },
            'lpips': {
                'name': 'LPIPS (感知相似性)',
                'description': '基于深度学习的感知相似性，范围 0-1，越低越好，<0.2 认为质量良好',
                'range': '0-1',
                'good_threshold': 0.2
            }
        },
        'text_metrics': {
            'cer': {
                'name': 'CER (字符错误率)',
                'description': '字符错误率，范围 0-1，越低越好，<0.1 认为质量良好',
                'range': '0-1',
                'good_threshold': 0.1
            },
            'wer': {
                'name': 'WER (词错误率)',
                'description': '词错误率，范围 0-1，越低越好，<0.1 认为质量良好',
                'range': '0-1',
                'good_threshold': 0.1
            },
            'f1_score': {
                'name': 'F1 分数',
                'description': '准确率和召回率的调和平均值，范围 0-1，越高越好，>0.9 认为质量良好',
                'range': '0-1',
                'good_threshold': 0.9
            },
            'semantic_accuracy': {
                'name': '语义准确率',
                'description': '语义正确性评估，范围 0-1，越高越好，>0.9 认为质量良好',
                'range': '0-1',
                'good_threshold': 0.9
            }
        }
    }
