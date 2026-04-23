<template>
  <div class="page">
    <div class="card">
      <div class="card-header">
        <h1 class="title">图片修复</h1>
        <p class="subtitle">
          上传图片，使用超分辨率技术增强图像清晰度和细节
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

      <form @submit.prevent="onRepair" v-else>
        <!-- 上传图片（移到最上面） -->
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
              <div v-if="file" class="file-preview">
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

        <!-- 模型选择 -->
        <div class="field">
          <label class="label">超分辨率模型 <span class="required">*</span></label>
          <select v-model="srModelType" class="model-select">
            <option value="classical">经典超分辨率 (ClassicalSR)</option>
            <option value="compressed">压缩图像恢复 (CompressedSR)</option>
            <option value="realworld">真实世界图像 (RealWorldSR)</option>
          </select>
        </div>

        <!-- 模型选择指南 -->
        <div class="model-guide">
          <div class="guide-title">模型选择指南</div>
          <div class="guide-description">
            <p>不同模型针对不同场景优化，选择合适的模型能获得更好的效果</p>
          </div>
          <div class="guide-grid">
            <!-- RealWorldSR - 主推模型，放在首位 -->
            <div class="guide-card realworld recommended" :class="{ active: srModelType === 'realworld' }" @click="srModelType = 'realworld'">
              <div class="recommended-badge">⭐ 主推</div>
              <div class="guide-header">
                <div class="guide-name">真实世界图像</div>
                <div class="guide-subname">RealWorldSR</div>
              </div>
              <div class="guide-description-text">
                <p>绝大部分情况通用 - 复杂退化</p>
                <p class="sub-text">真实照片、模糊文本、老照片、监控截图</p>
              </div>
            </div>
            
            <div class="guide-card classical" :class="{ active: srModelType === 'classical' }" @click="srModelType = 'classical'">
              <div class="guide-header">
                <div class="guide-name">经典超分辨率</div>
                <div class="guide-subname">ClassicalSR</div>
              </div>
              <div class="guide-description-text">
                <p>理想图片 - 高质量扫描件</p>
                <p class="sub-text">本身质量很高，需要强力锐化</p>
              </div>
            </div>
            
            <div class="guide-card compressed" :class="{ active: srModelType === 'compressed' }" @click="srModelType = 'compressed'">
              <div class="guide-header">
                <div class="guide-name">压缩图像恢复</div>
                <div class="guide-subname">CompressedSR</div>
              </div>
              <div class="guide-description-text">
                <p>网络压缩图 - 有损压缩图片</p>
                <p class="sub-text">JPEG 压缩、网络传图、小尺寸图</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 参数调节区域（移到图片预览下方） -->
        <div v-if="file" class="parameter-section">
          <!-- 超分倍数选择 -->
          <div class="field">
            <label class="label">超分倍数 <span class="required">*</span></label>
            <select v-model="srScale" class="model-select">
              <!-- 所有模型都只推荐使用 X4 -->
              <option value="4">X4 - 标准超分（推荐使用）</option>
            </select>
            <div class="scale-info">
              <span class="scale-badge">单阶段：X4</span>
            </div>
          </div>
        </div>

        <!-- 文字优化选项 -->
        <div class="field">
          <label class="checkbox-label">
            <input type="checkbox" v-model="enableTextOptimization" class="checkbox" />
            <span class="checkbox-text">
              启用文字优化
              <span class="checkbox-hint">针对文档/文字图像进行后处理增强，提升 OCR 识别效果</span>
            </span>
          </label>
        </div>

          <!-- 智能推荐面板 -->
          <div v-if="showRecommendation && recommendation" class="recommendation-panel">
            <div class="recommendation-header">
              <div class="recommendation-title">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="rec-icon">
                  <path d="M9.66347 16.9612C11.133 18.372 12.5339 18.9973 13.5999 18.9973C15.2209 18.9973 16.4261 17.6628 16.9526 16.2898C17.0938 15.9226 17.6153 15.8285 17.8812 16.0944L19.2954 17.5086C19.5613 17.7745 19.4672 18.296 19.1 18.4372C17.3294 19.1175 15.4491 19.4973 13.5999 19.4973C11.9256 19.4973 10.2567 18.9973 8.79394 17.9973C7.33115 16.9973 6.13379 15.6628 5.33344 14.1612C5.12735 13.775 5.33344 13.3226 5.73344 13.1612L7.59994 12.4112C7.99994 12.2512 8.44994 12.4973 8.59994 12.9112L9.66347 16.9612Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M12 15V3M12 3L8 7M12 3L16 7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span>智能推荐配置</span>
              </div>
              <button class="close-rec" @click="showRecommendation = false">×</button>
            </div>
            
            <div class="recommendation-content">
              <div class="rec-main">
                <div class="rec-item">
                  <span class="rec-label">推荐模型：</span>
                  <span class="rec-value model-tag">{{ recommendation.recommended_model_name }}</span>
                </div>
                <div class="rec-item">
                  <span class="rec-label">推荐倍数：</span>
                  <span class="rec-value scale-tag">X{{ recommendation.recommended_scale }}</span>
                </div>
                <div class="rec-item">
                  <span class="rec-label">置信度：</span>
                  <span class="rec-value confidence">{{ (recommendation.confidence * 100).toFixed(0) }}%</span>
                </div>
                <div class="rec-item">
                  <span class="rec-label">级联配置：</span>
                  <span class="rec-value">{{ recommendation.cascade_description }}</span>
                </div>
              </div>
              
              <div class="rec-reason">
                <div class="reason-title">推荐理由</div>
                <div class="reason-text">{{ recommendation.recommendation_reason }}</div>
              </div>
              
              <!-- 备选方案 -->
              <div v-if="recommendation.alternative_recommendations && recommendation.alternative_recommendations.length > 0" class="rec-alternatives">
                <div class="alternatives-title">备选方案</div>
                <div class="alternatives-list">
                  <div 
                    v-for="(alt, index) in recommendation.alternative_recommendations" 
                    :key="index"
                    class="alternative-item"
                    @click="selectAlternative(alt)"
                  >
                    <span class="alt-model">{{ alt.model_name }}</span>
                    <span class="alt-scale">X{{ alt.scale }}</span>
                    <span class="alt-reason">{{ alt.reason }}</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="recommendation-actions">
              <button class="btn ghost" @click="resetToDefault">使用默认参数</button>
              <button class="btn primary" @click="closeRecommendationPanel">
                确认使用
              </button>
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
            {{ loading ? "处理中..." : "开始修复" }}
          </button>
        </div>
      </form>

      <div v-if="result" class="result-section">
        <div class="result-header">
          <div class="result-title">处理结果</div>
        </div>

        <div v-if="originalPreviewUrl && repairedImageBase64" class="comparison-container" ref="comparisonContainer">
          <!-- 原图 -->
          <div class="comparison-original">
            <img 
              class="comparison-image"
              :src="croppedImageBase64 || originalPreviewUrl" 
              alt="原图" 
            />
          </div>
          <!-- 修复后 -->
          <div class="comparison-repaired">
            <img 
              class="comparison-image"
              :src="`data:image/png;base64,${repairedImageBase64}`" 
              alt="修复后" 
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
          <div class="version-label right-label">修复后</div>
        </div>

        <div class="stats-grid">
          <div class="info-card">
            <div class="info-label">原始尺寸</div>
            <div class="info-value">{{ result.original_size || 'N/A' }}</div>
          </div>
          <div class="info-card">
            <div class="info-label">修复后尺寸</div>
            <div class="info-value">{{ result.enhanced_size || 'N/A' }}</div>
          </div>
          <div class="info-card">
            <div class="info-label">处理时间</div>
            <div class="info-value">{{ (result.process_time || 0).toFixed(3) }}s</div>
          </div>
          <div class="info-card">
            <div class="info-label">放大倍数</div>
            <div class="info-value">{{ result.scale || '4' }}x</div>
          </div>
        </div>

        <div class="actions">
          <button
            class="btn primary"
            type="button"
            :disabled="downloading"
            @click="downloadResult"
          >
            {{ downloading ? "下载中..." : "下载修复后的图片" }}
          </button>
        </div>

        <!-- 链式工作流功能 -->
        <div class="workflow-section">
          <div class="workflow-title">链式工作流</div>
          <div class="workflow-buttons">
            <button
              class="btn primary"
              type="button"
              @click="goToComparison"
            >
              查看修复效果综合对比
            </button>
          </div>
          <div class="workflow-hint">
            点击上方按钮，将自动跳转至相应模块并携带当前修复结果数据
          </div>
        </div>

        <div class="next-actions">
          <div class="actions-title">其他后续操作</div>
          <div class="actions-container">
            <router-link to="/app/ocr-processing" class="btn ghost" style="text-decoration: none">
              进行OCR识别
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
import { onMounted, ref, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { API_BASE } from "../api/base";
import ImageCropper from '../components/ImageCropper.vue';

const router = useRouter();
const token = ref<string | null>(localStorage.getItem("token"));

const srModelType = ref("realworld"); // 默认使用 RealWorldSR（主推）
const srScale = ref("4"); // 默认 X4
const enableTextOptimization = ref(false); // 默认不启用文字优化
const file = ref<File | null>(null);
const loading = ref(false);
const downloading = ref(false);
const recommending = ref(false); // 推荐中

const formError = ref("");
const formOk = ref("");

// 智能推荐相关
const recommendation = ref<any>(null);
const showRecommendation = ref(false);

const result = ref<any>(null);
const originalPreviewUrl = ref("");
const repairedImageBase64 = ref("");
const originalImageBase64 = ref("");

const applyingRec = ref(false); // 应用推荐中

const fileInput = ref<HTMLInputElement | null>(null);

// 拖拽状态
const isDragging = ref(false);

const progress = ref(0);
const progressText = ref("");

// 裁剪相关
const showCropper = ref(false);
const croppedImageBase64 = ref("");
const cropInfo = ref<{x: number, y: number, width: number, height: number} | null>(null);

// 滑块对比相关
const sliderPosition = ref(50);
const comparisonContainer = ref<HTMLElement | null>(null);

function resetPage() {
  formError.value = "";
  formOk.value = "";
  result.value = null;
  originalPreviewUrl.value = "";
  repairedImageBase64.value = "";
  originalImageBase64.value = "";
  file.value = null;
  loading.value = false;  // 停止加载状态
  srModelType.value = "realworld"; // 重置为默认推荐模型
  srScale.value = "4";
  sliderPosition.value = 50;
  isDragging.value = false;
  progress.value = 0;
  progressText.value = "";
  recommendation.value = null;
  showRecommendation.value = false;
  applyingRec.value = false;
  showCropper.value = false;
  croppedImageBase64.value = "";
  cropInfo.value = null;
  comparisonContainer.value = null;
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
  console.log('[ImageRepair] onDragOver triggered', e.target);
  e.preventDefault();
  e.stopPropagation();
  // 设置拖拽效果
  if (e.dataTransfer) {
    e.dataTransfer.dropEffect = 'copy';
  }
  isDragging.value = true;
  console.log('[ImageRepair] isDragging set to true');
}

function onDragLeave(e: DragEvent) {
  console.log('[ImageRepair] onDragLeave triggered', e.target);
  // 只有当鼠标离开整个上传区域时才重置状态
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
  const x = e.clientX;
  const y = e.clientY;
  if (x < rect.left || x >= rect.right || y < rect.top || y >= rect.bottom) {
    e.preventDefault();
    e.stopPropagation();
    isDragging.value = false;
    console.log('[ImageRepair] isDragging set to false');
  }
}

function onDrop(e: DragEvent) {
  console.log('[ImageRepair] onDrop triggered', e.target);
  e.preventDefault();
  e.stopPropagation();
  isDragging.value = false;
  console.log('[ImageRepair] isDragging set to false');
  
  const files = e.dataTransfer?.files;
  console.log('[ImageRepair] Files in drop event:', files);
  
  if (files && files.length > 0) {
    console.log('[ImageRepair] Number of files:', files.length);
    const f = files[0];
    console.log('[ImageRepair] File:', f);
    console.log('[ImageRepair] File type:', f.type);
    
    if (f.type.startsWith('image/')) {
      console.log('[ImageRepair] Image file detected');
      file.value = f;
      originalPreviewUrl.value = URL.createObjectURL(f);
      console.log('[ImageRepair] File preview URL created:', originalPreviewUrl.value);
      
      // 转换原始图片为 base64
      const reader = new FileReader();
      reader.onload = (e) => {
        const base64 = e.target?.result as string;
        // 去掉 data:image/xxx;base64, 前缀
        originalImageBase64.value = base64.split(',')[1];
        console.log('[ImageRepair] Base64 conversion completed');
        
        // 获取智能推荐并自动应用
        getRecommendationAndAutoApply();
      };
      reader.readAsDataURL(f);
    } else {
      console.log('[ImageRepair] Non-image file detected');
      formError.value = '请上传图片文件！';
    }
  } else {
    console.log('[ImageRepair] No files in drop event');
  }
}

// 保存修复结果到 localStorage，供其他模块使用
function saveRepairResult() {
  // 如果有裁剪后的图片，使用裁剪后的图片作为原图
  const effectiveOriginalImage = croppedImageBase64.value || originalImageBase64.value;
  
  if (!effectiveOriginalImage || !repairedImageBase64.value) return;
  
  const repairData = {
    originalImage: effectiveOriginalImage,
    repairedImage: repairedImageBase64.value,
    srModelType: srModelType.value,
    hasCropped: !!croppedImageBase64.value,
    cropInfo: cropInfo.value,
    timestamp: Date.now()
  };
  
  localStorage.setItem('repair_result', JSON.stringify(repairData));
  console.log('[ImageRepair] 修复结果已保存到 localStorage', {
    hasCropped: !!croppedImageBase64.value,
    originalImageSize: effectiveOriginalImage.length,
    repairedImageSize: repairedImageBase64.value.length
  });
}

// 跳转到修复效果综合对比页面
function goToComparison() {
  saveRepairResult();
  
  // 确保使用最新的数据（从 result 对象中获取）
  // 如果有裁剪后的图片，使用裁剪后的图片作为原图
  // 注意：croppedImageBase64 是完整 data URL，originalImageBase64 是纯 base64
  let effectiveOriginalImage = croppedImageBase64.value;
  if (!effectiveOriginalImage && originalImageBase64.value) {
    // 如果没有裁剪，使用原始图片（需要添加前缀）
    effectiveOriginalImage = `data:image/png;base64,${originalImageBase64.value}`;
  }
  
  // 传递图片数据到综合对比页面
  sessionStorage.setItem('repair_original_image', effectiveOriginalImage);
  // 修复后的图片也是纯 base64，需要添加前缀
  const repairedImageFull = repairedImageBase64.value 
    ? `data:image/png;base64,${repairedImageBase64.value}` 
    : '';
  sessionStorage.setItem('repair_repaired_image', repairedImageFull);
  
  // 优先使用 result 中的数据（确保是最新的）
  const ocrTextToSave = (result.value && result.value.ocr_text) || '';
  const filledTextToSave = (result.value && result.value.completed_text) || '';
  
  console.log('[ImageRepair] 保存链式工作流数据:', {
    hasOcrText: !!ocrTextToSave,
    hasFilledText: !!filledTextToSave,
    ocrTextLength: ocrTextToSave?.length,
    filledTextLength: filledTextToSave?.length
  });
  
  sessionStorage.setItem('repair_ocr_text', ocrTextToSave);
  sessionStorage.setItem('repair_filled_text', filledTextToSave);
  
  // 传递裁剪信息
  if (cropInfo.value) {
    sessionStorage.setItem('repair_crop_info', JSON.stringify(cropInfo.value));
  }
  // 传递任务 ID（如果有）- task_id 可能是字符串或数字
  if (result.value && result.value.task_id) {
    console.log('[跳转] 保存 task_id:', result.value.task_id, '类型:', typeof result.value.task_id);
    sessionStorage.setItem('repair_task_id', result.value.task_id.toString());
  }
  router.push('/app/repair-comparison');
}

// 获取智能推荐并自动应用
async function getRecommendationAndAutoApply() {
  if (!file.value) {
    console.warn('[ImageRepair] 文件为空，跳过推荐');
    return;
  }
  
  // 先清空之前的推荐
  recommendation.value = null;
  showRecommendation.value = false;
  
  // 检查 token
  if (!token.value) {
    console.warn('[ImageRepair] 用户未登录，显示推荐面板让用户手动选择');
    showRecommendation.value = true;
    return;
  }
  
  recommending.value = true;
  formError.value = "";
  
  try {
    const fd = new FormData();
    fd.append("file", file.value);
    
    console.log('[ImageRepair] 正在获取智能推荐...');
    
    const res = await fetch(`${API_BASE}/sr/recommend/`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token.value}`,
      },
      body: fd,
      credentials: "omit",
    });
    
    console.log('[ImageRepair] 推荐请求响应状态:', res.status);
    
    if (!res.ok) {
      const errorText = await res.text();
      console.error('[ImageRepair] 推荐请求失败:', res.status, errorText);
      throw new Error(`推荐请求失败：${res.status}`);
    }
    
    const data = await res.json();
    recommendation.value = data.recommendation || data;
    
    console.log('[ImageRepair] 推荐结果:', recommendation.value);
    console.log('[ImageRepair] 置信度:', recommendation.value?.confidence);
    
    // 自动应用推荐配置
    console.log('[ImageRepair] 自动应用推荐配置');
    applyRecommendation(true);
    
    // 显示推荐面板，让用户可以看到推荐了什么，也可以选择不使用
    showRecommendation.value = true;
  } catch (e) {
    console.error('[ImageRepair] 推荐失败:', e);
    formError.value = e instanceof Error ? e.message : "获取推荐失败";
    // 即使失败也显示推荐面板，让用户手动选择
    showRecommendation.value = true;
  } finally {
    recommending.value = false;
  }
}

// 应用推荐配置
function applyRecommendation(silent: boolean = false) {
  if (!recommendation.value) return;
  
  applyingRec.value = true;
  
  // 应用推荐的模型和倍数
  const modelMap: Record<string, string> = {
    'ClassicalSR': 'classical',
    'CompressedSR': 'compressed',
    'RealWorldSR': 'realworld'
  };
  
  srModelType.value = modelMap[recommendation.value.recommended_model_name] || 'realworld';
  srScale.value = recommendation.value.recommended_scale.toString();
  
  console.log('[ImageRepair] 已应用推荐配置:', {
    model: srModelType.value,
    scale: srScale.value
  });
  
  applyingRec.value = false;
  
  if (!silent) {
    formOk.value = "已应用智能推荐配置，可点击开始修复";
    
    // 3 秒后清除提示信息
    setTimeout(() => {
      formOk.value = "";
    }, 3000);
  }
}

// 关闭推荐面板（不改变已应用的参数）
function closeRecommendationPanel() {
  showRecommendation.value = false;
}

// 重置为默认参数
function resetToDefault() {
  srModelType.value = 'realworld'; // 重置为默认推荐模型
  srScale.value = '4';
  showRecommendation.value = false;
  formOk.value = "已重置为默认参数";
  
  setTimeout(() => {
    formOk.value = "";
  }, 3000);
}

// 选择备选方案
function selectAlternative(alt: any) {
  console.log('[ImageRepair] 选择备选方案:', alt);
  
  const modelMap: Record<string, string> = {
    'ClassicalSR': 'classical',
    'CompressedSR': 'compressed',
    'RealWorldSR': 'realworld'
  };
  
  // 优先使用 model_name，如果没有则使用 model
  const modelName = alt.model_name || alt.model;
  const modelKey = modelMap[modelName] || alt.model || 'classical';
  
  console.log('[ImageRepair] 映射结果:', {
    modelName,
    modelKey,
    scale: alt.scale
  });
  
  srModelType.value = modelKey;
  srScale.value = alt.scale.toString();
  
  showRecommendation.value = false;
  formOk.value = `已选择备选方案：${modelName} X${alt.scale}`;
  
  setTimeout(() => {
    formOk.value = "";
  }, 3000);
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
  
  // 裁剪后重新获取智能推荐
  setTimeout(() => {
    getRecommendationAndAutoApply();
    formOk.value = `已裁剪图片，正在重新推荐模型...`;
  }, 500);
  
  setTimeout(() => {
    formOk.value = "";
  }, 3000);
}

function handleCropCancel() {
  showCropper.value = false;
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement;
  const f = input.files?.[0] ?? null;
  file.value = f;
  originalPreviewUrl.value = f ? URL.createObjectURL(f) : "";
  
  // 清除裁剪缓存
  croppedImageBase64.value = "";
  cropInfo.value = null;
  
  // 转换原始图片为 base64
  if (f) {
    const reader = new FileReader();
    reader.onload = (e) => {
      const base64 = e.target?.result as string;
      // 去掉 data:image/xxx;base64, 前缀
      originalImageBase64.value = base64.split(',')[1];
      console.log('[ImageRepair] Base64 conversion completed');
      
      // 获取智能推荐并自动应用
      getRecommendationAndAutoApply();
    };
    reader.readAsDataURL(f);
  }
}

async function onRepair() {
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
  progressText.value = "准备处理...";

  // 添加超时控制（5 分钟）
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 300000);

  const progressInterval = setInterval(() => {
    progress.value += 5;
    if (progress.value < 30) {
      progressText.value = "正在加载模型...";
    } else if (progress.value < 60) {
      progressText.value = "正在执行超分辨率处理...";
    } else if (progress.value < 90) {
      progressText.value = "正在生成结果...";
    } else if (progress.value >= 95) {
      progress.value = 95; // 保持在 95% 等待完成
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
      console.log('[ImageRepair] 使用裁剪后的图片进行修复');
    } else if (file.value) {
      fd.append("file", file.value);
    }
    
    fd.append("sr_model_type", srModelType.value);
    fd.append("sr_scale", srScale.value);
    fd.append("use_super_resolution", "true");
    fd.append("enable_text_optimization", enableTextOptimization.value ? "true" : "false");

    console.log(`[ImageRepair] 开始修复，模型：${srModelType.value}，倍数：X${srScale.value}`);

    const res = await fetch(`${API_BASE}/doc/repair`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token.value}`,
      },
      body: fd,
      credentials: "omit",
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    clearInterval(progressInterval);

    const data = await res.json();
    
    if (!res.ok) {
      throw new Error(data?.detail || "处理请求失败");
    }

    progress.value = 100;
    progressText.value = "处理完成！";

    result.value = data;
    // 从 meta 中获取超分信息
    if (data.meta && data.meta.super_resolution) {
      result.value.original_size = data.meta.super_resolution.original_size;
      result.value.enhanced_size = data.meta.super_resolution.enhanced_size;
      result.value.process_time = data.meta.super_resolution.process_time;
      result.value.scale = data.meta.super_resolution.scale_factor || data.meta.super_resolution.scale;
    }
    if (data.repaired_image_base64) {
      repairedImageBase64.value = data.repaired_image_base64.replace(/\s/g, "");
    }

    formOk.value = "图片修复完成！";
  } catch (e) {
    clearInterval(progressInterval);
    clearTimeout(timeoutId);
    
    if (e instanceof Error && e.name === 'AbortError') {
      formError.value = "处理超时，图片可能较大，请稍后重试";
    } else {
      formError.value = e instanceof Error ? e.message : "处理失败，请稍后重试。";
    }
    console.error('[ImageRepair] 处理失败:', e);
  } finally {
    loading.value = false;
  }
}

