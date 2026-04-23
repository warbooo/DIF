"""仪表盘数据统计接口"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from ..db.session import get_db
from ..db.models import RepairTask, OcrResult, CompletionLog, ModelUsageStat, UserSetting, SystemLog, User, UserSatisfactionRating
from ..deps import get_optional_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def get_local_today():
    """获取北京时间的今天日期"""
    from datetime import timezone
    # 获取当前 UTC 时间，然后转换为北京时间
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    beijing_tz = timezone(timedelta(hours=8))
    beijing_now = utc_now.astimezone(beijing_tz)
    return beijing_now


def utc_to_local(utc_dt: datetime) -> datetime:
    """将 UTC 时间转换为北京时间（东八区）"""
    if utc_dt is None:
        return None
    # 假设数据库存储的是 UTC 时间，转换为北京时间（东八区）
    from datetime import timezone
    if utc_dt.tzinfo is None:
        # 如果是没有时区信息的 UTC 时间，添加 UTC 时区
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    # 转换为北京时间（东八区）
    beijing_tz = timezone(timedelta(hours=8))
    return utc_dt.astimezone(beijing_tz)


@router.get("/stats")
def get_dashboard_stats(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    """获取仪表盘统计数据"""
    from ..core.settings import settings
    print(f"[Dashboard] 开始加载统计数据，days={days}")
    print(f"[Dashboard] 数据库路径: {settings.DATABASE_URL}")
    
    # 初始化返回数据结构
    stats = {
        "totalTasks": 0,
        "successRate": 0,
        "avgProcessingTime": 0,
        "activeUsers": 0
    }
    trend = []
    modelUsage = []
    completionStats = {
        "nlpCount": 0,
        "llmCount": 0,
        "totalTokens": 0,
        "successRate": 0,
        "avgDuration": 0
    }
    satisfactionStats = {
        "totalRatings": 0,
        "avgOverall": 0,
        "avgVisual": 0,
        "avgText": 0,
        "avgStain": 0,
        "avgColor": 0
    }
    activities = []
    
    # 获取本地今天的日期
    local_today = get_local_today().date()
    
    # 1. 基础统计 - 使用所有数据
    # 使用直接的 SQL 查询来获取任务数量，绕过 ORM 问题
    from sqlalchemy import text
    result = db.execute(text("SELECT COUNT(*) FROM repair_tasks"))
    total_tasks = result.scalar() or 0
    print(f"[Dashboard] 数据库中总任务数: {total_tasks}")
    
    # 获取所有任务，不过滤 created_at
    all_tasks = db.query(RepairTask).all()
    # 过滤掉 None 对象
    all_tasks = [task for task in all_tasks if task is not None]
    print(f"[Dashboard] 过滤后任务数: {len(all_tasks)}")
    
    # 转换为本地时间并过滤最近 N 天的任务
    local_today = get_local_today().date()
    recent_tasks = 0
    success_tasks = 0
    
    for task in all_tasks:
        try:
            if task and task.created_at:
                local_created = utc_to_local(task.created_at)
                if local_created:
                    # 检查是否在最近 N 天内
                    if local_created.date() >= local_today - timedelta(days=days-1):
                        recent_tasks += 1
                        # 检查是否成功（只统计最近 N 天的成功任务）
                        if task.status == "done":
                            success_tasks += 1
        except Exception as e:
            print(f"[Dashboard] 处理任务时出错：{e}")
            continue
    
    active_users = db.query(func.count(func.distinct(RepairTask.user_id))).scalar() or 0
    
    stats["totalTasks"] = total_tasks
    # 成功率 = 最近 N 天成功任务数 / 最近 N 天总任务数
    stats["successRate"] = round((success_tasks / recent_tasks * 100) if recent_tasks > 0 else 0, 1)
    stats["activeUsers"] = active_users
    
    # 计算平均处理时间 - 从 model_usage_stats 表获取数据
    total_processing_time = 0
    total_usage_count = 0
    
    model_stats = db.query(ModelUsageStat).all()
    for model_stat in model_stats:
        if model_stat.total_processing_time:
            total_processing_time += model_stat.total_processing_time
        if model_stat.usage_count:
            total_usage_count += model_stat.usage_count
    
    stats["avgProcessingTime"] = round(total_processing_time / total_usage_count, 2) if total_usage_count > 0 else 0
    
    print(f"[Dashboard] 总任务数：{total_tasks}, 近{days}天：{recent_tasks}, 成功：{success_tasks}")
    
    # 2. 处理趋势 - 在 Python 中按本地时间统计
    # 获取所有任务
    all_tasks_for_trend = db.query(RepairTask).filter(
        RepairTask.created_at != None
    ).all()
    
    trend_data = []
    for i in range(days - 1, -1, -1):
        day_date = local_today - timedelta(days=i)
        day_start = datetime(day_date.year, day_date.month, day_date.day, 0, 0, 0)
        day_end = day_start + timedelta(days=1)
        
        # 统计这一天的任务数
        count = 0
        for task in all_tasks_for_trend:
            try:
                if task and task.created_at:
                    # 将 UTC 时间转换为北京时间
                    task_created = utc_to_local(task.created_at)
                    if task_created:
                        # 移除时区信息进行比较
                        task_created_naive = task_created.replace(tzinfo=None) if task_created.tzinfo else task_created
                        if day_start <= task_created_naive < day_end:
                            count += 1
            except Exception as e:
                print(f"[Dashboard] 统计趋势时出错：{e}")
                continue
        
        trend_data.append({
            "date": day_date.strftime("%Y-%m-%d"),
            "count": count,
            "percentage": 0
        })
    
    if trend_data:
        max_count = max(item["count"] for item in trend_data)
        for item in trend_data:
            item["percentage"] = (item["count"] / max_count * 100) if max_count > 0 else 0
    
    trend = trend_data
    
    # 3. 模型使用统计
    model_stats = db.query(ModelUsageStat).all()
    
    # 按模型类型汇总统计数据
    model_usage_by_type = {}
    for model_stat in model_stats:
        if model_stat.model_type not in model_usage_by_type:
            model_usage_by_type[model_stat.model_type] = {
                "usage_count": 0,
                "success_count": 0,
                "total_processing_time": 0.0
            }
        model_usage_by_type[model_stat.model_type]["usage_count"] += model_stat.usage_count
        model_usage_by_type[model_stat.model_type]["success_count"] += model_stat.success_count
        model_usage_by_type[model_stat.model_type]["total_processing_time"] += model_stat.total_processing_time
    
    total_model_usage = sum(data["usage_count"] for data in model_usage_by_type.values()) or 1
    
    model_colors = ["#2196f3", "#4caf50", "#ff9800"]
    model_names = ["ClassicalSR", "CompressedSR", "RealWorldSR"]
    
    for i, model_type in enumerate(["classical", "compressed", "realworld"]):
        if model_type in model_usage_by_type:
            data = model_usage_by_type[model_type]
            usage_count = data["usage_count"]
            success_count = data["success_count"]
            total_processing_time = data["total_processing_time"]
            
            modelUsage.append({
                "name": model_names[i],
                "count": usage_count,
                "percentage": round(usage_count / total_model_usage * 100),
                "color": model_colors[i],
                "successRate": round((success_count / usage_count * 100) if usage_count > 0 else 0, 1),
                "avgTime": round(total_processing_time / usage_count) if usage_count > 0 else 0
            })
    
    print(f"[Dashboard] 模型使用统计：{len(modelUsage)} 条")
    
    # 4. 文本补全统计 - 在 Python 中按本地时间过滤
    all_completion_logs = db.query(CompletionLog).filter(
        CompletionLog.created_at != None
    ).all()
    
    # 过滤最近 N 天的日志
    completion_logs = []
    cutoff_date = local_today - timedelta(days=days)
    for log in all_completion_logs:
        if log.created_at:
            local_created = utc_to_local(log.created_at)
            if local_created and local_created.date() >= cutoff_date:
                completion_logs.append(log)
    
    completionStats["nlpCount"] = sum(1 for c in completion_logs if c.completion_type == "nlp_based")
    completionStats["llmCount"] = sum(1 for c in completion_logs if c.completion_type == "llm")
    completionStats["totalTokens"] = sum(c.tokens_used for c in completion_logs) or 0
    
    all_logs = completion_logs
    if all_logs:
        # 计算所有日志的成功率
        success_count = sum(1 for c in all_logs if c.success)
        completionStats["successRate"] = round(success_count / len(all_logs) * 100, 1)
        
        # 计算所有日志的平均耗时
        total_duration = sum(c.processing_time for c in all_logs if c.processing_time)
        completionStats["avgDuration"] = round(total_duration / len(all_logs), 2) if all_logs else 0
    
    # 5. 用户满意度统计
    # 使用新的 TaskRating 表（快速 1-5 星评价）
    from ..db.models import TaskRating
    task_ratings = db.query(TaskRating).all()
    total_task_ratings = len(task_ratings)
    
    # 同时查询旧的多维度评价作为备选
    old_ratings = db.query(UserSatisfactionRating).all()
    total_old_ratings = len(old_ratings)
    
    print(f"[Dashboard] TaskRating: {total_task_ratings} 条，UserSatisfactionRating: {total_old_ratings} 条")
    
    if total_task_ratings > 0:
        # 使用新的 TaskRating 统计数据
        satisfactionStats["totalRatings"] = total_task_ratings
        satisfactionStats["avgOverall"] = round(sum(r.rating for r in task_ratings) / total_task_ratings, 1)
        
        # 计算星级分布
        star_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for r in task_ratings:
            star_distribution[r.rating] += 1
        satisfactionStats["starDistribution"] = star_distribution
        
        print(f"[Dashboard] 星级分布：{star_distribution}")
    elif total_old_ratings > 0:
        # 回退到旧的多维度评价
        satisfactionStats["totalRatings"] = total_old_ratings
        satisfactionStats["avgOverall"] = round(sum(r.overall_satisfaction for r in old_ratings) / total_old_ratings, 1)
        # 旧数据没有星级分布，全部设为 0
        satisfactionStats["starDistribution"] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    
    print(f"[Dashboard] 用户满意度统计：{satisfactionStats['totalRatings']} 条，综合评分：{satisfactionStats['avgOverall']}")
    
    # 6. 最近活动（已移除）
    activities = []
    
    print(f"[Dashboard] 最近活动：0 条")
    
    return {
        "stats": stats,
        "trend": trend,
        "activities": activities,
        "modelUsage": modelUsage,
        "completionStats": completionStats,
        "satisfactionStats": satisfactionStats
    }
