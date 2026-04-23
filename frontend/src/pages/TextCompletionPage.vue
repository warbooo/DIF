<template>
  <div class="page">
    <div class="card">
      <div class="card-header">
        <h1 class="title">大模型语义补全</h1>
        <p class="subtitle">
          上传识别的文本，使用大语言模型智能补全缺失文字
        </p>
      </div>

      <form @submit.prevent="onCompletion">
        <div class="field">
          <label class="label">输入文本</label>
          <div class="text-input-container">
            <textarea
              v-model="inputText"
              class="textarea"
              placeholder="请输入需要补全的文本，缺失的文字可以用 □、■、_、? 等符号标记..."
              @input="handleTextInput"
            ></textarea>
            <div class="input-overlay">
              <div class="input-toolbar">
                <span class="toolbar-item char-counter">
                  <span class="counter-label">字符数:</span>
                  <span class="counter-value">{{ inputText.length }}</span>
                </span>
                <span class="toolbar-item hint-text">
                  支持 □、■、_、? 等标记
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="field">
          <label class="label">补全选项</label>
          <div class="options-container">
            <label class="option-item">
              <input type="checkbox" v-model="useLLM" class="checkbox" />
              <span class="option-text">使用大语言模型</span>
            </label>
            <label class="option-item">
              <input type="checkbox" v-model="enableSpellCorrection" class="checkbox" />
              <span class="option-text">先纠错再补全（MacBERT）</span>
            </label>
          </div>
        </div>

        <!-- 功能说明 -->
        <div class="feature-info">
          <div class="info-title">功能说明</div>
          <div class="info-grid">
            <div class="info-item">
              <div class="info-icon">LLM</div>
              <div class="info-content">
                <div class="info-heading">大语言模型</div>
                <div class="info-description">智能理解上下文，补全缺失内容</div>
              </div>
            </div>
            <div class="info-item">
              <div class="info-icon">NLP</div>
              <div class="info-content">
                <div class="info-heading">MacBERT 纠错</div>
                <div class="info-description">自动检测并纠正拼写错误</div>
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
          <button class="btn primary" type="submit" :disabled="loading || !inputText.trim()">
            {{ loading ? "补全中..." : "开始补全" }}
          </button>
        </div>
      </form>

      <div v-if="result" class="result-section">
        <div class="result-header">
          <div class="result-title">补全结果</div>
        </div>

        <!-- 纠错后文本展示（如果有） -->
        <div v-if="result.corrected_text" class="corrected-section">
          <div class="section-title">拼写纠错后（MacBERT）</div>
          <textarea
            :value="result.corrected_text"
            readonly
            class="result-textarea corrected"
          ></textarea>
        </div>

        <div class="completed-section">
          <div class="section-title">补全文本</div>
          <textarea
            v-model="resultText"
            class="result-textarea completed"
          ></textarea>
        </div>

        <!-- 执行步骤展示 -->
        <div v-if="result.steps && result.steps.length > 0" class="steps-section">
          <div class="section-title">执行步骤</div>
          <div class="steps-container">
            <span
              v-for="(step, index) in result.steps"
              :key="index"
              class="step-item"
            >
              <span class="step-label">
                {{ getStepName(step) }}
              </span>
              <span v-if="Number(index) < result.steps.length - 1" class="step-arrow">→</span>
            </span>
          </div>
        </div>

        <div class="actions">
          <button
            class="btn primary"
            type="button"
            :disabled="downloading"
            @click="downloadText"
          >
            {{ downloading ? "下载中..." : "下载补全文本" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { API_BASE } from "../api/base";

const token = ref<string | null>(localStorage.getItem("token"));

const useLLM = ref(true);
const enableSpellCorrection = ref(false);
const inputText = ref("");
const loading = ref(false);
const downloading = ref(false);

const formError = ref("");
const formOk = ref("");

const result = ref<any>(null);
const resultText = ref("");

const progress = ref(0);
const progressText = ref("");
const inputTextLength = ref(0);

function handleTextInput() {
  inputTextLength.value = inputText.value.length;
  // 可以在这里添加其他文本输入相关的逻辑
}

// 检查并加载从图片修复页面传递过来的数据
function checkAndLoadPassedData() {
  try {
    const ocrText = sessionStorage.getItem('repair_ocr_text');
    const filledText = sessionStorage.getItem('repair_filled_text');
    
    if (ocrText) {
      inputText.value = ocrText;
      formOk.value = "已加载图片修复后的 OCR 识别文本";
      
      // 清除 sessionStorage 中的数据，避免重复加载
      sessionStorage.removeItem('repair_ocr_text');
      sessionStorage.removeItem('repair_filled_text');
    }
  } catch (e) {
    console.error('[TextCompletion] 加载传递数据失败:', e);
  }
}

onMounted(() => {
  checkAndLoadPassedData();
});

function getStepName(step: string): string {
  const stepNames: Record<string, string> = {
    'spell_correction': '拼写纠错',
    'llm_completion': 'LLM补全',
    'rule_completion': '规则补全'
  };
  return stepNames[step] || step;
}

function resetPage() {
  formError.value = "";
  formOk.value = "";
  result.value = null;
  resultText.value = "";
  inputText.value = "";
  useLLM.value = true;
  enableSpellCorrection.value = false;
  progress.value = 0;
  progressText.value = "";
}

async function onCompletion() {
  if (!token.value) {
    formError.value = "未登录，请返回登录页。";
    return;
  }
  if (!inputText.value.trim()) {
    formError.value = "请先输入文本。";
    return;
  }

  formError.value = "";
  formOk.value = "";
  loading.value = true;
  progress.value = 0;
  
  if (enableSpellCorrection.value) {
    progressText.value = "正在加载MacBERT拼写纠错模型（首次使用可能需要几秒）...";
  } else {
    progressText.value = "准备补全...";
  }

  const progressInterval = setInterval(() => {
    progress.value += 3;
    if (enableSpellCorrection.value && progress.value < 30) {
      progressText.value = "正在进行MacBERT拼写纠错...";
    } else if (progress.value < 50) {
      progressText.value = "正在分析上下文...";
    } else if (progress.value < 80) {
      progressText.value = "正在智能补全...";
    } else if (progress.value < 95) {
      progressText.value = "正在生成结果...";
    }
  }, 300);

  try {
    const authToken = token.value;
    const res = await fetch(`${API_BASE}/text/complete`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${authToken}`,
      },
      body: JSON.stringify({
        text: inputText.value,
        use_llm: useLLM.value,
        enable_spell_correction: enableSpellCorrection.value,
      }),
    });

    const data = await res.json();
    
    if (!res.ok) {
      throw new Error(data?.detail || "补全请求失败");
    }

    progress.value = 100;
    progressText.value = "补全完成！";

    result.value = data;
    resultText.value = data.completed_text || "";

    formOk.value = "语义补全完成！";
  } catch (e) {
    formError.value = e instanceof Error ? e.message : "补全失败，请稍后重试。";
  } finally {
    clearInterval(progressInterval);
    loading.value = false;
  }
}

async function downloadText() {
  if (!resultText.value) return;
  downloading.value = true;
  try {
    const blob = new Blob([resultText.value], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `completed_text_${Date.now()}.txt`;
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

.label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.text-input-container {
  position: relative;
  width: 100%;
}

.textarea {
  width: 100%;
  min-height: 250px;
  resize: vertical;
  padding: 20px;
  padding-bottom: 60px; /* 为工具栏留出空间 */
  border: 1px solid rgba(0, 255, 136, 0.15);
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
  background: rgba(15, 23, 42, 0.8);
  color: var(--text);
  font-family: inherit;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
  z-index: 1;
  position: relative;
}

.textarea:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(0, 255, 136, 0.1),
              inset 0 2px 4px rgba(0, 0, 0, 0.2);
  transform: translateY(-1px);
}

.textarea::placeholder {
  color: var(--text-secondary);
  opacity: 0.6;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.input-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 2;
  pointer-events: none;
}

.input-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: linear-gradient(180deg, transparent, rgba(17, 24, 39, 0.95));
  border-bottom-left-radius: 12px;
  border-bottom-right-radius: 12px;
  pointer-events: all;
  backdrop-filter: blur(10px);
  border-top: 1px solid rgba(0, 255, 136, 0.1);
  transition: all 0.3s ease;
}

.toolbar-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.char-counter {
  color: var(--text-secondary);
}

.counter-label {
  font-weight: 500;
  opacity: 0.8;
}

.counter-value {
  font-weight: 700;
  color: var(--primary);
  background: rgba(0, 255, 136, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid rgba(0, 255, 136, 0.2);
}

.toolbar-divider {
  width: 1px;
  height: 20px;
  background: rgba(0, 255, 136, 0.2);
  margin: 0 16px;
}

.hint-text {
  color: var(--text-secondary);
  opacity: 0.8;
  font-style: italic;
}

.char-count {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-align: right;
  display: none; /* 隐藏旧的字符计数器，使用新的工具栏 */
}

.options-container {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  margin-top: 12px;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 12px 16px;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid var(--border);
  border-radius: 8px;
  transition: all 0.3s ease;
  flex: 1;
  min-width: 200px;
}

.option-item:hover {
  border-color: var(--primary);
  background: rgba(0, 255, 136, 0.05);
  box-shadow: 0 0 0 3px rgba(0, 255, 136, 0.1);
}

.checkbox {
  width: 20px;
  height: 20px;
  accent-color: var(--primary);
  cursor: pointer;
}

.option-text {
  font-size: 14px;
  color: var(--text);
  font-weight: 500;
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

.corrected-section {
  margin-bottom: 24px;
}

.completed-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.result-textarea {
  width: 100%;
  min-height: 150px;
  padding: 16px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
  font-family: inherit;
  transition: all 0.3s ease;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
}

.result-textarea.corrected {
  background: rgba(0, 255, 136, 0.05);
  border-color: rgba(0, 255, 136, 0.3);
  color: var(--text);
}

.result-textarea.completed {
  background: rgba(15, 23, 42, 0.8);
  border-color: var(--border);
  color: var(--text);
  resize: vertical;
}

.result-textarea:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(0, 255, 136, 0.1),
              inset 0 2px 4px rgba(0, 0, 0, 0.2);
}

.steps-section {
  margin-top: 24px;
  padding: 20px;
  background: rgba(15, 23, 42, 0.8);
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 136, 0.1);
}

.steps-container {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 12px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.step-label {
  padding: 8px 16px;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: var(--text);
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 4px 12px rgba(0, 255, 136, 0.15);
}

.step-arrow {
  color: var(--text-secondary);
  font-size: 20px;
  font-weight: 300;
}

.feature-info {
  margin: 24px 0;
  padding: 20px;
  background: rgba(15, 23, 42, 0.8);
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 136, 0.15);
  position: relative;
}

.feature-info::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--primary), transparent);
  opacity: 0.3;
}

.info-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 16px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-align: center;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.info-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: rgba(17, 24, 39, 0.95);
  border: 1px solid rgba(0, 255, 136, 0.1);
  border-radius: 8px;
  transition: all 0.3s ease;
}

.info-item:hover {
  border-color: var(--primary);
  background: rgba(0, 255, 136, 0.05);
  box-shadow: 0 4px 16px rgba(0, 255, 136, 0.1);
  transform: translateY(-2px);
}

.info-icon {
  font-size: 12px;
  font-weight: 800;
  color: var(--primary);
  text-transform: uppercase;
  letter-spacing: 1px;
  background: rgba(0, 255, 136, 0.08);
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid rgba(0, 255, 136, 0.2);
  display: inline-block;
  flex-shrink: 0;
}

.info-content {
  flex: 1;
}

.info-heading {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-description {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
  text-transform: uppercase;
  letter-spacing: 0.5px;
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
  
  .options-container {
    flex-direction: column;
  }
  
  .option-item {
    width: 100%;
  }
  
  .actions {
    flex-direction: column;
  }
  
  .actions .btn {
    width: 100%;
  }
  
  .steps-container {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .step-item {
    margin-bottom: 8px;
  }
  
  .step-arrow {
    display: none;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .info-item {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  
  .info-icon {
    margin-bottom: 12px;
  }
}
</style>
