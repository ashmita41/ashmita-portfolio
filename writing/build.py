#!/usr/bin/env python3
"""Generate the no-build portfolio's Writing page from the article manifest."""
from datetime import date
from html import escape
from pathlib import Path
from urllib.parse import urlparse
import argparse
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TARGET = ROOT / "writing.html"
SITE = "https://ashmita-dev.onrender.com"
ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.casefold()).strip("-")

def load():
    articles = json.loads((HERE / "articles.json").read_text())
    ids, links, tags = set(), set(), {}
    for entry in articles:
        key = entry["id"]
        assert ID.fullmatch(key) and key not in ids, key
        ids.add(key)
        source = entry["url"]
        u = urlparse(source)
        assert u.scheme == "https" and u.netloc and not u.username and not u.password and source not in links, source
        links.add(source)
        assert all(entry[f].strip() for f in ("title", "type", "source"))
        date.fromisoformat(entry["date"]) if entry.get("date") else None
        assert entry["tags"] and isinstance(entry["tags"], list), key
        assert not entry.get("body") or isinstance(entry["body"], list) and all(isinstance(p, str) and p.strip() for p in entry["body"]), key
        for tag in entry["tags"]:
            name = slug(tag)
            assert name and (name not in tags or tags[name] == tag), tag
            tags[name] = tag
        assert len(set(entry["tags"])) == len(entry["tags"]), key
    return sorted(articles, key=lambda e: e.get("date", ""), reverse=True), tags

def card(entry):
    eid = entry["id"]
    body = entry.get("body", [])
    source = escape(entry["source"])
    title = escape(entry["title"])
    link = escape(entry["url"])
    tag_ids = " ".join(slug(t) for t in entry["tags"])
    tag_html = "".join(f"<li>{escape(t)}</li>" for t in entry["tags"])
    formatted_date = ""
    if entry.get("date"):
        day = date.fromisoformat(entry["date"])
        month = day.strftime("%B")
        formatted_date = f' · <time datetime="{day}">{month} {day.day}, {day.year}</time>'
    summary = f'<p>{escape(entry["summary"])}</p>' if entry.get("summary") else ""
    content = (
        '<details class="article-body"><summary>Read on this site</summary>'
        + "".join(f"<p>{escape(p)}</p>" for p in body)
        + "</details>"
    ) if body else ""
    location = "Republished here" if body else "External link"
    return f'''<article id="{eid}" class="card article-card" data-tags="{tag_ids}" aria-labelledby="{eid}-title">
<p class="isrc">{escape(entry["type"])} · {source}{formatted_date}</p>
<h4 id="{eid}-title">{title}</h4>
{summary}
<ul class="article-tags" aria-label="Tags">{tag_html}</ul>
{content}
<p class="article-links"><a href="{link}" aria-label="Read original: {title}">Read original</a><span>{location}</span></p>
</article>'''

def render():
    entries, tags = load()
    by_name = sorted(tags, key=lambda key: tags[key].casefold())
    filters = ['<button type="button" data-filter="all" aria-pressed="true">All topics</button>']
    filters += [f'<button type="button" data-filter="{key}" aria-pressed="false">{escape(tags[key])}</button>' for key in by_name]
    def group(group_id, title, cards):
        if not cards:
            return ""
        articles = "\n".join(card(e) for e in cards)
        return f'<section class="archive-group" aria-labelledby="{group_id}"><h3 id="{group_id}">{title}</h3><div class="archive-grid">{articles}</div></section>'
    articles = group("technical-articles", "Technical articles", [e for e in entries if e["type"] != "Interview"])
    articles += group("studybase-interviews", "Studybase interviews", [e for e in entries if e["type"] == "Interview"])
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Writing | Ashmita Pandey</title>
<meta name="description" content="An archive of articles and interviews by Ashmita Pandey. Browse by topic and find the original sources.">
<link rel="canonical" href="{SITE}/writing.html">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&amp;family=Inter:wght@400;500;600&amp;display=swap" rel="stylesheet">
<link rel="stylesheet" href="styles.css">
<script src="writing/filter.js" defer></script>
</head>
<body>
<a class="skip" href="#main">Skip to writing</a>
<header class="nav"><div class="wrap nav-in writing-nav">
<a href="index.html" class="brand">Ashmita Pandey</a>
<nav aria-label="Main"><a href="index.html#speaking">Speaking</a><a href="writing.html" aria-current="page">Writing</a><a href="index.html#contact">Contact</a></nav>
</div></header>
<main id="main" tabindex="-1">
<section class="hero writing-hero"><div class="wrap">
<p class="eyebrow">Ashmita’s archive</p>
<h1>Writing</h1>
<p class="sub hero-intro">Articles and interviews I’ve written. Pick a topic below, or open the original from any entry.</p>
</div></section>
<section class="writing-list" aria-labelledby="archive-title"><div class="wrap">
<h2 id="archive-title">Browse articles</h2>
<div class="article-filters" role="group" aria-label="Filter by topic" hidden>{"".join(filters)}</div>
<p id="archive-status" class="archive-status" aria-live="polite" hidden></p>
<div id="article-list">{articles}</div>
</div></section>
</main>
<footer><div class="wrap"><a href="index.html">Back to portfolio</a></div></footer>
</body>
</html>
'''

if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--check", action="store_true", help="fail if writing.html is stale")
    args = cli.parse_args()
    content = render()
    if args.check:
        if not TARGET.is_file() or TARGET.read_text() != content:
            cli.exit(1, "writing.html is stale; run python3 writing/build.py\n")
    else:
        TARGET.write_text(content)
