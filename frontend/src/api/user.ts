import { API_BASE } from './base';
import { getAuthHeaders as getAuthHeadersFromUtils } from '../utils/auth';

export interface UserProfile {
  id: number;
  username: string;
  created_at: string;
}

export interface UpdateProfileRequest {
}

export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

export interface HistoryRecord {
  task_key: string;
  original_filename: string;
  doc_type: string;
  status: string;
  created_at: string;
  updated_at: string;
  ocr_text: string;
  filled_text: string;
}

export interface UserFile {
  task_key: string;
  filename: string;
  doc_type: string;
  status: string;
  created_at: string;
  has_result: boolean;
}

async function getAuthHeaders(): Promise<HeadersInit> {
  return await getAuthHeadersFromUtils();
}

export async function getProfile(): Promise<UserProfile> {
  const response = await fetch(`${API_BASE}/user/profile`, {
    headers: await getAuthHeaders(),
  });
  
  if (!response.ok) {
    const status = response.status;
    const errorData = await response.json().catch(() => ({}));
    const errorMessage = errorData.detail || `请求失败 (${status})`;
    const error = new Error(errorMessage);
    (error as any).status = status;
    throw error;
  }
  
  return response.json();
}

export async function updateProfile(data: UpdateProfileRequest): Promise<UserProfile> {
  const response = await fetch(`${API_BASE}/user/profile`, {
    method: 'PUT',
    headers: await getAuthHeaders(),
    body: JSON.stringify(data),
  });
  
  if (!response.ok) {
    const status = response.status;
    const errorData = await response.json().catch(() => ({}));
    const error = new Error(errorData.detail || `请求失败 (${status})`);
    (error as any).status = status;
    throw error;
  }
  
  return response.json();
}

export async function changePassword(data: ChangePasswordRequest): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE}/user/change-password`, {
    method: 'POST',
    headers: await getAuthHeaders(),
    body: JSON.stringify(data),
  });
  
  if (!response.ok) {
    const status = response.status;
    let errorMessage = `请求失败 (${status})`;
    
    try {
      // 尝试解析 JSON 响应
      const errorData = await response.json();
      console.error('[ChangePassword] 错误响应:', errorData);
      
      // 尝试多种方式提取错误信息
      if (typeof errorData === 'string') {
        errorMessage = errorData;
      } else if (errorData.detail) {
        errorMessage = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
      } else if (errorData.message) {
        errorMessage = typeof errorData.message === 'string' ? errorData.message : JSON.stringify(errorData.message);
      } else if (errorData.error) {
        errorMessage = typeof errorData.error === 'string' ? errorData.error : JSON.stringify(errorData.error);
      } else {
        // 如果都不是，尝试显示所有字段的 JSON
        errorMessage = JSON.stringify(errorData, null, 2);
      }
    } catch (parseError) {
      console.error('[ChangePassword] 解析错误响应失败:', parseError);
      // 尝试读取纯文本
      try {
        errorMessage = await response.text();
        console.error('[ChangePassword] 错误文本:', errorMessage);
      } catch (textError) {
        errorMessage = '无法解析错误响应';
      }
    }
    
    const error = new Error(errorMessage);
    (error as any).status = status;
    throw error;
  }
  
  return response.json();
}

export async function getHistory(skip: number = 0, limit: number = 20): Promise<HistoryRecord[]> {
  const response = await fetch(`${API_BASE}/user/history?skip=${skip}&limit=${limit}`, {
    headers: await getAuthHeaders(),
  });
  
  if (!response.ok) {
    const status = response.status;
    const errorData = await response.json().catch(() => ({}));
    const error = new Error(errorData.detail || `请求失败 (${status})`);
    (error as any).status = status;
    throw error;
  }
  
  return response.json();
}

export async function getHistoryCount(): Promise<{ total: number }> {
  const response = await fetch(`${API_BASE}/user/history/count`, {
    headers: await getAuthHeaders(),
  });
  
  if (!response.ok) {
    const status = response.status;
    const errorData = await response.json().catch(() => ({}));
    const error = new Error(errorData.detail || `请求失败 (${status})`);
    (error as any).status = status;
    throw error;
  }
  
  return response.json();
}

export async function getUserFiles(skip: number = 0, limit: number = 20): Promise<UserFile[]> {
  const response = await fetch(`${API_BASE}/user/files?skip=${skip}&limit=${limit}`, {
    headers: await getAuthHeaders(),
  });
  
  if (!response.ok) {
    const status = response.status;
    const errorData = await response.json().catch(() => ({}));
    const error = new Error(errorData.detail || `请求失败 (${status})`);
    (error as any).status = status;
    throw error;
  }
  
  return response.json();
}

export async function deleteUserFile(taskKey: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE}/user/files/${taskKey}`, {
    method: 'DELETE',
    headers: await getAuthHeaders(),
  });
  
  if (!response.ok) {
    const status = response.status;
    const errorData = await response.json().catch(() => ({}));
    const error = new Error(errorData.detail || `请求失败 (${status})`);
    (error as any).status = status;
    throw error;
  }
  
  return response.json();
}
