<template>
  <div class="image-cropper">
    <div class="cropper-header" v-if="showHeader">
      <div class="header-title">
        <svg viewBox="0 0 24 24" fill="none" class="crop-icon">
          <path d="M6 2L2 6V18L6 22H18L22 18V6L18 2H6Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M6 10H18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M10 6V18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>裁剪图片</span>
      </div>
      <div class="header-actions">
        <button class="btn-icon" @click="resetCrop" title="重置裁剪">
          <svg viewBox="0 0 24 24" fill="none">
            <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M3 3v5h5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
        <button class="btn-icon" @click="cancelCrop" title="取消裁剪">
          <svg viewBox="0 0 24 24" fill="none">
            <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
        <button class="btn-primary btn-sm" @click="confirmCrop">
          <svg viewBox="0 0 24 24" fill="none" class="btn-icon-sm">
            <path d="M5 13l4 4L19 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          确认裁剪
        </button>
      </div>
    </div>

    <div class="cropper-container" ref="container">
      <!-- 图片容器 -->
      <div 
        class="image-wrapper"
        :style="{
          transform: `scale(${zoom})`,
          transformOrigin: 'center center'
        }"
      >
        <img 
          :src="imageSrc" 
          alt="可裁剪图片"
          class="crop-image"
          draggable="false"
          @load="onImageLoad"
        />
      </div>
      
      <!-- 裁剪框（移到外部，不受 zoom 影响） -->
      <div 
        class="crop-box-wrapper"
        :style="{
          left: imageOffsetX + 'px',
          top: imageOffsetY + 'px',
          width: (imageWidth * zoom) + 'px',
          height: (imageHeight * zoom) + 'px'
        }"
      >
        <div 
          class="crop-box"
          :style="{
            left: (cropBox.x * zoom) + 'px',
            top: (cropBox.y * zoom) + 'px',
            width: (cropBox.width * zoom) + 'px',
            height: (cropBox.height * zoom) + 'px'
          }"
          @mousedown.stop="startCropBoxDrag"
          @touchstart.stop="startCropBoxDrag"
        >
          <!-- 裁剪框边角 -->
          <div class="crop-handle crop-handle-nw" @mousedown.stop="resizeCropBox('nw', $event)"></div>
          <div class="crop-handle crop-handle-ne" @mousedown.stop="resizeCropBox('ne', $event)"></div>
          <div class="crop-handle crop-handle-sw" @mousedown.stop="resizeCropBox('sw', $event)"></div>
          <div class="crop-handle crop-handle-se" @mousedown.stop="resizeCropBox('se', $event)"></div>
          
          <!-- 裁剪框边 -->
          <div class="crop-handle crop-handle-n" @mousedown.stop="resizeCropBox('n', $event)"></div>
          <div class="crop-handle crop-handle-s" @mousedown.stop="resizeCropBox('s', $event)"></div>
          <div class="crop-handle crop-handle-e" @mousedown.stop="resizeCropBox('e', $event)"></div>
          <div class="crop-handle crop-handle-w" @mousedown.stop="resizeCropBox('w', $event)"></div>
          
          <!-- 九宫格辅助线 -->
          <div class="crop-grid" style="pointer-events: none;">
            <div class="grid-line grid-line-v"></div>
            <div class="grid-line grid-line-v"></div>
            <div class="grid-line grid-line-h"></div>
            <div class="grid-line grid-line-h"></div>
          </div>
        </div>
      </div>
      
      <!-- 缩放控制 -->
      <div class="zoom-controls">
        <button class="zoom-btn" @click="zoomOut" :disabled="zoom <= 0.5">
          <svg viewBox="0 0 24 24" fill="none">
            <path d="M20 20l-4.35-4.35M16 10a6 6 0 1 1-12 0 6 6 0 0 1 12 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M8 10h4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
        <span class="zoom-value">{{ Math.round(zoom * 100) }}%</span>
        <button class="zoom-btn" @click="zoomIn" :disabled="zoom >= 3">
          <svg viewBox="0 0 24 24" fill="none">
            <path d="M20 20l-4.35-4.35M16 10a6 6 0 1 1-12 0 6 6 0 0 1 12 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M10 8v4M8 10h4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
        <button class="zoom-btn" @click="fitImage" title="适应屏幕">
          <svg viewBox="0 0 24 24" fill="none">
            <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- 裁剪信息 -->
    <div class="crop-info">
      <div class="info-item">
        <span class="info-label">裁剪区域:</span>
        <span class="info-value">{{ cropInfo }}</span>
      </div>
      <div class="info-item" v-if="originalSize">
        <span class="info-label">原始尺寸:</span>
        <span class="info-value">{{ originalSize.width }} × {{ originalSize.height }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';

const props = defineProps<{
  imageSrc: string;
  showHeader?: boolean;
  aspectRatio?: number; // 可选的宽高比限制
}>();

const emit = defineEmits<{
  (e: 'crop', cropData: {
    x: number;
    y: number;
    width: number;
    height: number;
    croppedImageBase64: string;
  }): void;
  (e: 'cancel'): void;
}>();

// 容器和图片相关
const container = ref<HTMLElement | null>(null);
const imageWidth = ref(0);
const imageHeight = ref(0);
const originalSize = ref<{ width: number; height: number } | null>(null);
const imageOffsetX = ref(0);
const imageOffsetY = ref(0);

// 缩放和平移
const zoom = ref(1);

// 裁剪框
const cropBox = ref({
  x: 100,
  y: 100,
  width: 200,
  height: 200
});

// 拖拽状态
const isResizing = ref(false);
const dragStart = ref({ x: 0, y: 0 });
const cropBoxStart = ref({ x: 0, y: 0, width: 0, height: 0 });
const resizeHandle = ref('');

// 裁剪信息
const cropInfo = computed(() => {
  if (!originalSize.value) return '';
  const scaleX = originalSize.value.width / imageWidth.value;
  const scaleY = originalSize.value.height / imageHeight.value;
  
  const x = Math.round(cropBox.value.x * scaleX);
  const y = Math.round(cropBox.value.y * scaleY);
  const width = Math.round(cropBox.value.width * scaleX);
  const height = Math.round(cropBox.value.height * scaleY);
  
  return `${x}, ${y}, ${width} × ${height}`;
});

// 图片加载完成
function onImageLoad(e: Event) {
  const img = e.target as HTMLImageElement;
  
  // 使用显示尺寸（CSS 渲染后的尺寸），而不是原始尺寸
  // 因为后续所有计算都是基于显示尺寸的
  imageWidth.value = img.width;
  imageHeight.value = img.height;
  originalSize.value = { width: img.naturalWidth, height: img.naturalHeight };
  
  // 先适应屏幕，计算 zoom
  fitImage();
  
  // 初始化裁剪框为整张图片（从 0,0 开始，覆盖整个显示尺寸）
  // 此时 imageWidth 和 imageHeight 已经是显示尺寸，不需要再乘以 zoom
  cropBox.value = {
    x: 0,
    y: 0,
    width: imageWidth.value,
    height: imageHeight.value
  };
  
  console.log('[ImageCropper] 初始化裁剪框:', {
    imageDisplaySize: { width: imageWidth.value, height: imageHeight.value },
    imageNaturalSize: { width: img.naturalWidth, height: img.naturalHeight },
    zoom: zoom.value,
    cropBox: cropBox.value
  });
}

// 适应屏幕
function fitImage() {
  if (!container.value || !imageWidth.value || !imageHeight.value) return;
  
  const containerRect = container.value.getBoundingClientRect();
  // 计算缩放比例，使图片适应容器
  const scaleX = containerRect.width / imageWidth.value;
  const scaleY = containerRect.height / imageHeight.value;
  // 使用 0.9 作为安全边距，确保图片完全可见
  zoom.value = Math.min(scaleX, scaleY) * 0.9;
  
  // 计算图片在容器中的居中偏移量
  const scaledWidth = imageWidth.value * zoom.value;
  const scaledHeight = imageHeight.value * zoom.value;
  imageOffsetX.value = (containerRect.width - scaledWidth) / 2;
  imageOffsetY.value = (containerRect.height - scaledHeight) / 2;
  
  console.log('[ImageCropper] fitImage:', {
    containerSize: { width: containerRect.width, height: containerRect.height },
    imageSize: { width: imageWidth.value, height: imageHeight.value },
    scaleX, scaleY,
    zoom: zoom.value,
    imageOffset: { x: imageOffsetX.value, y: imageOffsetY.value }
  });
}

// 缩放控制
function zoomIn() {
  zoom.value = Math.min(zoom.value + 0.1, 3);
}

function zoomOut() {
  zoom.value = Math.max(zoom.value - 0.1, 0.5);
}

// 拖拽裁剪框
function startCropBoxDrag(e: MouseEvent | TouchEvent) {
  // 如果点击的是手柄，不处理（手柄有独立的事件）
  if ((e.target as HTMLElement).closest('.crop-handle')) return;
  
  e.preventDefault();
  e.stopPropagation();
  
  isResizing.value = true;
  resizeHandle.value = '';
  const clientX = 'touches' in e ? e.touches[0].clientX : (e as MouseEvent).clientX;
  const clientY = 'touches' in e ? e.touches[0].clientY : (e as MouseEvent).clientY;
  dragStart.value = { x: clientX, y: clientY };
  cropBoxStart.value = { ...cropBox.value };
}

function onCropBoxDrag(e: MouseEvent | TouchEvent) {
  if (!isResizing.value || resizeHandle.value) return;
  
  const clientX = 'touches' in e ? e.touches[0].clientX : (e as MouseEvent).clientX;
  const clientY = 'touches' in e ? e.touches[0].clientY : (e as MouseEvent).clientY;
  
  const dx = (clientX - dragStart.value.x) * 0.5;  // 灵敏度减半
  const dy = (clientY - dragStart.value.y) * 0.5;  // 灵敏度减半
  
  let newX = cropBoxStart.value.x + dx;
  let newY = cropBoxStart.value.y + dy;
  
  // 边界检查 - 确保裁剪框不会移出图片
  // imageWidth 和 imageHeight 已经是显示尺寸
  const displayWidth = imageWidth.value;
  const displayHeight = imageHeight.value;
  
  // 使用当前的实际宽度
  const currentWidth = cropBox.value.width;
  const currentHeight = cropBox.value.height;
  
  // 限制左边界和上边界（不能小于 0）
  newX = Math.max(0, newX);
  newY = Math.max(0, newY);
  
  // 限制右边界和下边界（不能超出图片）
  // 裁剪框的右边界 = newX + width，必须 <= displayWidth
  // 所以 newX <= displayWidth - width
  const maxRightX = displayWidth - currentWidth;
  const maxBottomY = displayHeight - currentHeight;
  
  newX = Math.min(newX, maxRightX);
  newY = Math.min(newY, maxBottomY);
  
  // 双重检查：确保右边界和下边界不超出（防止精度问题）
  const rightEdge = newX + currentWidth;
  const bottomEdge = newY + currentHeight;
  
  if (rightEdge > displayWidth) {
    newX = displayWidth - currentWidth;
  }
  if (bottomEdge > displayHeight) {
    newY = displayHeight - currentHeight;
  }
  
  // 最终检查：确保不会小于 0
  newX = Math.max(0, newX);
  newY = Math.max(0, newY);
  
  cropBox.value.x = newX;
  cropBox.value.y = newY;
}

// 调整裁剪框大小
function resizeCropBox(handle: string, e: MouseEvent) {
  e.stopPropagation();
  e.preventDefault();
  
  isResizing.value = true;
  resizeHandle.value = handle;
  dragStart.value = { x: e.clientX, y: e.clientY };
  cropBoxStart.value = { ...cropBox.value };
}

function onResize(e: MouseEvent) {
  if (!isResizing.value || !resizeHandle.value) return;
  
  const dx = (e.clientX - dragStart.value.x) * 0.5;  // 灵敏度减半
  const dy = (e.clientY - dragStart.value.y) * 0.5;  // 灵敏度减半
  
  let box = { ...cropBoxStart.value };
  // imageWidth 和 imageHeight 已经是显示尺寸，不需要再乘以 zoom
  const maxX = imageWidth.value;  // 图片右边界
  const maxY = imageHeight.value; // 图片下边界
  
  // 调整东边（右边）
  if (resizeHandle.value === 'e' || resizeHandle.value === 'ne' || resizeHandle.value === 'se') {
    // 新宽度 = 原宽度 + 移动距离
    let newWidth = box.width + dx;
    
    // 限制：不能小于最小宽度
    newWidth = Math.max(50, newWidth);
    
    // 限制：右边不能超出图片（newWidth <= maxX - box.x）
    const maxPossibleWidth = maxX - box.x;
    newWidth = Math.min(newWidth, maxPossibleWidth);
    
    // 只有当宽度发生变化时才更新
    if (Math.abs(newWidth - box.width) > 0.1) {
      box.width = newWidth;
    }
  }
  
  // 调整西边（左边）
  if (resizeHandle.value === 'w' || resizeHandle.value === 'nw' || resizeHandle.value === 'sw') {
    // 向右拖（dx > 0）：左边向右移动，x 增加，宽度减小
    // 向左拖（dx < 0）：左边向左移动，x 减小，宽度增加
    let newX = box.x + dx;
    let newWidth = box.width - dx;
    
    // 限制：左边界不能小于 0
    newX = Math.max(0, newX);
    
    // 限制：右边界不能超出图片（newX + newWidth <= maxX）
    if (newX + newWidth > maxX) {
      newWidth = maxX - newX;
    }
    
    // 限制：不能小于最小宽度
    newWidth = Math.max(50, newWidth);
    
    // 更新裁剪框
    box.x = newX;
    box.width = newWidth;
  }
  
  // 调整南边（下边）
  if (resizeHandle.value === 's' || resizeHandle.value === 'se' || resizeHandle.value === 'sw') {
    // 新高度 = 原高度 + 移动距离
    let newHeight = box.height + dy;
    
    // 限制：不能小于最小高度
    newHeight = Math.max(50, newHeight);
    
    // 限制：下边不能超出图片（newHeight <= maxY - box.y）
    const maxPossibleHeight = maxY - box.y;
    newHeight = Math.min(newHeight, maxPossibleHeight);
    
    box.height = newHeight;
  }
  
  // 调整北边（上边）
  if (resizeHandle.value === 'n' || resizeHandle.value === 'ne' || resizeHandle.value === 'nw') {
    // 向下拖（dy > 0）：上边向下移动，y 增加，高度减小
    // 向上拖（dy < 0）：上边向上移动，y 减小，高度增加
    let newY = box.y + dy;
    let newHeight = box.height - dy;
    
    // 限制：上边界不能小于 0
    newY = Math.max(0, newY);
    
    // 限制：下边界不能超出图片（newY + newHeight <= maxY）
    if (newY + newHeight > maxY) {
      newHeight = maxY - newY;
    }
    
    // 限制：不能小于最小高度
    newHeight = Math.max(50, newHeight);
    
    // 更新裁剪框
    box.y = newY;
    box.height = newHeight;
  }
  
  // 保持宽高比（如果设置了）
  if (props.aspectRatio) {
    const targetWidth = box.height * props.aspectRatio;
    const targetHeight = box.width / props.aspectRatio;
    
    if (resizeHandle.value.includes('e') || resizeHandle.value.includes('w')) {
      box.height = targetHeight;
    } else {
      box.width = targetWidth;
    }
  }
  
  // ========== 最终边界检查 - 确保裁剪框完全在图片范围内 ==========
  // 1. 首先确保最小尺寸
  box.width = Math.max(50, box.width);
  box.height = Math.max(50, box.height);
  
  // 2. 确保裁剪框不会超出右边界和下边界
  // 如果宽度超出，优先调整 x 位置（向左移动），而不是缩小宽度
  const rightEdge = box.x + box.width;
  if (rightEdge > maxX) {
    // 尝试向左移动
    box.x = maxX - box.width;
  }
  
  const bottomEdge = box.y + box.height;
  if (bottomEdge > maxY) {
    // 尝试向上移动
    box.y = maxY - box.height;
  }
  
  // 3. 确保左/上边界不小于 0
  // 如果位置小于 0，说明裁剪框太大，需要缩小
  if (box.x < 0) {
    box.x = 0;
    box.width = Math.min(box.width, maxX);  // 缩小到不超过图片宽度
  }
  
  if (box.y < 0) {
    box.y = 0;
    box.height = Math.min(box.height, maxY);  // 缩小到不超过图片高度
  }
  
  // 4. 最终检查：确保右/下边界不超出（双重保险）
  box.width = Math.min(box.width, maxX - box.x);
  box.height = Math.min(box.height, maxY - box.y);
  
  // 5. 再次确保最小尺寸（如果图片本身很小）
  box.width = Math.max(Math.min(50, maxX), box.width);
  box.height = Math.max(Math.min(50, maxY), box.height);
  
  cropBox.value = box;
}

function stopResize() {
  isResizing.value = false;
  resizeHandle.value = '';
}

// 重置裁剪
function resetCrop() {
  // 重置 zoom 为 1
  zoom.value = 1;
  
  // 在显示尺寸基础上重置裁剪框（覆盖整张图片）
  // imageWidth 和 imageHeight 已经是显示尺寸
  cropBox.value = {
    x: 0,
    y: 0,
    width: imageWidth.value,
    height: imageHeight.value
  };
}

// 取消裁剪
function cancelCrop() {
  emit('cancel');
}

// 确认裁剪
function confirmCrop() {
  if (!originalSize.value || !container.value) return;
  
  // 计算相对于原始图片的裁剪区域
  // cropBox.value 是相对于显示图片（未缩放状态）的坐标
  // 需要转换为原始图片的坐标
  const scaleX = originalSize.value.width / imageWidth.value;
  const scaleY = originalSize.value.height / imageHeight.value;
  
  // cropBox.value 已经是显示尺寸的坐标，直接乘以缩放比例得到原始图片的坐标
  const cropX = Math.round(cropBox.value.x * scaleX);
  const cropY = Math.round(cropBox.value.y * scaleY);
  const cropWidth = Math.round(cropBox.value.width * scaleX);
  const cropHeight = Math.round(cropBox.value.height * scaleY);
  
  console.log('[ImageCropper] 裁剪参数:', {
    cropBox: cropBox.value,
    zoom: zoom.value,
    originalSize: originalSize.value,
    displaySize: { width: imageWidth.value, height: imageHeight.value },
    scaleX, scaleY,
    cropX, cropY, cropWidth, cropHeight
  });
  
  // 创建 canvas 裁剪图片
  const canvas = document.createElement('canvas');
  canvas.width = cropWidth;
  canvas.height = cropHeight;
  const ctx = canvas.getContext('2d');
  
  if (!ctx) return;
  
  const img = new Image();
  img.crossOrigin = 'anonymous';
  img.src = props.imageSrc;
  
  img.onload = () => {
    console.log('[ImageCropper] 图片加载成功，开始裁剪:', {
      imgSize: { width: img.width, height: img.height },
      cropParams: { x: cropX, y: cropY, width: cropWidth, height: cropHeight }
    });
    
    try {
      ctx.drawImage(
        img,
        cropX, cropY, cropWidth, cropHeight,
        0, 0, cropWidth, cropHeight
      );
      
      const croppedImageBase64 = canvas.toDataURL('image/png');
      
      console.log('[ImageCropper] 裁剪完成，base64 长度:', croppedImageBase64.length);
      
      emit('crop', {
        x: cropX,
        y: cropY,
        width: cropWidth,
        height: cropHeight,
        croppedImageBase64
      });
    } catch (error) {
      console.error('[ImageCropper] 裁剪失败:', error);
      alert('裁剪失败，请检查裁剪区域是否超出图片范围');
    }
  };
  
  img.onerror = () => {
    console.error('[ImageCropper] 图片加载失败');
    alert('图片加载失败，请重试');
  };
}

// 事件监听 - 使用 AbortController 优雅管理事件生命周期
let abortController: AbortController | null = null;

const setupEventListeners = () => {
  // 创建新的 AbortController
  abortController = new AbortController();
  const { signal } = abortController;
  
  // 使用 signal 添加事件监听器
  document.addEventListener('mousemove', handleDocumentMove, { signal, passive: false });
  document.addEventListener('mouseup', handleDocumentUp, { signal });
  document.addEventListener('touchmove', handleDocumentMove, { signal, passive: false });
  document.addEventListener('touchend', handleDocumentUp, { signal });
};

const removeEventListeners = () => {
  // 调用 abort() 一次性取消所有关联的监听器
  if (abortController) {
    abortController.abort();
    abortController = null;
  }
};

const handleDocumentMove = (e: MouseEvent | TouchEvent) => {
  if (!isResizing.value) return;
  
  if (resizeHandle.value) {
    onResize(e as MouseEvent);
  } else {
    onCropBoxDrag(e);
  }
};

const handleDocumentUp = () => {
  stopResize();
};

// 监听 isResizing 和 resizeHandle，动态管理事件监听器
let isListening = false;

const watchCleanup = watch([isResizing, resizeHandle], ([isResizingVal, resizeHandleVal]) => {
  if (isResizingVal) {
    // 开始调整时添加监听器
    if (!isListening) {
      removeEventListeners(); // 先清理旧的
      setupEventListeners();
      isListening = true;
    }
  } else if (!resizeHandleVal) {
    // 停止调整时移除监听器
    removeEventListeners();
    isListening = false;
  }
}, { immediate: true });

onUnmounted(() => {
  // 组件卸载时清理
  watchCleanup();
  removeEventListeners();
});
</script>

<style scoped>
.image-cropper {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 600px;
  background: rgba(17, 24, 39, 0.95);
  border-radius: 12px;
  overflow: hidden;
}

.cropper-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: rgba(15, 23, 42, 0.95);
  border-bottom: 1px solid rgba(0, 255, 136, 0.15);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 700;
  color: var(--primary);
}

