<template>
  <div class="page">
    <div class="card" style="width: 100%; max-width: 1200px">
      <div>
        <h1 class="title" style="margin-bottom: 6px">批量处理与任务管理</h1>
        <p class="subtitle" style="margin-bottom: 0">
          批量上传并处理多张图片，实时监控处理进度，统一管理处理结果
        </p>
      </div>

      <div style="height: 16px"></div>

      <!-- 批量上传区域 -->
      <div class="upload-section">
        <div class="field">
          <label class="label">批量上传图片</label>
          <div
            class="dropzone"
            :class="{ 'dropzone-active': isDragOver }"
            @dragover.prevent="isDragOver = true"
            @dragleave.prevent="isDragOver = false"
            @drop.prevent="handleDrop"
          >
            <input
              ref="fileInput"
              type="file"
              multiple
              accept="image/*"
              style="display: none"
              @change="handleFileSelect"
            />
            <!-- 支持文件夹的隐藏输入框 -->
            <input
              ref="folderInput"
              type="file"
              multiple
              webkitdirectory
              directory
              style="display: none"
              @change="handleFolderSelect"
            />
            <div class="dropzone-icon">
              <div class="icon-content">UPLOAD</div>
            </div>
            <div class="dropzone-text">
              拖拽图片到此处或 <span class="dropzone-link" @click="fileInput?.click()">点击选择文件</span>
            </div>
            <div class="dropzone-hint">支持多张图片同时上传</div>
            <!-- 额外的上传选项 -->
            <div class="upload-options">
              <button class="upload-option-btn" @click.stop="folderInput?.click()" title="选择整个文件夹">
                <div class="btn-icon">FOLDER</div> 选择文件夹
              </button>
            </div>
          </div>
        </div>

        <!-- 已选择的文件列表 -->
        <div v-if="selectedFiles.length > 0" class="file-list">
          <div class="file-list-header">
            <span class="header-file">文件</span>
            <span class="header-weight">退化类型</span>
            <span class="header-action">操作</span>
          </div>
          <div v-for="(file, index) in selectedFiles" :key="index" class="file-item">
            <div class="file-info">
              <span class="file-name">{{ file.name }}</span>
              <span class="file-size">{{ formatFileSize(file.size) }}</span>
            </div>
            <div class="file-weight">
              <select 
                :value="fileDegradationType.get(file)"
                @change="updateDegradationType(file, ($event.target as HTMLSelectElement).value)"
                class="weight-select"
              >
                <option value="classical">Classical (经典)</option>
                <option value="realworld">RealWorld (真实)</option>
                <option value="compressed">Compressed (压缩)</option>
              </select>
            </div>
            <div class="file-action">
              <button class="btn ghost" @click="removeFile(index)">✕</button>
            </div>
          </div>
        </div>

        <div v-if="formError" class="msg error">{{ formError }}</div>
        <div v-if="formOk" class="msg ok">{{ formOk }}</div>

        <div class="actions">
          <button class="btn ghost" type="button" @click="resetPage">重置</button>
          <button
            class="btn primary"
            type="button"
            :disabled="processing || selectedFiles.length === 0"
            @click="startBatchProcessing"
          >
            {{ processing ? '处理中...' : `开始处理 (${selectedFiles.length}张)` }}
          </button>
        </div>
      </div>

      <!-- 处理进度与状态 -->
      <div v-if="tasks.length > 0" class="tasks-section">
        <div class="tasks-header">
          <h2>处理任务</h2>
          <div class="tasks-stats">
            <span class="stat-item pending">待处理: {{ stats.pending }}</span>
            <span class="stat-item processing">处理中: {{ stats.processing }}</span>
            <span class="stat-item done">已完成: {{ stats.done }}</span>
            <span class="stat-item failed">失败: {{ stats.failed }}</span>
          </div>
        </div>

        <div class="tasks-list">
          <div v-for="task in tasks" :key="task.id" class="task-item" :class="task.status">
            <div class="task-header">
              <div class="task-info">
                <span class="task-filename">{{ task.filename }}</span>
                <span class="task-status-badge" :class="task.status">
                  {{ getStatusText(task.status) }}
                </span>
              </div>
              <div class="task-actions">
                <button
                  v-if="task.status === 'done'"
                  class="btn ghost"
                  style="padding: 4px 8px; font-size: 12px"
                  @click="viewTaskResult(task)"
                >
                  查看
                </button>
                <button
                  v-if="task.status === 'done'"
                  class="btn ghost"
                  style="padding: 4px 8px; font-size: 12px"
                  @click="downloadTaskResult(task)"
                >
                  下载
                </button>
                <button
                  v-if="task.status === 'failed'"
                  class="btn ghost"
                  style="padding: 4px 8px; font-size: 12px"
                  @click="retryTask(task)"
                >
                  重试
                </button>
              </div>
            </div>
            <div v-if="task.status === 'processing'" class="task-progress">
              <div class="progress-bar small">
                <div class="progress-fill" :style="{ width: task.progress + '%' }"></div>
              </div>
              <span class="progress-text-small">{{ task.progressText || '处理中...' }}</span>
            </div>
            <div v-if="task.status === 'failed'" class="task-error">
              {{ task.error }}
            </div>
          </div>
        </div>

        <div v-if="stats.done > 0" class="batch-actions">
          <button class="btn ghost" @click="downloadAllResults">下载全部结果</button>
          <button class="btn ghost" @click="exportBatchReport">导出处理报告</button>
        </div>
      </div>

      <!-- 任务结果详情弹窗 -->
      <div v-if="showResultModal" class="modal-overlay" @click="closeResultModal">
        <div class="result-container" @click.stop>
          <button class="modal-close-btn" @click="closeResultModal">×</button>
          <div class="result-image-wrapper">
            <img 
              v-if="selectedTask?.imageBase64" 
              :src="`data:image/png;base64,${selectedTask.imageBase64}`" 
              alt="修复结果" 
              class="result-image"
            />
          </div>
          <div class="result-info">
            <h3>{{ selectedTask?.filename }}</h3>
            <p>修复结果预览</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { API_BASE } from "../api/base";

