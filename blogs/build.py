#!/usr/bin/env python3
"""Build the review site's static blog catalog and any supplied originals."""
import argparse
from datetime import date
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import quote, urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
HOST = "https://ashmita-dev.onrender.com"
PREVIEW = re.compile(r"(<!-- blog-previews:start -->).*?(<!-- blog-previews:end -->)", re.S)
FOOTER = re.compile(r'<footer class="shell footer">.*?</footer>', re.S)

def site_footer():
    return """<footer class="shell footer">
  <p>Made with <span class="footer-heart" role="img" aria-label="love">♥</span> by Ashmita</p>
  <ul class="footer-socials" aria-label="Social media">
    <li><a href="https://www.instagram.com/ashmitap47/">Instagram</a></li>
    <li><a href="https://www.linkedin.com/in/ashmitapandey47">LinkedIn</a></li>
    <li><a href="https://github.com/ashmita41">GitHub</a></li>
  </ul>
</footer>"""

def t(value):
    assert isinstance(value, str) and value.strip(), value
    return escape(value.strip())

def body_text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Original text blocks must contain text")
    return escape(value)

def kind(item):
    result = item.get("kind", "article")
    if result not in ("article", "post"):
        raise ValueError(f"Unknown archive entry type: {result!r}")
    return result

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
        kind(item)
        if item.get("original"):
            assert item["original"].get("blocks"), item["id"]
            render_original(item)
    return sorted(entries,key=lambda item:item["date"],reverse=True)

THEME_TOGGLE = '<button class="theme-toggle" type="button" data-theme-toggle aria-label="Lights out? Dark mode" aria-pressed="false" hidden><svg class="theme-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M20.5 15.2A8.9 8.9 0 0 1 8.8 3.5a9 9 0 1 0 11.7 11.7Z"/></svg><svg class="theme-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.4 1.4m11.2 11.2L19 19M5 19l1.4-1.4M17.6 6.4 19 5"/></svg><span>Lights out?</span></button>'


def shell(title, description, canonical, body, *, prefix="", script="", css_version="creative-blue"):
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t(title)} · Ashmita Pandey</title>
<meta name="description" content="{t(description)}">
<meta name="author" content="Ashmita Pandey">
<link rel="canonical" href="{HOST}/{canonical}">
<link rel="icon" href="{prefix}favicon.svg?v=creative-blue" type="image/svg+xml">
<script src="{prefix}theme.js?v=1"></script>
<link rel="stylesheet" href="{prefix}styles.css?v={css_version}-footer-1">
{script}
<link rel="stylesheet" href="{prefix}theme.css?v=1">
<link rel="stylesheet" href="{prefix}site-integrations.css?v=1">
<script src="{prefix}site-integrations-config.js?v=1" defer></script>
<script src="{prefix}site-integrations.js?v=1" defer></script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header"><div class="shell nav-row">
  <a class="brand" href="{prefix}index.html" aria-label="Ashmita Pandey home"><span class="brand-mark" aria-hidden="true">a<span>.</span></span><span>Ashmita Pandey</span></a>
  {THEME_TOGGLE}
  <nav aria-label="Main"><a href="{prefix}index.html#home">Home</a><a href="{prefix}index.html#speaking">Speaking</a><a href="{prefix}blogs.html" aria-current="page">Blogs</a><a href="{prefix}index.html#contact">Contact</a></nav>
