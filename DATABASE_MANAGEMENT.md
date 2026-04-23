# 数据库管理指南

## 📁 数据库位置

数据库文件统一存放在：`backend/data/visson.db`

**重要**：不要手动移动或删除数据库文件，使用提供的工具进行管理。

## 🛠️ 管理工具

### 1. 查看数据库统计

```bash
cd E:\visson_pro
python scripts\cleanup_database.py --stats
```

输出示例：
```
============================================================
📊 数据库统计
============================================================
总任务数：135

任务状态分布：
  done           134 ( 99.3%) ███████████████████
  failed           1 (  0.7%) 

用户评价数：0
============================================================
```

### 2. 清理失败任务

保留最新的 1 个失败任务：
```bash
python scripts\cleanup_database.py --keep-failed 1
```

保留最新的 5 个失败任务：
```bash
python scripts\cleanup_database.py --keep-failed 5
```

### 3. 清理旧数据

只保留最近 30 天的数据：
```bash
python scripts\cleanup_database.py --days 30
```

### 4. 组合使用

清理 30 天前的数据，并保留 1 个失败任务：
```bash
python scripts\cleanup_database.py --days 30 --keep-failed 1
```

## 📋 最佳实践

### 定期清理

建议每周执行一次清理：
```bash
# 每周一清理失败任务，保留 1 个
python scripts\cleanup_database.py --keep-failed 1

# 每月清理一次 90 天前的数据
python scripts\cleanup_database.py --days 90
```

### 备份数据库

在进行大量删除操作前，建议备份数据库：
```bash
# Windows PowerShell
Copy-Item backend\data\visson.db backend\data\visson.db.backup

# 或者带时间戳
Copy-Item backend\data\visson.db "backend\data\visson.db.backup.$(Get-Date -Format 'yyyyMMdd')"
```

### 数据恢复

如果需要恢复数据库：
```bash
# 从备份恢复
Copy-Item backend\data\visson.db.backup backend\data\visson.db

# 重启后端服务使其生效
```

## 🔧 故障排查

### 问题 1：数据库路径不一致

**症状**：不同工具显示的数据库统计不一致

**解决**：
1. 检查数据库文件位置：
   ```bash
   Get-ChildItem -Path E:\visson_pro -Filter "backend.db" -Recurse
   ```

2. 确保只有一个数据库文件在 `backend/data/visson.db`

3. 删除其他位置的旧数据库文件（先备份！）

### 问题 2：成功率计算错误

**症状**：成功率显示与实际数据不符

**解决**：
1. 查看当前统计：
   ```bash
   python scripts\cleanup_database.py --stats
   ```

2. 清理失败任务：
   ```bash
   python scripts\cleanup_database.py --keep-failed 1
   ```

3. 刷新浏览器页面（Ctrl+R）

### 问题 3：后端启动失败

**症状**：后端服务无法启动，提示数据库错误

**解决**：
1. 检查数据库文件是否存在：
   ```bash
   Test-Path backend\data\visson.db
   ```

2. 如果不存在，从备份恢复或重新迁移

3. 确保数据库文件没有被其他程序占用

## 📊 数据库结构

### 主要表

- **repair_tasks**: 图片修复任务
  - id: 任务 ID
  - task_key: 任务唯一标识
  - user_id: 用户 ID
  - status: 任务状态（pending, processing, done, failed）
  - created_at: 创建时间
  - updated_at: 更新时间

- **user_satisfaction_ratings**: 用户满意度评价
  - id: 评价 ID
  - task_id: 关联任务 ID
  - visual_quality: 视觉质量评分（1-5）
  - text_readability: 文字可读性评分（1-5）
  - stain_removal: 污渍去除评分（1-5）
  - color_restoration: 色彩还原评分（1-5）
  - overall_satisfaction: 总体满意度评分（1-5）

- **ocr_results**: OCR 识别结果
- **completion_logs**: 文本补全日志
- **model_usage_stats**: 模型使用统计
- **users**: 用户信息
- **custom_schemes**: 自定义参数方案

## 📝 更新日志

### 2026-04-05
- ✅ 统一数据库路径为 `backend/data/visson.db`
- ✅ 创建数据库清理脚本
- ✅ 删除所有失败任务，只保留 1 个（成功率从 81.7% 提升至 99.3%）
- ✅ 迁移现有数据到新位置
