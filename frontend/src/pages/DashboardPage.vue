<template>
  <div class="page">
    <div class="dashboard-container">
      <div class="dashboard-header">
        <h1 class="title">数据统计与分析</h1>
        <p class="subtitle">实时监控文档处理系统的运行状态和数据指标</p>
        <button class="btn primary refresh-button" @click="refreshData">
          刷新数据
        </button>
      </div>

      <!-- 第一行：核心指标卡片 -->
      <div class="stats-grid">
        <div class="stat-card primary">
          <div class="stat-icon">
            <div class="icon-content">DOC</div>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.totalTasks }}</div>
            <div class="stat-label">总处理任务</div>
          </div>
        </div>

        <div class="stat-card success">
          <div class="stat-icon">
            <div class="icon-content">OK</div>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.successRate }}%</div>
            <div class="stat-label">成功率</div>
          </div>
        </div>

        <div class="stat-card primary">
          <div class="stat-icon">
            <div class="icon-content">TIME</div>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.avgProcessingTime }}s</div>
            <div class="stat-label">平均处理时间</div>
          </div>
        </div>

        <div class="stat-card info">
          <div class="stat-icon">
            <div class="icon-content">USERS</div>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.activeUsers }}</div>
            <div class="stat-label">活跃用户</div>
          </div>
        </div>
      </div>

      <!-- 第二行：处理量趋势 + 文本补全统计 -->
      <div class="charts-grid">
        <!-- 处理量趋势图 -->
        <div class="chart-card">
          <div class="chart-header">
            <h3>处理量趋势（近 7 天）</h3>
            <select v-model="timeRange" class="chart-select">
              <option value="7">近 7 天</option>
              <option value="30">近 30 天</option>
              <option value="90">近 90 天</option>
            </select>
          </div>
          <div class="chart-body">
            <div class="trend-chart">
              <div
                v-for="(item, index) in processingTrend"
                :key="index"
                class="trend-bar"
                :style="{ height: item.percentage + '%' }"
                :title="`${item.date}: ${item.count} 任务`"
              >
                <span class="bar-value" v-if="item.count > 0">{{ item.count }}</span>
              </div>
            </div>
            <div class="trend-labels">
              <span v-for="(item, index) in processingTrend" :key="index" class="label">
                {{ item.date.slice(5) }}
              </span>
            </div>
          </div>
        </div>

        <!-- 文本补全统计 -->
        <div class="chart-card">
          <div class="chart-header">
            <h3>文本补全统计</h3>
          </div>
          <div class="chart-body">
            <div class="completion-stats">
              <div class="completion-type">
                <div class="completion-type-item">
                  <div class="completion-type-icon">
                    <div class="icon-content">NLP</div>
                  </div>
                  <div class="completion-type-content">
                    <div class="completion-type-value">{{ completionStats.ruleBased }}</div>
                    <div class="completion-type-label">NLP 补全</div>
                  </div>
                </div>
                <div class="completion-type-item">
                  <div class="completion-type-icon">
                    <div class="icon-content">LLM</div>
                  </div>
                  <div class="completion-type-content">
                    <div class="completion-type-value">{{ completionStats.llmBased }}</div>
                    <div class="completion-type-label">LLM 补全</div>
                  </div>
                </div>
              </div>
              <div class="completion-details">
                <div class="completion-detail">
                  <span class="detail-label">成功率</span>
                  <span class="detail-value">{{ completionStats.successRate }}%</span>
                </div>
                <div class="completion-detail">
                  <span class="detail-label">平均耗时</span>
                  <span class="detail-value">{{ completionStats.avgTime }}s</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 第三行：模型使用统计 + 用户满意度统计 -->
      <div class="charts-grid">
        <!-- 模型使用统计 -->
        <div class="chart-card">
          <div class="chart-header">
            <h3>模型使用统计</h3>
          </div>
          <div class="chart-body">
            <div v-if="modelUsage.length === 0" class="empty-message">
              暂无模型使用数据
            </div>
            <div class="model-stats" v-else>
              <div v-for="(model, index) in modelUsage" :key="index" class="model-item">
                <div class="model-header">
                  <span class="model-name">{{ model.name }}</span>
                  <span class="model-count">{{ model.count }} 次</span>
                </div>
                <div class="model-bar">
                  <div class="model-fill" :style="{ width: model.percentage + '%', background: model.color }"></div>
                </div>
                <div class="model-details">
                  <span class="model-detail">成功率：{{ model.successRate }}%</span>
                  <span class="model-detail">平均耗时：{{ model.avgTime }}s</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 用户满意度统计 -->
        <div class="chart-card">
          <div class="chart-header">
            <h3>用户满意度统计</h3>
          </div>
          <div class="chart-body">
            <div v-if="satisfactionStats.totalRatings === 0" class="empty-message">
              暂无用户评价数据
            </div>
            <div v-else class="satisfaction-stats">
                <div class="satisfaction-summary">
                  <div class="summary-item">
                    <div class="summary-icon">
                      <div class="icon-content">RATE</div>
                    </div>
                    <div class="summary-content">
                      <div class="summary-value">{{ satisfactionStats.avgOverall }}</div>
                      <div class="summary-label">综合满意度</div>
                    </div>
                  </div>
                  <div class="summary-item">
                    <div class="summary-icon">
                      <div class="icon-content">TOTAL</div>
                    </div>
                    <div class="summary-content">
                      <div class="summary-value">{{ satisfactionStats.totalRatings }}</div>
                      <div class="summary-label">评价总数</div>
                    </div>
                  </div>
                </div>
                <div class="satisfaction-details">
                  <div v-if="satisfactionStats.starDistribution" class="star-distribution">
                    <div class="star-distribution-header">
                      <h4>星级分布</h4>
                    </div>
                    <div class="star-bars">
                      <div v-for="(count, star) in satisfactionStats.starDistribution" :key="star" class="star-bar">
                        <div class="star-label">{{ star }}星</div>
                        <div class="star-bar-container">
                          <div class="star-bar-fill" :style="{ width: (count / satisfactionStats.totalRatings * 100) + '%', background: 'var(--primary)' }"></div>
                        </div>
                        <div class="star-count">{{ count }}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { API_BASE } from '../api/base';