</div></header>
<main class="shell" id="main" tabindex="-1">
{body}
</main>
{site_footer()}
</body>
</html>
'''

IMAGE_SUFFIXES = {".webp", ".png", ".jpg", ".jpeg"}

def render_image(image):
    raw = image.get("path")
    alt = image.get("alt")
    if not isinstance(raw, str) or not raw.startswith("assets/") or "\\" in raw:
        raise ValueError("Image path must be relative to assets/")
    if any(part in ("", ".", "..") for part in raw.split("/")):
        raise ValueError("Image path must not contain empty or traversal segments")
    path = Path(raw)
    asset_root = (ROOT / "assets").resolve()
    image_file = (ROOT / path).resolve()
    if asset_root != ROOT.resolve() / "assets" or not image_file.is_relative_to(asset_root):
        raise ValueError("Image path must stay inside this site's assets/")
    if path.suffix.lower() not in IMAGE_SUFFIXES or not image_file.is_file():
        raise ValueError(f"Image must be an existing local WebP, PNG or JPEG: {raw}")
    if not isinstance(alt, str) or not alt.strip():
        raise ValueError("Image alt text is required")
    return f'<img src="../{quote(path.as_posix(), safe="/")}" alt="{t(alt)}" loading="lazy" decoding="async">'

def render_figure(figure):
    if not isinstance(figure, dict) or set(figure) - {"path", "alt", "caption", "credit"}:
        raise ValueError("Figure accepts path, alt, and optional caption and credit")
    image = render_image(figure)
    caption = t(figure["caption"]) if "caption" in figure else ""
    credit = f'<span class="figure-credit">Credit: {t(figure["credit"])}</span>' if "credit" in figure else ""
    details = " · ".join(part for part in (caption, credit) if part)
    return f'<figure>{image}' + (f'<figcaption>{details}</figcaption>' if details else "") + "</figure>"

def safe_href(value):
    if not isinstance(value, str) or any(ch.isspace() or ord(ch) < 32 for ch in value) or "\\" in value:
        raise ValueError("Invalid original outbound link")
    url = urlsplit(value)
    if url.scheme not in ("https", "http") or not url.hostname or url.username or url.password:
        raise ValueError("Original outbound links must be public HTTP(S) URLs")
    return escape(value, quote=True)

def render_inline(parts):
    if not isinstance(parts, list) or not parts:
        raise ValueError("Formatted paragraphs require a nonempty list of runs")
    output = []
    for part in parts:
        if isinstance(part, str):
            output.append(escape(part))
        elif isinstance(part, dict) and set(part) == {"text", "href"}:
            output.append(f'<a href="{safe_href(part["href"])}">{body_text(part["text"])}</a>')
        elif isinstance(part, dict) and len(part) == 1 and next(iter(part)) in ("strong", "em", "code"):
            tag, value = next(iter(part.items()))
            output.append(f'<{tag}>{body_text(value)}</{tag}>')
        else:
            raise ValueError(f"Invalid original inline content: {part!r}")
    return "".join(output)

RICH_VOID = {"br", "hr"}
RICH_CONTAINERS = {
    "p", "h2", "h3", "h4", "h5", "h6", "strong", "em", "u", "s", "mark", "sup", "sub",
    "ul", "ol", "li", "code", "pre", "blockquote", "table", "caption", "thead", "tbody",
    "tfoot", "tr", "th", "td", "a",
}

def render_source_node(node):
    if isinstance(node, str):
        return escape(node)
    if not isinstance(node, dict):
        raise ValueError("Original nodes must be text or structured elements")
    if set(node) == {"figure"}:
        return render_figure(node["figure"])
    tag = node.get("node")
    if tag in RICH_VOID and set(node) == {"node"}:
        return f'<{tag}>'
    if tag not in RICH_CONTAINERS or set(node) - {"node", "children", "attrs"}:
        raise ValueError(f"Invalid original element: {tag!r}")
    children = node.get("children")
    attrs = dict(node.get("attrs", {}))
    if not isinstance(children, list):
        raise ValueError("Original elements must have a children array")
    html_attrs = ' tabindex="0"' if tag == "pre" else ""
    if tag == "a":
        html_attrs += f' href="{safe_href(attrs.pop("href"))}"'
    number_attrs = {"ol": ("start",), "li": ("value",), "td": ("colspan", "rowspan"), "th": ("colspan", "rowspan")}
    for name in number_attrs.get(tag, ()):
        if name in attrs:
            number = attrs.pop(name)
            if not isinstance(number, int) or not -99999 <= number <= 99999:
                raise ValueError(f"Invalid {name} number")
            html_attrs += f' {name}="{number}"'
    if attrs:
        raise ValueError(f"Unexpected original attributes on {tag!r}")
    return f'<{tag}{html_attrs}>' + "".join(render_source_node(child) for child in children) + f'</{tag}>'

def render_original(item):
    original=item["original"]
    body=[]
    if cover:=original.get("cover"):
        body.append(render_figure(cover))
    for block in original["blocks"]:
        if isinstance(block,str):
            body.append(f"<p>{body_text(block)}</p>")
        elif set(block)=={"paragraph"}:
            body.append(f'<p>{render_inline(block["paragraph"])}</p>')
        elif set(block)=={"heading"}:
            body.append(f'<h2>{body_text(block["heading"])}</h2>')
        elif set(block)=={"subheading"}:
            body.append(f'<h3>{body_text(block["subheading"])}</h3>')
        elif set(block) in ({"list"}, {"ordered_list"}):
            key, lines = next(iter(block.items()))
            tag = "ul" if key == "list" else "ol"
            content = "".join(f"<li>{render_inline(line) if isinstance(line,list) else body_text(line)}</li>" for line in lines)
            body.append(f"<{tag}>{content}</{tag}>")
        elif set(block)=={"quote"}:
            body.append(f'<blockquote>{body_text(block["quote"])}</blockquote>')
        elif set(block)=={"code"}:
            body.append(f'<pre tabindex="0"><code>{escape(block["code"])}</code></pre>')
        elif set(block)=={"figure"}:
            body.append(render_figure(block["figure"]))
        elif set(block)=={"document"} and isinstance(block["document"], list):
            body.append('<div class="source-document">' + "".join(render_source_node(node) for node in block["document"]) + "</div>")
        else:
            raise ValueError(f"Unrecognized block in {item['id']}: {block!r}")
    content = f'''<article class="archive-head blog-detail">
