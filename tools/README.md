# tools/ 使用指南

数据处理工具集。默认路径以各脚本代码为准；文档与代码冲突时以代码为准。

工具分成三条线，不要当成必须串行的一条流水线：

```
Core collection
data/comments/comments_{note_id}_{timestamp}_v6.json   (scraper 输出)
         │
         ▼
  data_aggregator.py
         │
         ▼
  data/aggregated/comments.json
         │
         ▼
  comment_to_dialogue.py
         │
         ▼
  data/comment_to_dialogue/dialogues_enhanced.txt
         │
         ▼
  merge_datasets.py  ←  另读 data/marketing/营销对话数据.docx
         │
         ▼
  data/merged_dataset.jsonl  (+ .json / .txt)

Optional analysis
  long_comment_extractor.py     读取 aggregated/comments.json
                                写出 data/comment_to_single/long_comments_*.txt
  marketing_classifier.py       读取营销 DOCX
                                写出 data/marketing/marketing_*.txt

Optional snapshot conversion
  merge_and_management/*        读取 data/all_data_20251121/ 下的约定文件名
                                不自动消费上面的 live 输出
```

---

## Canonical artifacts

跨工具只使用下列默认名。历史名 `converted_dialogues.txt` 不是当前正式输出。

| Artifact | Producer | Consumer |
|----------|----------|----------|
| `data/comments/comments_{note_id}_{timestamp}_v6.json` | `scraper.py` | `data_aggregator.py`（glob：`comments_*.json`） |
| `data/aggregated/comments.json` | `data_aggregator.py` | `comment_to_dialogue.py`、`long_comment_extractor.py` |
| `data/comment_to_dialogue/dialogues_enhanced.txt` | `comment_to_dialogue.py` | `merge_datasets.py` |
| `data/marketing/营销对话数据.docx` | 外部放入 | `merge_datasets.py`、`marketing_classifier.py` |
| `data/merged_dataset.jsonl` | `merge_datasets.py` | 终端产物（无代码消费者） |

侧车输出（有 producer、无正式 live consumer）：scraper 的 CSV / `summary_*.txt`；aggregator 的 `titles.json` / `metadata.json`；`report_enhanced.txt`；`long_comments_full.txt` / `long_comments_top50.txt` / `long_comments_report.txt`；`marketing_dialogues.txt` / `marketing_narratives_full.txt` / `marketing_narratives_top50.txt` / `marketing_classification_report.txt`；`merged_dataset.json` / `merged_dataset.txt`（`merged_dataset.jsonl` 是 merge 的 canonical 终端产物，同样无代码消费者）。

---

## 工具说明

| 脚本 | 分类 | 默认输入 | 默认输出 | 用途 |
|------|------|----------|----------|------|
| `data_aggregator.py` | 主路径 | `data/comments/comments_*.json` | `data/aggregated/comments.json` + `titles.json` + `metadata.json` | 把 scraper 单篇 JSON 整合成按帖子分组的 `comments.json` |
| `comment_to_dialogue.py` | 主路径 | `data/aggregated/comments.json` | `data/comment_to_dialogue/dialogues_enhanced.txt` | 评论转 a/b/c 对话文本 |
| `merge_datasets.py` | 主路径 | 营销 DOCX + `dialogues_enhanced.txt` | `data/merged_dataset.jsonl` / `.json` / `.txt` | 合并营销对话与真实评论对话 |
| `long_comment_extractor.py` | 可选分析 | `data/aggregated/comments.json` | `data/comment_to_single/long_comments_full.txt` 等 | 提取长评论；无 live 下游 |
| `marketing_classifier.py` | 可选分析 | `data/marketing/营销对话数据.docx` | `marketing_dialogues.txt`、`marketing_narratives_*.txt` | 把营销 DOCX 拆成多轮对话 / 长叙述 |
| `merge_and_management/real_marketing_data_merge_data_convertor.py` | 快照转换 | `data/all_data_20251121/{real_dialogues,marketing_dialogues,real_narratives_full,marketing_narratives_full}.txt` | `converted_data/unified_all.jsonl` 等 | 将快照目录中的 txt 转为统一 JSONL |
| `merge_and_management/prepare_dialogue_generation.py` | 快照转换 | `--input` JSONL（无默认） | `--output` 目录 | 把 convertor 的对话 JSONL 转成训练任务格式 |

`diagnose.py` 在仓库根目录，属于页面诊断工具，不进入数据 pipeline。

---

## 使用步骤

### 第一步：整合原始评论

```powershell
python tools\data_aggregator.py
```

扫描 `data/comments/comments_*.json`（匹配 scraper 的 `comments_{id}_{timestamp}_v6.json`）。

输出到 `data/aggregated/`：
- `comments.json` — `{post_id: [ {comment_id, username, content, length, likes, replies?} ]}`
- `titles.json` — 笔记 ID → 标题
- `metadata.json` — 统计信息、热度排序

`comments.json` 里的 `length` 用正则 `re.sub(r'回复.*?[：:]', '', content)` 去掉回复前缀后再计算；`content` 字段仍保留原文。scraper 当前不写 `replies` / `sub_comments`，这些字段只在源 JSON 已有时透传。

