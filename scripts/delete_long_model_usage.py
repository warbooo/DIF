#!/usr/bin/env python3
"""
删除 ModelUsageStat 表中平均处理时间超过 100 秒的记录
"""

import os
import sys
from sqlalchemy.orm import Session

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.db.models import ModelUsageStat
from backend.app.db.session import get_db


def delete_long_model_usage():
    """删除 ModelUsageStat 表中平均处理时间超过 100 秒的记录"""
    print("开始删除 ModelUsageStat 表中平均处理时间超过 100 秒的记录...")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 查询所有模型使用统计记录
        all_stats = db.query(ModelUsageStat).all()
        
        # 找出平均处理时间超过 100 秒的记录
        long_usage_stats = []
        for stat in all_stats:
            if stat.usage_count > 0:
                avg_time = stat.total_processing_time / stat.usage_count
                if avg_time > 100:
                    long_usage_stats.append(stat)
        
        if len(long_usage_stats) == 0:
            print("没有发现平均处理时间超过 100 秒的模型使用记录")
            return
        
        print(f"发现 {len(long_usage_stats)} 条平均处理时间超过 100 秒的模型使用记录，准备删除...")
        
        # 执行删除操作
        for stat in long_usage_stats:
            print(f"删除记录: 模型类型={stat.model_type}, 平均处理时间={stat.total_processing_time/stat.usage_count:.2f}秒")
            db.delete(stat)
        
        # 提交事务
        db.commit()
        
        print(f"成功删除 {len(long_usage_stats)} 条平均处理时间超过 100 秒的模型使用记录")
        
    except Exception as e:
        print(f"删除过程中出现错误: {e}")
        db.rollback()
    finally:
        # 关闭数据库会话
        db.close()


if __name__ == "__main__":
    delete_long_model_usage()