<a href="../blogs.html">← All blogs</a>
<h1>{t(item["title"])}</h1>
<p>Ashmita Pandey · {date_label(item)} · {" · ".join(t(tag) for tag in item["tags"])}</p>
<div class="original-body">{"".join(body)}</div>
</article>'''
    # Numeric references preserve literal end-of-line spaces in source text/code without trailing whitespace in generated HTML.
    content = re.sub(r"[ \t]+(?=\n)", lambda m: "".join(f"&#{ord(c)};" for c in m[0]), content)
    return shell(item["title"],item.get("summary") or item["title"],f'blogs/{item["id"]}.html',content,prefix="../",css_version="archive-originals")

def archive_image(item, *, eager=False):
    original = item.get("original") or {}
    cover = original.get("cover")
    if not cover and kind(item) == "post":
        cover = next(
            (block["figure"] for block in original.get("blocks", [])
             if isinstance(block, dict) and "figure" in block), None
        )
    if not cover:
        return ""
    # Thumbnails are decorative in the same link as the title. Originals
    # retain their authored/descriptive alt text on each detail page.
    image = render_image(cover).replace('src="../', 'src="', 1)
    image = re.sub(r' alt="[^"]*"', ' alt=""', image, count=1)
    if eager:
        image = image.replace('loading="lazy"', 'fetchpriority="high"', 1)
    return f'<span class="archive-image">{image}</span>'


def archive_excerpt(item):
    text = item.get("summary") or ""
    if not text and kind(item) == "post":
        from itertools import islice
        for block in islice((item.get("original") or {}).get("blocks", []), 3):
            if isinstance(block, str):
                paragraphs = re.split(r"\n\s*\n", block.strip())
                text = next(
                    (p for p in paragraphs if p.strip() and p.strip() != item["title"].strip()),
                    ""
                )
            if text:
                break
    snippet = " ".join(text.split())
    if len(snippet) > 150:
        snippet = snippet[:148].rsplit(" ", 1)[0].rstrip(".,:;") + "…"
    return f'<p class="archive-excerpt">{t(snippet)}</p>' if snippet else ""


def archive_card(item):
    eid = item["id"]
    k = kind(item)
    label = "Article" if k == "article" else "Post"
    tags = "".join(f'<li>{t(tag)}</li>' for tag in item["tags"][:2])
    topics = escape(json.dumps(item["tags"], ensure_ascii=False))
    image = archive_image(item)
    excerpt = archive_excerpt(item)
    heading_id = f"{eid}-heading"
    content = f'''{image}<div class="archive-card-copy">
      <p class="archive-card-meta"><span class="archive-card-kind">{label}</span>{date_label(item)}</p>
      <h3 id="{heading_id}">{t(item["title"])}</h3>{excerpt}
      <div class="archive-card-footer"><ul aria-label="Topics">{tags}</ul>
      <span class="archive-arrow" aria-hidden="true">→</span></div>
    </div>'''
    if item.get("original"):
        card = f'<a class="archive-card" href="blogs/{eid}.html" aria-labelledby="{heading_id}">{content}</a>'
    else:
        card = f'<div class="archive-card archive-card-unavailable">{content}</div>'
    return f'<li class="archive-item" id="{eid}" data-kind="{k}" data-topics="{topics}">{card}</li>'


def archive_feature(item):
    if not item:
        return ""
    heading = "featured-blog-heading"
    return f'''<a class="archive-feature" href="blogs/{item["id"]}.html" aria-labelledby="{heading}">
  <div class="archive-feature-copy">
    <p class="archive-feature-label">Featured article</p>
    <h2 id="{heading}">{t(item["title"])}</h2>
    <p class="archive-feature-action" aria-hidden="true">Read article <span>→</span></p>
  </div>
  {archive_image(item, eager=True)}
