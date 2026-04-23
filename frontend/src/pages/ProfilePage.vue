<template>
  <div class="profile-page">
    <!-- 个人信息 -->
    <section v-if="currentView === 'info'" class="content-section">
      <h2>个人信息与密码修改</h2>
      <div class="info-card">
        <h3 class="section-subtitle">基本信息</h3>
        <div class="form-group">
          <label>用户名</label>
          <input type="text" :value="profile?.username" disabled class="form-input disabled" />
          <span class="hint">用户名不可修改</span>
        </div>
        
        <div class="form-group">
          <label>注册时间</label>
          <input type="text" :value="formatDate(profile?.created_at)" disabled class="form-input disabled" />
        </div>
        
        <h3 class="section-subtitle" style="margin-top: 24px">修改密码</h3>
        <div class="form-group">
          <label>原密码</label>
          <input 
            type="password" 
            v-model="passwordForm.old_password" 
            class="form-input"
            placeholder="请输入原密码"
          />
        </div>
        
        <div class="form-group">
          <label>新密码</label>
          <input 
            type="password" 
            v-model="passwordForm.new_password" 
            class="form-input"
            placeholder="请输入新密码（至少 8 位）"
          />
        </div>
        
        <div class="form-group">
          <label>确认新密码</label>
          <input 
            type="password" 
            v-model="passwordForm.confirm_password" 
            class="form-input"
            placeholder="请再次输入新密码"
          />
        </div>
        
        <div class="form-actions">
          <button class="btn btn-primary" @click="saveProfile" :disabled="saving">
            {{ saving ? '保存中...' : '保存修改' }}
          </button>
        </div>
      </div>
    </section>
    
    <!-- 文件中心 -->
    <section v-if="currentView === 'files'" class="content-section">
      <h2>个人文件库</h2>
      
      <div v-if="loadingFiles" class="loading-spinner"></div>
      
      <div v-else-if="files.length === 0" class="empty-state">
        <span class="empty-icon">📁</span>
        <p>暂无文件</p>
      </div>
      
      <div v-else class="file-list">
        <div v-for="file in files" :key="file.task_key" class="file-item">
          <div class="file-info">
            <div class="file-details">
              <span class="filename">{{ file.filename }}</span>
              <span class="file-meta">
                {{ formatDate(file.created_at) }} | 
                状态：{{ formatStatus(file.status) }}
                <span v-if="file.has_result" class="has-result">✓ 有结果</span>
              </span>
            </div>
          </div>
          <div class="file-actions">
            <button 
              v-if="file.has_result"
              class="btn btn-small btn-secondary"
              @click="viewFileDetail(file.task_key)"
            >
              查看详情
            </button>
            <button 
              class="btn btn-small btn-danger"
              @click="openDeleteConfirm(file.task_key)"
              :disabled="deletingFiles.has(file.task_key)"
            >
              {{ deletingFiles.has(file.task_key) ? '删除中...' : '删除' }}
            </button>
          </div>
        </div>
        
        <div v-if="hasMoreFiles" class="load-more">
          <button class="btn btn-secondary" @click="loadMoreFiles" :disabled="loadingMoreFiles">
            {{ loadingMoreFiles ? '加载中...' : '加载更多' }}
          </button>
        </div>
      </div>
    </section>
    
    <!-- 消息提示 -->
    <div v-if="message" class="message-toast" :class="message.type">
      {{ message.text }}
    </div>
  </div>
  
  <!-- 使用 Teleport 将模态框渲染到 body，确保始终相对于视口定位 -->
  <Teleport to="body">
    <!-- 文件详情模态框 -->
    <div v-if="showFileDetailModal" class="modal-overlay" @click.self="closeFileDetailModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>文件详情</h3>
          <button class="modal-close" @click="closeFileDetailModal">×</button>
        </div>
        <div class="modal-body">
          <div v-if="loadingFileDetail" class="loading-spinner"></div>
          <div v-else-if="fileDetail" class="file-detail">
            <div class="detail-row">
              <span class="detail-label">文件名:</span>
              <span class="detail-value">{{ fileDetail.original_filename }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">状态:</span>
              <span class="detail-value" :class="fileDetail.status">{{ formatStatus(fileDetail.status) }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">处理时间:</span>
              <span class="detail-value">{{ formatDate(fileDetail.created_at) }}</span>
            </div>
            
            <div v-if="fileDetail.ocr_text" class="detail-section">
              <h4>OCR 识别结果</h4>
              <div class="text-content">{{ fileDetail.ocr_text }}</div>
            </div>
            
            <div v-if="fileDetail.filled_text" class="detail-section">
              <h4>补全结果</h4>
              <div class="text-content">{{ fileDetail.filled_text }}</div>
            </div>
            
            <div v-if="fileDetail.repaired_image_base64" class="detail-section">
              <h4>修复后图像</h4>
              <div class="image-container">
                <img :src="'data:image/png;base64,' + fileDetail.repaired_image_base64" alt="修复后图像" class="result-image" />
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            <span class="empty-icon">⚠️</span>
            <p>暂无详情信息</p>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-primary" @click="downloadResult">下载结果</button>
        </div>
      </div>
    </div>
    
    <!-- 删除确认模态框 -->
    <div v-if="showDeleteConfirm" class="modal-overlay" @click.self="cancelDelete">
      <div class="modal-content">
        <div class="modal-header">
          <h3>确认删除</h3>
          <button class="modal-close" @click="cancelDelete">×</button>
        </div>
        <div class="modal-body">
          <div class="confirmation-content">
            <span class="confirmation-icon">⚠️</span>
            <p>确定要删除这个文件吗？此操作不可恢复。</p>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="cancelDelete">取消</button>
          <button class="btn btn-danger" @click="confirmDelete">确认删除</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { API_BASE } from '../api/base';
import { isTokenExpiringSoon, refreshToken } from '../utils/auth';
import {
  getProfile,
  updateProfile,
  changePassword as apiChangePassword,
  getUserFiles,
  deleteUserFile,
  type UserProfile,
  type UserFile,
} from '../api/user';

const route = useRoute();
const router = useRouter();

// 根据路由参数判断显示哪个视图
const currentView = computed(() => {
  if (route.path.includes('/files')) {
    return 'files';
  }
  return 'info'; // 默认显示个人信息
});
const message = ref<{ type: 'success' | 'error'; text: string } | null>(null);

// 个人信息
const profile = ref<UserProfile | null>(null);
const saving = ref(false);

// 密码修改
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
});