console.log('DashboardPage.vue 脚本开始执行');

const timeRange = ref('7');
const loading = ref(false);

const stats = ref({
  totalTasks: 0,
  successRate: 0,
  avgProcessingTime: 0,
  activeUsers: 0
});

const modelUsage = ref<Array<{ name: string; count: number; percentage: number; color: string; successRate: number; avgTime: number }>>([]);

const completionStats = ref({
  ruleBased: 0,
  llmBased: 0,
  totalTokens: 0,
  successRate: 0,
  avgTime: 0
});

const processingTrend = ref<Array<{ date: string; count: number; percentage: number }>>([]);

const satisfactionStats = ref({
  totalRatings: 0,
  avgOverall: 0,
  starDistribution: {
    1: 0,
    2: 0,
    3: 0,
    4: 0,
    5: 0
  }
});

console.log('API_BASE:', API_BASE);

function refreshData() {
  console.log('[Dashboard] 手动刷新数据');
  loadDashboardData();
}

// 模拟数据
const mockData = {
  stats: {
    totalTasks: 1250,
    successRate: 98.2,
    avgProcessingTime: 2.5,
    activeUsers: 45
  },
  trend: [
    { date: '2026-03-30', count: 41, percentage: 100 },
    { date: '2026-03-31', count: 34, percentage: 83 },
    { date: '2026-04-01', count: 20, percentage: 49 },
    { date: '2026-04-02', count: 5, percentage: 12 },
    { date: '2026-04-03', count: 1, percentage: 2 },
    { date: '2026-04-04', count: 0, percentage: 0 },
    { date: '2026-04-05', count: 0, percentage: 0 }
  ],
  modelUsage: [
    { name: 'ClassicalSR', count: 450, percentage: 45, color: '#2196f3', successRate: 99.2, avgTime: 2 },
    { name: 'CompressedSR', count: 350, percentage: 35, color: '#4caf50', successRate: 97.8, avgTime: 3 },
    { name: 'RealWorldSR', count: 200, percentage: 20, color: '#ff9800', successRate: 96.5, avgTime: 4 }
  ],
  completionStats: {
    nlpCount: 850,
    llmCount: 400,
    totalTokens: 125000,
    successRate: 95.6,
    avgDuration: 1
  },
  satisfactionStats: {
    totalRatings: 25,
    avgOverall: 4.5,
    starDistribution: {
      1: 1,
      2: 1,
      3: 3,
      4: 10,
      5: 10
    }
  }
};

