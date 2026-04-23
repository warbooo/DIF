"""
自定义纠错词典 - 补充 MacBERT 的不足
针对 OCR 识别错误进行专门优化
"""
from typing import Dict, List, Tuple

# 常见 OCR 错别字词典（按优先级排序）
CUSTOM_CORRECTION_DICT: Dict[str, str] = {
    # 常见字形混淆
    "切人点": "切入点",
    "进人了": "进入了",
    "突元": "突兀",
    "登路": "登录",
    "注消": "注销",
    "帐护": "账户",
    "账护": "账户",
    "密玛": "密码",
    "网止": "网址",
    "邮相": "邮箱",
    "手几": "手机",
    "电活": "电话",
    "信自": "信息",
    "更亲": "更新",
    "下裁": "下载",
}

class CustomDictCorrector:
    """自定义词典纠错器"""
    
    def __init__(self):
        self.correction_dict = CUSTOM_CORRECTION_DICT
    
    def correct(self, text: str) -> str:
        """
        对文本进行纠错
        
        Args:
            text: 输入文本
        
        Returns:
            纠错后的文本
        """
        if not text:
            return text
        
        # 应用词典替换
        for wrong, correct in self.correction_dict.items():
            text = text.replace(wrong, correct)
        
        return text
    
    def add_correction(self, wrong: str, correct: str) -> None:
        """
        动态添加纠错规则
        
        Args:
            wrong: 错误文本
            correct: 正确文本
        """
        self.correction_dict[wrong] = correct
    
    def remove_correction(self, wrong: str) -> bool:
        """
        移除纠错规则
        
        Args:
            wrong: 错误文本
        
        Returns:
            是否成功移除
        """
        if wrong in self.correction_dict:
            del self.correction_dict[wrong]
            return True
        return False
    
    def get_corrections(self) -> Dict[str, str]:
        """获取所有纠错规则"""
        return self.correction_dict.copy()

# 全局实例
_corrector = CustomDictCorrector()

def custom_correct(text: str) -> str:
    """
    使用自定义词典进行纠错（便捷函数）
    
    Args:
        text: 输入文本
    
    Returns:
        纠错后的文本
    """
    return _corrector.correct(text)

def add_correction(wrong: str, correct: str) -> None:
    """动态添加纠错规则"""
    _corrector.add_correction(wrong, correct)

def remove_correction(wrong: str) -> bool:
    """移除纠错规则"""
    return _corrector.remove_correction(wrong)
