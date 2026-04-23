"""
图像预处理器模块
用于 Swin2SR 超分辨率前的图像质量评估和预处理
"""

import cv2
import numpy as np
from PIL import Image
from typing import Dict, Tuple, Optional
from loguru import logger


class ImagePreprocessor:
    """图像预处理器"""
    
    def __init__(self):
        # 图像质量阈值
        self.quality_thresholds = {
            'laplacian_variance': 100,  # 拉普拉斯方差阈值
            'brightness': 30,  # 亮度阈值
            'noise_level': 25,  # 噪声水平阈值
        }
    
    def preprocess(self, image: Image.Image) -> Tuple[Image.Image, Dict]:
        """
        预处理图像：评估质量并应用增强
        
        返回：处理后的图像 + 质量评估信息
        """
        logger.info("开始预处理图像...")
        
        # 转换为 OpenCV 格式 (BGR)
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # 1. 评估图像质量
        quality_info = self.assess_quality(cv_image)
        logger.info(f"图像质量评估结果：{quality_info}")
        
        # 2. 应用预处理
        preprocessed = self._apply_preprocessing(cv_image, quality_info)
        
        # 3. 转换回 PIL 格式
        result = Image.fromarray(cv2.cvtColor(preprocessed, cv2.COLOR_BGR2RGB))
        
        logger.info("图像预处理完成，返回处理后的图像")
        return result, quality_info
    
    def assess_quality(self, image: np.ndarray) -> Dict:
        """
        评估图像质量
        
        返回：质量评估字典
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 1. 清晰度（拉普拉斯方差）
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        is_blurry = laplacian_var < self.quality_thresholds['laplacian_variance']
        
        # 2. 亮度
        mean_brightness = np.mean(gray)
        is_dark = mean_brightness < self.quality_thresholds['brightness']
        
        # 3. 噪声
        noise_level = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        noise_estimate = np.std(gray - noise_level)
        is_noisy = noise_estimate > self.quality_thresholds['noise_level']
        
        # 4. 压缩伪影
        has_compression_artifacts = self._detect_compression_artifacts(gray)
        
        return {
            'laplacian_variance': float(laplacian_var),
            'is_blurry': is_blurry,
            'mean_brightness': float(mean_brightness),
            'is_dark': is_dark,
            'noise_estimate': float(noise_estimate),
            'is_noisy': is_noisy,
            'has_compression_artifacts': has_compression_artifacts,
            'quality_score': self._calculate_quality_score(
                laplacian_var, mean_brightness, noise_estimate, has_compression_artifacts
            )
        }
    
    def _detect_compression_artifacts(self, gray: np.ndarray) -> bool:
        """
        检测 JPEG/WebP 压缩伪影
        
        使用傅里叶变换检测周期性噪声
        """
        # 傅里叶变换
        f = np.fft.fft2(gray.astype(np.float32))
        f_shift = np.fft.fftshift(f)
        magnitude_spectrum = np.log(np.abs(f_shift) + 1)
        
        # 检测高频分量
        h, w = magnitude_spectrum.shape
        center_h, center_w = h // 2, w // 2
        
        # 提取高频区域
        high_freq_h = magnitude_spectrum[center_h-8:center_h+8, :]
        high_freq_w = magnitude_spectrum[:, center_w-8:center_w+8]
        
        # 检测峰值
        h_peaks = np.max(high_freq_h, axis=1)
        w_peaks = np.max(high_freq_w, axis=0)
        
        # 判断是否有伪影
        h_peak_ratio = np.max(h_peaks) / (np.mean(h_peaks) + 1e-8)
        w_peak_ratio = np.max(w_peaks) / (np.mean(w_peaks) + 1e-8)
        
        has_artifacts = (h_peak_ratio > 3.0) or (w_peak_ratio > 3.0)
        return has_artifacts
    
    def _calculate_quality_score(
        self, 
        laplacian_var: float, 
        brightness: float, 
        noise: float,
        has_artifacts: bool
    ) -> float:
        """计算 0-100 的质量分数
        
        各项权重：
        - 清晰度：0-40 分
        - 亮度：0-20 分
        - 噪声：0-20 分
        - 伪影：0-20 分
        """
        # 清晰度得分（0-40 分）
        clarity_score = min(40, laplacian_var / 10)
        
        # 亮度得分（0-20 分）
        brightness_score = min(20, brightness / 12.75)  # 255/20
        
        # 噪声得分（0-20 分，噪声越低分越高）
        noise_score = max(0, 20 - noise)
        
        # 伪影得分（0-20 分，无伪影得满分）
        artifact_score = 0 if has_artifacts else 20
        
        total_score = clarity_score + brightness_score + noise_score + artifact_score
        return round(total_score, 2)
    
    def _apply_preprocessing(self, image: np.ndarray, quality_info: Dict) -> np.ndarray:
        """
        根据质量评估结果应用预处理
        
        处理顺序：去伪影 → 去噪 → 增亮 → 锐化
        """
        result = image.copy()
        
        # 1. 去除压缩伪影
        if quality_info['has_compression_artifacts']:
            logger.info("检测到压缩伪影，正在去除...")
            result = self._remove_compression_artifacts(result)
        
        # 2. 去噪
        if quality_info['is_noisy']:
            logger.info(f"检测到噪声 (σ={quality_info['noise_estimate']:.2f})，正在去噪...")
            result = self._denoise(result)
        
        # 3. 增亮暗区
        if quality_info['is_dark']:
            logger.info(f"图像偏暗 (μ={quality_info['mean_brightness']:.2f})，正在增亮...")
            result = self._brighten_dark_regions(result)
        
        # 4. 锐化
        if quality_info['is_blurry']:
            logger.info(f"图像模糊 (σ²={quality_info['laplacian_variance']:.2f})，正在锐化...")
            result = self._sharpen(result)
        
        return result
    
    def _remove_compression_artifacts(self, image: np.ndarray) -> np.ndarray:
        """
        去除 JPEG/WebP 压缩伪影
        
        使用非局部均值去噪算法
        """
        # 3 个参数
        h = 10  # 去噪强度
        hForColorComponents = 10  # 颜色分量去噪强度
        templateWindowSize = 7  # 模板窗口大小
        searchWindowSize = 21  # 搜索窗口大小
        
        denoised = cv2.fastNlMeansDenoisingColored(
            image, 
            None, 
            h, 
            hForColorComponents, 
            templateWindowSize, 
            searchWindowSize
        )
        return denoised
    
    def _denoise(self, image: np.ndarray) -> np.ndarray:
        """
        去噪
        
        使用非局部均值去噪算法
        """
        # 根据噪声水平调整参数
        h = min(15, max(5, 10))  # 去噪强度
        denoised = cv2.fastNlMeansDenoisingColored(
            image, 
            None, 
            h, 
            h, 
            7, 
            21
        )
        return denoised
    
    def _brighten_dark_regions(self, image: np.ndarray, gamma: float = 0.7) -> np.ndarray:
        """
        增亮暗区
        
        使用 Gamma 校正提升暗部细节
        """
        # 转换到 LAB 色彩空间
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0].astype(np.float32)
        
        # Gamma 校正
        l_channel_normalized = l_channel / 255.0
        l_channel_corrected = np.power(l_channel_normalized, 1.0 / gamma)
        l_channel_final = (l_channel_corrected * 255).astype(np.uint8)
        
        # 转换回 BGR
        lab[:, :, 0] = l_channel_final
        result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        return result
    
    def _sharpen(self, image: np.ndarray) -> np.ndarray:
        """
        锐化
        
        使用 USM (Unsharp Mask) 锐化算法
        """
        # 高斯模糊
        blurred = cv2.GaussianBlur(image, (0, 0), 3)
        
        # USM 锐化：原图 - 模糊图 = 高频细节
        sharpened = cv2.addWeighted(image, 1.5, blurred, -0.5, 0)
        
        return sharpened


class ParameterTuner:
    """参数调节器
    
    根据图像质量和目标缩放比例自动调节超分辨率参数
    """
    
    def __init__(self):
        # 3 个噪声级别
        self.noise_level_map = {
            'low': 5,      # 低噪声
            'medium': 15,  # 中噪声
            'high': 25,    # 高噪声
        }
    
    def tune_parameters(self, quality_info: Dict, target_scale: int) -> Dict:
        """
        根据图像质量调节参数
        
        返回：优化后的参数字典
        """
        params = {
            'noise_level': self._determine_noise_level(quality_info),
            'enhancement_strength': self._determine_enhancement_strength(quality_info, target_scale),
            'use_preprocessing': True,
            'use_postprocessing': True,
        }
        
        logger.info(f"参数调节完成：{params}")
        return params
    
    def _determine_noise_level(self, quality_info: Dict) -> int:
        """ noise_level """
        if quality_info['is_noisy']:
            return self.noise_level_map['high']
        elif quality_info['quality_score'] < 50:
            return self.noise_level_map['medium']
        else:
            return self.noise_level_map['low']
    
    def _determine_enhancement_strength(
        self, 
        quality_info: Dict, 
        target_scale: int
    ) -> float:
        """
        确定增强强度
        
        参数：
        - quality_info: 图像质量评估结果
        - target_scale: 目标缩放比例
        
        返回：
        - 增强强度（0.0-1.0）
        - 质量差的图像用低强度（0.5）
        - 质量中等的图像用中等强度（0.7）
        - 质量好的图像用高强度（0.8）
        """
        base_strength = 0.8
        
        # 根据质量调整基础强度
        if quality_info['quality_score'] < 50:
            base_strength = 0.5  # 质量差，降低强度
        elif quality_info['quality_score'] < 70:
            base_strength = 0.7
        
        # 根据缩放比例调整
        if target_scale >= 8:
            base_strength *= 0.8  # 高倍缩放时降低强度
        
        return round(base_strength, 2)


def get_preprocessor() -> ImagePreprocessor:
    """获取预处理器实例"""
    return ImagePreprocessor()


def get_parameter_tuner() -> ParameterTuner:
    """获取参数调节器实例"""
    return ParameterTuner()

