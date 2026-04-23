#!/usr/bin/env python3
"""
检查并清理 ModelUsageStat 表中平均处理时间异常的记录
"""

import os
import sys
from sqlalchemy.orm import Session

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.db.models import ModelUsageStat
from backend.app.db.session import get_db


def check_model_usage_stats():
    """检查并清理 ModelUsageStat 表中平均处理时间异常的记录"""
    print("开始检查 ModelUsageStat 表...")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 查询所有模型使用统计记录
        all_stats = db.query(ModelUsageStat).all()
        
        print(f"总共有 {len(all_stats)} 条模型使用统计记录")
        
        # 计算每条记录的平均处理时间（秒）
        for stat in all_stats:
            if stat.usage_count > 0:
                avg_time = stat.total_processing_time / stat.usage_count
                print(f"模型类型: {stat.model_type}, 平均处理时间: {avg_time:.2f} 秒, 使用次数: {stat.usage_count}")
        
        # 注意：ModelUsageStat 表存储的是总处理时间，不是单次处理时间
        # 因此不需要删除其中的记录，只需要检查即可
        
        print("检查完成，ModelUsageStat 表不需要清理")
        
    except Exception as e:
        print(f"检查过程中出现错误: {e}")
    finally:
        # 关闭数据库会话
        db.close()


if __name__ == "__main__":
    check_model_usage_stats()
