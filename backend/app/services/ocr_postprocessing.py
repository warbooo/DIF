"""
OCR 后处理模块
提供对 OCR 识别结果的后处理功能，包括文本清理、格式校正和布局分析
"""
import re
import os
import signal
from typing import Dict, List, Optional, Tuple
from functools import wraps

# 配置 HuggingFace 镜像和缓存
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['TRANSFORMERS_OFFLINE'] = '1'  # 强制离线模式，使用本地缓存
os.environ['TRANSFORMERS_CACHE'] = 'C:\\Users\\Administrator\\.cache\\huggingface\\hub'  # 指定缓存路径

# 导入 PyCorrector 用于中文拼写纠错
try:
    import pycorrector
    import torch
    # 检查是否有可用的GPU
    HAS_GPU = torch.cuda.is_available()
    if HAS_GPU:
        print("[OCR PostProcessing] 检测到可用GPU，将使用GPU加速拼写纠错")
    else:
        print("[OCR PostProcessing] 未检测到可用GPU，将使用CPU进行拼写纠错")
    HAS_PYCORRECTOR = True
except ImportError:
    HAS_PYCORRECTOR = False
    HAS_GPU = False
    print("[OCR PostProcessing] PyCorrector 未安装，将使用基础后处理")

# 导入评估模块
try:
    from app.services.ocr_evaluation import evaluate_ocr_result
    HAS_EVALUATION = True
except ImportError:
    HAS_EVALUATION = False
    print("[OCR PostProcessing] 评估模块未找到，将跳过评估步骤")

# 导入自定义词典
try:
    from app.services.custom_dict import custom_correct
    HAS_CUSTOM_DICT = True
    print("[OCR PostProcessing] 自定义纠错词典已加载")
except ImportError:
    HAS_CUSTOM_DICT = False
    print("[OCR PostProcessing] 自定义纠错词典未找到")

# 全局单例：拼写纠错器
_global_spell_corrector = None
_global_spell_corrector_initialized = False

def get_spell_corrector():
    """获取全局拼写纠错器（单例模式）"""
    global _global_spell_corrector, _global_spell_corrector_initialized
    
    if _global_spell_corrector_initialized:
        return _global_spell_corrector
    
    if not HAS_PYCORRECTOR:
        _global_spell_corrector_initialized = True
        return None
    
    try:
        print("[OCR PostProcessing] 正在初始化 MacBertCorrector...")
        print("[OCR PostProcessing] 使用本地缓存模型...")
        
        # 直接使用 Transformers 加载本地模型，绕过 PyCorrector 的网络验证
        from transformers import BertTokenizer, BertForMaskedLM
        import torch
        
        # 本地模型路径（使用 HuggingFace Hub 缓存的正确路径）
        model_path = r"C:\Users\Administrator\.cache\huggingface\hub\models--shibing624--macbert4csc-base-chinese\snapshots\615e6e09ef9a69ec487bc7c641ec3a311e2c11b9"
        
        print(f"[OCR PostProcessing] 从本地路径加载：{model_path}")
        
        # 加载 tokenizer 和 model（使用 Bert 而不是 Auto，更可靠）
        tokenizer = BertTokenizer.from_pretrained(model_path, local_files_only=True)
        model = BertForMaskedLM.from_pretrained(model_path, local_files_only=True)
        
        # 移动到 GPU（如果可用）
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model = model.to(device)
        model.eval()
        
        print(f"[OCR PostProcessing] MacBERT 模型加载成功！设备：{device}")
        
        # 创建纠错器对象
        _global_spell_corrector = {
            'tokenizer': tokenizer,
            'model': model,
            'device': device
        }
        print("[OCR PostProcessing] MacBertCorrector 初始化成功！")
        
    except Exception as e:
        print(f"[OCR PostProcessing] MacBertCorrector 初始化失败：{e}")
        print("[OCR PostProcessing] 将使用自定义词典进行纠错")
        _global_spell_corrector = None
    
    _global_spell_corrector_initialized = True
    return _global_spell_corrector