// 文件库
const files = ref<UserFile[]>([]);
const loadingFiles = ref(false);
const loadingMoreFiles = ref(false);
const filesPage = ref(0);
const hasMoreFiles = ref(true);
const deletingFiles = ref(new Set<string>());

// 文件详情模态框
const showFileDetailModal = ref(false);
const loadingFileDetail = ref(false);
const fileDetail = ref<any>(null);
const currentFileTaskKey = ref<string>('');

// 确认删除模态框
const showDeleteConfirm = ref(false);
const fileToDelete = ref<string>('');

function showMessage(text: string, type: 'success' | 'error' = 'success') {
  message.value = { text, type };
  setTimeout(() => {
    message.value = null;
  }, 3000);
}

function formatDate(dateStr: string | undefined) {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN');
}

function formatStatus(status: string) {
  const statusMap: Record<string, string> = {
    done: '已完成',
    failed: '失败',
    processing: '处理中',
  };
  return statusMap[status] || status;
}

async function loadProfile() {
  try {
    profile.value = await getProfile();
    
    // 加载成功后检查 token 是否即将过期
    if (isTokenExpiringSoon()) {
      console.log('[ProfilePage] token 即将过期，尝试刷新');
      const newToken = await refreshToken();
      if (newToken) {
        console.log('[ProfilePage] token 刷新成功');
      } else {
        console.warn('[ProfilePage] token 刷新失败');
      }
    }
  } catch (error: any) {
    console.error('[ProfilePage] 获取用户信息失败:', error);
    
    // 如果是认证错误（401/403），清除 token 并跳转到登录页
    const status = error.status || 0;
    if (status === 401 || status === 403) {
      localStorage.removeItem('token');
      router.push('/auth');
      showMessage('登录已过期，请重新登录', 'error');
      return;
    }
    
    showMessage('获取用户信息失败', 'error');
  }
}