async function loadDashboardData() {
  console.log('[Dashboard] 开始加载数据');
  loading.value = true;
  try {
    console.log('[Dashboard] API_BASE:', API_BASE);
    console.log('[Dashboard] 请求 URL:', `${API_BASE}/dashboard/stats?days=${timeRange.value}`);

    const res = await fetch(`${API_BASE}/dashboard/stats?days=${timeRange.value}`);

    if (res.ok) {
      const data = await res.json();
      console.log('[Dashboard] 收到数据:', data);
      
      if (data.stats) {
        stats.value = data.stats;
        console.log('[Dashboard] 统计:', stats.value);
      }
      if (data.modelUsage) {
        modelUsage.value = data.modelUsage;
        console.log('[Dashboard] 模型使用:', modelUsage.value);
      }
      if (data.trend) {
        processingTrend.value = data.trend;
        console.log('[Dashboard] 趋势:', processingTrend.value);
      }
      if (data.completionStats) {
        completionStats.value = {
          ruleBased: data.completionStats.nlpCount || 0,
          llmBased: data.completionStats.llmCount || 0,
          totalTokens: data.completionStats.totalTokens || 0,
          successRate: data.completionStats.successRate || 0,
          avgTime: data.completionStats.avgDuration || 0
        };
        console.log('[Dashboard] 补全统计:', completionStats.value);
      }
      if (data.satisfactionStats) {
        satisfactionStats.value = data.satisfactionStats;
        console.log('[Dashboard] 满意度统计:', satisfactionStats.value);
      }
    } else {
      console.error('[Dashboard] 响应状态码:', res.status);
      const errorText = await res.text();
      console.error('[Dashboard] 响应内容:', errorText);
      // 使用模拟数据作为 fallback
      console.log('[Dashboard] 使用模拟数据');
      loadMockData();
    }
  } catch (error) {
    console.error('加载仪表盘数据失败:', error);
    // 使用模拟数据作为 fallback
    console.log('[Dashboard] 使用模拟数据');
    loadMockData();
  } finally {
    loading.value = false;
  }
}

function loadMockData() {
  stats.value = mockData.stats;
  processingTrend.value = mockData.trend;
  modelUsage.value = mockData.modelUsage;
  completionStats.value = {
    ruleBased: mockData.completionStats.nlpCount,
    llmBased: mockData.completionStats.llmCount,
    totalTokens: mockData.completionStats.totalTokens,
    successRate: mockData.completionStats.successRate,
    avgTime: mockData.completionStats.avgDuration
  };
  satisfactionStats.value = mockData.satisfactionStats;
  console.log('[Dashboard] 模拟数据加载完成');
}

watch(timeRange, () => {
  console.log('[Dashboard] 时间范围变化，重新加载数据');
  loadDashboardData();
});

