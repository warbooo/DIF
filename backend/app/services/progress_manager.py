#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
进度管理器 - 用于向客户端发送实时进度更新
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

class ProgressManager:
    """管理修复任务的进度"""
    
    def __init__(self):
        self._progress: Dict[str, Dict[str, Any]] = {}
        self._callbacks: Dict[str, list] = {}
    
    def start_task(self, task_id: str) -> None:
        """开始一个新任务"""
        self._progress[task_id] = {
            "status": "started",
            "step": 0,
            "total_steps": 6,
            "message": "开始处理...",
            "timestamp": datetime.now().isoformat()
        }
        self._notify(task_id)
    
    def update_progress(self, task_id: str, step: int, message: str, details: Optional[str] = None) -> None:
        """更新任务进度"""
        if task_id not in self._progress:
            self.start_task(task_id)
        
        self._progress[task_id].update({
            "step": step,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        self._notify(task_id)
        print(f"[STAT] 任务 {task_id} 进度: {step}/6 - {message}")
    
    def complete_task(self, task_id: str, result: Optional[Dict] = None) -> None:
        """完成任务"""
        if task_id in self._progress:
            self._progress[task_id].update({
                "status": "completed",
                "step": 6,
                "message": "处理完成",
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
            self._notify(task_id)
    
    def fail_task(self, task_id: str, error: str) -> None:
        """任务失败"""
        if task_id in self._progress:
            self._progress[task_id].update({
                "status": "failed",
                "message": f"处理失败: {error}",
                "timestamp": datetime.now().isoformat()
            })
            self._notify(task_id)
    
    def get_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务进度"""
        return self._progress.get(task_id)
    
    def register_callback(self, task_id: str, callback) -> None:
        """注册进度回调函数"""
        if task_id not in self._callbacks:
            self._callbacks[task_id] = []
        self._callbacks[task_id].append(callback)
    
    def _notify(self, task_id: str) -> None:
        """通知所有回调函数"""
        if task_id in self._callbacks:
            progress = self._progress.get(task_id)
            if progress:
                for callback in self._callbacks[task_id]:
                    try:
                        callback(progress)
                    except Exception as e:
                        print(f"回调函数错误: {e}")

# 全局进度管理器实例
progress_manager = ProgressManager()
