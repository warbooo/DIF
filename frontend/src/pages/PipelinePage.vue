<template>
  <div class="page">
    <div class="guide-container">
      <!-- 页面标题 -->
      <div class="guide-header">
        <h1 class="title">使用指南</h1>
        <p class="subtitle">快速了解如何使用文档修复系统，获得最佳修复效果</p>
      </div>

      <!-- 快速入门 -->
      <div class="guide-section">
        <h2 class="section-title">快速入门</h2>
        <div class="quick-start-grid">
          <div class="step-card">
            <div class="step-number">1</div>
            <div class="step-content">
              <h3>选择功能</h3>
              <p>根据需求选择左侧边栏的功能模块</p>
              <ul>
                <li><strong>图片修复</strong> - 提升图像清晰度和细节</li>
                <li><strong>OCR识别</strong> - 提取图片中的文字</li>
                <li><strong>语义补全</strong> - 智能补全缺失文字</li>
              </ul>
            </div>
          </div>
          <div class="step-card">
            <div class="step-number">2</div>
            <div class="step-content">
              <h3>上传图片</h3>
              <p>支持 JPG、PNG、BMP 格式</p>
              <ul>
                <li>建议图片尺寸：小于 2000x2000 像素</li>
                <li>文件大小：不超过 10MB</li>
                <li>文字清晰可见，避免过度模糊</li>
              </ul>
            </div>
          </div>
          <div class="step-card">
            <div class="step-number">3</div>
            <div class="step-content">
              <h3>选择模型（图片修复）</h3>
              <p>根据图片类型选择合适的超分模型</p>
              <ul>
                <li><strong>ClassicalSR</strong> - 一般文档、扫描件</li>
                <li><strong>CompressedSR</strong> - 网络下载的压缩图</li>
                <li><strong>RealWorldSR</strong> - AI生成图、动漫</li>
              </ul>
            </div>
          </div>
          <div class="step-card">
            <div class="step-number">4</div>
            <div class="step-content">
              <h3>获取结果</h3>
              <p>等待处理完成，下载修复结果</p>
              <ul>
                <li>处理时间：通常 10-60 秒</li>
                <li>大图片可能需要更长时间</li>
                <li>支持下载修复后的图片和文本</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- 模型选择指南 -->
      <div class="guide-section">
        <h2 class="section-title">模型选择指南</h2>
        <div class="model-table">
          <table>
            <thead>
              <tr>
                <th>模型</th>
                <th>适用场景</th>
                <th>特点</th>
                <th>示例</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>ClassicalSR</strong></td>
                <td>扫描文档、书籍照片、一般图像</td>
                <td>经典超分辨率，保留细节</td>
                <td>扫描的PDF文档、书籍页面</td>
              </tr>
              <tr>
                <td><strong>CompressedSR</strong></td>
                <td>JPEG压缩图、网络下载图</td>
                <td>去除压缩伪影，恢复细节</td>
                <td>微信/QQ保存的图片、网页截图</td>
              </tr>
              <tr>
                <td><strong>RealWorldSR</strong></td>
                <td>AI生成图、动漫、复杂退化图</td>
                <td>处理真实世界复杂退化</td>
                <td>AI绘画、动漫截图、游戏素材</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 使用技巧 -->
      <div class="guide-section">
        <h2 class="section-title">使用技巧</h2>
        <div class="tips-grid">
          <div class="tip-card">
            <div class="tip-icon">DOC</div>
            <h3>图片准备</h3>
            <ul>
              <li>确保文字方向正确（不要倒置）</li>
              <li>裁剪掉无关的边框和背景</li>
              <li>避免过度曝光或欠曝光</li>
            </ul>
          </div>
          <div class="tip-card">
            <div class="tip-icon">SPEED</div>
            <h3>提升速度</h3>
            <ul>
              <li>使用较小的图片（< 2000px）</li>
              <li>关闭其他占用GPU的程序</li>
              <li>避免同时处理多个大文件</li>
            </ul>
          </div>
          <div class="tip-card">
            <div class="tip-icon">OCR</div>
            <h3>提升识别率</h3>
            <ul>
              <li>选择正确的超分模型</li>
              <li>OCR时选择正确的语言</li>
              <li>确保图片清晰度足够</li>
            </ul>
          </div>
          <div class="tip-card">
            <div class="tip-icon">TOKEN</div>
            <h3>节省Token</h3>
            <ul>
              <li>语义补全默认使用规则补全</li>
              <li>仅必要时勾选"使用大语言模型"</li>
              <li>批量处理时谨慎使用LLM</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- 常见问题 -->
      <div class="guide-section">
        <h2 class="section-title">常见问题</h2>
        <div class="faq-list">
          <div class="faq-item">
            <div class="faq-question" @click="toggleFaq(0)">
              <span>处理时间太长怎么办？</span>
              <span class="faq-toggle">{{ openFaq === 0 ? '−' : '+' }}</span>
            </div>
            <div class="faq-answer" v-show="openFaq === 0">
              <p>处理时间主要取决于图片尺寸。建议：</p>
              <ul>
                <li>使用较小的图片（< 2000x2000 像素）</li>
                <li>大图片会自动分块处理，需要更多时间</li>
                <li>确保GPU可用，CPU处理会慢很多</li>
              </ul>
            </div>
          </div>
          <div class="faq-item">
            <div class="faq-question" @click="toggleFaq(1)">
              <span>OCR识别率低怎么解决？</span>
              <span class="faq-toggle">{{ openFaq === 1 ? '−' : '+' }}</span>
            </div>
            <div class="faq-answer" v-show="openFaq === 1">
              <p>提升OCR识别率的方法：</p>
              <ul>
                <li>先进行图片修复（超分辨率）再OCR</li>
                <li>选择正确的语言类型</li>
                <li>确保图片清晰度足够，文字不小于10px</li>
                <li>避免过度压缩的图片</li>
              </ul>
            </div>
          </div>
          <div class="faq-item">
            <div class="faq-question" @click="toggleFaq(2)">
              <span>超分辨率后效果不明显？</span>
              <span class="faq-toggle">{{ openFaq === 2 ? '−' : '+' }}</span>
            </div>
            <div class="faq-answer" v-show="openFaq === 2">
              <p>可能的原因和解决方案：</p>
              <ul>
                <li>原图质量已经很高，超分边际效益低</li>
                <li>选择了不适合的模型，尝试其他模型</li>
                <li>图片类型不适合超分（如本身就很清晰的文字）</li>
                <li>使用"文字修复效果对比"功能测试不同模型</li>
              </ul>
            </div>
          </div>
          <div class="faq-item">
            <div class="faq-question" @click="toggleFaq(3)">
              <span>语义补全会消耗很多Token吗？</span>
              <span class="faq-toggle">{{ openFaq === 3 ? '−' : '+' }}</span>
            </div>
            <div class="faq-answer" v-show="openFaq === 3">
              <p>不会！系统采用智能策略：</p>
              <ul>
                <li>默认使用规则补全，不消耗Token</li>
                <li>仅当勾选"使用大语言模型"时才消耗Token</li>
                <li>浏览页面不会消耗Token</li>
                <li>建议仅在复杂缺失时启用LLM</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- 处理流程说明 -->
      <div class="guide-section">
        <h2 class="section-title">处理流程说明</h2>
        <div class="process-flow">
          <div class="process-step">
            <div class="process-icon">UPLOAD</div>
            <div class="process-name">上传</div>
            <div class="process-desc">接收文档图片</div>
          </div>
          <div class="process-arrow">→</div>
          <div class="process-step">
            <div class="process-icon">PRE</div>
            <div class="process-name">预处理</div>
            <div class="process-desc">轻度对比度调整</div>
          </div>
          <div class="process-arrow">→</div>
          <div class="process-step">
            <div class="process-icon">SR</div>
            <div class="process-name">超分辨率</div>
            <div class="process-desc">4倍图像放大</div>
          </div>
          <div class="process-arrow">→</div>
          <div class="process-step">
            <div class="process-icon">OCR</div>
            <div class="process-name">OCR识别</div>
            <div class="process-desc">提取文字内容</div>
          </div>
          <div class="process-arrow">→</div>
          <div class="process-step">
            <div class="process-icon">POST</div>
            <div class="process-name">后处理</div>
            <div class="process-desc">拼写纠错优化</div>
          </div>
          <div class="process-arrow">→</div>
          <div class="process-step">
            <div class="process-icon">EXPORT</div>
            <div class="process-name">导出</div>
            <div class="process-desc">生成修复结果</div>
          </div>
        </div>
      </div>

      <!-- 联系我们 -->
      <div class="guide-section">
        <h2 class="section-title">需要帮助？</h2>
        <div class="contact-card">
          <p>如果您在使用过程中遇到问题，或有功能建议，欢迎反馈！</p>
          <div class="contact-links">
            <a href="/app/effect-showcase" class="contact-link">
              <span>SHOWCASE</span>
              <span>查看社区分享</span>
            </a>
            <a href="/app/sr-comparison" class="contact-link">
              <span>TEST</span>
              <span>测试不同模型</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const openFaq = ref<number | null>(null);

