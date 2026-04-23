"""
异步任务队列服务
支持后台任务执行，即使页面跳转也不会中断
"""
import asyncio
import threading
import uuid
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, Future


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """任务数据类"""
    task_id: str
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    progress: int = 0
    progress_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class AsyncTaskQueue:
    """异步任务队列"""
    
    def __init__(self, max_workers: int = 4):
        self._tasks: Dict[str, Task] = {}
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.Lock()
        self._futures: Dict[str, Future] = {}
    
    def submit_task(
        self,
        func: Callable,
        *args,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        提交一个异步任务
        
        Args:
            func: 要执行的函数，会接收task_id作为第一个参数
            *args: 函数参数
            metadata: 任务元数据
            **kwargs: 函数关键字参数
        
        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())
        
        # 创建任务记录
        task = Task(
            task_id=task_id,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            metadata=metadata or {}
        )
        
        with self._lock:
            self._tasks[task_id] = task
        
        # 提交任务到线程池
        future = self._executor.submit(
            self._execute_task,
            task_id,
            func,
            *args,
            **kwargs
        )
        
        with self._lock:
            self._futures[task_id] = future
        
        return task_id
    
    def _execute_task(self, task_id: str, func: Callable, *args, **kwargs):
        """
        执行任务的包装函数
        
        Args:
            task_id: 任务ID
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
        """
        # 更新任务状态为运行中
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].status = TaskStatus.RUNNING
                self._tasks[task_id].started_at = datetime.now()
        
        try:
            # 执行任务，传入task_id作为第一个参数
            result = func(task_id, *args, **kwargs)
            
            # 更新任务状态为完成
            with self._lock:
                if task_id in self._tasks:
                    self._tasks[task_id].status = TaskStatus.COMPLETED
                    self._tasks[task_id].completed_at = datetime.now()
                    self._tasks[task_id].result = result
                    self._tasks[task_id].progress = 100
                    self._tasks[task_id].progress_message = "处理完成"
        
        except Exception as e:
            # 更新任务状态为失败
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            
            with self._lock:
                if task_id in self._tasks:
                    self._tasks[task_id].status = TaskStatus.FAILED
                    self._tasks[task_id].completed_at = datetime.now()
                    self._tasks[task_id].error = error_msg
                    self._tasks[task_id].progress_message = f"处理失败: {str(e)}"
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务信息
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务对象，如果不存在返回None
        """
        with self._lock:
            return self._tasks.get(task_id)
    
    def update_progress(self, task_id: str, progress: int, message: str):
        """
        更新任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度百分比 (0-100)
            message: 进度消息
        """
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].progress = max(0, min(100, progress))
                self._tasks[task_id].progress_message = message
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否成功取消
        """
        with self._lock:
            if task_id not in self._tasks:
                return False
            
            task = self._tasks[task_id]
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                return False
            
            # 尝试取消future
            if task_id in self._futures:
                future = self._futures[task_id]
                future.cancel()
            
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            return True
    
    def list_tasks(self, status: Optional[TaskStatus] = None) -> list[Task]:
        """
        列出任务
        
        Args:
            status: 可选的状态过滤
        
        Returns:
            任务列表
        """
        with self._lock:
            tasks = list(self._tasks.values())
            if status:
                tasks = [t for t in tasks if t.status == status]
            return tasks
    
    def cleanup_completed_tasks(self, older_than_hours: int = 24):
        """
        清理已完成的旧任务
        
        Args:
            older_than_hours: 清理多少小时前的任务
        """
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(hours=older_than_hours)
        
        with self._lock:
            task_ids_to_remove = []
            for task_id, task in self._tasks.items():
                if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                    task.completed_at and task.completed_at < cutoff):
                    task_ids_to_remove.append(task_id)
            
            for task_id in task_ids_to_remove:
                del self._tasks[task_id]
                if task_id in self._futures:
                    del self._futures[task_id]
    
    def shutdown(self, wait: bool = True):
        """
        关闭任务队列
        
        Args:
            wait: 是否等待所有任务完成
        """
        self._executor.shutdown(wait=wait)


# 全局任务队列实例
_task_queue: Optional[AsyncTaskQueue] = None


def get_task_queue() -> AsyncTaskQueue:
    """获取全局任务队列实例"""
    global _task_queue
    if _task_queue is None:
        _task_queue = AsyncTaskQueue(max_workers=4)
    return _task_queue


def init_task_queue(max_workers: int = 4):
    """初始化任务队列"""
    global _task_queue
    _task_queue = AsyncTaskQueue(max_workers=max_workers)
    return _task_queue