async function saveProfile() {
  saving.value = true;
  try {
    // 如果填写了密码信息，则修改密码
    const hasPasswordChange = passwordForm.old_password || passwordForm.new_password || passwordForm.confirm_password;
    
    if (hasPasswordChange) {
      // 验证原密码是否填写
      if (!passwordForm.old_password) {
        showMessage('请输入原密码', 'error');
        saving.value = false;
        return;
      }
      
      if (passwordForm.new_password !== passwordForm.confirm_password) {
        showMessage('两次输入的新密码不一致', 'error');
        saving.value = false;
        return;
      }
      
      if (passwordForm.new_password.length < 8) {
        showMessage('新密码至少需要 8 位', 'error');
        saving.value = false;
        return;
      }
      
      await apiChangePassword({
        old_password: passwordForm.old_password,
        new_password: passwordForm.new_password,
      });
      
      // 清空密码表单
      passwordForm.old_password = '';
      passwordForm.new_password = '';
      passwordForm.confirm_password = '';
      
      showMessage('密码修改成功');
    } else {
      showMessage('个人信息保存成功');
    }
  } catch (error: any) {
    const status = error.status || 0;
    if (status === 401 || status === 403) {
      localStorage.removeItem('token');
      router.push('/auth');
      showMessage('登录已过期，请重新登录', 'error');
      return;
    }
    
    // 提取错误信息
    let errorMsg = '操作失败';
    if (error) {
      if (typeof error === 'string') {
        errorMsg = error;
      } else if (error.message) {
        errorMsg = error.message;
      } else if (error.detail) {
        errorMsg = typeof error.detail === 'string' ? error.detail : JSON.stringify(error.detail);
      } else if (error.error) {
        errorMsg = typeof error.error === 'string' ? error.error : JSON.stringify(error.error);
      }
    }
    
    console.error('[ProfilePage] 修改密码失败:', error);
    showMessage(errorMsg, 'error');
  } finally {
    saving.value = false;
  }
}

async function loadFiles(reset = false) {
  if (reset) {
    filesPage.value = 0;
    files.value = [];
  }
  
  loadingFiles.value = true;
  try {
    const records = await getUserFiles(filesPage.value * 20, 20);
    files.value = reset ? records : [...files.value, ...records];
    hasMoreFiles.value = records.length === 20;
  } catch (error: any) {
    const status = error.status || 0;
    if (status === 401 || status === 403) {
      localStorage.removeItem('token');
      router.push('/auth');
      showMessage('登录已过期，请重新登录', 'error');
      return;
    }
    showMessage('获取文件列表失败', 'error');
  } finally {
    loadingFiles.value = false;
  }
}

async function loadMoreFiles() {
  loadingMoreFiles.value = true;
  filesPage.value++;
  try {
    const records = await getUserFiles(filesPage.value * 20, 20);
    files.value.push(...records);
    hasMoreFiles.value = records.length === 20;
  } catch (error) {
    showMessage('加载更多失败', 'error');
  } finally {
    loadingMoreFiles.value = false;
  }
}

function openDeleteConfirm(taskKey: string) {
  console.log('[Delete] 打开删除确认模态框，taskKey:', taskKey);
  fileToDelete.value = taskKey;
  showDeleteConfirm.value = true;
}

function cancelDelete() {
  console.log('[Delete] 用户取消删除');
  showDeleteConfirm.value = false;
  fileToDelete.value = '';
}

