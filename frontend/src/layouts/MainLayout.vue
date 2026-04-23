<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="logo-container">
          <div class="logo-icon">[DIF]</div>
          <h2 class="sidebar-title">文档智能修复</h2>
        </div>
        <div class="logo-subtitle">DOCUMENT INTELLIGENCE FIX</div>
      </div>
      <nav class="sidebar-nav">
        <div class="nav-section">
          <div class="nav-section-title">文档处理</div>
          <router-link
            to="/app/image-repair"
            class="nav-item"
            active-class="active"
          >
            <span>图片修复</span>
          </router-link>
          <router-link
            to="/app/image-enhance"
            class="nav-item"
            active-class="active"
          >
            <span>图片美化</span>
          </router-link>
          <router-link
            to="/app/ocr-processing"
            class="nav-item"
            active-class="active"
          >
            <span>OCR 识别</span>
          </router-link>
          <router-link
            to="/app/text-completion"
            class="nav-item"
            active-class="active"
          >
            <span>语义补全</span>
          </router-link>
        </div>
        
        <div class="nav-section">
          <div class="nav-section-title">实用工具</div>
        <router-link
          to="/app/batch-processing"
          class="nav-item"
          active-class="active"
        >
          <span>批量处理</span>
        </router-link>
        <router-link
          to="/app/repair-comparison"
          class="nav-item"
          active-class="active"
        >
          <span>修复效果综合对比</span>
        </router-link>
        </div>
        
        <div class="nav-section">
          <div class="nav-section-title">系统</div>
        <router-link
          to="/app/dashboard"
          class="nav-item"
          active-class="active"
        >
          <span>数据统计</span>
        </router-link>
        <router-link
          to="/app/user-guide"
          class="nav-item"
          active-class="active"
        >
          <span>使用指南</span>
        </router-link>
        <router-link
          to="/app/profile/files"
          class="nav-item"
          active-class="active"
        >
          <span>文件中心</span>
        </router-link>
        <router-link
          to="/app/profile/info"
          class="nav-item"
          active-class="active"
        >
          <span>个人中心</span>
        </router-link>
        </div>
      </nav>
      <div class="sidebar-footer">
        <button class="btn logout-btn" @click="logout">
          退出登录
        </button>
      </div>
    </aside>
    <main class="main-content">
      <router-view :key="$route.path" />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";

const router = useRouter();

function logout() {
  localStorage.removeItem("token");
  router.push("/auth");
}
</script>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: linear-gradient(135deg, #0a0a0a 0%, #0f161c 20%, #121e26 40%, #0f221e 60%, #0a1a15 80%, #0a0a0a 100%);
  position: relative;
}

.layout::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 20%, rgba(0, 255, 136, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(0, 204, 136, 0.08) 0%, transparent 50%),
    linear-gradient(90deg, rgba(0, 255, 136, 0.05) 1px, transparent 1px),
    linear-gradient(rgba(0, 255, 136, 0.03) 1px, transparent 1px);
  background-size: 100% 100%, 100% 100%, 40px 40px, 40px 40px;
  pointer-events: none;
  animation: gridMove 30s linear infinite;
  z-index: 0;
}

.sidebar {
  width: 280px;
  background: linear-gradient(135deg, #0a0a0a 0%, #0f161c 20%, #121e26 40%, #0f221e 60%, #0a1a15 80%, #0a0a0a 100%);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  flex-shrink: 0;
  border-right: 1px solid rgba(0, 255, 136, 0.15);
}

.sidebar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 10% 30%, rgba(0, 255, 136, 0.05) 0%, transparent 40%),
    radial-gradient(circle at 90% 70%, rgba(0, 204, 136, 0.03) 0%, transparent 40%),
    linear-gradient(90deg, rgba(0, 255, 136, 0.03) 1px, transparent 1px),
    linear-gradient(rgba(0, 255, 136, 0.02) 1px, transparent 1px);
  background-size: 100% 100%, 100% 100%, 20px 20px, 20px 20px;
  pointer-events: none;
  animation: gridMove 20s linear infinite;
  z-index: 1;
}

.sidebar::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 1px;
  background: rgba(0, 255, 136, 0.1);
  pointer-events: none;
  z-index: 2;
}

.sidebar-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, rgba(0, 255, 136, 0.3) 50%, transparent 100%);
  box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
  pointer-events: none;
  z-index: 3;
}

.sidebar-footer::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, rgba(0, 255, 136, 0.3) 50%, transparent 100%);
  box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
  pointer-events: none;
  z-index: 3;
}

.sidebar-footer::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, rgba(0, 255, 136, 0.3) 50%, transparent 100%);
  box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
  pointer-events: none;
  z-index: 3;
}

