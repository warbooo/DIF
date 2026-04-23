"""
文本补全服务 - 修复版本
逐行处理，避免换行符干扰
支持 Qwen 大模型补全（DashScope API）
"""
import re
import requests
from typing import Dict, List, Optional, Tuple
from ..core.settings import settings
from .ocr_postprocessing import get_spell_corrector, OCRPostProcessor


class TextCompletionService:
    """文本补全服务"""
    
    def __init__(self):
        # 缺失标记字符集
        # 包括：下划线、方框、叉号、圆圈、点等常见占位符（移除问号避免混淆）
        self.missing_marks = set([
            # 基础符号
            '_', '□', '■', '▢', '▣', '▤', '▥', '▦', '▧', '▨', '▩', '▪', '▫',
            # 叉号
            '×', 'X', 'x', '*',
            # 圆圈和点
            '○', '●', '◎', '•', '·', '…',
            # 菱形和三角
            '◇', '◆', '▲', '△', '▼', '▽', '★', '☆',
            # 其他占位符
            '#', '@', '~', '-', '—'
        ])
        
        # Qwen 大模型配置 - 支持两种配置方式
        # 方式一：QWEN_API_URL（旧格式）
        # 方式二：LLM_API_BASE + LLM_API_KEY（新格式，DashScope 兼容）
        self.api_key = settings.LLM_API_KEY or ""
        self.api_base = settings.LLM_API_BASE or ""
        self.model = settings.LLM_MODEL or "qwen3.6-plus"
        
        # 优先使用新配置，如果没有则使用旧配置
        if self.api_base and self.api_key:
            self.enable_llm = True
            self.api_url = self.api_base
            print(f"[TextCompletion] Qwen 大模型：已启用 (模型：{self.model}, API: {self.api_base})")
        elif settings.QWEN_API_URL:
            self.enable_llm = True
            self.api_url = settings.QWEN_API_URL
            print(f"[TextCompletion] Qwen 大模型：已启用 (API URL: {self.api_url})")
        else:
            self.enable_llm = False
            self.api_url = ""
            print(f"[TextCompletion] Qwen 大模型：未启用 (未配置 API)")
    
    def detect_missing(self, text: str) -> List[Tuple[int, str]]:
        """
        检测文本中的缺失标记
        
        Args:
            text: 输入文本
        
        Returns:
            List[Tuple[int, str]]: [(位置，标记字符), ...]
        """
        positions = []
        for idx, char in enumerate(text):
            if char in self.missing_marks:
                positions.append((idx, char))
        return positions
    
    def spell_correct_text(self, text: str) -> tuple:
        """
        使用 MacBERT 进行拼写纠错（严格模式）
        
        Args:
            text: 输入文本
        
        Returns:
            tuple: (纠错后的文本，是否成功)
        """
        if not text or not text.strip():
            return text, False
        
        try:
            corrector_dict = get_spell_corrector()
            
            if corrector_dict is None:
                return text, False
            
            # 逐行处理，避免换行符干扰
            lines = text.split('\n')
            corrected_lines = []
            all_errors = []
            
            processor = OCRPostProcessor()
            
            for line_idx, line in enumerate(lines):
                if not line.strip():
                    corrected_lines.append(line)
                    continue
                
                # 保护行首和行尾的空格（格式）
                leading_spaces = len(line) - len(line.lstrip())
                trailing_spaces = len(line) - len(line.rstrip())
                line_content = line.strip() if leading_spaces > 0 or trailing_spaces > 0 else line
                
                # 对该行进行纠错（_macbert_correct 内部会处理非中文字符保护）
                corrected_line, line_errors = processor._macbert_correct(corrector_dict, line_content)
                
                # 恢复行首和行尾的空格（保护格式）
                if leading_spaces > 0 or trailing_spaces > 0:
                    corrected_line = ' ' * leading_spaces + corrected_line + ' ' * trailing_spaces
                
                corrected_lines.append(corrected_line)
                
                # 收集错误（添加行号信息）
                for error in line_errors:
                    error['line'] = line_idx
                    all_errors.append(error)
            
            final_text = '\n'.join(corrected_lines)
            success = len(all_errors) > 0
            
            if success:
                print(f"[TextCompletion] 拼写纠错完成：{repr(text)} → {repr(final_text)}")
                print(f"[TextCompletion] 纠错详情：{all_errors}")
            
            return final_text, success
            
        except Exception as e:
            print(f"[TextCompletion] 拼写纠错失败：{e}")
            import traceback
            traceback.print_exc()
            return text, False
    
    def _call_qwen_llm(self, text: str, missing_positions: List[Tuple[int, str]]) -> Optional[str]:
        """
        调用 Qwen 大模型进行文本补全（支持 DashScope API）
        
        Args:
            text: 输入文本
            missing_positions: 缺失位置列表
        
        Returns:
            Optional[str]: 补全后的文本，失败返回 None
        """
        if not self.enable_llm:
            print("[TextCompletion] Qwen 大模型未启用，跳过 LLM 补全")
            return None
        
        try:
            # 构建提示词
            system_prompt = "你是一个文本补全助手。请补全文本中的缺失部分，缺失处用特殊标记（如□、_等）表示。直接返回补全后的完整文本，不要任何解释。"
            user_prompt = f"请补全以下文本中的缺失部分：\n\n{text}"
            
            # 调用 DashScope API（OpenAI 兼容格式）
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}',
            }
            
            # DashScope 兼容格式（chat/completions）
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.3,  # 较低温度，确保输出稳定
                "top_p": 0.9,
                "stream": False
            }
            
            # 构建完整的 API URL
            # 如果 api_base 已经包含 /v1，则直接使用
            # 否则添加 /v1/chat/completions
            if self.api_base.endswith('/v1') or self.api_base.endswith('/v1/'):
                api_url = f"{self.api_base.rstrip('/')}/chat/completions"
            else:
                api_url = f"{self.api_base.rstrip('/')}/v1/chat/completions"
            
            print(f"[TextCompletion] 调用 Qwen API: {api_url}")
            print(f"[TextCompletion] 模型：{self.model}")
            
            # 重试机制（最多 2 次）
            max_retries = 2
            response = None
            
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        api_url,
                        json=payload,
                        headers=headers,
                        timeout=60  # 增加到 60 秒
                    )
                    if response.status_code == 200:
                        break  # 成功则跳出
                    else:
                        print(f"[TextCompletion] 第 {attempt+1} 次尝试失败：{response.status_code}")
                except requests.exceptions.RequestException as e:
                    if attempt < max_retries - 1:
                        print(f"[TextCompletion] 请求异常，{max_retries - attempt - 1} 秒后重试...")
                        import time
                        time.sleep(1)
                    else:
                        raise  # 最后一次失败则抛出
            
            if response.status_code == 200:
                result = response.json()
                # DashScope 标准响应格式
                completed_text = None
                if 'choices' in result and len(result['choices']) > 0:
                    choice = result['choices'][0]
                    if 'message' in choice and 'content' in choice['message']:
                        completed_text = choice['message']['content']
                    elif 'text' in choice:
                        completed_text = choice['text']
                
                if completed_text:
                    print(f"[TextCompletion] Qwen 补全成功：{repr(text)} → {repr(completed_text)}")
                    return completed_text
                else:
                    print(f"[TextCompletion] Qwen 返回格式未知：{result}")
                    return None
            else:
                print(f"[TextCompletion] Qwen API 调用失败：{response.status_code}")
                print(f"[TextCompletion] 错误信息：{response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"[TextCompletion] Qwen API 请求异常：{e}")
            return None
        except Exception as e:
            print(f"[TextCompletion] Qwen 调用失败：{e}")
            import traceback
            traceback.print_exc()
            return None
    
    def semantic_completion(self, text: str, use_llm: bool = False, enable_spell_correction: bool = False) -> Dict:
        """
        语义补全主函数
        
        Args:
            text: OCR 识别的文本（可能包含缺失标记）
            use_llm: 是否使用大语言模型
            enable_spell_correction: 是否先进行拼写纠错
        
        Returns:
            Dict: 包含补全结果的字典
        """
        steps = []
        completed_text = text
        corrected_text = None
        
        # 1. 拼写纠错（如果启用）- 先纠错
        if enable_spell_correction:
            corrected_text, success = self.spell_correct_text(text)
            if success:
                completed_text = corrected_text
                steps.append('spell_correction')
                print(f"[TextCompletion] MacBERT 拼写纠错完成")
        
        # 2. 检测缺失字符
        missing_positions = self.detect_missing(completed_text)
        
        # 3. 语义补全（如果启用）- 后补全
        if use_llm and missing_positions:
            print(f"[TextCompletion] 检测到 {len(missing_positions)} 处缺失，尝试使用 Qwen 大模型补全...")
            llm_result = self._call_qwen_llm(completed_text, missing_positions)
            
            if llm_result:
                completed_text = llm_result
                steps.append('llm_completion')
                print(f"[TextCompletion] LLM 补全成功")
            else:
                # LLM 失败，保留原始文本（不补全）
                print(f"[TextCompletion] LLM 补全失败，保留原始缺失标记")
        # 如果不使用 LLM，跳过补全，保持原始文本
        
        # 重新检测缺失字符（确认是否全部补全）
        remaining_missing = self.detect_missing(completed_text)
        
        # 确定最终方法（支持组合）
        method_parts = []
        if 'spell_correction' in steps:
            method_parts.append('macbert')
        if 'llm_completion' in steps:
            method_parts.append('llm')
        
        return {
            'completed_text': completed_text,
            'corrected_text': corrected_text,  # 返回纠错后的文本
            'steps': steps,
            'original_text': text,
            'missing_count': len(missing_positions) - len(remaining_missing),  # 实际补全数量
            'completion_positions': [  # 已补全的位置列表
                {'position': pos, 'char': char} 
                for pos, char in missing_positions
            ],
            'method': '+'.join(method_parts) if method_parts else 'none'
        }


# 全局实例
completion_service = TextCompletionService()


# 便捷函数（保持向后兼容）
def quick_complete(text: str) -> Dict:
    """快速补全（只处理缺失标记）"""
    return completion_service.semantic_completion(text, use_llm=False, enable_spell_correction=False)


def detect_missing(text: str) -> List[Tuple[int, str]]:
    """检测缺失标记"""
    return completion_service.detect_missing(text)
