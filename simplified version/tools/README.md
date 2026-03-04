# tools/ 使用指南

数据处理流水线工具集，将原始爬虫输出转换为可用于模型训练的结构化数据集。

---

## 整体流程

```
data/comments/comments_*.json   (爬虫输出)
         │
         ▼
  data_aggregator.py            整合、清洗多个 JSON 文件
         │
         ▼
  data/comment_aggregated/comments.json
         │
         ├──→ comment_to_dialogue_converter_fixed2.py  →  对话格式（问答对）
         │
         ├──→ long_comment_extractor.py                →  长评论格式（深度评测）
         │
         └──→ marketing_dialogue_classifier_fixed1.py  →  营销对话分类
                      │
                      ▼
              merge_datasets.py  合并真实评论 + 营销数据 → 最终训练集
```

---

## 工具说明

| 脚本 | 输入 | 输出 | 用途 |
|------|------|------|------|
| `data_aggregator.py` | `data/comments/comments_*.json` | `comments.json` + `titles.json` + `metadata.json` | 整合分散的评论文件 |
| `comment_to_dialogue_converter_fixed2.py` | `comments.json` | `converted_dialogues.txt` | 评论转对话格式 ⭐推荐 |
| `long_comment_extractor.py` | `comments.json` | `long_comments_full.txt` + `long_comments_top50.txt` | 提取长评论 |
| `marketing_dialogue_classifier_fixed1.py` | 对话数据 | 分类后的营销对话 | 营销场景分类 |
| `merge_datasets.py` | 营销对话 + 真实评论对话 | `merged_dataset.jsonl` | 合并多数据源 |
| `merge_and_managemnet/prepare_dialogue_generation.py` | `unified_all.jsonl` | 任务专用数据集 | 准备模型训练数据 |
| `merge_and_managemnet/real_marketing_data_merge_data_convertor.py` | 多源数据 | `unified_all.jsonl` | 统一格式转换 |

---

## 使用步骤

### 第一步：整合原始评论

```bash
python data_aggregator.py
```

输出到 `data/comment_aggregated/`：
- `comments.json` — 按帖子 ID 分组，含回复树结构
- `titles.json` — 笔记 ID → 标题映射
- `metadata.json` — 统计信息、热度排序

数据清洗说明：使用正则 `re.sub(r'回复.*?[：:]', '', content)` 移除"回复 用户名："前缀，兼容中英文冒号。

### 第二步A：转换为对话格式（推荐用于 AI 训练）

```bash
python comment_to_dialogue_converter_fixed2.py
```

**三种提取策略**，合计从 1163 条评论中提取 317 组对话（转换率 27.3%）：

| 策略 | 原理 | 贡献量 |
|------|------|--------|
| 明确回复链 | 识别"回复 XXX ："格式，BFS 构建对话树 | 132 组 (41.6%) |
| 关键词聚类 | 将提到相同关键词的评论聚为一组 | 59 组 (18.6%) |
| 智能问答配对 | 为高质量独立评论生成匹配问题 | 163 组 (51.4%) |

输出示例：
```
【对话 1】
a：会不会长痘?
b：我乳化了用也没见长痘 你要不试试？

【对话 2】
a：真的能美白吗?
b：用了两个月，白了很多
c：我也觉得有效果
```

品牌/产品名自动替换为占位符（A=产品名、B=品牌名、C=活动、D=平台）。

自定义参数：
```python
converter = EnhancedCommentConverter(mode='strict')    # 高质量，少数量
converter = EnhancedCommentConverter(mode='balanced')  # 默认
converter = EnhancedCommentConverter(mode='loose')     # 大数量

converter.min_turns = 2                # 最少对话轮数
converter.similarity_threshold = 0.85 # 去重相似度阈值
```

### 第二步B：提取长评论（推荐用于产品分析）

```bash
python long_comment_extractor.py
```

从 1163 条评论中筛选 67 条长评论（提取率 5.8%），按质量评分排序。

