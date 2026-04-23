#!/usr/bin/env python3
"""
删除 SystemLog 表中时长超过 100 秒的记录
"""

import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.db.models import SystemLog
from backend.app.db.session import get_db


def delete_long_duration_logs():
    """删除时长超过 100 秒的系统日志记录"""
    print("开始删除时长超过 100 秒的系统日志记录...")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 计算阈值：100 秒 = 100000 毫秒
        threshold_ms = 100 * 1000
        
        # 查询符合条件的记录数量
        long_logs_count = db.query(SystemLog).filter(SystemLog.duration > threshold_ms).count()
        
        if long_logs_count == 0:
            print("没有发现时长超过 100 秒的记录")
            return
        
        print(f"发现 {long_logs_count} 条时长超过 100 秒的记录，准备删除...")
        
        # 执行删除操作
        deleted_count = db.query(SystemLog).filter(SystemLog.duration > threshold_ms).delete()
        
        # 提交事务
        db.commit()
        
        print(f"成功删除 {deleted_count} 条时长超过 100 秒的记录")
        
    except Exception as e:
        print(f"删除过程中出现错误: {e}")
        db.rollback()
    finally:
        # 关闭数据库会话
        db.close()


if __name__ == "__main__":
    delete_long_duration_logs()
