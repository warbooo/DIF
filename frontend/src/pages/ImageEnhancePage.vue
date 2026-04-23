<template>
  <div class="page">
    <div class="card">
        <div class="card-header">
          <h1 class="title">图片美化</h1>
          <p class="subtitle">智能推荐参数，一键美化图片</p>
        </div>

        <!-- 上传图片（移到最上面） -->
        <div class="upload-section">
          <div class="section-title">上传图片</div>
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
              type="file"
              accept="image/*"
              style="display: none;"
              @change="onFileChange"
            />
            <div class="upload-content">
              <div class="upload-icon">
                <svg viewBox="0 0 24 24" fill="none">
                  <path d="M12 15V3M12 3L8 7M12 3L16 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M21 15H3M21 15C21 18.3137 18.3137 21 15 21H9C5.68629 21 3 18.3137 3 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div class="upload-text">
                <div class="upload-title">{{ isDragging ? '释放文件到此处' : '点击或拖拽文件到此处' }}</div>
                <div class="upload-hint">支持 JPG、PNG、BMP 等常见图片格式</div>
              </div>
              <div v-if="file" class="file-preview">
                <img :src="originalPreviewUrl" alt="预览" class="preview-image" />
                <div class="file-info">
                  <div class="file-name">{{ file.name }}</div>
                  <div class="file-size">{{ formatFileSize(file.size) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 智能推荐面板（仅在有图片时显示） -->
        <div v-if="file && showRecommendation && recommendation" class="recommendation-panel">
        <div class="recommendation-header">
          <div class="recommendation-title">
            <svg viewBox="0 0 24 24" fill="none" class="rec-icon">
              <path d="M9.66347 16.9612C11.133 18.372 12.5339 18.9973 13.5999 18.9973C15.2209 18.9973 16.4261 17.6628 16.9526 16.2898C17.0938 15.9226 17.6153 15.8285 17.8812 16.0944L19.2954 17.5086C19.5613 17.7745 19.4672 18.296 19.1 18.4372C17.3294 19.1175 15.4491 19.4973 13.5999 19.4973C11.9256 19.4973 10.2567 18.9973 8.79394 17.9973C7.33115 16.9973 6.13379 15.6628 5.33344 14.1612C5.12735 13.775 5.33344 13.3226 5.73344 13.1612L7.59994 12.4112C7.99994 12.2512 8.44994 12.4973 8.59994 12.9112L9.66347 16.9612Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M12 15V3M12 3L8 7M12 3L16 7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>智能推荐美化方案</span>
          </div>
          <button class="close-rec" @click="showRecommendation = false">×</button>
        </div>
        
        <div class="recommendation-content">
          <div class="rec-reason">
            <div class="reason-title">推荐理由</div>
            <div class="reason-text">{{ recommendation.recommendation_reason }}</div>
          </div>
          
          <div class="rec-analysis">
            <div class="analysis-item">
              <span class="analysis-label">图像分析:</span>
              <span class="analysis-value">
                亮度 <strong>{{ (Number(recommendation.image_analysis.brightness) * 100).toFixed(0) }}%</strong> · 
                对比度 <strong>{{ (Number(recommendation.image_analysis.contrast) * 100).toFixed(0) }}%</strong> · 
                饱和度 <strong>{{ (Number(recommendation.image_analysis.saturation) * 100).toFixed(0) }}%</strong>
              </span>
            </div>
          </div>
          
          <!-- 显示推荐参数 -->
          <div v-if="recommendation.recommended_params" class="rec-params">
            <div class="params-title">推荐参数</div>
            <div class="params-grid">
              <div class="param-tag">
                <span class="param-name">亮度</span>
                <span class="param-value">{{ Number(recommendation.recommended_params.brightness || 1).toFixed(2) }}</span>
              </div>
              <div class="param-tag">
                <span class="param-name">对比度</span>
                <span class="param-value">{{ Number(recommendation.recommended_params.contrast || 1).toFixed(2) }}</span>
              </div>
              <div class="param-tag">
                <span class="param-name">饱和度</span>
                <span class="param-value">{{ Number(recommendation.recommended_params.saturation || 1).toFixed(2) }}</span>
              </div>
              <div class="param-tag">
                <span class="param-name">锐化</span>
                <span class="param-value">{{ Number(recommendation.recommended_params.sharpness || 1).toFixed(2) }}</span>
              </div>
              <div class="param-tag">
                <span class="param-name">色温</span>
                <span class="param-value">{{ recommendation.recommended_params.warmth || 0 }}</span>
              </div>
              <div class="param-tag">
                <span class="param-name">曝光</span>
                <span class="param-value">{{ recommendation.recommended_params.exposure || 0 }}</span>
              </div>
              <div class="param-tag">
                <span class="param-name">高光</span>
                <span class="param-value">{{ recommendation.recommended_params.highlights || 0 }}</span>
              </div>
              <div class="param-tag">
                <span class="param-name">阴影</span>
                <span class="param-value">{{ recommendation.recommended_params.shadows || 0 }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="recommendation-actions">
          <button class="btn ghost" @click="showRecommendation = false">暂不使用</button>
          <button class="btn primary" @click="applyRecommendation" :disabled="applyingRec">
            {{ applyingRec ? "应用中..." : "使用推荐方案" }}
          </button>
        </div>
      </div>

      <!-- 预设方案 -->
      <div class="presets-section">
        <div class="section-title">预设方案</div>
        <div class="presets-grid">
          <div 
            v-for="preset in presets" 
            :key="preset.id"
            class="preset-card"
            :class="{ active: activePreset === preset.id }"
            @click="applyPreset(preset)"
          >
            <div class="preset-name">{{ preset.name }}</div>
            <div class="preset-desc">{{ preset.description }}</div>
          </div>
        </div>
      </div>

      <!-- 参数调节 -->
      <div class="params-section">
        <div class="section-title">参数调节</div>
        
        <div class="param-sliders">
          <!-- 亮度 -->
          <div class="param-item">
            <div class="param-header">
              <label class="param-label">亮度</label>
              <span class="param-value">{{ params.brightness.toFixed(2) }}</span>
            </div>
            <input 
              type="range" 
              v-model.number="params.brightness"
              min="0" max="2" step="0.01"
              class="param-slider"
              @input="debouncedEnhance"
            />
            <div class="param-labels">
              <span>暗</span>
              <span>正常</span>
              <span>亮</span>
            </div>
          </div>

          <!-- 对比度 -->
          <div class="param-item">
            <div class="param-header">
              <label class="param-label">对比度</label>
              <span class="param-value">{{ params.contrast.toFixed(2) }}</span>
            </div>
            <input 
              type="range" 
              v-model.number="params.contrast"
              min="0" max="2" step="0.01"
              class="param-slider"
              @input="debouncedEnhance"
            />
            <div class="param-labels">
              <span>低</span>
              <span>正常</span>
              <span>高</span>
            </div>
          </div>

          <!-- 饱和度 -->
          <div class="param-item">
            <div class="param-header">
              <label class="param-label">饱和度</label>
              <span class="param-value">{{ params.saturation.toFixed(2) }}</span>
            </div>
            <input 
              type="range" 
              v-model.number="params.saturation"
              min="0" max="2" step="0.01"
              class="param-slider"
              @input="debouncedEnhance"
            />
            <div class="param-labels">
              <span>淡</span>
              <span>正常</span>
              <span>艳</span>
            </div>
          </div>

          <!-- 锐化 -->
          <div class="param-item">
            <div class="param-header">
              <label class="param-label">锐化</label>
              <span class="param-value">{{ params.sharpness.toFixed(2) }}</span>
            </div>
            <input 
              type="range" 
              v-model.number="params.sharpness"
              min="0" max="2" step="0.01"
              class="param-slider"
              @input="debouncedEnhance"
            />
            <div class="param-labels">
              <span>柔</span>
              <span>正常</span>
              <span>锐</span>
            </div>
          </div>

          <!-- 色温 -->
          <div class="param-item">
            <div class="param-header">
              <label class="param-label">色温</label>
              <span class="param-value">{{ params.warmth }}</span>
            </div>
            <input 
              type="range" 
              v-model.number="params.warmth"
              min="-100" max="100" step="1"
              class="param-slider"
              @input="debouncedEnhance"
            />
            <div class="param-labels">
              <span>冷</span>
              <span>正常</span>
              <span>暖</span>
            </div>
          </div>

          <!-- 曝光 -->
          <div class="param-item">
            <div class="param-header">
              <label class="param-label">曝光</label>
              <span class="param-value">{{ params.exposure }}</span>
            </div>
            <input 
              type="range" 
              v-model.number="params.exposure"
              min="-100" max="100" step="1"
              class="param-slider"
              @input="debouncedEnhance"
            />
            <div class="param-labels">
              <span>暗</span>
              <span>正常</span>
              <span>亮</span>
            </div>
          </div>

          <!-- 高光 -->
          <div class="param-item">
            <div class="param-header">
              <label class="param-label">高光</label>
              <span class="param-value">{{ params.highlights }}</span>
            </div>
            <input 
              type="range" 
              v-model.number="params.highlights"
              min="-100" max="100" step="1"
              class="param-slider"
              @input="debouncedEnhance"
            />
            <div class="param-labels">
              <span>压低</span>
              <span>正常</span>
              <span>提亮</span>
            </div>
          </div>

          <!-- 阴影 -->
          <div class="param-item">
            <div class="param-header">
              <label class="param-label">阴影</label>
              <span class="param-value">{{ params.shadows }}</span>
            </div>
            <input 
              type="range" 
              v-model.number="params.shadows"
              min="-100" max="100" step="1"
              class="param-slider"
              @input="debouncedEnhance"
            />
            <div class="param-labels">
              <span>压暗</span>
              <span>正常</span>
              <span>提亮</span>
            </div>
          </div>
        </div>

        <div class="param-actions">
          <button class="btn ghost" @click="resetParams">重置参数</button>
          <button class="btn primary" @click="enhanceImage" :disabled="enhancing || !file">
            {{ enhancing ? "美化中..." : "应用美化" }}
          </button>
        </div>
      </div>

      <!-- 对比预览（仅在有图片时显示） -->
        <div v-if="file && enhancedImageBase64" class="preview-section">
          <div class="section-title">美化效果对比</div>
          <div class="comparison-container" ref="comparisonContainer">
            <!-- 原图 -->
            <div class="comparison-original">
              <img 
                class="comparison-image"
                :src="originalPreviewUrl" 
                alt="原图" 
              />
            </div>
            <!-- 美化后 -->
            <div class="comparison-repaired">
              <img 
                class="comparison-image"
                :src="`data:image/png;base64,${enhancedImageBase64}`" 
                alt="美化后" 
              />
            </div>
            <!-- 分隔线 -->
            <div class="divider-line" :style="{ left: sliderPosition + '%' }"></div>
            <!-- 滑块 -->
            <div 
              class="comparison-slider" 
              :style="{ left: sliderPosition + '%' }"
              @mousedown="startSlider"
            >
              <div class="slider-handle">
                <svg viewBox="0 0 24 24" fill="none">
                  <path d="M15 18L9 12L15 6" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <svg viewBox="0 0 24 24" fill="none">
                  <path d="M9 18L15 12L9 6" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
            </div>
            <!-- 标签 -->
            <div class="version-label left-label">原图</div>
            <div class="version-label right-label">美化后</div>
          </div>
        </div>

      <div v-if="formError" class="msg error">{{ formError }}</div>
      <div v-if="formOk" class="msg ok">{{ formOk }}</div>

      <div class="actions">
        <button class="btn ghost" type="button" @click="resetPage">清空</button>
        <button 
          class="btn primary" 
          type="button" 
          @click="downloadResult"
          :disabled="!enhancedImageBase64 || downloading"
        >
          {{ downloading ? "下载中..." : "下载美化后的图片" }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { API_BASE } from "../api/base";

const token = ref<string | null>(localStorage.getItem("token"));

// 文件相关
const file = ref<File | null>(null);
const originalPreviewUrl = ref("");
const enhancedImageBase64 = ref("");
const fileInput = ref<HTMLInputElement | null>(null);
const isDragging = ref(false);

// 参数相关
const params = ref({
  brightness: 1.0,
  contrast: 1.0,
  saturation: 1.0,
  sharpness: 1.0,
  warmth: 0,
  exposure: 0,
  highlights: 0,
  shadows: 0
});

const defaultParams = { ...params.value };

// 预设方案
const presets = ref<any[]>([]);
const activePreset = ref("");

// 智能推荐
const recommendation = ref<any>(null);
const showRecommendation = ref(false);
const applyingRec = ref(false);

// 状态
const enhancing = ref(false);
const downloading = ref(false);
const formError = ref("");
const formOk = ref("");

// 滑块
const sliderPosition = ref(50);
const comparisonContainer = ref<HTMLElement | null>(null);

// 防抖定时器
let enhanceTimer: any = null;

// 加载预设方案
async function loadPresets() {
  try {
    const res = await fetch(`${API_BASE}/image/enhance/presets`);
    const data = await res.json();
    if (res.ok) {
      presets.value = data.presets || [];
    }
  } catch (e) {
    console.error('[ImageEnhance] 加载预设方案失败:', e);
  }
}

// 应用预设
function applyPreset(preset: any) {
  activePreset.value = preset.id;
  params.value = { ...preset.params };
  debouncedEnhance();
}

// 应用推荐（如果用户关闭了推荐面板后想重新应用）
function applyRecommendation() {
  if (!recommendation.value) return;
  
  applyingRec.value = true;
  params.value = { ...recommendation.value.recommended_params };
  activePreset.value = "custom";
  
  showRecommendation.value = false;
  applyingRec.value = false;
  formOk.value = "已重新应用推荐方案";
  
  setTimeout(() => {
    formOk.value = "";
  }, 3000);
  
  debouncedEnhance();
}


// 美化图片
async function enhanceImage() {
  if (!file.value || !token.value) {
    formError.value = "请先上传图片";
    return;
  }
  
  enhancing.value = true;
  formError.value = "";
  formOk.value = "";
  
  try {
    const fd = new FormData();
    fd.append("file", file.value);
    fd.append("brightness", params.value.brightness.toString());
    fd.append("contrast", params.value.contrast.toString());
    fd.append("saturation", params.value.saturation.toString());
    fd.append("sharpness", params.value.sharpness.toString());
    fd.append("warmth", params.value.warmth.toString());
    fd.append("exposure", params.value.exposure.toString());
    fd.append("highlights", params.value.highlights.toString());
    fd.append("shadows", params.value.shadows.toString());
    
    const res = await fetch(`${API_BASE}/image/enhance/`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token.value}` },
      body: fd,
    });
    
    const data = await res.json();
    if (res.ok) {
      enhancedImageBase64.value = data.image_base64;
      formOk.value = "美化完成！";
    } else {
      formError.value = data.detail || "美化失败";
    }
  } catch (e) {
    formError.value = e instanceof Error ? e.message : "美化失败";
  } finally {
    enhancing.value = false;
  }
}

// 防抖美化
function debouncedEnhance() {
  if (enhanceTimer) clearTimeout(enhanceTimer);
  enhanceTimer = setTimeout(() => {
    enhanceImage();
  }, 500); // 500ms 防抖
}

// 重置参数
function resetParams() {
  params.value = { ...defaultParams };
  activePreset.value = "default";
  debouncedEnhance();
}

// 文件处理
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

function onDragOver(e: DragEvent) {
  e.preventDefault();
  isDragging.value = true;
}

function onDragLeave(e: DragEvent) {
  e.preventDefault();
  isDragging.value = false;
}

function onDrop(e: DragEvent) {
  e.preventDefault();
  isDragging.value = false;
  
  const files = e.dataTransfer?.files;
  if (files && files.length > 0) {
    handleFile(files[0]);
  }
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement;
  const f = input.files?.[0];
  if (f) {
    handleFile(f);
  }
}

function handleFile(f: File) {
  if (!f.type.startsWith('image/')) {
    formError.value = '请上传图片文件！';
    return;
  }
  
  file.value = f;
  originalPreviewUrl.value = URL.createObjectURL(f);
  enhancedImageBase64.value = "";
  recommendation.value = null; // 清空之前的推荐
  showRecommendation.value = false; // 关闭推荐面板
  
  // 获取推荐并自动应用参数
  getRecommendationAndApply();
}

// 获取推荐并应用，然后美化
async function getRecommendationAndApply() {
  if (!file.value || !token.value) {
    // 如果没有 token，直接美化
    console.log('[ImageEnhance] 没有 token，直接美化');
    enhanceImage();
    return;
  }
  
  try {
    console.log('[ImageEnhance] 开始获取推荐...');
    const fd = new FormData();
    fd.append("file", file.value);
    
    const res = await fetch(`${API_BASE}/image/enhance/recommend`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token.value}` },
      body: fd,
    });
    
    const data = await res.json();
    if (res.ok) {
      console.log('[ImageEnhance] 获取推荐成功:', data.recommendation);
      recommendation.value = data.recommendation;
      
      // 自动应用推荐参数
      params.value = { ...recommendation.value.recommended_params };
      activePreset.value = "custom";
      
      // 显示推荐信息
      showRecommendation.value = true;
      formOk.value = "已应用智能推荐参数，可手动微调";
      
      setTimeout(() => {
        formOk.value = "";
      }, 3000);
      
      // 应用推荐参数后进行美化
      console.log('[ImageEnhance] 开始美化...');
      enhanceImage();
    } else {
      // 推荐失败，使用默认参数美化
      console.error('[ImageEnhance] 推荐失败:', data);
      enhanceImage();
    }
  } catch (e) {
    console.error('[ImageEnhance] 获取推荐失败:', e);
    // 出错时使用默认参数美化
    enhanceImage();
  }
}

// 初始化滑块位置
function initSliderPosition() {
  if (comparisonContainer.value) {
    comparisonContainer.value.style.setProperty('--slider-position', `${sliderPosition.value}%`);
  }
}

// 滑块
function startSlider(e: MouseEvent) {
  e.preventDefault();
  const onMouseMove = (ev: MouseEvent) => {
    if (!comparisonContainer.value) return;
    const rect = comparisonContainer.value.getBoundingClientRect();
    let newPosition = ((ev.clientX - rect.left) / rect.width) * 100;
    newPosition = Math.max(0, Math.min(100, newPosition));
    sliderPosition.value = newPosition;
    // 更新CSS变量
    comparisonContainer.value.style.setProperty('--slider-position', `${newPosition}%`);
  };
  
  const onMouseUp = () => {
    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup', onMouseUp);
  };
  
  document.addEventListener('mousemove', onMouseMove);
  document.addEventListener('mouseup', onMouseUp);
}

// 下载
async function downloadResult() {
  if (!enhancedImageBase64.value) return;
  
  downloading.value = true;
  try {
    const link = document.createElement("a");
    link.href = `data:image/png;base64,${enhancedImageBase64.value}`;
    link.download = `enhanced_image_${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    formOk.value = "下载完成！";
  } catch (e) {
    formError.value = "下载失败";
  } finally {
    downloading.value = false;
  }
}

// 重置页面
function resetPage() {
  file.value = null;
  originalPreviewUrl.value = "";
  enhancedImageBase64.value = "";
  params.value = { ...defaultParams };
  activePreset.value = "";
  recommendation.value = null;
  showRecommendation.value = false;
  formError.value = "";
  formOk.value = "";
  sliderPosition.value = 50;
}

onMounted(() => {
  loadPresets();
  initSliderPosition();
});
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
  max-width: 1200px;
  background: rgba(17, 24, 39, 0.95);
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 0 0 1px rgba(0, 255, 136, 0.1);
  border: 1px solid rgba(0, 255, 136, 0.15);
}

.card-header {
  text-align: center;
  margin-bottom: 32px;
}

.title {
  font-size: 36px;
  font-weight: 900;
  color: var(--primary);
  margin: 0 0 8px 0;
  text-shadow: 0 0 30px rgba(0, 255, 136, 0.4);
}

.subtitle {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 0;
}

/* 推荐面板 */
.recommendation-panel {
  margin: 24px 0;
  padding: 24px;
  background: rgba(0, 255, 136, 0.05);
  border: 1px solid rgba(0, 255, 136, 0.3);
  border-radius: 12px;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.recommendation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.recommendation-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 700;
  color: var(--primary);
}

.rec-icon {
  width: 24px;
  height: 24px;
}

.close-rec {
  width: 32px;
  height: 32px;
  border: 1px solid rgba(0, 255, 136, 0.2);
  background: rgba(17, 24, 39, 0.95);
  color: var(--primary);
  border-radius: 8px;
  font-size: 24px;
  cursor: pointer;
}

.close-rec:hover {
  transform: rotate(90deg);
}

.recommendation-content {
  display: grid;
  gap: 16px;
  margin-bottom: 20px;
}

.rec-reason {
  padding: 16px;
  background: rgba(15, 23, 42, 0.8);
  border-radius: 8px;
  border-left: 3px solid var(--primary);
}

.reason-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--primary);
  margin-bottom: 8px;
}

.reason-text {
  font-size: 14px;
  color: var(--text);
  line-height: 1.6;
}

.rec-analysis {
  margin-top: 16px;
  padding: 16px;
  background: rgba(0, 255, 136, 0.05);
  border: 1px solid rgba(0, 255, 136, 0.15);
  border-radius: 8px;
}

.analysis-item {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.analysis-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.analysis-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--primary);
  flex: 1;
}

.recommendation-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

/* 推荐参数显示 */
.rec-params {
  margin-top: 16px;
}

.params-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--primary);
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 8px;
}

.param-tag {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px;
  background: rgba(17, 24, 39, 0.95);
  border: 1px solid rgba(0, 255, 136, 0.15);
  border-radius: 6px;
  transition: all 0.3s ease;
}

.param-tag:hover {
  border-color: var(--primary);
  background: rgba(0, 255, 136, 0.05);
  transform: translateY(-2px);
}

.param-name {
  font-size: 11px;
  color: var(--text-secondary);
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.param-value {
  font-size: 16px;
  font-weight: 700;
  color: var(--primary);
}

/* 预设方案 */
.presets-section {
  margin: 24px 0;
}

.section-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 16px;
}

.presets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
}

.preset-card {
  padding: 16px;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(0, 255, 136, 0.15);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
}

.preset-card:hover {
  border-color: var(--primary);
  transform: translateY(-2px);
}

.preset-card.active {
  border-color: var(--primary);
  background: rgba(0, 255, 136, 0.1);
}

.preset-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 4px;
}

.preset-desc {
  font-size: 12px;
  color: var(--text-secondary);
}

/* 参数调节 */
.params-section {
  margin: 24px 0;
}

.param-sliders {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.param-item {
  padding: 16px;
  background: rgba(15, 23, 42, 0.6);
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 136, 0.1);
}

.param-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.param-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}

.param-value {
  font-size: 14px;
  font-weight: 700;
  color: var(--primary);
}

.param-slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: rgba(31, 41, 55, 0.8);
  outline: none;
  appearance: none;
  -webkit-appearance: none;
}

.param-slider::-webkit-slider-thumb {
  appearance: none;
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--primary);
  cursor: pointer;
  box-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
}

.param-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 11px;
  color: var(--text-secondary);
}

.param-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

/* 上传区域 */
.upload-section {
  margin: 24px 0;
}

.file-upload-area {
  min-height: 200px;
  border: 2px dashed rgba(0, 255, 136, 0.3);
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.6);
  cursor: pointer;
  transition: all 0.3s ease;
}

.file-upload-area:hover,
.file-upload-area.dragover {
  border-color: var(--primary);
  background: rgba(0, 255, 136, 0.05);
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.upload-icon {
  width: 60px;
  height: 60px;
  margin-bottom: 20px;
  color: var(--primary);
}

.file-preview {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
  padding: 16px;
  background: rgba(17, 24, 39, 0.95);
  border-radius: 8px;
}

.preview-image {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 6px;
}

/* 对比预览 */
.preview-section {
  margin: 24px 0;
}

.comparison-container {
  position: relative;
  width: 100%;
  max-width: 800px;
  height: 500px;
  margin: 0 auto;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(0, 255, 136, 0.15);
}

.comparison-original,
.comparison-repaired {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.comparison-repaired {
  clip-path: polygon(0 0, 0 100%, 100% 100%, 100% 0);
  z-index: 1;
}

.comparison-original {
  clip-path: polygon(0 0, 0 100%, var(--slider-position, 50%) 100%, var(--slider-position, 50%) 0);
  z-index: 2;
}

.comparison-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.divider-line {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--primary);
  z-index: 9;
  box-shadow: 0 0 20px rgba(0, 255, 136, 0.5);
}

.comparison-slider {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  z-index: 10;
  cursor: ew-resize;
}

.slider-handle {
  width: 40px;
  height: 40px;
  background: rgba(17, 24, 39, 0.95);
  border: 2px solid var(--primary);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: var(--primary);
}

.slider-handle svg {
  width: 16px;
  height: 16px;
}

.version-label {
  position: absolute;
  bottom: 20px;
  padding: 8px 20px;
  background: rgba(17, 24, 39, 0.95);
  border: 1px solid rgba(0, 255, 136, 0.2);
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
  z-index: 15;
}

.left-label {
  left: 20px;
}

.right-label {
  right: 20px;
}

/* 消息 */
.msg {
  padding: 12px 20px;
  border-radius: 8px;
  margin: 16px 0;
  font-size: 14px;
  font-weight: 600;
}

.msg.error {
  background: rgba(255, 68, 68, 0.1);
  border: 1px solid rgba(255, 68, 68, 0.3);
  color: #ff4444;
}

.msg.ok {
  background: rgba(0, 255, 136, 0.1);
  border: 1px solid rgba(0, 255, 136, 0.3);
  color: var(--primary);
}

/* 按钮 */
.actions {
  display: flex;
  gap: 16px;
  justify-content: flex-end;
  margin-top: 24px;
}

.btn {
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn.primary {
  background: var(--primary);
  color: #000;
}

.btn.primary:hover:not(:disabled) {
  box-shadow: 0 0 20px rgba(0, 255, 136, 0.4);
  transform: translateY(-2px);
}

.btn.ghost {
  background: transparent;
  border: 1px solid rgba(0, 255, 136, 0.3);
  color: var(--primary);
}

.btn.ghost:hover:not(:disabled) {
  background: rgba(0, 255, 136, 0.1);
}

/* 响应式 */
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
  
  .presets-grid,
  .param-sliders,
  .rec-analysis {
    grid-template-columns: 1fr;
  }
  
  .comparison-container {
    height: 300px;
  }
  
  .actions {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
  }
}
</style>
