# 小红书评论爬虫 & 数据处理流水线

基于 Chrome CDP 协议的小红书评论采集工具，配套完整的数据清洗与格式转换流水线，输出可直接用于模型训练的结构化数据集。

---

## 目录结构

```
.
├── start_xiaohongshu_chrome.bat        # 启动 Chrome 调试模式
├── comment_extractor_fixed7.py         # 评论采集主脚本（当前推荐，V5.2）
├── comment_extractor_fixed8_ing.py     # 开发中（V6.0，含增量去重）
├── diagnose_web.py                     # 页面结构诊断工具
├── note_urls.txt                       # 批量处理的笔记 URL 列表
├── VERSIONS.md                         # 版本演进记录与功能对比
├── 小红书评论爬虫技术路线记录.md
├── old_version/                        # 历史版本归档（V1.0–V5.1）
├── data/                               # 采集与处理输出（已 .gitignore）
│   ├── comments/                       # 原始评论 JSON/CSV
│   ├── comment_aggregated/             # 整合后的评论数据
│   ├── comment_to_dialogue/            # 对话格式数据
│   ├── comment_to_single/              # 长评论数据
│   ├── marketing/                      # 营销分类数据
│   └── all_data_20251121/              # 最终整合数据集
└── tools/                              # 数据处理工具
    ├── README.md                       # 工具使用指南
    ├── data_aggregator.py              # 整合分散的评论 JSON
    ├── comment_to_dialogue_converter_fixed2.py  # 评论转对话格式
    ├── long_comment_extractor.py       # 长评论提取器
    ├── marketing_dialogue_classifier_fixed1.py  # 营销对话分类
    ├── merge_datasets.py               # 合并多数据源
    └── merge_and_managemnet/           # 统一格式转换与训练数据准备
```

---

## 核心架构

本项目采用**"人工登录 + 脚本接管"**的半自动化策略，规避小红书的滑块验证码和风控机制。

```
Chrome 调试模式（端口 9222）
        │
        ▼
comment_extractor_fixed7.py  ──→  data/comments/comments_*.json
                                           │
                                           ▼
                                tools/data_aggregator.py
                                           │
                                           ▼
                              data/comment_aggregated/comments.json
                                           │
                  ┌────────────────────────┼────────────────────────┐
                  ▼                        ▼                        ▼
   comment_to_dialogue_converter   long_comment_extractor   marketing_classifier
        （317 组对话）                  （67 条长评论）            （营销分类）
                  └────────────────────────┴────────────────────────┘
                                           │
                                           ▼
                                  merge_datasets.py
                                           │
                                           ▼
                               merged_dataset.jsonl（训练集）
```

---

## 快速开始

### 环境要求

```bash
pip install selenium python-docx
```

- Python 3.7+
- Google Chrome（已安装）
- ChromeDriver（版本需与 Chrome 匹配）

### 第一步：启动 Chrome 调试模式

双击运行 `start_xiaohongshu_chrome.bat`，脚本会：
1. 检测并关闭现有 Chrome 进程（可选）
2. 以 `--remote-debugging-port=9222` 启动 Chrome
3. 指定独立的用户数据目录，保持登录态

> 首次运行需在弹出的 Chrome 窗口中**手动登录小红书账号**，之后每次运行无需重新登录。

### 第二步：采集评论

```bash
python comment_extractor_fixed7.py
```

启动后选择模式：
- **单篇模式**：处理当前浏览器中已打开的笔记页面
- **批量模式**：读取 `note_urls.txt`，自动遍历所有 URL

编辑 `note_urls.txt` 配置批量 URL，每行一条，`#` 开头为注释：

```
# 格式示例
https://www.xiaohongshu.com/explore/[笔记ID]?xsec_token=...
```

输出保存在 `data/comments/`，每篇笔记生成 `comments_[笔记ID].json` 和对应 CSV。

### 第三步：整合数据

```bash
python tools/data_aggregator.py
```

输出到 `data/comment_aggregated/`：
- `comments.json` — 按帖子 ID 分组的完整评论树
- `titles.json` — 笔记 ID 到标题的映射
- `metadata.json` — 统计信息和热度排序

### 第四步：转换为训练格式

```bash
# 提取多轮对话（317 组，适合对话模型、客服机器人）
python tools/comment_to_dialogue_converter_fixed2.py

# 提取长评论（67 条，适合产品分析、用户洞察）
python tools/long_comment_extractor.py

# 合并多数据源，生成最终训练集
python tools/merge_datasets.py
```

详细参数配置与输出格式说明见 [tools/README.md](tools/README.md)。

---

## 数据格式

### 原始评论 JSON

```json
{
  "note_info": {
    "note_id": "6819d2a1000000002100fcf2",
    "note_title": "笔记标题",
    "note_url": "https://...",
    "author": "作者昵称"
  },
  "comments": [
    {
      "username": "用户A",
      "content": "评论内容",
      "likes": 12,
      "time": "2小时前",
      "comment_type": "主评论"
    }
  ],
  "total_comments": 42,
  "crawl_time": "2025-11-20 14:30:00"
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

| 文件 | 版本 | 状态 | 说明 |
|------|------|------|------|
| `old_version/comment_extractor_fixed1~6.py` | V2.0–V5.1 | 归档 | 历史迭代版本 |
| `comment_extractor_fixed7.py` | V5.2 | **当前推荐** | 稳定版，XPath 精确定位 |
| `comment_extractor_fixed8_ing.py` | V6.0 | 开发中 | 增量去重，代码精简 36% |

完整版本演进记录与功能对比见 [VERSIONS.md](VERSIONS.md)。

---

## 注意事项

- 运行期间**不要关闭**调试模式的 Chrome 窗口
- 批量爬取建议每批不超过 20 个 URL，两批之间适当间隔
- 小红书页面结构可能随版本更新变化，如遇元素定位失败可运行 `diagnose_web.py` 诊断
- 本工具仅供学习研究使用，请遵守小红书用户协议及相关法律法规
