<template>
  <div class="user-guide-page">
    <h1 class="page-title">使用指南</h1>
    
    <div class="guide-content">
      <!-- 快速开始 -->
      <section class="guide-section">
        <h2 class="section-title">快速开始</h2>
        <div class="section-content">
          <div class="step">
            <div class="step-number">1</div>
            <div class="step-content">
              <h3>选择功能</h3>
              <p>在左侧导航栏选择需要的功能：图片修复、批量处理、OCR 识别等</p>
            </div>
          </div>
          <div class="step">
            <div class="step-number">2</div>
            <div class="step-content">
              <h3>上传图片</h3>
              <p>拖拽图片或点击选择文件，支持 PNG、JPG、BMP 等常见格式</p>
            </div>
          </div>
          <div class="step">
            <div class="step-number">3</div>
            <div class="step-content">
              <h3>选择模型</h3>
              <p>推荐使用 <strong>RealWorldSR（通用）</strong>，适合绝大部分场景</p>
            </div>
          </div>
          <div class="step">
            <div class="step-number">4</div>
            <div class="step-content">
              <h3>查看结果</h3>
              <p>处理完成后在文件中心查看和下载结果</p>
            </div>
          </div>
        </div>
      </section>

      <!-- 功能说明 -->
      <section class="guide-section">
        <h2 class="section-title">功能说明</h2>
        
        <div class="feature-grid">
          <div class="feature-card">
            <div class="feature-icon"></div>
            <h3>图片修复</h3>
            <p>使用超分辨率技术增强图像清晰度和细节</p>
            <ul>
              <li>单张图片处理</li>
              <li>4 倍超分辨率放大</li>
              <li>三种模型可选</li>
            </ul>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon"></div>
            <h3>批量处理</h3>
            <p>批量上传并处理多张图片，统一管理处理结果</p>
            <ul>
              <li>文件夹批量上传</li>
              <li>实时监控处理进度</li>
              <li>统一下载结果</li>
            </ul>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon"></div>
            <h3>OCR 识别</h3>
            <p>智能识别图片中的文字内容</p>
            <ul>
              <li>高精度文字识别</li>
              <li>支持多语言</li>
              <li>自动检测文本区域</li>
            </ul>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon"></div>
            <h3>图片美化</h3>
            <p>优化图片质量，增强视觉效果</p>
            <ul>
              <li>智能去噪</li>
              <li>色彩增强</li>
              <li>锐化处理</li>
            </ul>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon"></div>
            <h3>语义补全</h3>
            <p>基于上下文智能补全文档内容</p>
            <ul>
              <li>语境理解</li>
              <li>智能预测</li>
              <li>自然流畅</li>
            </ul>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon"></div>
            <h3>修复效果综合对比</h3>
            <p>综合评估图片修复和文字识别效果</p>
            <ul>
              <li>多维度指标对比</li>
              <li>可视化分析</li>
              <li>用户评价系统</li>
            </ul>
          </div>
        </div>
      </section>

      <!-- 模型选择指南 -->
      <section class="guide-section">
        <h2 class="section-title">模型选择指南</h2>
        <div class="model-comparison">
          <div class="model-card recommended">
            <div class="model-badge">主推</div>
            <h3>RealWorldSR（真实世界图像）</h3>
            <div class="model-desc">适合绝大部分场景，温和处理不引入 artifacts</div>
            <ul class="model-features">
              <li>✓ 真实照片</li>
              <li>✓ 模糊文本</li>
              <li>✓ 老照片</li>
              <li>✓ 监控截图</li>
              <li>✓ 复杂退化图像</li>
            </ul>
            <div class="model-hint">💡 推荐首选，适用于 90% 以上的场景</div>
          </div>
          
          <div class="model-card">
            <h3>ClassicalSR（经典超分辨率）</h3>
            <div class="model-desc">强力锐化，适合高质量扫描件</div>
            <ul class="model-features">
              <li>✓ 高质量扫描件</li>
              <li>✓ 理想图片</li>
              <li>✓ 本身质量很高</li>
              <li>⚠ 需要强力锐化</li>
            </ul>
            <div class="model-hint">💡 仅推荐用于本身质量很高的图片</div>
          </div>
          
          <div class="model-card">
            <h3>CompressedSR（压缩图像恢复）</h3>
            <div class="model-desc">专门处理 JPEG 压缩 artifacts</div>
            <ul class="model-features">
              <li>✓ 网络压缩图</li>
              <li>✓ 有损压缩图片</li>
              <li>✓ JPEG 压缩 artifacts</li>
              <li>✓ 小尺寸图片</li>
            </ul>
            <div class="model-hint">💡 专门针对压缩损失的恢复</div>
          </div>
        </div>
      </section>

      <!-- 常见问题 -->
      <section class="guide-section">
        <h2 class="section-title">常见问题</h2>
        <div class="faq-list">
          <div class="faq-item">
            <h3>Q: 应该选择哪个模型？</h3>
            <p>A: 推荐使用 <strong>RealWorldSR（真实世界图像）</strong>，它适用于绝大部分场景，包括真实照片、模糊文本、老照片等。只有在处理高质量扫描件时才考虑 ClassicalSR。</p>
          </div>
          
          <div class="faq-item">
            <h3>Q: 支持哪些图片格式？</h3>
            <p>A: 支持常见的图片格式，包括 PNG、JPG、JPEG、BMP、WEBP 等。</p>
          </div>
          
          <div class="faq-item">
            <h3>Q: 批量处理有限制吗？</h3>
            <p>A: 支持批量上传整个文件夹的图片，系统会自动处理所有图片。建议单次处理不超过 50 张图片以获得最佳性能。</p>
          </div>
          
          <div class="faq-item">
            <h3>Q: 处理后的图片在哪里查看？</h3>
            <p>A: 处理完成后，可以在左侧导航栏的"文件中心"查看所有处理过的文件和结果。</p>
          </div>
          
          <div class="faq-item">
            <h3>Q: 如何下载处理结果？</h3>
            <p>A: 在文件中心点击文件查看详情，然后点击"下载结果"按钮即可下载处理后的图片。</p>
          </div>
          
          <div class="faq-item">
            <h3>Q: 评价系统有什么用？</h3>
            <p>A: 您可以对每次处理结果进行 1-5 星评分，帮助我们改进服务质量。评分记录可在数据统统计页面查看。</p>
          </div>
        </div>
      </section>

      <!-- 技巧提示 -->
      <section class="guide-section">
        <h2 class="section-title">使用技巧</h2>
        <div class="tips-grid">
          <div class="tip-card">
            <div class="tip-icon"></div>
            <h4>首选 RealWorldSR</h4>
            <p>如果不确定选什么模型，就选 RealWorldSR，它在 90% 的场景下都表现优秀</p>
          </div>
          
          <div class="tip-card">
            <div class="tip-icon"></div>
            <h4>批量处理更高效</h4>
            <p>使用文件夹上传功能，一次性处理所有图片，节省时间</p>
          </div>
          
          <div class="tip-card">
            <div class="tip-icon"></div>
            <h4>评价帮助改进</h4>
            <p>对处理结果评分，帮助我们了解哪些场景需要优化</p>
          </div>
          
          <div class="tip-card">
            <div class="tip-icon"></div>
            <h4>查看数据统计</h4>
            <p>在数据统计页面查看处理历史、成功率和用户满意度</p>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