const router = useRouter();

type TaskStatus = 'pending' | 'processing' | 'done' | 'failed';

interface BatchTask {
  id: string;
  file: File;
  filename: string;
  status: TaskStatus;
  progress: number;
  progressText?: string;
  ocrText?: string;
  filledText?: string;
  imageBase64?: string;
  taskId?: string;
  error?: string;
}

const token = ref<string | null>(localStorage.getItem("token"));
const fileInput = ref<HTMLInputElement | null>(null);
const folderInput = ref<HTMLInputElement | null>(null);
const isDragOver = ref(false);
const selectedFiles = ref<File[]>([]);
// 每个文件的退化类型设置 (classical, realworld, compressed)
const fileDegradationType = ref<Map<File, string>>(new Map());

const processing = ref(false);
const formError = ref("");
const formOk = ref("");
const tasks = ref<BatchTask[]>([]);
const showResultModal = ref(false);
const selectedTask = ref<BatchTask | null>(null);

const stats = computed(() => {
  const result = { pending: 0, processing: 0, done: 0, failed: 0 };
  tasks.value.forEach(task => {
    result[task.status]++;
  });
  return result;
});

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function getStatusText(status: TaskStatus): string {
  const map: Record<TaskStatus, string> = {
    pending: '待处理',
    processing: '处理中',
    done: '已完成',
    failed: '失败'
  };
  return map[status];
}

function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement;
  if (input.files) {
    addFiles(Array.from(input.files));
  }
}

function handleDrop(e: DragEvent) {
  isDragOver.value = false;
  if (e.dataTransfer?.files) {
    addFiles(Array.from(e.dataTransfer.files));
  }
}

