"""
性能分析API路由
提供性能监控数据的查询和分析接口
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..db.models import User
from ..services.performance_monitor import (
    get_monitor,
    get_timer,
    format_duration
)

router = APIRouter(prefix="/api/performance", tags=["performance"])


@router.get("/current")
async def get_current_performance(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前会话的性能数据
    """
    monitor = get_monitor()
    report = monitor.get_session_report()
    
    # 格式化输出，便于阅读
    formatted_report = {
        "total_processing_time": format_duration(report.get("total_processing_time", 0)),
        "statistics": {},
        "session_data": report.get("session_data", {})
    }
    
    # 格式化统计数据
    stats = report.get("statistics", {})
    for stage_name, stage_stats in stats.items():
        if stage_stats:
            formatted_report["statistics"][stage_name] = {
                "count": stage_stats["count"],
                "total": format_duration(stage_stats["total"]),
                "avg": format_duration(stage_stats["avg"]),
                "min": format_duration(stage_stats["min"]),
                "max": format_duration(stage_stats["max"]),
                "median": format_duration(stage_stats["median"])
            }
    
    return formatted_report


@router.get("/statistics")
async def get_performance_statistics(
    current_user: User = Depends(get_current_user)
):
    """
    获取性能统计数据
    """
    monitor = get_monitor()
    all_stats = monitor.get_all_statistics()
    
    result = {}
    for stage_name, stats in all_stats.items():
        if stats:
            result[stage_name] = {
                "count": stats["count"],
                "total": format_duration(stats["total"]),
                "avg": format_duration(stats["avg"]),
                "min": format_duration(stats["min"]),
                "max": format_duration(stats["max"]),
                "median": format_duration(stats["median"])
            }
    
    return result


@router.post("/clear")
async def clear_performance_data(
    current_user: User = Depends(get_current_user)
):
    """
    清除性能监控数据
    """
    monitor = get_monitor()
    monitor.clear()
    return {"success": True, "message": "性能数据已清除"}


@router.get("/bottlenecks")
async def find_performance_bottlenecks(
    current_user: User = Depends(get_current_user),
    top_n: int = 5
):
    """
    找出性能瓶颈（耗时最长的阶段）
    """
    monitor = get_monitor()
    all_stats = monitor.get_all_statistics()
    
    bottlenecks = []
    for stage_name, stats in all_stats.items():
        if stats and stats["count"] > 0:
            bottlenecks.append({
                "stage": stage_name,
                "avg_duration": stats["avg"],
                "total_duration": stats["total"],
                "count": stats["count"],
                "formatted_avg": format_duration(stats["avg"]),
                "formatted_total": format_duration(stats["total"])
            })
    
    # 按平均耗时排序
    bottlenecks.sort(key=lambda x: x["avg_duration"], reverse=True)
    
    return {
        "total_stages": len(bottlenecks),
        "bottlenecks": bottlenecks[:top_n]
    }


@router.get("/report")
async def get_full_performance_report(
    current_user: User = Depends(get_current_user)
):
    """
    获取完整的性能报告
    """
    monitor = get_monitor()
    report = monitor.get_session_report()
    
    # 计算总耗时
    total_time = report.get("total_processing_time", 0)
    
    # 分析各阶段占比
    stage_percentages = {}
    stats = report.get("statistics", {})
    for stage_name, stage_stats in stats.items():
        if stage_stats and total_time > 0:
            percentage = (stage_stats["total"] / total_time) * 100
            stage_percentages[stage_name] = {
                "duration": format_duration(stage_stats["total"]),
                "percentage": round(percentage, 2)
            }
    
    return {
        "summary": {
            "total_time": format_duration(total_time),
            "total_stages": len(stats),
            "session_data": report.get("session_data", {})
        },
        "stage_breakdown": stage_percentages,
        "detailed_statistics": stats,
        "raw_records": report.get("records", {})
    }
