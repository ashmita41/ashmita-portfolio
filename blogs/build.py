#!/usr/bin/env python3
"""Build the review site's static blog catalog and any supplied originals."""
import argparse
from datetime import date
from html import escape
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EMAIL = "ashmitap.official@gmail.com"
HOST = "https://ashmita-dev.onrender.com"
PREVIEW = re.compile(r"(<!-- blog-previews:start -->).*?(<!-- blog-previews:end -->)", re.S)

def t(value):
    assert isinstance(value, str) and value.strip(), value
    return escape(value.strip())

def date_label(record):
    day = date.fromisoformat(record["date"])
    return f'<time datetime="{day}">{day.strftime("%b")} {day.day}, {day.year}</time>'

def load():
    entries=json.loads((HERE/"catalog.json").read_text())
    seen=set()
    for item in entries:
        assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*",item["id"]) and item["id"] not in seen
        seen.add(item["id"])
        assert len(item["tags"]) and len(set(item["tags"])) == len(item["tags"])
        date_label(item)
        t(item["title"])
        if item.get("original"):
            assert item["original"].get("blocks"), item["id"]
            render_original(item)
    return sorted(entries,key=lambda item:item["date"],reverse=True)

def shell(title, description, canonical, body, *, prefix="", script=""):
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t(title)} · Ashmita Pandey</title>
<meta name="description" content="{t(description)}">
<meta name="author" content="Ashmita Pandey">
<link rel="canonical" href="{HOST}/{canonical}">
<link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{prefix}styles.css">
{script}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header"><div class="shell nav-row">
  <a class="brand" href="{prefix}index.html" aria-label="Ashmita Pandey home"><span class="brand-mark" aria-hidden="true">a<span>.</span></span><span>Ashmita Pandey</span></a>
  <nav aria-label="Main"><a href="{prefix}index.html#home">Home</a><a href="{prefix}index.html#speaking">Speaking</a><a href="{prefix}blogs.html" aria-current="page">Blogs</a><a href="{prefix}index.html#contact">Contact</a></nav>
</div></header>
<main class="shell" id="main" tabindex="-1">
{body}
</main>
<footer class="shell footer"><p>© Ashmita Pandey</p><a href="mailto:{EMAIL}">{EMAIL}</a><a href="{prefix}index.html">Back to home ↑</a></footer>
</body>
</html>
'''

def render_original(item):
    original=item["original"]
    body=[]
    if cover:=original.get("cover"):
        path=Path(cover["path"])
        assert path.parts and path.parts[0]=="assets" and path.suffix.lower() in (".webp",".png",".jpg",".jpeg")
        assert not path.is_absolute() and (ROOT/path).resolve().is_relative_to((ROOT/"assets").resolve())
        assert (ROOT/path).is_file()
        body.append(f'<img src="../{escape(path.as_posix())}" alt="{t(cover["alt"])}">')
    for block in original["blocks"]:
        if isinstance(block,str):
            body.append(f"<p>{t(block)}</p>")
        elif set(block)=={"heading"}:
            body.append(f'<h2>{t(block["heading"])}</h2>')
        elif set(block)=={"list"}:
            body.append("<ul>"+"".join(f"<li>{t(line)}</li>" for line in block["list"])+"</ul>")
        elif set(block)=={"code"}:
            body.append(f'<pre tabindex="0"><code>{escape(block["code"])}</code></pre>')
        else:
            raise ValueError(f"Unrecognized block in {item['id']}: {block!r}")
    content = f'''<article class="archive-head blog-detail">
<a href="../blogs.html">← All blogs</a>
<h1>{t(item["title"])}</h1>
<p>{date_label(item)} · {" · ".join(t(tag) for tag in item["tags"])}</p>
<div>{"".join(body)}</div>
</article>'''
    return shell(item["title"],item.get("summary") or item["title"],f'blogs/{item["id"]}.html',content,prefix="../")

def to_index(entries):
    tags=sorted({tag for e in entries for tag in e["tags"]},key=str.casefold)
    options='<option value="">All topics</option>'+''.join(f'<option value="{t(tag)}">{t(tag)}</option>' for tag in tags)
    results=[]
    for item in entries:
        eid=item["id"]
        title=t(item["title"])
        if item.get("original"):
            title=f'<a href="blogs/{eid}.html">{title}</a>'
        tags_html=" · ".join(t(tag) for tag in item["tags"])
        tags_data=escape(json.dumps(item["tags"],ensure_ascii=False))
        results.append(f'<li class="archive-item" id="{eid}" data-topics="{tags_data}">{date_label(item)}<div><h2>{title}</h2><p class="topic">{tags_html}</p></div></li>')
    body=f'''<header class="archive-head"><p class="eyebrow"><span class="status-dot"></span> The technical notebook</p><h1>Blogs<span class="pink">.</span></h1><p>Distributed systems, databases, AI, and the details that make them work.</p></header>
<p class="archive-note">This index lists verified article titles and topics. Full original articles and cover images will be added here from the source files.</p>
<div class="controls" hidden><label for="filter">Filter by topic</label><select id="filter">{options}</select><span id="result-count" aria-live="polite"></span></div>
<ul class="archive-list">{"".join(results)}</ul>'''
    return shell("Blogs","Technical articles by Ashmita Pandey: browse distributed systems, databases, system design, and practical AI.","blogs.html",body,script='<script src="blogs/filter.js" defer></script>')

def home_previews(entries):
    output=[]
    for item in entries[:3]:
        eid=item["id"]
        path=f"blogs/{eid}.html" if item.get("original") else f"blogs.html#{eid}"
        desc=t(item.get("summary") or " · ".join(item["tags"]))
        output.append(f'      <li><a class="preview-item" href="{path}"><p class="small-label">{t(item["tags"][0])}</p><h3>{t(item["title"])}</h3><p>{desc}</p></a></li>')
    return "\n".join(output)

if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--check",action="store_true")
    args=cli.parse_args()
    entries=load()
    home=ROOT/"index.html"
    source=home.read_text()
    replacement=lambda m:m.group(1)+"\n"+home_previews(entries)+"\n      "+m.group(2)
    refreshed,count=PREVIEW.subn(replacement,source)
    assert count==1
    files={home:refreshed,ROOT/"blogs.html":to_index(entries)}
    files.update({HERE/(e["id"]+".html"):render_original(e) for e in entries if e.get("original")})
    for path,content in files.items():
        if args.check:
            assert path.is_file() and path.read_text()==content,f"{path.name} is stale"
        else:
            path.write_text(content)
