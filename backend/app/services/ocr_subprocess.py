"""
OCR 服务 - 使用 RapidOCR v5 + ONNXRuntime GPU 加速
基于 PaddleOCR v5 的 ONNX 模型，启动速度快（仅1秒）

毕设场景优化:
- 启动速度快，适合频繁重启的开发和演示场景
- 无 PaddlePaddle 和 PyTorch 的 CUDA 冲突
- 使用 ONNXRuntime 调用 GPU，性能优秀
"""
import os
import sys
import json
import base64
import subprocess
import threading
import time
from typing import Dict, Optional

# 导入 OCR 后处理模块
from .ocr_postprocessing import post_process

# RapidOCR v5 服务脚本路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # backend 目录
RAPIDOCR_SERVICE_SCRIPT = os.path.join(BASE_DIR, 'rapidocr_service.py')


class RapidOCRService:
    """
    RapidOCR v5 持久化服务 - 保持子进程运行，避免重复初始化
    使用 ONNXRuntime GPU 加速
    """
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.lock = threading.Lock()
        self._start_process()
    
    def _start_process(self):
        """启动 RapidOCR 子进程"""
        print("[OCR Service] 启动 RapidOCR v5 子进程...")
        
        env = os.environ.copy()
        # 确保 ONNXRuntime 使用 GPU
        env['CUDA_VISIBLE_DEVICES'] = '0'
        
        self.process = subprocess.Popen(
            [sys.executable, RAPIDOCR_SERVICE_SCRIPT],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env,
            cwd=BASE_DIR  # 设置工作目录为 backend 目录
        )
        
        # 等待初始化完成
        print("[OCR Service] 等待 RapidOCR 引擎初始化...")
        start_time = time.time()
        while time.time() - start_time < 60:
            line = self.process.stdout.readline()
            if line:
                print(f"[OCR Worker] {line.strip()}", file=sys.stderr)
                if "引擎初始化完成" in line:
                    print("[OCR Service] RapidOCR 引擎初始化完成！")
                    break
        
        # 启动 stderr 读取线程
        self.stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
        self.stderr_thread.start()
    
    def _read_stderr(self):
        """后台读取 stderr"""
        while self.process and self.process.poll() is None:
            try:
                line = self.process.stderr.readline()
                if line:
                    print(f"[OCR Worker] {line.strip()}", file=sys.stderr)
            except:
                break
    
    def recognize(self, image_bytes: bytes, enable_spell_correction: bool = True) -> Dict:
        """
        执行 OCR 识别
        
        Args:
            image_bytes: 图像字节数据
            enable_spell_correction: 是否启用拼写纠错
        
        Returns:
            Dict: 识别结果
        """
        with self.lock:
            # 检查进程是否还在运行
            if self.process is None or self.process.poll() is not None:
                print("[OCR Service] 子进程已退出，重新启动...")
                self._start_process()
            
            try:
                # 将图像编码为 base64
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                
                # 构建请求（不传递 enable_spell_correction 给子进程，只获取原始 OCR 结果）
                request = {'image': image_base64, 'enable_spell_correction': False}
                
                # 发送请求
                request_json = json.dumps(request)
                self.process.stdin.write(request_json + '\n')
                self.process.stdin.flush()
                
                # 读取响应
                print("[OCR Service] 等待 OCR 响应...")
                start_time = time.time()
                
                while time.time() - start_time < 60:  # 60 秒超时
                    try:
                        line = self.process.stdout.readline()
                        if line:
                            response = json.loads(line.strip())
                            print(f"[OCR Service] 收到响应，成功：{response.get('success', False)}")
                            print(f"[OCR Service] 识别文本长度：{len(response.get('text', ''))} 字符")
                            text_lines = response.get('text', '').split('\n')
                            print(f"[OCR Service] 识别行数：{len(text_lines)} 行")
                            print(f"[OCR Service] 置信度：{response.get('confidences', [])}")
                            print(f"[OCR Service] 响应时间：{time.time() - start_time:.2f} 秒")
                            # 返回原始 OCR 结果，不进行后处理
                            return response
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        print(f"[OCR Service] 读取响应错误：{e}")
                        break
                
                # 超时或错误
                raise Exception("OCR 识别超时或失败")
                
            except Exception as e:
                print(f"[OCR Service] 错误：{e}")
                # 如果出错，尝试重启进程
                self._restart_process()
                
                error_response = {
                    'success': False,
                    'text': '',
                    'confidences': [],
                    'message': f'OCR 服务错误：{str(e)}'
                }
                return error_response
    
    def _restart_process(self):
        """重启子进程"""
        print("[OCR Service] 重启 OCR 子进程...")
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                try:
                    self.process.kill()
                except:
                    pass
        self._start_process()
    
    def close(self):
        """关闭服务"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
            self.process = None


# 全局持久化 OCR 服务
_ocr_service: Optional[RapidOCRService] = None

def get_ocr_service() -> RapidOCRService:
    """获取全局持久化 OCR 服务"""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = RapidOCRService()
    return _ocr_service


def close_ocr_service():
    """关闭 OCR 服务（用于程序退出时清理）"""
    global _ocr_service
    if _ocr_service:
        _ocr_service.close()
        _ocr_service = None


def recognize_once(image_bytes: bytes) -> Dict:
    """
    执行 OCR 识别（使用持久化服务）
    
    Args:
        image_bytes: 图像字节数据
    
    Returns:
        Dict: 识别结果
    """
    service = get_ocr_service()
    return service.recognize(image_bytes)
