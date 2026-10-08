"""
小红书用户调研工具

工作流：关键词搜索 / URL 列表 → 抓取笔记正文 + 评论 → 生成调研报告。
可选：配置 OpenAI 兼容 API 环境变量后自动生成 AI 总结。

用法:
    python tools/user_research.py --keyword "露营装备" --notes 15
    python tools/user_research.py --urls note_urls.txt --question "用户对XX的痛点"
    python tools/user_research.py --from-json data/research/xxx/research_data.json

LLM 环境变量（OpenAI 兼容接口）:
    XHS_LLM_API_KEY   API Key（也可用 OPENAI_API_KEY）
    XHS_LLM_BASE      接口地址，默认 https://api.openai.com/v1
    XHS_LLM_MODEL     模型名，默认 gpt-4o-mini
"""

import argparse
import json
import os
import random
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scraper import CommentExtractorV6  # noqa: E402

NOTE_ID_RE = re.compile(r"/(?:explore|search_result)/([0-9a-zA-Z]+)")


class ResearchCollector(CommentExtractorV6):
    """在评论提取能力之上增加搜索与笔记正文提取。"""

    # ---------- 搜索 ----------

    def search_notes(self, keyword, limit=10, max_scrolls=8):
        """在小红书搜索关键词，返回 [{note_id, url, title, likes_text}]"""
        search_url = (
            "https://www.xiaohongshu.com/search_result?keyword="
            + urllib.parse.quote(keyword)
            + "&source=web_explore_feed"
        )
        self.log(f"搜索关键词: {keyword}", "🔍")
        self.driver.get(search_url)
        time.sleep(random.uniform(4, 6))

        if "login" in self.driver.current_url:
            self.log("被重定向到登录页，请先在浏览器中登录小红书", "❌")
            return []

        found = {}
        for round_i in range(max_scrolls):
            cards = self.driver.execute_script(
                """
                return Array.from(
                    document.querySelectorAll(
                        'a[href*="/explore/"], a[href*="/search_result/"]'
                    )
                ).map(a => {
                    const card = a.closest('section')
                        || a.closest('div[class*="note-item"]')
                        || a.parentElement;
                    let title = '';
                    let likes = '';
                    if (card) {
                        const t = card.querySelector('.title, [class*="title"]');
                        if (t) title = (t.innerText || '').trim();
                        const l = card.querySelector(
                            '.like-wrapper .count, [class*="like"] [class*="count"]'
                        );
                        if (l) likes = (l.innerText || '').trim();
                    }
                    if (!title) title = (a.innerText || '').trim();
                    return {href: a.href, title: title, likes: likes};
                });
                """
            )
            for card in cards:
                m = NOTE_ID_RE.search(card["href"])
                if not m:
                    continue
                note_id = m.group(1)
                if note_id not in found:
                    found[note_id] = {
                        "note_id": note_id,
                        "url": card["href"],
                        "title": card["title"] or "未知标题",
                        "likes_text": card["likes"],
                    }
            self.log(
                f"第 {round_i + 1} 屏：累计发现 {len(found)} 篇笔记", "📄"
            )
            if len(found) >= limit:
                break
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            time.sleep(random.uniform(1.5, 2.5))

        results = list(found.values())[:limit]
        self.log(f"搜索完成，取前 {len(results)} 篇", "✅")
        return results

    # ---------- 笔记正文 ----------

    def get_note_content(self):
        """提取笔记正文与话题标签。返回 {'content': str, 'hashtags': [str]}"""
        result = {"content": "", "hashtags": []}
        try:
            data = self.driver.execute_script(
                """
                const descSelectors = [
                    '#detail-desc',
                    '.note-content',
                    '[class*="note-text"]',
                    'div[class*="desc"]'
                ];
                let descEl = null;
                for (const sel of descSelectors) {
                    const el = document.querySelector(sel);
                    if (el && (el.innerText || '').trim().length > 0) {
                        descEl = el;
                        break;
                    }
                }
                let content = '';
                let hashtags = [];
                if (descEl) {
                    content = (descEl.innerText || '').trim();
                    hashtags = Array.from(
                        descEl.querySelectorAll(
                            'a.tag, a[href*="search_result?keyword="]'
                        )
                    ).map(t => (t.innerText || '').trim())
                     .filter(t => t.length > 0);
                }
                return {content: content, hashtags: hashtags};
                """
            )
            if data:
                result["content"] = data.get("content", "")
                result["hashtags"] = data.get("hashtags", [])
        except Exception as e:
            self.debug_log(f"提取笔记正文失败: {e}")

        preview = result["content"][:50].replace("\n", " ")
        self.log(
            f"正文: {len(result['content'])} 字 | 标签: {len(result['hashtags'])} 个"
            + (f" | {preview}..." if preview else ""),
            "📄",
        )
        return result

    # ---------- 调研主流程 ----------

    def collect_note(self, url, max_scrolls=8):
        """访问单篇笔记，返回 {note_info, content, hashtags, comments}"""
        self.driver.get(url)
        time.sleep(random.uniform(4, 6))

        note_info = self.get_note_info()
        note_content = self.get_note_content()

        self.smart_scroll_to_comments()
        self.load_all_comments_with_expansion(max_scrolls=max_scrolls)
        comments = self.extract_comments_v6()

        # 沿用既有 data/comments 契约（data_aggregator.py 可继续消费）
        if comments:
            self.save_comments(comments, note_info)

        return {
            "note_info": note_info,
            "content": note_content["content"],
            "hashtags": note_content["hashtags"],
            "comment_count": len(comments),
            "comments": comments,
        }

    def collect_by_keyword(self, keyword, notes_limit, max_scrolls,
                           min_delay=18, max_delay=28):
        """搜索关键词并逐篇采集。"""
        search_results = self.search_notes(keyword, limit=notes_limit)
        records = []
        for i, item in enumerate(search_results, 1):
            self.log(f"采集笔记 {i}/{len(search_results)}: {item['title'][:40]}", "📝")
            try:
                record = self.collect_note(item["url"], max_scrolls=max_scrolls)
                record["search_title"] = item["title"]
                record["search_likes"] = item["likes"]
                records.append(record)
            except Exception as e:
                self.log(f"采集失败: {e}", "❌")
                records.append({
                    "note_info": {"note_id": item["note_id"],
                                  "note_title": item["title"],
                                  "note_url": item["url"]},
                    "content": "", "hashtags": [],
                    "comment_count": 0, "comments": [],
                    "error": str(e),
                })
            if i < len(search_results):
                delay = random.randint(min_delay, max_delay)
                self.log(f"等待 {delay} 秒后继续（避免触发风控）...", "⏸️")
                time.sleep(delay)
        return records