// 使用指南页面
</script>

<style scoped>
.user-guide-page {
  min-height: 100vh;
  background: var(--background);
  background-image: 
    radial-gradient(circle at 20% 80%, rgba(0, 255, 136, 0.03) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(0, 204, 136, 0.03) 0%, transparent 50%),
    linear-gradient(180deg, #0a0a0a 0%, #0f1419 100%);
  padding: 40px;
}

.page-title {
  font-size: 32px;
  font-weight: 800;
  color: var(--text);
  margin-bottom: 40px;
  text-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.guide-content {
  max-width: 1200px;
  margin: 0 auto;
}

.guide-section {
  margin-bottom: 48px;
}

.section-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(0, 255, 136, 0.12);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 快速开始步骤 */
.step {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  padding: 20px;
  background: rgba(17, 24, 39, 0.85);
  border: 1px solid rgba(0, 255, 136, 0.12);
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.step-number {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 255, 136, 0.1);
  border: 1px solid rgba(0, 255, 136, 0.2);
  border-radius: 50%;
  font-size: 18px;
  font-weight: 800;
  color: var(--primary);
  flex-shrink: 0;
}

.step-content h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 8px;
}

.step-content p {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
}

/* 功能网格 */
.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.feature-card {
  padding: 24px;
  background: rgba(17, 24, 39, 0.85);
  border: 1px solid rgba(0, 255, 136, 0.12);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.feature-card:hover {
  border-color: rgba(0, 255, 136, 0.2);
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 255, 136, 0.1);
}

.feature-icon {
  font-size: 36px;
  margin-bottom: 12px;
}

.feature-card h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 8px;
}

.feature-card p {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
  line-height: 1.6;
}

.feature-card ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.feature-card li {
  font-size: 13px;
  color: var(--text-hint);
  padding: 4px 0;
  padding-left: 16px;
  position: relative;
}

.feature-card li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: var(--primary);
}

/* 模型对比 */
.model-comparison {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.model-card {
  padding: 24px;
  background: rgba(17, 24, 39, 0.85);
  border: 1px solid rgba(0, 255, 136, 0.12);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  position: relative;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.model-card:hover {
  border-color: rgba(0, 255, 136, 0.2);
  transform: translateY(-4px);
}

.model-card.recommended {
  border-color: rgba(0, 255, 136, 0.3);
  box-shadow: 0 0 30px rgba(0, 255, 136, 0.1);
}

.model-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba(0, 255, 136, 0.15);
  color: var(--primary);
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  border: 1px solid rgba(0, 255, 136, 0.3);
}

.model-card h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 8px;
}

.model-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 16px;
  line-height: 1.6;
}

.model-features {
  list-style: none;
  padding: 0;
  margin: 0 0 16px 0;
}

.model-features li {
  font-size: 13px;
  color: var(--text-hint);
  padding: 4px 0;
}

.model-hint {
  font-size: 13px;
  color: var(--primary);
  padding: 12px;
  background: rgba(0, 255, 136, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 136, 0.1);
}

/* FAQ */
.faq-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.faq-item {
  padding: 20px;
  background: rgba(17, 24, 39, 0.85);
  border: 1px solid rgba(0, 255, 136, 0.12);
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.faq-item h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 12px;
}

.faq-item p {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.8;
}

.faq-item strong {
  color: var(--primary);
}

/* 技巧提示 */
.tips-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}

.tip-card {
  padding: 20px;
  background: rgba(17, 24, 39, 0.85);
  border: 1px solid rgba(0, 255, 136, 0.12);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  text-align: center;
}

.tip-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.tip-card h4 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 8px;
}

.tip-card p {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .user-guide-page {
    padding: 20px;
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .feature-grid,
  .model-comparison,
  .tips-grid {
    grid-template-columns: 1fr;
  }
  
  .step {
    flex-direction: column;
    text-align: center;
  }
  
  .step-number {
    margin: 0 auto;
  }
}
</style>
