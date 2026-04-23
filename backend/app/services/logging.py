from __future__ import annotations

import time
from typing import Dict, Optional, Any, Callable, TypeVar, ParamSpec
from functools import wraps

from fastapi import Request, Depends
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..db.models import SystemLog, User
from ..deps import get_current_user

P = ParamSpec('P')
R = TypeVar('R')


def get_client_info(request: Request) -> Dict[str, Optional[str]]:
    """获取客户端信息"""
    return {
        'ip_address': request.client.host if request.client else None,
        'user_agent': request.headers.get('user-agent')
    }


def log_operation(
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    include_response: bool = False
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """日志记录装饰器"""
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        async def async_wrapper(
            *args: P.args,
            **kwargs: P.kwargs
        ) -> R:
            # 提取请求和数据库会话
            request: Optional[Request] = None
            db: Optional[Session] = None
            current_user: Optional[User] = None
            
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                elif isinstance(arg, Session):
                    db = arg
            
            for key, value in kwargs.items():
                if key == 'request' and isinstance(value, Request):
                    request = value
                elif key == 'db' and isinstance(value, Session):
                    db = value
                elif key == 'current_user' and isinstance(value, User):
                    current_user = value
            
            start_time = time.time()
            client_info = get_client_info(request) if request else {}
            
            try:
                result = await func(*args, **kwargs)
                status = "success"
                message = "Operation completed successfully"
                duration = int((time.time() - start_time) * 1000)  # 转换为毫秒
                
                if db:
                    log_entry = SystemLog(
                        user_id=current_user.id if current_user else None,
                        action=action,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        ip_address=client_info.get('ip_address'),
                        user_agent=client_info.get('user_agent'),
                        duration=duration,
                        status=status,
                        message=message,
                        meta={
                            'response': str(result) if include_response else None
                        }
                    )
                    db.add(log_entry)
                    db.commit()
                
                return result
            except Exception as e:
                status = "error"
                message = str(e)
                duration = int((time.time() - start_time) * 1000)
                
                if db:
                    log_entry = SystemLog(
                        user_id=current_user.id if current_user else None,
                        action=action,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        ip_address=client_info.get('ip_address'),
                        user_agent=client_info.get('user_agent'),
                        duration=duration,
                        status=status,
                        message=message
                    )
                    db.add(log_entry)
                    db.commit()
                
                raise
        
        @wraps(func)
        def sync_wrapper(
            *args: P.args,
            **kwargs: P.kwargs
        ) -> R:
            # 提取请求和数据库会话
            request: Optional[Request] = None
            db: Optional[Session] = None
            current_user: Optional[User] = None
            
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                elif isinstance(arg, Session):
                    db = arg
            
            for key, value in kwargs.items():
                if key == 'request' and isinstance(value, Request):
                    request = value
                elif key == 'db' and isinstance(value, Session):
                    db = value
                elif key == 'current_user' and isinstance(value, User):
                    current_user = value
            
            start_time = time.time()
            client_info = get_client_info(request) if request else {}
            
            try:
                result = func(*args, **kwargs)
                status = "success"
                message = "Operation completed successfully"
                duration = int((time.time() - start_time) * 1000)  # 转换为毫秒
                
                if db:
                    log_entry = SystemLog(
                        user_id=current_user.id if current_user else None,
                        action=action,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        ip_address=client_info.get('ip_address'),
                        user_agent=client_info.get('user_agent'),
                        duration=duration,
                        status=status,
                        message=message,
                        meta={
                            'response': str(result) if include_response else None
                        }
                    )
                    db.add(log_entry)
                    db.commit()
                
                return result
            except Exception as e:
                status = "error"
                message = str(e)
                duration = int((time.time() - start_time) * 1000)
                
                if db:
                    log_entry = SystemLog(
                        user_id=current_user.id if current_user else None,
                        action=action,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        ip_address=client_info.get('ip_address'),
                        user_agent=client_info.get('user_agent'),
                        duration=duration,
                        status=status,
                        message=message
                    )
                    db.add(log_entry)
                    db.commit()
                
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def log_event(
    db: Session,
    action: str,
    status: str,
    user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    duration: Optional[int] = None,
    message: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None
) -> SystemLog:
    """手动记录日志事件"""
    log_entry = SystemLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        duration=duration,
        status=status,
        message=message,
        meta=meta
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry

import asyncio
