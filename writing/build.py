#!/usr/bin/env python3
"""Generate the linkable on-site Articles archive and article pages."""
from datetime import date
from html import escape
from pathlib import Path
from urllib.parse import urlparse
import argparse
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MANIFEST = HERE / "articles.json"
SITE = "https://ashmita-dev.onrender.com"
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
COVERS = {
    "sarwat-bano-interview": ("assets/interview_bano.webp", "Cover for the conversation with Ms. Sarwat Bano"),
    "chandan-talreja-interview": ("assets/interview_talreja.webp", "Cover for the conversation with Mr. Chandan Talreja"),
}

def tag_id(label):
    return re.sub(r"[^a-z0-9]+", "-", label.casefold()).strip("-")

def clean(text):
    assert isinstance(text, str) and text.strip()
    return escape(text.strip())

def render_body(blocks):
    assert isinstance(blocks, list)
    output = []
    for block in blocks:
        if isinstance(block, str):
            output.append(f"<p>{clean(block)}</p>")
        elif set(block) == {"h2"}:
            output.append(f'<h2>{clean(block["h2"])}</h2>')
        elif set(block) == {"p"}:
            output.append(f'<p>{clean(block["p"])}</p>')
        elif "code" in block and set(block).issubset({"code", "language"}):
            code = escape(block["code"].rstrip())
            assert code.strip()
            lang = clean(block.get("language", "text"))
            output.append(f'<pre tabindex="0" aria-label="Code example: {lang}"><code>{code}</code></pre>')
        elif set(block) == {"list"}:
            assert isinstance(block["list"], list) and block["list"]
            items = "".join(f"<li>{clean(item)}</li>" for item in block["list"])
            output.append(f"<ul>{items}</ul>")
        else:
            raise ValueError(f"Unknown article block: {block!r}")
    return "\n".join(output)

def load():
    source = json.loads(MANIFEST.read_text())
    by_id, links, tags = set(), set(), {}
    for entry in source:
        eid = entry["id"]
        assert SLUG.fullmatch(eid) and eid not in by_id, eid
        by_id.add(eid)
        url = urlparse(entry["url"])
        assert url.scheme == "https" and url.netloc and not url.username and not url.password
        assert entry["url"] not in links, entry["url"]
        links.add(entry["url"])
        assert all(entry[label].strip() for label in ("title", "type", "source"))
        if entry.get("date"):
            date.fromisoformat(entry["date"])
        assert entry["tags"] and len(set(entry["tags"])) == len(entry["tags"])
        for tag in entry["tags"]:
            slug = tag_id(tag)
            assert slug and (slug not in tags or tags[slug] == tag)
            tags[slug] = tag
        if entry.get("body"):
            assert entry.get("edition", "adapted") in {"adapted", "original", "notes"}, eid
            render_body(entry["body"])
    return source, tags

def format_date(entry, fallback=""):
    if not entry.get("date"):
        return fallback
    day = date.fromisoformat(entry["date"])
    return f'<time datetime="{day}">{day.strftime("%b")} {day.day}, {day.year}</time>'

def show_tags(entry):
    links = "".join(f"<li>{clean(tag)}</li>" for tag in entry["tags"])
    return f'<ul class="article-tags" aria-label="Topics">{links}</ul>'

def document(*, title, description, slug, prefix, body, script=""):
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{clean(title)} · Ashmita Pandey</title>
<meta name="description" content="{clean(description)}">
<link rel="canonical" href="{SITE}/{slug}">
<link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{prefix}styles.css">
{script}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header"><div class="shell header-inner">
<a class="brand" href="{prefix}index.html">Ashmita Pandey</a>
<nav aria-label="Main"><a href="{prefix}index.html#work">Work</a><a href="{prefix}index.html#speaking">Talks</a><a href="{prefix}writing.html" aria-current="page">Articles</a><a href="{prefix}index.html#leadership">Leadership</a></nav>
</div></header>
<main id="main" tabindex="-1">
{body}
</main>
<footer class="shell site-footer"><p>© Ashmita Pandey</p><a href="{prefix}index.html#contact">Contact</a></footer>
</body>
</html>
'''

def index_entry(entry):
    eid = entry["id"]
    tag_ids = " ".join(tag_id(t) for t in entry["tags"])
    return f'''<article class="article-card archive-entry" data-tags="{tag_ids}" aria-labelledby="{eid}-title">
