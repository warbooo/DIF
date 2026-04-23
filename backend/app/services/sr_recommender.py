"""
超分智能推荐服务
根据图片特征自动推荐最优的模型权重和超分倍数
"""
from typing import Dict, Optional
from .image_analyzer import analyze_image, ImageType, ImageQuality


class SRRecommender:
    """超分推荐器"""
    
    # 模型配置
    AVAILABLE_MODELS = {
        'classical': {
            'name': 'ClassicalSR',
            'description': '经典超分模型',
            'scales': [2, 4],
            'best_for': '文字文档、扫描件、书籍照片',
            'tags': ['文字清晰化', '扫描文档', '书籍照片']
        },
        'compressed': {
            'name': 'CompressedSR',
            'description': '压缩图像恢复模型',
            'scales': [4],
            'best_for': '网络压缩图、JPEG 图片',
            'tags': ['去除压缩噪点', 'JPEG 压缩图', '网络下载图']
        },
        'realworld': {
            'name': 'RealWorldSR',
            'description': '真实世界超分模型',
            'scales': [4],
            'best_for': '真实照片、复杂退化',
            'tags': ['人像', '风景', 'AI 图']
        }
    }
    
    # 级联配置（系统只有 X4 模型）
    # 注意：只推荐使用 X4，不推荐级联 X16
    CASCADE_CONFIG = {
        4: {'scales': [4], 'description': '单阶段：X4', 'available': True},   # 有 X4 模型 ✅
    }
    
    def recommend(self, image_bytes: bytes) -> Dict:
        """
        智能推荐最优的模型和超分倍数
        
        Args:
            image_bytes: 图片字节流
        
        Returns:
            推荐结果字典
        """
        # 分析图片
        analysis = analyze_image(image_bytes)
        
        # 提取特征
        image_type = analysis['image_type']
        quality = analysis['quality']
        recommended_scale = analysis['recommended_scale']
        recommended_model = analysis['recommended_model']
        confidence = analysis['confidence']
        
        # 调试日志
        print(f"\n[SR 推荐器] 图片分析结果:")
        print(f"  - 图片类型：{image_type}")
        print(f"  - 质量：{quality}")
        print(f"  - 推荐模型：{recommended_model}")
        print(f"  - 推荐倍数：{recommended_scale}")
        print(f"  - 置信度：{confidence}")
        
        # 生成推荐
        recommendation = self._generate_recommendation(
            image_type=image_type,
            quality=quality,
            scale=recommended_scale,
            model=recommended_model,
            confidence=confidence,
            analysis=analysis
        )
        
        return recommendation
    
    def _generate_recommendation(
        self,
        image_type: str,
        quality: str,
        scale: int,
        model: str,
        confidence: float,
        analysis: Dict
    ) -> Dict:
        """生成推荐结果"""
        
        # 获取模型信息
        model_info = self.AVAILABLE_MODELS.get(model, self.AVAILABLE_MODELS['classical'])
        
        # 限制 CompressedSR 和 RealWorldSR 的超分倍数
        if model in ['compressed', 'realworld']:
            # 这两个模型只有 X4 预训练模型
            scale = 4  # 固定使用 X4
        
        # 调整推荐（根据质量微调）
        # 注意：系统只有 X4 模型，统一推荐 X4
        scale = 4  # 固定使用 X4
        
        # 客观描述图片特征（不添加主观推荐）
        # 从 analysis 中获取实际存在的字段
        quality_score = 7.5  # 默认值
        if analysis['quality'] == 'excellent':
            quality_score = 9.0
        elif analysis['quality'] == 'good':
            quality_score = 7.5
        elif analysis['quality'] == 'fair':
            quality_score = 5.0
        elif analysis['quality'] == 'poor':
            quality_score = 3.0
        
        recommendation_reason = f"图片质量评分：{quality_score:.1f}/10，图片类型：{analysis['image_type']}，分辨率：{analysis['resolution']}"
        
        # 获取级联配置（只有 X4）
        cascade_info = self.CASCADE_CONFIG.get(scale, self.CASCADE_CONFIG[4])
        
        # 生成推荐结果
        result = {
            'recommended_model': model,
            'recommended_model_name': model_info['name'],
            'recommended_scale': scale,
            'cascade_config': cascade_info['scales'],
            'cascade_description': cascade_info['description'],
            'confidence': round(confidence, 2),
            'recommendation_reason': recommendation_reason,
            'image_analysis': {
                'type': image_type,
                'quality': quality,
                'resolution': analysis['resolution'],
                'megapixels': analysis['megapixels']
            },
            'alternative_recommendations': self._get_alternatives(
                model=model,
                scale=scale,
                image_type=image_type
            )
        }
        
        return result
    
    def _get_alternatives(self, model: str, scale: int, image_type: str) -> list:
        """获取备选推荐"""
        alternatives = []
        
        # 备选模型
        for model_key, model_info in self.AVAILABLE_MODELS.items():
            if model_key != model:
                # 所有模型都只推荐 X4
                alternatives.append({
                    'model': model_key,
                    'model_name': model_info['name'],
                    'scale': 4,
                    'reason': f"备选：{model_info['best_for']}"
                })
        
        return alternatives[:2]  # 最多返回 2 个备选


# 全局推荐器实例
recommender = SRRecommender()


def recommend_sr_config(image_bytes: bytes) -> Dict:
    """
    便捷函数：推荐超分配置
    
    Args:
        image_bytes: 图片字节流
    
    Returns:
        推荐结果字典
    """
    return recommender.recommend(image_bytes)