function toggleFaq(index: number) {
  openFaq.value = openFaq.value === index ? null : index;
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
  justify-content: center;
  align-items: flex-start;
}

.guide-container {
  width: 100%;
  max-width: 1000px;
  padding: 24px;
}

.guide-header {
  margin-bottom: 32px;
  text-align: center;
  position: relative;
  padding-bottom: 24px;
}

.guide-header::after {
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

.guide-header .title {
  font-size: 32px;
  font-weight: 800;
  margin-bottom: 12px;
  color: var(--text);
  text-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.guide-header .subtitle {
  color: var(--text-secondary);
  font-size: 16px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  line-height: 1.4;
}

/* 指南区块 */
.guide-section {
  background: rgba(17, 24, 39, 0.95);
  border-radius: 16px;
  padding: 28px;
  margin-bottom: 24px;
  box-shadow: 0 0 0 1px rgba(0, 255, 136, 0.1), 
              0 8px 32px rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(0, 255, 136, 0.15);
  backdrop-filter: blur(10px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.guide-section:hover {
  box-shadow: 0 0 0 1px rgba(0, 255, 136, 0.2), 
              0 12px 40px rgba(0, 0, 0, 0.5),
              0 0 60px rgba(0, 255, 136, 0.08);
  transform: translateY(-2px);
}

.section-title {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 24px;
  color: var(--text);
  position: relative;
  padding-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.section-title::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 60px;
  height: 2px;
  background: var(--primary);
  box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
}

/* 快速入门 */
.quick-start-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.step-card {
  display: flex;
  gap: 16px;
  padding: 24px;
  background: rgba(15, 23, 42, 0.8);
  border-radius: 12px;
  border: 1px solid rgba(0, 255, 136, 0.15);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(10px);
}

.step-card:hover {
  border-color: var(--primary);
  background: rgba(0, 255, 136, 0.05);
  box-shadow: 0 4px 16px rgba(0, 255, 136, 0.15);
  transform: translateY(-2px);
}

.step-number {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: #0a0a0a;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 800;
  flex-shrink: 0;
  box-shadow: 0 4px 16px rgba(0, 255, 136, 0.2);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.step-content h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.step-content p {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
  line-height: 1.5;
}

.step-content ul {
  margin: 0;
  padding-left: 20px;
}

.step-content li {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 6px;
  line-height: 1.4;
}

/* 模型表格 */
.model-table {
  overflow-x: auto;
  background: rgba(15, 23, 42, 0.8);
  border-radius: 12px;
  border: 1px solid rgba(0, 255, 136, 0.15);
  padding: 16px;
  backdrop-filter: blur(10px);
}

.model-table table {
  width: 100%;
  border-collapse: collapse;
}

.model-table th,
.model-table td {
  padding: 16px 20px;
  text-align: left;
  border-bottom: 1px solid rgba(0, 255, 136, 0.1);
}

.model-table th {
  background: rgba(0, 255, 136, 0.05);
  font-weight: 600;
  color: var(--text);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-size: 13px;
}

.model-table td {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.model-table tr:hover {
  background: rgba(0, 255, 136, 0.05);
}

/* 使用技巧 */
.tips-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
}

.tip-card {
  padding: 24px;
  background: rgba(15, 23, 42, 0.8);
  border-radius: 12px;
  border: 1px solid rgba(0, 255, 136, 0.15);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(10px);
}

.tip-card:hover {
  border-color: var(--primary);
  background: rgba(0, 255, 136, 0.05);
  box-shadow: 0 4px 16px rgba(0, 255, 136, 0.15);
  transform: translateY(-2px);
}

.tip-icon {
  font-size: 12px;
  font-weight: 800;
  color: var(--primary);
  background: rgba(0, 255, 136, 0.1);
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid rgba(0, 255, 136, 0.2);
  display: inline-block;
  margin-bottom: 16px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(0, 255, 136, 0.1);
}

.tip-card h3 {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--text);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.tip-card ul {
  margin: 0;
  padding-left: 20px;
}

.tip-card li {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  line-height: 1.4;
}

/* FAQ */
.faq-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.faq-item {
  border: 1px solid rgba(0, 255, 136, 0.15);
  border-radius: 12px;
  overflow: hidden;
  background: rgba(15, 23, 42, 0.8);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(10px);
}

.faq-item:hover {
  border-color: var(--primary);
  box-shadow: 0 4px 16px rgba(0, 255, 136, 0.15);
}

.faq-question {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: rgba(17, 24, 39, 0.95);
  cursor: pointer;
  font-weight: 600;
  color: var(--text);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid rgba(0, 255, 136, 0.1);
}

.faq-question:hover {
  background: rgba(0, 255, 136, 0.05);
}

.faq-toggle {
  font-size: 24px;
  color: var(--primary);
  font-weight: 300;
  transition: all 0.3s ease;
}

.faq-answer {
  padding: 24px;
  background: rgba(15, 23, 42, 0.95);
  border-top: 1px solid rgba(0, 255, 136, 0.1);
}

.faq-answer p {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.faq-answer ul {
  margin: 0;
  padding-left: 24px;
}

.faq-answer li {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 6px;
  line-height: 1.4;
}

/* 处理流程 */
.process-flow {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 16px;
  padding: 24px;
  background: rgba(15, 23, 42, 0.8);
  border-radius: 12px;
  border: 1px solid rgba(0, 255, 136, 0.15);
  backdrop-filter: blur(10px);
}

.process-step {
  text-align: center;
  padding: 20px;
  min-width: 100px;
  background: rgba(17, 24, 39, 0.95);
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 136, 0.15);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(10px);
}

.process-step:hover {
  border-color: var(--primary);
  background: rgba(0, 255, 136, 0.05);
  box-shadow: 0 4px 16px rgba(0, 255, 136, 0.15);
  transform: translateY(-2px);
}

.process-icon {
  font-size: 12px;
  font-weight: 800;
  color: var(--primary);
  background: rgba(0, 255, 136, 0.1);
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid rgba(0, 255, 136, 0.2);
  display: inline-block;
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(0, 255, 136, 0.1);
}

.process-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.process-desc {
  font-size: 11px;
  color: var(--text-secondary);
  line-height: 1.4;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.process-arrow {
  font-size: 24px;
  color: var(--primary);
  font-weight: 700;
  text-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
  margin: 0 8px;
}

/* 联系我们 */
.contact-card {
  text-align: center;
  padding: 28px;
  background: rgba(0, 255, 136, 0.05);
  border-radius: 12px;
  border: 1px solid rgba(0, 255, 136, 0.15);
  backdrop-filter: blur(10px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.contact-card:hover {
  border-color: var(--primary);
  box-shadow: 0 4px 16px rgba(0, 255, 136, 0.15);
  transform: translateY(-2px);
}

.contact-card p {
  margin-bottom: 24px;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.5;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.contact-links {
  display: flex;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;
}

.contact-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 24px;
  background: rgba(17, 24, 39, 0.95);
  border-radius: 8px;
  text-decoration: none;
  color: var(--text);
  font-weight: 600;
  border: 1px solid rgba(0, 255, 136, 0.15);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.contact-link:hover {
  border-color: var(--primary);
  background: rgba(0, 255, 136, 0.05);
  box-shadow: 0 6px 24px rgba(0, 255, 136, 0.15);
  transform: translateY(-2px);
}

.contact-link span:first-child {
  font-size: 12px;
  font-weight: 800;
  color: var(--primary);
  background: rgba(0, 255, 136, 0.1);
  padding: 6px 10px;
  border-radius: 4px;
  border: 1px solid rgba(0, 255, 136, 0.2);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  min-width: 80px;
  text-align: center;
}

@media (max-width: 768px) {
  .page {
    padding: 16px;
  }
  
  .guide-container {
    padding: 16px;
  }
  
  .guide-header .title {
    font-size: 24px;
  }
  
  .guide-section {
    padding: 20px;
  }
  
  .quick-start-grid {
    grid-template-columns: 1fr;
  }
  
  .tips-grid {
    grid-template-columns: 1fr;
  }
  
  .process-flow {
    flex-direction: column;
  }
  
  .process-arrow {
    transform: rotate(90deg);
    margin: 8px 0;
  }
  
  .process-step {
    min-width: 120px;
  }
  
  .contact-links {
    flex-direction: column;
    align-items: center;
  }
  
  .contact-link {
    width: 100%;
    justify-content: center;
  }
  
  .model-table {
    padding: 12px;
  }
  
  .model-table th,
  .model-table td {
    padding: 12px 16px;
  }
}
</style>