# ---------- 报告生成 ----------

ANALYSIS_PROMPT_TEMPLATE = """你是一名资深用户研究分析师。以下是从小红书采集的关于「{question}」的真实用户内容（笔记正文 + 评论区），请基于此输出一份用户调研报告：

1. **核心需求与痛点**：用户反复提及的需求/抱怨，按提及频率排序
2. **使用场景**：用户在什么场景下讨论这个话题
3. **用户画像线索**：从发言推断的人群特征（年龄段、消费能力、身份等）
4. **情绪倾向**：整体态度（正面/负面/中性）及典型情绪点
5. **高频诉求 Top 5**：最值得产品关注的点
6. **产品设计建议**：基于以上发现给出可落地的建议
7. **代表性原声**：引用 5-10 条最有代表性的用户原话

要求：所有结论必须有语料支撑，标注来源笔记编号（如 [笔记3]）；不要编造语料中不存在的内容。"""


def _note_label(idx, rec):
    title = rec.get("note_info", {}).get("note_title") or rec.get("search_title") or "未知标题"
    return f"[笔记{idx}] {title}"


def build_corpus_text(notes, per_note_comment_cap=None):
    """把采集结果转成供 AI 阅读的纯文本语料。"""
    blocks = []
    for idx, rec in enumerate(notes, 1):
        info = rec.get("note_info", {})
        lines = [f"===== {_note_label(idx, rec)} ====="]
        lines.append(f"作者: {info.get('author', '未知')} | 点赞: {info.get('likes', 0)} | 收藏: {info.get('collects', 0)}")
        if rec.get("hashtags"):
            lines.append("标签: " + " ".join(rec["hashtags"]))
        if rec.get("content"):
            lines.append("正文:\n" + rec["content"])
        comments = rec.get("comments", [])
        if per_note_comment_cap:
            comments = comments[:per_note_comment_cap]
        if comments:
            lines.append(f"评论 ({rec.get('comment_count', len(comments))} 条):")
            for c in comments:
                like_tag = f" [赞{c['likes']}]" if c.get("likes") else ""
                lines.append(f"- {c.get('username', '?')}{like_tag}: {c.get('content', '')}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def generate_report(run_dir, question, keywords, notes, llm_summary=None):
    """生成 Markdown 调研报告。返回报告路径。"""
    total_comments = sum(n.get("comment_count", 0) for n in notes)
    all_comments = [c for n in notes for c in n.get("comments", [])]
    top_comments = sorted(all_comments, key=lambda c: c.get("likes", 0), reverse=True)[:20]
    total_likes = sum(n.get("note_info", {}).get("likes", 0) for n in notes)

    corpus = build_corpus_text(notes)

    lines = []
    lines.append(f"# 小红书用户调研报告\n")
    lines.append(f"- 调研问题：{question}")
    lines.append(f"- 搜索关键词：{'、'.join(keywords) if keywords else '（URL 模式）'}")
    lines.append(f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- 笔记数：{len(notes)} | 评论总数：{total_comments} | 笔记总赞数：{total_likes}\n")

    if llm_summary:
        lines.append("## AI 分析总结\n")
        lines.append(llm_summary + "\n")

    lines.append("## 笔记概览\n")
    lines.append("| # | 标题 | 作者 | 赞 | 评论数 |")
    lines.append("|---|------|------|-----|--------|")
    for idx, rec in enumerate(notes, 1):
        info = rec.get("note_info", {})
        title = (info.get("note_title") or rec.get("search_title") or "未知标题").replace("|", "\\|")[:40]
        lines.append(
            f"| {idx} | {title} | {info.get('author', '?')} "
            f"| {info.get('likes', 0)} | {rec.get('comment_count', 0)} |"
        )
    lines.append("")

    lines.append("## 高赞评论 Top 20\n")
    for i, c in enumerate(top_comments, 1):
        content = c.get("content", "").replace("\n", " ")[:120]
        lines.append(f"{i}. [赞{c.get('likes', 0)}] {c.get('username', '?')}：{content}")
    lines.append("")

    lines.append("## 给 AI 的分析提示词\n")
    lines.append("把下面这段提示词 + `corpus.txt` 的语料一起发给任意大模型即可复现分析：\n")
    lines.append("```")
    lines.append(ANALYSIS_PROMPT_TEMPLATE.format(question=question))
    lines.append("```\n")

    lines.append("## 笔记明细\n")
    for idx, rec in enumerate(notes, 1):
        info = rec.get("note_info", {})
        lines.append(f"### {_note_label(idx, rec)}\n")
        lines.append(f"- 作者：{info.get('author', '?')} | 赞 {info.get('likes', 0)} | 收藏 {info.get('collects', 0)}")
        lines.append(f"- 链接：{info.get('note_url', '')}")
        if rec.get("hashtags"):
            lines.append(f"- 标签：{' '.join(rec['hashtags'])}")
        if rec.get("content"):
            lines.append(f"\n{rec['content']}\n")
        if rec.get("error"):
            lines.append(f"\n> ⚠️ 采集失败：{rec['error']}\n")

    report_path = run_dir / "report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")

    corpus_path = run_dir / "corpus.txt"
    corpus_path.write_text(corpus, encoding="utf-8")

    return report_path, corpus_path


# ---------- LLM 总结 ----------

def llm_configured():
    return bool(os.environ.get("XHS_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY"))


def summarize_with_llm(question, corpus, max_chars=24000):
    """调用 OpenAI 兼容 chat/completions 接口生成总结。失败返回 None。"""
    api_key = os.environ.get("XHS_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    base = os.environ.get("XHS_LLM_BASE", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("XHS_LLM_MODEL", "gpt-4o-mini")

    prompt = ANALYSIS_PROMPT_TEMPLATE.format(question=question)
    if len(corpus) > max_chars:
        corpus = corpus[:max_chars] + "\n\n（语料过长，已截断）"

    payload = {
        "model": model,
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "以下是采集到的小红书语料：\n\n" + corpus},
        ],
    }
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"⚠️  LLM 总结失败（不影响报告生成）: {e}")
        return None


