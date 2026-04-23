<template>
  <div class="page">
    <div class="card">
      <div class="card-header">
        <h1 class="title">OCR 识别与后处理</h1>
        <p class="subtitle">
          上传图片，识别文字并自动纠错
        </p>
      </div>

      <!-- 裁剪模式 -->
      <div v-if="showCropper && originalPreviewUrl" class="cropper-modal-wrapper">
        <ImageCropper
          :imageSrc="originalPreviewUrl"
          :showHeader="true"
          @crop="handleCrop"
          @cancel="handleCropCancel"
        />
      </div>

      <form @submit.prevent="onOcr" v-else>
        <div class="field">
          <label class="label">上传图片</label>
          <div 
            class="file-upload-area" 
            @click="triggerFileInput"
            @dragover.prevent="onDragOver"
            @dragleave.prevent="onDragLeave"
            @drop.prevent="onDrop"
            :class="{ 'dragover': isDragging }"
          >
            <input
              ref="fileInput"
              class="file-input"
              type="file"
              accept="image/*"
              @change="onFileChange"
              style="display: none;"
            />
            <div class="upload-content">
              <div v-if="!file">
                <div class="upload-icon">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 15V3M12 3L8 7M12 3L16 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M21 15H3M21 15C21 18.3137 18.3137 21 15 21H9C5.68629 21 3 18.3137 3 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
                <div class="upload-text">
                  <div class="upload-title">{{ isDragging ? '释放文件到此处' : '点击或拖拽文件到此处' }}</div>
                  <div class="upload-hint">支持 JPG、PNG、BMP 等常见图片格式</div>
                </div>
              </div>
              <div v-else class="file-preview">
                <img :src="originalPreviewUrl" alt="预览" class="preview-image" />
                <div class="file-info">
                  <div class="file-name">{{ file.name }}</div>
                  <div class="file-size">{{ formatFileSize(file.size) }}</div>
                </div>
                <div class="file-actions">
                  <button type="button" class="crop-btn" @click.stop="showCropModal">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M6 6V16C6 17.1046 6.89543 18 8 18H18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M18 18V8C18 6.89543 17.1046 6 16 6H6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M10 6L10 3M10 3L13 6M10 3L7 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M14 18L14 21M14 21L17 18M14 21L11 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    裁剪图片
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="formError" class="msg error">{{ formError }}</div>
        <div v-if="formOk" class="msg ok">{{ formOk }}</div>

        <div v-if="loading" class="progress-container">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progress + '%' }"></div>
          </div>
          <div class="progress-text">{{ progressText }}</div>
        </div>

        <div class="actions">
          <button class="btn ghost" type="button" @click="resetPage">清空</button>
          <button class="btn primary" type="submit" :disabled="loading || !file">
            {{ loading ? "识别中..." : "开始识别" }}
          </button>
        </div>
        
        <!-- 拼写纠错选项 -->
        <div class="spell-correction-option">
          <label class="spell-correction-label">
            <div class="checkbox-wrapper">
              <input type="checkbox" v-model="enableSpellCorrection" class="checkbox" />
              <span class="checkbox-custom"></span>
            </div>
            <div class="spell-content">
              <div class="spell-title">
                <span class="title-text">启用拼写纠错</span>
                <span class="title-badge">MacBERT 模型</span>
              </div>
              <div class="spell-description">使用 AI 模型进行智能纠错，只纠正中文错别字，保持原文其他内容不变。</div>
            </div>
          </label>
        </div>
      </form>

      <div v-if="result" class="result-section">
        <div class="result-header">
          <div class="result-title">识别结果</div>
        </div>

        <div v-if="originalPreviewUrl" class="image-preview">
          <img 
            :src="originalPreviewUrl" 
            alt="原图" 
            class="preview-image"
          />
        </div>

        <div v-if="ocrResult" class="ocr-section">
          <div class="section-title">识别文本</div>
          <textarea 
            v-model="ocrResult" 
            class="result-textarea ocr"
          ></textarea>
        </div>

        <div v-if="correctedResult" class="corrected-section">
          <div class="section-title">纠错后文本</div>
          <textarea 
            v-model="correctedResult" 
            class="result-textarea corrected"
          ></textarea>
        </div>

        <div class="stats-grid">
          <div class="info-card">
            <div class="info-label">识别时间</div>
            <div class="info-value">{{ (result.ocr_time || 0) }}s</div>
          </div>
          <div class="info-card">
            <div class="info-label">纠错时间</div>
            <div class="info-value">{{ (result.correction_time || 0) }}s</div>
          </div>
          <div class="info-card">
            <div class="info-label">字符数</div>
            <div class="info-value">{{ (result.char_count || 0) }}</div>
          </div>
        </div>

        <div class="actions">
          <button
            class="btn primary"
            type="button"
            :disabled="downloading"
            @click="downloadText"
          >
            {{ downloading ? "下载中..." : "下载识别文本" }}
          </button>
        </div>

        <div class="next-actions">
          <div class="actions-title">下一步操作</div>
          <div class="actions-container">
            <router-link to="/app/image-repair" class="btn ghost" style="text-decoration: none">
              进行图片修复
            </router-link>
            <router-link to="/app/text-completion" class="btn ghost" style="text-decoration: none">
              进行语义补全
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { API_BASE } from "../api/base";
import ImageCropper from '../components/ImageCropper.vue';

