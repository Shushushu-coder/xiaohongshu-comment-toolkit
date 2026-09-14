# 小红书评论爬虫 & 数据处理流水线

基于 Chrome CDP 协议的小红书评论采集工具，配套数据清洗与格式转换工具，输出可用于模型训练的结构化数据集。

正式工具之间的契约以代码的默认读写路径为准。工具不是一条必须跑完的线性流水线：采集与对话合并是主路径，其余为可选分析或快照转换。

---

## 目录结构

```
.
├── start_chrome_debug.bat              # 启动 Chrome 调试模式
├── scraper.py                          # 评论采集主脚本
├── diagnose.py                         # 页面结构诊断工具（独立）
├── examples/
│   └── note_urls.example.txt           # 批量 URL 列表示例
├── docs/
│   └── technical-notes.md              # 技术路线说明
├── data/                               # 采集与处理输出（已 .gitignore）
│   ├── comments/                       # scraper 原始评论 JSON/CSV
│   ├── aggregated/                     # aggregator 整合后的评论数据
│   ├── comment_to_dialogue/            # 对话格式数据
│   ├── comment_to_single/              # 长评论提取（可选）
│   ├── marketing/                      # 营销源文件与分类输出（可选）
│   └── all_data_20251121/              # 快照训练转换输入/输出（独立 workflow）
└── tools/                              # 数据处理工具
    ├── README.md                       # 工具使用指南与契约说明
    ├── data_aggregator.py              # 整合分散的评论 JSON
    ├── comment_to_dialogue.py          # 评论转对话格式
    ├── long_comment_extractor.py       # 长评论提取器（可选）
    ├── marketing_classifier.py         # 营销对话分类（可选）
    ├── merge_datasets.py               # 合并营销对话 + 真实评论对话
    ├── test_pipeline_contract.py       # 合成数据契约冒烟测试
    └── merge_and_management/           # 快照目录上的统一格式转换
```

---

## 核心架构

本项目采用**"人工登录 + 脚本接管"**的半自动化策略，规避小红书的滑块验证码和风控机制。

```
Core collection
Chrome 调试模式（端口 9222）
        │
        ▼
scraper.py
        │
        ▼
data/comments/comments_{note_id}_{timestamp}_v6.json
        │
        ▼
tools/data_aggregator.py
        │
        ▼
data/aggregated/comments.json
        │
        ▼
tools/comment_to_dialogue.py
        │
        ▼
data/comment_to_dialogue/dialogues_enhanced.txt
        │
        ▼
tools/merge_datasets.py  ←  另读 data/marketing/营销对话数据.docx
        │
        ▼
data/merged_dataset.jsonl  (+ .json / .txt)

Optional analysis
├── tools/long_comment_extractor.py
│     读取 aggregated/comments.json
│     写出 data/comment_to_single/long_comments_*.txt
└── tools/marketing_classifier.py
      读取 data/marketing/营销对话数据.docx
      写出 marketing_dialogues.txt / marketing_narratives_*.txt

Optional snapshot conversion（需自行把文件放到快照目录并使用约定文件名）
└── tools/merge_and_management/
```

`marketing_classifier.py` 与 `merge_datasets.py` 都读取同一份营销 DOCX，但不是上下游：分类器写出拆分后的 txt；`merge_datasets.py` 直接解析 DOCX。

---

## 快速开始

### 环境要求

- Tested with Python 3.10
- Google Chrome（已安装）
- ChromeDriver（版本需与 Chrome 匹配）

### 安装依赖

```powershell
python -m pip install -r requirements.txt
```

### 第一步：启动 Chrome 调试模式

双击运行 `start_chrome_debug.bat`，脚本会：
1. 检测并关闭现有 Chrome 进程（可选）
2. 以 `--remote-debugging-port=9222` 启动 Chrome
3. 指定独立的用户数据目录，保持登录态

> 首次运行需在弹出的 Chrome 窗口中**手动登录小红书账号**，之后每次运行无需重新登录。

