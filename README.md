# Xiaohongshu Comment Toolkit

A lightweight toolkit for collecting and processing Xiaohongshu comment data for research and analysis.

轻量级小红书评论采集与研究数据处理工具包。面向需要从已登录浏览器会话中收集评论，再做聚合、对话转换或数据集合并的研究与分析场景。

它不是完整的小红书爬虫平台。

## What this project includes

- Comment collection
- Data aggregation
- Dialogue conversion
- Optional analysis utilities
- Dataset merging

## Features

- Selenium + Chrome DevTools Protocol browser attachment
- Single-note and batch comment collection
- Expands long comments and nested replies on the page, then extracts a flat comment list
- JSON / CSV / summary output
- Comment aggregation
- Comment-to-dialogue conversion
- Optional long-comment analysis
- Optional marketing-text classification
- Dataset merging

## Requirements

- Windows
- Google Chrome
- Python 3.10 (tested)

```powershell
python -m pip install -r requirements.txt
```

## Quick Start

```powershell
git clone https://github.com/Shushushu-coder/xiaohongshu-comment-toolkit.git
cd xiaohongshu-comment-toolkit

python -m pip install -r requirements.txt

Copy-Item .\examples\note_urls.example.txt .\note_urls.txt
```

Then:

1. Edit `note_urls.txt` and put one Xiaohongshu note URL per line (`#` starts a comment).
2. Run `start_chrome_debug.bat`.
3. In the Chrome window that opens, log in to Xiaohongshu normally.
4. From the repository root, run:

```powershell
python scraper.py
```

The scraper is interactive. Choose single-note (current tab), batch from `note_urls.txt`, or paste URLs manually.

`note_urls.txt` is a local runtime file and is gitignored. Keep using the tracked example at `examples/note_urls.example.txt`.

The scraper connects to a user-controlled Chrome session through Chrome DevTools Protocol. Users log in normally in the browser, and the script processes pages accessible in that session.

程序通过 Chrome DevTools Protocol 连接用户自行启动并登录的浏览器会话。

## Workflow

Live collection and processing path:

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

`merge_datasets.py` also reads `data/marketing/营销对话数据.docx`, which you must place there yourself.

`data_aggregator.py` prompts for an input directory; press Enter to use the default `data/comments`.

Long-comment extraction, marketing classification, page diagnosis, and `tools/merge_and_management/` are not required steps in this path. Tool-level input/output contracts are in [tools/README.md](tools/README.md). Implementation notes: [docs/technical-notes.md](docs/technical-notes.md).

## Optional Analysis Tools

### `tools/long_comment_extractor.py`

- Purpose: extract longer single-author comments from aggregated data
- Default input: `data/aggregated/comments.json`
- Default output: `data/comment_to_single/long_comments_full.txt`, `long_comments_top50.txt`, `long_comments_report.txt`

```powershell
python tools\long_comment_extractor.py
```

### `tools/marketing_classifier.py`

- Purpose: split a marketing DOCX into multi-turn dialogues and longer narratives
- Default input: `data/marketing/营销对话数据.docx`
- Default output: `data/marketing/marketing_dialogues.txt`, `marketing_narratives_full.txt`, `marketing_narratives_top50.txt`, `marketing_classification_report.txt`

```powershell
python tools\marketing_classifier.py
```

This is parallel to `merge_datasets.py` (both read the same DOCX). It is not a merge prerequisite.

### `diagnose.py`

- Purpose: inspect the current Chrome tab for like / collect / comment count signals in page source
- Default input: the page already open in the attached Chrome session
- Default output: `interaction_diagnosis.txt` in the repository root (gitignored)

```powershell
python diagnose.py
```

## Snapshot / Historical Dataset Utilities

`tools/merge_and_management/` is an independent snapshot workflow.

It uses a separate artifact naming convention and is not part of the live collection pipeline.

Default snapshot input directory: `data/all_data_20251121/`, with names such as `real_dialogues.txt` and `marketing_dialogues.txt`. See [tools/README.md](tools/README.md) for commands.

## Project structure

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
└── data/                       # generated locally, ignored
```

## Output artifacts

| Artifact | Purpose |
|----------|---------|
| `data/comments/comments_{note_id}_{timestamp}_v6.json` | Per-note collection result used by aggregation. `_v6` is the current filename suffix, not a product version. |
| `data/comments/*.csv`, `summary_*_v6.txt` | Sidecar collection exports |
| `data/aggregated/comments.json` | Canonical aggregated comments |
| `data/aggregated/titles.json`, `metadata.json` | Sidecar aggregation exports |
| `data/comment_to_dialogue/dialogues_enhanced.txt` | Dialogue text for merge |
| `data/merged_dataset.jsonl` | Canonical merged dataset (also writes `.json` / `.txt`) |
| `data/comment_to_single/long_comments_*.txt` | Optional long-comment analysis |
| `data/marketing/marketing_*.txt` | Optional marketing classification |

## Known Limitations

- Depends on current Xiaohongshu page structure
- Requires an authenticated browser session for content that requires login
- Selectors may need maintenance when page markup changes
- Intended for small-scale research / analysis workflows
- Tested primarily on the documented Windows + Chrome + Python 3.10 environment
- Collection, aggregation, and diagnosis prompts are interactive; they do not take CLI flags
- Collected comments are stored as a flat list, not a nested reply tree
- Dataset merge requires the marketing DOCX at the default path

## Responsible use

Use this project only for content you are authorized to access and in accordance with applicable platform terms, laws, research ethics, and privacy requirements.

请仅用于你有权访问的内容，并遵守平台条款、法律法规、研究伦理与隐私要求。

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