function addFiles(files: File[]) {
  const imageFiles = files.filter(file => file.type.startsWith('image/'));
  selectedFiles.value = [...selectedFiles.value, ...imageFiles];
  // 初始化退化类型设置为 realworld
  imageFiles.forEach(file => {
    fileDegradationType.value.set(file, "realworld");
  });
  formError.value = "";
}

// 更新文件的退化类型
function updateDegradationType(file: File, degradationType: string) {
  fileDegradationType.value.set(file, degradationType);
}

// 处理文件夹选择
async function handleFolderSelect(e: Event) {
  const input = e.target as HTMLInputElement;
  const files = Array.from(input.files || []);
  if (files.length === 0) return;
  
  try {
    formError.value = "";
    formOk.value = `已选择文件夹，共 ${files.length} 个文件`;
    // 只保留图片文件
    const imageFiles = files.filter(f => f.type.startsWith('image/'));
    selectedFiles.value = [...selectedFiles.value, ...imageFiles];
    // 为每个新文件设置默认退化类型
    imageFiles.forEach(file => {
      if (!fileDegradationType.value.has(file)) {
        fileDegradationType.value.set(file, 'realworld');
      }
    });
  } catch (error) {
    formError.value = "文件夹选择失败";
  } finally {
    // 清空 input
    input.value = "";
  }
}

function removeFile(index: number) {
  selectedFiles.value.splice(index, 1);
}

function clearSelectedFiles() {
  selectedFiles.value = [];
  if (fileInput.value) {
    fileInput.value.value = "";
  }
}

function resetPage() {
  selectedFiles.value = [];
  tasks.value = [];
  processing.value = false;
  formError.value = "";
  formOk.value = "";
  if (fileInput.value) {
    fileInput.value.value = "";
  }
}

async function startBatchProcessing() {
  if (selectedFiles.value.length === 0) {
    formError.value = "请先选择要处理的文件";
    return;
  }

  processing.value = true;
  formError.value = "";
  formOk.value = "";

  // 清空之前的任务列表
  tasks.value = [];

  // 初始化新的任务列表
  tasks.value = selectedFiles.value.map(file => ({
    id: Math.random().toString(36).substr(2, 9),
    file,
    filename: file.name,
    status: 'pending',
    progress: 0
  }));

  // 逐个处理文件
  for (const task of tasks.value) {
    await processTask(task);
  }

  processing.value = false;
  formOk.value = `批量处理完成！成功：${stats.value.done}, 失败：${stats.value.failed}`;
}

async function processTask(task: BatchTask) {
  task.status = 'processing';
  task.progress = 0;
  task.progressText = '准备处理...';

  try {
    const fd = new FormData();
    fd.append("file", task.file);
    fd.append("doc_type", "document");
    // 使用每个文件自己的退化类型设置
    const degradationType = fileDegradationType.value.get(task.file) ?? "realworld";
    fd.append("degradation_type", degradationType);

    // 更新进度
    task.progress = 20;
    task.progressText = '上传文件...';

    const res = await fetch(`${API_BASE}/doc/repair`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token.value}`,
      },
      body: fd,
    });

    task.progress = 60;
    task.progressText = '处理中...';

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data?.detail || "处理失败");
    }

    task.progress = 100;
    task.status = 'done';
    task.progressText = '完成';
    task.taskId = data.task_id;
    task.ocrText = data.ocr_text || "";
    task.filledText = data.filled_text || "";
    task.imageBase64 = data.repaired_image_base64?.replace(/\s/g, "");

  } catch (e) {
    task.status = 'failed';
    task.error = e instanceof Error ? e.message : "处理失败";
  }
}

async function retryTask(task: BatchTask) {
  await processTask(task);
}

function viewTaskResult(task: BatchTask) {
  selectedTask.value = task;
  showResultModal.value = true;
}

function closeResultModal() {
  showResultModal.value = false;
  selectedTask.value = null;
}

// 将 File 转换为 base64
function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const base64 = reader.result as string;
      // 去掉 data:image/xxx;base64, 前缀
      resolve(base64.split(',')[1]);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

async function downloadTaskResult(task: BatchTask) {
  if (!task.imageBase64) return;

  try {
    const byteCharacters = atob(task.imageBase64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: 'image/png' });

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `repaired_${task.filename}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  } catch (e) {
    formError.value = "下载失败";
  }
}