@keyframes gridMove {
  0% {
    background-position: 0 0, 0 0, 0 0, 0 0;
  }
  100% {
    background-position: 20px 20px, 0 0, 20px 20px, 20px 20px;
  }
}

.sidebar-header {
  padding: 28px 24px;
  border-bottom: 1px solid rgba(0, 255, 136, 0.1);
  position: relative;
  z-index: 1;
}

.logo-container {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.logo-icon {
  font-size: 24px;
  font-weight: 900;
  color: var(--primary);
  letter-spacing: -1px;
  text-shadow: 0 0 30px rgba(0, 255, 136, 0.5);
  background: linear-gradient(135deg, var(--primary) 0%, #00cc88 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  padding: 8px 12px;
  border: 1px solid rgba(0, 255, 136, 0.3);
  border-radius: 6px;
  box-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
  animation: pulse 2s ease-in-out infinite alternate;
}

@keyframes pulse {
  from {
    box-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
  }
  to {
    box-shadow: 0 0 30px rgba(0, 255, 136, 0.4);
  }
}

.sidebar-title {
  color: var(--text);
  font-size: 18px;
  font-weight: 800;
  margin: 0;
  line-height: 1.3;
  letter-spacing: 2px;
  text-transform: uppercase;
  text-shadow: 0 0 10px rgba(0, 255, 136, 0.2);
}

.logo-subtitle {
  color: var(--text-hint);
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 3px;
  text-transform: uppercase;
  opacity: 0.8;
  transition: opacity 0.3s ease;
}

.logo-container:hover .logo-subtitle {
  opacity: 1;
  color: var(--primary);
  text-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
}

.sidebar-nav {
  flex: 1;
  padding: 12px 16px;
  overflow-y: auto;
  position: relative;
  z-index: 1;
}

.sidebar-nav::-webkit-scrollbar {
  width: 3px;
}

.sidebar-nav::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
}

.sidebar-nav::-webkit-scrollbar-thumb {
  background: rgba(0, 255, 136, 0.3);
  border-radius: 2px;
}

.nav-section {
  margin-bottom: 20px;
}

.nav-section-title {
  color: var(--text-hint);
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 2px;
  padding: 10px 14px 6px;
  margin-bottom: 6px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 16px;
  color: var(--text-secondary);
  text-decoration: none;
  border-radius: 4px;
  margin-bottom: 4px;
  transition: all 0.2s ease;
  font-size: 14px;
  font-weight: 500;
  position: relative;
  overflow: hidden;
  border: 1px solid transparent;
  backdrop-filter: blur(10px);
}

.nav-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--primary);
  opacity: 0;
  transition: opacity 0.2s ease;
  box-shadow: 0 0 10px var(--primary);
}

.nav-item::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  background: radial-gradient(circle, rgba(0, 255, 136, 0.1) 0%, transparent 70%);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: width 0.3s ease, height 0.3s ease;
  pointer-events: none;
}

.nav-item:hover {
  background: rgba(0, 255, 136, 0.08);
  color: var(--primary);
  border-color: rgba(0, 255, 136, 0.2);
  box-shadow: 0 0 15px rgba(0, 255, 136, 0.1);
}

.nav-item:hover::before {
  opacity: 1;
}

.nav-item:hover::after {
  width: 200px;
  height: 200px;
}

.nav-item.active {
  background: rgba(0, 255, 136, 0.1);
  color: var(--primary);
  border-color: rgba(0, 255, 136, 0.3);
  box-shadow: 0 0 20px rgba(0, 255, 136, 0.15);
}

.nav-item.active::before {
  opacity: 1;
}

.nav-item.active::after {
  width: 150px;
  height: 150px;
  background: radial-gradient(circle, rgba(0, 255, 136, 0.15) 0%, transparent 70%);
}

.sidebar-footer {
  padding: 20px 16px;
  border-top: 1px solid rgba(0, 255, 136, 0.1);
  margin-top: auto;
  position: relative;
  z-index: 1;
}

.logout-btn {
  width: 100%;
  padding: 12px 18px;
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid rgba(255, 68, 68, 0.3);
  border-radius: 4px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.logout-btn:hover {
  background: rgba(255, 68, 68, 0.1);
  border-color: rgba(255, 68, 68, 0.5);
  color: #ff4444;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 32px;
  background: rgba(10, 16, 22, 0.9);
  backdrop-filter: blur(20px);
  position: relative;
  z-index: 1;
}

.main-content::-webkit-scrollbar {
  width: 6px;
}

.main-content::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
}

.main-content::-webkit-scrollbar-thumb {
  background: rgba(0, 255, 136, 0.3);
  border-radius: 3px;
}

.main-content::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 255, 136, 0.5);
}
</style>