const token = ref<string | null>(localStorage.getItem("token"));

const file = ref<File | null>(null);
const loading = ref(false);
const downloading = ref(false);
const enableSpellCorrection = ref(true); // 默认启用拼写纠错

const formError = ref("");
const formOk = ref("");

const result = ref<any>(null);
const originalPreviewUrl = ref("");
const ocrResult = ref("");
const correctedResult = ref("");

const progress = ref(0);
const progressText = ref("");
const isDragging = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);

// 裁剪相关
const showCropper = ref(false);
const croppedImageBase64 = ref("");
const cropInfo = ref<{x: number, y: number, width: number, height: number} | null>(null);

function resetPage() {
  formError.value = "";
  formOk.value = "";
  result.value = null;
  originalPreviewUrl.value = "";
  ocrResult.value = "";
  correctedResult.value = "";
  file.value = null;
  progress.value = 0;
  progressText.value = "";
  isDragging.value = false;
  showCropper.value = false;
  croppedImageBase64.value = "";
  cropInfo.value = null;
}

function triggerFileInput() {
  fileInput.value?.click();
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 拖拽事件处理
function onDragOver(e: DragEvent) {
  console.log('[OcrProcessing] onDragOver triggered', e.target);
  e.preventDefault();
  e.stopPropagation();
  // 设置拖拽效果
  if (e.dataTransfer) {
    e.dataTransfer.dropEffect = 'copy';
  }
  isDragging.value = true;
  console.log('[OcrProcessing] isDragging set to true');
}

function onDragLeave(e: DragEvent) {
  console.log('[OcrProcessing] onDragLeave triggered', e.target);
  // 只有当鼠标离开整个上传区域时才重置状态
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
  const x = e.clientX;
  const y = e.clientY;
  if (x < rect.left || x >= rect.right || y < rect.top || y >= rect.bottom) {
    e.preventDefault();
    e.stopPropagation();
    isDragging.value = false;
    console.log('[OcrProcessing] isDragging set to false');
  }
}

function onDrop(e: DragEvent) {
  console.log('[OcrProcessing] onDrop triggered', e.target);
  e.preventDefault();
  e.stopPropagation();
  isDragging.value = false;
  console.log('[OcrProcessing] isDragging set to false');
  
  const files = e.dataTransfer?.files;
  console.log('[OcrProcessing] Files in drop event:', files);
  
  if (files && files.length > 0) {
    console.log('[OcrProcessing] Number of files:', files.length);
    const f = files[0];
    console.log('[OcrProcessing] File:', f);
    console.log('[OcrProcessing] File type:', f.type);
    
    if (f.type.startsWith('image/')) {
      console.log('[OcrProcessing] Image file detected');
      file.value = f;
      originalPreviewUrl.value = URL.createObjectURL(f);
      console.log('[OcrProcessing] File preview URL created:', originalPreviewUrl.value);
    } else {
      console.log('[OcrProcessing] Non-image file detected');
      formError.value = '请上传图片文件！';
    }
  } else {
    console.log('[OcrProcessing] No files in drop event');
  }
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement;
  const f = input.files?.[0] ?? null;
  file.value = f;
  originalPreviewUrl.value = f ? URL.createObjectURL(f) : "";
  
  // 清除裁剪缓存
  croppedImageBase64.value = "";
  cropInfo.value = null;
}

// 裁剪功能
function showCropModal() {
  showCropper.value = true;
}

function handleCrop(cropData: {
  x: number;
  y: number;
  width: number;
  height: number;
  croppedImageBase64: string;
}) {
  croppedImageBase64.value = cropData.croppedImageBase64;
  cropInfo.value = {
    x: cropData.x,
    y: cropData.y,
    width: cropData.width,
    height: cropData.height
  };
  showCropper.value = false;
  formOk.value = `已裁剪图片区域：${cropData.width}x${cropData.height}，起始位置 (${cropData.x}, ${cropData.y})`;
  setTimeout(() => {
    formOk.value = "";
  }, 3000);
}

function handleCropCancel() {
  showCropper.value = false;
}

async function onOcr() {
  if (!token.value) {
    formError.value = "未登录，请返回登录页。";
    return;
  }
  if (!file.value && !croppedImageBase64.value) {
    formError.value = "请先选择文件。";
    return;
  }

  formError.value = "";
  formOk.value = "";
  loading.value = true;
  progress.value = 0;
  progressText.value = "准备识别...";

  const progressInterval = setInterval(() => {
    progress.value += 5;
    if (progress.value < 40) {
      progressText.value = "正在进行 OCR 识别...";
    } else if (progress.value < 70) {
      progressText.value = "正在进行文本纠错...";
    } else if (progress.value < 90) {
      progressText.value = "正在生成结果...";
    }
  }, 300);

  try {
    const fd = new FormData();
    
    // 如果有裁剪后的图片，使用裁剪后的图片
    if (croppedImageBase64.value) {
      // 将 base64 转换为 Blob
      const response = await fetch(croppedImageBase64.value);
      const blob = await response.blob();
      const croppedFile = new File([blob], 'cropped_image.png', { type: 'image/png' });
      fd.append("file", croppedFile);
      console.log('[OCR] 使用裁剪后的图片进行识别');
    } else if (file.value) {
      fd.append("file", file.value);
    }
    
    // 传递拼写纠错参数
    fd.append("enable_spell_correction", enableSpellCorrection.value ? "true" : "false");
    console.log(`[OCR] 开始识别，拼写纠错：${enableSpellCorrection.value}`);

    const res = await fetch(`${API_BASE}/ocr/recognize`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token.value}`,
      },
      body: fd,
    });

    const data = await res.json();
    
    if (!res.ok) {
      throw new Error(data?.detail || "识别请求失败");
    }

    progress.value = 100;
    progressText.value = "识别完成！";

    result.value = data;
    ocrResult.value = data.raw_text || "";
    correctedResult.value = data.corrected_text || "";

    formOk.value = "OCR识别完成！";
  } catch (e) {
    formError.value = e instanceof Error ? e.message : "识别失败，请稍后重试。";
  } finally {
    clearInterval(progressInterval);
    loading.value = false;
  }
}

async function downloadText() {
  if (!correctedResult.value) return;
  downloading.value = true;
  try {
    const blob = new Blob([correctedResult.value], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `ocr_result_${Date.now()}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    formOk.value = "下载完成！";
  } catch (e) {
    formError.value = "下载失败，请稍后重试。";
  } finally {
    downloading.value = false;
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--background);
  background-image: 
    radial-gradient(circle at 20% 80%, rgba(0, 255, 136, 0.03) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(0, 204, 136, 0.03) 0%, transparent 50%),
    linear-gradient(180deg, #0a0a0a 0%, #0f1419 100%);
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card {
  width: 100%;
  max-width: 1000px;
  background: rgba(17, 24, 39, 0.95);
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 0 0 1px rgba(0, 255, 136, 0.1), 
              0 8px 32px rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(0, 255, 136, 0.15);
  backdrop-filter: blur(10px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.card:hover {
  box-shadow: 0 0 0 1px rgba(0, 255, 136, 0.2), 
              0 12px 40px rgba(0, 0, 0, 0.5),
              0 0 60px rgba(0, 255, 136, 0.08);
  transform: translateY(-2px);
}

.card-header {
  margin-bottom: 32px;
  text-align: center;
  position: relative;
  padding-bottom: 24px;
}

.card-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 80%;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--primary), transparent);
  opacity: 0.3;
}

.title {
  font-size: 36px;
  font-weight: 900;
  color: var(--primary);
  margin: 0 0 8px 0;
  text-shadow: 0 0 30px rgba(0, 255, 136, 0.4);
  letter-spacing: 0.02em;
  line-height: 1.2;
  background: linear-gradient(135deg, var(--primary) 0%, #00cc88 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: titleGlow 2s ease-in-out infinite alternate;
}

@keyframes titleGlow {
  from {
    text-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
  }
  to {
    text-shadow: 0 0 40px rgba(0, 255, 136, 0.6);
  }
}

.subtitle {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.4;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.field {
  margin-bottom: 24px;
}

.label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.file-upload-area {
  width: 100%;
  min-height: 200px;
  border: 2px dashed rgba(0, 255, 136, 0.3);
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.6);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.file-upload-area:hover {
  border-color: var(--primary);
  background: rgba(0, 255, 136, 0.05);
  box-shadow: 0 0 0 4px rgba(0, 255, 136, 0.1);
  transform: translateY(-2px);
}

.file-upload-area.dragover {
  border-color: var(--primary);
  background: rgba(0, 255, 136, 0.1);
  box-shadow: 0 0 0 4px rgba(0, 255, 136, 0.2);
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  min-height: 200px;
}

.upload-icon {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 255, 136, 0.1);
  border-radius: 50%;
  margin: 0 auto 20px;
  color: var(--primary);
  transition: all 0.3s ease;
}

.upload-icon svg {
  width: 32px;
  height: 32px;
  display: block;
  filter: drop-shadow(0 0 10px rgba(0, 255, 136, 0.3));
}

.upload-text {
  text-align: center;
  margin-bottom: 20px;
}

.upload-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.upload-hint {
  font-size: 12px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  line-height: 1.4;
}

.file-preview {
  width: 100%;
  max-width: 400px;
  background: rgba(17, 24, 39, 0.95);
  border: 1px solid rgba(0, 255, 136, 0.2);
  border-radius: 8px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.file-preview:hover {
  border-color: var(--primary);
  box-shadow: 0 6px 24px rgba(0, 255, 136, 0.15);
  transform: translateY(-2px);
}

.preview-image {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 6px;
  border: 1px solid rgba(0, 255, 136, 0.2);
  flex-shrink: 0;
}

.file-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.file-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
}

.file-size {
  font-size: 12px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  display: block;
}

.file-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.crop-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(0, 255, 136, 0.1);
  border: 1px solid rgba(0, 255, 136, 0.3);
  border-radius: 6px;
  color: var(--primary);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.crop-btn:hover {
  background: rgba(0, 255, 136, 0.15);
  border-color: var(--primary);
  box-shadow: 0 4px 12px rgba(0, 255, 136, 0.2);
  transform: translateY(-2px);
}

.crop-btn svg {
  width: 16px;
  height: 16px;
}

.progress-container {
  margin: 24px 0;
  padding: 20px;
  background: rgba(15, 23, 42, 0.8);
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 136, 0.1);
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: rgba(31, 41, 55, 0.8);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 12px;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), var(--secondary));
  border-radius: 4px;
  transition: width 0.3s ease;
  box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
}

