# Swin2SR 超分服务集成指南

## 概述

已成功将 **Swin2SR** 图像超分服务集成到 Visson Pro 系统中。

Swin2SR 是基于 **Swin Transformer V2** 架构的图像超分辨率模型，特别适用于：
- 压缩图像恢复
- 文档图像超分
- 低质量图像增强

**论文**: Swin2SR: SwinV2 Transformer for Compressed Image Super-Resolution and Restoration

## 文件变更

### 新增文件

1. `backend/app/services/swin2sr_service.py` - Swin2SR 超分服务核心实现

### 修改文件

1. `backend/app/services/doc_repair.py` - 集成超分功能到文档修复流程
2. `backend/requirements.txt` - 添加依赖说明
3. `backend/.env.example` - 添加 Swin2SR 配置示例

## 配置说明

在 `backend/.env` 文件中添加以下配置：

```env
# Swin2SR 超分服务配置
# 基于 Swin Transformer V2 的图像超分辨率模型

SWIN2SR_USE_LOCAL=true          # 使用本地模型模式
SWIN2SR_MODEL_PATH=./weights/swin2sr  # 模型路径
SWIN2SR_SCALE=4                 # 超分倍数（2, 4, 8）
SWIN2SR_API_URL=http://localhost:8001  # API服务地址（API模式时使用）
```

## 使用方式

### 方式一：本地模型模式（推荐）

1. 下载 Swin2SR 模型文件
   - 官方仓库: https://github.com/mv-lab/swin2sr
   - 下载预训练模型权重

2. 将模型文件放入 `./weights/swin2sr/` 目录
   ```
   weights/swin2sr/
   ├── swin2sr.pth          # 模型权重文件
   └── config.json          # 模型配置文件（可选）
   ```

3. 设置 `SWIN2SR_USE_LOCAL=true`

4. 系统会自动加载模型并进行推理

### 方式二：API服务模式

1. 部署 Swin2SR API 服务到指定地址
2. 设置 `SWIN2SR_API_URL=http://your-service:port`
3. 系统会通过 HTTP 调用服务

### 方式三：备用模式（无需配置）

如果以上两种方式都不可用，系统会自动使用 **Lanczos 高质量插值** 作为备用方案，仍然可以实现图像放大。

## 工作流程

```
用户上传图像
    ↓
文档修复流程启动
    ↓
[STEP 1] 图像预处理
    ↓
[STEP 2] 超分辨率处理 (Swin2SR)
    ├─ 尝试加载 Swin2SR 本地模型
    ├─ 或使用 API 服务
    └─ 或使用 Lanczos 插值（备用）
    ↓
[STEP 3] OCR 文字识别（对超分后的图像）
    ↓
[STEP 4] 保存结果
    ↓
返回修复后的图像和 OCR 文本
```

## Swin2SR 模型特点

### 架构优势
- **Swin Transformer V2**: 基于窗口的自注意力机制
- **分层特征提取**: 多尺度特征融合
- **压缩图像恢复**: 专门针对压缩失真优化

### 适用场景
- ✅ 老旧文档数字化
- ✅ 低分辨率扫描件增强
- ✅ 压缩图像质量恢复
- ✅ 文档图像超分辨率

## API 接口

### 超分辨率对比测试

```http
POST /api/sr-comparison/test
Content-Type: multipart/form-data

file: <图像文件>
doc_type: document
```

返回结果包含：
- `original` - 原图 OCR 结果
- `super_resolved` - 超分后 OCR 结果
- `improvement` - 改进指标
- `is_better` - 是否有提升
- `repair_result.repaired_image_base64` - 超分后的图像

### 文档修复（带超分）

```http
POST /api/doc/repair
Content-Type: multipart/form-data

file: <图像文件>
doc_type: document
use_super_resolution: true
```

## 性能指标

系统会记录以下性能指标：

- 图像读取时间
- 图像预处理时间
- 超分辨率处理时间（Swin2SR 推理时间）
- OCR 文字识别时间
- 结果保存时间
- 总处理时间

## 模型下载

### 官方资源
- GitHub: https://github.com/mv-lab/swin2sr
- Hugging Face: https://huggingface.co/mv-lab/swin2sr

### 预训练模型
根据你的需求选择合适的模型：
- `Swin2SR_ClassicalSR_X4_64.pth` - 经典图像超分（4倍）
- `Swin2SR_CompressedSR_X4_48.pth` - 压缩图像恢复（4倍）
- `Swin2SR_RealworldSR_X4_64.pth` - 真实世界图像超分（4倍）

对于文档图像，推荐使用 **CompressedSR** 或 **RealworldSR** 版本。

## 测试验证

启动后端服务后，可以通过以下方式验证：

1. 打开前端页面 "超分辨率对比测试"
2. 上传一张低分辨率文档图像
3. 查看对比结果，确认：
   - 图像尺寸是否放大（如 400x300 → 1600x1200）
   - OCR 识别率是否有提升
   - 处理时间是否正常

## 注意事项

1. **GPU 内存**：Swin2SR 模型较大，确保 GPU 内存足够（建议 4GB+）
2. **模型文件**：将模型文件放在正确的路径下
3. **依赖安装**：运行 `pip install -r requirements.txt` 安装依赖
4. **环境变量**：确保 `.env` 文件配置正确

## 故障排查

### 问题：超分服务不可用

**现象**：日志显示 "Swin2SR 服务不可用"

**解决**：
- 检查模型文件是否存在
- 检查 PyTorch 是否正确安装
- 查看详细错误日志

### 问题：超分后图像质量没有提升

**现象**：对比测试显示无改进

**解决**：
- 确认 `use_super_resolution=true` 参数已传递
- 检查模型是否正确加载
- 查看处理日志中的方法信息

### 问题：处理时间过长

**现象**：超分处理耗时过长

**解决**：
- 使用 GPU 加速
- 减小输入图像尺寸
- 使用 Lanczos 插值模式（更快但质量稍低）

## 参考资料

- **论文**: https://arxiv.org/abs/2209.11345
- **官方代码**: https://github.com/mv-lab/swin2sr
- **Hugging Face**: https://huggingface.co/mv-lab/swin2sr