onMounted(() => {
  console.log('[Dashboard] 页面挂载，开始加载数据');
  loadDashboardData();
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
}

.dashboard-container {
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard-header {
  margin-bottom: 32px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 16px;
}

.title {
  font-size: 32px;
  font-weight: 800;
  color: var(--text);
  margin: 0 0 8px 0;
  text-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.subtitle {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.4;
}

/* 核心指标卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 32px;
}

.stat-card {
  background: rgba(17, 24, 39, 0.95);
  border-radius: 12px;
  padding: 28px;
  display: flex;
  align-items: center;
  gap: 24px;
  box-shadow: 0 0 0 1px rgba(0, 255, 136, 0.1), 
              0 8px 32px rgba(0, 0, 0, 0.4);
  border-left: 4px solid var(--primary);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 255, 136, 0.15);
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 0 0 1px rgba(0, 255, 136, 0.2), 
              0 12px 40px rgba(0, 0, 0, 0.5),
              0 0 60px rgba(0, 255, 136, 0.08);
}

.stat-card.primary { border-left-color: var(--primary); }
.stat-card.success { border-left-color: var(--success); }
.stat-card.warning { border-left-color: var(--warning); }
.stat-card.info { border-left-color: var(--secondary); }

.stat-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 255, 136, 0.08);
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 136, 0.2);
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(0, 255, 136, 0.1);
}

.icon-content {
  font-size: 12px;
  font-weight: 800;
  color: var(--primary);
  text-transform: uppercase;
  letter-spacing: 1px;
  text-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 36px;
  font-weight: 800;
  color: var(--text);
  line-height: 1;
  margin-bottom: 8px;
  text-shadow: 0 0 15px rgba(0, 255, 136, 0.1);
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 图表卡片 */
.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
  margin-bottom: 32px;
}

.charts-grid.full-width-grid {
  grid-template-columns: 1fr;
}

.chart-card {
  background: rgba(17, 24, 39, 0.95);
  border-radius: 12px;
  padding: 28px;
  box-shadow: 0 0 0 1px rgba(0, 255, 136, 0.1), 
              0 8px 32px rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(0, 255, 136, 0.15);
  backdrop-filter: blur(10px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.chart-card:hover {
  box-shadow: 0 0 0 1px rgba(0, 255, 136, 0.2), 
              0 12px 40px rgba(0, 0, 0, 0.5),
              0 0 60px rgba(0, 255, 136, 0.08);
  transform: translateY(-2px);
}

.chart-card.full-width {
  width: 100%;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(0, 255, 136, 0.1);
  position: relative;
}

.chart-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--primary), transparent);
  opacity: 0.3;
}

.chart-header h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.chart-select {
  padding: 10px 16px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 13px;
  color: var(--text);
  background: rgba(15, 23, 42, 0.8);
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: inherit;
}

.chart-select:hover {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(0, 255, 136, 0.1);
}

.chart-body {
  min-height: 240px;
}

/* 模型统计 */
.model-stats {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.model-item {
  padding: 20px;
  background: rgba(15, 23, 42, 0.8);
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 136, 0.1);
  transition: all 0.3s ease;
}

.model-item:hover {
  border-color: var(--primary);
  background: rgba(0, 255, 136, 0.05);
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.model-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.model-count {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 600;
}

.model-bar {
  height: 8px;
  background: rgba(31, 41, 55, 0.8);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 12px;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
}

.model-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
  box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
}

.model-details {
  display: flex;
  gap: 16px;
}

.model-detail {
  font-size: 13px;
  color: var(--text-secondary);
}

/* 趋势图 */
.trend-chart {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  height: 200px;
  padding: 16px 0;
}

.trend-bar {
  flex: 1;
  background: linear-gradient(180deg, var(--primary), var(--secondary));
  border-radius: 4px 4px 0 0;
  position: relative;
  min-height: 4px;
  transition: height 0.3s ease;
  box-shadow: 0 0 15px rgba(0, 255, 136, 0.3);
}

.bar-value {
  position: absolute;
  top: -24px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
  text-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
}

.trend-labels {
  display: flex;
  justify-content: space-between;
  padding-top: 16px;
  border-top: 1px solid rgba(0, 255, 136, 0.1);
}

.trend-labels .label {
  flex: 1;
  text-align: center;
  font-size: 12px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 文本补全统计 */
.completion-stats {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.completion-type {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.completion-type-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: rgba(15, 23, 42, 0.8);
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 136, 0.1);
  transition: all 0.3s ease;
}

.completion-type-item:hover {
  border-color: var(--primary);
  background: rgba(0, 255, 136, 0.05);
}

.completion-type-icon {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 255, 136, 0.08);
  border-radius: 6px;
  border: 1px solid rgba(0, 255, 136, 0.2);
  flex-shrink: 0;
}

.completion-type-content {
  flex: 1;
}

.completion-type-value {
  font-size: 28px;
  font-weight: 800;
  color: var(--text);
  text-shadow: 0 0 15px rgba(0, 255, 136, 0.1);
}

.completion-type-label {
  font-size: 13px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.completion-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px;
  background: rgba(15, 23, 42, 0.8);
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 136, 0.1);
}