自动提取的结构化信息：
- 肤质（油皮 / 干皮 / 混合 / 敏感肌）
- 使用时长、价格、功效、质地、适用季节

输出示例：
```
【评论 1】质量分: 60.0
标签: 好评, 产品评测, 热门
关键信息: 肤质：混干 | 功效：美白/补水

【原文】
混干，只用了光感水和美白奶罐，个人觉得补水还不错...

【品牌替换后】
混干，只用了A3和A2，个人觉得补水还不错...
```

自定义参数：
```python
extractor = LongCommentExtractor(min_length=50)   # 默认50字
extractor = LongCommentExtractor(min_length=100)  # 更精选
```

### 第三步：合并数据集

```bash
python merge_datasets.py
```

将真实评论对话与营销对话数据合并，生成 `merged_dataset.jsonl`（可直接用于训练）。

安装依赖：
```bash
pip install python-docx
```

---

## 两种提取工具对比

| 特性 | 对话提取器 | 长评论提取器 |
|------|-----------|------------|
| 提取对象 | 多人对话链 | 单人长评论 |
| 输出数量 | 317 组 | 67 条 |
| 平均长度 | 2–3 轮 | 50–200 字 |
| 数据格式 | a/b/c 问答 | 段落 + 结构分析 |
| 信息密度 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 适用场景 | AI训练 / FAQ / 客服 | 产品分析 / 用户洞察 / 营销素材 |

**同时使用两者可获得最完整的数据覆盖。**

---

## 数据组织与训练格式

### 统一 JSONL 格式（推荐用于训练）

由 `merge_and_managemnet/real_marketing_data_merge_data_convertor.py` 生成：

```json
{
  "id": "real_dialogue_001",
  "type": "dialogue",
  "source": "real_comment",
  "content": {
    "turns": [
      {"speaker": "a", "text": "会不会长痘?"},
      {"speaker": "b", "text": "我乳化了用也没见长痘"}
    ]
  },
  "metadata": {
    "quality_score": 60,
    "turn_count": 2,
    "sentiment": "neutral",
    "tags": ["使用体验"],
    "length": 28
  }
}
```

数据总览（合并后）：

| 类型 | 真实评论 | 营销内容 | 合计 |
|------|---------|---------|------|
| 对话 | 317 组 | 245 组 | 562 组 |
| 长叙述 | 67 条 | 70 条 | 137 条 |
| **总计** | **384** | **315** | **699** |

### 针对不同训练任务的数据选择

| 训练任务 | 推荐数据 | 说明 |
|---------|---------|------|
| 对话生成 / 客服机器人 | 全部 562 组对话 | 混合真实+营销，50:50 |
| 营销文案生成 | 营销长叙述（70条）+ 营销对话 | 营销数据为主 |
| 情感分析 | 真实评论长叙述（67条）| 仅真实数据，已有情感标注 |
| 全面训练 | 全部 699 条 | 过滤质量分 < 30 的数据 |

```bash
# 准备对话生成训练数据（instruction 格式）
python merge_and_managemnet/prepare_dialogue_generation.py \
    --input converted_data/by_type/dialogues.jsonl \
    --output tasks/dialogue_generation \
    --format instruction \
    --context-window 3
```

支持的格式：`single_turn`、`instruction`（Alpaca/Vicuna/ChatGLM）、`chat`（GPT/Claude/Llama-2-Chat）

### 数据质量建议

- **高质量**（score ≥ 70）：188 条，用于主要训练
- **中质量**（40–69）：96 条，补充训练
- **低质量**（< 40）：98 条，建议过滤或降权
- **未评分**（317 条真实对话）：需人工评估或自动打分

---

## 注意事项

1. **路径配置**：脚本内有部分硬编码路径（如 `/mnt/user-data/uploads/`），使用前需按实际路径修改
2. **数据隐私**：真实评论数据已进行品牌替换脱敏，商业使用需确认授权
3. `comment_to_dialogue_converter.py`（原始版）和 `comment_to_dialogue_converter_fixed1_待修复.py` 为旧版本，请使用 `fixed2.py`