.crop-icon {
  width: 20px;
  height: 20px;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.btn-icon {
  width: 32px;
  height: 32px;
  border: 1px solid rgba(0, 255, 136, 0.2);
  background: rgba(17, 24, 39, 0.95);
  color: var(--text);
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.btn-icon:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: rgba(0, 255, 136, 0.05);
}

.btn-primary {
  padding: 8px 16px;
  background: var(--primary);
  color: #000;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  box-shadow: 0 0 15px rgba(0, 255, 136, 0.3);
}

.btn-sm {
  font-size: 13px;
  padding: 6px 12px;
}

.btn-icon-sm {
  width: 14px;
  height: 14px;
}

.cropper-container {
  flex: 1;
  min-height: 500px;
  position: relative;
  overflow: hidden;
  background: #0a0a0a;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-wrapper {
  position: relative;
  transform-origin: center center;
  transition: transform 0.1s ease-out;
}

.crop-image {
  display: block;
  max-width: none;
  user-select: none;
  pointer-events: none;
}

.crop-box-wrapper {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
}

.crop-box {
  position: absolute;
  border: 2px solid var(--primary);
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.5);
  cursor: move;
  pointer-events: all;
}

.crop-handle {
  position: absolute;
  width: 10px;
  height: 10px;
  background: var(--primary);
  border: 1px solid rgba(0, 0, 0, 0.5);
}