</a>'''


def to_index(entries):
    articles = [entry for entry in entries if kind(entry) == "article"]
    posts = [entry for entry in entries if kind(entry) == "post" and entry.get("original")]
    entries = [entry for entry in entries if kind(entry) == "article" or entry.get("original")]
    tags = sorted({tag for e in entries for tag in e["tags"]}, key=str.casefold)
    options = '<option value="">All topics</option>' + ''.join(
        f'<option value="{t(tag)}">{t(tag)}</option>' for tag in tags
    )
    cards = "\n".join(archive_card(item) for item in entries)
    original_count = sum(bool(entry.get("original")) for entry in articles)
    if not articles and not posts:
        note = "No articles are listed yet."
    elif articles and original_count == 0:
        note = "This index lists verified titles and topics. Original text and cover images are not included yet."
    elif original_count < len(articles):
        note = f"Full text is available for {original_count} of {len(articles)} articles. The others are listed by title and topic."
    else:
        note = ""
    notice = f'<p class="archive-note">{t(note)}</p>' if note else ""
    with_covers = [article for article in articles if (article.get("original") or {}).get("cover")]
    featured = next(
        (article for article in with_covers if article["id"] == "what-a-message-queue-really-is"),
        next(iter(with_covers), None)
    )
    types = (
        '<div id="kind-filter" class="archive-types" role="group" aria-label="Content type">'
        '<button type="button" data-kind="article" aria-pressed="true">Articles</button>'
        '<button type="button" data-kind="post" aria-pressed="false">Posts</button></div>'
        if posts else ""
    )
    intro = "Long-form articles and shorter posts" if posts else "Articles"
    body = f'''<div class="blog-archive">
<header class="archive-hero">
  <div class="archive-intro">
    <p class="eyebrow"><span class="status-dot" aria-hidden="true"></span> Engineering blog</p>
    <h1>Blogs<span class="accent-dot">.</span></h1>
    <p class="archive-description">{intro} on backend engineering, system design, and AI.</p>
  </div>
  {archive_feature(featured)}
</header>
{notice}
<section class="archive-library" aria-labelledby="archive-heading">
  <h2 id="archive-heading">Browse the archive</h2>
  <form class="archive-controls" role="search" aria-label="Filter blogs" hidden>
    {types}
    <div class="archive-fields">
      <label class="archive-search">
        <span class="archive-sr-only">Search by title or topic</span>
        <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.7"><circle cx="10.5" cy="10.5" r="5.8"/><path d="m15 15 4 4"/></svg>
        <input id="archive-search" type="search" placeholder="Search titles or topics" autocomplete="off">
      </label>
      <label class="archive-topic"><span class="archive-sr-only">Filter by topic</span>
        <select id="filter">{options}</select>
      </label>
    </div>
  </form>
  <div class="archive-results-bar" hidden>
    <p id="result-count" aria-live="polite"></p>
    <button class="archive-clear" type="button" hidden>Clear filters</button>
  </div>
  <ul class="archive-grid" id="archive-grid">
{cards}
  </ul>
  <div class="archive-empty" hidden>
    <h3>No matches</h3><p>Try a different search or clear the topic filter.</p>
  </div>
  <div class="archive-more" hidden>
    <button type="button" aria-controls="archive-grid">Show more</button>
  </div>
</section>
</div>'''
    return shell(
        "Blogs",
        "Technical writing by Ashmita Pandey on backend engineering, system design, and AI.",
        "blogs.html", body,
        script='<link rel="stylesheet" href="blogs/archive.css?v=editorial-1">\n<script src="blogs/filter.js?v=editorial-1" defer></script>'
    )


def home_preview_image(item):
    cover = item["original"].get("cover")
    if not cover:
        return ""
    # Use lightweight homepage derivatives when they exist. The article
    # detail page continues to use its untouched original cover.
    thumb = Path(cover["path"]).with_name("home-thumb.webp")
    media = {**cover, "path": thumb.as_posix()} if (ROOT / thumb).is_file() else cover
    image = render_image(media).replace('src="../', 'src="', 1)
    image = re.sub(r' alt="[^"]*"', ' alt=""', image, count=1)
    return f'<span class="home-blog-thumb">{image}</span>'


def home_previews(entries):
    output = []
    for item in [entry for entry in entries if kind(entry) == "article" and entry.get("original")][:6]:
        eid = item["id"]
        label = f"home-article-{eid}"
        description = item.get("summary") or ""
        excerpt = f'<p class="home-blog-excerpt">{t(description)}</p>' if description else ""
        output.append(f'''      <li class="home-blog-slide">
        <a class="home-blog-card" href="blogs/{eid}.html" aria-labelledby="{label}">
          {home_preview_image(item)}
          <div class="home-blog-copy">
            <p class="home-blog-meta"><span>{t(item["tags"][0])}</span>{date_label(item)}</p>
            <h3 id="{label}">{t(item["title"])}</h3>
            {excerpt}
            <p class="home-blog-link" aria-hidden="true">Read article <span>→</span></p>
          </div>
        </a>
      </li>''')
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
    refreshed,count=FOOTER.subn(lambda _: site_footer(),refreshed)
    assert count==1
    files={home:refreshed,ROOT/"blogs.html":to_index(entries)}
    files.update({HERE/(e["id"]+".html"):render_original(e) for e in entries if e.get("original")})
    for path,content in files.items():
        if args.check:
            assert path.is_file() and path.read_text()==content,f"{path.name} is stale"
        else:
            path.write_text(content)
