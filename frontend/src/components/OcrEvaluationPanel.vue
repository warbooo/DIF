<template>
  <div class="evaluation-panel">
    <h3>OCR 评估结果</h3>
    
    <!-- 输入区域 -->
    <div class="input-section">
      <div class="field">
        <label>OCR识别文本</label>
        <textarea 
          v-model="recognizedText" 
          placeholder="请输入OCR识别的文本..."
          rows="4"
        ></textarea>
      </div>
      
      <div class="field">
        <label>真实文本（标注数据）</label>
        <textarea 
          v-model="groundTruth" 
          placeholder="请输入真实的标注文本..."
          rows="4"
        ></textarea>
      </div>
      
      <button class="btn primary" @click="evaluate" :disabled="loading">
        {{ loading ? '评估中...' : '开始评估' }}
      </button>
    </div>

    <!-- 评估结果 -->
    <div v-if="result" class="result-section">
      <div class="score-card">
        <div class="score-item">
          <div class="score-value" :class="getScoreClass(result.composite_score)">
            {{ (result.composite_score * 100).toFixed(1) }}%
          </div>
          <div class="score-label">综合得分</div>
          <div class="score-level">{{ result.evaluation_level }}</div>
        </div>
      </div>

      <div class="metrics-grid">
        <div class="metric-item">
          <div class="metric-name">字符错误率 (CER)</div>
          <div class="metric-value" :class="getMetricClass(result.cer, true)">
            {{ (result.cer * 100).toFixed(2) }}%
          </div>
          <div class="metric-desc">越低越好</div>
        </div>

        <div class="metric-item">
          <div class="metric-name">词错误率 (WER)</div>
          <div class="metric-value" :class="getMetricClass(result.wer, true)">
            {{ (result.wer * 100).toFixed(2) }}%
          </div>
          <div class="metric-desc">越低越好</div>
        </div>

        <div class="metric-item">
          <div class="metric-name">准确率</div>
          <div class="metric-value" :class="getMetricClass(result.accuracy, false)">
            {{ (result.accuracy * 100).toFixed(2) }}%
          </div>
          <div class="metric-desc">越高越好</div>
        </div>

        <div class="metric-item">
          <div class="metric-name">置信度</div>
          <div class="metric-value" :class="result.confidence > 0 ? getMetricClass(result.confidence, false) : 'neutral'">
            {{ result.confidence > 0 ? (result.confidence * 100).toFixed(2) + '%' : '无数据' }}
          </div>
          <div class="metric-desc">越高越好</div>
        </div>
      </div>

      <!-- 评估说明 -->
      <div class="evaluation-info">
        <h4>评估指标说明</h4>
        <ul>
          <li><strong>CER（字符错误率）</strong>：计算插入、删除、替换的字符数占总字符数的比例，是最重要的指标</li>
          <li><strong>WER（词错误率）</strong>：计算插入、删除、替换的词数占总词数的比例</li>
          <li><strong>准确率</strong>：正确识别的字符数占总字符数的比例</li>
          <li><strong>置信度</strong>：OCR引擎对识别结果的平均置信度</li>
        </ul>
      </div>
    </div>

    <!-- 对比评估 -->
    <div v-if="showCompare" class="compare-section">
      <h3>修复前后对比评估</h3>
      
      <div class="input-section">
        <div class="field">
          <label>修复前OCR文本</label>
          <textarea v-model="beforeText" rows="3"></textarea>
        </div>
        
        <div class="field">
          <label>修复后OCR文本</label>
          <textarea v-model="afterText" rows="3"></textarea>
        </div>
        
        <button class="btn primary" @click="compare" :disabled="loading">
          对比评估
        </button>
      </div>

      <div v-if="compareResult" class="compare-result">
        <div class="improvement-card" :class="{ 'improved': compareResult.is_better }">
          <div class="improvement-title">
            {{ compareResult.is_better ? '修复效果提升' : '修复效果下降' }}
          </div>
          <div class="improvement-value">
            {{ compareResult.improvement_percentage > 0 ? '+' : '' }}
            {{ compareResult.improvement_percentage.toFixed(2) }}%
          </div>
        </div>

        <div class="compare-metrics">
          <div class="compare-metric">
            <span class="label">CER改进：</span>
            <span class="value" :class="{ 'positive': compareResult.improvement.cer_improvement > 0 }">
              {{ compareResult.improvement.cer_improvement > 0 ? '+' : '' }}
              {{ (compareResult.improvement.cer_improvement * 100).toFixed(2) }}%
            </span>
          </div>
          <div class="compare-metric">
            <span class="label">准确率提升：</span>
            <span class="value" :class="{ 'positive': compareResult.improvement.accuracy_improvement > 0 }">
              {{ compareResult.improvement.accuracy_improvement > 0 ? '+' : '' }}
              {{ (compareResult.improvement.accuracy_improvement * 100).toFixed(2) }}%
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { API_BASE } from '../api/base';

const props = defineProps<{
  initialRecognizedText?: string;
  initialConfidences?: number[];
}>();