<p class="entry-date">{format_date(entry, clean(entry["type"]))}</p>
<div><h3 id="{eid}-title"><a href="writing/{eid}.html">{clean(entry["title"])}</a></h3>
{show_tags(entry)}</div>
</article>'''

def render_index(entries, tags):
    buttons = ['<button type="button" data-filter="all" aria-pressed="true">All topics</button>']
    for tid in sorted(tags, key=lambda key: tags[key].casefold()):
        buttons.append(f'<button type="button" data-filter="{tid}" aria-pressed="false">{clean(tags[tid])}</button>')
    def group(eid, title, selected):
        if not selected:
            return ""
        cards = "\n".join(index_entry(entry) for entry in selected)
        return f'<section id="{eid}" class="archive-group" aria-labelledby="{eid}-heading"><h2 id="{eid}-heading">{title}</h2>{cards}</section>'
    body = f'''<div class="shell">
<header class="read-header">
<p class="kicker">Ashmita Pandey</p>
<h1>Articles</h1>
<p class="intro">Plain-language explainers on backend systems, AI, and software design, plus conversations with educators.</p>
</header>
<div class="article-filters" role="group" aria-label="Filter by topic" hidden>{"".join(buttons)}</div>
<p id="archive-status" class="archive-status" aria-live="polite" hidden></p>
{group("technical-articles", "Technical articles", [e for e in entries if e["type"] != "Interview"])}
{group("studybase-interviews", "Studybase interviews", [e for e in entries if e["type"] == "Interview"])}
</div>'''
    return document(title="Articles", description="On-site articles and interviews from Ashmita Pandey.", slug="writing.html", prefix="", body=body, script='<script src="writing/filter.js" defer></script>')

def read_article(entry):
    blocks = entry.get("body", [])
    eid = entry["id"]
    edition = entry.get("edition", "adapted") if blocks else "overview"
    source_note = {
        "adapted": "An on-site adaptation of Ashmita’s earlier article, not a verbatim republication.",
        "original": "",
        "notes": "Notes from a Studybase interview, not a transcript.",
        "overview": "A short overview; the full article is not reproduced here."
    }[edition]
    note = f'<aside class="edition-note">{source_note}</aside>' if source_note else ""
    formatted_date = format_date(entry)
    meta = f'<p class="article-meta">Originally published {formatted_date}</p>' if formatted_date else ""
    image = ""
    if eid in COVERS:
        file, alt = COVERS[eid]
        assert (ROOT / file).is_file()
        image = f'<figure><img src="../{file}" alt="{escape(alt)}" loading="lazy" decoding="async"></figure>'
    body = f'''<article class="article-shell">
<header class="read-header">
<a class="back-link" href="../writing.html">← All articles</a>
<p class="kicker">{"Studybase interview" if entry["type"] == "Interview" else "Technical article"}</p>
<h1>{clean(entry["title"])}</h1>
{meta}
{show_tags(entry)}
</header>
<div class="article-content">
{note}
{image}
{render_body(blocks) if blocks else f'<p>{clean(entry.get("summary") or entry["title"])}</p>'}
</div>
</article>'''
    return document(title=entry["title"], description=entry.get("summary") or entry["title"], slug=f"writing/{eid}.html", prefix="../", body=body)

def import_bodies(path):
    entries, _ = load()
    bodies = json.loads(path.read_text())
    assert isinstance(bodies, dict)
    assert set(bodies) <= {e["id"] for e in entries}, set(bodies) - {e["id"] for e in entries}
    for entry in entries:
        if entry["id"] in bodies:
            blocks = bodies[entry["id"]]
            if isinstance(blocks, dict):
                edition, blocks = blocks["edition"], blocks["body"]
            else:
                edition = "notes" if entry["type"] == "Interview" else "adapted"
            assert edition in {"original", "notes", "adapted"}
            assert blocks and render_body(blocks)
            entry["edition"] = edition
            entry["body"] = blocks
    MANIFEST.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--check", action="store_true", help="fail if generated files are stale")
    cli.add_argument("--import-bodies", type=Path, help="merge article bodies before generating")
    args = cli.parse_args()
    if args.import_bodies:
        if args.check:
            cli.error("--check cannot be used with --import-bodies")
        import_bodies(args.import_bodies)
    entries, tags = load()
    entries.sort(key=lambda entry: entry.get("date", ""), reverse=True)
    generated = {ROOT / "writing.html": render_index(entries, tags)}
    generated.update({HERE / f'{entry["id"]}.html': read_article(entry) for entry in entries})
    for path, content in generated.items():
        if args.check:
            if not path.is_file() or path.read_text() != content:
                cli.exit(1, f"{path.name} is stale; run python3 writing/build.py\n")
        else:
            path.write_text(content)