function downloadAllResults() {
  const doneTasks = tasks.value.filter(t => t.status === 'done');
  doneTasks.forEach(downloadTaskResult);
}

function exportBatchReport() {
  let report = `批量处理报告\n`;
  report += `生成时间: ${new Date().toLocaleString()}\n`;
  report += `总任务数: ${tasks.value.length}\n`;
  report += `已完成: ${stats.value.done}\n`;
  report += `失败: ${stats.value.failed}\n\n`;

  tasks.value.forEach((task, index) => {
    report += `\n--- 任务 ${index + 1}: ${task.filename} ---\n`;
    report += `状态: ${getStatusText(task.status)}\n`;
    if (task.status === 'done') {
      report += `OCR文本:\n${task.ocrText}\n`;
      report += `补全文本:\n${task.filledText}\n`;
    } else if (task.status === 'failed') {
      report += `错误: ${task.error}\n`;
    }
  });

  const blob = new Blob([report], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `batch_report_${Date.now()}.txt`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
</script>

<style scoped>
.upload-section {
  margin-bottom: 32px;
}

.dropzone {
  border: 2px dashed var(--border);
  border-radius: 12px;
  padding: 60px 20px;
  text-align: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  background: rgba(17, 24, 39, 0.5);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 255, 136, 0.12);
  position: relative;
  overflow: hidden;
}

.dropzone::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(0, 255, 136, 0.06), transparent);
  transition: left 0.6s;
}

.dropzone:hover::before {
  left: 100%;
}

.dropzone-active {
  border-color: var(--primary);
  background: rgba(0, 255, 136, 0.04);
  box-shadow: 0 0 30px rgba(0, 255, 136, 0.1);
}

.dropzone-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 255, 136, 0.06);
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 136, 0.12);
  margin: 0 auto 20px;
  box-shadow: 0 4px 12px rgba(0, 255, 136, 0.06);
}

.icon-content {
  font-size: 12px;
  font-weight: 800;
  color: var(--primary);
  text-transform: uppercase;
  letter-spacing: 1px;
  text-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
}

.dropzone-text {
  font-size: 18px;
  margin-bottom: 12px;
  color: var(--text);
  font-weight: 500;
  letter-spacing: 0.5px;
}

.dropzone-link {
  color: var(--primary);
  text-decoration: none;
  border-bottom: 2px solid var(--primary);
  padding-bottom: 2px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 600;
}

.dropzone-link:hover {
  color: var(--primary);
  border-bottom-color: var(--secondary);
  text-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
}

.dropzone-hint {
  font-size: 14px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 上传选项按钮 */
.upload-options {
  display: flex;
  gap: 16px;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid rgba(0, 255, 136, 0.1);
  justify-content: center;
  position: relative;
}

.upload-options::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--primary), transparent);
  opacity: 0.3;
}

.upload-option-btn {
  padding: 12px 20px;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(0, 255, 136, 0.12);
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.upload-option-btn:hover {
  border-color: var(--primary);
  background: rgba(0, 255, 136, 0.04);
  color: var(--primary);
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 255, 136, 0.1);
}

.upload-option-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(0, 255, 136, 0.06);
}

.btn-icon {
  font-size: 10px;
  font-weight: 800;
  color: var(--primary);
  text-transform: uppercase;
  letter-spacing: 1px;
  background: rgba(0, 255, 136, 0.06);
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid rgba(0, 255, 136, 0.12);
}

.file-list {
  margin-top: 24px;
  border: 1px solid rgba(0, 255, 136, 0.12);
  border-radius: 8px;
  overflow: hidden;
  background: rgba(17, 24, 39, 0.5);
  backdrop-filter: blur(10px);
}