const recognizedText = ref(props.initialRecognizedText || '');
const groundTruth = ref('');
const beforeText = ref('');
const afterText = ref('');
const loading = ref(false);
const result = ref<any>(null);
const compareResult = ref<any>(null);
const showCompare = ref(false);

// 监听外部传入的识别文本
watch(() => props.initialRecognizedText, (newVal) => {
  if (newVal) {
    recognizedText.value = newVal;
  }
});

async function evaluate() {
  if (!recognizedText.value || !groundTruth.value) {
    alert('请输入OCR识别文本和真实文本');
    return;
  }

  loading.value = true;
  try {
    const requestBody: any = {
      recognized_text: recognizedText.value,
      ground_truth: groundTruth.value
    };
    
    // 如果有置信度数据，传入评估
    if (props.initialConfidences && Array.isArray(props.initialConfidences) && props.initialConfidences.length > 0) {
      requestBody.confidences = props.initialConfidences;
    }
    
    const res = await fetch(`${API_BASE}/ocr/evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    });

    const data = await res.json();
    if (data.success) {
      result.value = data;
    } else {
      alert(data.message);
    }
  } catch (e) {
    alert('评估失败，请稍后重试');
  } finally {
    loading.value = false;
  }
}

async function compare() {
  if (!beforeText.value || !afterText.value || !groundTruth.value) {
    alert('请输入修复前文本、修复后文本和真实文本');
    return;
  }

  loading.value = true;
  try {
    const res = await fetch(`${API_BASE}/ocr/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        before_text: beforeText.value,
        after_text: afterText.value,
        ground_truth: groundTruth.value
      })
    });

    const data = await res.json();
    if (data.success) {
      compareResult.value = data;
    } else {
      alert(data.message);
    }
  } catch (e) {
    alert('对比评估失败，请稍后重试');
  } finally {
    loading.value = false;
  }
}

function getScoreClass(score: number): string {
  if (score >= 0.9) return 'excellent';
  if (score >= 0.8) return 'good';
  if (score >= 0.7) return 'average';
  if (score >= 0.6) return 'poor';
  return 'bad';
}

function getMetricClass(value: number, isLowerBetter: boolean): string {
  if (isLowerBetter) {
    if (value <= 0.1) return 'excellent';
    if (value <= 0.2) return 'good';
    if (value <= 0.3) return 'average';
    return 'poor';
  } else {
    if (value >= 0.9) return 'excellent';
    if (value >= 0.8) return 'good';
    if (value >= 0.7) return 'average';
    return 'poor';
  }
}
</script>

<style scoped>
.evaluation-panel {
  padding: 20px;
  background: #f5f5f5;
  border-radius: 12px;
  margin-top: 20px;
}

.input-section {
  margin-bottom: 20px;
}

.field {
  margin-bottom: 16px;
}

.field label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #333;
}

.field textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  resize: vertical;
}

.score-card {
  text-align: center;
  margin-bottom: 24px;
}

.score-item {
  display: inline-block;
  padding: 24px 48px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.score-value {
  font-size: 48px;
  font-weight: bold;
  margin-bottom: 8px;
}

.score-value.excellent { color: #4caf50; }
.score-value.good { color: #8bc34a; }
.score-value.average { color: #ff9800; }
.score-value.poor { color: #f44336; }
.score-value.bad { color: #9e9e9e; }

.score-label {
  font-size: 16px;
  color: #666;
  margin-bottom: 4px;
}

.score-level {
  font-size: 14px;
  color: #999;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.metric-item {
  background: white;
  padding: 16px;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.1);
}

.metric-name {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 4px;
}

.metric-value.excellent { color: #4caf50; }
.metric-value.good { color: #8bc34a; }
.metric-value.average { color: #ff9800; }
.metric-value.poor { color: #f44336; }
.metric-value.neutral { color: #9e9e9e; }

.metric-desc {
  font-size: 12px;
  color: #999;
}

.evaluation-info {
  background: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 24px;
}

.evaluation-info h4 {
  margin-top: 0;
  margin-bottom: 12px;
  color: #333;
}

.evaluation-info ul {
  margin: 0;
  padding-left: 20px;
}

.evaluation-info li {
  margin-bottom: 8px;
  line-height: 1.5;
  color: #666;
}

.compare-section {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 2px solid #ddd;
}

.improvement-card {
  text-align: center;
  padding: 24px;
  background: #ffebee;
  border-radius: 12px;
  margin-bottom: 16px;
}

.improvement-card.improved {
  background: #e8f5e8;
}

.improvement-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #f44336;
}

.improvement-card.improved .improvement-title {
  color: #4caf50;
}

.improvement-value {
  font-size: 36px;
  font-weight: bold;
  color: #f44336;
}

.improvement-card.improved .improvement-value {
  color: #4caf50;
}

.compare-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.compare-metric {
  background: white;
  padding: 12px 16px;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.compare-metric .label {
  color: #666;
}

.compare-metric .value {
  font-weight: 600;
  color: #f44336;
}

.compare-metric .value.positive {
  color: #4caf50;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn.primary {
  background: #2196f3;
  color: white;
}

.btn.primary:hover:not(:disabled) {
  background: #1976d2;
}
</style>
