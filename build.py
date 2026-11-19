#!/usr/bin/env python3
"""把 topics/*.md 编译成 <slug>/index.html，并重建首页。

用法：
    python3 build.py            # 全量构建
    python3 build.py --check    # 只校验，不写文件

约定：topic 文件顶部必须有 YAML frontmatter，含 title / slug / date。
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from datetime import date
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
TOPICS = ROOT / "topics"
SITE_TITLE = "Learning Notes"
SITE_SUB = "学一门手艺，不是读完一本书"

CSS = """
:root{
  --paper:#fcfbf8; --ink:#191919; --muted:#77746d; --rule:#e4e0d8;
  --accent:#9c3222; --wash:#f7f2ec;
  --serif:"Songti SC","Noto Serif CJK SC","Source Han Serif SC",Georgia,"Times New Roman",serif;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Noto Sans SC",sans-serif;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0;background:var(--paper);color:var(--ink);
  font-family:var(--sans);font-size:17px;line-height:1.8;
  font-feature-settings:"palt" 1;
}
.wrap{max-width:820px;margin:0 auto;padding:0 26px}
header.top{border-bottom:1px solid var(--rule)}
header.top .wrap{display:flex;align-items:baseline;justify-content:space-between;padding:20px 26px}
header.top a{color:var(--ink);text-decoration:none;font-size:12.5px;letter-spacing:.22em;text-transform:uppercase;font-weight:600}
header.top .meta{color:var(--muted);font-size:11.5px;letter-spacing:.16em;text-transform:uppercase}
main{padding:42px 0 84px}

.kicker{font-size:11.5px;letter-spacing:.26em;text-transform:uppercase;color:var(--accent);font-weight:600;margin-bottom:14px}
h1,h2,h3,h4{font-family:var(--serif);font-weight:600;line-height:1.3}
h1{font-size:clamp(1.62rem,3.4vw,2.18rem);margin:0 0 .5em;letter-spacing:-.012em;text-wrap:balance;max-width:19em}
h2{font-size:1.36rem;margin:3.1em 0 .75em;letter-spacing:-.005em;text-wrap:balance}
h2::before{content:"";display:block;width:26px;height:2px;background:var(--accent);margin-bottom:.62em}
h3{font-size:1.04rem;margin:2em 0 .45em;font-family:var(--sans);font-weight:650;letter-spacing:.01em}
p{margin:0 0 1.1em}
a{color:var(--accent);text-decoration:none;border-bottom:1px solid rgba(156,50,34,.25)}
a:hover{border-bottom-color:var(--accent)}
ul,ol{padding-left:1.3em;margin:0 0 1.2em}
li{margin:.3em 0}
strong{font-weight:650}
blockquote{
  margin:2em 0;padding:0 0 0 22px;border-left:2px solid var(--accent);
  font-family:var(--serif);font-size:1.02rem;color:#3d3630;line-height:1.75
}
blockquote p:last-child{margin-bottom:0}

table{border-collapse:collapse;width:100%;margin:1.6em 0 .6em;font-size:.88rem;line-height:1.6}
th{text-align:left;font-weight:650;font-size:.78rem;letter-spacing:.06em;color:var(--muted);
   border-bottom:1.5px solid var(--ink);padding:.55em .62em;white-space:nowrap}
td{border-bottom:1px solid var(--rule);padding:.62em .62em;vertical-align:top}
td:first-child{font-weight:550}
code{background:var(--wash);padding:.1em .35em;border-radius:2px;font-size:.85em;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
pre{background:var(--wash);padding:1.05em 1.15em;overflow-x:auto;font-size:.82rem;line-height:1.65;
  border-left:2px solid var(--rule)}
pre code{background:none;padding:0}
hr{border:none;border-top:1px solid var(--rule);margin:3em 0}
img{max-width:100%;height:auto;display:block;margin:2em 0 .6em;border:1px solid var(--rule)}
figure{margin:2em 0}
figcaption{font-size:.8rem;color:var(--muted);letter-spacing:.03em}

details{margin:1.2em 0;border-left:2px solid var(--rule);padding:.2em 0 .2em 18px}
summary{cursor:pointer;font-size:.86rem;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);font-weight:600}
summary::marker{color:var(--accent)}
details p{margin-top:.9em}

