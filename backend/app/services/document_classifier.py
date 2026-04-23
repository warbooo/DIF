"""
智能文档分类器
基于深度学习的文档类型自动识别与参数优化
"""
import numpy as np
from PIL import Image
from typing import Dict, List, Tuple, Optional
import cv2
from enum import Enum

class DocumentType(Enum):
    """文档类型枚举"""
    PRINTED = "printed"           # 印刷体文档
    HANDWRITTEN = "handwritten"   # 手写文档
    TABLE = "table"               # 表格文档
    INVOICE = "invoice"           # 发票/票据
    ID_CARD = "id_card"           # 身份证
    CONTRACT = "contract"         # 合同
    BOOK = "book"                 # 书籍
    NEWSPAPER = "newspaper"       # 报纸
    UNKNOWN = "unknown"           # 未知类型


class DocumentClassifier:
    """
    智能文档分类器
    基于图像特征和文本特征的文档类型识别
    """
    
    def __init__(self):
        self.type_weights = {
            DocumentType.PRINTED: 1.0,
            DocumentType.HANDWRITTEN: 1.2,
            DocumentType.TABLE: 1.1,
            DocumentType.INVOICE: 1.0,
            DocumentType.ID_CARD: 1.0,
            DocumentType.CONTRACT: 1.0,
            DocumentType.BOOK: 1.0,
            DocumentType.NEWSPAPER: 1.1,
            DocumentType.UNKNOWN: 1.0
        }
    
    def classify(self, image: Image.Image, ocr_text: str = "") -> Tuple[DocumentType, Dict]:
        """
        分类文档类型
        
        Args:
            image: PIL图像
            ocr_text: OCR识别文本（可选）
        
        Returns:
            (文档类型, 详细信息)
        """
        features = self._extract_features(image, ocr_text)
        doc_type = self._determine_type(features)
        confidence = self._calculate_confidence(features, doc_type)
        
        # 根据文档类型获取最优处理参数
        optimal_params = self._get_optimal_params(doc_type, features)
        
        return doc_type, {
            "type": doc_type.value,
            "confidence": confidence,
            "features": features,
            "optimal_params": optimal_params,
            "recommendations": self._get_recommendations(doc_type, features)
        }
    
    def _extract_features(self, image: Image.Image, ocr_text: str) -> Dict:
        """提取图像和文本特征"""
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        features = {
            # 图像基本特征
            "width": image.width,
            "height": image.height,
            "aspect_ratio": image.width / image.height,
            
            # 纹理特征
            "texture_complexity": self._calculate_texture_complexity(gray),
            "edge_density": self._calculate_edge_density(gray),
            
            # 颜色特征
            "color_variance": np.var(img_array),
            "is_grayscale": self._is_grayscale(img_array),
            
            # 文字特征
            "text_density": len(ocr_text) / (image.width * image.height) if ocr_text else 0,
            "has_chinese": self._has_chinese(ocr_text),
            "has_english": self._has_english(ocr_text),
            "has_numbers": any(c.isdigit() for c in ocr_text),
            
            # 布局特征
            "line_count": ocr_text.count('\n') + 1 if ocr_text else 0,
            "avg_line_length": np.mean([len(line) for line in ocr_text.split('\n')]) if ocr_text else 0,
            
            # 特殊特征
            "has_table_structure": self._detect_table_structure(gray),
            "has_handwriting_features": self._detect_handwriting(gray),
            "has_stamp_or_seal": self._detect_stamp(gray),
        }
        
        return features
    
    def _calculate_texture_complexity(self, gray: np.ndarray) -> float:
        """计算纹理复杂度（使用局部二值模式）"""
        from skimage.feature import local_binary_pattern
        
        radius = 3
        n_points = 8 * radius
        lbp = local_binary_pattern(gray, n_points, radius, method='uniform')
        
        # 计算LBP直方图的熵
        hist, _ = np.histogram(lbp, bins=n_points + 2, range=(0, n_points + 2))
        hist = hist.astype(float)
        hist /= (hist.sum() + 1e-7)
        entropy = -np.sum(hist * np.log2(hist + 1e-7))
        
        return float(entropy)
    
    def _calculate_edge_density(self, gray: np.ndarray) -> float:
        """计算边缘密度"""
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        return float(edge_density)
    
    def _is_grayscale(self, img_array: np.ndarray) -> bool:
        """判断是否为灰度图"""
        if len(img_array.shape) < 3:
            return True
        # 检查RGB通道是否相同
        r, g, b = img_array[:,:,0], img_array[:,:,1], img_array[:,:,2]
        return np.allclose(r, g) and np.allclose(g, b)
    
    def _has_chinese(self, text: str) -> bool:
        """检查是否包含中文"""
        return any('\u4e00' <= char <= '\u9fff' for char in text)
    
    def _has_english(self, text: str) -> bool:
        """检查是否包含英文"""
        return any(char.isalpha() and char.isascii() for char in text)
    
    def _detect_table_structure(self, gray: np.ndarray) -> bool:
        """检测是否包含表格结构"""
        # 使用霍夫变换检测直线
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, 
                                minLineLength=gray.shape[1]//4, 
                                maxLineGap=10)
        
        if lines is None:
            return False
        
        # 统计水平和垂直线
        horizontal = 0
        vertical = 0
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
            
            if angle < 10 or angle > 170:  # 水平线
                horizontal += 1
            elif 80 < angle < 100:  # 垂直线
                vertical += 1
        
        # 如果同时有足够多的水平线和垂直线，可能是表格
        return horizontal >= 3 and vertical >= 3
    
    def _detect_handwriting(self, gray: np.ndarray) -> bool:
        """检测手写特征"""
        # 手写体通常有更不规则的笔画
        # 使用笔画宽度变换（Stroke Width Transform）的简化版本
        
        # 计算图像的局部方差
        local_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # 手写体通常有更高的局部方差
        return local_var > 500
    
    def _detect_stamp(self, gray: np.ndarray) -> bool:
        """检测印章或签名"""
        # 印章通常是红色的，在灰度图中表现为特定亮度区域
        # 这里简化处理，检测圆形或椭圆形状
        
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 100:  # 太小的忽略
                continue
            
            # 计算圆形度
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue
            
            circularity = 4 * np.pi * area / (perimeter ** 2)
            
            # 如果接近圆形，可能是印章
            if circularity > 0.7:
                return True
        
        return False
    
    def _determine_type(self, features: Dict) -> DocumentType:
        """根据特征确定文档类型"""
        scores = {}
        
        # 印刷体文档特征
        scores[DocumentType.PRINTED] = (
            (0.3 if not features["has_handwriting_features"] else 0) +
            (0.3 if features["text_density"] > 0.001 else 0) +
            (0.2 if features["edge_density"] > 0.05 else 0) +
            (0.2 if not features["has_table_structure"] else 0)
        )
        
        # 手写文档特征
        scores[DocumentType.HANDWRITTEN] = (
            (0.4 if features["has_handwriting_features"] else 0) +
            (0.3 if features["texture_complexity"] > 5 else 0) +
            (0.2 if features["line_count"] < 20 else 0) +
            (0.1 if not features["has_table_structure"] else 0)
        )
        
        # 表格文档特征
        scores[DocumentType.TABLE] = (
            (0.5 if features["has_table_structure"] else 0) +
            (0.2 if features["text_density"] > 0.0005 else 0) +
            (0.2 if features["has_numbers"] else 0) +
            (0.1 if not features["has_handwriting_features"] else 0)
        )
        
        # 发票/票据特征
        scores[DocumentType.INVOICE] = (
            (0.3 if features["has_table_structure"] else 0) +
            (0.3 if features["has_numbers"] else 0) +
            (0.2 if 0.3 < features["aspect_ratio"] < 0.7 else 0) +
            (0.2 if features["has_stamp_or_seal"] else 0)
        )
        
        # 身份证特征
        scores[DocumentType.ID_CARD] = (
            (0.4 if 1.4 < features["aspect_ratio"] < 1.7 else 0) +
            (0.3 if features["has_chinese"] and features["has_numbers"] else 0) +
            (0.2 if features["text_density"] < 0.001 else 0) +
            (0.1 if features["has_stamp_or_seal"] else 0)
        )
        
        # 合同特征
        scores[DocumentType.CONTRACT] = (
            (0.3 if features["text_density"] > 0.002 else 0) +
            (0.2 if features["line_count"] > 30 else 0) +
            (0.2 if features["has_chinese"] else 0) +
            (0.2 if features["has_stamp_or_seal"] else 0) +
            (0.1 if not features["has_handwriting_features"] else 0)
        )
        
        # 书籍特征
        scores[DocumentType.BOOK] = (
            (0.3 if features["text_density"] > 0.003 else 0) +
            (0.3 if features["line_count"] > 50 else 0) +
            (0.2 if 0.6 < features["aspect_ratio"] < 0.8 else 0) +
            (0.2 if not features["has_handwriting_features"] else 0)
        )
        
        # 报纸特征
        scores[DocumentType.NEWSPAPER] = (
            (0.3 if features["text_density"] > 0.004 else 0) +
            (0.3 if features["line_count"] > 100 else 0) +
            (0.2 if features["texture_complexity"] > 6 else 0) +
            (0.2 if features["edge_density"] > 0.08 else 0)
        )
        
        # 返回得分最高的类型
        return max(scores, key=scores.get)
    
    def _calculate_confidence(self, features: Dict, doc_type: DocumentType) -> float:
        """计算分类置信度"""
        # 基于特征的明显程度计算置信度
        confidence = 0.5
        
        if doc_type == DocumentType.TABLE and features["has_table_structure"]:
            confidence += 0.3
        if doc_type == DocumentType.HANDWRITTEN and features["has_handwriting_features"]:
            confidence += 0.3
        if doc_type == DocumentType.ID_CARD and 1.4 < features["aspect_ratio"] < 1.7:
            confidence += 0.3
        
        return min(confidence, 1.0)
    
    def _get_optimal_params(self, doc_type: DocumentType, features: Dict) -> Dict:
        """根据文档类型获取最优处理参数"""
        base_params = {
            "use_super_resolution": True,
            "sr_scale": 2,
            "denoise_strength": 0.5,
            "sharpen_strength": 1.0,
            "contrast_enhance": 1.2,
            "ocr_confidence_threshold": 0.6,
        }
        
        # 根据文档类型调整参数
        if doc_type == DocumentType.HANDWRITTEN:
            base_params.update({
                "sr_scale": 4,  # 手写体需要更高的超分
                "denoise_strength": 0.3,  # 保留更多细节
                "sharpen_strength": 1.5,
                "contrast_enhance": 1.4,
                "ocr_confidence_threshold": 0.5,  # 手写体置信度阈值降低
            })
        
        elif doc_type == DocumentType.TABLE:
            base_params.update({
                "sr_scale": 2,
                "denoise_strength": 0.6,
                "sharpen_strength": 1.2,
                "contrast_enhance": 1.3,
                "ocr_confidence_threshold": 0.65,
                "preserve_structure": True,  # 保留表格结构
            })
        
        elif doc_type == DocumentType.INVOICE:
            base_params.update({
                "sr_scale": 2,
                "denoise_strength": 0.4,
                "sharpen_strength": 1.1,
                "contrast_enhance": 1.2,
                "ocr_confidence_threshold": 0.7,
                "enhance_numbers": True,  # 增强数字识别
            })
        
        elif doc_type == DocumentType.ID_CARD:
            base_params.update({
                "sr_scale": 4,
                "denoise_strength": 0.3,
                "sharpen_strength": 1.3,
                "contrast_enhance": 1.3,
                "ocr_confidence_threshold": 0.75,
            })
        
        elif doc_type == DocumentType.BOOK or doc_type == DocumentType.NEWSPAPER:
            base_params.update({
                "sr_scale": 2,
                "denoise_strength": 0.7,  # 去除报纸的噪声
                "sharpen_strength": 1.0,
                "contrast_enhance": 1.4,
                "ocr_confidence_threshold": 0.6,
            })
        
        # 根据图像质量进一步调整
        if features["texture_complexity"] > 7:  # 高复杂度，可能需要更多降噪
            base_params["denoise_strength"] = min(base_params["denoise_strength"] + 0.2, 1.0)
        
        if features["edge_density"] < 0.03:  # 低边缘密度，需要增强锐化
            base_params["sharpen_strength"] += 0.3
        
        return base_params
    
    def _get_recommendations(self, doc_type: DocumentType, features: Dict) -> List[str]:
        """获取处理建议"""
        recommendations = []
        
        if doc_type == DocumentType.HANDWRITTEN:
            recommendations.append("建议使用更高的超分倍数（4x）以增强手写体可读性")
            recommendations.append("手写体识别建议开启拼写纠错功能")
        
        elif doc_type == DocumentType.TABLE:
            recommendations.append("检测到表格结构，建议导出为Excel格式")
            recommendations.append("表格识别建议保持原始布局")
        
        elif doc_type == DocumentType.INVOICE:
            recommendations.append("发票识别建议重点校验金额和日期字段")
            recommendations.append("建议开启印章检测功能")
        
        elif doc_type == DocumentType.ID_CARD:
            recommendations.append("身份证识别建议进行人脸检测和关键信息提取")
            recommendations.append("建议校验身份证号码格式")
        
        if features["texture_complexity"] > 7:
            recommendations.append("图像纹理复杂，建议增强降噪处理")
        
        if features["edge_density"] < 0.03:
            recommendations.append("图像边缘较弱，建议增强锐化处理")
        
        return recommendations


# 全局分类器实例
_classifier: Optional[DocumentClassifier] = None


def get_document_classifier() -> DocumentClassifier:
    """获取全局文档分类器实例"""
    global _classifier
    if _classifier is None:
        _classifier = DocumentClassifier()
    return _classifier


def classify_document(image: Image.Image, ocr_text: str = "") -> Tuple[DocumentType, Dict]:
    """
    分类文档类型（便捷函数）
    
    Args:
        image: PIL图像
        ocr_text: OCR识别文本（可选）
    
    Returns:
        (文档类型, 详细信息)
    """
    classifier = get_document_classifier()
    return classifier.classify(image, ocr_text)