async function confirmDelete() {
  if (!fileToDelete.value) {
    return;
  }
  
  const taskKey = fileToDelete.value;
  console.log('[Delete] 用户确认删除，开始执行，taskKey:', taskKey);
  
  showDeleteConfirm.value = false;
  fileToDelete.value = '';
  
  deletingFiles.value.add(taskKey);
  try {
    // 先调用后端 API 删除
    await deleteUserFile(taskKey);
    
    // 成功后再从前端移除
    files.value = files.value.filter(f => f.task_key !== taskKey);
    console.log('[Delete] 删除成功，剩余文件数量:', files.value.length);
    showMessage('文件删除成功');
  } catch (error: any) {
    console.error('[Delete] 删除失败:', error);
    showMessage(error.message || '删除失败', 'error');
  } finally {
    deletingFiles.value.delete(taskKey);
  }
}

async function viewFileDetail(taskKey: string) {
  currentFileTaskKey.value = taskKey;
  showFileDetailModal.value = true;
  loadingFileDetail.value = true;
  fileDetail.value = null;
  
  try {
    const token = localStorage.getItem('token');
    console.log('[ProfilePage] 请求文件详情，taskKey:', taskKey, 'token:', token ? '存在' : '不存在');
    
    const response = await fetch(`${API_BASE}/history/${taskKey}/detail`, {
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
      },
    });
    
    console.log('[ProfilePage] 响应状态:', response.status, response.ok);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('[ProfilePage] 响应错误:', errorText);
      throw new Error(`获取文件详情失败：${response.status}`);
    }
    
    fileDetail.value = await response.json();
    console.log('[ProfilePage] 获取详情成功:', fileDetail.value);
  } catch (error: any) {
    console.error('[ProfilePage] 获取详情失败:', error);
    showMessage(error.message || '获取详情失败', 'error');
  } finally {
    loadingFileDetail.value = false;
  }
}

function closeFileDetailModal() {
  showFileDetailModal.value = false;
  fileDetail.value = null;
  currentFileTaskKey.value = '';
}

