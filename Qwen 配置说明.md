# Qwen 大模型配置说明

本文档介绍如何配置和使用 Qwen（通义千问）大模型进行文本智能补全功能。

---

## 📋 目录

- [功能说明](#功能说明)
- [配置方法](#配置方法)
- [部署方式](#部署方式)
- [使用示例](#使用示例)
- [故障排查](#故障排查)

---

## 功能说明

DIF 系统集成了 Qwen 大模型用于**智能文本补全**，主要针对以下场景：

1. **OCR 识别缺字补全** - 文档扫描识别后的缺失文字智能补全
2. **语义理解补全** - 基于上下文的语义推理补全
3. **固定搭配识别** - 识别常见词组和固定搭配

### 工作流程

```
OCR 识别文本 
  ↓
检测缺失标记（□、_ 等）
  ↓
启用 LLM？
  ├─ 是 → 调用 Qwen API → 补全成功？
  │        ├─ 是 → 返回补全结果 ✓
  │        └─ 否 → 回退到规则补全
  │
  └─ 否 → 使用规则补全（固定搭配匹配）
```

---

## 配置方法

### 1. 编辑环境变量文件

在 `backend/.env` 文件中配置（**已配置**）：

```bash
# 通义千问 API Key
LLM_API_KEY=sk-e387f7a70dee489fb9253672f34185c5

# API 基础地址（DashScope 兼容格式）
LLM_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1

# 模型名称
LLM_MODEL=qwen3.6-plus
```

### 2. 重启后端服务

修改配置后需要重启后端服务：

```bash
# 停止服务
.\stop.bat

# 启动服务
.\start.bat
```

### 3. 验证配置

启动日志中会显示：

```
[TextCompletion] Qwen 大模型：已启用 (模型：qwen3.6-plus, API: https://dashscope.aliyuncs.com/compatible-mode/v1)
```

---

## 部署方式

### 方式一：本地部署（推荐）

使用 Ollama、vLLM 等工具本地部署 Qwen 模型。

#### 使用 Ollama

```bash
# 安装 Ollama
# Windows: 下载安装 https://ollama.ai/download

# 拉取 Qwen 模型
ollama pull qwen:7b

# 启动 API 服务（默认端口 11434）
ollama serve

# 配置 QWEN_API_URL
QWEN_API_URL=http://localhost:11434/api/generate
```

#### 使用 vLLM

```bash
# 安装 vLLM
pip install vllm

# 启动 API 服务
python -m vllm.entrypoints.api_server \
    --model Qwen/Qwen-7B-Chat \
    --host 0.0.0.0 \
    --port 8000

# 配置 QWEN_API_URL
QWEN_API_URL=http://localhost:8000/generate
```

---

### 方式二：阿里云 DashScope（云服务）

使用阿里云通义千问 API 服务。

#### 1. 获取 API Key

1. 访问 [阿里云 DashScope](https://dashscope.aliyun.com/)
2. 注册/登录账号
3. 创建 API Key

#### 2. 配置 API

```bash
# 配置 QWEN_API_URL
QWEN_API_URL=https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation

# 如果需要 API Key（暂未实现），可在代码中添加
```

#### 3. 计费说明

- Qwen-7B: ¥0.002/1K tokens
- Qwen-14B: ¥0.003/1K tokens
- Qwen-72B: ¥0.006/1K tokens

详细价格请参考 [阿里云官方文档](https://help.aliyun.com/zh/dashscope/developer-reference/tongyi-qianwen-llm-price)

---

### 方式三：其他兼容 API

Qwen 支持 OpenAI 兼容格式的 API，可使用以下服务：

- **FastChat** - 开源模型 Serving 框架
- **LM Studio** - 本地模型部署工具
- **Text Generation WebUI** - Web 界面部署

配置示例：

```bash
# FastChat
QWEN_API_URL=http://localhost:8000/v1/completions

# LM Studio
QWEN_API_URL=http://localhost:1234/v1/completions
```

---

## 使用示例

### 1. 通过 API 接口调用

```bash
# 请求
curl -X POST http://localhost:8000/api/text/complete \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "这是一□测试文档，请□系相关人员。",
    "use_llm": true,
    "enable_spell_correction": true
  }'

# 响应
{
  "success": true,
  "message": "补全完成，共补全 2 处缺失（步骤：拼写纠错 → LLM 补全）",
  "original_text": "这是一□测试文档，请□系相关人员。",
  "corrected_text": "这是一□测试文档，请联系相关人员。",
  "completed_text": "这是一个测试文档，请联系相关人员。",
  "missing_count": 2,
  "method": "llm"
}
```

### 2. 前端界面使用

在文本补全页面：

1. 输入包含缺失标记的文本
2. 勾选"使用大语言模型"选项
3. 点击"智能补全"按钮
4. 查看补全结果

### 3. Python 代码调用

```python
import requests

# 登录获取 token
login_response = requests.post('http://localhost:8000/api/auth/login', json={
    'username': 'admin',
    'password': 'password123'
})
token = login_response.json()['access_token']

# 文本补全
response = requests.post(
    'http://localhost:8000/api/text/complete',
    headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    },
    json={
        'text': '这□一□测试，□联系。',
        'use_llm': True,
        'enable_spell_correction': True
    }
)

result = response.json()
print(f"补全结果：{result['completed_text']}")
```

---

## 故障排查

### 问题 1：大模型未启用

**现象**: 日志显示 `Qwen 大模型：未启用`

**原因**: 未配置 `QWEN_API_URL`

**解决方法**:
1. 检查 `backend/.env` 文件是否存在
2. 确认 `QWEN_API_URL` 已配置
3. 重启后端服务

---

### 问题 2：API 调用失败

**现象**: 日志显示 `Qwen API 调用失败：404` 或连接超时

**原因**: API 地址错误或服務未启动

**解决方法**:
1. 检查 API URL 是否正确
2. 确认本地模型服务已启动
3. 检查防火墙设置
4. 测试 API 连通性：
   ```bash
   curl http://localhost:8000/v1/completions
   ```

---

### 问题 3：补全效果不佳

**现象**: 补全结果不准确或胡言乱语

**原因**: 模型参数或提示词问题

**解决方法**:
1. 调整 `temperature` 参数（降低随机性）
2. 增加上下文信息
3. 更换更大的模型（如 Qwen-14B、Qwen-72B）
4. 优化提示词模板

---

### 问题 4：回退到规则补全

**现象**: 日志显示 `LLM 补全失败，回退到规则补全`

**原因**: LLM API 调用失败

**解决方法**:
1. 检查网络连接
2. 检查 API 服务状态
3. 查看详细的错误日志
4. 增加超时时间（当前 30 秒）

---

## 性能优化建议

### 1. 使用本地模型

- 避免网络延迟
- 保护数据隐私
- 降低使用成本

### 2. 批量处理

对于多条文本，使用批量接口减少 API 调用次数：

```python
# 批量补全
response = requests.post(
    'http://localhost:8000/api/text/complete/batch',
    json={
        'texts': ['文本 1', '文本 2', '文本 3'],
        'use_llm': True
    }
)
```

### 3. 缓存结果

对于相同的输入，缓存补全结果避免重复调用。

### 4. 混合策略

- 简单文本使用规则补全（快速）
- 复杂文本使用 LLM 补全（准确）
- 设置超时时间避免长时间等待

---

## 支持的缺失标记

系统支持以下缺失标记：

- `_` - 下划线
- `□` - 方框
- `■` - 实心方框
- `▢` - 空心方框
- `▣` - 带点方框
- `▤`, `▥`, `▦`, `▧`, `▨`, `▩` - 各种图案
- `▪`, `▫` - 小方块

---

## 常见固定搭配

规则补全支持以下常见搭配：

| 缺失模式 | 补全为 |
|---------|--------|
| □系 | 联系 |
| □生 | 学生 |
| □请 | 申请 |
| 一□ | 一个 |
| 这□ | 这个 |
| □是 | 这是 |
| □们 | 我们 |
| □他 | 其他 |
| □以 | 所以 |
| □要 | 需要 |

---

## 相关文档

- [API 接口文档](API 接口文档.md#文本补全接口)
- [第三方库说明](第三方库说明.md)
- [项目总览](项目总览.md#3-文本补全-macbert)

---

*最后更新：2026 年 4 月*