.progress-text {
  font-size: 14px;
  color: var(--text-secondary);
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 500;
}

.actions {
  display: flex;
  gap: 16px;
  margin-top: 24px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

/* 拼写纠错选项样式 */
.spell-correction-option {
  margin-top: 20px;
  padding: 20px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(0, 255, 136, 0.12);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.spell-correction-option:hover {
  border-color: rgba(0, 255, 136, 0.2);
  background: rgba(15, 23, 42, 0.7);
  box-shadow: 0 4px 16px rgba(0, 255, 136, 0.08);
}

.spell-correction-label {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  cursor: pointer;
}

.checkbox-wrapper {
  position: relative;
  flex-shrink: 0;
  margin-top: 2px;
}

.checkbox {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.checkbox-custom {
  display: inline-block;
  width: 20px;
  height: 20px;
  background: rgba(15, 23, 42, 0.8);
  border: 2px solid rgba(0, 255, 136, 0.3);
  border-radius: 6px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.checkbox-custom::after {
  content: '';
  position: absolute;
  display: none;
  left: 6px;
  top: 2px;
  width: 5px;
  height: 10px;
  border: solid var(--primary);
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.checkbox:checked + .checkbox-custom {
  border-color: var(--primary);
  background: rgba(0, 255, 136, 0.1);
  box-shadow: 0 0 10px rgba(0, 255, 136, 0.2);
}

.checkbox:checked + .checkbox-custom::after {
  display: block;
}

.checkbox-custom:hover {
  border-color: rgba(0, 255, 136, 0.5);
  box-shadow: 0 0 8px rgba(0, 255, 136, 0.15);
}

.spell-content {
  flex: 1;
}

.spell-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.title-text {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.title-badge {
  font-size: 11px;
  font-weight: 700;
  color: var(--primary);
  background: rgba(0, 255, 136, 0.1);
  padding: 3px 8px;
  border-radius: 4px;
  border: 1px solid rgba(0, 255, 136, 0.2);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.spell-description {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.result-section {
  margin-top: 32px;
  padding-top: 32px;
  border-top: 1px solid rgba(0, 255, 136, 0.1);
  position: relative;
}

.result-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--primary), transparent);
  opacity: 0.3;
}

.result-header {
  margin-bottom: 24px;
  text-align: center;
}

.result-title {
  font-size: 24px;
  font-weight: 800;
  color: var(--text);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-shadow: 0 0 15px rgba(0, 255, 136, 0.1);
}

.image-preview {
  margin-bottom: 24px;
  text-align: left;
  width: 100%;
  overflow: visible;
}

.preview-image {
  max-width: 400px;
  height: auto;
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 136, 0.2);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
  display: block;
}

.preview-image:hover {
  transform: scale(1.02);
  box-shadow: 0 6px 24px rgba(0, 255, 136, 0.15);
}

.ocr-section {
  margin-bottom: 24px;
}

.corrected-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.result-textarea {
  width: 100%;
  min-height: 200px;
  padding: 16px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
  font-family: inherit;
  transition: all 0.3s ease;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
}

.result-textarea.ocr {
  background: rgba(15, 23, 42, 0.8);
  color: var(--text);
  resize: vertical;
}

.result-textarea.corrected {
  background: rgba(0, 255, 136, 0.05);
  border-color: rgba(0, 255, 136, 0.3);
  color: var(--text);
  resize: vertical;
}

.result-textarea:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(0, 255, 136, 0.1),
              inset 0 2px 4px rgba(0, 0, 0, 0.2);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin: 24px 0;
}

.info-card {
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(0, 255, 136, 0.15);
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.info-card:hover {
  border-color: var(--primary);
  box-shadow: 0 6px 24px rgba(0, 255, 136, 0.15);
  transform: translateY(-2px);
}

.info-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-value {
  font-size: 24px;
  font-weight: 800;
  color: var(--text);
  text-shadow: 0 0 15px rgba(0, 255, 136, 0.1);
}

.next-actions {
  margin-top: 24px;
  padding: 24px;
  background: rgba(15, 23, 42, 0.8);
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 136, 0.1);
  position: relative;
}

.next-actions::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--primary), transparent);
  opacity: 0.3;
}

.actions-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 16px;
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.actions-container {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  justify-content: center;
}



/* 响应式设计 */
@media (max-width: 768px) {
  .page {
    padding: 16px;
  }
  
  .card {
    padding: 24px;
  }
  
  .title {
    font-size: 24px;
  }
  
  .actions {
    flex-direction: column;
  }
  
  .actions .btn {
    width: 100%;
  }
  
  .actions-container {
    flex-direction: column;
  }
  
  .actions-container .btn {
    width: 100%;
  }
  
  .file-actions {
    flex-direction: column;
    width: 100%;
  }
  
  .crop-btn {
    width: 100%;
    justify-content: center;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .upload-content {
    padding: 30px 16px;
  }
  
  .upload-icon {
    width: 50px;
    height: 50px;
  }
  
  .upload-icon svg {
    width: 24px;
    height: 24px;
  }
  
  .file-preview {
    flex-direction: column;
    text-align: center;
  }
  
  .preview-image {
    max-width: 100%;
  }
}
</style>