.file-list-header {
  display: grid;
  grid-template-columns: 1fr 180px 80px;
  gap: 16px;
  padding: 16px 20px;
  background: rgba(15, 23, 42, 0.8);
  font-weight: 600;
  font-size: 14px;
  color: var(--text);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid rgba(0, 255, 136, 0.1);
}

.header-file {
  text-align: left;
}

.header-weight {
  text-align: center;
}

.header-action {
  text-align: center;
}

.file-list-content {
  max-height: 400px;
  overflow-y: auto;
}

.file-item {
  display: grid;
  grid-template-columns: 1fr 180px 80px;
  gap: 16px;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(0, 255, 136, 0.05);
  align-items: center;
  transition: all 0.3s ease;
}

.file-item:hover {
  background: rgba(0, 255, 136, 0.03);
}

.file-item:last-child {
  border-bottom: none;
}

.file-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.file-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--text);
  line-height: 1.4;
}

.file-size {
  font-size: 12px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.file-weight {
  display: flex;
  align-items: center;
  justify-content: center;
}

.weight-select {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 13px;
  color: var(--text);
  background: rgba(15, 23, 42, 0.8);
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: inherit;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.weight-select:hover {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(0, 255, 136, 0.1);
}

.weight-select:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(0, 255, 136, 0.1);
}

.file-action {
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-action .btn {
  padding: 8px 12px;
  font-size: 12px;
}

.file-actions {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid rgba(0, 255, 136, 0.1);
}

.tasks-section {
  margin-top: 40px;
  padding-top: 32px;
  border-top: 1px solid rgba(0, 255, 136, 0.1);
  position: relative;
}

.tasks-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--primary), transparent);
  opacity: 0.3;
}

.tasks-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.tasks-header h2 {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
  color: var(--text);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-shadow: 0 0 15px rgba(0, 255, 136, 0.1);
}

.tasks-stats {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.stat-item {
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border: 1px solid rgba(0, 255, 136, 0.2);
  transition: all 0.3s ease;
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 255, 136, 0.15);
}

.stat-item.pending {
  background: rgba(255, 170, 0, 0.1);
  color: var(--warning);
  border-color: rgba(255, 170, 0, 0.3);
}

.stat-item.processing {
  background: rgba(0, 255, 136, 0.1);
  color: var(--primary);
  border-color: rgba(0, 255, 136, 0.3);
}

.stat-item.done {
  background: rgba(0, 255, 136, 0.1);
  color: var(--success);
  border-color: rgba(0, 255, 136, 0.3);
}

