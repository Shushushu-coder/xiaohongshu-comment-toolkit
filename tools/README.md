# tools/

Processing scripts. Default paths follow the code. If this file and the code disagree, the code wins.

Project overview and Quick Start: [../README.md](../README.md).

## Canonical artifacts

| Artifact | Producer | Consumer |
|----------|----------|----------|
| `data/comments/comments_{note_id}_{timestamp}_v6.json` | `scraper.py` | `data_aggregator.py` (glob: `comments_*.json`) |
| `data/aggregated/comments.json` | `data_aggregator.py` | `comment_to_dialogue.py`, `long_comment_extractor.py` |
| `data/comment_to_dialogue/dialogues_enhanced.txt` | `comment_to_dialogue.py` | `merge_datasets.py` |
| `data/marketing/营销对话数据.docx` | supplied by the user | `merge_datasets.py`, `marketing_classifier.py` |
| `data/merged_dataset.jsonl` | `merge_datasets.py` | terminal artifact |

`_v6` is the current collection filename suffix. `converted_dialogues.txt` is not a live default input or output.

Sidecar files (no live consumer): collection CSV / `summary_*.txt`; aggregator `titles.json` / `metadata.json`; `report_enhanced.txt`; `long_comments_*.txt`; `marketing_*.txt`; `merged_dataset.json` / `merged_dataset.txt`.

## Live tools

| Script | Default input | Default output | Purpose |
|--------|---------------|----------------|---------|
| `data_aggregator.py` | `data/comments/comments_*.json` | `data/aggregated/comments.json` (+ `titles.json`, `metadata.json`) | Merge per-note JSON into `{post_id: [comments]}` |
| `comment_to_dialogue.py` | `data/aggregated/comments.json` | `data/comment_to_dialogue/dialogues_enhanced.txt` | Convert comments to `a` / `b` / `c` dialogue text |
| `merge_datasets.py` | marketing DOCX + `dialogues_enhanced.txt` | `data/merged_dataset.jsonl` (+ `.json`, `.txt`) | Merge marketing dialogues with converted comments |

### Aggregation

```powershell
python tools\data_aggregator.py
```

Prompts for a source directory; Enter uses `data/comments`.

`comments.json` values are lists of `{comment_id, username, content, length, likes, replies?}`. `length` is measured after `re.sub(r'回复.*?[：:]', '', content)`; `content` is unchanged. `replies` is copied only when the source JSON already has `replies` or `sub_comments`. Current `scraper.py` output does not include those fields.

### Dialogue conversion

```powershell
python tools\comment_to_dialogue.py
```

Also writes `report_enhanced.txt`. Encoding is UTF-8. Some brand/product strings are replaced with placeholders. The CLI always uses `mode='balanced'`. Constructor options `strict` / `balanced` / `loose` exist in code but are not CLI flags.

Example shape:

```text
评论转对话 - 增强版输出
==================================================

【对话 1】
a：…
b：…
```

### Dataset merge

```powershell
python tools\merge_datasets.py
```

Requires `data/marketing/营销对话数据.docx`. Canonical terminal file is `data/merged_dataset.jsonl` with fields `id`, `dialogue`, `type`, `source`, `label`.

## Optional analysis

| Script | Default input | Default output | Purpose |
|--------|---------------|----------------|---------|
| `long_comment_extractor.py` | `data/aggregated/comments.json` | `data/comment_to_single/long_comments_full.txt`, `long_comments_top50.txt`, `long_comments_report.txt` | Longer single-author comments |
| `marketing_classifier.py` | `data/marketing/营销对话数据.docx` | `data/marketing/marketing_dialogues.txt`, `marketing_narratives_*.txt`, `marketing_classification_report.txt` | Split marketing DOCX into dialogues vs narratives |

```powershell
python tools\long_comment_extractor.py
python tools\marketing_classifier.py
```

`marketing_classifier.py` is parallel to merge, not a merge step. Snapshot conversion expects some of the same *filenames* under `data/all_data_20251121/`, not under `data/marketing/`. Copy manually if you need that path; do not rename live outputs.

`diagnose.py` lives at the repository root and is not part of this data path.

## Snapshot workflow

Independent of the live pipeline. Default input directory:

```text
data/all_data_20251121/
  real_dialogues.txt
  marketing_dialogues.txt
  real_narratives_full.txt
  marketing_narratives_full.txt
```

```powershell
python tools\merge_and_management\real_marketing_data_merge_data_convertor.py
```

Default output: `data/all_data_20251121/converted_data/` (`unified_all.jsonl`, `by_type/`, `by_source/`, `by_quality/`, `dataset/`, `statistics.json`).

That JSONL schema (`id`, `type`, `source`, `content`, `metadata`) is not the same as `merged_dataset.jsonl`.

```powershell
python tools\merge_and_management\prepare_dialogue_generation.py `
    --input data\all_data_20251121\converted_data\by_type\dialogues.jsonl `
    --output data\all_data_20251121\tasks\dialogue_generation `
    --format instruction `
    --context-window 3
```

`--input` and `--output` are required. `--format`: `single_turn` (default), `instruction`, `chat`.
