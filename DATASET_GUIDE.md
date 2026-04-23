# 老旧文档修复系统 - 数据集构建指南

## 概述

本项目针对**近现代（民国末期至今）的退化中文文档**进行高清修复。本文档说明如何构建和管理数据集。

## 数据集来源

### 1. 公开数据集推荐

| 数据集名称 | 描述 | 适用性 | 获取方式 |
|------------|------|--------|----------|
| **民国档案数字化平台** | 国家图书馆民国文献 | 民国契约、家谱 | http://www.nlc.cn/oldbooks/ |
| **CADAL (大学数字图书馆** | 大量民国书籍、期刊 | 各类民国文档 | https://www.cadal.cn/ |
| **家谱数字化平台** | 各地方图书馆 | 各地家谱 | 各地方图书馆官网 |
| **百度网盘资源** | 网友分享的老照片、扫描件 | 各类老文档 | 搜索相关关键词 |
| **孔夫子旧书网** | 可购买实体书扫描 | 各类老文档 | https://www.kongfz.com/ |

### 2. 自行收集渠道

1. **家庭收藏**：祖辈留下的老照片、证书、契约等
2. **地方档案馆**：可以申请查阅和扫描
3. **旧书市场**：购买旧书、旧报纸等
4. **线上论坛**：相关收藏论坛、微信群等

## 数据集标注规范

### 文档分类 (CATEGORIES)

| 类别 | 说明 | 示例 |
|------|------|------|
| 契约 | 土地契约、房屋契约、买卖契约等 | 地契、房契 |
| 家谱 | 族谱、宗谱、家谱等 | 某氏家谱 |
| 证书 | 毕业证书、奖状、结婚证等 | 毕业证书 |
| 报纸 | 老报纸、期刊等 | 民国日报 |
| 书信 | 家书、信件等 | 家书 |
| 笔记 | 笔记、日记等 | 日记 |
| 书籍 | 旧书籍、教材等 | 旧书 |
| 照片 | 老照片、合影等 | 老照片 |
| 其他 | 不属于以上类别的文档 | - |

### 年代分类 (ERAS)

| 年代 | 时间范围 | 说明 |
|------|----------|------|
| 清末 | 1900年以前 | 清代晚期 |
| 民国 | 1912-1949 | 中华民国时期 |
| 建国初期 | 1949-1966 | 中华人民共和国成立初期 |
| 文革时期 | 1966-1976 | 文化大革命时期 |
| 改革开放后 | 1978-2000 | 改革开放时期 |
| 其他 | - | 其他年代 |

### 退化类型 (DEGRADATION_TYPES)

| 退化类型 | 说明 |
|----------|------|
| 泛黄 | 纸张老化变黄 |
| 撕裂 | 纸张有撕裂痕迹 |
| 墨迹扩散 | 墨迹晕染扩散 |
| 模糊 | 图像模糊、失焦 |
| 折痕 | 纸张有折痕 |
| 污渍 | 有各种污渍 |
| 水渍 | 有水渍痕迹 |
| 霉斑 | 有霉斑 |
| 缺角 | 纸张有缺角 |
| 褪色 | 颜色褪色 |

## 数据集目录结构

```
dataset/
├── metadata.json          # 数据集元数据
├── samples/             # 样本图像
│   ├── 001.png
│   ├── 002.png
│   └── ...
└── ground_truth/       # 真值文本（可选）
    ├── 001.txt
    ├── 002.txt
    └── ...
```

## 数据集管理API

### 初始化数据集管理器

```python
from pathlib import Path
from app.services.dataset_manager import DatasetManager, CATEGORIES, ERAS, DEGRADATION_TYPES

# 初始化
dataset_root = Path("path/to/dataset")
manager = DatasetManager(dataset_root)
```

### 添加样本

```python
# 添加一个样本
sample = manager.add_sample(
    image_path=Path("path/to/image.png"),
    category="契约",
    era="民国",
    degradation_types=["泛黄", "墨迹扩散"],
    ground_truth_text="民国三十五年正月...",
    notes="这是一份土地契约"
)

print(f"添加了样本: {sample.id}")
```

### 查询样本

```python
# 获取单个样本
sample = manager.get_sample("sample_id")

# 按条件过滤
samples = manager.list_samples(
    category="契约",
    era="民国",
    degradation_type="泛黄"
)

# 获取统计信息
stats = manager.get_statistics()
print(f"总样本数: {stats['total_samples']}")
print(f"有真值标注: {stats['samples_with_ground_truth']}")
```

## 评估指标使用

### 1. OCR字符错误率 (CER)

```python
from app.services.evaluation import calculate_cer

reference = "这是参考文本"
hypothesis = "这是识别文本"

cer, insertions, deletions, substitutions, ref_len = calculate_cer(reference, hypothesis)
print(f"CER: {cer:.2%}")
print(f"插入: {insertions}, 删除: {deletions}, 替换: {substitutions}")
```

### 2. 图像质量评估 (PSNR/SSIM)

```python
from app.services.evaluation import evaluate_repair_result, interpret_evaluation
from PIL import Image

original = Image.open("original.png")
repaired = Image.open("repaired.png")

report = evaluate_repair_result(original, repaired, reference_text="真值文本", ocr_text="OCR识别文本")
interpretations = interpret_evaluation(report)

print(f"PSNR: {report['image_quality']['psnr']:.2f} dB")
print(f"SSIM: {report['image_quality']['ssim']:.4f}")
print(f"解释: {interpretations}")
```

## 数据集构建建议

### 1. 样本数量建议

- **初期阶段**：30-50张样本（满足开题报告要求）
- **中期阶段**：100-200张样本
- **完整阶段**：500+张样本

### 2. 样本多样性

确保样本涵盖：
- 不同年代（清末、民国、建国初期等）
- 不同类型（契约、家谱、证书、报纸等）
- 不同纸张质量（好、中、差）
- 不同退化类型（泛黄、撕裂、墨迹扩散等）
- 不同字体（宋体、楷体、黑体、手写体）

### 3. 真值标注

对于重要的样本，建议进行人工真值标注：

1. 转录文档内容
2. 标注文档类型和年代
3. 标注退化类型
4. 记录特殊说明

## 注意事项

1. **版权问题**：确保使用的样本有合法的使用权限
2. **隐私保护**：对于包含个人信息的文档，进行适当的脱敏处理
3. **数据备份**：定期备份数据集，防止数据丢失
4. **版本管理**：对数据集进行版本管理，记录变更历史