.stat-item.failed {
  background: rgba(255, 68, 68, 0.1);
  color: var(--error);
  border-color: rgba(255, 68, 68, 0.3);
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.task-item {
  border: 1px solid rgba(0, 255, 136, 0.15);
  border-radius: 8px;
  padding: 20px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: rgba(17, 24, 39, 0.5);
  backdrop-filter: blur(10px);
}

.task-item:hover {
  box-shadow: 0 4px 16px rgba(0, 255, 136, 0.1);
  transform: translateY(-2px);
}

.task-item.processing {
  border-color: var(--primary);
  background: rgba(0, 255, 136, 0.05);
  box-shadow: 0 0 20px rgba(0, 255, 136, 0.1);
}

.task-item.done {
  border-color: var(--success);
  background: rgba(0, 255, 136, 0.05);
  box-shadow: 0 0 20px rgba(0, 255, 136, 0.1);
}

.task-item.failed {
  border-color: var(--error);
  background: rgba(255, 68, 68, 0.05);
  box-shadow: 0 0 20px rgba(255, 68, 68, 0.1);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 12px;
}

.task-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.task-filename {
  font-weight: 600;
  font-size: 14px;
  color: var(--text);
  line-height: 1.4;
  flex: 1;
  min-width: 200px;
}

.task-status-badge {
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border: 1px solid;
}

.task-status-badge.pending {
  background: rgba(255, 170, 0, 0.1);
  color: var(--warning);
  border-color: rgba(255, 170, 0, 0.3);
}

.task-status-badge.processing {
  background: rgba(0, 255, 136, 0.1);
  color: var(--primary);
  border-color: rgba(0, 255, 136, 0.3);
}

.task-status-badge.done {
  background: rgba(0, 255, 136, 0.1);
  color: var(--success);
  border-color: rgba(0, 255, 136, 0.3);
}

.task-status-badge.failed {
  background: rgba(255, 68, 68, 0.1);
  color: var(--error);
  border-color: rgba(255, 68, 68, 0.3);
}

.task-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.task-actions .btn {
  padding: 6px 12px;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.task-progress {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(0, 255, 136, 0.05);
}

.progress-bar.small {
  flex: 1;
  height: 6px;
  background: rgba(31, 41, 55, 0.8);
  border-radius: 3px;
  overflow: hidden;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
}

.progress-bar.small .progress-fill {
  background: linear-gradient(90deg, var(--primary), var(--secondary));
  box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
}

.progress-text-small {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.task-error {
  font-size: 13px;
  color: var(--error);
  padding: 12px;
  background: rgba(255, 68, 68, 0.1);
  border-radius: 6px;
  margin-top: 12px;
  border: 1px solid rgba(255, 68, 68, 0.2);
  line-height: 1.4;
}

.batch-actions {
  display: flex;
  gap: 16px;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid rgba(0, 255, 136, 0.1);
  justify-content: flex-end;
  flex-wrap: wrap;
}

.batch-actions .btn {
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  cursor: pointer;
  backdrop-filter: blur(5px);
  animation: fadeIn 0.3s ease;
  transform: none !important;
  will-change: opacity;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.result-container {
  background: linear-gradient(135deg, rgba(17, 24, 39, 0.98), rgba(31, 41, 55, 0.98));
  border: 1px solid rgba(0, 255, 136, 0.3);
  border-radius: 16px;
  padding: 32px;
  max-width: 800px;
  max-height: 70vh;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0, 255, 136, 0.15);
  backdrop-filter: blur(15px);
  display: flex;
  flex-direction: column;
  position: relative;
  margin: auto;
  animation: slideIn 0.3s ease;
  cursor: default;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.result-image-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 20px 0;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  padding: 20px;
  overflow: hidden;
  min-height: 400px;
  max-height: 60vh;
}

.result-image {
  display: block;
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  object-fit: contain;
  border-radius: 4px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
}

.result-info {
  text-align: center;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(0, 255, 136, 0.1);
}

.result-info h3 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
}

.result-info p {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.modal-close-btn {
  position: absolute;
  top: 30px;
  right: 30px;
  width: 48px;
  height: 48px;
  border-radius: 8px;
  background: rgba(17, 24, 39, 0.9);
  border: 1px solid rgba(0, 255, 136, 0.2);
  color: var(--primary);
  font-size: 20px;
  cursor: pointer;
  z-index: 1001;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.modal-close-btn:hover {
  background: rgba(0, 255, 136, 0.1);
  border-color: var(--primary);
  transform: scale(1.1);
  box-shadow: 0 6px 20px rgba(0, 255, 136, 0.2);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .file-list-header {
    grid-template-columns: 1fr;
    gap: 8px;
    text-align: left;
  }
  
  .file-item {
    grid-template-columns: 1fr;
    gap: 12px;
    text-align: left;
  }
  
  .file-weight {
    justify-content: flex-start;
  }
  
  .file-action {
    justify-content: flex-start;
  }
  
  .tasks-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .tasks-stats {
    width: 100%;
    justify-content: space-between;
  }
  
  .task-header {
    flex-direction: column;
    align-items: flex-start;
    text-align: left;
  }
  
  .task-actions {
    width: 100%;
    justify-content: space-between;
  }
  
  .batch-actions {
    flex-direction: column;
  }
  
  .batch-actions .btn {
    width: 100%;
  }
  
  .result-image-full {
    max-width: calc(100vw - 40px);
    max-height: calc(100vh - 40px);
  }
}
</style>