### 第二步：采集评论

```bash
python scraper.py
```

启动后选择模式：
- **单篇模式**：处理当前浏览器中已打开的笔记页面
- **批量模式**：读取 `note_urls.txt`，自动遍历所有 URL

`note_urls.txt` 是本地运行输入，已加入 `.gitignore`，clone 后需要从示例复制：

```powershell
Copy-Item .\examples\note_urls.example.txt .\note_urls.txt
```

```bash
cp examples/note_urls.example.txt note_urls.txt
```

编辑 `note_urls.txt`，每行填写一个需要处理的小红书笔记 URL。`#` 开头为注释。公开示例见 `examples/note_urls.example.txt`：

```
# One Xiaohongshu note URL per line
https://www.xiaohongshu.com/explore/<NOTE_ID>
```

输出保存在 `data/comments/`。每篇笔记生成：

- `comments_{笔记ID}_{时间戳}_v6.json` — 正式下游输入
- 同名 `.csv` — 侧车导出，无正式消费者
- `summary_{时间戳}_v6.txt` — 采集摘要，无正式消费者

### 第三步：整合数据（主路径必选）

`comment_to_dialogue.py` 和 `long_comment_extractor.py` 读取的是按帖子 ID 分组的 `comments.json`，不是 scraper 的单篇 JSON。必须先整合：

```bash
python tools/data_aggregator.py
```

输出到 `data/aggregated/`：
- `comments.json` — 按帖子 ID 分组的评论列表（下游 canonical 输入）
- `titles.json` — 笔记 ID 到标题的映射（无正式消费者）
- `metadata.json` — 统计信息和热度排序（无正式消费者）

### 第四步：转换为对话并合并训练集

```bash
python tools/comment_to_dialogue.py
python tools/merge_datasets.py
```

`comment_to_dialogue.py` 写出 `data/comment_to_dialogue/dialogues_enhanced.txt`。

`merge_datasets.py` 默认读取：
- `data/comment_to_dialogue/dialogues_enhanced.txt`
- `data/marketing/营销对话数据.docx`（需自行放置）

并写出：
- `data/merged_dataset.jsonl`
- `data/merged_dataset.json`
- `data/merged_dataset.txt`

可选分析（不是 `merge_datasets.py` 的输入）：

```bash
python tools/long_comment_extractor.py
python tools/marketing_classifier.py
```

详细参数、canonical 文件名与独立 workflow 说明见 [tools/README.md](tools/README.md)。

---

## 数据格式

### 原始评论 JSON

```json
{
  "note_info": {
    "note_id": "6819d2a1000000002100fcf2",
    "note_title": "笔记标题",
    "note_url": "https://...",
    "author": "作者昵称",
    "publish_time": "",
    "likes": 0,
    "collects": 0
  },
  "comment_count": 42,
  "collected_at": "2025-11-20T14:30:00",
  "version": "V6",
  "comments": [
    {
      "comment_id": "comment_1",
      "username": "用户A",
      "content": "评论内容",
      "time": "2小时前",
      "likes": 12,
      "collected_at": "2025-11-20T14:30:00"
    }
  ]
}
```

### 对话格式输出

```
【对话 1】
a：会不会长痘?
b：我乳化了用也没见长痘 你要不试试？

【对话 2】
a：真的能美白吗?
b：用了两个月，白了很多
c：我也觉得有效果
```

品牌名、产品名自动替换为占位符（A=产品名、B=品牌名、C=活动、D=平台）进行脱敏。

---

## 版本说明

当前正式采集入口为 `scraper.py`。技术说明见 [docs/technical-notes.md](docs/technical-notes.md)。

---

## 注意事项

- 运行期间**不要关闭**调试模式的 Chrome 窗口
- 批量爬取建议每批不超过 20 个 URL，两批之间适当间隔
- 小红书页面结构可能随版本更新变化，如遇元素定位失败可运行 `diagnose.py` 诊断
- 本工具仅供学习研究使用，请遵守小红书用户协议及相关法律法规