async function downloadResult() {
  if (!currentFileTaskKey.value) return;
  
  try {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_BASE}/doc/result/${currentFileTaskKey.value}`, {
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
      },
    });
    
    if (!response.ok) {
      throw new Error('下载失败');
    }
    
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `repaired_${currentFileTaskKey.value}.png`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    showMessage('下载成功');
  } catch (error: any) {
    showMessage(error.message || '下载失败', 'error');
  }
}

onMounted(() => {
  loadProfile();
  // 如果是文件中心视图，加载文件
  if (currentView.value === 'files') {
    loadFiles(true);
  }
});
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: var(--background);
  background-image: 
    radial-gradient(circle at 20% 80%, rgba(0, 255, 136, 0.03) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(0, 204, 136, 0.03) 0%, transparent 50%),
    linear-gradient(180deg, #0a0a0a 0%, #0f1419 100%);
  padding: 32px;
}

.profile-page .content-section {
  max-width: 900px;
  margin: 0 auto;
}

.content-section h2 {
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
  margin: 0 0 20px 0;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(0, 255, 136, 0.1);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.section-subtitle {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(0, 255, 136, 0.1);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-card {
  max-width: 600px;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(0, 255, 136, 0.15);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-input {
  width: 100%;
  padding: 14px 18px;
  border: 1px solid rgba(0, 255, 136, 0.15);
  border-radius: 8px;
  font-size: 15px;
  transition: all 0.3s ease;
  background: rgba(15, 23, 42, 0.95);
  color: var(--text);
  font-family: inherit;
}

.form-input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(0, 255, 136, 0.1);
}

.form-input.disabled {
  background: rgba(15, 23, 42, 0.6);
  color: var(--text-secondary);
  cursor: not-allowed;
  border-color: rgba(0, 255, 136, 0.1);
}

.hint {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-actions {
  margin-top: 24px;
  display: flex;
  gap: 12px;
}

.btn {
  padding: 12px 24px;
  border: 1px solid rgba(0, 255, 136, 0.15);
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-family: inherit;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-primary {
  background: var(--primary);
  color: #0a0a0a;
  border-color: var(--primary);
  box-shadow: 0 4px 16px rgba(0, 255, 136, 0.2);
}

.btn-primary:hover:not(:disabled) {
  background: var(--secondary);
  border-color: var(--secondary);
  box-shadow: 0 6px 24px rgba(0, 255, 136, 0.3);
  transform: translateY(-2px);
}

.btn-secondary {
  background: rgba(15, 23, 42, 0.95);
  color: var(--text);
  border-color: rgba(0, 255, 136, 0.2);
}

.btn-secondary:hover:not(:disabled) {
  border-color: var(--primary);
  background: rgba(0, 255, 136, 0.05);
  box-shadow: 0 4px 16px rgba(0, 255, 136, 0.15);
  transform: translateY(-2px);
}

.btn-danger {
  background: rgba(255, 68, 68, 0.1);
  color: #ff4444;
  border-color: rgba(255, 68, 68, 0.3);
}

.btn-danger:hover:not(:disabled) {
  background: rgba(255, 68, 68, 0.2);
  border-color: #ff4444;
  box-shadow: 0 4px 16px rgba(255, 68, 68, 0.2);
  transform: translateY(-2px);
}

.btn-small {
  padding: 8px 16px;
  font-size: 13px;
}

.stats-bar {
  background: rgba(0, 255, 136, 0.05);
  padding: 16px 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  border: 1px solid rgba(0, 255, 136, 0.15);
}

.stats-item {
  font-size: 14px;
  color: var(--primary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stats-item strong {
  font-size: 18px;
  font-weight: 800;
  text-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
}

.loading {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.loading-spinner {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px;
}

.loading-spinner::after {
  content: '';
  display: inline-block;
  width: 24px;
  height: 24px;
  border: 3px solid rgba(0, 255, 136, 0.3);
  border-radius: 50%;
  border-top-color: var(--primary);
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
  background: rgba(15, 23, 42, 0.6);
  border: 1px dashed rgba(0, 255, 136, 0.2);
  border-radius: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.empty-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 16px;
  color: var(--primary);
}

.history-list,
.file-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item,
.file-item {
  background: rgba(15, 23, 42, 0.8);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid rgba(0, 255, 136, 0.15);
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
}

.history-item:hover,
.file-item:hover {
  border-color: var(--primary);
  box-shadow: 0 4px 16px rgba(0, 255, 136, 0.15);
  transform: translateY(-2px);
}

.history-header,
.file-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 12px;
}

.file-info {
  gap: 16px;
}

.filename {
  font-weight: 600;
  color: var(--text);
  word-break: break-all;
  flex: 1;
  min-width: 200px;
}

.status-badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border: 1px solid;
}

.status-badge.done {
  background: rgba(0, 255, 136, 0.1);
  color: var(--primary);
  border-color: rgba(0, 255, 136, 0.3);
}

.status-badge.failed {
  background: rgba(255, 68, 68, 0.1);
  color: #ff4444;
  border-color: rgba(255, 68, 68, 0.3);
}

.status-badge.processing {
  background: rgba(255, 215, 0, 0.1);
  color: #ffd700;
  border-color: rgba(255, 215, 0, 0.3);
}

.history-meta,
.file-meta {
  font-size: 13px;
  color: var(--text-secondary);
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.history-text {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(0, 255, 136, 0.1);
}

.text-preview {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
  background: rgba(15, 23, 42, 0.95);
  padding: 12px;
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 136, 0.1);
}

.file-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 200px;
}

.has-result {
  color: var(--primary);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-size: 12px;
}

.file-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.load-more {
  text-align: center;
  padding: 20px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px dashed rgba(0, 255, 136, 0.2);
  border-radius: 12px;
  margin-top: 16px;
}

.message-toast {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 16px 24px;
  border-radius: 8px;
  color: #0a0a0a;
  font-weight: 600;
  z-index: 1000;
  animation: slideIn 0.3s ease;
  border: 1px solid;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}

.message-toast.success {
  background: var(--primary);
  border-color: var(--primary);
  box-shadow: 0 4px 16px rgba(0, 255, 136, 0.3);
}

.message-toast.error {
  background: #ff4444;
  border-color: #ff4444;
  box-shadow: 0 4px 16px rgba(255, 68, 68, 0.3);
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
  animation: fadeIn 0.3s ease;
  backdrop-filter: blur(10px);
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal-content {
  background: rgba(17, 24, 39, 0.95);
  border-radius: 16px;
  width: 100%;
  max-width: 700px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  animation: slideUp 0.3s ease;
  border: 1px solid rgba(0, 255, 136, 0.15);
  box-shadow: 0 0 0 1px rgba(0, 255, 136, 0.1), 
              0 20px 60px rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(10px);
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(0, 255, 136, 0.1);
  background: rgba(15, 23, 42, 0.95);
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.modal-close {
  background: rgba(15, 23, 42, 0.95);
  border: 1px solid rgba(0, 255, 136, 0.15);
  font-size: 28px;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.modal-close:hover {
  background: rgba(0, 255, 136, 0.1);
  border-color: var(--primary);
  color: var(--primary);
  box-shadow: 0 2px 8px rgba(0, 255, 136, 0.2);
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
  background: rgba(17, 24, 39, 0.95);
}

.confirmation-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.confirmation-icon {
  font-size: 24px;
  flex-shrink: 0;
  color: #ffd700;
}

.modal-footer {
  display: flex;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid rgba(0, 255, 136, 0.1);
  background: rgba(15, 23, 42, 0.95);
  flex-shrink: 0;
  justify-content: flex-end;
}

.file-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-row {
  display: flex;
  gap: 16px;
  padding: 16px 0;
  border-bottom: 1px solid rgba(0, 255, 136, 0.1);
  flex-wrap: wrap;
}

.detail-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  min-width: 120px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  flex-shrink: 0;
}

.detail-value {
  font-size: 14px;
  color: var(--text-secondary);
  flex: 1;
  min-width: 200px;
}

.detail-value.done {
  color: var(--primary);
  font-weight: 600;
}

.detail-value.failed {
  color: #ff4444;
  font-weight: 600;
}

.detail-section {
  margin-top: 8px;
  padding: 20px;
  background: rgba(15, 23, 42, 0.8);
  border-radius: 12px;
  border: 1px solid rgba(0, 255, 136, 0.15);
}

.detail-section h4 {
  margin: 0 0 16px 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.text-content {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
  white-space: pre-wrap;
  max-height: 300px;
  overflow-y: auto;
  background: rgba(15, 23, 42, 0.95);
  padding: 16px;
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 136, 0.1);
}

.image-container {
  text-align: center;
  background: rgba(15, 23, 42, 0.95);
  padding: 20px;
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 136, 0.15);
}

.result-image {
  max-width: 100%;
  max-height: 400px;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3),
              0 0 20px rgba(0, 255, 136, 0.1);
  border: 1px solid rgba(0, 255, 136, 0.15);
}

.detail-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(0, 255, 136, 0.1);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .profile-page {
    padding: 16px;
  }
  
  .profile-page .content-section {
    max-width: 100%;
  }
  
  .info-card {
    max-width: 100%;
  }
  
  .form-actions {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
  }
  
  .file-info {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .file-actions {
    width: 100%;
    justify-content: space-between;
  }
  
  .modal-content {
    margin: 12px;
    max-width: calc(100% - 24px);
  }
  
  .modal-footer {
    flex-direction: column;
  }
  
  .detail-row {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .detail-label {
    min-width: auto;
  }
  
  .detail-value {
    min-width: auto;
    width: 100%;
  }
}
</style>