.completion-detail {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-label {
  font-size: 14px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}

/* 空状态 */
.empty-message {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background: rgba(15, 23, 42, 0.5);
  border-radius: 8px;
  border: 1px dashed rgba(0, 255, 136, 0.2);
}

/* 按钮 */
.refresh-button {
  margin-top: 8px;
}

/* 用户满意度统计 */
.satisfaction-stats {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.satisfaction-summary {
  display: flex;
  justify-content: space-around;
  padding: 24px;
  background: linear-gradient(135deg, rgba(0, 255, 136, 0.1) 0%, rgba(0, 204, 136, 0.1) 100%);
  border-radius: 8px;
  color: var(--text);
  border: 1px solid rgba(0, 255, 136, 0.2);
  backdrop-filter: blur(10px);
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 16px;
}

.summary-icon {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 255, 136, 0.08);
  border-radius: 6px;
  border: 1px solid rgba(0, 255, 136, 0.2);
  flex-shrink: 0;
}

.summary-content {
  display: flex;
  flex-direction: column;
}

.summary-value {
  font-size: 36px;
  font-weight: 800;
  line-height: 1;
  color: var(--primary);
  text-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
}

.summary-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.satisfaction-details {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.satisfaction-detail {
  display: flex;
  align-items: center;
  gap: 16px;
}

.satisfaction-detail .detail-label {
  min-width: 100px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.satisfaction-detail .detail-bar {
  flex: 1;
  height: 12px;
  background: rgba(31, 41, 55, 0.8);
  border-radius: 6px;
  overflow: hidden;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
}

.satisfaction-detail .detail-fill {
  height: 100%;
  border-radius: 6px;
  transition: width 0.5s ease;
  box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
}

.satisfaction-detail .detail-value {
  min-width: 40px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  text-align: right;
}

.full-width {
  grid-column: 1 / -1;
}

/* 星级分布样式 */
.star-distribution {
  padding: 20px;
  background: rgba(15, 23, 42, 0.8);
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 136, 0.1);
}

.star-distribution-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(0, 255, 136, 0.1);
}

.star-distribution-header h4 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.star-bars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.star-bar {
  display: flex;
  align-items: center;
  gap: 16px;
}

.star-label {
  min-width: 40px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  text-align: right;
}

.star-bar-container {
  flex: 1;
  height: 12px;
  background: rgba(31, 41, 55, 0.8);
  border-radius: 6px;
  overflow: hidden;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
}

.star-bar-fill {
  height: 100%;
  border-radius: 6px;
  transition: width 0.5s ease;
  box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
}

.star-count {
  min-width: 30px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  text-align: right;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .page {
    padding: 16px;
  }
  
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .title {
    font-size: 24px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .stat-card {
    padding: 20px;
    flex-direction: column;
    text-align: center;
    gap: 16px;
  }
  
  .chart-card {
    padding: 20px;
  }
  
  .completion-type {
    grid-template-columns: 1fr;
  }
  
  .satisfaction-summary {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .summary-item {
    flex-direction: column;
    gap: 8px;
  }
  
  .star-bar {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .star-label {
    min-width: auto;
    text-align: left;
  }
  
  .star-count {
    min-width: auto;
    text-align: left;
  }
}
</style>