# 服务启动时预加载 MacBERT 模型（避免首次使用延迟）
if HAS_PYCORRECTOR:
    print("[OCR PostProcessing] 预加载 MacBERT 模型...")
    get_spell_corrector()
    print("[OCR PostProcessing] MacBERT 模型预加载完成！")


class OCRPostProcessor:
    """
    OCR 后处理器
    提供对 OCR 识别结果的后处理功能
    """
    
    def __init__(self):
        """初始化后处理器"""
        pass
    
    def process(self, ocr_result: Dict, enable_cleaning: bool = True, enable_formatting: bool = True, enable_layout_analysis: bool = True, enable_spell_correction: bool = True) -> Dict:
        """
        处理 OCR 结果
        
        Args:
            ocr_result: OCR 识别结果
            enable_cleaning: 是否启用文本清理
            enable_formatting: 是否启用格式校正
            enable_layout_analysis: 是否启用布局分析
            enable_spell_correction: 是否启用拼写纠错
        
        Returns:
            Dict: 处理后的结果
        """
        if not ocr_result.get('success', False):
            # 如果 OCR 失败，直接返回原始结果
            return {
                **ocr_result,
                'processed_text': '',
                'post_processing_applied': []
            }
        
        processed_text = ocr_result.get('text', '')
        applied_processes = []
        
        if enable_cleaning:
            processed_text = self._clean_text(processed_text)
            applied_processes.append('cleaning')
        
        if enable_spell_correction and HAS_PYCORRECTOR:
            # 严格模式：只纠错明显的错别字，过滤单字符纠错
            spell_result = self._correct_spelling(processed_text, strict_mode=True)
            
            # 处理返回值（可能是 tuple 或 string）
            if isinstance(spell_result, tuple):
                processed_text, filtered_errors = spell_result
                applied_processes.append('spell_correction')
            else:
                processed_text = spell_result
                applied_processes.append('spell_correction')
                filtered_errors = []
        
        # 跳过格式化和布局分析（保持原文格式）
        # if enable_formatting:
        #     processed_text = self._format_text(processed_text)
        #     applied_processes.append('formatting')
        # 
        # if enable_layout_analysis:
        #     processed_text = self._analyze_layout(processed_text)
        #     applied_processes.append('layout_analysis')
        
        # 评估后处理效果
        evaluation = None
        if HAS_EVALUATION:
            original_text = ocr_result.get('text', '')
            evaluation = evaluate_ocr_result(original_text, processed_text)
        
        return {
            **ocr_result,
            'processed_text': processed_text,
            'post_processing_applied': applied_processes,
            'evaluation': evaluation,
            'filtered_corrections': filtered_errors if 'filtered_errors' in locals() else []  # 被过滤的纠错
        }
    
    def _clean_text(self, text: str) -> str:
        """
        清理文本（仅保留必要的清理，保持原文格式）
        
        Args:
            text: 原始文本
        
        Returns:
            str: 清理后的文本
        """
        # 去除首尾空格
        text = text.strip()
        # 保留原文的标点、大小写和格式
        return text
    
    # _format_text 方法已移除 - 不再进行格式化，保持原文格式
    # _analyze_layout 方法已移除 - 不再进行布局分析
    
    def _correct_spelling(self, text: str, confidence_threshold: float = 0.8, strict_mode: bool = True) -> tuple:
        """
        拼写纠错
        
        Args:
            text: 清理后的文本
            confidence_threshold: 置信度阈值（0-1），只应用置信度高于此值的纠错
            strict_mode: 严格模式，只纠错明显的错别字（音近字、形近字）
        
        Returns:
            tuple: (纠错后的文本，被过滤的错误列表)
        """
        try:
            # 使用全局单例获取纠错器
            corrector = get_spell_corrector()
            
            # 如果纠错器不可用，使用自定义词典降级处理（不显示警告）
            if corrector is None:
                if HAS_CUSTOM_DICT:
                    text = custom_correct(text)
                return text, []
            
            # 如果文本太短（< 2 字符），不需要纠错
            if len(text.strip()) < 2:
                return text, []
            
            # 检测是否包含中文（MacBERT 只针对中文优化）
            if not re.search(r'[\u4e00-\u9fa5]', text):
                # 纯英文/数字文本，仅使用自定义词典
                if HAS_CUSTOM_DICT:
                    text = custom_correct(text)
                return text, []
            
            # 1. 先使用自定义词典纠错（优先级高）
            if HAS_CUSTOM_DICT:
                text = custom_correct(text)
            
            # 2. 再使用 MacBERT 纠错
            # 如果文本太长（> 500 字符），限制纠错范围避免过慢
            if len(text.strip()) > 500:
                print(f"[OCR PostProcessing] 文本过长（{len(text)} 字符），仅进行保守纠错")
                strict_mode = True
            
            # 使用 Transformers 模型进行纠错
            corrected_text, errors = self._macbert_correct(corrector, text)
            
            if errors:
                print(f"[OCR PostProcessing] 检测到 {len(errors)} 处错误")
            
            return corrected_text, errors
            
        except Exception as e:
            print(f"[OCR PostProcessing] 拼写纠错失败：{e}")
            # 如果纠错失败，返回原始文本
            return text, []
    
    def _apply_de_rule(self, text: str) -> dict:
        """
        应用的/地/得 语法规则
        
        规则：
        1. 动词/形容词 + 的 + 名词 → 的（正确）
        2. 动词 + 地 + 动词/形容词 → 地（状语标记）
        3. 动词/形容词 + 得 + 形容词/副词 → 得（补语标记）
        
        常见错误：
        - 跑的很快 → 跑得很快（动词 + 得 + 补语）
        - 高兴的说 → 高兴地说（形容词 + 地 + 动词）
        - 慢慢的走 → 慢慢地走（形容词 + 地 + 动词）
        
        Args:
            text: 纯中文文本
        
        Returns:
            dict: {位置：纠正后的字符}
        """
        import re
        
        corrections = {}
        
        # 规则 1：动词/形容词 + 的 + 很/非常/特别 + 形容词 → 得
        # 例如：跑的很快 → 跑得很快
        pattern1 = r'(.+?) 的 (很 | 非常 | 特别 | 十分 | 格外 | 极其 | 相当 | 挺 | 真 | 太)'
        for match in re.finditer(pattern1, text):
            pos = match.start() + len(match.group(1)) + 1  # "的"的位置
            if pos < len(text) and text[pos] == '的':
                corrections[pos] = '得'
                print(f"[OCR PostProcessing] 规则 1: 动词 + 得 + 补语 → 位置{pos}: 的→得")
        
        # 规则 2：形容词/副词 + 的 + 动词 → 地
        # 例如：高兴的说 → 高兴地说
        # 常见形容词后缀：的、地、得、然
        adj_suffix = '的|地|得|然'
        pattern2 = f'(.+?)({adj_suffix}) 的 ([\u4e00-\u9fa5]+动 | 走 | 跑 | 跳 | 说 | 做 | 看 | 听 | 想 | 笑 | 哭 | 吃 | 喝 | 睡 | 醒 | 站 | 坐 | 躺 | 爬 | 飞 | 游 | 打 | 骂 | 写 | 读 | 学 | 教 | 买 | 卖 | 送 | 收 | 给 | 拿 | 放 | 开 | 关 | 进 | 出 | 上 | 下 | 回 | 去 | 来 | 起 | 倒 | 正 | 反 | 转 | 停 | 等 | 找 | 帮 | 陪 | 跟 | 带 | 领 | 引 | 指 | 点 | 拍 | 摸 | 抱 | 亲 | 吻 | 推 | 拉 | 扯 | 撕 | 剪 | 切 | 炒 | 煮 | 蒸 | 炸 | 烤 | 烧 | 炖 | 焖 | 煨 | 烙 | 摊 | 擀 | 包 | 裹 | 扎 | 系 | 绑 | 解 | 松 | 紧 | 拉 | 扯 | 拽 | 拖 | 拉 | 推 | 按 | 压 | 顶 | 撑 | 托 | 举 | 抬 | 搬 | 移 | 挪 | 推 | 拉 | 扯 | 拽 | 拖 | 拉 | 推)'
        
        # 简化版：形容词/副词 + 的 + 动词 → 地
        simple_pattern = r'([\u4e00-\u9fa5]{2,}) 的 ([\u4e00-\u9fa5])(?!的 | 地 | 得)'
        for match in re.finditer(simple_pattern, text):
            adj = match.group(1)
            verb = match.group(3)
            pos = match.start() + len(adj) + 1  # "的"的位置
            
            # 如果"的"前面是形容词性成分，后面是动词，改为"地"
            # 常见形容词：慢慢、快快、轻轻、重重、悄悄、默默、静静、匆匆、缓缓、渐渐
            adj_words = ['慢慢', '快快', '轻轻', '重重', '悄悄', '默默', '静静', '匆匆', '缓缓', '渐渐',
                        '高兴', '快乐', '愉快', '开心', '伤心', '难过', '痛苦', '愤怒', '生气', '气愤',
                        '认真', '仔细', '小心', '大胆', '勇敢', '害怕', '紧张', '放松', '自然', '随便',
                        '主动', '被动', '积极', '消极', '努力', '用力', '拼命', '全力', '尽力', '尽情',
                        '很快', '非常', '特别', '十分', '极其', '格外', '相当', '挺', '真', '太']
            
            is_adj = any(adj.endswith(w) for w in adj_words) or adj.endswith('地') or adj.endswith('的')
            
            if is_adj:
                if pos not in corrections:  # 不覆盖规则 1
                    corrections[pos] = '地'
                    print(f"[OCR PostProcessing] 规则 2: 形容词 + 地 + 动词 → 位置{pos}: 的→地 (adj={adj}, verb={verb})")
        
        return corrections
    
    def _macbert_correct(self, corrector: dict, text: str) -> tuple:
        """
        使用 MacBERT 进行拼写纠错（严格模式）
        
        处理逻辑：
        1. 提取所有非中文字符，记录位置
        2. 如果中文字符太少（< 5 个），直接返回原文
        3. 只用中文文本调用 MacBERT
        4. 在原始位置还原非中文字符
        5. 只纠正很确定的中文错别字（的/地/得等）
        
        Args:
            corrector: 包含 tokenizer、model、device 的字典
            text: 输入文本
        
        Returns:
            tuple: (纠错后的文本，错误列表)
        """
        try:
            import re
            
            # 1. 统计中文字符数量
            chinese_chars = re.findall(r'[\u4e00-\u9fa5]', text)
            if len(chinese_chars) < 5:
                # 中文字符太少，直接返回
                return text, []
            
            # 2. 提取所有非中文字符片段，记录位置
            non_chinese_segments = []
            segment_id = 0
            
            # 匹配所有连续的非中文字符（包括空格、标点、英文、数字、URL 等）
            pattern = r'[^\u4e00-\u9fa5]+'
            
            for match in re.finditer(pattern, text):
                start, end = match.span()
                segment = match.group()
                non_chinese_segments.append({
                    'id': segment_id,
                    'start': start,
                    'end': end,
                    'text': segment
                })
                segment_id += 1
            
            # 3. 提取纯中文文本（移除所有非中文字符）
            pure_chinese_text = re.sub(pattern, '', text)
            
            # 如果纯中文文本为空，直接返回
            if not pure_chinese_text.strip():
                return text, []
            
            # 4. 对纯中文文本进行 MacBERT 纠错
            tokenizer = corrector['tokenizer']
            model = corrector['model']
            device = corrector['device']
            
            # Tokenize
            inputs = tokenizer(pure_chinese_text, return_tensors='pt', truncation=True, max_length=512)
            input_ids = inputs['input_ids'].to(device)
            attention_mask = inputs['attention_mask'].to(device)
            
            # 预测
            with torch.no_grad():
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                predictions = outputs.logits
            
            # 获取预测结果
            predicted_ids = torch.argmax(predictions, dim=-1)[0]
            
            # 逐字比较，替换模型预测的字符
            corrected_chars = []
            errors = []
            
            # 获取原始 token IDs
            original_ids = input_ids[0]
            
            # 的/地/得 特殊处理规则
            de_pattern_correction = self._apply_de_rule(pure_chinese_text)
            
            for i, (orig_id, pred_id) in enumerate(zip(original_ids, predicted_ids)):
                # 跳过特殊 token（如 [CLS], [SEP], [PAD]）
                if orig_id in [tokenizer.cls_token_id, tokenizer.sep_token_id, tokenizer.pad_token_id]:
                    continue
                
                orig_char = tokenizer.decode([orig_id], skip_special_tokens=True)
                pred_char = tokenizer.decode([pred_id], skip_special_tokens=True)
                
                should_correct = False
                
                # 条件 1：原文和预测不同
                if orig_char == pred_char:
                    # 检查是否是的/地/得规则纠正
                    if de_pattern_correction.get(i) is not None:
                        pred_char = de_pattern_correction[i]
                        should_correct = True
                        print(f"[OCR PostProcessing] 的/地/得 规则纠正：{orig_char} → {pred_char} (位置 {i})")
                    else:
                        corrected_chars.append(orig_char)
                        continue
                else:
                    # 原文和预测不同，应用模型预测结果
                    should_correct = True
                
                if should_correct:
                    errors.append({
                        'position': i,
                        'original': orig_char,
                        'correction': pred_char,
                        'confidence': 0.85
                    })
                    corrected_chars.append(pred_char)
                    print(f"[OCR PostProcessing] 纠正：{orig_char} → {pred_char}")
                else:
                    # 不纠正，保持原文
                    corrected_chars.append(orig_char)
            
            corrected_chinese = ''.join(corrected_chars)
            
            # 5. 在原始位置还原非中文字符
            # 方法：按照原文顺序，交替插入中文片段和非中文片段
            result_chars = []
            chinese_idx = 0
            
            # 重新构建文本：按照原文顺序插入中文和非中文
            pos = 0
            for segment in non_chinese_segments:
                # 添加 segment 之前的中文字符
                while chinese_idx < len(corrected_chinese) and pos < segment['start']:
                    result_chars.append(corrected_chinese[chinese_idx])
                    chinese_idx += 1
                    pos += 1
                
                # 添加非中文片段
                result_chars.append(segment['text'])
                pos = segment['end']
            
            # 添加剩余的中文字符
            while chinese_idx < len(corrected_chinese):
                result_chars.append(corrected_chinese[chinese_idx])
                chinese_idx += 1
            
            result_text = ''.join(result_chars)
            
            if errors:
                print(f"[OCR PostProcessing] 严格模式：检测到 {len(errors)} 处确定的错误")
            
            return result_text, errors
                
        except Exception as e:
            print(f"[OCR PostProcessing] MacBERT 纠错失败：{e}")
            import traceback
            traceback.print_exc()
            return text, []
    
    def _analyze_layout(self, text: str) -> str:
        """
        分析布局
        
        Args:
            text: 格式化后的文本
        
        Returns:
            str: 布局分析后的文本
        """
        # 基于文本内容进行简单的布局分析
        # 例如，识别标题、段落等
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 简单的标题识别（长度较短且全部大写或以特定符号结尾）
            if len(line) < 30 and (line.isupper() or line.endswith(':')):
                # 标题处理
                processed_lines.append(line)
            else:
                # 段落处理
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)


# 全局后处理器实例
_post_processor: Optional[OCRPostProcessor] = None


def get_post_processor() -> OCRPostProcessor:
    """获取全局后处理器实例"""
    global _post_processor
    if _post_processor is None:
        _post_processor = OCRPostProcessor()
    return _post_processor


def post_process(ocr_result: Dict, **kwargs) -> Dict:
    """
    对 OCR 结果进行后处理
    
    Args:
        ocr_result: OCR 识别结果
        **kwargs: 后处理参数
    
    Returns:
        Dict: 处理后的结果
    """
    processor = get_post_processor()
    return processor.process(ocr_result, **kwargs)
