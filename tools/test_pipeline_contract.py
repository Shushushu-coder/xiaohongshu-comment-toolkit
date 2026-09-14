#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Synthetic producer-consumer contract smoke test.

Uses tempfile + tiny fake comments only. Does not read live collected data.
"""

import sys
import tempfile
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import importlib.util

from comment_to_dialogue import EnhancedCommentConverter
from merge_datasets import load_real_dialogues

OFFICIAL_PY = [
    Path(__file__).resolve().parents[1] / "scraper.py",
    Path(__file__).resolve().parents[1] / "diagnose.py",
    TOOLS_DIR / "comment_to_dialogue.py",
    TOOLS_DIR / "data_aggregator.py",
    TOOLS_DIR / "long_comment_extractor.py",
    TOOLS_DIR / "marketing_classifier.py",
    TOOLS_DIR / "merge_datasets.py",
    TOOLS_DIR / "merge_and_management" / "prepare_dialogue_generation.py",
    TOOLS_DIR / "merge_and_management" / "real_marketing_data_merge_data_convertor.py",
    Path(__file__).resolve(),
]


def assert_default_paths():
    """Lock repaired default Path literals so a filename/path regression fails this test."""
    comment_to_dialogue = (TOOLS_DIR / "comment_to_dialogue.py").read_text(encoding="utf-8")
    long_comment = (TOOLS_DIR / "long_comment_extractor.py").read_text(encoding="utf-8")
    merge = (TOOLS_DIR / "merge_datasets.py").read_text(encoding="utf-8")

    required = [
        (comment_to_dialogue, 'PROJECT_ROOT / "data" / "aggregated" / "comments.json"'),
        (comment_to_dialogue, 'output_dir / "dialogues_enhanced.txt"'),
        (comment_to_dialogue, "评论转对话 - 增强版输出"),
        (long_comment, 'PROJECT_ROOT / "data" / "aggregated" / "comments.json"'),
        (merge, 'PROJECT_ROOT / "data" / "comment_to_dialogue" / "dialogues_enhanced.txt"'),
        (merge, "parts[1:]"),
    ]
    missing = [literal for source, literal in required if literal not in source]
    if missing:
        raise SystemExit("FAIL: missing canonical path/format literals:\n" + "\n".join(missing))
    if 'converted_dialogues.txt' in merge:
        raise SystemExit("FAIL: merge_datasets.py still references converted_dialogues.txt")
    print("PASS: canonical default path literals")


def import_smoke():
    failed = []
    for path in OFFICIAL_PY:
        spec = importlib.util.spec_from_file_location(f"contract_{path.stem}", path)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception as exc:
            failed.append(f"{path}: {type(exc).__name__}: {exc}")
    if failed:
        raise SystemExit("FAIL import smoke:\n" + "\n".join(failed))
    print("PASS: import smoke")


def _write_dialogues_enhanced(path: Path, dialogues):
    """Match comment_to_dialogue.main() write format exactly."""
    with open(path, "w", encoding="utf-8") as f:
        f.write("评论转对话 - 增强版输出\n")
        f.write("=" * 50 + "\n\n")
        for i, dialogue in enumerate(dialogues, 1):
            f.write(f"【对话 {i}】\n{dialogue}\n\n")


def main():
    aggregated_shaped = {
        "note_synthetic_001": [
            {
                "comment_id": "comment_1",
                "username": "alice",
                "content": "这个产品好用吗? 想知道会不会长痘",
                "length": 20,
                "likes": 3,
            },
            {
                "comment_id": "comment_2",
                "username": "bob",
                "content": "回复 alice：我乳化了用也没见长痘 你要不试试？效果不错",
                "length": 28,
                "likes": 5,
            },
            {
                "comment_id": "comment_3",
                "username": "carol",
                "content": "用了两个月，白了很多，真的能美白",
                "length": 18,
                "likes": 4,
            },
        ]
    }

    converter = EnhancedCommentConverter(mode="balanced")
    produced = converter.convert_all(aggregated_shaped)
    if not produced:
        raise SystemExit("FAIL: comment_to_dialogue produced no dialogues from synthetic aggregated comments.json")

    with tempfile.TemporaryDirectory() as tmp:
        output_file = Path(tmp) / "dialogues_enhanced.txt"
        _write_dialogues_enhanced(output_file, produced)

        parsed = load_real_dialogues(output_file)
        if not parsed:
            raise SystemExit("FAIL: merge_datasets.load_real_dialogues returned no dialogues")
        if len(parsed) != len(produced):
            raise SystemExit(
                f"FAIL: parsed {len(parsed)} dialogues but producer wrote {len(produced)}"
            )

        sample = parsed[0]
        if "：" not in sample and ":" not in sample:
            raise SystemExit(f"FAIL: parsed dialogue missing speaker delimiter: {sample!r}")

    assert_default_paths()
    import_smoke()
    print("PASS: aggregator-shaped comments.json -> comment_to_dialogue -> merge_datasets parser")
    print(f"  produced_dialogues={len(produced)}")
    print(f"  parsed_dialogues={len(parsed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
