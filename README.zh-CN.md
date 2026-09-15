# Xiaohongshu Comment Toolkit

[English](README.md) | **简体中文**

## 项目简介

一个用于采集和处理小红书评论数据的轻量级研究与数据分析工具集。

面向需要从已登录浏览器会话中收集评论，再做聚合、对话转换或数据集合并的研究与分析场景。

它不是完整的小红书爬虫平台。

本工具集涵盖：

- 评论采集
- 数据聚合
- 对话转换
- 可选分析工具
- 数据集合并

## 功能

- 通过 Selenium + Chrome DevTools Protocol 接入浏览器会话
- 支持单条笔记与批量评论采集
- 在页面上展开长评论与嵌套回复，再提取扁平评论列表
- 输出 JSON / CSV / 摘要
- 评论聚合
- 评论转对话
- 可选的长评论分析
- 可选的营销文本分类
- 数据集合并

## 环境要求

- Windows
- Google Chrome
- Python 3.10（已测试）

```powershell
python -m pip install -r requirements.txt
```

## 快速开始

```powershell
git clone https://github.com/Shushushu-coder/xiaohongshu-comment-toolkit.git
cd xiaohongshu-comment-toolkit

python -m pip install -r requirements.txt

Copy-Item .\examples\note_urls.example.txt .\note_urls.txt
```

然后：

1. 编辑 `note_urls.txt`，每行放一个小红书笔记 URL（`#` 开头为注释）。
2. 运行 `.\start_chrome_debug.bat`。
3. 在打开的 Chrome 窗口中正常登录小红书。
4. 在仓库根目录运行：

```powershell
python scraper.py
```

采集脚本是交互式的。可选择单条笔记（当前标签页）、从 `note_urls.txt` 批量采集，或手动粘贴 URL。

`note_urls.txt` 是本地运行时文件，已被 Git 忽略。请继续使用已跟踪的示例文件 `examples/note_urls.example.txt`。

## 工作原理

程序通过 Chrome DevTools Protocol 连接由用户自行启动和登录的 Chrome 浏览器会话。用户在浏览器中正常登录后，脚本只处理该会话中可访问的页面。

## 主工作流程

实时采集与处理路径：

```text
Collection
python scraper.py
↓
data/comments/*.json

Aggregation
python tools\data_aggregator.py
↓
data/aggregated/comments.json

Dialogue Conversion
python tools\comment_to_dialogue.py
↓
data/comment_to_dialogue/dialogues_enhanced.txt

Dataset Merge
python tools\merge_datasets.py
↓
data/merged_dataset.jsonl
```

`merge_datasets.py` 还会读取 `data/marketing/营销对话数据.docx`，该文件需由你自行放到该路径。

`data_aggregator.py` 会提示输入目录；直接按 Enter 即使用默认目录 `data/comments`。

长评论提取、营销文本分类、页面诊断以及 `tools/merge_and_management/` 都不是这条路径的必要步骤。工具级输入/输出约定见 [tools/README.md](tools/README.md)。实现说明见 [docs/technical-notes.md](docs/technical-notes.md)。

## 可选分析工具

### `tools/long_comment_extractor.py`

- 用途：从聚合数据中提取较长的单作者评论
- 默认输入：`data/aggregated/comments.json`
- 默认输出：`data/comment_to_single/long_comments_full.txt`、`long_comments_top50.txt`、`long_comments_report.txt`

```powershell
python tools\long_comment_extractor.py
```

### `tools/marketing_classifier.py`

- 用途：将营销 DOCX 拆分为多轮对话与较长叙述文本
- 默认输入：`data/marketing/营销对话数据.docx`
- 默认输出：`data/marketing/marketing_dialogues.txt`、`marketing_narratives_full.txt`、`marketing_narratives_top50.txt`、`marketing_classification_report.txt`

```powershell
python tools\marketing_classifier.py
```

该工具与 `merge_datasets.py` 并行（两者读取同一份 DOCX），不是合并步骤的前置条件。

### `diagnose.py`

- 用途：检查当前 Chrome 标签页源码中的点赞 / 收藏 / 评论数信号
- 默认输入：已接入 Chrome 会话中当前打开的页面
- 默认输出：仓库根目录下的 `interaction_diagnosis.txt`（已被 Git 忽略）

```powershell
python diagnose.py
```

## 快照 / 历史数据工具

`tools/merge_and_management/` 是独立的快照工作流。

该工作流使用独立的文件命名约定，不属于实时采集主流程。

默认快照输入目录：`data/all_data_20251121/`，文件名例如 `real_dialogues.txt` 和 `marketing_dialogues.txt`。命令见 [tools/README.md](tools/README.md)。

## 项目结构

```text
xiaohongshu-comment-toolkit/
├── scraper.py
├── diagnose.py
├── start_chrome_debug.bat
├── requirements.txt
├── examples/
│   └── note_urls.example.txt
├── tools/
│   ├── data_aggregator.py
│   ├── comment_to_dialogue.py
│   ├── long_comment_extractor.py
│   ├── marketing_classifier.py
│   ├── merge_datasets.py
│   └── merge_and_management/
├── docs/
│   └── technical-notes.md
└── data/                       # 本地生成，Git 忽略
```

## 输出文件

| 文件 | 用途 |
|----------|---------|
| `data/comments/comments_{note_id}_{timestamp}_v6.json` | 供聚合使用的单笔记采集结果。`_v6` 是当前文件名后缀，不是产品版本号。 |
| `data/comments/*.csv`、`summary_*_v6.txt` | 采集过程的附属导出文件 |
| `data/aggregated/comments.json` | 规范的聚合评论文件 |
| `data/aggregated/titles.json`、`metadata.json` | 聚合过程的附属导出文件 |
| `data/comment_to_dialogue/dialogues_enhanced.txt` | 供合并使用的对话文本 |
| `data/merged_dataset.jsonl` | 规范的合并数据集（同时还会写出 `.json` / `.txt`） |
| `data/comment_to_single/long_comments_*.txt` | 可选的长评论分析 |
| `data/marketing/marketing_*.txt` | 可选的营销文本分类 |

## 已知限制

- 依赖当前小红书页面结构
- 需要登录的内容必须使用已登录的浏览器会话
- 页面结构变化时，选择器可能需要维护
- 面向小规模研究 / 分析工作流
- 主要在文档所述的 Windows + Chrome + Python 3.10 环境中测试
- 采集、聚合和诊断均为交互式提示，不提供 CLI 参数
- 采集到的评论以扁平列表存储，不是嵌套回复树
- 数据集合并要求营销 DOCX 位于默认路径

## 负责任使用

请仅将本项目用于你有权访问的内容，并遵守适用的平台条款、法律法规、研究伦理与隐私要求。

## 许可证

本项目采用 [MIT License](LICENSE)。