.meta-row{display:flex;flex-wrap:wrap;gap:16px;margin:20px 0 0;font-size:11.5px;color:var(--muted);letter-spacing:.08em}
.meta-row span{padding:0}
.meta-row span:first-child{color:var(--ink)}

.toc{margin:34px 0 0;padding:0}
.toc>b{display:block;font-size:10.5px;letter-spacing:.26em;text-transform:uppercase;color:var(--muted);margin-bottom:14px;font-weight:600}
.toc ol{list-style:none;padding:0;margin:0;column-count:2;column-gap:38px}
.toc li{margin:0;break-inside:avoid}
.toc a{display:flex;gap:10px;align-items:baseline;padding:4px 0;color:var(--ink);border-bottom:none;font-size:.88rem}
.toc a:hover{color:var(--accent)}
.toc .n{color:var(--accent);font-size:.72rem;font-variant-numeric:tabular-nums;letter-spacing:.1em;min-width:17px}

.card{display:block;padding:30px 0;border-bottom:1px solid var(--rule);text-decoration:none;color:inherit;border-left:none}
.card:hover h3{color:var(--accent)}
.card .k{font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);margin-bottom:9px}
.card h3{margin:0 0 .4em;font-size:1.22rem;font-family:var(--serif);font-weight:600;transition:color .15s}
.card p{margin:0;color:var(--muted);font-size:.9rem;line-height:1.65}
.card .tags{margin-top:.7em;font-size:11px;color:var(--muted);letter-spacing:.09em;text-transform:uppercase}

