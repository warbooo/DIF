import { API_BASE } from '../api/base';

/**
 * 检查 token 是否即将过期（剩余时间少于 1 天）
 * @returns boolean 是否即将过期
 */
export function isTokenExpiringSoon(): boolean {
  const token = localStorage.getItem('token');
  if (!token) return false;
  
  try {
    const tokenParts = token.split('.');
    if (tokenParts.length !== 3) return false;
    
    const payload = JSON.parse(atob(tokenParts[1]));
    const currentTime = Date.now() / 1000;
    const expirationTime = payload.exp;
    
    if (!expirationTime) return false;
    
    // 剩余时间少于 1 天（86400 秒）时认为即将过期
    // 注意：现在 token 默认 100 年过期，所以这个检查主要是为了兼容性
    const remainingTime = expirationTime - currentTime;
    return remainingTime < 86400;
  } catch (e) {
    return false;
  }
}

/**
 * 检查 token 是否已过期
 * @returns boolean 是否已过期
 */
export function isTokenExpired(): boolean {
  const token = localStorage.getItem('token');
  if (!token) return true;
  
  try {
    const tokenParts = token.split('.');
    if (tokenParts.length !== 3) return true;
    
    const payload = JSON.parse(atob(tokenParts[1]));
    const currentTime = Date.now() / 1000;
    const expirationTime = payload.exp;
    
    if (!expirationTime) return true;
    
    return expirationTime < currentTime;
  } catch (e) {
    return true;
  }
}

/**
 * 刷新 token
 * @returns Promise<string> 新的 token
 */
export async function refreshToken(): Promise<string | null> {
  const token = localStorage.getItem('token');
  if (!token) return null;
  
  try {
    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    
    if (!response.ok) {
      return null;
    }
    
    const data = await response.json();
    const newToken = data.token;
    
    if (newToken) {
      localStorage.setItem('token', newToken);
      return newToken;
    }
    
    return null;
  } catch (e) {
    console.error('[Auth] 刷新 token 失败:', e);
    return null;
  }
}

/**
 * 获取认证头，自动处理 token 刷新
 * @returns Promise<HeadersInit>
 */
export async function getAuthHeaders(): Promise<HeadersInit> {
  const token = localStorage.getItem('token');
  
  // 如果 token 不存在，返回基础头
  if (!token) {
    return {
      'Content-Type': 'application/json',
    };
  }
  
  // 检查 token 格式
  const tokenParts = token.split('.');
  if (tokenParts.length !== 3) {
    console.warn('[Auth] token 格式无效，使用基础头');
    return {
      'Content-Type': 'application/json',
    };
  }
  
  // 现在 token 默认 100 年过期，所以不再需要频繁检查和刷新
  // 但如果检测到即将过期（兼容性），仍然尝试刷新
  if (isTokenExpiringSoon()) {
    console.log('[Auth] token 即将过期，尝试刷新');
    try {
      const newToken = await refreshToken();
      if (newToken) {
        return {
          'Authorization': `Bearer ${newToken}`,
          'Content-Type': 'application/json',
        };
      } else {
        // 刷新失败，继续使用旧 token
        console.warn('[Auth] token 刷新失败，继续使用旧 token');
        return {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        };
      }
    } catch (error) {
      console.error('[Auth] 刷新 token 时出错:', error);
      // 出错时继续使用旧 token
      return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      };
    }
  }
  
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
}