### 第二步A：转换为对话格式（主路径）

```powershell
python tools\comment_to_dialogue.py
```

读取 `data/aggregated/comments.json`，写出：

- `data/comment_to_dialogue/dialogues_enhanced.txt`
- `data/comment_to_dialogue/report_enhanced.txt`（报告，无消费者）

文本结构：

```
评论转对话 - 增强版输出
==================================================

【对话 1】
a：会不会长痘?
b：我乳化了用也没见长痘 你要不试试？

【对话 2】
a：真的能美白吗?
b：用了两个月，白了很多
c：我也觉得有效果
```

编码 UTF-8。品牌/产品名替换为占位符（A=产品名、B=品牌名、C=活动、D=平台）。

自定义参数：
```python
converter = EnhancedCommentConverter(mode='strict')    # 高质量，少数量
converter = EnhancedCommentConverter(mode='balanced')  # 默认
converter = EnhancedCommentConverter(mode='loose')     # 大数量

converter.min_turns = 2
converter.similarity_threshold = 0.85
```

### 第二步B：提取长评论（可选，用于产品分析）

```powershell
python tools\long_comment_extractor.py
```

读取 `data/aggregated/comments.json`，输出到 `data/comment_to_single/`：

- `long_comments_full.txt`
- `long_comments_top50.txt`
- `long_comments_report.txt`

当前没有正式工具读取这些文件。`merge_and_management` 快照转换期望的是 `real_narratives_full.txt`，不会自动消费本工具输出。

自定义参数：
```python
extractor = LongCommentExtractor(min_length=50)   # 默认50字
extractor = LongCommentExtractor(min_length=100)  # 更精选
```

### 第三步：合并数据集（主路径）

```powershell
python tools\merge_datasets.py
```

默认读取：
- `data/marketing/营销对话数据.docx`
- `data/comment_to_dialogue/dialogues_enhanced.txt`

写出 `data/merged_dataset.jsonl`、`.json`、`.txt`。

依赖安装见仓库根目录：

```powershell
python -m pip install -r requirements.txt
```

---

## 可选：营销分类

```powershell
python tools\marketing_classifier.py
```

默认读取 `data/marketing/营销对话数据.docx`，在同一目录写出：

- `marketing_dialogues.txt`
- `marketing_narratives_full.txt`
- `marketing_narratives_top50.txt`
- `marketing_classification_report.txt`

这与 `merge_datasets.py` 是并行消费同一 DOCX，不是 merge 的前置步骤。

分类 txt 的文件名与 `real_marketing_data_merge_data_convertor.py` 期望的 `marketing_dialogues.txt` / `marketing_narratives_full.txt` 一致，但默认目录不同（`data/marketing/` vs `data/all_data_20251121/`）。要把它们送进快照转换，需要手动复制到快照目录，并另外准备 `real_dialogues.txt` / `real_narratives_full.txt`。不要改 live 输出名去迁就快照目录。

---

## 两种提取工具对比

| 特性 | 对话提取器 | 长评论提取器 |
|------|-----------|------------|
| 提取对象 | 多人对话链 | 单人长评论 |
| 数据格式 | a/b/c 问答 | 段落 + 结构分析 |
| 是否进入 merge_datasets | 是 | 否 |
| 适用场景 | 对话合并 / 训练文本 | 产品分析 / 用户洞察 |

---

## 快照转换与训练格式（独立 workflow）

`merge_and_management/` 面向已经整理好的快照目录，默认：

```
data/all_data_20251121/
  real_dialogues.txt
  marketing_dialogues.txt
  real_narratives_full.txt
  marketing_narratives_full.txt
```

```powershell
python tools\merge_and_management\real_marketing_data_merge_data_convertor.py
```

默认输出 `data/all_data_20251121/converted_data/`：

- `unified_all.jsonl`
- `by_type/dialogues.jsonl`、`by_type/narratives.jsonl`
- `by_source/`、`by_quality/`、`dataset/`、`statistics.json`

统一 JSONL 记录形状（由 convertor 生成，与 `merged_dataset.jsonl` 的 schema 不同）：

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
    "turn_count": 2,
    "participant_count": 2,
    "total_length": 28
  }
}
```

`merge_datasets.py` 的 JSONL 是另一套字段：`id` / `dialogue` / `type` / `source` / `label`。两套训练集不要混用默认路径。

准备对话生成任务数据：

```powershell
python tools\merge_and_management\prepare_dialogue_generation.py `
    --input data\all_data_20251121\converted_data\by_type\dialogues.jsonl `
    --output data\all_data_20251121\tasks\dialogue_generation `
    --format instruction `
    --context-window 3
```

`--input` 与 `--output` 均为必填。支持的格式：`single_turn`、`instruction`、`chat`。

---

## 注意事项

1. **路径配置**：正式 live 工具默认读写仓库内 `data/`。营销 DOCX 需放到 `data/marketing/营销对话数据.docx`。
2. **不要使用** `converted_dialogues.txt` 作为当前默认输入或输出名。
3. **数据隐私**：真实评论数据会做品牌替换脱敏，商业使用需确认授权。
4. 对话转换请使用 `comment_to_dialogue.py`。