footer{border-top:1px solid var(--rule);padding:28px 0 64px;color:var(--muted);font-size:12px;letter-spacing:.04em}
.index-lede{font-family:var(--serif);font-size:1.14rem;line-height:1.7;color:#4a453e;margin:0 0 44px;max-width:34em}

@media (max-width:640px){
  body{font-size:16px}
  .wrap{padding:0 20px}
  header.top .wrap{padding:16px 20px}
  main{padding:38px 0 70px}
  .toc ol{column-count:1}
  table{font-size:.8rem}
  th,td{padding:.5em .38em}
  th{white-space:normal}
}
@media print{
  body{background:#fff;font-size:10.5pt}
  header.top,.toc,footer{display:none}
  h2{page-break-after:avoid}
  table,details{page-break-inside:avoid}
}
"""

PAGE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · {site}</title>
<meta name="description" content="{desc}">
<style>{css}</style>
</head>
<body>
<header class="top"><div class="wrap">
  <a href="/learning/">{site}</a>
  <span class="meta">{date}</span>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">{site} · {sub} · 材料由学习系统生成，请以原始文献为准</div></footer>
</body>
</html>
"""

INDEX = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{site}</title>
<style>{css}</style>
</head>
<body>
<header class="top"><div class="wrap">
  <a href="/learning/">{site}</a>
  <span class="meta">{n} 份材料</span>
</div></header>
<main><div class="wrap">
<h1>{site}</h1>
<p class="index-lede">{sub}。<br>每份材料都按同一套结构：学习台阶 → 时间预算 → 三份资源 → 概念地图 → 自测 → 速查 → 费曼复述。</p>
{cards}
</div></main>
<footer><div class="wrap">持续更新 · 最后构建 {today}</div></footer>
</body>
</html>
"""


def split_frontmatter(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2)


def slugify(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff-]+", "-", s).strip("-").lower()
    return s or "untitled"


def add_anchors(html_body: str) -> tuple[str, list[tuple[str, str]]]:
    """给 h2 加 id，返回 (新 html, [(id, 文本)]) 用于目录。"""
    toc = []

    def repl(m):
        text = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        sid = slugify(text)[:40]
        toc.append((sid, text))
        return f'<h2 id="{sid}">{m.group(1)}</h2>' 

    return re.sub(r"<h2>(.*?)</h2>", repl, html_body, flags=re.S), toc


def _first_paragraph(md: str) -> str:
    """取正文第一段纯文本作摘要（跳过标题行）。"""
    for line in md.splitlines():
        t = line.strip()
        if not t or t.startswith("#") or t.startswith("---"):
            continue
        t = re.sub(r"^>\s*", "", t)
        t = re.sub(r"[*`\[\]]", "", t)
        t = re.sub(r"\(https?://[^)]+\)", "", t)
        if t:
            return " ".join(t.split())[:110]
    return ""

def build_topic(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    meta, body_md = split_frontmatter(raw)
    title = meta.get("title") or path.stem
    slug = meta.get("slug") or slugify(path.stem)
    tags = meta.get("tags", "")
    hours = meta.get("hours", "")
    level = meta.get("level", "")
    dt = meta.get("date", "")

    body = markdown.markdown(body_md, extensions=["tables", "fenced_code", "sane_lists", "attr_list"])
    body, toc = add_anchors(body)

    toc_html = ""
    if toc:
        items = "".join(
            f'<li><a href="#{i}"><span class="n">{n:02d}</span>{html.escape(t)}</a></li>'
            for n, (i, t) in enumerate(toc, 1)
        )
        toc_html = f'<nav class="toc"><b>Contents</b><ol>{items}</ol></nav>'

    tag_html = ""
    if tags:
        chips = "".join(f"<span>{html.escape(t.strip())}</span>" for t in tags.strip("[]").split(","))
        bits = [chips]
        if hours:
            bits.append(f"<span>{html.escape(hours)} 小时</span>")
        if level:
            bits.append(f"<span>{html.escape(level)}</span>")
        tag_html = f'<div class="meta-row">{"".join(bits)}</div>'

    # 首个 h1 之后插入元信息与目录
    body = body.replace("<h1>", '<div class="kicker">Learning Note \u00b7 \u5b66\u4e60\u6750\u6599</div><h1>', 1)
    m = re.search(r"</h1>", body)
    if m:
        body = body[: m.end()] + tag_html + toc_html + body[m.end():]

    desc = meta.get("desc") or _first_paragraph(body_md)

    out_dir = ROOT / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(
        PAGE.format(title=html.escape(title), site=SITE_TITLE, css=CSS, body=body,
                    desc=html.escape(desc), date=html.escape(dt), sub=SITE_SUB),
        encoding="utf-8",
    )
    return {"slug": slug, "title": title, "desc": desc, "tags": tags, "date": dt, "hours": hours}


def build_index(topics: list[dict]) -> None:
    topics = sorted(topics, key=lambda t: t["date"], reverse=True)
    cards = []
    for t in topics:
        tags = html.escape(t["tags"].strip("[]"))
        cards.append(
            f'<a class="card" href="/learning/{t["slug"]}/">'
            f'<div class="k">{html.escape(t["date"])}{" · " + html.escape(t["hours"]) + "h" if t["hours"] else ""}</div>'
            f'<h3>{html.escape(t["title"])}</h3>'
            f'<p>{html.escape(t["desc"])}</p>'
            f'<div class="tags">{tags}</div></a>'
        )
    (ROOT / "index.html").write_text(
        INDEX.format(site=SITE_TITLE, sub=SITE_SUB, css=CSS, cards="\n".join(cards),
                     n=len(topics), today=date.today().isoformat()),
        encoding="utf-8",
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只校验 frontmatter，不写文件")
    args = ap.parse_args()

    files = sorted(TOPICS.glob("*.md"))
    if not files:
        print("no topics found", file=sys.stderr)
        return 1

    built, errors = [], []
    for f in files:
        meta, _ = split_frontmatter(f.read_text(encoding="utf-8"))
        if not meta.get("title"):
            errors.append(f"{f.name}: missing title")
            continue
        if args.check:
            built.append({"slug": meta.get("slug", f.stem), "title": meta["title"],
                          "desc": "", "tags": meta.get("tags", ""),
                          "date": meta.get("date", ""), "hours": meta.get("hours", "")})
            continue
        built.append(build_topic(f))

    if errors:
        print("ERRORS:", *errors, sep="\n  ")
        return 1

    if not args.check:
        build_index(built)
        print(f"built {len(built)} topic(s) + index")
    else:
        print(f"checked {len(built)} topic(s), all ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())