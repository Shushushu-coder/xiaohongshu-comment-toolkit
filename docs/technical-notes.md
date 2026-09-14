# Technical Notes

Current implementation notes for the live toolkit. Paths and filenames below match the code defaults.

## Architecture

The project is a comment-collection script plus local processing tools:

- `start_chrome_debug.bat` starts or reuses a user-owned Chrome instance with remote debugging on port `9222` and a project-local profile at `data/chrome_profile`.
- `scraper.py` and `diagnose.py` attach to that instance with Selenium (`debuggerAddress=127.0.0.1:9222`).
- Collection writes per-note files under `data/comments/`.
- `tools/` transforms those files. The live path is aggregation → dialogue conversion → dataset merge. Analysis scripts and `tools/merge_and_management/` are separate.

There is no package CLI, no headless browser launcher in the live path, and no crawl-history service.

## Browser Connection Strategy

`start_chrome_debug.bat` (Windows):

1. Probes `http://127.0.0.1:9222/json/version` for a valid Chrome DevTools browser websocket.
2. If DevTools is already up, it does not launch another Chrome.
3. If port `9222` is occupied without a valid DevTools endpoint, it exits with an error and does not kill processes.
4. Otherwise it locates `chrome.exe` in common install paths and starts Chrome with `--remote-debugging-port=9222` and `--user-data-dir` pointing at `data/chrome_profile`.

Python then attaches to that session. Login happens in the browser, not in the scripts. The profile directory keeps the session across runs of the launcher.

## Data Collection Flow

`scraper.py` is interactive (`python scraper.py`):

1. Optional debug logging.
2. Mode: current tab, URLs from repository-root `note_urls.txt`, or URLs typed in the terminal.
3. Attach to Chrome.
4. For each note: wait for render, collect note metadata, scroll and expand long comments / nested replies, extract comment items, write files.

Note metadata uses the page title, JSON-like strings in page source, and CSS/XPath fallbacks.

Comment extraction:

- Tries CSS selectors such as `div[class*='comment-item']`.
- Reads username, content, relative time, and like count from each element.
- Deduplicates by `username` plus a content prefix.
- Stores a flat list. There is no `replies` / `sub_comments` field in the written JSON; nested replies that become visible after expansion are extracted as additional items when they match the comment selectors.

`note_urls.txt` is a local ignored input. The tracked template is `examples/note_urls.example.txt`. Lines must start with `http`; `#` comments are skipped.

`diagnose.py` attaches the same way, scans the current page source for like / collect / comment count patterns, and writes `interaction_diagnosis.txt` at the repository root.

## Data Processing Pipeline

Live path (defaults):

1. `tools/data_aggregator.py` reads `data/comments/comments_*.json` (or a directory typed at the prompt) and writes `data/aggregated/comments.json`, plus sidecar `titles.json` and `metadata.json`.
2. `tools/comment_to_dialogue.py` reads `data/aggregated/comments.json` and writes `data/comment_to_dialogue/dialogues_enhanced.txt` (and `report_enhanced.txt`).
3. `tools/merge_datasets.py` reads `data/marketing/营销对话数据.docx` and `dialogues_enhanced.txt`, then writes `data/merged_dataset.jsonl` (and `.json` / `.txt`).

Aggregator length is computed after stripping a `回复…：` / `回复…:` prefix; the stored `content` is unchanged. `replies` is copied only if the source JSON already has `replies` or `sub_comments`.

Optional, not on the live path:

- `tools/long_comment_extractor.py` → `data/comment_to_single/`
- `tools/marketing_classifier.py` → `data/marketing/` (same DOCX as merge, not a merge input)

`tools/merge_and_management/` is a snapshot converter. It defaults to `data/all_data_20251121/` and filenames such as `real_dialogues.txt`. It does not read live pipeline outputs.

## Output Artifacts

| Path | Writer |
|------|--------|
| `data/comments/comments_{note_id}_{timestamp}_v6.json` | `scraper.py` |
| `data/comments/comments_{note_id}_{timestamp}_v6.csv` | `scraper.py` |
| `data/comments/summary_{timestamp}_v6.txt` | `scraper.py` |
| `data/aggregated/comments.json` | `data_aggregator.py` |
| `data/comment_to_dialogue/dialogues_enhanced.txt` | `comment_to_dialogue.py` |
| `data/merged_dataset.jsonl` | `merge_datasets.py` |

The `_v6` suffix is part of the current collection filename. JSON also stores `"version": "V6"`. That is the on-disk contract, not a separate architecture.

Collection JSON shape (fields the scraper writes):

```json
{
  "note_info": {
    "note_id": "",
    "note_title": "",
    "note_url": "",
    "author": "",
    "publish_time": "",
    "likes": 0,
    "collects": 0
  },
  "comment_count": 0,
  "collected_at": "",
  "version": "V6",
  "comments": [
    {
      "comment_id": "comment_1",
      "username": "",
      "content": "",
      "time": "",
      "likes": 0,
      "collected_at": ""
    }
  ]
}
```

## Known Limitations

- Page markup and embedded JSON keys can change; selectors and regexes then need updates.
- Content that requires login is only available in an authenticated Chrome session.
- Tested with Python 3.10, Windows, and Google Chrome.
- No crawl-history skip, no `--force`, no CLI flags on the live collection/aggregation scripts.
- Collection output is a flat comment list.
- `merge_datasets.py` fails if the marketing DOCX is missing.
- Snapshot utilities keep their own directory and filenames; do not treat them as the live pipeline.