.crop-handle-nw { top: -5px; left: -5px; cursor: nw-resize; }
.crop-handle-ne { top: -5px; right: -5px; cursor: ne-resize; }
.crop-handle-sw { bottom: -5px; left: -5px; cursor: sw-resize; }
.crop-handle-se { bottom: -5px; right: -5px; cursor: se-resize; }

.crop-handle-n { top: -5px; left: 50%; transform: translateX(-50%); cursor: n-resize; }
.crop-handle-s { bottom: -5px; left: 50%; transform: translateX(-50%); cursor: s-resize; }
.crop-handle-e { right: -5px; top: 50%; transform: translateY(-50%); cursor: e-resize; }
.crop-handle-w { left: -5px; top: 50%; transform: translateY(-50%); cursor: w-resize; }

.crop-grid {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.grid-line {
  position: absolute;
  background: rgba(255, 255, 255, 0.3);
}

.grid-line-v {
  width: 1px;
  height: 100%;
  left: 33.33%;
}

.grid-line-v:last-child {
  left: 66.66%;
}

.grid-line-h {
  height: 1px;
  width: 100%;
  top: 33.33%;
}

.grid-line-h:last-child {
  top: 66.66%;
}

.zoom-controls {
  position: absolute;
  bottom: 20px;
  right: 20px;
  display: flex;
  gap: 8px;
  align-items: center;
  background: rgba(17, 24, 39, 0.95);
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 136, 0.2);
}

