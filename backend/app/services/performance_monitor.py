"""
性能监控和分析工具
用于记录和分析文档处理全流程的时间分布
"""
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
from functools import wraps
import threading


@dataclass
class TimingRecord:
    """单个计时记录"""
    name: str
    start_time: float
    end_time: float = 0.0
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_complete: bool = False


class PerformanceMonitor:
    """
    性能监控器
    记录处理流程中各阶段的耗时
    """
    
    _instance: Optional['PerformanceMonitor'] = None
    _lock: threading.Lock = threading.Lock()
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化监控器"""
        if getattr(self, '_initialized', False):
            return
        
        self._records: Dict[str, List[TimingRecord]] = defaultdict(list)
        self._active_records: Dict[str, TimingRecord] = {}
        self._session_data: Dict[str, Any] = {}
        self._initialized = True
        print("[Performance Monitor] 性能监控器初始化完成")
    
    def start(self, name: str, metadata: Dict[str, Any] = None) -> str:
        """
        开始计时
        
        Args:
            name: 计时项名称
            metadata: 元数据
        
        Returns:
            记录ID
        """
        record_id = f"{name}_{time.time_ns()}"
        record = TimingRecord(
            name=name,
            start_time=time.perf_counter(),
            metadata=metadata or {}
        )
        self._active_records[record_id] = record
        return record_id
    
    def end(self, record_id: str, metadata: Dict[str, Any] = None) -> Optional[TimingRecord]:
        """
        结束计时
        
        Args:
            record_id: 记录ID
            metadata: 额外的元数据
        
        Returns:
            完整的计时记录
        """
        if record_id not in self._active_records:
            return None
        
        record = self._active_records.pop(record_id)
        record.end_time = time.perf_counter()
        record.duration = record.end_time - record.start_time
        record.is_complete = True
        
        if metadata:
            record.metadata.update(metadata)
        
        self._records[record.name].append(record)
        return record
    
    def measure(self, name: str, metadata: Dict[str, Any] = None):
        """
        装饰器：测量函数执行时间
        
        Args:
            name: 计时项名称
            metadata: 元数据
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                record_id = self.start(name, metadata)
                try:
                    result = func(*args, **kwargs)
                    self.end(record_id)
                    return result
                except Exception as e:
                    self.end(record_id, {"error": str(e)})
                    raise
            return wrapper
        return decorator
    
    def get_statistics(self, name: str) -> Optional[Dict[str, float]]:
        """
        获取某个计时项的统计信息
        
        Args:
            name: 计时项名称
        
        Returns:
            统计信息字典
        """
        if name not in self._records or not self._records[name]:
            return None
        
        durations = [r.duration for r in self._records[name] if r.is_complete]
        
        if not durations:
            return None
        
        return {
            "count": len(durations),
            "total": sum(durations),
            "avg": sum(durations) / len(durations),
            "min": min(durations),
            "max": max(durations),
            "median": sorted(durations)[len(durations) // 2]
        }
    
    def get_all_statistics(self) -> Dict[str, Dict[str, float]]:
        """获取所有计时项的统计信息"""
        return {name: self.get_statistics(name) for name in self._records}
    
    def get_session_report(self) -> Dict[str, Any]:
        """获取当前会话的性能报告"""
        total_time = sum(
            sum(r.duration for r in records if r.is_complete)
            for records in self._records.values()
        )
        
        return {
            "session_data": self._session_data,
            "total_processing_time": total_time,
            "statistics": self.get_all_statistics(),
            "records": {
                name: [
                    {
                        "name": r.name,
                        "duration": r.duration,
                        "metadata": r.metadata
                    }
                    for r in records
                    if r.is_complete
                ]
                for name, records in self._records.items()
            }
        }
    
    def set_session_data(self, key: str, value: Any):
        """设置会话数据"""
        self._session_data[key] = value
    
    def clear(self):
        """清除所有记录"""
        self._records.clear()
        self._active_records.clear()
        self._session_data.clear()


class ProcessingTimer:
    """
    处理流程计时器
    用于记录完整文档处理流程的各阶段耗时
    """
    
    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.current_task_id: Optional[str] = None
    
    def start_task(self, task_id: str):
        """开始一个新的处理任务"""
        self.current_task_id = task_id
        self.monitor.set_session_data("task_id", task_id)
        self.monitor.set_session_data("start_time", time.perf_counter())
    
    def end_task(self):
        """结束处理任务"""
        if self.current_task_id:
            total_time = time.perf_counter() - self.monitor._session_data.get("start_time", 0)
            self.monitor.set_session_data("total_time", total_time)
            self.monitor.set_session_data("end_time", time.perf_counter())
    
    def time_stage(self, stage_name: str, metadata: Dict[str, Any] = None):
        """
        计时上下文管理器，用于记录单个处理阶段
        
        Usage:
            with timer.time_stage("OCR识别"):
                ocr_result = perform_ocr(image)
        """
        return self._StageContext(self.monitor, stage_name, metadata)
    
    class _StageContext:
        """阶段计时上下文管理器"""
        def __init__(self, monitor: PerformanceMonitor, stage_name: str, metadata: Dict[str, Any] = None):
            self.monitor = monitor
            self.stage_name = stage_name
            self.metadata = metadata
            self.record_id: Optional[str] = None
        
        def __enter__(self):
            self.record_id = self.monitor.start(self.stage_name, self.metadata)
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            metadata = None
            if exc_type:
                metadata = {"error": str(exc_val)}
            self.monitor.end(self.record_id, metadata)
            return False
    
    def get_breakdown(self) -> Dict[str, Any]:
        """获取详细的时间分解报告"""
        report = self.monitor.get_session_report()
        return report


# 便捷函数
def get_monitor() -> PerformanceMonitor:
    """获取全局性能监控器实例"""
    return PerformanceMonitor()


def get_timer() -> ProcessingTimer:
    """获取全局处理计时器实例"""
    return ProcessingTimer()


def format_duration(seconds: float) -> str:
    """
    格式化时间显示
    
    Args:
        seconds: 秒数
    
    Returns:
        格式化的字符串
    """
    if seconds < 0.001:
        return f"{seconds * 1000000:.1f}µs"
    elif seconds < 1:
        return f"{seconds * 1000:.1f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