async function downloadResult() {
  if (!repairedImageBase64.value) return;
  downloading.value = true;
  try {
    const link = document.createElement("a");
    link.href = `data:image/png;base64,${repairedImageBase64.value}`;
    link.download = `repaired_image_${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    formOk.value = "下载完成！";
  } catch (e) {
    formError.value = "下载失败，请稍后重试。";
  } finally {
    downloading.value = false;
  }
}

// 初始化滑块位置
function initSliderPosition() {
  if (comparisonContainer.value) {
    comparisonContainer.value.style.setProperty('--slider-position', `${sliderPosition.value}%`);
  }
}

// 滑块对比函数
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

// 页面加载时初始化
onMounted(() => {
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
  max-width: 1000px;
  background: rgba(17, 24, 39, 0.85);
  border-radius: 12px;
  padding: 32px;
  border: 1px solid rgba(0, 255, 136, 0.12);
  backdrop-filter: blur(10px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.card:hover {
  border-color: rgba(0, 255, 136, 0.2);
  background: rgba(17, 24, 39, 0.9);
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
  letter-spacing: -0.02em;
  line-height: 1.2;
  text-transform: uppercase;
  letter-spacing: 0.5px;
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

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  cursor: pointer;
  padding: 16px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(0, 255, 136, 0.15);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.checkbox-label:hover {
  background: rgba(15, 23, 42, 0.8);
  border-color: rgba(0, 255, 136, 0.3);
}

.checkbox {
  width: 20px;
  height: 20px;
  margin-top: 2px;
  cursor: pointer;
  accent-color: var(--primary);
}

.checkbox-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.checkbox-hint {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: normal;
  line-height: 1.5;
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

.required {
  color: var(--error);
  font-weight: 800;
}

.model-select {
  width: 100%;
  max-width: 300px;
  padding: 16px 20px;
  border: 1px solid rgba(0, 255, 136, 0.12);
  border-radius: 12px;
  font-size: 14px;
  color: var(--text);
  background: rgba(15, 23, 42, 0.95);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-family: inherit;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 16px center;
  background-size: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.model-select:hover {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(0, 255, 136, 0.08), 0 6px 24px rgba(0, 255, 136, 0.1);
  transform: translateY(-2px);
}

.model-select:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(0, 255, 136, 0.1), 0 6px 24px rgba(0, 255, 136, 0.15);
}

/* 自定义下拉菜单样式 */
.model-select option {
  background: #0f1419;
  color: var(--text);
  padding: 12px;
  border: none;
  font-family: inherit;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  transition: all 0.3s ease;
}

.scale-info {
  margin-top: 12px;
  padding: 12px 16px;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(0, 255, 136, 0.15);
  border-radius: 8px;
  min-height: 44px;
  display: flex;
  align-items: center;
  transition: all 0.3s ease;
}

.model-limit-hint {
  margin-top: 12px;
  padding: 12px 16px;
  background: rgba(255, 191, 0, 0.05);
  border: 1px solid rgba(255, 191, 0, 0.2);
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: rgba(255, 191, 0, 0.9);
}

.hint-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

/* 智能推荐面板样式 */
.recommendation-panel {
  margin: 24px 0;
  padding: 24px;
  background: rgba(0, 255, 136, 0.05);
  border: 1px solid rgba(0, 255, 136, 0.3);
  border-radius: 12px;
  box-shadow: 0 0 30px rgba(0, 255, 136, 0.1);
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.recommendation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(0, 255, 136, 0.15);
}

.recommendation-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 700;
  color: var(--primary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.rec-icon {
  width: 24px;
  height: 24px;
  filter: drop-shadow(0 0 10px rgba(0, 255, 136, 0.3));
}

.close-rec {
  width: 32px;
  height: 32px;
  border: 1px solid rgba(0, 255, 136, 0.2);
  background: rgba(17, 24, 39, 0.95);
  color: var(--primary);
  border-radius: 8px;
  font-size: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.close-rec:hover {
  background: rgba(0, 255, 136, 0.1);
  border-color: var(--primary);
  transform: rotate(90deg);
}

.recommendation-content {
  display: grid;
  gap: 20px;
}

.rec-main {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  padding: 16px;
  background: rgba(17, 24, 39, 0.95);
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 136, 0.15);
}

.rec-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rec-label {
  font-size: 12px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.rec-value {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
}

.model-tag {
  color: var(--primary);
  text-shadow: 0 0 10px rgba(0, 255, 136, 0.2);
}

.scale-tag {
  color: var(--primary);
  background: rgba(0, 255, 136, 0.1);
  padding: 4px 12px;
  border-radius: 4px;
  display: inline-block;
  border: 1px solid rgba(0, 255, 136, 0.2);
}

.confidence {
  color: #00ff88;
  font-weight: 800;
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
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.reason-text {
  font-size: 14px;
  color: var(--text);
  line-height: 1.6;
}

.rec-alternatives {
  padding: 16px;
  background: rgba(15, 23, 42, 0.6);
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 136, 0.1);
}

.alternatives-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.alternatives-list {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.alternative-item {
  flex: 1;
  min-width: 180px;
  padding: 12px 16px;
  background: rgba(17, 24, 39, 0.95);
  border: 1px solid rgba(0, 255, 136, 0.15);
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.alternative-item:hover {
  border-color: var(--primary);
  background: rgba(0, 255, 136, 0.08);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 255, 136, 0.15);
}

.alt-model {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  flex: 1;
}

.alt-scale {
  font-size: 14px;
  font-weight: 700;
  color: var(--primary);
  background: rgba(0, 255, 136, 0.1);
  padding: 4px 10px;
  border-radius: 4px;
  border: 1px solid rgba(0, 255, 136, 0.2);
}

.alt-reason {
  font-size: 11px;
  color: var(--text-secondary);
  flex: 2;
  text-align: right;
}

.recommendation-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
  justify-content: flex-end;
}

.scale-info:hover {
  border-color: var(--primary);
  background: rgba(0, 255, 136, 0.05);
}

.scale-badge {
  padding: 6px 16px;
  background: rgba(0, 255, 136, 0.1);
  color: var(--primary);
  border: 1px solid rgba(0, 255, 136, 0.3);
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(0, 255, 136, 0.1);
}

.scale-badge.scale-complex {
  background: rgba(0, 255, 136, 0.15);
  border-color: rgba(0, 255, 136, 0.5);
  box-shadow: 0 4px 12px rgba(0, 255, 136, 0.2);
}

.model-select option:hover {
  background: rgba(0, 255, 136, 0.15);
  color: var(--primary);
  box-shadow: 0 2px 8px rgba(0, 255, 136, 0.1);
}

.model-select option:checked {
  background: rgba(0, 255, 136, 0.2);
  color: var(--primary);
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(0, 255, 136, 0.15);
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
  margin-bottom: 20px;
  color: var(--primary);
  transition: all 0.3s ease;
}

.upload-icon svg {
  width: 32px;
  height: 32px;
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
}

.file-info {
  flex: 1;
  min-width: 0;
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
}

.file-size {
  font-size: 12px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
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

/* 参数调节区域样式 */
.parameter-section {
  margin-top: 32px;
  padding: 24px;
  background: rgba(17, 24, 39, 0.6);
  border: 1px solid rgba(0, 255, 136, 0.15);
  border-radius: 12px;
  animation: fadeIn 0.4s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.parameter-section .field {
  margin-bottom: 20px;
}

.parameter-section .field:last-child {
  margin-bottom: 0;
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

/* 对比预览 */
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

.workflow-section {
  margin-top: 24px;
  padding: 24px;
  background: rgba(0, 255, 136, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 136, 0.15);
  position: relative;
}

.workflow-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--primary), transparent);
  opacity: 0.3;
}

.workflow-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--primary);
  margin-bottom: 16px;
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.workflow-buttons {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 16px;
  justify-content: center;
}

.workflow-hint {
  font-size: 13px;
  color: var(--text-secondary);
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  line-height: 1.4;
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

/* 模型选择指南样式 */
.model-guide {
  margin: 24px 0;
  padding: 24px;
  background: rgba(15, 23, 42, 0.8);
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 136, 0.15);
  position: relative;
}

.model-guide::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--primary), transparent);
  opacity: 0.3;
}

.guide-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 12px;
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.guide-description {
  text-align: center;
  margin-bottom: 20px;
}

.guide-description p {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
}

.guide-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.guide-card {
  background: rgba(17, 24, 39, 0.95);
  border: 1px solid rgba(0, 255, 136, 0.1);
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.guide-card:hover {
  border-color: var(--primary);
  background: rgba(0, 255, 136, 0.05);
  box-shadow: 0 6px 24px rgba(0, 255, 136, 0.15);
  transform: translateY(-2px);
}

.guide-card.active {
  border-color: var(--primary);
  background: rgba(0, 255, 136, 0.08);
  box-shadow: 0 0 0 1px var(--primary), 
              0 6px 24px rgba(0, 255, 136, 0.15);
}

.guide-card.classical.active {
  border-color: #00d4ff;
  box-shadow: 0 0 0 1px #00d4ff, 0 6px 24px rgba(0, 212, 255, 0.2);
}

.guide-card.compressed.active {
  border-color: #ff6b6b;
  box-shadow: 0 0 0 1px #ff6b6b, 0 6px 24px rgba(255, 107, 107, 0.2);
}

.guide-card.realworld.active {
  border-color: #00ff88;
  box-shadow: 0 0 0 1px #00ff88, 0 6px 24px rgba(0, 255, 136, 0.2);
}

/* 主推卡片样式 - RealWorldSR 绿色 */
.guide-card.recommended {
  position: relative;
  border-color: #00ff88;
  background: rgba(0, 255, 136, 0.05);
}

.guide-card.recommended:hover {
  border-color: #00ff88;
  background: rgba(0, 255, 136, 0.08);
  box-shadow: 0 6px 24px rgba(0, 255, 136, 0.2);
}

.guide-card.recommended.active {
  border-color: #00ff88;
  background: rgba(0, 255, 136, 0.1);
  box-shadow: 0 0 0 1px #00ff88, 0 6px 24px rgba(0, 255, 136, 0.25);
}

.recommended-badge {
  position: absolute;
  top: -10px;
  right: 16px;
  background: linear-gradient(135deg, #00ff88 0%, #00d4a8 100%);
  color: white;
  font-size: 11px;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 255, 136, 0.4);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.guide-header {
  margin-bottom: 16px;
}

.guide-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 6px;
}

.guide-subname {
  font-size: 11px;
  color: var(--text-secondary);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.guide-description-text {
  margin-top: 12px;
}

.guide-description-text p {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 6px 0;
  line-height: 1.6;
}

.guide-description-text .sub-text {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
  opacity: 0.8;
}

.guide-scenes {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
  text-align: left;
}

.scene-tag {
  font-size: 11px;
  padding: 6px 10px;
  background: rgba(0, 255, 136, 0.08);
  color: var(--primary);
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 4px;
}

.scene-tag:hover {
  background: rgba(0, 255, 136, 0.15);
  border-color: var(--primary);
  box-shadow: 0 2px 8px rgba(0, 255, 136, 0.1);
  transform: translateY(-1px);
}

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
  
  .model-select {
    max-width: 100%;
  }
  
  .actions {
    flex-direction: column;
  }
  
  .actions .btn {
    width: 100%;
  }
  
  .comparison-container {
    height: 350px;
    max-width: 100%;
  }
  
  .slider-handle {
    width: 48px;
    height: 48px;
  }
  
  .slider-button svg {
    width: 18px;
    height: 18px;
  }
  
  .version-label {
    font-size: 12px;
    padding: 8px 16px;
  }
  
  .guide-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .workflow-buttons {
    flex-direction: column;
  }
  
  .workflow-buttons .btn {
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
  
  .recommendation-panel {
    padding: 16px;
  }
  
  .rec-main {
    grid-template-columns: 1fr;
  }
  
  .alternatives-list {
    flex-direction: column;
  }
  
  .alternative-item {
    width: 100%;
  }
  
  .recommendation-actions {
    flex-direction: column;
  }
  
  .recommendation-actions .btn {
    width: 100%;
  }
}
</style>