.zoom-btn {
  width: 32px;
  height: 32px;
  border: 1px solid rgba(0, 255, 136, 0.2);
  background: rgba(17, 24, 39, 0.95);
  color: var(--text);
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.zoom-btn:hover:not(:disabled) {
  border-color: var(--primary);
  color: var(--primary);
}

.zoom-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.zoom-btn svg {
  width: 16px;
  height: 16px;
}

.zoom-value {
  min-width: 50px;
  text-align: center;
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}

.crop-info {
  padding: 12px 20px;
  background: rgba(15, 23, 42, 0.95);
  border-top: 1px solid rgba(0, 255, 136, 0.15);
  display: flex;
  gap: 20px;
  font-size: 13px;
}

.info-item {
  display: flex;
  gap: 8px;
}

.info-label {
  color: var(--text-secondary);
  font-weight: 600;
}

.info-value {
  color: var(--primary);
  font-weight: 700;
}

@media (max-width: 768px) {
  .cropper-header {
    padding: 12px 16px;
  }
  
  .header-title {
    font-size: 14px;
  }
  
  .crop-icon {
    width: 18px;
    height: 18px;
  }
  
  .btn-icon {
    width: 28px;
    height: 28px;
  }
  
  .btn-primary {
    padding: 6px 12px;
    font-size: 12px;
  }
  
  .btn-icon-sm {
    width: 12px;
    height: 12px;
  }
  
  .crop-handle {
    width: 14px;
    height: 14px;
  }
  
  .crop-handle-nw, .crop-handle-ne, .crop-handle-sw, .crop-handle-se {
    width: 14px;
    height: 14px;
  }
  
  .zoom-controls {
    bottom: 12px;
    right: 12px;
    padding: 6px 10px;
  }
  
  .zoom-btn {
    width: 28px;
    height: 28px;
  }
  
  .zoom-value {
    min-width: 45px;
    font-size: 12px;
  }
  
  .crop-info {
    padding: 10px 16px;
    font-size: 12px;
    flex-direction: column;
    gap: 8px;
  }
}

/* 模态框样式 */
.cropper-modal-wrapper {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.cropper-modal-wrapper .image-cropper {
  width: 100%;
  max-width: 1200px;
  height: 80vh;
  min-height: 600px;
}
</style>
