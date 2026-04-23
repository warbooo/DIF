# DIF (DocIntelliFix) - 智能文档修复与增强系统

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.78.0-green.svg)
![Vue](https://img.shields.io/badge/Vue-3.3.x-brightgreen.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

🖼️ **图像增强** | 📝 **OCR 识别** | ✨ **文本纠错** | 📊 **效果评估**

</div>

---

## 📖 项目简介

**DIF (DocIntelliFix)** 是一款智能文档修复与增强系统，集成了 OCR 识别、超分辨率重建、文本补全、图像增强等多种 AI 技术，用于处理和修复低质量文档图像。

### 核心功能

- 🖼️ **图像增强** - 基于 Swin2SR 的超分辨率重建 (4x 放大)
- 📝 **OCR 识别** - 基于 RapidOCR v5 的高精度文字识别
- ✨ **文本补全** - 基于 MacBERT 的智能拼写纠错
- 📊 **效果评估** - 完整的 OCR 质量评估体系 (CER、SSIM、PSNR 等)
- 📁 **批量处理** - 支持多文档批量处理
- 👤 **用户管理** - 完整的用户认证与历史记录

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.10+
- **Node.js**: 18+
- **GPU**: NVIDIA RTX 3060 或更高 (推荐)
- **CUDA**: 11.7+

### 安装步骤

#### 1. 克隆项目

```bash
git clone <repository-url>
cd DIF
```

#### 2. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

#### 3. 安装前端依赖

```bash
cd frontend
npm install
```

#### 4. 配置环境变量

```bash
# 后端配置
cd backend
cp .env.example .env
# 编辑 .env 文件，修改 JWT_SECRET

# 前端配置
cd frontend
cp .env.example .env
```

#### 5. 启动服务

**方式一：使用启动脚本 (推荐)**

```bash
# Windows
.\start.bat
```

**方式二：手动启动**

```bash
# 终端 1 - 启动后端
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 终端 2 - 启动前端
cd frontend
npm run dev
```

### 访问应用

- **前端界面**: http://localhost:5173
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

---

## 🏗️ 技术架构

### 后端技术栈

**框架与核心**
- Python 3.10
- FastAPI (Web 框架)
- Uvicorn (ASGI 服务器)
- SQLAlchemy (ORM)
- SQLite (数据库)

**AI 模型**
- **Swin2SR** - 超分辨率重建 (PyTorch)
- **RapidOCR** - OCR 识别 (ONNX Runtime)
- **MacBERT** - 文本纠错 (PyTorch, PyCorrector)

### 前端技术栈

**框架与核心**
- Vue 3 (Composition API)
- TypeScript
- Vite (构建工具)
- Vue Router (路由管理)

**UI 组件**
- 自定义组件系统
- 图片对比滑块组件
- OCR 评估面板组件
- 图片裁剪组件

---

## 📁 项目结构

```
DIF/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── core/              # 核心配置与安全
│   │   ├── db/                # 数据库模型
│   │   ├── routes/            # API 路由
│   │   ├── schemas/           # Pydantic 模型
│   │   ├── services/          # 业务服务
│   │   └── main.py            # 应用入口
│   ├── swin2sr/               # Swin2SR 模型代码
│   ├── rapidocr_service.py    # OCR 子进程服务
│   └── requirements.txt       # Python 依赖
│
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── api/               # API 客户端
│   │   ├── components/        # UI 组件
│   │   ├── layouts/           # 布局组件
│   │   ├── pages/             # 页面组件
│   │   └── main.ts            # 应用入口
│   └── vite.config.ts         # Vite 配置
│
├── scripts/                    # 工具脚本
├── start.bat                   # 启动脚本
└── README.md                   # 项目说明
```

---

## 🔧 核心功能详解

### 1. 图像超分辨率 (Swin2SR)

**功能**: 将低分辨率图像放大 4x，同时保持清晰度

**技术特点**:
- 使用 Swin Transformer V2 架构
- 支持 RealWorldSR 模型 (真实场景优化)
- GPU 加速 (CUDA)
- 文字区域专项优化

**使用示例**:
```python
from app.services.swin2sr_service import get_sr_service

sr_service = get_sr_service()
result = sr_service.enhance_image(
    image=pil_image,
    scale=4,
    method='realworld'  # realworld, classical, compressed
)
```

### 2. OCR 识别 (RapidOCR)

**功能**: 高精度文字识别，支持多语言

**技术特点**:
- 基于 ONNX Runtime，跨平台
- 子进程隔离，避免阻塞主服务
- 支持检测 + 识别 + 方向分类
- 置信度评估

### 3. 文本纠错 (MacBERT)

**功能**: 智能拼写纠错，特别针对 OCR 错误

**严格模式逻辑**:
1. 提取所有非中文字符
2. 中文字符太少时跳过 (<5 个)
3. 只对纯中文调用 MacBERT
4. 还原非中文字符

**常见纠错对**:
- 的 ↔ 地 ↔ 得
- 在 ↔ 再
- 做 ↔ 作
- 需 ↔ 须
- 像 ↔ 象

### 4. 效果评估

**评估指标**:
- **字符准确率 (CER)**: 字符级错误率
- **编辑距离 (ED)**: 最少编辑次数
- **置信度评分**: OCR 置信度统计
- **结构相似度 (SSIM)**: 图像质量评估
- **峰值信噪比 (PSNR)**: 图像重建质量

---

## 🔐 认证与安全

### JWT Token 认证

**流程**:
1. 用户登录 → 获取 token
2. 前端存储 token (localStorage)
3. 每次请求携带 token
4. 后端验证 token 有效性

**安全特性**:
- bcrypt 密码哈希
- Token 可配置过期时间
- 密码强度验证
- 用户权限控制

---

## 📊 数据库设计

### 核心表结构

**users** - 用户表
- id, username, email, password_hash
- created_at, is_active

**repair_tasks** - 修复任务表
- id, user_id, original_image, enhanced_image
- ocr_text, corrected_text
- status, created_at

**model_usage_stats** - 模型使用统计
- model_name, usage_count
- total_processing_time
- last_used_at

**ocr_evaluation_results** - OCR 评估结果
- task_id, cer, edit_distance
- confidence, ssim, psnr

---

## 🎨 前端特性

### 图片对比滑块

左右滑动对比原图和处理后的图片，直观展示效果。

### OCR 评估面板

实时显示 OCR 识别质量评估，包括：
- 识别置信度
- 字符准确率
- 编辑距离
- 对比分析

### 批量处理

支持多文档同时处理，任务队列管理，进度实时跟踪。

---

## 🛠️ 开发与维护

### 开发模式

**后端热重载**:
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端热重载**:
```bash
cd frontend
npm run dev
```

### 停止服务

```bash
# Windows
.\stop.bat
```

带重试机制和缓存清理，确保完全停止所有进程。

---

## 📝 文档资料

- **[部署指南](部署指南.md)** - 详细部署指南（供导师使用）
- **[项目总览](项目总览.md)** - 完整的项目介绍和技术架构
- **[数据库管理](DATABASE_MANAGEMENT.md)** - 数据库管理文档
- **[Swin2SR 集成](SWIN2SR_INTEGRATION.md)** - Swin2SR 集成文档
- **[技术创新](INNOVATIONS.md)** - 技术创新点
- **[数据集指南](DATASET_GUIDE.md)** - 数据集使用指南
- **[API 接口文档](API 接口文档.md)** - 详细的 API 接口说明

---

## 🎯 项目亮点

### 技术创新

1. **多模型协同** - Swin2SR + RapidOCR + MacBERT 联合工作
2. **严格纠错模式** - 只纠正高置信度中文错误，保护格式和特殊内容
3. **子进程隔离** - OCR 服务独立进程，避免阻塞主服务
4. **实时效果评估** - 完整的评估指标体系

### 用户体验

1. **滑块对比** - 直观的前后对比效果
2. **批量处理** - 支持多文档同时处理
3. **历史记录** - 完整的处理历史追溯
4. **数据看板** - 实时统计与可视化

### 性能优化

1. **GPU 加速** - 所有 AI 模型支持 CUDA
2. **模型预加载** - 启动时加载，减少延迟
3. **异步处理** - 支持后台任务队列
4. **图片压缩** - WebP 格式存储

---

## 📦 依赖版本

### 后端核心依赖

```
fastapi==0.78.0
uvicorn==0.18.3
sqlalchemy==1.4.52
pydantic==1.10.14
torch==1.13.1
torchvision==0.14.1
onnxruntime-gpu>=1.15.0
pycorrector>=0.4.0
rapidocr-onnxruntime>=1.3.0
```

### 前端核心依赖

```
vue@3.3.x
typescript@5.x
vite@5.x
vue-router@4.x
```

---

## 🤝 团队与贡献

**主要开发者**: DIF Team

**技术支持**:
- Swin2SR: NVIDIA Research
- RapidOCR: OpenMMLab
- MacBERT: PyCorrector

---

## 📄 许可证

本项目采用 MIT 许可证

---

## 📞 联系与支持

**问题反馈**: 提交 Issue  
**技术支持**: 查看文档或联系开发团队

---

<div align="center">

**DIF (DocIntelliFix)** - 让文档更清晰

*最后更新：2026 年 4 月*

</div>
