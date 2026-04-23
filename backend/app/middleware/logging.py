from __future__ import annotations

import time
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..db.models import SystemLog, User
from ..deps import get_current_user_from_token


class LoggingMiddleware(BaseHTTPMiddleware):
    """日志记录中间件"""
    
    async def dispatch(
        self, request: Request,
        call_next: Callable[[Request], Response]
    ) -> Response:
        start_time = time.time()
        
        # 获取客户端信息
        client_info = {
            'ip_address': request.client.host if request.client else None,
            'user_agent': request.headers.get('user-agent')
        }
        
        # 尝试获取当前用户
        current_user: Optional[User] = None
        try:
            db = next(get_db())
            current_user = get_current_user_from_token(request, db)
        except Exception:
            pass
        finally:
            if 'db' in locals():
                db.close()
        
        # 处理请求
        try:
            response = await call_next(request)
            status_code = response.status_code
            status = "success" if 200 <= status_code < 400 else "error"
            message = f"Request completed with status code {status_code}"
        except Exception as e:
            status = "error"
            message = str(e)
            raise
        finally:
            # 计算耗时
            duration = int((time.time() - start_time) * 1000)
            
            # 记录日志
            try:
                db = next(get_db())
                log_entry = SystemLog(
                    user_id=current_user.id if current_user else None,
                    action=f"{request.method} {request.url.path}",
                    resource_type="api_request",
                    resource_id=request.url.path,
                    ip_address=client_info['ip_address'],
                    user_agent=client_info['user_agent'],
                    duration=duration,
                    status=status,
                    message=message,
                    meta={
                        'method': request.method,
                        'path': request.url.path,
                        'query': dict(request.query_params),
                        'status_code': status_code if 'status_code' in locals() else None
                    }
                )
                db.add(log_entry)
                db.commit()
            except Exception:
                # 日志记录失败不应影响请求处理
                pass
            finally:
                if 'db' in locals():
                    db.close()
        
        return response