# ---------- 入口 ----------

def load_urls_source(args):
    """解析 --url / --urls 输入为 URL 列表。"""
    urls = list(args.url or [])
    if args.urls:
        p = Path(args.urls)
        if not p.exists():
            print(f"❌ 未找到 URL 文件: {p}")
            sys.exit(1)
        urls += [
            line.strip() for line in p.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith("http")
        ]
    return urls


def sanitize_name(text, fallback="research"):
    slug = re.sub(r"[^\w一-鿿]+", "_", text).strip("_")[:30]
    return slug or fallback


def main():
    parser = argparse.ArgumentParser(description="小红书用户调研采集工具")
    parser.add_argument("-k", "--keyword", action="append",
                        help="搜索关键词，可多次指定")
    parser.add_argument("--url", action="append", help="笔记 URL，可多次指定")
    parser.add_argument("--urls", help="URL 列表文件（每行一个）")
    parser.add_argument("-q", "--question", help="调研问题（用于报告与 AI 提示词）")
    parser.add_argument("--notes", type=int, default=10, help="每个关键词采集的笔记数（默认 10）")
    parser.add_argument("--scrolls", type=int, default=8, help="每篇笔记评论滚动轮数（默认 8）")
    parser.add_argument("--no-llm", action="store_true", help="跳过 LLM 总结")
    parser.add_argument("--from-json", help="从已有 research_data.json 重新生成报告（不采集）")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    args = parser.parse_args()

    # 仅重新生成报告
    if args.from_json:
        data = json.loads(Path(args.from_json).read_text(encoding="utf-8"))
        run_dir = Path(args.from_json).parent
        question = args.question or data.get("question") or "用户调研"
        corpus = build_corpus_text(data["notes"])
        llm_summary = None
        if not args.no_llm and llm_configured():
            print("🤖 调用 LLM 生成总结...")
            llm_summary = summarize_with_llm(question, corpus)
        report, corpus_path = generate_report(
            run_dir, question, data.get("keywords", []), data["notes"], llm_summary)
        print(f"✅ 报告已重新生成: {report}")
        print(f"✅ 语料: {corpus_path}")
        return

    urls = load_urls_source(args)
    keywords = args.keyword or []

    if not keywords and not urls:
        kw = input("请输入调研关键词（空格分隔多个）: ").strip()
        keywords = kw.split() if kw else []
        if not keywords:
            print("❌ 需要至少一个关键词或 URL")
            sys.exit(1)

    question = args.question
    if not question:
        default_q = "、".join(keywords) if keywords else "这些笔记反映的用户需求"
        q = input(f"调研问题（回车默认：{default_q}）: ").strip()
        question = q or default_q

    collector = ResearchCollector(debug=args.debug)
    if not collector.connect_to_chrome():
        sys.exit(1)

    notes = []
    try:
        for kw in keywords:
            notes.extend(collector.collect_by_keyword(
                kw, notes_limit=args.notes, max_scrolls=args.scrolls))
            if kw != keywords[-1]:
                time.sleep(random.randint(20, 30))
        for i, url in enumerate(urls, 1):
            print(f"\n🔗 处理手动 URL {i}/{len(urls)}")
            try:
                notes.append(collector.collect_note(url, max_scrolls=args.scrolls))
            except Exception as e:
                print(f"❌ 失败: {e}")
            if i < len(urls):
                time.sleep(random.randint(18, 28))
    finally:
        # 数据先落盘，报告失败也不丢采集结果
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = PROJECT_ROOT / "data" / "research" / f"{sanitize_name(question)}_{ts}"
        run_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "question": question,
            "keywords": keywords,
            "collected_at": datetime.now().isoformat(),
            "note_count": len(notes),
            "comment_count": sum(n.get("comment_count", 0) for n in notes),
            "notes": notes,
        }
        data_path = run_dir / "research_data.json"
        data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n💾 原始数据: {data_path}")

    corpus = build_corpus_text(notes)
    llm_summary = None
    if not args.no_llm and llm_configured():
        print("🤖 调用 LLM 生成总结...")
        llm_summary = summarize_with_llm(question, corpus)
    elif not args.no_llm:
        print("💡 未配置 LLM（设置 XHS_LLM_API_KEY 等环境变量可自动生成总结）")

    report, corpus_path = generate_report(run_dir, question, keywords, notes, llm_summary)

    print("\n" + "=" * 60)
    print(f"🎉 调研完成：{len(notes)} 篇笔记，{data['comment_count']} 条评论")
    print(f"📄 报告: {report}")
    print(f"📚 语料: {corpus_path}")
    if not llm_summary:
        print("💡 把 report.md 中的提示词 + corpus.txt 发给任意 AI 即可得到总结")
    print("=" * 60)


if __name__ == "__main__":
    main()
